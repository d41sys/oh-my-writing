#!/usr/bin/env python3
"""List the sentences of a text that deserve an evidence check.

The script is a screening aid. It never rewrites the text and never decides
whether a claim is true; it only points at sentences whose wording usually
needs support, and leaves the verdict (status column) blank for a person.

Usage:
    python claim_ledger.py draft.md              # markdown ledger table
    python claim_ledger.py draft.md --json       # machine-readable output
    cat draft.md | python claim_ledger.py -      # read stdin
    python claim_ledger.py draft.md --strict     # exit 1 if a flagged
                                                 # sentence has no citation

A sentence is listed when at least one signal fires:
    number, percent, currency, date      figures and time references
    comparative, superlative             comparisons and rankings
    causal                               cause-and-effect wording
    absolute                             always / never / all / none ...
    vague-attribution                    "studies show", "experts say" ...

Citation column: yes (a citation marker, link or identifier is in the
sentence), pending (a gap marker is in the sentence), no (neither).

Standard gap markers: [ASK AUTHOR: ...] (only the author knows), [VERIFY: ...]
(an external fact, source or citation must be checked) and [UNTESTED] (a
command or code sample that was not run). For robustness the script also
reads the older [CITATION NEEDED], [SOURCE NEEDED] and [UNVERIFIED] as
pending; write new text with the three standard markers only.

Skipped on purpose: YAML front matter, fenced code blocks, headings, table
separator rows, HTML comments. Inline code spans, citation markers, URLs and
figure/table/section labels are ignored when looking for numbers.

Limits: English wording only; numbers spelled out as words ("three users")
are not detected; a year-like number such as "2000 users" reads as a date.

Exit codes: 0 ok, 1 --strict found an uncited flagged sentence, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Signal patterns
# --------------------------------------------------------------------------

_MONTHS = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

# Case-sensitive on purpose: lowercase "may" is a modal verb, not a month.
DATE_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b" + _MONTHS + r"\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+(?:19|20)\d{2})?\b"
    r"|\b" + _MONTHS + r"\.?\s+(?:19|20)\d{2}\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)?\s+" + _MONTHS + r"\.?(?:,?\s+(?:19|20)\d{2})?\b"
    r"|\b(?:FY|H[12]|Q[1-4])\s?'?(?:19|20)?\d{2}\b"
    r"|\b(?:19|20)\d{2}s?\b"
)

_FLAGS = re.IGNORECASE

PERCENT_RE = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s?%"
    r"|\bpercent(?:age)?(?:\s+points?)?\b"
    r"|\bper\s?cent\b"
    r"|\bpercentage\s+points?\b"
    r"|\bbasis\s+points?\b",
    _FLAGS,
)

_SCALE = r"(?:\s?(?:thousand|million|billion|trillion|k|m|bn))?"
CURRENCY_RE = re.compile(
    r"[$€£¥₹]\s?\d"
    r"|\b(?:USD|EUR|GBP|JPY|CAD|AUD|CHF)\s?\d"
    r"|\b\d[\d,.]*" + _SCALE + r"\s?(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|dollars?|euros?|pounds?|yen|bucks)\b",
    _FLAGS,
)

MULTIPLIER_RE = re.compile(
    r"\b(?:twice|thrice|double[ds]?|doubling|triple[ds]?|tripling|quadrupl\w+|halv(?:e|es|ed|ing))\b"
    r"|\b\d+(?:\.\d+)?x\b"
    r"|\b\d+-?fold\b"
    r"|\b(?:two|three|four|five|six|ten)[\s-]?(?:times|fold)\b",
    _FLAGS,
)

# Digits that are not glued to letters, dots or slashes (so GPT-4, v3.2, 2nd,
# 10.1/abc do not count), after more specific signals were removed.
NUMBER_RE = re.compile(r"(?<![\w./])(?<![A-Za-z]-)\d[\d,]*(?:\.\d+)?(?![\w/]|-[A-Za-z])")

REF_LABEL_RE = re.compile(
    r"\b(?:Figures?|Figs?\.?|Tables?|Sections?|Secs?\.?|Steps?|Eqs?\.?|Equations?|Chapters?|"
    r"Appendix|Pages?|pp?\.|Lines?|Parts?|Algorithms?|Listings?|Examples?|Footnotes?|Items?)\s+"
    r"[A-Z]?\d+(?:\.\d+)*[a-z]?",
    _FLAGS,
)
VERSION_RE = re.compile(r"\bv\d[\w.]*", _FLAGS)

_COMPARATIVES = (
    r"more|less|fewer|greater|higher|lower|better|worse|faster|slower|larger|smaller|bigger|"
    r"cheaper|longer|shorter|stronger|weaker|safer|simpler|easier|harder|than|"
    r"outperform\w*|surpass\w*|exceed\w*|beats?|improv\w+|increas\w+|decreas\w+|reduc\w+|"
    r"boost\w*|declin\w+|compared (?:to|with)|versus|vs"
)
COMPARATIVE_RE = re.compile(r"\b(?:" + _COMPARATIVES + r")\b", _FLAGS)

# Words that end in "est" but are not superlatives.
_NOT_SUPERLATIVE = (
    "interest|west|test|request|rest|forest|honest|harvest|suggest|invest|protest|contest|"
    "digest|manifest|east|nest|chest|quest|guest|arrest|attest|detest|conquest|southwest|"
    "northwest|southeast|northeast|crest|vest|pest|jest|bequest|foremost|unrest|wrest|"
    "ingest|congest|infest|divest|midwest|everest|ernest|modest|molest"
)
SUPERLATIVE_RE = re.compile(
    r"\b(?:best|worst|most|least|first|only|last|top|leading|unique|"
    r"(?!(?:" + _NOT_SUPERLATIVE + r")\b)[a-z]{3,}est)\b",
    _FLAGS,
)

CAUSAL_RE = re.compile(
    r"\b(?:caus(?:e|es|ed|ing)|lead(?:s|ing)?\s+to|led\s+to|driv(?:e|es|ing)|drove|driven\s+by|"
    r"result(?:s|ed|ing)?\s+in|because|due\s+to|owing\s+to|thanks\s+to|as\s+a\s+result\s+of|"
    r"contribut(?:e|es|ed|ing)\s+to|trigger(?:s|ed|ing)?|responsible\s+for)\b",
    _FLAGS,
)

ABSOLUTE_RE = re.compile(
    r"\b(?:always|never|all|none|every|everyone|everybody|everything|nobody|no\s+one|"
    r"proven|prove[sd]?|guarantee\w*|impossible|undeniabl[ey]|definitely|absolutely|"
    r"invariably|universally|without\s+exception|completely|entirely|perfectly|forever)\b",
    _FLAGS,
)

_VAGUE_SUBJECT = (
    r"(?:studies|research|surveys?|reports|analyses|experts|scientists|researchers|analysts|"
    r"critics|observers|sources|insiders|authorities|people|many|some|most|others)"
)
_VAGUE_VERB = (
    r"(?:show(?:s|ed|n)?|suggest(?:s|ed)?|indicat(?:e|es|ed)|find|finds|found|say|says|said|"
    r"believ(?:e|es|ed)|agree[sd]?|argu(?:e|es|ed)|claim(?:s|ed)?|think|thinks|warn(?:s|ed)?|"
    r"prov(?:e|es|ed|en)|confirm(?:s|ed)?|demonstrat(?:e|es|ed)|conclud(?:e|es|ed)|"
    r"recommend(?:s|ed)?|know|knows)"
)
VAGUE_RE = re.compile(
    r"\b(?:(?:many|several|some|numerous|recent|multiple|most|various|countless|few|a\s+number\s+of)\s+)?"
    + _VAGUE_SUBJECT
    + r"\s+(?:(?:have|has|had|also|often|consistently|repeatedly|clearly|widely|generally|increasingly|now)\s+){0,2}"
    + _VAGUE_VERB
    + r"\b"
    r"|\bit\s+is\s+(?:widely\s+|commonly\s+|generally\s+|often\s+)?"
    r"(?:known|believed|said|thought|argued|accepted|agreed|understood|recognized|acknowledged)\s+that\b"
    r"|\b(?:widely|commonly|generally)\s+(?:known|believed|accepted|regarded|considered)\b"
    r"|\beveryone\s+knows\b|\bas\s+we\s+all\s+know\b"
    r"|\baccording\s+to\s+(?:some|many|most|experts|critics|insiders)\b"
    r"|\bthey\s+say\b",
    _FLAGS,
)

# --------------------------------------------------------------------------
# Citation detection
# --------------------------------------------------------------------------

_NAME = r"[A-Z][A-Za-z'’\-]+"
CITATION_RE = re.compile(
    r"\[\d+(?:\s*[-–,]\s*\d+)*\]"                       # [3] [1-4] [1, 2]
    r"|\[@[^\]\s][^\]]*\]"                              # [@key]
    r"|\\cite[a-z]*\*?(?:\[[^\]]*\])*\{[^}]*\}"         # \cite{key}
    r"|\[\^[^\]]+\]"                                    # footnote
    r"|\(" + _NAME + r"(?:\s+et\s+al\.?|\s+(?:and|&)\s+" + _NAME + r")?,?\s+(?:19|20)\d{2}[a-z]?(?:[,;:][^)]*)?\)"
    r"|\[" + _NAME + r"(?:\s+et\s+al\.?|\s+(?:and|&)\s+" + _NAME + r")?,?\s+(?:19|20)\d{2}[a-z]?\]"
    r"|\]\((?:https?://|doi:|#|\./|\.\./)[^)\s]*\)"     # markdown link
    r"|https?://\S+"
    r"|\bdoi:\s?\S+|\b10\.\d{4,9}/\S+"
    r"|\barXiv:\s?\d{4}\.\d{4,5}(?:v\d+)?",
    re.IGNORECASE,
)
# Standard markers first; the older placeholder spellings stay accepted as "pending".
PENDING_RE = re.compile(
    r"\[(?:VERIFY|ASK\s+AUTHOR|UNTESTED|CITATION\s+NEEDED|SOURCE\s+NEEDED|UNVERIFIED)\b[^\]]*\]",
    re.IGNORECASE,
)

INLINE_CODE_RE = re.compile(r"`[^`]*`")
URL_RE = re.compile(r"https?://\S+")

# --------------------------------------------------------------------------
# Text -> sentences
# --------------------------------------------------------------------------

ABBREVIATIONS = {
    "e.g", "i.e", "al", "fig", "figs", "vs", "cf", "dr", "mr", "mrs", "ms", "prof", "no", "nos",
    "approx", "ca", "eq", "eqs", "sec", "st", "inc", "ltd", "co", "u.s", "u.k", "jr", "sr", "p", "pp",
}
SENT_BREAK_RE = re.compile(r"([.!?]+[\"'”’)\]]*)\s+(?=[\"“‘(\[]?[A-Z0-9])")
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")
RULE_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->")


def _blocks(text: str) -> list[tuple[str, int]]:
    """Return (sentence, source_line) pairs for the prose of `text`.

    Skips front matter, fenced code, headings, rules, table separators and
    HTML comments; list items and table rows are separate units.
    """
    lines = text.splitlines()
    units: list[tuple[list[tuple[str, int]], bool]] = []  # ([(text, line)], is_table_row)
    current: list[tuple[str, int]] = []
    in_fence: str | None = None
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                i = j + 1
                break

    def flush() -> None:
        nonlocal current
        if current:
            units.append((current, False))
            current = []

    for idx in range(i, len(lines)):
        raw = lines[idx]
        lineno = idx + 1
        fence = FENCE_RE.match(raw)
        if in_fence:
            if fence and fence.group(1) == in_fence:
                in_fence = None
            continue
        if fence:
            flush()
            in_fence = fence.group(1)
            continue
        raw = HTML_COMMENT_RE.sub("", raw)
        stripped = raw.strip()
        if not stripped:
            flush()
            continue
        if HEADING_RE.match(raw) or RULE_RE.match(raw) or TABLE_SEP_RE.match(raw):
            flush()
            continue
        if stripped.startswith("|") and stripped.count("|") >= 2:
            flush()
            cells = " | ".join(c.strip() for c in stripped.strip("|").split("|"))
            units.append(([(cells, lineno)], True))
            continue
        body = re.sub(r"^\s*>+\s?", "", raw)
        if LIST_MARKER_RE.match(body):
            flush()
            body = LIST_MARKER_RE.sub("", body)
        current.append((body.strip(), lineno))
    flush()

    return _expand(units)


def _expand(units: list[tuple[list[tuple[str, int]], bool]]) -> list[tuple[str, int]]:
    """Split each unit into sentences and attach each sentence's source line."""
    result: list[tuple[str, int]] = []
    for parts, is_table in units:
        joined = ""
        starts: list[tuple[int, int]] = []
        for piece, ln in parts:
            if joined:
                joined += " "
            starts.append((len(joined), ln))
            joined += piece
        if is_table:
            spans = [(0, len(joined))]
        else:
            spans = _sentence_spans(joined)
        for a, b in spans:
            sentence = joined[a:b].strip()
            if not sentence:
                continue
            line = starts[0][1]
            for off, ln in starts:
                if off <= a:
                    line = ln
                else:
                    break
            result.append((sentence, line))
    return result


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for m in SENT_BREAK_RE.finditer(text):
        terminator = m.group(1)
        if "." in terminator and not re.search(r"[!?]", terminator):
            before = text[: m.start(1)]
            tok = re.search(r"([A-Za-z][\w.]*)$", before)
            word = tok.group(1).lower() if tok else ""
            if word in ABBREVIATIONS or (len(word) == 1 and word.isalpha()):
                continue
        end = m.end(1)
        spans.append((start, end))
        start = m.end()
    spans.append((start, len(text)))
    return spans


