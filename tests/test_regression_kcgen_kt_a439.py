# Teste de regressão do KCGen-KT no A439, contra a extração de referência gravada em tests/data/kc.

# Marcado @pytest.mark.regression, fora da suíte padrão, porque lê a CSEDM e carrega os modelos.

# A primeira camada refaz o sorteio pelo CodeBERT e o agrupamento pelo SBERT, sem chamar o LLM.

# A segunda refaz a extração inteira lendo o cache gravado, e qualquer pergunta fora dele falha.

# Leva cerca de um minuto e meio na GPU, e uns 17 minutos sem ela.

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from api.classroom_import.domain.services.submission_cleaning import clean_submissions
from api.classroom_import.infrastructure.implementations.progsnap_csv_reader import (
    ProgSnapCsvReader,
)
from api.knowledge_components.infrastructure.implementations.kcgen_kt_generator import (
    KcGenKtGenerator,
)
from api.shared.infrastructure import settings
from api.shared.infrastructure.filesystem import data_layout
from ml.kc_generation.embedding_models import embed_kc_names, embed_solutions
from ml.kc_generation.kc_grouping import group_similar_kcs, kc_group_count
from ml.kc_generation.solution_sampling import select_sample_solutions
from tests.fixtures.csedm import resolve_csedm_path

A439 = 439
DATA = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="module")
def reference() -> dict:
    path = DATA / "kc" / "a439_reference_extraction.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def correct_runs() -> pd.DataFrame:
    # As execuções corretas do A439 pelo leitor e pela limpeza da importação, na ordem do banco
    csedm = resolve_csedm_path()
    reader = ProgSnapCsvReader()
    main_table, _ = reader.read_main_table(csedm / "MainTable.csv")
    cleaned, _ = clean_submissions(main_table, reader.read_code_snapshots(csedm))
    runs = cleaned[(cleaned["progsnap_assignment_id"] == A439) & (cleaned["is_correct"] == 1)]
    # O id segue a ordem em que a importação grava, e é ele que desempata os horários iguais
    return runs.assign(submission_id=range(1, len(runs) + 1)).reset_index(drop=True)


def _unique_names(reference: dict) -> list[str]:
    # Os nomes na ordem dos problemas e das respostas, a ordem em que entram no agrupamento
    problems = sorted(reference["candidate_kcs"], key=int)
    return list(
        dict.fromkeys(kc["name"] for p in problems for kc in reference["candidate_kcs"][p])
    )


@pytest.mark.regression
def test_codebert_draws_the_same_solutions_as_the_reference(correct_runs, reference):
    for problem, expected in reference["sampled_solutions"].items():
        runs = correct_runs[correct_runs["problem_id"] == int(problem)]
        samples = select_sample_solutions(runs, embed_solutions)
        assert [str(s["code_snapshot_id"]) for s in samples] == expected, f"problema {problem}"


@pytest.mark.regression
def test_sbert_groups_the_recorded_names_as_the_reference(reference):
    # No A439 nenhum grupo foi fundido por nome, então cada grupo é um conceito da referência
    names = _unique_names(reference)

    labels = group_similar_kcs(embed_kc_names(names), kc_group_count(len(names)))

    produced = {
        frozenset(n for n, label in zip(names, labels) if label == group) for group in set(labels)
    }
    group_of_name = reference["group_of_name"]
    expected = {
        frozenset(n for n in names if group_of_name[n] == group)
        for group in set(group_of_name.values())
    }
    assert produced == expected


class _OnlyTheCache:
    # LLM que falha em toda pergunta, então a extração só passa se as respostas vierem do cache
    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        raise AssertionError(f"pergunta fora do cache gravado, começando por {prompt[:80]!r}")


@pytest.mark.regression
def test_the_whole_extraction_from_the_recorded_cache_gives_the_reference(
    correct_runs, reference, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    cache_dir = data_layout.llm_cache_dir(1, 1)
    cache_dir.mkdir(parents=True)
    shutil.copy(DATA / "kc" / "a439_llm_cache.json", cache_dir / "kc_cache.json")
    statements = {
        problem: text
        for (assignment, problem), text in ProgSnapCsvReader()
        .read_problem_statements(DATA / "csedm_problem_statements")
        .items()
        if assignment == A439
    }

    generated = KcGenKtGenerator(_OnlyTheCache()).generate(
        correct_runs,
        statements,
        1,
        1,
        on_stage=lambda stage: None,
        on_progress=lambda done, total: None,
    )

    snapshot_of = dict(zip(correct_runs["submission_id"], correct_runs["code_snapshot_id"]))
    sampled = {
        str(p): [str(snapshot_of[i]) for i in ids] for p, ids in generated.sampled_solutions.items()
    }
    assert sampled == reference["sampled_solutions"]
    candidates = {str(p): kcs for p, kcs in generated.candidate_kcs.items()}
    assert candidates == reference["candidate_kcs"]
    assert generated.group_of_name == reference["group_of_name"]
    concepts = {
        str(g): {"generated_name": name, "name": generated.translated_group_names[g]}
        for g, name in generated.group_names.items()
    }
    assert concepts == reference["concepts"]
    groups = {str(p): g for p, g in generated.groups_by_problem.items()}
    assert groups == reference["groups_by_problem"]
    evidence = {str(p): items for p, items in generated.evidence.items() if items}
    assert evidence == reference["evidence"]
