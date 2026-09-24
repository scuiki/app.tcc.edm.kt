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
WEB = ROOT / "src/web"
# O schema.d.ts é gerado pelo openapi-typescript e nunca editado à mão
WEB_FILES = sorted(
    f
    for pattern in ("src/**/*.ts", "src/**/*.tsx", "src/**/*.css", "*.ts", "*.js")
    for f in WEB.glob(pattern)
    if f.name != "schema.d.ts"
)
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


# No TypeScript, uma barra depois destes caracteres abre uma regex e não uma divisão
_REGEX_STARTS_AFTER = set("(,=:[!&|?{};+-*%~^")
_WEB_PRAGMA = re.compile(r"eslint-|@ts-|prettier-ignore|<reference")


def _skip_quoted(source: str, start: int, quote: str) -> int:
    # Para no fecho ou no fim da linha, para um erro de leitura nunca passar da linha
    i = start + 1
    while i < len(source) and source[i] not in (quote, "\n"):
        i += 2 if source[i] == "\\" else 1
    return i + 1 if i < len(source) and source[i] == quote else i


def _skip_regex(source: str, start: int) -> int:
    i, in_class = start + 1, False
    while i < len(source) and source[i] != "\n":
        char = source[i]
        if char == "\\":
            i += 2
            continue
        if char == "/" and not in_class:
            return i + 1
        in_class = (in_class or char == "[") and char != "]"
        i += 1
    return i


def _web_comments(source: str, is_css: bool) -> list[tuple[int, str, bool, bool]]:
    # Cada comentário como linha, texto, se é em bloco e se ocupa a linha sozinho
    comments = []
    row, i, n = 1, 0, len(source)
    template_braces: list[int] = []
    previous = ""
    while i < n:
        char, pair = source[i], source[i : i + 2]
        comment_only = source[source.rfind("\n", 0, i) + 1 : i].strip() == ""
        if char == "\n":
            row, i = row + 1, i + 1
        elif pair == "/*":
            end = source.find("*/", i + 2)
            end = n if end < 0 else end
            text = source[i + 2 : end]
            comments.append((row, text, True, comment_only))
            row, i = row + text.count("\n"), end + 2
        elif is_css:
            i += 1
        elif pair == "//":
            end = source.find("\n", i)
            end = n if end < 0 else end
            comments.append((row, source[i + 2 : end], False, comment_only))
            i = end
        elif char in "'\"":
            i, previous = _skip_quoted(source, i, char), char
        elif char == "`" or (char == "}" and template_braces and template_braces[-1] == 0):
            if char == "}":
                template_braces.pop()
            i += 1
            while i < n and source[i] != "`":
                if source[i] == "\\":
                    i += 2
                    continue
                if source.startswith("${", i):
                    template_braces.append(0)
                    i += 2
                    break
                row += source[i] == "\n"
                i += 1
            else:
                i += 1
            previous = "`"
        elif char == "/" and (previous == "" or previous in _REGEX_STARTS_AFTER):
            i, previous = _skip_regex(source, i), "/"
        else:
            if char == "{" and template_braces:
                template_braces[-1] += 1
            elif char == "}" and template_braces:
                template_braces[-1] -= 1
            if not char.isspace():
                previous = char
            i += 1
    return comments


@pytest.mark.parametrize("path", WEB_FILES, ids=_relative)
def test_web_comments_follow_the_rule(path):
    source = path.read_text()
    is_css = path.suffix == ".css"
    lines = source.splitlines()
    problems = []
    previous_comment_only = None
    for row, text, is_block, comment_only in _web_comments(source, is_css):
        if _WEB_PRAGMA.search(text):
            continue
        if is_block and not is_css:
            problems.append(f"linha {row} comentário em bloco, use //")
        if is_block and "\n" in text:
            problems.append(f"linha {row} comentário em mais de uma linha")
        if not is_block and comment_only and previous_comment_only == row - 1:
            problems.append(f"linha {row} comentário em mais de uma linha")
        if not is_block and comment_only:
            previous_comment_only = row
        problems += [f"linha {row} {p}" for p in _text_problems(text)]
        if len(lines[row - 1]) > MAX_LINE:
            problems.append(f"linha {row} passa de {MAX_LINE} colunas")
    assert not problems, "\n".join(problems)
