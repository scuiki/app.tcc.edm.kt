# Cache em disco dos AST paths (por turma), reaproveitado entre treino e inferência.

from __future__ import annotations

import pickle
from typing import Optional

from ml.code_dkt.ast_paths import extract_ast_paths_for_snapshots

from api.shared.infrastructure.filesystem import data_layout
from api.model_training.infrastructure.implementations.code_snapshot_id import CodeSnapshotId
from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug

def load_or_extract_ast_paths(
    classroom_slug: ClassroomSlug,
    all_snapshot_ids: list[str],
    code_by_snapshot: dict[str, str],
    config: dict,
    n_workers: Optional[int] = None,
) -> dict[str, list[tuple[str, str, str]]]:
    # Cache incremental crash-safe por turma; o filtro train-only ocorre depois, não vaza no vocab.
    cache_dir = data_layout.ast_path_cache_dir(classroom_slug)
    cache_dir.mkdir(parents=True, exist_ok=True)

    ast_paths_by_snapshot: dict[str, list[tuple[str, str, str]]] = {}
    missing: list[str] = []
    for snapshot_id in all_snapshot_ids:
        safe = CodeSnapshotId(snapshot_id)
        pkl = cache_dir / f"{safe}.pkl"
        if pkl.exists():
            ast_paths_by_snapshot[snapshot_id] = pickle.loads(pkl.read_bytes())
        else:
            missing.append(snapshot_id)

    if missing:
        fresh = extract_ast_paths_for_snapshots(
            missing,
            code_by_snapshot,
            max_path_length=config["max_path_length"],
            max_path_width=config["max_path_width"],
            R=config["R"],
            seed=config["seed"],
            n_workers=n_workers,
        )
        for snapshot_id, paths in fresh.items():
            safe = CodeSnapshotId(snapshot_id)
            tmp = cache_dir / f"{safe}.pkl.tmp"
            tmp.write_bytes(pickle.dumps(paths))
            tmp.rename(cache_dir / f"{safe}.pkl")
            ast_paths_by_snapshot[snapshot_id] = paths

    return ast_paths_by_snapshot
