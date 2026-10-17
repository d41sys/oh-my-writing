#!/usr/bin/env python3
"""Build one self-contained HTML report from a Markdown file and diagram files.

Usage:
    python build_report.py report.md --diagrams diagrams --out report.html
    python build_report.py report.md --diagrams diagrams --ledger ledger.md --strict

Input is a Markdown subset (standard library converter, no pandoc needed):
    front matter   --- title, subtitle, type, project, prepared_for, prepared_by,
                   period, date, version, status, lang ---
    blocks         headings, paragraphs, bullet and numbered lists (nested),
                   tables (pipe syntax, alignment honoured), block quotes,
                   fenced code, horizontal rules, HTML comments (dropped)
    inline         **bold**, *italic*, `code`, [text](url), bare URLs
    markers        [ASK AUTHOR: ...], [VERIFY: ...], [UNTESTED] are highlighted
    figures        ![Caption](diagrams/slug.html "Source: plan.md, section 2")
                   on a line of its own. The target may be diagram-design HTML,
                   an SVG file, or a PNG/JPEG/GIF/WebP image. Resolved relative
                   to the report, then inside --diagrams.
    Mermaid        ```mermaid caption="..." source="..." id="slug"  (fallback
                   when no designed diagram exists; shown as labelled source,
                   never executed)
    cross-refs     [[fig:slug]] becomes a link reading "Figure N". A typed
                   "Figure ", "figure " or "Fig. " in front of it is absorbed,
                   so "Figure [[fig:x]]" reads "Figure 1", not "Figure Figure 1"
    contents       listed only with 6+ top-level sections (--toc auto|on|off)
    raw HTML       is escaped, never passed through

Diagram embedding (see references/assembly.md):
    The first top-level <svg> of each diagram HTML is inlined. The page CSS that
    styles it is scoped to that figure (page chrome such as body, h1, cards and
    motion controls is dropped), :root tokens move onto the figure, body colour
    and font family are carried over, and every id is prefixed per figure so
    several diagrams cannot collide. Scripts, event handlers and foreignObject
    are removed. Output has no script and no external asset except, with
    --fonts auto (default), the font stylesheet link(s) the diagrams themselves
    use; --fonts system drops them and the diagrams fall back to system fonts.

Portable Markdown (--md-out FILE):
    writes a second copy of the report that reads on its own in any Markdown
    viewer or as plain text: the front matter becomes a title and a meta line,
    [[fig:x]] becomes "Figure N", each designed diagram becomes an image link to
    a standalone diagrams/<slug>.svg written beside FILE, followed by a caption
    line that carries the diagram's own <desc> text and the source line, and
    Mermaid blocks stay as fenced blocks with a caption line. The input file is
    the source of truth; FILE must be a different path.

Checks (reported, and fatal with --strict):
    figure without caption or source line, unresolved [[fig:...]], gap markers
    left in the text, numbers inside diagram labels (including bare scale or
    grid numbers) that appear neither in the --ledger file (or, without one, in
    the report text), external references inside a diagram.

Exit codes: 0 ok, 1 --strict and a check failed, 2 bad input (missing file,
missing diagram without --allow-missing).
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import mimetypes
import re
import sys
from pathlib import Path

ASSET_CSS = Path(__file__).resolve().parent.parent / "assets" / "report.css"

MARKER_RE = re.compile(r"\[(?:ASK AUTHOR|VERIFY)(?::[^\]]*)?\]|\[UNTESTED\]")
NUM_RE = re.compile(r"(?<![\w.])[$€£]?\d[\d,]*(?:\.\d+)?%?")
LI_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
FIG_RE = re.compile(r'^!\[(.*?)\]\(([^)\s]+)(?:\s+"(.*)")?\)\s*$')
FENCE_RE = re.compile(r"^(```+|~~~+)\s*(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HR_RE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
CALLOUT_RE = re.compile(r"^\*\*(?:Decision needed|Decisions needed|Key points|Bottom line|Recommendation|Overall assessment|Assessment|Outcome)[^*]*\*\*", re.I)
SOURCE_LINE_RE = re.compile(r"^(?:\*|_)?Sources?(?:\*|_)?\s*:", re.I)
SHORT_TABLE_ROWS = 4
TOC_MIN_SECTIONS = 6
TEXT_WIDTH_PX = {"a4": 673, "letter": 695}
LEGIBLE_PRINT_SCALE = 0.75

META_ORDER = [("project", "Project"), ("prepared_for", "Prepared for"), ("prepared_by", "Prepared by"),
              ("period", "Period"), ("date", "Date"), ("version", "Version"), ("status", "Status")]

CHROME_TAGS = {"html", "body", "main", "h1", "h2", "h3", "h4", "p", "noscript", "header", "footer"}
CHROME_CLASSES = {"frame", "eyebrow", "subtitle", "cards", "card", "card-header", "card-dot", "header",
                  "header-eyebrow", "footer", "container", "diagram-container", "sr-only"}


class BuildError(Exception):
    pass


# --------------------------------------------------------------------------
# Inline Markdown
# --------------------------------------------------------------------------

def esc(text: str) -> str:
    return html.escape(text, quote=True)


def safe_url(url: str) -> str | None:
    clean = html.unescape(url).strip()
    scheme = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", clean)
    if scheme and scheme.group(1).lower() not in {"http", "https", "mailto"}:
        return None
    return esc(clean)


def _format(text: str) -> str:
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w_])__(?=\S)(.+?)(?<=\S)__(?![\w_])", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\*\w])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\*\w])", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![\w_])", r"<em>\1</em>", text)
    return text


class Context:
    def __init__(self, report_dir: Path, diagrams_dir: Path | None, args):
        self.report_dir, self.diagrams_dir, self.args = report_dir, diagrams_dir, args
        self.headings: list[dict] = []
        self.used_ids: set[str] = set()
        self.n2 = self.n3 = 0
        self.title: str | None = None
        self.figures: list[dict] = []
        self.fig_slugs: dict[str, int] = {}
        self.markers = {"ask": 0, "verify": 0, "untested": 0}
        self.warnings: list[str] = []
        self.notes: list[str] = []
        self.css_blocks: list[str] = []
        self.font_links: list[str] = []
        self.svg_texts: list[tuple[int, str]] = []
        self.pending: list[str] = []
        self.md_figs: list[dict] = []

    def marker(self, raw: str) -> str:
        kind = "untested" if raw.startswith("[UNTESTED") else ("ask" if raw.startswith("[ASK") else "verify")
        self.markers[kind] += 1
        return f'<mark class="marker marker-{kind}">{esc(raw)}</mark>'


def inline(text: str, ctx: Context) -> str:
    stash: list[str] = []

    def keep(fragment: str) -> str:
        stash.append(fragment)
        return f"\x00{len(stash) - 1}\x00"

    text = re.sub(r"(`+)(.+?)\1", lambda m: keep(f"<code>{esc(m.group(2).strip())}</code>"), text)
    text = MARKER_RE.sub(lambda m: keep(ctx.marker(m.group(0))), text)
    # "Figure [[fig:x]]", "figure [[fig:x]]" and "Fig. [[fig:x]]" render once, as "Figure N".
    text = re.sub(r"(?<![\w-])(?:[Ff]igure|[Ff]ig\.?)[ \t]+(?=\[\[fig:)", "", text)
    text = re.sub(r"\[\[fig:([\w-]+)\]\]", lambda m: keep(f"\x01{m.group(1)}\x01"), text)
    text = esc(text)

    def link(m):
        url = safe_url(m.group(2))
        label = _format(m.group(1))
        if url is None:
            ctx.warnings.append(f"link with a disallowed scheme was written as plain text: {m.group(1)}")
            return keep(label)
        return keep(f'<a href="{url}">{label}</a>')

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;.*?&quot;)?\)", link, text)

    def autolink(m):
        url = m.group(0)
        tail = ""
        while url and url[-1] in ".,;:!?)":
            tail = url[-1] + tail
            url = url[:-1]
        return keep(f'<a href="{url}">{url}</a>') + tail

    text = re.sub(r"(?<![\w\"'=>/])https?://[^\s<]+", autolink, text)
    text = _format(text)
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


def plain(html_text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"\x01[\w-]+\x01", "", html_text))).strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


# --------------------------------------------------------------------------
# CSS and SVG handling for embedded diagrams
# --------------------------------------------------------------------------

def _skip_string(css: str, i: int) -> int:
    quote = css[i]
    i += 1
    while i < len(css) and css[i] != quote:
        i += 2 if css[i] == "\\" else 1
    return i


def split_blocks(css: str):
    i, n = 0, len(css)
    while i < n:
        j = i
        while j < n and css[j] not in "{;":
            j = _skip_string(css, j) + 1 if css[j] in "\"'" else j + 1
        if j >= n:
            if css[i:].strip():
                yield css[i:].strip(), None
            return
        if css[j] == ";":
            yield css[i:j].strip(), None
            i = j + 1
            continue
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] in "\"'":
                k = _skip_string(css, k)
            elif css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        yield css[i:j].strip(), css[j + 1:k - 1]
        i = k


def split_top(text: str, sep: str) -> list[str]:
    parts, depth, cur, i = [], 0, [], 0
    while i < len(text):
        ch = text[i]
        if ch in "\"'":
            end = _skip_string(text, i)
            cur.append(text[i:end + 1])
            i = end + 1
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


def scope_selector(sel: str, root: str) -> str:
    sel = sel.strip()
    if not sel or "data-motion" in sel or sel.startswith("@"):
        return ""
    if sel == ":root":
        return f"#{root}"
    if sel == "svg":
        return ""
    m = re.match(r"svg(?=[\s.\[:#>+~])(.*)$", sel, re.S)
    if m:
        rest = m.group(1)
        return f"#{root}{rest}" if rest[:1] in ".[:#" else f"#{root} {rest.lstrip()}"
    first = re.match(r"[^\s>+~]+", sel).group(0)
    if first.startswith("*") or re.split(r"[.\[:#]", first, maxsplit=1)[0] in CHROME_TAGS:
        return ""
    if set(re.findall(r"\.([\w-]+)", first)) & CHROME_CLASSES:
        return ""
    return f"#{root} {sel}"


def scope_rules(css: str, root: str, imports: list[str], top: bool = True) -> str:
    out = []
    for prelude, body in split_blocks(css):
        if body is None:
            m = re.match(r"@import\s+(?:url\(\s*)?['\"]?([^'\")\s]+)", prelude)
            if m:
                imports.append(html.unescape(m.group(1)))
            continue
        if prelude.startswith("@"):
            name = (re.match(r"@([\w-]+)", prelude) or [None, ""])[1].lower()
            if name in {"media", "supports"}:
                inner = scope_rules(body, root, imports, top=False)
                if inner.strip():
                    out.append(f"{prelude}{{{inner}}}")
            elif name == "font-face":
                out.append(f"{prelude}{{{body}}}")
            continue
        if top and prelude.strip() == "body":
            decls = re.findall(r"(?:^|;)\s*((?:color|font-family|background(?:-color)?)\s*:[^;]+)", body)
            if decls:
                out.append(f"#{root}{{{';'.join(d.strip() for d in decls)}}}")
            continue
        sels = [s for s in (scope_selector(s, root) for s in split_top(prelude, ",")) if s]
        if sels:
            out.append(f"{', '.join(sels)}{{{body.strip()}}}")
    return "\n".join(out)


def _mask(text: str) -> str:
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    return re.sub(r"<(script|style)\b.*?</\1\s*>", blank, text, flags=re.S | re.I)


SVG_TAG_RE = re.compile(r"<(/?)svg\b((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>", re.I)


def find_svg(page: str) -> tuple[int, int] | None:
    depth, start = 0, None
    for t in SVG_TAG_RE.finditer(_mask(page)):
        if t.group(1) != "/":
            if depth == 0:
                start = t.start()
            if t.group(2).rstrip().endswith("/"):
                if depth == 0:
                    return start, t.end()
            else:
                depth += 1
        elif depth:
            depth -= 1
            if depth == 0:
                return start, t.end()
    return None


def sanitize_svg(svg: str) -> str:
    svg = re.sub(r"<script\b.*?</script\s*>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"<(foreignObject|iframe|object|embed)\b.*?</\1\s*>", "", svg, flags=re.S | re.I)
    svg = re.sub(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", svg, flags=re.I)
    return re.sub(r"((?:xlink:)?href\s*=\s*[\"'])\s*javascript:[^\"']*", r"\1#", svg, flags=re.I)


def rename_ids(svg: str, css: str, prefix: str) -> tuple[str, str, dict[str, str]]:
    ids = re.findall(r"""\sid\s*=\s*(?:"([^"]*)"|'([^']*)')""", svg)
    mapping = {a or b: prefix + (a or b) for a, b in ids if (a or b)}
    if not mapping:
        return svg, css, mapping

    def fix_css(text: str) -> str:
        for old, new in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
            text = re.sub(r"#" + re.escape(old) + r"(?![\w-])", "#" + new, text)
        return text

    svg = re.sub(r"(\sid\s*=\s*)(\"|')(.*?)\2", lambda m: f"{m.group(1)}{m.group(2)}{mapping.get(m.group(3), m.group(3))}{m.group(2)}", svg)
    svg = re.sub(r"url\(\s*(['\"]?)#([^)'\"\s]+)\1\s*\)",
                 lambda m: f"url({m.group(1)}#{mapping.get(m.group(2), m.group(2))}{m.group(1)})", svg)
    svg = re.sub(r"((?:xlink:)?href\s*=\s*)(\"|')#([^\"']+)\2",
                 lambda m: f"{m.group(1)}{m.group(2)}#{mapping.get(m.group(3), m.group(3))}{m.group(2)}", svg)
    svg = re.sub(r"(aria-(?:labelledby|describedby)\s*=\s*)(\"|')([^\"']*)\2",
                 lambda m: f"{m.group(1)}{m.group(2)}{' '.join(mapping.get(t, t) for t in m.group(3).split())}{m.group(2)}", svg)
    svg = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", lambda m: m.group(1) + fix_css(m.group(2)) + m.group(3), svg, flags=re.S | re.I)
    return svg, fix_css(css), mapping


