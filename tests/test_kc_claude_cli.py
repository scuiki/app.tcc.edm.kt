"""RED — transporte LLM headless via subscription (KC-01, D-01).

Pina o contrato de `edmkt_app.llm.claude_cli.call_claude`: invoca `claude -p` em list-form
(NUNCA shell=True / NUNCA --bare — quebraria a auth OAuth de subscription), parseia o campo
`structured_output` do envelope JSON verificado ao vivo (RESEARCH §Pattern 1), e classifica
exit≠0 / is_error / subtype≠success como TransientLLMError. TODO o subprocess é monkeypatchado
— nenhum teste chama o binário `claude` real nem gasta cota (T-05-01, DoS).

Wave 0: o módulo alvo ainda não existe → estes testes FALHAM RED (ImportError) e viram o
gate GREEN da Wave 1.
"""

from __future__ import annotations

import json
import subprocess

import pytest

# RED: edmkt_app.llm.claude_cli não existe ainda (gate da Wave 1).
from edmkt_app.llm.claude_cli import (  # noqa: E402
    EmptyContentError,
    TransientLLMError,
    call_claude,
)

_SCHEMA = {
    "type": "object",
    "properties": {"kcs": {"type": "array", "items": {"type": "object"}}},
    "required": ["kcs"],
}
_PARSED = {"problem_description": "soma", "kcs": [{"name": "laços", "reasoning": "usa for"}]}


class _FakeCompleted:
    """Stand-in de subprocess.CompletedProcess sem spawnar processo (claude real nunca roda)."""

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

    out = call_claude(system="sys", prompt="prompt", schema=_SCHEMA)

    assert out == _PARSED


def test_invokes_list_form_claude_print_with_schema(monkeypatch, fake_claude_envelope):
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(fake_claude_envelope(_PARSED))), capture)

    call_claude(system="SYS", prompt="P", schema=_SCHEMA)

    args = capture["args"]
    # list-form de str puras (sem shell=True / sem interpolação — T-05-02 command injection).
    assert isinstance(args, list)
    assert all(isinstance(a, str) for a in args)
    assert args[0] == "claude"
    assert "-p" in args
    assert "--json-schema" in args
    assert "--disallowedTools" in args
    # --bare força ANTHROPIC_API_KEY e pula OAuth → quebraria D-01. NUNCA presente.
    assert "--bare" not in args
    # shell=True nunca é passado ao subprocess.run.
    assert capture["kwargs"].get("shell") is not True


def test_nonzero_exit_raises_transient(monkeypatch):
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stderr="boom", returncode=1), capture)

    with pytest.raises(TransientLLMError):
        call_claude(system="s", prompt="p", schema=_SCHEMA)


def test_is_error_envelope_raises_transient(monkeypatch):
    capture: dict = {}
    env = {"type": "result", "subtype": "success", "is_error": True, "result": "rate limited"}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    with pytest.raises(TransientLLMError):
        call_claude(system="s", prompt="p", schema=_SCHEMA)


def test_non_success_subtype_raises_transient(monkeypatch):
    capture: dict = {}
    env = {"type": "result", "subtype": "error_max_turns", "is_error": False, "result": "x"}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(env)), capture)

    with pytest.raises(TransientLLMError):
        call_claude(system="s", prompt="p", schema=_SCHEMA)


def test_empty_structured_output_is_recognized(monkeypatch, fake_claude_envelope):
    """Envelope success mas com structured_output vazio/sem 'kcs' → o transporte não pode
    devolver silenciosamente algo inválido (a validação de conteúdo é exercida em
    test_kc_validation; aqui só garantimos que o transporte não inventa dados)."""
    capture: dict = {}
    _patch_run(monkeypatch, _FakeCompleted(stdout=json.dumps(fake_claude_envelope({}))), capture)

    # Conteúdo vazio é falha-dura (EmptyContentError) OU devolve {} para a validação a jusante
    # decidir — qualquer um dos dois é aceitável; o que NÃO pode é mascarar como sucesso pleno.
    try:
        out = call_claude(system="s", prompt="p", schema=_SCHEMA)
        assert out == {} or out == {"kcs": []}
    except EmptyContentError:
        pass
