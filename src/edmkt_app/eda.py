"""EDA de turma a partir do Parquet canônico (DASH-04, D-06) — SEM modelo treinado.

A EDA é a view SEMPRE disponível: lê só o Parquet canônico da Fase 3 (CANONICAL_COLUMNS
de clean.py) e nunca toca um artefato de modelo nem a stack de inferência (D-06). O professor
tem dashboard de EDA antes mesmo do treino.

Módulo majoritariamente puro (DataFrame-in → out), no estilo de `ingestion/clean.py:9`. O
ÚNICO I/O é o `pd.read_parquet` num wrapper fino (`_read_canonical`), reaproveitado pelas
funções públicas que recebem o caminho do Parquet.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# Só o contrato do stream canônico é importado de outro módulo do app. EDA NÃO importa
# train.py/persistence: aquele lado puxa torch + ArtifactStore e quebraria a invariante
# "EDA roda sem modelo" (D-06). _slug/_progsnap_aid são triviais e reproduzidos aqui.
from edmkt_app.ingestion.clean import ALLOWED_EVENTS  # noqa: F401  (documenta o contrato do stream)

RUN_EVENT = "Run.Program"
COMPILE_ERROR_EVENT = "Compile.Error"

# Default herdado de train.DATA_ROOT; não importado de lá para manter a EDA livre de torch.
DATA_ROOT = Path("data")

# Semente do protocolo congelado (Code-DKT, Shi et al. 2022) — reusada pelos clusters opcionais
# para que o KMeans seja determinístico. EDA não treina modelo; só agrega.
SEED = 42


def _slug(name: str) -> str:
    # Mesma forma de train._slug: o diretório da turma vem do slug interno, nunca de upload.
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "turma"


def _progsnap_aid(assignment_name: str) -> int:
    # AssignmentID do ProgSnap2 (sufixo de "Assignment <N>"), igual a train._progsnap_aid.
    m = re.search(r"(\d+)", assignment_name)
    if m is None:
        raise ValueError(f"AssignmentID não derivável do nome: {assignment_name!r}")
    return int(m.group(1))


def _read_canonical(pq: Path | str) -> pd.DataFrame:
    # Único ponto de I/O do módulo (T-06-05): o caminho vem de IDs int + _slug/_progsnap_aid
    # internos, NUNCA de caminho de cliente; o read não carrega artefato de modelo (D-06).
    return pd.read_parquet(pq, engine="pyarrow")


def canonical_parquet_path(turma_name: str, assignment_name: str) -> Path:
    """Deriva o caminho do Parquet canônico igual a `train.py:89` — a partir de nomes internos."""
    return (
        DATA_ROOT / _slug(turma_name) / "clean" / f"assignment_{_progsnap_aid(assignment_name)}.parquet"
    )


# --- Agregações puras (DataFrame-in → out) ---------------------------------------


def _success_rate_by_assignment(df: pd.DataFrame) -> dict[int, float]:
    runs = df[df["EventType"] == RUN_EVENT]
    return {int(aid): float(rate) for aid, rate in runs.groupby("AssignmentID")["correct"].mean().items()}


def _learning_curve(df: pd.DataFrame) -> dict[int, float]:
    runs = df[df["EventType"] == RUN_EVENT].sort_values("ServerTimestamp")
    # attempt_num = cumcount por (aluno, assignment): a n-ésima tentativa de Run.Program do aluno.
    attempt = runs.groupby(["SubjectID", "AssignmentID"]).cumcount()
    curve = runs.assign(attempt_num=attempt).groupby("attempt_num")["correct"].mean()
    return {int(k): float(v) for k, v in curve.sort_index().items()}


def _compile_error_rate_by_assignment(df: pd.DataFrame) -> dict[int, float]:
    # WR-03: a taxa é CE_count / Run_count (compile-errors POR tentativa de execução), não
    # CE_count / (CE+Run). A média sobre TODOS os eventos misturava os dois tipos e variava
    # com quantos Run.Program o aluno teve, tornando a métrica incomparável com a convenção.
    runs = df[df["EventType"] == RUN_EVENT]
    ce = df[df["EventType"] == COMPILE_ERROR_EVENT]
    run_counts = runs.groupby("AssignmentID").size()
    ce_counts = ce.groupby("AssignmentID").size().reindex(run_counts.index, fill_value=0)
    rate = (ce_counts / run_counts).fillna(0.0)
    return {int(aid): float(v) for aid, v in rate.items()}


# --- API pública: caminho-in → agregado-out (single read no wrapper) -------------


def success_rate_by_assignment(pq: Path | str) -> dict[int, float]:
    """Taxa de acerto por AssignmentID = média de `correct` sobre eventos Run.Program."""
    return _success_rate_by_assignment(_read_canonical(pq))


def learning_curve(pq: Path | str) -> dict[int, float]:
    """Curva de aprendizado: média de `correct` por número de tentativa (cumcount), ordenada."""
    return _learning_curve(_read_canonical(pq))


def compile_error_rate_by_assignment(pq: Path | str) -> dict[int, float]:
    """Taxa de compile-error por AssignmentID = Compile.Error por tentativa (CE_count/Run_count)."""
    return _compile_error_rate_by_assignment(_read_canonical(pq))


# --- Profile clusters: SÓ features do Parquet, degrada sem X-Grade (D-06, Pitfall 3) ----


def _student_features(df: pd.DataFrame) -> pd.DataFrame:
    runs = df[df["EventType"] == RUN_EVENT]
    g = runs.groupby("SubjectID")
    return pd.DataFrame(
        {
            "correct_rate": g["correct"].mean(),
            "attempt_count": g.size(),
            "completion": g["correct"].max(),  # chegou a passar ao menos um Run.Program
        }
    )


def profile_clusters(pq: Path | str, n_clusters: int = 3) -> dict[str, int] | None:
    """Agrupa alunos por features DERIVÁVEIS do Parquet (sem Subject.csv / X-Grade).

    D-06: não constrói os clusters completos do KCGen — só os perfis de esforço/acerto que o
    Parquet permite. Degrada limpo (retorna None) quando há alunos de menos para n_clusters.
    """
    feats = _student_features(_read_canonical(pq))
    if len(feats) < n_clusters:
        return None  # features esparsas demais — sem X-Grade não há como adensar (degrada).

    from sklearn.cluster import KMeans

    labels = KMeans(n_clusters=n_clusters, random_state=SEED, n_init=10).fit_predict(feats.values)
    return {str(sid): int(lab) for sid, lab in zip(feats.index, labels)}