def prepare_diagram(page: str, index: int, caption: str, ctx: Context, name: str) -> tuple[str, str]:
    """Return (inline svg, scoped css) for the first top-level svg of a diagram page."""
    span = find_svg(page)
    if span is None:
        raise BuildError(f"{name}: no <svg> element found")
    svg = sanitize_svg(page[span[0]:span[1]])
    outside = page[:span[0]] + page[span[1]:]
    for href in re.findall(r"<link\b[^>]*href=[\"']([^\"']*fonts\.googleapis\.com[^\"']*)[\"']", outside, re.I):
        ctx.font_links.append(html.unescape(href))
    page_css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", re.sub(r"<!--.*?-->", "", outside, flags=re.S), re.S | re.I))
    page_css = re.sub(r"/\*.*?\*/", "", page_css, flags=re.S)

    prefix = f"f{index}-"
    # root tag bookkeeping before renaming
    root_tag = re.match(r"<svg\b(?:\"[^\"]*\"|'[^']*'|[^>\"'])*>", svg, re.I).group(0)
    new_root = root_tag
    for attr in ("width", "height"):
        new_root = re.sub(rf"\s{attr}\s*=\s*(\"[^\"]*\"|'[^']*')", "", new_root)
    if not re.search(r"\sid\s*=", new_root):
        new_root = new_root[:-1].rstrip("/").rstrip() + f' id="root"' + ("/>" if root_tag.endswith("/>") else ">")
    if not re.search(r"\srole\s*=", new_root):
        new_root = new_root[:-1] + ' role="img">'
    if "<title" not in svg[:600].lower() and "aria-label" not in new_root:
        new_root = new_root[:-1] + f' aria-label="{esc(caption or name)}">'
    svg = new_root + svg[len(root_tag):]
    if not re.search(r"\sxmlns\s*=", new_root):
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)

    # move @import fonts out of inner style blocks
    def strip_import(m):
        body = m.group(2)
        for url in re.findall(r"@import\s+url\(\s*['\"]?([^'\")\s]+)", body):
            ctx.font_links.append(html.unescape(url))
        body = re.sub(r"@import\s+url\([^)]*\)\s*;?", "", body)
        return m.group(1) + body + m.group(3)
    svg = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", strip_import, svg, flags=re.S | re.I)

    root_id = re.search(r"\sid\s*=\s*[\"']([^\"']+)[\"']", svg[:len(new_root) + 20]).group(1)
    imports: list[str] = []
    scoped = scope_rules(page_css, root_id, imports)
    ctx.font_links.extend(imports)
    svg, scoped, _ = rename_ids(svg, scoped, prefix)
    # scope selectors were written with the un-prefixed root id and renamed by rename_ids
    if re.search(r"https?://(?!www\.w3\.org/)", re.sub(r"<style\b.*?</style>", "", svg, flags=re.S)):
        ctx.warnings.append(f"{name}: diagram references an external URL")
    return svg, scoped


