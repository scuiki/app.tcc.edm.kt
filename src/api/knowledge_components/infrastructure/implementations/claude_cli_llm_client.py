# O LLM pela assinatura, o binário `claude` em modo print (`-p`), nunca o SDK `anthropic`.
from __future__ import annotations

import json
import os
import subprocess
import tempfile

from api.knowledge_components.infrastructure.implementations.llm_call_retry import (
    EmptyContentError,
    TransientLLMError,
)

# Sem tool nenhum o LLM não faz I/O, o que também fecha a injeção de prompt via código de aluno.
DISALLOWED_TOOLS = "Bash,Read,Edit,Write,WebSearch,WebFetch,Glob,Grep"


def _neutral_cwd() -> str:
    # EDMKT_KC_CWD fixa um dir neutro para não carregar o CLAUDE.md do repo em cada chamada.
    return os.environ.get("EDMKT_KC_CWD") or tempfile.gettempdir()


def _parse_json_from_text(text: str) -> dict:
    # Fallback só quando structured_output vem ausente, extrai o JSON da cerca markdown ou o cru.
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
    model: str,
    timeout_s: int = 120,
) -> dict:
    # `model` vem de quem chama, o pin científico é dele, este transporte não escolhe modelo.
    argv = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--model",
        model,
        "--system-prompt",  # substitui o prompt default; nunca bare, que exigiria ANTHROPIC_API_KEY
        system,
        "--json-schema",
        json.dumps(schema),
        "--disallowedTools",
        DISALLOWED_TOOLS,
    ]
    try:
        # list-form, sem shell, fecha command injection.
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


# LLMClient (interface do ml/kc_generation) sobre `claude -p`, injeção troca o transporte.
class ClaudeCliLLMClient:
    def __init__(self, model: str, timeout_s: int = 120) -> None:
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

