# Cache das respostas do LLM, chaveado pelo hash de tudo que determina a resposta.
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Callable

from api.knowledge_components.infrastructure.implementations.kc_generation_model import (
    KC_GENERATION_MODEL_ID,
    PROMPT_VERSION,
)
from api.knowledge_components.infrastructure.implementations.llm_call_retry import call_with_retry
from ml.kc_generation.llm_client import InvalidLLMResponseError, LLMClient

# Nome fixo no código, nunca string controlada pelo usuário, fecha path traversal.
_CACHE_FILENAME = "kc_cache.json"

# As chamadas ao LLM rodam em paralelo, e sem a trava duas gravações perderiam uma resposta
_FILE_LOCK = threading.Lock()


def kc_input_hash(
    model_id: str,
    prompt_version: str,
    payload: str,
    system: str = "",
    schema: dict | None = None,
) -> str:
    # Hash cobre tudo que decide a resposta (model, prompt_version, system, schema, payload).
    schema_repr = "" if schema is None else json.dumps(schema, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256()
    # NUL separa as partes, evita colisão tipo ("a","b") virar igual a ("ab","").
    h.update(
        b"\x00".join(
            part.encode("utf-8")
            for part in (model_id, prompt_version, system, schema_repr, payload)
        )
    )
    return h.hexdigest()


def _cache_file(base_path) -> Path:
    # Diretório vem de caller interno, nunca de upload; nome fixo e .resolve() fecham traversal.
    return (Path(base_path).resolve()) / _CACHE_FILENAME


def _load(base_path) -> dict:
    f = _cache_file(base_path)
    if not f.exists():
        return {}
    return json.loads(f.read_text())


def cache_get(base_path, *, problem_id: str, key: str) -> dict | None:
    # Registro de (problem_id, key), chave obsoleta vira miss e o caller re-chama o LLM.
    with _FILE_LOCK:
        store = _load(base_path)
    record = store.get(str(problem_id))
    if record is None:
        return None
    # input_hash divergente é de outro modelo ou prompt, vira miss e não devolve resposta velha.
    if record.get("input_hash") not in (None, key):
        return None
    return record


def cache_put(base_path, *, problem_id: str, key: str, record: dict) -> None:
    # Grava só a entrada de `problem_id`, read-modify-write do arquivo inteiro, preserva as irmãs.
    f = _cache_file(base_path)
    f.parent.mkdir(parents=True, exist_ok=True)
    # Garante o input_hash mesmo sem o caller passar, cache_get usa pra achar entrada obsoleta.
    record = {"input_hash": key, **record}
    with _FILE_LOCK:
        store = _load(base_path)
        store[str(problem_id)] = record
        # Ordena só as entradas, porque a ordem das chaves de uma resposta é a ordem dos KCs dela
        f.write_text(json.dumps(dict(sorted(store.items())), ensure_ascii=False, indent=2))


def _passes(validate: Callable[[dict], object] | None, response: dict) -> bool:
    # Sem validação toda resposta passa, e com ela só a que não levanta InvalidLLMResponseError
    if validate is None:
        return True
    try:
        validate(response)
    except InvalidLLMResponseError:
        return False
    return True


# LLMClient com cache e retry, resposta já paga não é pedida de novo.
class CachedLLMClient:
    def __init__(self, llm: LLMClient, cache_dir: Path, stage: str) -> None:
        self._llm = llm
        self._cache_dir = cache_dir
        self._stage = stage  # generate, label, evidence ou translate, sem colisão entre as etapas

    def generate(
        self,
        system: str,
        prompt: str,
        schema: dict | None = None,
        validate: Callable[[dict], object] | None = None,
    ) -> dict:
        key = kc_input_hash(
            KC_GENERATION_MODEL_ID, PROMPT_VERSION, prompt, system=system, schema=schema
        )
        cache_id = f"{self._stage}:{key}"
        cached = cache_get(self._cache_dir, problem_id=cache_id, key=key)
        # Uma resposta guardada que a validação de hoje recusa é pedida de novo e trocada no cache
        if cached is not None and _passes(validate, cached["parsed"]):
            return cached["parsed"]

        def ask() -> dict:
            response = self._llm.generate(system, prompt, schema)
            # A resposta inválida levanta aqui, é pedida de novo e nunca chega ao cache
            if validate is not None:
                validate(response)
            return response

        parsed = call_with_retry(ask)
        cache_put(
            self._cache_dir,
            problem_id=cache_id,
            key=key,
            record={
                "model_id": KC_GENERATION_MODEL_ID,
                "prompt_version": PROMPT_VERSION,
                "parsed": parsed,
            },
        )
        return parsed