def standalone_svg(svg: str, css: str) -> str:
    """The inlined figure as a file of its own: the page CSS scoped to the figure goes inside the root element."""
    root = re.match(r"<svg\b(?:\"[^\"]*\"|'[^']*'|[^>\"'])*>", svg, re.I)
    if not css.strip() or root is None or root.group(0).endswith("/>"):
        return svg + "\n"
    return svg[:root.end()] + f"<style><![CDATA[\n{css.strip()}\n]]></style>" + svg[root.end():] + "\n"


def svg_description(svg: str) -> str:
    """The diagram's own <desc> text (its accessible long description), whitespace normalised."""
    m = re.search(r"<desc\b[^>]*>(.*?)</desc>", svg, re.S | re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).split()) if m else ""


def svg_labels(svg: str) -> list[str]:
    labels = []
    for m in re.finditer(r"<(text|title|desc)\b[^>]*>(.*?)</\1>", svg, re.S | re.I):
        label = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split())
        if label:
            labels.append(label)
    return labels


def norm_num(token: str) -> str:
    s = token.strip("$€£%").replace(",", "")
    return s.rstrip("0").rstrip(".") if "." in s else s


def numbers_missing(labels: list[str], reference: str) -> list[tuple[str, str]]:
    known = {norm_num(t) for t in NUM_RE.findall(reference)}
    bad = []
    for label in labels:
        if label.strip() == "0":  # a zero baseline needs no source; every other printed number does
            continue
        for tok in NUM_RE.findall(label):
            if norm_num(tok) not in known:
                bad.append((label, tok))
    return bad


