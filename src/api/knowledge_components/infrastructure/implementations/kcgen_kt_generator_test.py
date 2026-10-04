# O paralelismo das chamadas ao LLM, que acelera sem mudar o que o KCGen-KT vê
from __future__ import annotations

import re
import threading
import time

import pandas as pd
import pytest

from api.knowledge_components.infrastructure.implementations import kcgen_kt_generator
from ml.kc_generation.llm_client import InvalidLLMResponseError
from api.knowledge_components.infrastructure.implementations.kcgen_kt_generator import (
    LLM_CONCURRENCY,
    KcGenKtGenerator,
    run_in_parallel,
)
from tests.fixtures.knowledge_components import fake_embed


class _ConcurrencyProbe:
    # Conta quantas tarefas rodam ao mesmo tempo, e cada tarefa dorme um pouco para se sobrepor
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = 0
        self.peak = 0
        self.started = 0

    def task(self, value: str, delay: float = 0.05, fail: bool = False):
        def run() -> str:
            with self._lock:
                self.running += 1
                self.started += 1
                self.peak = max(self.peak, self.running)
            time.sleep(delay)
            with self._lock:
                self.running -= 1
            if fail:
                raise RuntimeError(f"falhou {value}")
            return value

        return run


def test_runs_up_to_the_concurrency_limit_at_once():
    probe = _ConcurrencyProbe()
    tasks = {i: probe.task(str(i)) for i in range(LLM_CONCURRENCY * 2)}
    run_in_parallel(tasks, lambda done, total: None)
    assert probe.peak == LLM_CONCURRENCY


def test_returns_each_result_by_its_key_whatever_the_finishing_order():
    probe = _ConcurrencyProbe()
    # A primeira tarefa é a mais lenta, então termina por último
    tasks = {"a": probe.task("A", delay=0.2), "b": probe.task("B"), "c": probe.task("C")}
    assert run_in_parallel(tasks, lambda done, total: None) == {"a": "A", "b": "B", "c": "C"}


def test_reports_progress_from_the_calling_thread_only():
    probe = _ConcurrencyProbe()
    calls: list[tuple[int, int, int]] = []
    run_in_parallel(
        {i: probe.task(str(i)) for i in range(5)},
        lambda done, total: calls.append((done, total, threading.get_ident())),
    )
    assert [(done, total) for done, total, _ in calls] == [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]
    # A conexão SQLite do worker nunca é usada por duas threads ao mesmo tempo
    assert {thread for _, _, thread in calls} == {threading.get_ident()}


def test_a_failure_stops_the_tasks_that_did_not_start():
    probe = _ConcurrencyProbe()
    tasks = {0: probe.task("0", delay=0.01, fail=True)}
    tasks.update({i: probe.task(str(i), delay=0.2) for i in range(1, 20)})
    with pytest.raises(RuntimeError, match="falhou 0"):
        run_in_parallel(tasks, lambda done, total: None)
    assert probe.started < 20


class _EchoLLM:
    # Devolve um KC com o id do problema tirado do código no prompt, para saber quem ficou com o quê
    def __init__(self) -> None:
        self.prompts: dict[str, str] = {}

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        problem_id = re.search(r"public int p(\d+)\(", prompt).group(1)
        self.prompts[problem_id] = prompt
        # O problema 1 demora mais, então termina depois dos outros
        time.sleep(0.1 if problem_id == "1" else 0.0)
        return {"KC 1": {"reasoning": "eco", "name": f"kc do problema {problem_id}"}}


def _correct_runs(problem_ids: list[int], runs_per_problem: int = 3) -> pd.DataFrame:
    rows = [
        {
            "submission_id": problem_id * 10 + i,
            "student_id": f"S{i}",
            "problem_id": problem_id,
            "code_snapshot_id": f"c{problem_id}_{i}",
            "code": f"public int p{problem_id}() {{ return {i}; }}",
            "submitted_at": pd.Timestamp("2026-01-01T00:00:00Z") + pd.Timedelta(minutes=i),
        }
        for problem_id in problem_ids
        for i in range(runs_per_problem)
    ]
    return pd.DataFrame(rows)


