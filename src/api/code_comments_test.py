# A regra dos comentários, verificada em todo o Python, nos testes e nas migrations SQL.

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PYTHON_FILES = sorted(
    f
    for folder in ("src/api", "src/ml", "tests")
    for f in (ROOT / folder).rglob("*.py")
    if "__pycache__" not in f.parts
) + [ROOT / "conftest.py"]
SQL_FILES = sorted((ROOT / "src/api").rglob("*.sql"))
MAX_LINE = 100

# Pragmas de ferramenta precisam do dois-pontos para funcionar
_PRAGMA = re.compile(r"\b(noqa|type:\s*ignore|pragma:)")


def _text_problems(text: str) -> list[str]:
    # Trechos de código entre crases e URLs podem ter dois-pontos
    prose = re.sub(r"`[^`]*`|\w+://\S+", "", text)
    problems = []
    if "—" in prose or "–" in prose:
        problems.append("travessão")
    if ":" in prose and not _PRAGMA.search(prose):
        problems.append("dois-pontos")
    return problems


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


@pytest.mark.parametrize("path", PYTHON_FILES, ids=_relative)
def test_python_comments_follow_the_rule(path):
    source = path.read_text()
    problems = []

    for node in ast.walk(ast.parse(source)):
        is_container = isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
        if is_container and ast.get_docstring(node, clean=False) is not None:
            problems.append(f"linha {getattr(node, 'lineno', 1)} docstring, use um comentário #")

    lines = source.splitlines()
    previous_comment_only = None
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        row = token.start[0]
        comment_only = lines[row - 1].lstrip().startswith("#")
        if comment_only and previous_comment_only == row - 1:
            problems.append(f"linha {row} comentário em mais de uma linha")
        if comment_only:
            previous_comment_only = row
        problems += [f"linha {row} {p}" for p in _text_problems(token.string)]
        if len(lines[row - 1]) > MAX_LINE:
            problems.append(f"linha {row} passa de {MAX_LINE} colunas")

    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("path", SQL_FILES, ids=_relative)
def test_sql_comments_follow_the_rule(path):
    problems = []
    previous = None
    for row, line in enumerate(path.read_text().splitlines(), start=1):
        if "--" not in line:
            continue
        comment = line[line.index("--") + 2 :]
        if line.lstrip().startswith("--") and previous == row - 1:
            problems.append(f"linha {row} comentário em mais de uma linha")
        if line.lstrip().startswith("--"):
            previous = row
        problems += [f"linha {row} {p}" for p in _text_problems(comment)]
        if len(line) > MAX_LINE:
            problems.append(f"linha {row} passa de {MAX_LINE} colunas")
    assert not problems, "\n".join(problems)
