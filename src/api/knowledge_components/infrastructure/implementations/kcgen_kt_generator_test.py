# O gerador do KCGen-KT, o paralelismo das chamadas ao LLM, o agrupamento e a nomeação.
from __future__ import annotations

import json
import re
import threading
import time

import numpy as np
import pandas as pd
import pytest

from api.knowledge_components.infrastructure.implementations import kcgen_kt_generator
from ml.kc_generation.llm_client import InvalidLLMResponseError
from api.knowledge_components.infrastructure.implementations.kcgen_kt_generator import (
    LLM_CONCURRENCY,
    KcGenKtGenerator,
    run_in_parallel,
)
from tests.fixtures.knowledge_components import (
    FOR_MARK,
    LENGTH_MARK,
    MarkedCodeLLM,
    evidence_concepts,
    evidence_solutions,
    fake_embed,
    multiline_runs,
    naming_answer,
    stage_answer,
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
    # Devolve um KC com o id do problema tirado do código no prompt, para saber quem ficou com o quê
    def __init__(self) -> None:
        self.prompts: dict[str, str] = {}

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        answer = stage_answer(prompt)
        if answer is not None:
            return answer
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


def test_generation_reports_the_progress_of_each_problem(data_root):
    stages: list[str] = []
    progress: list[tuple[int, int]] = []

    generated = KcGenKtGenerator(_EchoLLM(), embed=fake_embed, embed_names=fake_embed).generate(
        _correct_runs([1, 2, 3]),
        statements={},
        classroom_id=1,
        assignment_id=1,
        on_stage=stages.append,
        on_progress=lambda done, total: progress.append((done, total)),
    )

    assert stages == ["generate", "cluster", "qmatrix", "evidence", "translate"]
    # Três problemas no generate e nos trechos, 1 grupo na nomeação, e a tradução não conta itens
    assert progress == [
        (0, 3), (1, 3), (2, 3), (3, 3), (0, 1), (1, 1), (0, 3), (1, 3), (2, 3), (3, 3)
    ]
    assert generated.problem_ids == [1, 2, 3]
    # Cada problema fica com o próprio KC candidato, mesmo o que terminou por último
    assert {p: [kc["name"] for kc in kcs] for p, kcs in generated.candidate_kcs.items()} == {
        p: [f"kc do problema {p}"] for p in (1, 2, 3)
    }
    # As três soluções distintas de cada problema vão para o LLM e ficam registradas
    assert {p: sorted(ids) for p, ids in generated.sampled_solutions.items()} == {
        p: [p * 10, p * 10 + 1, p * 10 + 2] for p in (1, 2, 3)
    }


class _RecordingLLM:
    # Guarda os prompts de geração, para conferir a ordem das soluções que o LLM leu
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        answer = stage_answer(prompt)
        if answer is not None:
            return answer
        self.prompts.append(prompt)
        return {"KC 1": {"reasoning": "eco", "name": "kc"}}


def test_the_sampled_solutions_keep_the_order_of_the_prompt(data_root):
    # A posição gravada de cada solução é a ordem em que ela aparece no prompt
    runs = _correct_runs([1], runs_per_problem=8)
    llm = _RecordingLLM()

    generated = KcGenKtGenerator(llm, embed=fake_embed, embed_names=fake_embed).generate(
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

    KcGenKtGenerator(_RecordingLLM(), embed_names=fake_embed).generate(
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

    generated = KcGenKtGenerator(llm, embed=fake_embed, embed_names=fake_embed).generate(
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
        p: [{"name": f"kc do problema {p}", "reasoning": "eco", "translated_reasoning": "pt eco"}]
        for p in (1, 2)
    }
    assert set(generated.group_of_name) == {"kc do problema 1", "kc do problema 2"}
    assert (generated.model_id, generated.prompt_version) == ("claude-sonnet-5-5", "kcgen-v2")


class _EmptyForProblemTwo(_EchoLLM):
    # O pedido de geração do problema 2 recebe sempre uma resposta sem KC, e o resto o de sempre
    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        if prompt.startswith("# Example 1:") and re.search(r"public int p2\(", prompt):
            return {}
        return super().generate(system, prompt, schema, validate)


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


class _ScriptedLLM:
    # Os KCs de cada problema vêm do dicionário, e a nomeação fica com o primeiro nome do grupo
    def __init__(self, names_by_problem: dict[int, list[str]]) -> None:
        self._names = names_by_problem
        self.naming_prompts: list[str] = []

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        naming = naming_answer(prompt)
        if naming is not None:
            self.naming_prompts.append(prompt)
            return naming
        answer = stage_answer(prompt)
        if answer is not None:
            return answer
        problem_id = int(re.search(r"public int p(\d+)\(", prompt).group(1))
        return {
            f"KC {i}": {"reasoning": "r", "name": name}
            for i, name in enumerate(self._names[problem_id], 1)
        }


def _embed_by_group(group_of: dict[str, int]):
    # Vetores falsos do SBERT, iguais para os nomes de um grupo e ortogonais entre os grupos
    size = max(group_of.values()) + 1
    return lambda names: np.stack([np.eye(size)[group_of[name]] for name in names])


def _generate(llm, problem_ids: list[int], group_of: dict[str, int], progress=None):
    # O progresso vai para `progress` como (estágio, feitos, total)
    progress = [] if progress is None else progress
    stages: list[str] = []
    return KcGenKtGenerator(llm, embed=fake_embed, embed_names=_embed_by_group(group_of)).generate(
        _correct_runs(problem_ids),
        {},
        1,
        1,
        on_stage=stages.append,
        on_progress=lambda done, total: progress.append((stages[-1], done, total)),
    )


def _listed_names(naming_prompt: str) -> list[str]:
    return json.loads(naming_prompt.split("is: ", 1)[1].split("\n", 1)[0])


def test_the_names_enter_the_grouping_in_the_numeric_order_of_the_problems(data_root):
    # Como texto, o problema 10 viria antes do 2
    llm = _ScriptedLLM({2: ["while loop"], 10: ["for loop"]})

    generated = _generate(llm, [10, 2], {"while loop": 0, "for loop": 0})

    assert generated.problem_ids == [2, 10]
    [naming_prompt] = llm.naming_prompts
    assert _listed_names(naming_prompt) == ["while loop", "for loop"]


def test_a_group_of_one_kc_keeps_its_name_in_lowercase_without_a_call(data_root):
    # Quatro nomes dão 2 grupos, e só o grupo dos três laços vai para o LLM
    llm = _ScriptedLLM({1: ["For loop", "While loop", "Do while loop"], 2: ["String Length"]})
    group_of = {"For loop": 0, "While loop": 0, "Do while loop": 0, "String Length": 1}
    progress: list[tuple[int, int]] = []

    generated = _generate(llm, [1, 2], group_of, progress)

    assert [_listed_names(prompt) for prompt in llm.naming_prompts] == [
        ["For loop", "While loop", "Do while loop"]
    ]
    assert [item for item in progress if item[0] == "cluster"] == [
        ("cluster", 0, 1),
        ("cluster", 1, 1),
    ]
    assert generated.group_names == {0: "for loop", 1: "string length"}
    assert generated.groups_by_problem == {1: [0], 2: [1]}


def test_groups_that_get_the_same_name_become_one_concept(data_root):
    # Os dois grupos de laços recebem o nome "for loop", e a Q-matrix fica com uma coluna só
    llm = _ScriptedLLM({1: ["For loop", "for loop iteration"], 2: ["FOR LOOP", "loop counter"]})
    group_of = {"For loop": 0, "for loop iteration": 0, "FOR LOOP": 1, "loop counter": 1}

    generated = _generate(llm, [1, 2], group_of)

    assert len(llm.naming_prompts) == 2
    assert generated.group_names == {0: "for loop"}
    assert generated.groups_by_problem == {1: [0], 2: [0]}
    assert set(generated.group_of_name.values()) == {0}


def test_a_single_name_is_one_concept_without_naming(data_root):
    llm = _ScriptedLLM({1: ["While Loop"], 2: ["While Loop"]})
    progress: list[tuple[int, int]] = []

    generated = _generate(llm, [1, 2], {"While Loop": 0}, progress)

    assert llm.naming_prompts == []
    # Sem grupo para nomear, o estágio da nomeação não conta nada
    assert [item for item in progress if item[0] == "cluster"] == []
    assert generated.group_names == {0: "while loop"}
    assert generated.groups_by_problem == {1: [0], 2: [0]}


def test_without_fake_name_vectors_the_generator_uses_the_sbert(data_root, monkeypatch):
    # O app não passa `embed_names`, então o padrão do gerador é o SBERT que a extração real usa
    calls: list[list[str]] = []

    def sbert(names: list[str]):
        calls.append(names)
        return fake_embed(names)

    monkeypatch.setattr(kcgen_kt_generator, "embed_kc_names", sbert)

    KcGenKtGenerator(_RecordingLLM(), embed=fake_embed).generate(
        _correct_runs([1]),
        {},
        1,
        1,
        on_stage=lambda stage: None,
        on_progress=lambda done, total: None,
    )

    assert calls == [["kc"]]


def test_without_correct_runs_nothing_is_embedded_named_or_asked(data_root):
    # Sem execução correta não há problema, nem KC, nem nome para agrupar, e o SBERT nem é chamado
    def boom(names):
        raise AssertionError("o SBERT não devia ser chamado")

    llm = _RecordingLLM()
    stages: list[str] = []

    generated = KcGenKtGenerator(llm, embed=fake_embed, embed_names=boom).generate(
        _correct_runs([1]).iloc[0:0],
        {},
        1,
        1,
        on_stage=stages.append,
        on_progress=lambda done, total: None,
    )

    assert llm.prompts == []
    assert (generated.problem_ids, generated.group_names, generated.group_of_name) == ([], {}, {})
    assert stages == ["generate", "cluster", "qmatrix", "evidence", "translate"]


class _InvalidNaming(_ScriptedLLM):
    # A geração responde certo, e a nomeação vem sempre sem nome
    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        if naming_answer(prompt) is not None:
            return {"reasoning": "x", "representative kc": None, "summary name": None}
        return super().generate(system, prompt, schema, validate)


def test_an_invalid_naming_answer_names_its_group(data_root, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    llm = _InvalidNaming({1: ["For loop"], 2: ["While loop"]})

    with pytest.raises(InvalidLLMResponseError, match=r"grupo \['For loop', 'While loop'\],"):
        _generate(llm, [1, 2], {"For loop": 0, "While loop": 0})


def test_names_are_deduplicated_by_the_exact_text(data_root):
    # Só o texto idêntico entra uma vez, e a caixa ou um espaço a mais fazem outro nome
    llm = _ScriptedLLM({1: ["Loop", "loop", "For loop"], 2: ["Loop", "Loop "]})
    group_of = {"Loop": 0, "loop": 0, "For loop": 0, "Loop ": 1}

    generated = _generate(llm, [1, 2], group_of)

    assert list(generated.group_of_name) == ["Loop", "loop", "For loop", "Loop "]
    # O grupo de um KC só guarda o nome como veio, só que em minúsculas
    assert sorted(generated.group_names.values()) == ["loop", "loop "]


def test_the_evidence_points_to_the_sampled_solution_and_its_lines(data_root):
    # O LLM falso aponta a primeira linha da solução 1 para cada conceito
    llm = _ScriptedLLM({1: ["For loop"], 2: ["String length"]})

    generated = _generate(llm, [1, 2], {"For loop": 0, "String length": 0})

    assert generated.evidence == {
        1: [{"group": 0, "position": 1, "first_line": 1, "last_line": 1}],
        2: [{"group": 0, "position": 1, "first_line": 1, "last_line": 1}],
    }


class _SnippetOutsideTheCode(_ScriptedLLM):
    # O pedido dos trechos recebe um trecho que não está em solução nenhuma
    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        if prompt.startswith("# Knowledge components:"):
            return {"KC 1": {"solution": 1, "snippet": "while (true) { }"}}
        return super().generate(system, prompt, schema, validate)


def test_a_snippet_that_is_not_in_the_solution_is_dropped(data_root):
    generated = _generate(_SnippetOutsideTheCode({1: ["For loop"]}), [1], {"For loop": 0})

    assert generated.evidence == {1: []}
    # O conceito continua, só sem trecho
    assert generated.groups_by_problem == {1: [0]}


class _CountingTranslations(_ScriptedLLM):
    def __init__(self, names_by_problem: dict[int, list[str]]) -> None:
        super().__init__(names_by_problem)
        self.translation_prompts: list[str] = []

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        if prompt.startswith("# Names:"):
            self.translation_prompts.append(prompt)
        return super().generate(system, prompt, schema, validate)


def test_the_names_and_the_reasonings_come_translated_in_one_call(data_root):
    names = {1: ["For loop"], 2: ["For loop", "String length"], 3: ["While loop"]}
    llm = _CountingTranslations(names)

    generated = _generate(llm, [1, 2, 3], {"For loop": 0, "String length": 1, "While loop": 0})

    assert len(llm.translation_prompts) == 1
    assert generated.translated_group_names == {
        group: f"pt {name}" for group, name in generated.group_names.items()
    }
    reasonings = {kc["translated_reasoning"] for kcs in generated.candidate_kcs.values() for kc in kcs}
    assert reasonings == {"pt r"}


# Quatro nomes únicos dão 2 grupos, os laços e os textos, e cada problema tem os seus
_MARKED_NAMES = {
    1: ["For loop", "String length", "While loop", "Array index"],
    2: ["String length", "Array index"],
    3: ["For loop", "While loop"],
}
_MARKED_GROUPS = {"For loop": 0, "While loop": 0, "String length": 1, "Array index": 1}


def _generate_marked(llm):
    return KcGenKtGenerator(
        llm, embed=fake_embed, embed_names=_embed_by_group(_MARKED_GROUPS)
    ).generate(
        multiline_runs([1, 2, 3]),
        {},
        1,
        1,
        on_stage=lambda stage: None,
        on_progress=lambda done, total: None,
    )


def test_the_evidence_of_each_concept_is_the_lines_of_its_own_snippet(data_root):
    generated = _generate_marked(MarkedCodeLLM(_MARKED_NAMES))

    runs = multiline_runs([1, 2, 3])
    code_of = dict(zip(runs["submission_id"], runs["code"]))
    assert generated.group_names == {0: "for loop", 1: "string length"}
    assert generated.groups_by_problem == {1: [0, 1], 2: [1], 3: [0]}
    for problem, items in generated.evidence.items():
        sampled = [code_of[i] for i in generated.sampled_solutions[problem]]
        for item in items:
            mark = FOR_MARK if generated.group_names[item["group"]] == "for loop" else LENGTH_MARK
            position = max(k for k, code in enumerate(sampled, 1) if mark in code)
            lines = sampled[position - 1].split("\r\n")
            first = next(j for j, line in enumerate(lines) if mark in line) + 1
            assert (item["position"], item["first_line"], item["last_line"]) == (
                position,
                first,
                first + 1,
            )
    assert {p: [i["group"] for i in items] for p, items in generated.evidence.items()} == {
        1: [0, 1],
        2: [1],
        3: [0],
    }
    # No problema 1 os dois conceitos apontam solução e linha diferentes, então uma troca aparece
    assert len({(i["position"], i["first_line"]) for i in generated.evidence[1]}) == 2


def test_each_evidence_request_has_only_the_concepts_and_the_solutions_of_its_problem(data_root):
    llm = MarkedCodeLLM(_MARKED_NAMES)

    generated = _generate_marked(llm)

    runs = multiline_runs([1, 2, 3])
    code_of = dict(zip(runs["submission_id"], runs["code"]))
    requests = {}
    for prompt in llm.evidence_prompts:
        solutions = evidence_solutions(prompt)
        problem = int(re.search(r"public int p(\d+)v", solutions[0]).group(1))
        requests[problem] = (evidence_concepts(prompt), solutions)
    assert {p: concepts for p, (concepts, _) in requests.items()} == {
        1: ["for loop", "string length"],
        2: ["string length"],
        3: ["for loop"],
    }
    for problem, (_, solutions) in requests.items():
        assert solutions == [code_of[i] for i in generated.sampled_solutions[problem]]


class _InvalidEvidenceForProblemTwo(MarkedCodeLLM):
    # O pedido dos trechos do problema 2 recebe sempre uma solução que não existe
    def __init__(self, names_by_problem: dict[int, list[str]]) -> None:
        super().__init__(names_by_problem)
        self.invalid_calls = 0

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        if prompt.startswith("# Knowledge components:") and "public int p2v" in prompt:
            self.invalid_calls += 1
            return {"KC 1": {"solution": 99, "snippet": "x"}}
        return super().generate(system, prompt, schema, validate)


def test_an_invalid_evidence_answer_is_asked_three_times_and_names_its_problem(
    data_root, monkeypatch
):
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    llm = _InvalidEvidenceForProblemTwo(_MARKED_NAMES)

    with pytest.raises(InvalidLLMResponseError, match="problema 2, KC 1 aponta uma solução"):
        _generate_marked(llm)

    assert llm.invalid_calls == 3
    cache = json.loads(next(data_root.rglob("kc_cache.json")).read_text())
    assert all('"solution": 99' not in json.dumps(record["parsed"]) for record in cache.values())


class _InvalidTranslation(MarkedCodeLLM):
    # A tradução volta sempre com um texto só
    def __init__(self, names_by_problem: dict[int, list[str]]) -> None:
        super().__init__(names_by_problem)
        self.invalid_calls = 0

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        if prompt.startswith("# Names:"):
            self.invalid_calls += 1
            return {"N1": "só um"}
        return super().generate(system, prompt, schema, validate)


def test_an_invalid_translation_is_asked_three_times_then_stops(data_root, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    llm = _InvalidTranslation(_MARKED_NAMES)

    with pytest.raises(InvalidLLMResponseError, match="tradução"):
        _generate_marked(llm)

    assert llm.invalid_calls == 3


def test_a_second_extraction_reads_the_evidence_and_the_translation_from_the_cache(data_root):
    first = MarkedCodeLLM(_MARKED_NAMES)
    _generate_marked(first)
    assert (len(first.evidence_prompts), len(first.translation_prompts)) == (3, 1)

    second = MarkedCodeLLM(_MARKED_NAMES)
    _generate_marked(second)

    assert (second.evidence_prompts, second.translation_prompts) == ([], [])


def test_each_translation_goes_back_to_its_own_concept_and_candidate(data_root):
    generated = _generate_marked(MarkedCodeLLM(_MARKED_NAMES))

    assert generated.translated_group_names == {
        group: f"pt {name}" for group, name in generated.group_names.items()
    }
    candidates = [kc for kcs in generated.candidate_kcs.values() for kc in kcs]
    assert all(kc["translated_reasoning"] == f"pt {kc['reasoning']}" for kc in candidates)
    # Cada justificativa tem o problema no texto, então uma troca de ordem apareceria
    assert len({kc["reasoning"] for kc in candidates}) == 8