# --------------------------------------------------------------------------
# Block Markdown
# --------------------------------------------------------------------------

def indent_of(line: str) -> int:
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip())


def is_table_start(lines: list[str], i: int) -> bool:
    return ("|" in lines[i] and i + 1 < len(lines) and "|" in lines[i + 1]
            and bool(TABLE_SEP_RE.match(lines[i + 1])))


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


NUMERIC_CELL = re.compile(r"^[~≈<>≤≥+\-−]?\s*[$€£]?\s*\d[\d,.\s]*\s*(%|[kKmMbB]|[a-zA-Z]{0,4})?\s*$")


def render_table(lines: list[str], i: int, ctx: Context) -> tuple[str, int]:
    head = split_row(lines[i])
    aligns = []
    for cell in split_row(lines[i + 1]):
        aligns.append("center" if cell.startswith(":") and cell.endswith(":") else ("num" if cell.endswith(":") else ""))
    i += 2
    rows = []
    while i < len(lines) and lines[i].strip() and "|" in lines[i]:
        rows.append(split_row(lines[i]))
        i += 1
    width = len(head)
    rows = [(r + [""] * width)[:width] for r in rows]
    for c in range(width):
        if not aligns[c:c + 1] or not aligns[c]:
            col = [r[c] for r in rows if r[c]]
            if col and all(NUMERIC_CELL.match(v) and re.search(r"\d", v) for v in col):
                if c >= len(aligns):
                    aligns.extend([""] * (c + 1 - len(aligns)))
                aligns[c] = "num"
    aligns = (aligns + [""] * width)[:width]

    def cell(tag, text, a):
        cls = f' class="{a}"' if a else ""
        return f"<{tag}{cls}>{inline(text, ctx)}</{tag}>"

    short = " short" if len(rows) <= SHORT_TABLE_ROWS else ""
    out = [f'<div class="table-wrap{short}"><table>', "<thead><tr>" + "".join(cell("th", h, aligns[k]) for k, h in enumerate(head)) + "</tr></thead>", "<tbody>"]
    for r in rows:
        out.append("<tr>" + "".join(cell("td", v, aligns[k]) for k, v in enumerate(r)) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out), i


