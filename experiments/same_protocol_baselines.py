# O BKT e o DKT no mesmo protocolo do Code-DKT do app, para só o modelo variar entre os três.

# Roda num container descartável da edmkt-core com o pyBKT 1.4.1 instalado só nele, e grava em docs/results.

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from api.classroom_import.domain.services.submission_cleaning import PROGSNAP_TO_CLEANED_COLUMNS  # noqa: E402
from ml.code_dkt.loss import dkt_loss  # noqa: E402
from ml.code_dkt.model_input import build_model_input_tensors  # noqa: E402
from ml.code_dkt.problem_index import build_problem_index  # noqa: E402
from ml.code_dkt.student_sequences import build_student_sequences, truncate_student_sequences  # noqa: E402
from ml.code_dkt.student_split import split_students_into_train_and_test  # noqa: E402
from ml.evaluation.auc import compute_auc  # noqa: E402
from ml.evaluation.seed_evaluation import EVALUATION_SEEDS  # noqa: E402
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS  # noqa: E402
from ml.reproducibility.random_seed import seed_all_random_generators  # noqa: E402

RESULTS_DIR = ROOT / "docs" / "results"
RESULTS_PATH = RESULTS_DIR / "same_protocol_baselines.json"
TABLE_PATH = RESULTS_DIR / "same_protocol_baselines.md"
CODE_DKT_RESULTS_PATH = RESULTS_DIR / "code_dkt_order_ablation.json"

PAPER_ASSIGNMENTS = {439: "A1", 487: "A2", 492: "A3", 494: "A4", 502: "A5"}
ATTEMPT_ORDER = "file"
MAX_LEN = CODE_DKT_HYPERPARAMETERS["max_len"]
BKT_NUM_FITS = 5

PROTOCOL = {
    "data": "CSEDM CodeWorkout, só Run.Program, acerto quando Score == 1.0, sem filtro de alunos",
    "split": "split_students_into_train_and_test do app, 4:1 por exercício, random_state=1",
    "attempt_order": "file, build_student_sequences do app",
    "window": "as últimas 50 execuções, truncate_student_sequences do app, no treino e no teste",
    "first_attempt": "a primeira do par aluno e problema na sequência inteira, marcada antes do truncamento",
    "evaluated_rows": "todas as execuções da janela menos a primeira de cada aluno, as mesmas do Code-DKT",
    "auc": "compute_auc do app, geral e de primeira tentativa, com os problemas do exercício juntos",
    "std": "desvio amostral, ddof=1",
    "bkt": (
        "pyBKT 1.4.1, um KC por problema (skill_name = problem_id), sem forgets, num_fits=5, "
        "Model(seed=s, num_fits=5, parallel=False) para cada seed, order_id = posição na sequência do aluno, "
        "previsões juntadas pelo índice do DataFrame. Dos 5 pontos de partida do EM fica o ajuste de "
        "maior log-verossimilhança. A seed entra por seed_all_random_generators(s) antes de cada ajuste, "
        "porque na versão em Python puro o Model(seed=s) guarda a seed mas não a usa, e as partidas vêm "
        "do random e do np.random globais (random_model_uni.py e dirrnd.py). O Model(seed=s) fica para "
        "a versão compilada, que usaria o RandomState dele"
    ),
    "dkt": (
        "o Code-DKT do app sem o ramo de código, LSTM(2M para 128) + Linear(128 para M) + sigmoid, "
        "sem dropout, entrada de build_model_input_tensors com R=0 (só o one-hot 2M), Adam lr 0,0005, "
        "40 épocas, lote 128 com acumulação em 64, dkt_loss do app, sem corte de gradiente, "
        "seed_all_random_generators(s, strict=False) com o cuDNN determinístico"
    ),
    "seeds": list(EVALUATION_SEEDS),
    "pybkt_build": (
        "a versão legada em Python puro do pyBKT 1.4.1 (source-py), a mesma do TCC 1. O wheel tem a "
        "extensão C++ compilada contra o numpy 1.x e não carrega com o numpy 2.2.6 da imagem, e sem "
        "compilador no container o setup.py cai no Python puro. Essa versão abre um multiprocessing.Pool "
        "a cada iteração do EM, o que levava 9 minutos por seed. Como no TCC 1, o Pool vira a lista "
        "[inner(tc) for tc in thread_counts], com a mesma função e a mesma soma, e parallel=False deixa "
        "um bloco só, para a soma não depender do número de CPUs"
    ),
    "pybkt_compat_patch": (
        "o pyBKT 1.4.1 quebra na importação com o scikit-learn 1.9, ao montar a lista de métricas do "
        "sklearn para evaluate e crossvalidate, que este script não usa. No container o except TypeError "
        "de fetch_supported_metrics vira except (TypeError, AttributeError, ValueError), sem tocar no "
        "fit nem no predict"
    ),
    "run_command": (
        'docker run --rm --gpus all --security-opt label=disable -v "$PWD":/app -w /app '
        '-v "$PWD/datasets/CSEDM":/data/CSEDM:ro -e EDMKT_CSEDM_PATH=/data/CSEDM edmkt-core:dev bash -c '
        '"pip install -q --no-deps --no-binary pyBKT --root-user-action=ignore pyBKT==1.4.1 && '
        "sed -i 's/except TypeError:/except (TypeError, AttributeError, ValueError):/' "
        '/opt/conda/lib/python3.11/site-packages/pyBKT/util/metrics.py && '
        "sed -i -e 's/^    p = Pool(len(thread_counts))$/    x = [inner(tc) for tc in thread_counts]/' "
        "-e '/^    x = p.map(inner, thread_counts)$/d' -e '/^    p.close()$/d' "
        '/opt/conda/lib/python3.11/site-packages/pyBKT/fit/EM_fit.py && '
        'python experiments/same_protocol_baselines.py"'
    ),
}


