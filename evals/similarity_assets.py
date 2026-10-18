"""Turn any text file of a skill folder into prose and code, for evals/source_similarity.py.

extract(path_or_text, suffix) returns an Extract:
  prose  text whose line numbers are the file's own (non-prose lines are blank): Markdown text outside fences,
         comments and docstrings of code, string values of YAML and JSON, the text nodes of HTML, TeX text.
  code   (line number, normalised line) pairs: code with comments removed and all whitespace stripped, lines under
         CODE_MIN characters dropped; Markdown fenced blocks count as code too (kind "md-fence").
Binary files, files that are not UTF-8 and files over MAX_BYTES return None.
"""
from __future__ import annotations

import ast
import html as htmllib
import io
import re
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

CODE_MIN = 20
MAX_BYTES = 1_500_000
FENCE = re.compile(r"^```.*?^```", re.S | re.M)

COMMENT_STYLE = {
    **{s: "hash" for s in (".py", ".sh", ".bash", ".zsh", ".rb", ".ps1", ".toml", ".mplstyle", ".cfg", ".ini", ".setting")},
    **{s: "c" for s in (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".scss", ".java", ".c", ".h", ".cpp", ".go", ".rs",
                        ".swift", ".jsonc", ".kt")},
    ".css": "css", ".lua": "dash", ".sql": "dash",
    **{s: "pct" for s in (".tex", ".bib", ".bst", ".sty", ".cls")},
    **{s: "xml" for s in (".xml", ".xsd", ".svg")},
}
FENCE_STYLE = {
    **{k: "hash" for k in ("python", "py", "bash", "sh", "shell", "zsh", "yaml", "yml", "toml", "ruby", "rb", "python3")},
    **{k: "c" for k in ("js", "javascript", "ts", "typescript", "tsx", "jsx", "java", "c", "cpp", "go", "rust", "swift",
                        "json5", "jsonc")},
    "css": "css", "sql": "dash", "lua": "dash",
}
KIND_ALIAS = {"yml": "yaml", "markdown": "md", "mjs": "js", "cjs": "js", "bash": "sh", "zsh": "sh", "jsx": "js"}
PROSE_FILES = {"md", "txt", "rst"}
SKIP_FILE_NAMES = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock")


@dataclass
class Extract:
    kind: str
    prose: str = ""
    code: list = field(default_factory=list)       # (line number, normalised line)
    code_kind: str = ""                            # kind label for the code lines (differs from `kind` for md-fence)


def kind_of(path: Path) -> str:
    s = path.suffix.lower().lstrip(".") or path.name.lower()
    return KIND_ALIAS.get(s, s)


def normalise(line: str) -> str | None:
    n = re.sub(r"\s+", "", line)
    return n if len(n) >= CODE_MIN else None


def _pairs(lines: dict[int, str]) -> list[tuple[int, str]]:
    out = []
    for ln in sorted(lines):
        n = normalise(lines[ln])
        if n:
            out.append((ln, n))
    return out


def split_comments(text: str, style: str) -> tuple[dict[int, str], dict[int, str]]:
    """(comment text by line, code by line) with comments removed from the code. Strings do not span lines here."""
    blocks = {"c": [("/*", "*/")], "css": [("/*", "*/")], "xml": [("<!--", "-->")]}.get(style, [])
    marker = {"hash": "#", "c": "//", "dash": "--", "pct": "%"}.get(style)
    quotes = "\"'`" if style in ("hash", "c", "css", "dash") else ""
    comments: dict[int, str] = {}
    code: dict[int, str] = {}
    in_block = None
    for ln, line in enumerate(text.split("\n"), 1):
        out: list[str] = []
        com: list[str] = []
        quote = None
        i = 0
        while i < len(line):
            if in_block:
                end = line.find(in_block, i)
                if end < 0:
                    com.append(line[i:])
                    break
                com.append(line[i:end])
                i = end + len(in_block)
                in_block = None
                continue
            ch = line[i]
            if quote:
                out.append(ch)
                if ch == "\\" and i + 1 < len(line):
                    out.append(line[i + 1])
                    i += 2
                    continue
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in quotes and not (style == "css" and ch == "`"):
                quote = ch
                out.append(ch)
                i += 1
                continue
            opened = next((b for b in blocks if line.startswith(b[0], i)), None)
            if opened:
                in_block = opened[1]
                i += len(opened[0])
                continue
            if marker and line.startswith(marker, i) and not (marker == "#" and i == 0 and line.startswith("#!")):
                com.append(line[i + len(marker):])
                break
            out.append(ch)
            i += 1
        if com:
            comments[ln] = " ".join(c.strip() for c in com if c.strip())
        code[ln] = "".join(out)
    return comments, code


def coalesce(lines: list[str]) -> list[str]:
    """Join runs of consecutive non-blank lines into the first line of the run (hard-wrapped comments)."""
    out = [""] * len(lines)
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        j = i
        while j < len(lines) and lines[j].strip():
            j += 1
        out[i] = " ".join(x.strip() for x in lines[i:j])
        i = j
    return out