def parse_list(lines: list[str], i: int, base: int, ctx: Context) -> tuple[str, int]:
    first = LI_RE.match(lines[i])
    ordered = first.group(2)[0].isdigit()
    start = int(re.match(r"\d+", first.group(2)).group(0)) if ordered else None
    items = []
    while i < len(lines):
        j = i
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            break
        m = LI_RE.match(lines[j])
        if not m or indent_of(lines[j]) != base or m.group(2)[0].isdigit() != ordered:
            break
        i = j + 1
        text, subs = [m.group(3)], []
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and indent_of(lines[j]) > base:
                    i = j
                    continue
                break
            ind, mm = indent_of(line), LI_RE.match(line)
            if ind > base and mm:
                sub, i = parse_list(lines, i, ind, ctx)
                subs.append(sub)
            elif ind > base:
                text.append(line.strip())
                i += 1
            else:
                break
        items.append("<li>" + inline(" ".join(text), ctx) + "".join(subs) + "</li>")
    tag = "ol" if ordered else "ul"
    attr = f' start="{start}"' if ordered and start not in (None, 1) else ""
    return f"<{tag}{attr}>" + "".join(items) + f"</{tag}>", i


def parse_info(info: str) -> dict[str, str]:
    return {k: v for k, v in re.findall(r'(\w+)="([^"]*)"', info)}


def resolve_target(target: str, ctx: Context) -> Path | None:
    cands = [ctx.report_dir / target]
    if ctx.diagrams_dir:
        cands += [ctx.diagrams_dir / target, ctx.diagrams_dir / Path(target).name]
    return next((c for c in cands if c.is_file()), None)


def viewbox_width(svg: str) -> float | None:
    root = re.match(r"<svg\b(?:\"[^\"]*\"|'[^']*'|[^>\"'])*>", svg, re.I)
    m = re.search(r"\sviewBox\s*=\s*[\"']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+[\d.]+", root.group(0)) if root else None
    return float(m.group(1)) if m else None


def figure_html(ctx: Context, art: str, caption: str, source: str, slug: str, note: str = "", vbw: float | None = None) -> str:
    n = len(ctx.figures) + 1
    base, k = slug, 2
    while slug in ctx.fig_slugs:
        slug, k = f"{base}-{k}", k + 1
    ctx.fig_slugs[slug] = n
    scale = round(min(1.0, TEXT_WIDTH_PX[ctx.args.paper] / vbw), 2) if vbw else None
    ctx.figures.append({"n": n, "slug": slug, "caption": caption, "source": source, "print_scale": scale})
    if scale is not None and scale < LEGIBLE_PRINT_SCALE:
        ctx.notes.append(f"figure {n} ({slug}) is {vbw:g} units wide and prints at about {scale:.0%} scale; "
                         f"labels may be too small on paper (draw it nearer {TEXT_WIDTH_PX[ctx.args.paper]} units wide, or fewer nodes)")
    if not caption:
        ctx.warnings.append(f"figure {n} ({slug}) has no caption")
    if not source:
        ctx.warnings.append(f"figure {n} ({slug}) has no source line")
    cap = inline(caption, ctx) if caption else ""
    lines = []
    if source:
        lines.append(source if re.match(r"(?i)sources?\b", source) else "Source: " + source)
    if note:
        lines.append(note)
    src = "".join(f'<span class="fig-source">{inline(t, ctx)}</span>' for t in lines)
    style = f' style="--vbw:{vbw:g}"' if vbw else ""
    return (f'<figure class="figure" id="fig-{slug}">\n<div class="figure-art"{style}>{art}</div>\n'
            f'<figcaption><span class="fig-label">Figure {n}.</span>{cap}{src}</figcaption>\n</figure>')


def embed_figure(caption: str, target: str, source: str, ctx: Context) -> str:
    path = resolve_target(target, ctx)
    slug = slugify(Path(target).stem)
    if path is None:
        if not ctx.args.allow_missing:
            raise BuildError(f"diagram not found: {target} (looked next to the report and in --diagrams)")
        ctx.pending.append(target)
        ctx.markers["ask"] += 1
        art = f'<p class="diagram-pending"><mark class="marker marker-ask">[ASK AUTHOR: diagram {esc(Path(target).name)} is missing]</mark></p>'
        fig = figure_html(ctx, art, caption, source, slug)
        ctx.md_figs.append({"kind": "missing", "name": Path(target).name})
        return fig
    ext = path.suffix.lower()
    if ext in {".html", ".htm", ".svg"}:
        n = len(ctx.figures) + 1
        svg, css = prepare_diagram(path.read_text(encoding="utf-8"), n, caption, ctx, path.name)
        if css.strip():
            ctx.css_blocks.append(css)
        ctx.svg_texts.append((n, "\n".join(svg_labels(svg))))
        fig = figure_html(ctx, svg, caption, source, slug, vbw=viewbox_width(svg))
        ctx.md_figs.append({"kind": "svg", "slug": ctx.figures[-1]["slug"], "svg": standalone_svg(svg, css),
                            "desc": svg_description(svg), "origin": path})
        return fig
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        art = f'<img src="data:{mime};base64,{data}" alt="{esc(caption)}">'
        fig = figure_html(ctx, art, caption, source, slug)
        ctx.md_figs.append({"kind": "image", "slug": ctx.figures[-1]["slug"], "origin": path})
        return fig
    raise BuildError(f"unsupported diagram type: {target}")