def test_generation_reports_the_progress_of_each_problem(data_root, monkeypatch):
    stages: list[str] = []
    progress: list[tuple[int, int]] = []
    # Nomes de KC demais passariam pelo SBERT, e aqui só interessa o estágio generate
    monkeypatch.setattr(kcgen_kt_generator, "CANDIDATE_GROUP_COUNTS", [99])

    generated = KcGenKtGenerator(_EchoLLM(), embed=fake_embed).generate(
        _correct_runs([1, 2, 3]),
        statements={},
        classroom_id=1,
        assignment_id=1,
        on_stage=stages.append,
        on_progress=lambda done, total: progress.append((done, total)),
    )

    assert stages == ["generate", "cluster", "qmatrix"]
    assert progress == [(0, 3), (1, 3), (2, 3), (3, 3)]
    assert generated.problem_ids == [1, 2, 3]
    # Cada problema fica com o próprio conceito, mesmo o que terminou por último
    for problem_id, groups in generated.groups_by_problem.items():
        assert [generated.group_names[g] for g in groups] == [f"kc do problema {problem_id}"]
    # As três soluções distintas de cada problema vão para o LLM e ficam registradas
    assert {p: sorted(ids) for p, ids in generated.sampled_solutions.items()} == {
        p: [p * 10, p * 10 + 1, p * 10 + 2] for p in (1, 2, 3)
    }


class _RecordingLLM:
    # Guarda os prompts, para conferir a ordem das soluções que o LLM leu
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        self.prompts.append(prompt)
        return {"KC 1": {"reasoning": "eco", "name": "kc"}}


def test_the_sampled_solutions_keep_the_order_of_the_prompt(data_root):
    # A posição gravada de cada solução é a ordem em que ela aparece no prompt
    runs = _correct_runs([1], runs_per_problem=8)
    llm = _RecordingLLM()

    generated = KcGenKtGenerator(llm, embed=fake_embed).generate(
        runs, {}, 1, 1, on_stage=lambda stage: None, on_progress=lambda done, total: None
    )

    code_of = dict(zip(runs["submission_id"], runs["code"]))
    [prompt] = llm.prompts
    positions = [prompt.index(code_of[i]) for i in generated.sampled_solutions[1]]
    assert len(positions) == 5
    assert positions == sorted(positions)


def test_without_fake_vectors_the_generator_uses_the_codebert(data_root, monkeypatch):
    # O app não passa `embed`, então o padrão do gerador é o que a extração real usa
    calls: list[list[str]] = []

    def codebert(codes: list[str]):
        calls.append(codes)
        return fake_embed(codes)

    monkeypatch.setattr(kcgen_kt_generator, "embed_solutions", codebert)

    KcGenKtGenerator(_RecordingLLM()).generate(
        _correct_runs([1]),
        {},
        1,
        1,
        on_stage=lambda stage: None,
        on_progress=lambda done, total: None,
    )

    assert len(calls) == 1


def test_each_problem_gets_its_own_statement_and_the_one_without_gets_none(data_root):
    llm = _EchoLLM()

    generated = KcGenKtGenerator(llm, embed=fake_embed).generate(
        _correct_runs([1, 2]),
        {1: "Return the sum of a and b.", 2: None},
        1,
        1,
        on_stage=lambda stage: None,
        on_progress=lambda done, total: None,
    )

    # Os exemplos têm `## Problem:`, e a linha do enunciado do problema analisado é `# Problem:`
    assert "\n# Problem:\nReturn the sum of a and b.\n" in llm.prompts["1"]
    assert "\n# Problem:\n" not in llm.prompts["2"]
    # O resultado traz os candidatos, o grupo de cada nome e quem gerou
    assert generated.candidate_kcs == {
        p: [{"name": f"kc do problema {p}", "reasoning": "eco"}] for p in (1, 2)
    }
    assert set(generated.group_of_name) == {"kc do problema 1", "kc do problema 2"}
    assert (generated.model_id, generated.prompt_version) == ("claude-sonnet-5-5", "kcgen-v2")


class _EmptyForProblemTwo(_EchoLLM):
    # O problema 2 recebe sempre uma resposta sem KC, e os outros o eco de sempre
    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        answer = super().generate(system, prompt, schema, validate)
        return {} if re.search(r"public int p2\(", prompt) else answer


def test_an_invalid_answer_names_its_problem(data_root, monkeypatch):
    # A mensagem vai para o diálogo da extração, e sem o problema ninguém sabe onde olhar
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    with pytest.raises(InvalidLLMResponseError, match="problema 2,"):
        KcGenKtGenerator(_EmptyForProblemTwo(), embed=fake_embed).generate(
            _correct_runs([1, 2, 3]),
            {},
            1,
            1,
            on_stage=lambda stage: None,
            on_progress=lambda done, total: None,
        )