def load_csedm(data_dir: Path) -> pd.DataFrame:
    # A mesma carga do fixture csedm_main_table, sem o código Java, que nenhum dos dois modelos lê
    df = pd.read_csv(data_dir / "MainTable.csv")
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")
    df = df[df["EventType"] == "Run.Program"].copy()
    df["correct"] = (df["Score"] == 1.0).astype(int)
    df = df.rename(columns={**PROGSNAP_TO_CLEANED_COLUMNS, "correct": "is_correct"})
    return df.reset_index(drop=True)


def windows(df: pd.DataFrame, progsnap_assignment_id: int) -> list[dict]:
    # Sequências na ordem do arquivo, com a primeira tentativa marcada e depois a janela das últimas 50
    sequences = build_student_sequences(df, progsnap_assignment_id, ATTEMPT_ORDER)
    return truncate_student_sequences(sequences, max_len=MAX_LEN)


def summarize(first_by_seed: dict[int, float], all_by_seed: dict[int, float]) -> dict:
    first, overall = list(first_by_seed.values()), list(all_by_seed.values())
    return {
        "first_attempt_auc_by_seed": {str(s): a for s, a in first_by_seed.items()},
        "all_attempts_auc_by_seed": {str(s): a for s, a in all_by_seed.items()},
        "first_attempt_auc_mean": float(np.mean(first)),
        "first_attempt_auc_std": float(np.std(first, ddof=1)),
        "all_attempts_auc_mean": float(np.mean(overall)),
        "all_attempts_auc_std": float(np.std(overall, ddof=1)),
    }


def evaluated_keys(predictions: pd.DataFrame) -> list[tuple]:
    # A identidade de cada linha avaliada, para provar que os modelos avaliam as mesmas
    return list(zip(predictions["student_id"], predictions["position"], predictions["is_first_attempt"]))


# BKT