def add_heading(level: int, raw: str, ctx: Context) -> str:
    text = inline(raw, ctx)
    if level == 1 and ctx.title is not None and plain(text) == ctx.title:
        return ""  # the title block already shows it
    if level == 1 and ctx.title is None:
        ctx.title = plain(text)
        return ""
    level = max(level, 2)
    number = ""
    if level in (2, 3) and not re.match(r"(?i)appendix\b", plain(text)) and not ctx.args.no_number:
        if level == 2:
            ctx.n2 += 1
            ctx.n3 = 0
            number = str(ctx.n2)
        elif ctx.n2:
            ctx.n3 += 1
            number = f"{ctx.n2}.{ctx.n3}"
    hid = slugify(plain(text))
    base, k = hid, 2
    while hid in ctx.used_ids:
        hid, k = f"{base}-{k}", k + 1
    ctx.used_ids.add(hid)
    ctx.headings.append({"level": level, "id": hid, "number": number, "text": text})
    num = f'<span class="secnum">{number}</span>' if number else ""
    cls = ' class="appendix"' if level == 2 and re.match(r"(?i)appendix\b", plain(text)) else ""
    return f'<h{level} id="{hid}"{cls}>{num}{text}</h{level}>'


def starts_block(lines: list[str], i: int) -> bool:
    line = lines[i]
    return bool(FENCE_RE.match(line) or HEADING_RE.match(line) or HR_RE.match(line) or line.lstrip().startswith(">")
                or LI_RE.match(line) or FIG_RE.match(line.strip()) or line.lstrip().startswith("<!--") or is_table_start(lines, i))


def convert_blocks(lines: list[str], ctx: Context) -> str:
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        fence = FENCE_RE.match(line.strip())
        if fence:
            marker, info = fence.group(1), fence.group(2).strip()
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(marker[:3]):
                body.append(lines[i])
                i += 1
            i += 1
            lang = info.split()[0] if info else ""
            if lang == "mermaid":
                attrs = parse_info(info)
                art = '<pre class="diagram-source"><code>' + esc("\n".join(body)) + "</code></pre>"
                fig = figure_html(
                    ctx, art, attrs.get("caption", ""), attrs.get("source", ""),
                    slugify(attrs.get("id", attrs.get("caption", "diagram"))),
                    note="Diagram source (Mermaid), not rendered. Open it in a Mermaid viewer for the drawn version.")
                ctx.md_figs.append({"kind": "mermaid", "body": "\n".join(body)})
                out.append(fig)
            else:
                out.append(f'<pre><code>{esc(chr(10).join(body))}</code></pre>')
            continue
        if line.lstrip().startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        m = HEADING_RE.match(line)
        if m:
            h = add_heading(len(m.group(1)), m.group(2), ctx)
            if h:
                out.append(h)
            i += 1
            continue
        if HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue
        fm = FIG_RE.match(line.strip())
        if fm:
            out.append(embed_figure(fm.group(1), fm.group(2), fm.group(3) or "", ctx))
            i += 1
            continue
        if line.lstrip().startswith(">"):
            quote = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote.append(re.sub(r"^\s*> ?", "", lines[i]))
                i += 1
            cls = ' class="callout"' if CALLOUT_RE.match(quote[0].strip()) else ""
            out.append(f"<blockquote{cls}>\n{convert_blocks(quote, ctx)}\n</blockquote>")
            continue
        if is_table_start(lines, i):
            tbl, i = render_table(lines, i, ctx)
            out.append(tbl)
            continue
        if LI_RE.match(line):
            lst, i = parse_list(lines, i, indent_of(line), ctx)
            out.append(lst)
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not starts_block(lines, i):
            para.append(lines[i].strip())
            i += 1
        text = " ".join(para)
        cls = ' class="source-line"' if SOURCE_LINE_RE.match(text) else ""
        out.append(f"<p{cls}>{inline(text, ctx)}</p>")
    return "\n".join(out)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            meta = {}
            for line in lines[1:end]:
                m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
                if m:
                    meta[m.group(1).lower().replace("-", "_")] = m.group(2).strip().strip("\"'")
            return meta, "\n".join(lines[end + 1:])
    return {}, text


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def wrap_appendix(main_html: str) -> str:
    """Wrap everything from the first appendix heading on in one compact section."""
    m = re.search(r'<h2 id="[^"]*" class="appendix">', main_html)
    if not m:
        return main_html
    return main_html[:m.start()] + '<section class="appendix-body">\n' + main_html[m.start():] + "\n</section>"


def render_toc(ctx: Context) -> str:
    items = [h for h in ctx.headings if h["level"] in (2, 3)]
    sections = [h for h in ctx.headings if h["level"] == 2]
    mode = ctx.args.toc
    if mode == "off" or not items or (mode == "auto" and len(sections) < TOC_MIN_SECTIONS):
        return ""
    out = ['<nav class="toc" aria-label="Contents"><h2>Contents</h2>', "<ol>"]
    for h in items:
        num = f'<span class="secnum">{h["number"]}</span>' if h["number"] else ""
        out.append(f'<li class="l{h["level"]}"><a href="#{h["id"]}">{num}{h["text"]}</a></li>')
    out.append("</ol></nav>")
    return "\n".join(out)