def _prose_of_comments(n_lines: int, comments: dict[int, str]) -> str:
    return "\n".join(coalesce([comments.get(i, "") for i in range(1, n_lines + 1)]))


def py_extract(text: str) -> Extract:
    n = text.count("\n") + 1
    try:
        tree = ast.parse(text)
        doc: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                b = node.body
                if (b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant)
                        and isinstance(b[0].value.value, str)):
                    doc.update(range(b[0].lineno, b[0].end_lineno + 1))
        cols: dict[int, tuple[int, str]] = {}
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                cols[tok.start[0]] = (tok.start[1], tok.string)
    except (SyntaxError, tokenize.TokenError, ValueError, IndentationError):
        comments, code = split_comments(text, "hash")
        return Extract("py", _prose_of_comments(n, comments), _pairs(code), "py")
    lines = text.split("\n")
    prose = [""] * n
    code: dict[int, str] = {}
    for i, line in enumerate(lines, 1):
        if i in doc:
            s = re.sub(r"^\s*[rRuUbB]{0,2}(\"{3}|'{3}|\"|')", "", line)
            prose[i - 1] = re.sub(r"(\"{3}|'{3}|\"|')\s*$", "", s)
        elif i in cols:
            col, s = cols[i]
            prose[i - 1] = "" if s.startswith("#!") else s.lstrip("#").strip()
            code[i] = line[:col]
        else:
            code[i] = line
    return Extract("py", "\n".join(coalesce(prose)), _pairs(code), "py")


def yaml_prose(text: str) -> str:
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("#"):
            out.append(s.lstrip("# "))
            continue
        m = re.match(r"^(?:-\s+)?[\w.\-\"']+:\s+(.*)$", s)
        s = m.group(1) if m else re.sub(r"^-\s+", "", s)
        out.append(s.strip().strip("\"'"))
    return "\n".join(out)


JSON_VALUE = re.compile(r"""(?:^\s*|:\s*)"((?:[^"\\]|\\.)*)"\s*,?\s*$""")


def json_prose(text: str) -> str:
    out = []
    for line in text.split("\n"):
        m = JSON_VALUE.search(line)
        out.append(m.group(1).replace('\\"', '"').replace("\\n", " ") if m and not re.match(r'^\s*"[^"]*"\s*:\s*$', line) else "")
    return "\n".join(out)


def html_extract(text: str) -> Extract:
    n = text.count("\n") + 1
    code: dict[int, str] = {}
    for m in re.finditer(r"<(script|style)\b[^>]*>(.*?)</\1>", text, re.S | re.I):
        start = text.count("\n", 0, m.start(2)) + 1
        for k, ln in enumerate(m.group(2).split("\n")):
            code[start + k] = ln
    text = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->|<[^>]+>", lambda m: "\n" * m.group().count("\n") + " ", text,
                  flags=re.S | re.I)
    return Extract("html", htmllib.unescape(text), _pairs(code), "html")


def tex_prose(text: str) -> str:
    out = []
    for line in text.split("\n"):
        line = re.sub(r"(?<!\\)%.*$", "", line)
        line = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", line)
        out.append(re.sub(r"[{}$&~]", " ", line))
    return "\n".join(out)


def md_fences(text: str) -> list[tuple[int, str]]:
    lines: dict[int, str] = {}
    for m in FENCE.finditer(text):
        block = m.group().split("\n")
        start = text.count("\n", 0, m.start()) + 1
        lang = re.sub(r"^`+", "", block[0]).strip().split(" ")[0].lower()
        body = "\n".join(block[1:-1])
        _, code = split_comments(body, FENCE_STYLE.get(lang, "none"))
        for k, ln in code.items():
            lines[start + k] = ln
    return _pairs(lines)


def extract_text(text: str, suffix: str) -> Extract:
    suffix = suffix.lower()
    kind = KIND_ALIAS.get(suffix.lstrip("."), suffix.lstrip("."))
    if suffix in (".md", ".markdown", ".txt", ".rst"):
        blank = FENCE.sub(lambda m: "\n" * m.group().count("\n"), text)
        return Extract(kind, blank, md_fences(text) if suffix in (".md", ".markdown") else [], "md-fence")
    if suffix == ".py":
        return py_extract(text)
    if suffix in (".yaml", ".yml"):
        return Extract(kind, yaml_prose(text))
    if suffix == ".json":
        return Extract(kind, json_prose(text))
    if suffix in (".html", ".htm"):
        return html_extract(text)
    if suffix == ".tex":
        comments, code = split_comments(text, "pct")
        return Extract(kind, tex_prose(text), _pairs(code), kind)
    style = COMMENT_STYLE.get(suffix, "none")
    comments, code = split_comments(text, style)
    return Extract(kind, _prose_of_comments(text.count("\n") + 1, comments), _pairs(code), kind)


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        data = path.read_bytes()
        if b"\0" in data[:8192]:
            return None
        return data.decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def extract(path: Path) -> Extract | None:
    if path.name.lower() in SKIP_FILE_NAMES or path.name.startswith("."):
        return None
    text = read_text(path)
    if text is None:
        return None
    return extract_text(text, path.suffix.lower() if path.suffix else ".none")