def bkt_frame(sequences: list[dict]) -> pd.DataFrame:
    # Uma linha por execução da janela, com a posição dela na sequência do aluno
    rows = []
    for seq in sequences:
        for position, event in enumerate(seq["events"].itertuples(index=False)):
            rows.append({
                "order_id": len(rows),
                "user_id": str(seq["student_id"]),
                "skill_name": str(int(event.problem_id)),
                "correct": int(event.is_correct),
                "position": position,
                "is_first_attempt": bool(event.is_first_attempt),
            })
    return pd.DataFrame(rows)


def bkt_params(model) -> dict:
    # Prior, learn, guess e slip de cada problema, para ver se a seed muda o ajuste além do AUC
    out: dict[str, dict[str, float]] = {}
    for (skill, param, _klass), value in model.params()["value"].items():
        if param in ("prior", "learns", "guesses", "slips"):
            out.setdefault(str(skill), {})[param] = float(value)
    return out


def run_bkt_seed(train_frame: pd.DataFrame, test_frame: pd.DataFrame, seed: int):
    from pyBKT.models import Model

    # Na versão em Python puro as partidas do EM vêm do random e do np.random globais, e não da seed do Model
    seed_all_random_generators(seed, strict=False)
    columns = ["order_id", "user_id", "skill_name", "correct"]
    model = Model(seed=seed, num_fits=BKT_NUM_FITS, parallel=False)
    model.fit(data=train_frame[columns])
    predicted = model.predict(data=test_frame[columns])
    test = test_frame.copy()
    test["predicted_correct_probability"] = predicted["correct_predictions"].reindex(test.index).values
    test = test[test["position"] > 0].rename(columns={"user_id": "student_id", "correct": "is_correct"})
    return test.reset_index(drop=True), bkt_params(model)


# DKT