def render_title_block(meta: dict[str, str], title: str, ctx: Context) -> str:
    parts = ['<header class="title-block">']
    if meta.get("type"):
        parts.append(f'<p class="kicker">{inline(meta["type"], ctx)}</p>')
    parts.append(f"<h1>{esc(title)}</h1>")
    if meta.get("subtitle"):
        parts.append(f'<p class="subtitle">{inline(meta["subtitle"], ctx)}</p>')
    rows = [(label, meta[key]) for key, label in META_ORDER if meta.get(key)]
    if rows:
        parts.append('<dl class="meta">' + "".join(f"<dt>{label}</dt><dd>{inline(v, ctx)}</dd>" for label, v in rows) + "</dl>")
    parts.append("</header>")
    return "\n".join(parts)


def _sentence(text: str) -> str:
    text = text.strip()
    return text if not text or text[-1] in ".!?:)" else text + "."


def portable_markdown(meta: dict[str, str], body: str, title: str, ctx: Context, dest: Path) -> tuple[str, dict[Path, str | bytes]]:
    """Report text that stands alone without this build: no front matter, no [[fig:]] tokens, figures as image
    links to standalone files plus a caption line that also carries the diagram's own description.
    Returns (markdown, files to write beside it)."""
    files: dict[Path, str | bytes] = {}
    entries = iter(zip(ctx.md_figs, ctx.figures))

    def xref(text: str) -> str:
        text = re.sub(r"(?<![\w-])(?:[Ff]igure|[Ff]ig\.?)[ \t]+(?=\[\[fig:)", "", text)
        return re.sub(r"\[\[fig:([\w-]+)\]\]",
                      lambda m: f"Figure {ctx.fig_slugs[m.group(1)]}" if m.group(1) in ctx.fig_slugs else f"figure {m.group(1)}", text)

    def caption_line(fig: dict, desc: str = "") -> str:
        parts = [f"*Figure {fig['n']}.*", _sentence(fig["caption"]), _sentence(desc)]
        if fig["source"]:
            parts.append(fig["source"] if re.match(r"(?i)sources?\b", fig["source"]) else "Source: " + fig["source"])
        return " ".join(p for p in parts if p)

    def figure_block(entry: dict, fig: dict) -> list[str]:
        kind = entry["kind"]
        if kind == "mermaid":
            return ["```mermaid", entry["body"], "```", "", caption_line(fig), ""]
        if kind == "missing":
            return [f"[ASK AUTHOR: diagram {entry['name']} is missing]", "", caption_line(fig), ""]
        folder = dest.parent / "diagrams"
        if kind == "svg":
            name, desc = entry["slug"] + ".svg", entry["desc"]
            if entry["origin"].suffix.lower() != ".svg" or entry["origin"].resolve() != (folder / name).resolve():
                files[folder / name] = entry["svg"]
        else:
            name, desc = entry["origin"].name, ""
            if entry["origin"].resolve() != (folder / name).resolve():
                files[folder / name] = entry["origin"].read_bytes()
        alt = f"Figure {fig['n']}. {fig['caption']}".strip()
        return [f"![{alt}](diagrams/{name})", "", caption_line(fig, desc), ""]

    head = [f"# {title}", ""]
    if meta.get("subtitle"):
        head += [f"*{meta['subtitle']}*", ""]
    facts = ([meta["type"]] if meta.get("type") else []) + [f"**{label}:** {meta[key]}" for key, label in META_ORDER if meta.get(key)]
    if facts:
        head += [" · ".join(facts), ""]

    out: list[str] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        fence = FENCE_RE.match(stripped)
        if fence:
            marker, info = fence.group(1), fence.group(2).strip()
            block: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(marker[:3]):
                block.append(lines[i])
                i += 1
            i += 1
            if info.split()[:1] == ["mermaid"]:
                entry, fig = next(entries)
                out += figure_block({**entry, "body": "\n".join(block)}, fig)
            else:
                out += [line, *block, marker]
            continue
        if stripped.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 1 and re.sub(r"[*_`]", "", heading.group(2)).strip() == title:
            i += 1
            continue
        fm = FIG_RE.match(stripped)
        if fm:
            entry, fig = next(entries)
            out += figure_block(entry, fig)
            i += 1
            continue
        out.append(xref(line))
        i += 1
    text = "\n".join(head + out)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n", files


def css_string(text: str) -> str:
    return re.sub(r"[\\\"\n]", lambda m: "\\" + ("A " if m.group(0) == "\n" else m.group(0)), text)