def split_sentences(text: str) -> list[tuple[str, int]]:
    """Public helper: (sentence, 1-based source line) pairs of prose text."""
    return _blocks(text)


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

def _blank(pattern: re.Pattern[str], text: str) -> str:
    return pattern.sub(" ", text)


def analyse(sentence: str) -> dict:
    """Return the signals and citation status for one sentence."""
    no_code = INLINE_CODE_RE.sub(" ", sentence)
    pending = bool(PENDING_RE.search(no_code))
    cited = bool(CITATION_RE.search(PENDING_RE.sub(" ", no_code)))

    work = PENDING_RE.sub(" ", no_code)
    work = _blank(CITATION_RE, work)
    work = _blank(URL_RE, work)
    work = _blank(REF_LABEL_RE, work)
    work = _blank(VERSION_RE, work)

    reasons: list[str] = []
    for name, pattern in (("percent", PERCENT_RE), ("currency", CURRENCY_RE), ("date", DATE_RE)):
        if pattern.search(work):
            reasons.append(name)
            work = _blank(pattern, work)
    if MULTIPLIER_RE.search(work):
        reasons.append("number")
        work = _blank(MULTIPLIER_RE, work)
    elif NUMBER_RE.search(work):
        reasons.append("number")
    if COMPARATIVE_RE.search(work):
        reasons.append("comparative")
    if SUPERLATIVE_RE.search(work):
        reasons.append("superlative")
    if CAUSAL_RE.search(work):
        reasons.append("causal")
    if ABSOLUTE_RE.search(work):
        reasons.append("absolute")
    if VAGUE_RE.search(work):
        reasons.append("vague-attribution")
    return {"reasons": reasons, "citation_present": cited, "pending_marker": pending}


