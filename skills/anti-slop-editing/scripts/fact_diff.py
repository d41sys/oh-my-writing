#!/usr/bin/env python3
"""Deterministic preservation diff between a BEFORE text and an AFTER text.

Extracts the items an edit must not silently change, then reports items that were
lost and items that were added. Categories:

    numbers      numbers with units or percent (1,000 equals 1000; "5 percent"
                 equals "5%"; "6 minutes" equals "six minutes" and "6-minute";
                 24/7 is one number; the words two..twelve count as 2..12)
    negations    not, no, never, without, neither, nor, none, nothing, nobody,
                 nowhere (contractions such as isn't count as "not")
    certainty    may, might, could, must, should, likely, probably, always, ...
    scope        all, every, most, some, only, often, at least, up to, ...
    names        capitalized names and acronyms (a sentence-initial capital
                 counts only when the same word is capitalized mid-sentence)
    urls         bare URLs and Markdown link destinations
    code         inline code spans
    code_blocks  fenced code blocks
    quotes       double-quoted strings
    citations    [12], [1, 3], (Author, 2020), Author (2020), \\cite{key}, [@key]

A clean result is "no mechanical preservation errors found". It does NOT show that
meaning, causality, attribution or certainty survived. Read both texts for that.
It cannot see a changed word that is not in the lists above, and it cannot tell
which differences the user asked for; review those against the request.

Usage:
    python scripts/fact_diff.py BEFORE AFTER
    python scripts/fact_diff.py --json before.md after.md
    cat after.md | python scripts/fact_diff.py before.md -
    python scripts/fact_diff.py --ignore names before.md after.md

Output: human lines use [OK], [FLAG] and "->"; --json prints one JSON object.
Exit codes: 0 nothing lost or added, 1 something lost or added, 2 input error.
The script never rewrites either text.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

CATEGORIES = ("numbers", "negations", "certainty", "scope", "names", "urls", "code", "code_blocks", "quotes", "citations")

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"')\]]+")
MD_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.M | re.S)
CITE_RES = [
    re.compile(r"\[\^?\d+(?:\s*[,\u2013-]\s*\d+)*\]"),
    re.compile(r"\((?:[A-Z][\w'\u2019-]+(?: (?:et al\.?|and|&) ?[A-Z]?[\w'\u2019-]*)*),? \d{4}[a-z]?(?:[;,][^)]*)?\)"),
    re.compile(r"\b[A-Z][\w'\u2019-]+(?: et al\.)? \(\d{4}[a-z]?\)"),
    re.compile(r"\\cite[tp]?\{[^}]*\}"),
    re.compile(r"\[@[^\]]+\]"),
]
STRAIGHT_QUOTE_RE = re.compile(r'(?<![\w])"(?=\S)([^"]{1,600}?)(?<=\S)"(?!\w)')
CURLY_QUOTE_RE = re.compile("\u201c([^\u201d]{1,600})\u201d")

NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
DIGIT_RE = re.compile(r"(?<![\w.])(?P<cur>[$\u20ac\u00a3\u00a5])?(?P<num>\d+(?:[.,]\d+)*(?:/\d+(?!\d|[.,]\d))?)"
                      r"(?:[\s-]?(?P<unit>%|per cent\b|[A-Za-z\u00b5\u00b0][A-Za-z\u00b5\u00b0/]*))?")
IDENT_RE = re.compile(r"\b[A-Za-z]+\d+(?:[.\-]\d+)*[A-Za-z]*\b")
LIST_MARKER_RE = re.compile(r"^[ \t]*(?:\d+[.)]|[-*+])[ \t]+", re.M)
# Markers this skill tells the editor to insert; their wording is a question, not a fact.
MARKER_RE = re.compile(r"\[(?:ASK AUTHOR|VERIFY|CONFIRM|UNTESTED|CITATION NEEDED)\b[^\]\n]*\]", re.I)
CURRENCY = {"$": "usd", "\u20ac": "eur", "\u00a3": "gbp", "\u00a5": "jpy"}
UNIT_CANON = {
    "%": "%", "percent": "%", "per cent": "%", "pp": "pp", "bps": "bps",
    "ms": "ms", "millisecond": "ms", "milliseconds": "ms", "ns": "ns", "us": "us", "\u00b5s": "us",
    "s": "s", "sec": "s", "secs": "s", "second": "s", "seconds": "s",
    "min": "min", "mins": "min", "minute": "min", "minutes": "min",
    "h": "h", "hr": "h", "hrs": "h", "hour": "h", "hours": "h",
    "day": "day", "days": "day", "week": "week", "weeks": "week", "month": "month", "months": "month",
    "year": "year", "years": "year", "yr": "year", "yrs": "year",
    "kb": "kb", "mb": "mb", "gb": "gb", "tb": "tb", "pb": "pb", "kib": "kib", "mib": "mib", "gib": "gib",
    "kg": "kg", "g": "g", "mg": "mg", "lb": "lb", "lbs": "lb", "oz": "oz",
    "km": "km", "m": "m", "cm": "cm", "mm": "mm", "mi": "mi", "mile": "mi", "miles": "mi", "ft": "ft",
    "hz": "hz", "khz": "khz", "mhz": "mhz", "ghz": "ghz", "fps": "fps", "rpm": "rpm",
    "w": "w", "kw": "kw", "mw": "mw", "v": "v", "px": "px", "pt": "pt",
    "x": "x", "k": "k", "bn": "bn", "million": "million", "billion": "billion", "trillion": "trillion", "thousand": "thousand",
    "usd": "usd", "dollar": "usd", "dollars": "usd", "eur": "eur", "euro": "eur", "euros": "eur", "gbp": "gbp",
    "\u00b0c": "\u00b0c", "\u00b0f": "\u00b0f", "\u00b0": "\u00b0",
    "gb/s": "gb/s", "mb/s": "mb/s", "kb/s": "kb/s",
}
# A spelled number takes the same units as a digit ("six minutes" equals "6 minutes"); only known units are
# consumed so that "two three" still yields both numbers.
_WORD_UNITS = "|".join(sorted((u for u in UNIT_CANON if u.isalpha()), key=len, reverse=True))
WORD_NUM_RE = re.compile(r"\b(?P<word>" + "|".join(NUMBER_WORDS) + r")\b(?:[\s-]?(?P<unit>%|percent\b|per cent\b|(?:"
                         + _WORD_UNITS + r")\b))?", re.I)

NEGATIONS = {"not", "no", "never", "without", "neither", "nor", "none", "nothing", "nobody", "nowhere"}
CERTAINTY = {"may", "might", "could", "must", "should", "shall", "would", "likely", "unlikely", "probably", "possibly",
             "perhaps", "potentially", "apparently", "seems", "seem", "appears", "appear", "suggests", "suggest",
             "indicates", "indicate", "allegedly", "reportedly", "definitely", "certainly", "undoubtedly", "clearly",
             "always", "never", "guaranteed", "proves", "proven", "demonstrates"}
SCOPE = {"all", "every", "each", "most", "some", "many", "few", "several", "only", "often", "usually", "sometimes",
         "rarely", "generally", "typically", "approximately", "roughly", "nearly", "almost", "entire"}
SCOPE_PHRASE_RE = re.compile(r"\b(?:no more than|no fewer than|more than|less than|fewer than|at least|at most|up to)\b", re.I)
CONTRACTION_BASES = {"can't": "can", "won't": "will", "shan't": "shall"}
TOKEN_RE = re.compile(r"[A-Za-z]+(?:['\u2019][A-Za-z]+)?")

CAP = r"[A-Z][A-Za-z0-9&'\u2019-]*"
NAME_RE = re.compile(r"\b" + CAP + r"(?:[ \t]+(?:(?:of|de|van|von|der|la|le|del)[ \t]+)?" + CAP + r")*")
ACRONYM_RE = re.compile(r"^(?:[A-Z]{2,}[A-Za-z0-9]*|(?:[A-Z]\.){2,})$")
CAMEL_RE = re.compile(r"^[A-Za-z]*[a-z][A-Z][A-Za-z0-9]*$|^[A-Z][a-z]+[A-Z][A-Za-z0-9]*$")
COMMON_START = {
    "the", "a", "an", "this", "that", "these", "those", "in", "on", "at", "for", "we", "our", "it", "he", "she", "they",
    "however", "but", "and", "also", "if", "when", "while", "as", "after", "before", "because", "since", "so", "there",
    "here", "what", "how", "why", "who", "which", "where", "my", "his", "her", "their", "you", "your", "with", "without",
    "to", "from", "by", "of", "not", "no", "yes", "one", "some", "many", "most", "each", "every", "all", "both", "i",
    "moreover", "furthermore", "additionally", "overall", "then", "thus", "therefore", "instead", "still", "yet", "or",
    "nor", "just", "now", "today", "first", "second", "third", "finally", "next", "once", "although", "though", "unless",
    "until", "whether", "any", "such", "other", "another", "its", "us", "them", "is", "are", "was", "were", "do", "does",
    "did", "can", "will", "would", "should", "could", "may", "might", "must", "let", "see", "note", "please", "use",
    "run", "add", "set", "make", "check", "open", "read", "write", "get", "try", "keep", "select", "install",
}


def mask(text: str, spans) -> str:
    chars = list(text)
    for a, b in spans:
        for i in range(a, b):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def flat(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


class Extraction:
    """Items per category: item -> (count, first position in the original text)."""

    def __init__(self, text: str):
        self.text = text
        self.items: dict[str, dict[str, list]] = {c: {} for c in CATEGORIES}
        self.mid_tokens: set[str] = set()
        self._start_singles: list[tuple[str, int]] = []
        self._extract()

    def add(self, cat: str, item: str, pos: int) -> None:
        slot = self.items[cat].setdefault(item, [0, pos])
        slot[0] += 1

    def _extract(self) -> None:
        text = self.text
        spans: list[tuple[int, int]] = []

        for m in FENCE_RE.finditer(text):
            body = "\n".join(line.rstrip() for line in m.group(2).strip("\n").split("\n"))
            self.add("code_blocks", body, m.start())
            spans.append((m.start(), m.end()))
        work = mask(text, spans)

        markers = list(MARKER_RE.finditer(work))
        self.markers = len(markers)
        work = mask(work, [(m.start(), m.end()) for m in markers])

        spans = []
        for m in URL_RE.finditer(work):
            self.add("urls", m.group(0).rstrip(".,;:!?"), m.start())
            spans.append((m.start(), m.end()))
        for m in MD_LINK_RE.finditer(work):
            target = m.group(1)
            if not URL_RE.match(target):
                self.add("urls", target, m.start(1))
            spans.append((m.start(1), m.end(1)))
        work = mask(work, spans)

        spans = []
        for m in INLINE_CODE_RE.finditer(work):
            self.add("code", m.group(2).strip(), m.start())
            spans.append((m.start(), m.end()))
        work = mask(work, spans)

        spans = []
        for rx in CITE_RES:
            for m in rx.finditer(work):
                self.add("citations", flat(m.group(0)), m.start())
                spans.append((m.start(), m.end()))
        work = mask(work, spans)

        spans = []
        for rx in (STRAIGHT_QUOTE_RE, CURLY_QUOTE_RE):
            for m in rx.finditer(work):
                if "\n\n" not in m.group(0):
                    self.add("quotes", flat(m.group(1)), m.start())
                    spans.append((m.start(), m.end()))
        work = mask(work, spans)
        work = LIST_MARKER_RE.sub(lambda m: " " * len(m.group(0)), work)
        self.work = work

        self._numbers(work)
        self._words(work)
        self._names(work)

    def _numbers(self, work: str) -> None:
        for m in DIGIT_RE.finditer(work):
            num = m.group("num")
            if re.fullmatch(r"\d{1,3}(?:,\d{3})+", num):
                num = num.replace(",", "")
            unit = (m.group("unit") or "").lower()
            canon = UNIT_CANON.get(unit, "")
            cur = CURRENCY.get(m.group("cur") or "", "")
            canon = canon or cur
            self.add("numbers", f"{num}{canon}" if canon == "%" else (f"{num} {canon}" if canon else num), m.start())
        for m in WORD_NUM_RE.finditer(work):
            unit = UNIT_CANON.get((m.group("unit") or "").lower(), "")
            num = str(NUMBER_WORDS[m.group("word").lower()])
            self.add("numbers", f"{num}{unit}" if unit == "%" else (f"{num} {unit}" if unit else num), m.start())
        for m in IDENT_RE.finditer(work):
            self.add("numbers", m.group(0), m.start())

    def _words(self, work: str) -> None:
        for m in TOKEN_RE.finditer(work):
            tok = m.group(0).lower().replace("\u2019", "'")
            if tok.endswith("n't"):
                base = CONTRACTION_BASES.get(tok, tok[:-3])
                self.add("negations", "not", m.start())
                if base in CERTAINTY:
                    self.add("certainty", base, m.start())
                elif base in SCOPE:
                    self.add("scope", base, m.start())
                continue
            if tok == "cannot":
                self.add("negations", "not", m.start())
                continue
            if tok in NEGATIONS:
                self.add("negations", tok, m.start())
            if tok in CERTAINTY:
                self.add("certainty", tok, m.start())
            if tok in SCOPE:
                self.add("scope", tok, m.start())
        for m in SCOPE_PHRASE_RE.finditer(work):
            self.add("scope", m.group(0).lower(), m.start())

    def _names(self, work: str) -> None:
        for m in NAME_RE.finditer(work):
            tokens = [re.sub(r"['\u2019](?:s|m|d|ll|ve|re)$", "", t) for t in re.split(r"[ \t]+", m.group(0))]
            tokens = [t for t in tokens if t and not (len(t) == 1 and t.isalpha())]
            if not tokens:
                continue
            prefix = work[: m.start()].rstrip(" \t")
            at_start = (not prefix) or prefix[-1] in ".!?\n\"\u201c(-*\u2022>#"
            if at_start:
                while tokens and tokens[0].lower() in COMMON_START:
                    tokens.pop(0)
                if not tokens:
                    continue
                if len(tokens) == 1 and not (ACRONYM_RE.match(tokens[0]) or CAMEL_RE.match(tokens[0])):
                    self._start_singles.append((tokens[0], m.start()))
                    continue
            else:
                for t in tokens:
                    self.mid_tokens.add(t)
            self.add("names", " ".join(tokens), m.start())

    def finish(self, known: set[str]) -> None:
        for token, pos in self._start_singles:
            if token in known:
                self.add("names", token, pos)


def context(text: str, pos: int, width: int = 40) -> str:
    return flat(text[max(0, pos - width): pos + width])


def compare(before: Extraction, after: Extraction, ignore: set[str]) -> dict:
    cats = {}
    for cat in CATEGORIES:
        if cat in ignore:
            continue
        b, a = before.items[cat], after.items[cat]
        lost, added = [], []
        for item in sorted(set(b) | set(a)):
            nb = b.get(item, [0, 0])[0]
            na = a.get(item, [0, 0])[0]
            if nb > na:
                lost.append({"item": item, "before": nb, "after": na, "context": context(before.text, b[item][1])})
            elif na > nb:
                added.append({"item": item, "before": nb, "after": na, "context": context(after.text, a[item][1])})
        cats[cat] = {"before_count": sum(v[0] for v in b.values()), "after_count": sum(v[0] for v in a.values()),
                     "lost": lost, "added": added}
    return cats


def read_text(path: str) -> str:
    if path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8-sig", errors="replace")


def short(s: str, limit: int = 70) -> str:
    return s if len(s) <= limit else s[: limit - 3] + "..."


def render_human(report: dict) -> str:
    out = [f"fact_diff: {report['before']} -> {report['after']}"]
    for cat, d in report["categories"].items():
        for kind in ("lost", "added"):
            for it in d[kind]:
                out.append(f"[FLAG] {cat} {kind}: \"{short(it['item'])}\" (before {it['before']}, after {it['after']})")
                out.append(f"  -> {'before' if kind == 'lost' else 'after'}: \"...{short(it['context'], 90)}...\"")
        if not d["lost"] and not d["added"] and d["before_count"]:
            out.append(f"[OK] {cat}: {d['before_count']} unchanged")
    if report["markers_after"]:
        out.append(f"-> {report['markers_after']} [ASK AUTHOR]/[VERIFY]-style marker(s) in AFTER were not compared; "
                   "resolve them before publishing.")
    if report["ok"]:
        out.append("[OK] no mechanical preservation errors found")
    else:
        out.append(f"[FLAG] {report['lost_total']} lost, {report['added_total']} added")
    out.append("-> Mechanical check only. It does not confirm meaning, causality, attribution or certainty. "
               "Review each flagged item against what the user asked for, then read both texts.")
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Report numbers, negations, certainty words, scope words, names, URLs, code, quotes and "
                    "citations that were lost or added between BEFORE and AFTER. Never rewrites either text.")
    parser.add_argument("before", help="original text file ('-' reads stdin)")
    parser.add_argument("after", help="edited text file ('-' reads stdin)")
    parser.add_argument("--json", action="store_true", help="print one JSON object instead of text")
    parser.add_argument("--ignore", action="append", default=[], choices=CATEGORIES, metavar="CATEGORY",
                        help="skip a category, for example one the user asked to change (repeatable; "
                             + ", ".join(CATEGORIES) + ")")
    args = parser.parse_args(argv)
    if args.before == "-" and args.after == "-":
        print("fact_diff: error: only one input can be read from stdin", file=sys.stderr)
        return 2
    try:
        before_text = read_text(args.before)
        after_text = read_text(args.after)
    except OSError as exc:
        print(f"fact_diff: error: {exc.strerror or exc}: {exc.filename or ''}".rstrip(": "), file=sys.stderr)
        return 2
    before, after = Extraction(before_text), Extraction(after_text)
    known = before.mid_tokens | after.mid_tokens
    before.finish(known)
    after.finish(known)
    cats = compare(before, after, set(args.ignore))
    lost_total = sum(len(d["lost"]) for d in cats.values())
    added_total = sum(len(d["added"]) for d in cats.values())
    report = {
        "before": "<stdin>" if args.before == "-" else args.before,
        "after": "<stdin>" if args.after == "-" else args.after,
        "ok": lost_total == 0 and added_total == 0,
        "lost_total": lost_total,
        "added_total": added_total,
        "ignored": sorted(set(args.ignore)),
        "categories": cats,
        "markers_before": before.markers,
        "markers_after": after.markers,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_human(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