def build(report_md: Path, args) -> tuple[str, dict, tuple[str, dict[Path, str | bytes]] | None]:
    text = report_md.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    diagrams = Path(args.diagrams) if args.diagrams else None
    ctx = Context(report_md.parent, diagrams, args)
    ctx.title = meta.get("title")
    main_html = convert_blocks(body.splitlines(), ctx)
    title = ctx.title or "Untitled report"
    if not ctx.title:
        ctx.warnings.append("no title: add a front matter title or a first # heading")

    def fig_ref(m):
        slug = m.group(1)
        if slug in ctx.fig_slugs:
            return f'<a href="#fig-{slug}">Figure {ctx.fig_slugs[slug]}</a>'
        ctx.warnings.append(f"unresolved cross-reference [[fig:{slug}]]")
        return f'<mark class="marker marker-ask">[ASK AUTHOR: figure {esc(slug)} not found]</mark>'
    toc = render_toc(ctx)
    block = render_title_block(meta, title, ctx) + "\n" + toc + "\n" + wrap_appendix(main_html)
    block = re.sub(r"\x01([\w-]+)\x01", fig_ref, block)

    report_css = ASSET_CSS.read_text(encoding="utf-8") if ASSET_CSS.is_file() else ""
    size = "Letter" if args.paper == "letter" else "A4"
    page_css = (f"@page {{ size: {size}; margin: 18mm 16mm 20mm;\n"
                f"  @bottom-left {{ content: \"{css_string(title)}\"; font: 8pt sans-serif; color: #5b6676; }}\n"
                f"  @bottom-right {{ content: counter(page); font: 8pt sans-serif; color: #5b6676; }} }}")
    links = []
    if args.fonts == "auto":
        for href in dict.fromkeys(ctx.font_links):
            links.append(f'<link rel="stylesheet" href="{esc(href)}">')
    lang = esc(meta.get("lang", "en"))
    doc = "\n".join([
        "<!DOCTYPE html>", f'<html lang="{lang}">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>", *links,
        "<style>", report_css, page_css, "</style>",
        '<style id="diagram-styles">', "\n".join(ctx.css_blocks), "</style>",
        "</head>", "<body>", '<main class="report">', block, "</main>", "</body>", "</html>", ""])

    reference = ""
    if args.ledger:
        reference = Path(args.ledger).read_text(encoding="utf-8")
    else:
        reference = body
    unmatched = []
    for n, labels in ctx.svg_texts:
        for label, tok in numbers_missing(labels.splitlines(), reference):
            unmatched.append({"figure": n, "label": label, "number": tok})
            where = "ledger" if args.ledger else "report text"
            if re.fullmatch(NUM_RE, label.strip()):
                ctx.warnings.append(f"figure {n}: bare number {tok} is not in the {where}; it reads as a scale tick or grid label, so label the values directly and draw no numeric ticks")
            else:
                ctx.warnings.append(f"figure {n}: number {tok} in label '{label}' is not in the {where}")
    marker_total = sum(ctx.markers.values())
    if marker_total:
        ctx.warnings.append(f"{marker_total} gap marker(s) remain in the report")
    summary = {
        "title": title, "output": str(args.out), "figures": ctx.figures, "headings": len(ctx.headings),
        "markers": dict(ctx.markers), "missing_diagrams": ctx.pending, "numbers_not_in_reference": unmatched,
        "markdown_output": str(args.md_out) if args.md_out else None,
        "font_links": list(dict.fromkeys(ctx.font_links)) if args.fonts == "auto" else [],
        "warnings": ctx.warnings, "notes": ctx.notes, "generated": dt.date.today().isoformat(),
    }
    portable = portable_markdown(meta, body, title, ctx, args.md_out) if args.md_out else None
    return doc, summary, portable


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a self-contained HTML report from Markdown and diagram files.")
    ap.add_argument("report", type=Path)
    ap.add_argument("--diagrams", type=Path, help="folder with diagram HTML/SVG/image files")
    ap.add_argument("--out", type=Path, default=None, help="output file (default: report name with .html)")
    ap.add_argument("--paper", choices=["a4", "letter"], default="a4")
    ap.add_argument("--fonts", choices=["auto", "system"], default="auto",
                    help="auto: keep the font stylesheet link the diagrams use; system: no external request")
    ap.add_argument("--ledger", type=Path, help="fact ledger; diagram numbers are checked against it")
    ap.add_argument("--toc", choices=["auto", "on", "off"], default="auto",
                    help=f"contents list: auto (only with {TOC_MIN_SECTIONS}+ top-level sections), on, off")
    ap.add_argument("--no-number", action="store_true", help="do not number headings")
    ap.add_argument("--allow-missing", action="store_true", help="render a visible placeholder for a missing diagram")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any warning remains")
    ap.add_argument("--md-out", type=Path, default=None,
                    help="also write a portable Markdown copy (no front matter or [[fig:]] tokens, figures as "
                         "diagrams/<slug>.svg links); must differ from the input file")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    args = ap.parse_args(argv)
    if not args.report.is_file():
        print(f"error: not a file: {args.report}", file=sys.stderr)
        return 2
    if args.ledger and not args.ledger.is_file():
        print(f"error: not a file: {args.ledger}", file=sys.stderr)
        return 2
    if args.md_out and args.md_out.resolve() == args.report.resolve():
        print(f"error: --md-out must not be the input file: {args.report}", file=sys.stderr)
        return 2
    args.out = args.out or args.report.with_suffix(".html")
    try:
        doc, summary, portable = build(args.report, args)
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(doc, encoding="utf-8")
    if portable:
        md_text, extra = portable
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(md_text, encoding="utf-8")
        for path, content in extra.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        summary["markdown_files"] = [str(p) for p in extra]
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"wrote {args.out} ({len(doc) // 1024} KB): {len(summary['figures'])} figure(s), {summary['headings']} heading(s)")
        if portable:
            print(f"wrote {args.md_out}: portable Markdown, {len(summary['markdown_files'])} figure file(s)")
        for n in summary["notes"]:
            print(f"  note: {n}")
        for w in summary["warnings"]:
            print(f"  warning: {w}")
    return 1 if args.strict and summary["warnings"] else 0


if __name__ == "__main__":
    sys.exit(main())
