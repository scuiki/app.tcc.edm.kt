"""O cache das respostas do LLM, chaveado pelo hash de tudo que determina a resposta.

Mesma entrada, mesma chave; qualquer mudança (modelo, versão do prompt, system, schema, conteúdo),
chave diferente. Cada entrada guarda a resposta CRUA + a identidade que a gerou: é o objeto
científico reproduzível, e é o que evita gastar cota da assinatura duas vezes. O cache é um JSON
por diretório, com uma entrada por problema/grupo: regravar um não invalida os outros.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from api.knowledge_components.infrastructure.llm_call_retry import call_with_retry
from ml.kc_generation.llm_client import LLMClient

# O modelo congelado do TCC 1: o id pinado, não o alias `haiku`, por fidelidade científica. Faz
# parte da chave do cache junto com a versão do prompt.
KC_GENERATION_MODEL_ID = "claude-haiku-4-5-20251001"

# Incremente quando o prompt mudar: um prompt novo é uma entrada nova, não um acerto do antigo.
PROMPT_VERSION = "kcgen-v1"

# Nome do arquivo por-estágio sob o diretório de KC. Componente fixo do código, nunca string
# controlada pelo usuário.
_CACHE_FILENAME = "kc_cache.json"


def kc_input_hash(
    model_id: str,
    prompt_version: str,
    payload: str,
    system: str = "",
    schema: dict | None = None,
) -> str:
    """sha256 hex de TUDO que determina a resposta, separado por NUL.

    O `system` e o `schema` entram na chave porque determinam a saída tanto quanto o payload —
    e o system é justamente onde moram as INSTRUÇÕES, a parte que mais muda. Sem eles, editar o
    prompt de sistema devolvia, em silêncio, a resposta gerada pelo prompt antigo; mudar o
    schema devolvia um parse que não batia com ele. A rede era lembrar de incrementar
    PROMPT_VERSION à mão — uma constante que depende de memória.

    O NUL separa as partes para que ("a","b") e ("ab","") não colidam. É identidade/dedup, não
    um segredo (V6 n/a) — só decide hit vs miss."""
    schema_repr = "" if schema is None else json.dumps(schema, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256()
    h.update(
        b"\x00".join(
            part.encode("utf-8")
            for part in (model_id, prompt_version, system, schema_repr, payload)
        )
    )
    return h.hexdigest()


def _cache_file(base_path) -> Path:
    # Diretório vem de um caller interno (slug/aid), nunca de upload; o arquivo é nome fixo —
    # sem traversal. O .resolve() confina a leitura/escrita ao base resolvido.
    return (Path(base_path).resolve()) / _CACHE_FILENAME


def _load(base_path) -> dict:
    f = _cache_file(base_path)
    if not f.exists():
        return {}
    return json.loads(f.read_text())


def cache_get(base_path, *, problem_id: str, key: str) -> dict | None:
    """Registro cacheado de (problem_id, key) ou None no miss.

    Checa a entrada por-id (NÃO a existência do arquivo) e que o `input_hash` gravado bate com
    `key` — uma chave obsoleta vira miss, então o caller re-chama o LLM. Lookup por-id mantém
    os irmãos independentes."""
    store = _load(base_path)
    record = store.get(str(problem_id))
    if record is None:
        return None
    # input_hash divergente ⇒ a entrada é de uma identidade antiga (modelo/prompt/conteúdo
    # mudou): trata como miss para não devolver ciência desatualizada.
    if record.get("input_hash") not in (None, key):
        return None
    return record


def cache_put(base_path, *, problem_id: str, key: str, record: dict) -> None:
    """Grava/atualiza SÓ a entrada de `problem_id`, preservando as irmãs.

    Read-modify-write do arquivo `{id: record}` inteiro: lê o que existe, troca a única chave
    do problema e regrava. O registro carrega a resposta CRUA + identidade — o objeto
    reproduzível que defende a tese."""
    f = _cache_file(base_path)
    f.parent.mkdir(parents=True, exist_ok=True)
    store = _load(base_path)
    # Garante o input_hash na identidade do registro mesmo se o caller não o passou — é o que
    # cache_get usa para detectar entrada obsoleta.
    record = {"input_hash": key, **record}
    store[str(problem_id)] = record
    f.write_text(json.dumps(store, ensure_ascii=False, sort_keys=True, indent=2))


class CachedLLMClient:
    """LLMClient com cache e retry: uma resposta já paga não é pedida de novo.

    Cada `generate` deriva a chave do (modelo, versão do prompt, system, schema, prompt) e consulta
    o cache antes de chamar; um acerto pula a chamada. Só o erro transiente é repetido.
    """

    def __init__(self, llm: LLMClient, cache_dir: Path, stage: str) -> None:
        self._llm = llm
        self._cache_dir = cache_dir
        self._stage = stage  # generate | label: o mesmo prompt em etapas diferentes não colide

    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        key = kc_input_hash(
            KC_GENERATION_MODEL_ID, PROMPT_VERSION, prompt, system=system, schema=schema
        )
        cache_id = f"{self._stage}:{key}"
        cached = cache_get(self._cache_dir, problem_id=cache_id, key=key)
        if cached is not None:
            return cached["parsed"]

        parsed = call_with_retry(lambda: self._llm.generate(system, prompt, schema))
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