class DKTModel(nn.Module):
    # O Code-DKT do app sem o ramo de código, a entrada do LSTM é só o one-hot 2M

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.rnn = nn.LSTM(input_size=input_dim, hidden_size=hidden_dim, num_layers=1, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(x)
        return torch.sigmoid(self.fc(out))


def dkt_tensors(sequences: list[dict], problem_to_idx: dict[int, int]):
    # Com R=0 o build_model_input_tensors devolve só as 2M colunas do one-hot do Code-DKT
    return build_model_input_tensors(sequences, {}, {}, {}, problem_to_idx, max_len=MAX_LEN, R=0)


def train_dkt(train_sequences: list[dict], problem_to_idx: dict[int, int], seed: int, device) -> DKTModel:
    # O laço de train_code_dkt do app com o modelo trocado
    config = CODE_DKT_HYPERPARAMETERS
    torch.manual_seed(seed)
    np.random.seed(seed)

    M = len(problem_to_idx)
    model = DKTModel(2 * M, config["hidden_dim"], M).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"])

    X, Y_next, mask = dkt_tensors(train_sequences, problem_to_idx)
    correct_t = X[:, :, :M].sum(dim=-1)
    y_true = torch.zeros_like(correct_t)
    y_true[:, :-1] = correct_t[:, 1:]
    X, Y_next, mask, y_true = X.to(device), Y_next.to(device), mask.to(device), y_true.to(device)

    N = len(train_sequences)
    indices = np.arange(N)
    model.train()
    for _epoch in range(config["epochs"]):
        np.random.shuffle(indices)
        for start in range(0, N, config["batch_size"]):
            batch = torch.tensor(indices[start : start + config["batch_size"]], dtype=torch.long, device=device)
            optimizer.zero_grad()
            for chunk in range(0, len(batch), config["batch_chunk_size"]):
                ct = batch[chunk : chunk + config["batch_chunk_size"]]
                dkt_loss(model(X[ct]), y_true[ct], Y_next[ct], mask[ct]).backward()
            optimizer.step()
    return model


def predict_dkt(model: DKTModel, sequences: list[dict], problem_to_idx: dict[int, int], device) -> pd.DataFrame:
    # A mesma leitura de predict_code_dkt, a previsão do passo t sai da saída do passo t-1
    model.eval()
    X, _Y_next, _mask = dkt_tensors(sequences, problem_to_idx)
    with torch.no_grad():
        y_pred = model(X.to(device)).cpu().numpy()
    rows = []
    for i, seq in enumerate(sequences):
        events = seq["events"]
        start = MAX_LEN - len(events)
        for position in range(1, len(events)):
            event = events.iloc[position]
            rows.append({
                "student_id": str(seq["student_id"]),
                "position": position,
                "problem_id": int(event["problem_id"]),
                "is_correct": int(event["is_correct"]),
                "is_first_attempt": bool(event["is_first_attempt"]),
                "predicted_correct_probability": float(
                    y_pred[i, start + position - 1, problem_to_idx[int(event["problem_id"])]]
                ),
            })
    return pd.DataFrame(rows)


# Execução

def run_assignment(df: pd.DataFrame, progsnap_assignment_id: int, code_dkt: dict, device) -> dict:
    train_df, test_df = split_students_into_train_and_test(df, progsnap_assignment_id=progsnap_assignment_id)
    train_sequences = windows(train_df, progsnap_assignment_id)
    test_sequences = windows(test_df, progsnap_assignment_id)
    problem_to_idx = build_problem_index(train_sequences + test_sequences)

    train_problems = {int(p) for s in train_sequences for p in s["events"]["problem_id"]}
    test_problems = {int(p) for s in test_sequences for p in s["events"]["problem_id"]}
    assert test_problems <= train_problems, f"A{progsnap_assignment_id} tem problema do teste sem treino"

    common = {
        "paper_name": PAPER_ASSIGNMENTS[progsnap_assignment_id],
        "attempt_order": ATTEMPT_ORDER,
        "seeds": list(EVALUATION_SEEDS),
        "n_students": {"train": len(train_sequences), "test": len(test_sequences)},
    }

    # BKT, dez seeds e a seed 42 de novo, para separar o efeito da seed do de uma execução repetida
    started = time.time()
    train_frame, test_frame = bkt_frame(train_sequences), bkt_frame(test_sequences)
    bkt_first, bkt_all, bkt_params_by_seed, bkt_keys = {}, {}, {}, None
    for seed in EVALUATION_SEEDS:
        predictions, params = run_bkt_seed(train_frame, test_frame, seed)
        bkt_keys = evaluated_keys(predictions)
        bkt_first[seed] = compute_auc(predictions, first_attempt_only=True)
        bkt_all[seed] = compute_auc(predictions, first_attempt_only=False)
        bkt_params_by_seed[str(seed)] = params
        print(f"[bkt] A{progsnap_assignment_id} seed {seed} first {bkt_first[seed]:.6f} all {bkt_all[seed]:.6f}", flush=True)
    repeat, _ = run_bkt_seed(train_frame, test_frame, EVALUATION_SEEDS[0])
    n_predictions, n_first = len(bkt_keys), sum(k[2] for k in bkt_keys)
    bkt = {
        **common, **summarize(bkt_first, bkt_all),
        "n_predictions_in_test": n_predictions,
        "n_first_attempts_in_test": n_first,
        "num_fits": BKT_NUM_FITS,
        "params_by_seed": bkt_params_by_seed,
        "seed_42_repeated": {
            "first_attempt_auc": compute_auc(repeat, first_attempt_only=True),
            "all_attempts_auc": compute_auc(repeat, first_attempt_only=False),
        },
        "seconds": round(time.time() - started, 1),
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    # O Code-DKT conta as mesmas primeiras tentativas, senão a comparação não é a mesma avaliação
    expected_first = code_dkt["n_first_attempts_in_test"][ATTEMPT_ORDER]
    assert n_first == expected_first, f"A{progsnap_assignment_id} BKT tem {n_first} primeiras, o Code-DKT {expected_first}"

    # DKT, dez seeds na GPU
    started = time.time()
    dkt_first, dkt_all = {}, {}
    for seed in EVALUATION_SEEDS:
        seed_all_random_generators(seed, strict=False)
        model = train_dkt(train_sequences, problem_to_idx, seed, device)
        predictions = predict_dkt(model, test_sequences, problem_to_idx, device)
        assert sorted(evaluated_keys(predictions)) == sorted(bkt_keys), (
            f"A{progsnap_assignment_id} DKT e BKT avaliam linhas diferentes"
        )
        dkt_first[seed] = compute_auc(predictions, first_attempt_only=True)
        dkt_all[seed] = compute_auc(predictions, first_attempt_only=False)
        print(f"[dkt] A{progsnap_assignment_id} seed {seed} first {dkt_first[seed]:.6f} all {dkt_all[seed]:.6f}", flush=True)
    dkt = {
        **common, **summarize(dkt_first, dkt_all),
        "n_predictions_in_test": len(predictions),
        "n_first_attempts_in_test": int(predictions["is_first_attempt"].sum()),
        "torch": torch.__version__,
        "device": torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu",
        "seconds": round(time.time() - started, 1),
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return {"bkt": bkt, "dkt": dkt}


def percent(record: dict, metric: str) -> str:
    return f"{100 * record[f'{metric}_auc_mean']:.2f} ± {100 * record[f'{metric}_auc_std']:.2f}"


def write_table(results: dict, code_dkt: dict) -> None:
    lines = [
        "# BKT, DKT e Code-DKT no mesmo protocolo",
        "",
        "Gerado por `experiments/same_protocol_baselines.py`. Média ± desvio amostral das seeds 42 a 51, em "
        "porcentagem, na ordem do arquivo. O Code-DKT vem da chave `file` do `code_dkt_order_ablation.json`.",
        "",
    ]
    for metric, title in (("first_attempt", "AUC de primeira tentativa"), ("all_attempts", "AUC geral")):
        lines += [f"## {title}", "", "| Exercício | BKT | DKT | Code-DKT |", "|---|:---:|:---:|:---:|"]
        for aid, name in PAPER_ASSIGNMENTS.items():
            key = str(aid)
            lines.append(
                f"| {name} ({aid}) | {percent(results['bkt']['assignments'][key], metric)} | "
                f"{percent(results['dkt']['assignments'][key], metric)} | {percent(code_dkt[key], metric)} |"
            )
        lines.append("")
    TABLE_PATH.write_text("\n".join(lines))


def main() -> None:
    assert sys.flags.hash_randomization == 0, "PYTHONHASHSEED não é 0 neste processo"
    assert torch.cuda.is_available(), "o DKT roda na GPU, como o Code-DKT de referência"
    import pyBKT  # noqa: F401
    from importlib.metadata import version

    device = torch.device("cuda")
    df = load_csedm(Path(os.environ["EDMKT_CSEDM_PATH"]))
    code_dkt = json.loads(CODE_DKT_RESULTS_PATH.read_text())[ATTEMPT_ORDER]["assignments"]
    only = [int(a) for a in sys.argv[1:]] or list(PAPER_ASSIGNMENTS)

    results = json.loads(RESULTS_PATH.read_text()) if RESULTS_PATH.exists() else {}
    results["protocol"] = {**PROTOCOL, "pybkt": version("pyBKT"), "torch": torch.__version__}
    for aid in only:
        record = run_assignment(df, aid, code_dkt[str(aid)], device)
        for model_name in ("bkt", "dkt"):
            results.setdefault(model_name, {}).setdefault("assignments", {})[str(aid)] = record[model_name]
        RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    if all(str(a) in results.get("bkt", {}).get("assignments", {}) for a in PAPER_ASSIGNMENTS):
        write_table(results, code_dkt)
    print(f"resultados em {RESULTS_PATH}")


if __name__ == "__main__":
    main()
