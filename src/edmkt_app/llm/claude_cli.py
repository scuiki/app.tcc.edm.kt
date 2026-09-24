"""Transporte LLM headless via subscription (KC-01, D-01) — VERIFICADO AO VIVO.

`call_claude` invoca o binário `claude` em modo print (`-p`) via `subprocess.run` em list-form,
restringe a saída por `--json-schema` e desabilita todo tool, depois parseia
`envelope.structured_output` (o contrato confirmado ao vivo em 05-RESEARCH §Pattern 1).
`ClaudeCLIClient` adapta isso ao `edmkt_core.kc.ports.LLMClient` Protocol (DIP). O SDK
`anthropic` NUNCA é importado: a auth é a credencial OAuth de subscription resolvida pelo CLI.

A classificação de falhas (`TransientLLMError` vs `EmptyContentError`) e o retry com backoff
limitado vivem em `validation.py`.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

from edmkt_app.llm.validation import EmptyContentError, TransientLLMError

# Tarefa de texto pura: sem nenhum tool o LLM não faz I/O (não vaza arquivo/credencial) nem infla
# latência — fecha também a injeção de prompt via código de aluno (T-05-03).
DISALLOWED_TOOLS = "Bash,Read,Edit,Write,WebSearch,WebFetch,Glob,Grep"

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # pin científico (fidelidade TCC 1); não o alias `haiku`


def _neutral_cwd() -> str:
    # `claude` carrega o CLAUDE.md do cwd no contexto; rodar dentro do repo inflaria cada chamada
    # com o nosso CLAUDE.md inteiro (Pitfall 1). EDMKT_KC_CWD permite fixar um dir neutro no deploy;
    # default = tempdir do SO, sem CLAUDE.md.
    return os.environ.get("EDMKT_KC_CWD") or tempfile.gettempdir()


def _parse_json_from_text(text: str) -> dict:
    # Fallback defensivo SÓ quando structured_output vem ausente: extrai o JSON de uma cerca
    # markdown (```json ... ```) ou do primeiro objeto {...} no texto cru.
    if not text:
        raise EmptyContentError("envelope sem structured_output e result vazio")
    fence = "```json"
    if fence in text:
        body = text.split(fence, 1)[1].split("```", 1)[0]
    elif "```" in text:
        body = text.split("```", 1)[1].split("```", 1)[0]
    else:
        start, end = text.find("{"), text.rfind("}")
        body = text[start : end + 1] if start != -1 and end > start else text
    try:
        return json.loads(body.strip())
    except json.JSONDecodeError as exc:
        raise EmptyContentError(f"result não-JSON: {exc}") from exc


def call_claude(
    system: str,
    prompt: str,
    schema: dict,
    model: str = _DEFAULT_MODEL,
    timeout_s: int = 120,
) -> dict:
    """Chama `claude -p` uma vez e devolve a saída estruturada validada por schema.

    Levanta TransientLLMError em exit≠0 / is_error / subtype≠success (retentável); o conteúdo
    vazio/malformado vira EmptyContentError (falha-dura, NÃO retentável).
    """
    argv = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--model",
        model,
        "--system-prompt",  # substitui o prompt default; nunca o modo bare (forçaria ANTHROPIC_API_KEY, quebra D-01)
        system,
        "--json-schema",
        json.dumps(schema),
        "--disallowedTools",
        DISALLOWED_TOOLS,
    ]
    try:
        # list-form, sem shell — fecha command injection (T-05-CMD); espelha training.py:62.
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=_neutral_cwd(),
        )
    except subprocess.TimeoutExpired as exc:
        raise TransientLLMError(f"claude timeout após {timeout_s}s") from exc

    if proc.returncode != 0:
        raise TransientLLMError(proc.stderr.strip() or f"claude exit {proc.returncode}")

    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise TransientLLMError(f"stdout do claude não-JSON: {exc}") from exc

    if env.get("is_error") or env.get("subtype") != "success":
        raise TransientLLMError(env.get("result", "claude error"))

    out = env.get("structured_output")
    if out is None:
        out = _parse_json_from_text(env.get("result", ""))
    return out


class ClaudeCLIClient:
    """Adapta `call_claude` ao `edmkt_core.kc.ports.LLMClient` Protocol (DIP).

    O core puro recebe um LLMClient injetado e nunca toca subprocess/anthropic; trocar o
    transporte (ex.: mock nos testes) é trocar a instância.
    """

    def __init__(self, model: str = _DEFAULT_MODEL, timeout_s: int = 120) -> None:
        self._model = model
        self._timeout_s = timeout_s

    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        return call_claude(
            system=system,
            prompt=prompt,
            schema=schema,
            model=self._model,
            timeout_s=self._timeout_s,
        )