def build_ledger(text: str) -> dict:
    sentences = split_sentences(text)
    claims = []
    for sentence, line in sentences:
        info = analyse(sentence)
        if not info["reasons"]:
            continue
        claims.append(
            {
                "id": f"C{len(claims) + 1}",
                "line": line,
                "sentence": sentence,
                "reasons": info["reasons"],
                "citation_present": info["citation_present"],
                "pending_marker": info["pending_marker"],
                "status": "",
            }
        )
    return {"sentences_total": len(sentences), "flagged": len(claims), "claims": claims}


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def _citation_label(claim: dict) -> str:
    if claim["citation_present"]:
        return "yes"
    if claim["pending_marker"]:
        return "pending"
    return "no"


def render_markdown(ledger: dict) -> str:
    if not ledger["claims"]:
        return f"[OK] no check-worthy sentences found in {ledger['sentences_total']} sentences.\n"
    uncited = sum(1 for c in ledger["claims"] if not c["citation_present"])
    out = [
        f"[FLAG] {ledger['flagged']} of {ledger['sentences_total']} sentences need a check; "
        f"{uncited} have no citation -> fill the status column "
        "(supported / partial / unsupported / needs-check) and decide keep / narrow / cut / ask.",
        "",
        "| id | line | sentence | reasons | citation | status |",
        "|----|------|----------|---------|----------|--------|",
    ]
    for c in ledger["claims"]:
        sentence = c["sentence"].replace("|", "\\|")
        out.append(
            f"| {c['id']} | {c['line']} | {sentence} | {', '.join(c['reasons'])} | {_citation_label(c)} |  |"
        )
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _read_input(path: str | None) -> tuple[str, str]:
    if path is None or path == "-":
        return sys.stdin.read(), "<stdin>"
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    return p.read_text(encoding="utf-8"), str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claim_ledger.py",
        description="List sentences that need an evidence check (numbers, comparisons, causal "
        "wording, absolutes, vague attribution) as a claims-ledger skeleton. Never edits the text.",
    )
    parser.add_argument("file", nargs="?", help="text or markdown file; '-' or omitted reads stdin")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a markdown table")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when any flagged sentence has no citation marker",
    )
    args = parser.parse_args(argv)

    try:
        text, name = _read_input(args.file)
    except FileNotFoundError as exc:
        print(f"[FLAG] file not found: {exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print("[FLAG] input is not valid UTF-8 text", file=sys.stderr)
        return 2

    ledger = build_ledger(text)
    if args.json:
        print(json.dumps({"file": name, **ledger}, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_markdown(ledger))

    if args.strict and any(not c["citation_present"] for c in ledger["claims"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
