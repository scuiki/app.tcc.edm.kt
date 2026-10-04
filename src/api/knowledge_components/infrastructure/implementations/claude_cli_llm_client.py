# O LLM pela assinatura, o binário `claude` em modo print (`-p`), nunca o SDK `anthropic`.
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Callable

from api.knowledge_components.infrastructure.implementations.llm_call_retry import (
    TransientLLMError,
)
from ml.kc_generation.llm_client import InvalidLLMResponseError

# O tempo limite de uma chamada, folgado para uma resposta lenta não virar outra tentativa
CALL_TIMEOUT_S = 300


def _neutral_cwd() -> str:
    # EDMKT_KC_CWD fixa um dir neutro para não carregar o CLAUDE.md do repo em cada chamada.
    return os.environ.get("EDMKT_KC_CWD") or tempfile.gettempdir()


def _parse_json_from_text(text: str) -> dict:
    # Sem structured_output, a resposta é o último objeto JSON não vazio do texto, com ou sem cerca
    decoder = json.JSONDecoder()
    last: dict | None = None
    position = text.find("{")
    while position != -1:
        try:
            value, end = decoder.raw_decode(text, position)
        except json.JSONDecodeError:
            position = text.find("{", position + 1)
            continue
        if value:
            last = value
        # A busca segue depois do objeto inteiro, para um objeto de dentro dele não virar a resposta
        position = text.find("{", end)
    if last is None:
        raise InvalidLLMResponseError("a resposta não traz um objeto JSON")
    return last


def call_claude(
    system: str,
    prompt: str,
    model: str,
    schema: dict | None = None,
    timeout_s: int = CALL_TIMEOUT_S,
) -> dict:
    # `model` vem de quem chama, a versão fixada é decisão dele, este transporte não escolhe modelo.
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
        # Sem ferramenta nenhuma o LLM não faz I/O, e o contexto cai de 10 mil tokens para mil
        "--tools",
        "",
        # Nenhum servidor MCP do host sobe a cada chamada, e nenhuma sessão fica gravada em disco
        "--strict-mcp-config",
        "--no-session-persistence",
    ]
    # Sem schema, o JSON vem no texto da resposta, como os prompts do Duan pedem
    if schema is not None:
        argv += ["--json-schema", json.dumps(schema)]
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
        out = _parse_json_from_text(env.get("result") or "")
    return out


# LLMClient (interface do ml/kc_generation) sobre `claude -p`, injeção troca o transporte.
class ClaudeCliLLMClient:
    def __init__(self, model: str, timeout_s: int = CALL_TIMEOUT_S) -> None:
        self._model = model
        self._timeout_s = timeout_s

    def generate(
        self,
        system: str,
        prompt: str,
        schema: dict | None = None,
        validate: Callable[[dict], object] | None = None,
    ) -> dict:
        response = call_claude(
            system=system,
            prompt=prompt,
            model=self._model,
            schema=schema,
            timeout_s=self._timeout_s,
        )
        # Aqui a validação só recusa, e quem pede de novo e guarda é o CachedLLMClient
        if validate is not None:
            validate(response)
        return response

