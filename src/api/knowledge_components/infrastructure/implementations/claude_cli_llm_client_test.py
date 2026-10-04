# call_claude roda `claude -p`; o subprocess é sempre substituído, nenhum teste gasta cota real.
from __future__ import annotations

import json
import subprocess

import pytest

from api.knowledge_components.infrastructure.implementations.claude_cli_llm_client import (
    ClaudeCliLLMClient,
    call_claude,
)
from api.knowledge_components.infrastructure.implementations.llm_call_retry import (
    TransientLLMError,
)
from api.knowledge_components.infrastructure.implementations.kc_generation_model import (
    KC_GENERATION_MODEL_ID as MODEL_ID,
)
from api.knowledge_components.infrastructure.implementations.llm_response_cache import (
    CachedLLMClient,
)
from ml.kc_generation.candidate_generation import generate_candidate_kcs
from ml.kc_generation.llm_client import InvalidLLMResponseError

_SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
}
_PARSED = {"KC 1": {"reasoning": "usa for", "name": "laços"}}


# Stand-in de subprocess.CompletedProcess sem spawnar processo, claude real nunca roda.
class _FakeCompleted:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _patch_run(monkeypatch, completed, capture):
    def _fake_run(args, *a, **kw):
        capture["args"] = args
        capture["kwargs"] = kw
        return completed

    monkeypatch.setattr(subprocess, "run", _fake_run)


def test_returns_structured_output(monkeypatch, fake_claude_envelope):
    capture: dict = {}
    env = fake_claude_envelope(_PARSED)
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    out = call_claude(model=MODEL_ID, system="sys", prompt="prompt", schema=_SCHEMA)

    assert out == _PARSED


def test_invokes_list_form_claude_print_with_schema(monkeypatch, fake_claude_envelope):
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(fake_claude_envelope(_PARSED))), capture)

    call_claude(model=MODEL_ID, system="SYS", prompt="P", schema=_SCHEMA)

    args = capture["args"]
    # list-form de str puras, sem shell=True e sem interpolação, fecha command injection.
    assert isinstance(args, list)
    assert all(isinstance(a, str) for a in args)
    assert args[0] == "claude"
    assert "-p" in args
    assert json.loads(args[args.index("--json-schema") + 1]) == _SCHEMA
    # Nenhuma ferramenta disponível, o que também fecha a injeção de prompt via código de aluno
    assert args[args.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in args
    assert "--no-session-persistence" in args
    # --bare força ANTHROPIC_API_KEY e pula a autenticação OAuth da assinatura, nunca presente.
    assert "--bare" not in args
    # shell=True nunca é passado ao subprocess.run.
    assert capture["kwargs"].get("shell") is not True


def test_nonzero_exit_raises_transient(monkeypatch):
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stderr="boom", returncode=1), capture)

    with pytest.raises(TransientLLMError):
        call_claude(model=MODEL_ID, system="s", prompt="p", schema=_SCHEMA)


def test_is_error_envelope_raises_transient(monkeypatch):
    capture: dict = {}
    env = {"type": "result", "subtype": "success", "is_error": True, "result": "rate limited"}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    with pytest.raises(TransientLLMError):
        call_claude(model=MODEL_ID, system="s", prompt="p", schema=_SCHEMA)


def test_non_success_subtype_raises_transient(monkeypatch):
    capture: dict = {}
    env = {"type": "result", "subtype": "error_max_turns", "is_error": False, "result": "x"}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    with pytest.raises(TransientLLMError):
        call_claude(model=MODEL_ID, system="s", prompt="p", schema=_SCHEMA)


def test_empty_structured_output_is_recognized(monkeypatch, fake_claude_envelope):
    # structured_output vazio, o transporte só não pode inventar dado nem mascarar erro.
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(fake_claude_envelope({}))), capture)

    # Resposta inválida ou {} para a validação a jusante decidir, ambos aceitáveis.
    try:
        out = call_claude(model=MODEL_ID, system="s", prompt="p", schema=_SCHEMA)
        assert out == {}
    except InvalidLLMResponseError:
        pass


def test_without_a_schema_the_json_comes_from_the_text(monkeypatch, fake_claude_envelope):
    # Os prompts do Duan pedem o JSON no texto, e a CLI não recebe schema nenhum
    capture: dict = {}
    text = "```json\n" + json.dumps(_PARSED) + "\n```"
    env = fake_claude_envelope(None, result=text)
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    out = call_claude(model=MODEL_ID, system="s", prompt="p")

    assert out == _PARSED
    assert "--json-schema" not in capture["args"]


def test_a_text_that_is_not_json_is_an_invalid_response(monkeypatch, fake_claude_envelope):
    capture: dict = {}
    env = fake_claude_envelope(None, result="Os KCs são laços e condicionais.")
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    with pytest.raises(InvalidLLMResponseError):
        call_claude(model=MODEL_ID, system="s", prompt="p")


def test_a_call_waits_up_to_five_minutes(monkeypatch, fake_claude_envelope):
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(fake_claude_envelope(_PARSED))), capture)

    ClaudeCliLLMClient(model=MODEL_ID).generate("s", "p")

    assert capture["kwargs"]["timeout"] == 300


def test_the_client_refuses_a_response_the_validation_rejects(monkeypatch, fake_claude_envelope):
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(fake_claude_envelope(_PARSED))), capture)

    def reject(response: dict) -> None:
        raise InvalidLLMResponseError("fora do formato")

    with pytest.raises(InvalidLLMResponseError):
        ClaudeCliLLMClient(model=MODEL_ID).generate("s", "p", validate=reject)


_JSON = json.dumps(_PARSED)


@pytest.mark.parametrize(
    "text",
    [
        _JSON,
        "```json\n" + _JSON + "\n```",
        "```JSON\n" + _JSON + "\n```",
        "A análise.\n```java\nint f() { return 1; }\n```\n```\n" + _JSON + "\n```",
        "Os laços usam { e }, como em while (x) { x--; }.\n" + _JSON,
        _JSON + "\nAs chaves {} ficam de fora.",
        '```json\n{"rascunho": 1}\n```\n```json\n' + _JSON + "\n```",
    ],
    ids=[
        "json_puro",
        "cerca_json",
        "cerca_maiuscula",
        "java_antes_e_cerca_sem_linguagem",
        "chaves_na_analise_e_json_sem_cerca",
        "chaves_depois_do_json",
        "dois_blocos_vale_o_ultimo",
    ],
)
def test_the_answer_is_the_last_json_object_of_the_text(monkeypatch, fake_claude_envelope, text):
    capture: dict = {}
    env = fake_claude_envelope(None, result=text)
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    assert call_claude(model=MODEL_ID, system="s", prompt="p") == _PARSED


def test_a_text_without_json_is_asked_again_through_the_cache(
    monkeypatch, fake_claude_envelope, tmp_path
):
    # A segunda resposta traz uma análise antes do JSON, como a do Sonnet sem enunciado
    texts = iter(["Os KCs são laços.", "Análise.\n```json\n" + _JSON + "\n```"])
    argvs: list[list[str]] = []

    def _fake_run(args, *a, **kw):
        argvs.append(args)
        return _FakeCompleted(stdout=json.dumps(fake_claude_envelope(None, result=next(texts))))

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    cached = CachedLLMClient(ClaudeCliLLMClient(model=MODEL_ID), tmp_path, stage="generate")

    candidates = generate_candidate_kcs(["int f() { return 1; }"], None, cached)

    assert candidates == [{"name": "laços", "reasoning": "usa for"}]
    assert len(argvs) == 2
    assert all("--json-schema" not in args for args in argvs)
