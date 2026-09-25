# O paralelismo das chamadas ao LLM, que acelera sem mudar o que o KCGen-KT vê
from __future__ import annotations

import re
import threading
import time

import pandas as pd
import pytest

from api.knowledge_components.infrastructure.implementations import kcgen_kt_generator
from api.knowledge_components.infrastructure.implementations.kcgen_kt_generator import (
    LLM_CONCURRENCY,
    KcGenKtGenerator,
    run_in_parallel,
)


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
    # Devolve um KC com o id do problema tirado do prompt, para conferir quem ficou com o quê
    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        problem_id = re.search(r"Problem (\d+) — Correct student solutions", prompt).group(1)
        # O problema 1 demora mais, então termina depois dos outros
        time.sleep(0.1 if problem_id == "1" else 0.0)
        return {"kcs": [{"name": f"kc do problema {problem_id}", "reasoning": "eco"}]}


def _submissions(problem_ids: list[int]) -> pd.DataFrame:
    rows = [
        {
            "student_id": f"S{i}",
            "problem_id": problem_id,
            "code_snapshot_id": f"c{problem_id}_{i}",
            "code": f"public int p{problem_id}() {{ return {i}; }}",
            "is_correct": 1,
            "submitted_at": pd.Timestamp("2026-01-01T00:00:00Z") + pd.Timedelta(minutes=i),
        }
        for problem_id in problem_ids
        for i in range(3)
    ]
    return pd.DataFrame(rows)


def test_generation_reports_the_progress_of_each_problem(data_root, monkeypatch):
    stages: list[str] = []
    progress: list[tuple[int, int]] = []
    # Nomes de KC demais passariam pelo SBERT, e aqui só interessa o estágio generate
    monkeypatch.setattr(kcgen_kt_generator, "CANDIDATE_GROUP_COUNTS", [99])

    generated = KcGenKtGenerator(_EchoLLM()).generate(
        _submissions([1, 2, 3]),
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
