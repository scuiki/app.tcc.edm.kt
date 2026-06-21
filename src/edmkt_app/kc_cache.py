"""Cache fino do LLM keyed por hash de conteúdo (KC-04, D-02/D-03).

A chave é `sha256(model_id + prompt_version + payload)`: mesma entrada → mesma chave hex,
qualquer mudança → chave diferente. Um hit devolve o registro CRU cacheado sem invocar o
LLM. O cache é por-problema/por-cluster dentro de um arquivo `{ "<id>": {record} }`: gravar
o problema A não toca a entrada do problema B (D-02 — re-rodar 1 problema não invalida os
outros). Cada registro guarda a resposta CRUA + model_id + prompt_version + input_hash
(D-03 — o objeto científico reproduzível).

FS puro keyed por hash, espelhando a convenção blob-no-FS de `persistence/artifacts.py`. Sem
I/O de LLM e sem DB aqui: o caller faz get-or-call e, no miss, chama/valida/grava.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Identidade do cache (D-03): parte da chave, junto de model_id e do payload. Bump quando o
# prompt mudar — um prompt novo é uma entrada nova, não um hit do prompt antigo.
PROMPT_VERSION = "kcgen-v1"

# Nome do arquivo por-estágio sob o diretório de KC. Componente fixo do código, nunca string
# controlada pelo usuário (KC-04 path-traversal).
_CACHE_FILENAME = "kc_cache.json"


def kc_input_hash(model_id: str, prompt_version: str, payload: str) -> str:
    """sha256 hex de (model_id, prompt_version, payload) separados por NUL.

    O NUL separa as partes para que ("a","b") e ("ab","") não colidam. É identidade/dedup, não
    um segredo (V6 n/a) — só decide hit vs miss."""
    h = hashlib.sha256()
    h.update(b"\x00".join(p.encode("utf-8") for p in (model_id, prompt_version, payload)))
    return h.hexdigest()


def _cache_file(base_path) -> Path:
    # Diretório vem de um caller interno (slug/aid), nunca de upload; o arquivo é nome fixo —
    # sem traversal (KC-04). O .resolve() confina a leitura/escrita ao base resolvido.
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
    os irmãos independentes (D-02)."""
    store = _load(base_path)
    record = store.get(str(problem_id))
    if record is None:
        return None
    # input_hash divergente ⇒ a entrada é de uma identidade antiga (modelo/prompt/conteúdo
    # mudou): trata como miss para não devolver ciência desatualizada (D-03).
    if record.get("input_hash") not in (None, key):
        return None
    return record


def cache_put(base_path, *, problem_id: str, key: str, record: dict) -> None:
    """Grava/atualiza SÓ a entrada de `problem_id`, preservando as irmãs (D-02 isolation).

    Read-modify-write do arquivo `{id: record}` inteiro: lê o que existe, troca a única chave
    do problema e regrava. O registro carrega a resposta CRUA + identidade (D-03) — o objeto
    reproduzível que defende a tese."""
    f = _cache_file(base_path)
    f.parent.mkdir(parents=True, exist_ok=True)
    store = _load(base_path)
    # Garante o input_hash na identidade do registro mesmo se o caller não o passou — é o que
    # cache_get usa para detectar entrada obsoleta (D-03).
    record = {"input_hash": key, **record}
    store[str(problem_id)] = record
    f.write_text(json.dumps(store, ensure_ascii=False, sort_keys=True, indent=2))
