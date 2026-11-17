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
                 counts only when the same word is capitalized mid-sentence).
                 A name counts as lost or added only when one of its words is
                 absent from the other text; salutations and titles (Dear, Dr,
                 Professor, Hi, ...) and contractions such as I'm are not name
                 words, and the report shows the phrase as written
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
LOCATOR_RE = re.compile(r"\b[\w./-]+\.(?:md|txt|pdf|docx?|csv|tsv|json|ya?ml|toml|py|tex|html?|xlsx?|log)"
                        r"(?::|#L|,? lines? )\d+(?:\s?[-–]\s?L?\d+)?")
# "3/7" opening or closing a line of a thread numbers the post, it states no figure
THREAD_COUNTER_RE = re.compile(r"(?m)^[ \t>*-]*\(?\d{1,2}/\d{1,2}\)?(?=[\s.:)]|$)|(?<=\s)\(?\d{1,2}/\d{1,2}\)?[ \t]*$")

NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
DIGIT_RE = re.compile(r"(?<![\w.])(?P<cur>[$\u20ac\u00a3\u00a5])?(?P<num>\d+(?:[.,]\d+)*(?:/\d+(?!\d|[.,]\d))?)"
                      r"(?:[\s-]?(?P<unit>%|per cent\b|[A-Za-z\u00b5\u00b0][A-Za-z\u00b5\u00b0/]*))?")
IDENT_RE = re.compile(r"\b[A-Za-z]+\d+(?:[.\-]\d+)*[A-Za-z]*\b")
MONTHS = {m: i for i, names in enumerate(
    [("January", "Jan"), ("February", "Feb"), ("March", "Mar"), ("April", "Apr"), ("May",), ("June", "Jun"),
     ("July", "Jul"), ("August", "Aug"), ("September", "Sept", "Sep"), ("October", "Oct"), ("November", "Nov"),
     ("December", "Dec")], start=1) for m in names}
_MONTH = "(?:" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?"
_ORD = "(?:st|nd|rd|th)?"
_RANGE = r"(?:\s?[–-]\s?|\s+(?:to|through|until|and)\s+)"
DATE_RE = re.compile(
    r"(?<![\w-])(?P<iy>\d{4})-(?P<im>\d{2})-(?P<id>\d{2})(?![\w-])"
    rf"|(?<![\w.])(?P<dd>\d{{1,2}}){_ORD}(?:{_RANGE}(?P<dd2>\d{{1,2}}){_ORD})?[\s-]+(?P<dm>{_MONTH})"
    rf"(?:,?\s+(?P<dy>\d{{4}}))?(?!\w)"
    rf"|(?<!\w)(?P<mm>{_MONTH})\s+(?P<md>\d{{1,2}}){_ORD}(?:{_RANGE}(?P<md2>\d{{1,2}}){_ORD})?"
    rf"(?:,?\s+(?P<my>\d{{4}}))?(?![\w.]\d)")


def _date_items(m: re.Match) -> list[str]:
    """'date:2026-04-06' for a full date, 'date:--04-06' when the text gives no year; a day range
    ("13–31 July") gives both ends."""
    if m.group("iy"):
        y, mo, days = m.group("iy"), int(m.group("im")), [m.group("id")]
    elif m.group("dm"):
        y, mo, days = m.group("dy"), MONTHS[m.group("dm").rstrip(".")], [m.group("dd"), m.group("dd2")]
    else:
        y, mo, days = m.group("my"), MONTHS[m.group("mm").rstrip(".")], [m.group("md"), m.group("md2")]
    return [f"date:{y}-{mo:02d}-{int(d):02d}" if y else f"date:--{mo:02d}-{int(d):02d}" for d in days if d]


def _match_dates(lost: list, added: list, before_items: dict, after_items: dict) -> tuple[list, list]:
    """Dates compare by day and month whatever the format: an added date is the source's when the source holds
    that day and month (and its year, if the added date has one, appears in the source); a lost date is kept when
    the text still names that day and month."""
    def day(item: str) -> str:
        return item[-5:]
    src_days = {day(i) for i in before_items if i.startswith("date:")}
    src_years = {i[5:9] for i in before_items if i.startswith("date:") and not i.startswith("date:--")}
    src_years |= {i for i in before_items if re.fullmatch(r"\d{4}", i)}
    out_days = {day(i) for i in after_items if i.startswith("date:")}
    added = [a for a in added if not (a["item"].startswith("date:") and day(a["item"]) in src_days
                                      and (a["item"].startswith("date:--") or a["item"][5:9] in src_years))
             and not (a["item"].startswith("date:--??-") and a["item"][-2:] in {d[-2:] for d in src_days})
             and not (re.fullmatch(r"\d{4}", a["item"]) and a["item"] in src_years)]
    lost = [l for l in lost if not (l["item"].startswith("date:") and day(l["item"]) in out_days)
            and not (l["item"].startswith("date:--??-") and l["item"][-2:] in {d[-2:] for d in out_days})]
    return lost, added


FIELD_LABEL_RE = re.compile(r"[A-Z]{3,}|[A-Z][a-z]+(?:-[A-Z][a-z]+)+")  # VERDICT, Reviewer-Model
# List markers and heading section numbers ("## 2.1 Method", "## 1. Summary") are layout, not figures. A section
# number without a closing dot or bracket needs a sub-number and a capitalised title word after it, so headings that
# carry a figure ("## 2024 results", "## 2.5 million users", "## 1.5 Billion Rows") keep it.
LIST_MARKER_RE = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]+(?:\d+(?:\.\d+)*[.)]|\d+(?:\.\d+)+(?=[ \t]+[A-Z])"
    r"(?![ \t]+(?:Million|Billion|Trillion|Thousand|Percent|Hundred)\b))|\d+[.)]|[-*+])[ \t]+", re.M)
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
# "more than ever", "less than ideal": comparison idioms, not a bound on a quantity.
SCOPE_PHRASE_RE = re.compile(r"\b(?:no more than|no fewer than|more than|less than|fewer than|at least|at most|up to)\b"
                             r"(?!\s+(?:ever|enough|anything|anyone|anybody|ideal|perfect|stellar)\b)", re.I)
CONTRACTION_BASES = {"can't": "can", "won't": "will", "shan't": "shall"}
TOKEN_RE = re.compile(r"[A-Za-z]+(?:['\u2019][A-Za-z]+)?")

CAP = r"[A-Z][A-Za-z0-9&'\u2019-]*"
NAME_RE = re.compile(r"\b" + CAP + r"(?:[ \t]+(?:(?:of|de|van|von|der|la|le|del)[ \t]+)?" + CAP + r")*")
ACRONYM_RE = re.compile(r"^(?:[A-Z]{2,}[A-Za-z0-9]*|(?:[A-Z]\.){2,})$")
CAMEL_RE = re.compile(r"^[A-Za-z]*[a-z][A-Z][A-Za-z0-9]*$|^[A-Z][a-z]+[A-Z][A-Za-z0-9]*$")
# Words that start a capitalised run without being part of a name.
SALUTATIONS = {"dear", "mr", "mrs", "ms", "dr", "prof", "professor", "hi", "hello"}
PRONOUN_CONTRACTION_RE = re.compile(r"^(?:i|you|he|she|it|we|they|that|there|here|who|what|let)['\u2019](?:m|s|d|ll|ve|re)$", re.I)
POSSESSIVE_RE = re.compile(r"['\u2019](?:s|m|d|ll|ve|re)$", re.I)
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
        # notes.md:93-108 points at a place in the source and 3/7 numbers a thread post; neither is a figure
        work = mask(work, [(m.start(), m.end()) for rx in (LOCATOR_RE, THREAD_COUNTER_RE) for m in rx.finditer(work)])

        # Quotes form their own category, but the numbers, words and names inside them are still facts
        # of the text: a figure quoted in the source and restated unquoted is not invented.
        facts = LIST_MARKER_RE.sub(lambda m: " " * len(m.group(0)), work)
        spans = []
        for rx in (STRAIGHT_QUOTE_RE, CURLY_QUOTE_RE):
            for m in rx.finditer(work):
                if "\n\n" not in m.group(0):
                    self.add("quotes", flat(m.group(1)), m.start())
                    spans.append((m.start(), m.end()))
        work = mask(work, spans)
        work = LIST_MARKER_RE.sub(lambda m: " " * len(m.group(0)), work)
        self.work = work

        self._numbers(facts)
        self._words(facts)
        self._names(facts)

    def _numbers(self, work: str) -> None:
        # A date is one fact, not three numbers: "2026-04-06", "6 April 2026" and "April 6" all become one item
        spans = []
        for m in DATE_RE.finditer(work):
            for item in _date_items(m):
                self.add("numbers", item, m.start())
            spans.append((m.start(), m.end()))
        work = mask(work, spans)
        for m in DIGIT_RE.finditer(work):
            num = m.group("num")
            if re.fullmatch(r"\d{1,3}(?:,\d{3})+", num):
                num = num.replace(",", "")
            unit = (m.group("unit") or "").lower()
            canon = UNIT_CANON.get(unit, "")
            cur = CURRENCY.get(m.group("cur") or "", "")
            canon = canon or cur
            if unit in ("st", "nd", "rd", "th") and num.isdigit() and 1 <= int(num) <= 31:
                self.add("numbers", f"date:--??-{int(num):02d}", m.start())  # "the 17th": a day of a month the text does not name
                continue
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
            tokens = [POSSESSIVE_RE.sub("", t) for t in re.split(r"[ \t]+", m.group(0)) if not PRONOUN_CONTRACTION_RE.match(t)]
            tokens = [t for t in tokens if t and not (len(t) == 1 and t.isalpha())]
            if not tokens:
                continue
            prefix = work[: m.start()].rstrip(" \t")
            # "VERDICT: ready" and "Reviewer-Model: <id>" are field labels of a template, not names
            if work[m.end(): m.end() + 1] == ":" and len(tokens) == 1 and FIELD_LABEL_RE.fullmatch(tokens[0]):
                continue
            at_start = (not prefix) or prefix[-1] in ".!?:\n\"\u201c(-*\u2022>#|"
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


def _norm_words(text: str) -> list[str]:
    """Lower-cased word chunks (letters, digits, & ' -), apostrophes normalised, possessives removed."""
    text = text.casefold().replace("\u2019", "'")
    return [w for w in (POSSESSIVE_RE.sub("", c).strip("'-") for c in re.findall(r"[a-z0-9&'-]+", text)) if w]


def word_set(text: str) -> set[str]:
    """Every word in TEXT, whole chunks and their alphanumeric parts, for deciding whether a name word is new."""
    words = set()
    for chunk in _norm_words(text):
        words.add(chunk)
        words.update(re.findall(r"[a-z0-9]+", chunk))
    return words


def new_name_words(phrase: str, known: set[str]) -> list[str]:
    """Words of a name phrase that are absent from KNOWN (the other text's word_set).

    Salutations, titles and pronoun contractions are not name words. A chunk with a digit ("GPT-4") must match
    whole; any other chunk ("Thomas-Smith") matches when each of its parts is known."""
    new = []
    for raw in phrase.split():
        if PRONOUN_CONTRACTION_RE.match(raw):
            continue
        for chunk in _norm_words(raw):
            if chunk in SALUTATIONS:
                continue
            parts = re.findall(r"[a-z0-9]+", chunk)
            if chunk in known or (not re.search(r"\d", chunk) and all(p in known for p in parts)):
                continue
            new.append(chunk)
    return new


def compare(before: Extraction, after: Extraction, ignore: set[str]) -> dict:
    cats = {}
    before_words, after_words = word_set(before.text), word_set(after.text)
    for cat in CATEGORIES:
        if cat in ignore:
            continue
        b, a = before.items[cat], after.items[cat]
        lost, added = [], []
        for item in sorted(set(b) | set(a)):
            nb = b.get(item, [0, 0])[0]
            na = a.get(item, [0, 0])[0]
            if nb > na:
                if cat == "names" and not new_name_words(item, after_words):
                    continue
                lost.append({"item": item, "before": nb, "after": na, "context": context(before.text, b[item][1])})
            elif na > nb:
                if cat == "names" and not new_name_words(item, before_words):
                    continue
                added.append({"item": item, "before": nb, "after": na, "context": context(after.text, a[item][1])})
        derived = []
        if cat == "numbers":
            lost, added = _pair_units(lost, added)
            lost, added = _match_dates(lost, added, b, a)
            added = _drop_unit_echoes(added, b)
            added, derived = _split_derived(added, b)
        cats[cat] = {"before_count": sum(v[0] for v in b.values()), "after_count": sum(v[0] for v in a.values()),
                     "lost": lost, "added": added}
        if derived:
            cats[cat]["derived"] = derived
    return cats


STRICT_UNITS = {"%", "pp", "bps", "x", "×"}  # adding these changes the meaning: 12 -> 12% is not a restatement


def _num_value(item: str) -> tuple[str, str]:
    """('512', 's') for '512.0 s'; trailing zero decimals are dropped so 512.0 and 512 compare equal."""
    num, _, unit = item.partition(" ")
    if num.endswith("%"):
        num, unit = num[:-1], "%"
    if re.fullmatch(r"\d+\.0+", num):
        num = num.split(".")[0]
    return num, unit


def _pair_units(lost: list, added: list) -> tuple[list, list]:
    """A bare figure restated with an implied unit (512.0 -> '512 seconds') or a different zero tail
    (512.0 -> 512) is the same figure: drop the pair. Different units (5 ms vs 5 s) and percent or multiplier
    units (12 -> 12%) stay flagged."""
    lost, added = list(lost), list(added)
    for a in list(added):
        a_num, a_unit = _num_value(a["item"])
        for l in lost:
            l_num, l_unit = _num_value(l["item"])
            if l_num != a_num or (l_unit and a_unit and l_unit != a_unit):
                continue
            if l_unit != a_unit and (l_unit or a_unit) in STRICT_UNITS:
                continue
            lost.remove(l)
            added.remove(a)
            break
    return lost, added


def _drop_unit_echoes(added: list, before_items: dict) -> list:
    """A bare figure whose value the source states with a unit ("180 ms" -> "the 180-to-45-ms drop", "25 minutes
    instead of 90") is that figure again, not a new one. Percent and multiplier units stay strict."""
    with_unit = set()
    for item in before_items:
        num, unit = _num_value(item)
        if unit and unit not in STRICT_UNITS:
            with_unit.add(num)
    return [a for a in added if not (_num_value(a["item"])[1] == "" and _num_value(a["item"])[0] in with_unit)]


DERIVED_MIN = 100  # a sum or difference below this matches some pair of source figures by chance; bare counts never qualify
PRODUCT_MIN = 1000  # a product of a priced or measured figure and a count (rate x volume) at or above this
OPERAND_MIN = 10  # operands under this (1, 2, 5) make chance matches; "x 1" is no calculation at all


def _as_float(num: str) -> float | None:
    try:
        return float(num)
    except ValueError:
        return None


def _exact(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(b))


def _is_year(value: float, unit: str) -> bool:
    return not unit and value.is_integer() and 1900 <= value <= 2100


def _quoted_rate(v: float) -> bool:
    """A bare fraction that reads as a quoted unit rate (0.042 per request): below 1 with two or more significant
    decimals. Round fractions (0.5, 1.5) multiply into round figures by chance, so they are not rates here."""
    return 0 < v < 1 and round(v, 1) != v


def _derivation(value: float, unit: str, pool: dict[str, set[float]]) -> str | None:
    """How value follows exactly from two different source figures, or None. Sums and differences need both
    operands in the value's own unit; a product is a price times a count: a currency amount (or a quoted rate when
    the value has no unit) times a bare count. Other units times a count (30 min x 100) hit round figures by
    chance, so they stay flagged."""
    same = sorted(v for v in pool.get(unit, set()) if v >= OPERAND_MIN and not _is_year(v, unit))
    if unit and abs(value) >= DERIVED_MIN:
        for i, x in enumerate(same):
            for y in same[i + 1:]:
                if _exact(x + y, value):
                    return f"{x:g} + {y:g}"
                if _exact(y - x, value):
                    return f"{y:g} - {x:g}"
    if abs(value) >= PRODUCT_MIN and (not unit or unit in set(CURRENCY.values())):
        rates = sorted(pool.get(unit, set())) if unit else sorted(v for v in pool.get("", set()) if _quoted_rate(v))
        counts = sorted(v for v in pool.get("", set()) if v >= OPERAND_MIN and v.is_integer() and not _is_year(v, ""))
        for x in rates:
            for n in counts:
                if x != 1 and _exact(x * n, value):
                    return f"{x:g} × {n:g}"
    return None


def _chained(value: float, unit: str, derived: dict[str, set[float]]) -> str | None:
    """A difference or sum of two figures the text itself derived (two period costs and the gap between them)."""
    same = sorted(derived.get(unit, set()))
    if abs(value) < DERIVED_MIN:
        return None
    for i, x in enumerate(same):
        for y in same[i:]:
            if _exact(x + y, value):
                return f"{x:g} + {y:g} (both derived)"
            if _exact(y - x, value):
                return f"{y:g} - {x:g} (both derived)"
    return None


def _context_figures(context: str) -> list[tuple[float, str]]:
    out = []
    for m in DIGIT_RE.finditer(context):
        num = m.group("num").replace(",", "") if re.fullmatch(r"\d{1,3}(?:,\d{3})+", m.group("num")) else m.group("num")
        value = _as_float(num)
        if value is not None:
            unit = UNIT_CANON.get((m.group("unit") or "").lower(), "") or CURRENCY.get(m.group("cur") or "", "")
            out.append((value, unit))
    return out


def _local(value: float, unit: str, context: str, pool: dict[str, set[float]]) -> str | None:
    """A gap or total of any size whose two operands are source figures written beside it ("310 ms, 10 ms over the
    300 ms limit"): the reader sees the arithmetic, so it is a calculation, not a new figure."""
    near = sorted({v for v, u in _context_figures(context) if u == unit and v in pool.get(unit, set()) and v != value})
    for i, x in enumerate(near):
        for y in near[i + 1:]:
            if _exact(y - x, value):
                return f"{y:g} - {x:g} (operands beside it)"
            if _exact(x + y, value):
                return f"{x:g} + {y:g} (operands beside it)"
    return None


def _split_derived(added: list, before_items: dict) -> tuple[list, list]:
    """New figures that follow exactly from two source figures by one sum, difference or rate-times-count, that
    combine two such figures, or whose two source operands are written right beside them, are calculations, not
    inventions: report them apart so the writer checks the arithmetic instead of hunting for a source. Otherwise
    rounded results, percentages, multipliers and small figures stay flagged, because they match some pair of
    source figures by chance."""
    pool: dict[str, set[float]] = {}
    for item in before_items:
        num, unit = _num_value(item)
        value = _as_float(num)
        if value is not None and unit not in STRICT_UNITS:
            pool.setdefault(unit, set()).add(value)
    kept, derived = [], []
    found: dict[str, set[float]] = {}
    for a in added:
        num, unit = _num_value(a["item"])
        value = _as_float(num)
        hit = None
        if value is not None and unit not in STRICT_UNITS:  # sums need a unit, so a bare year only matches a product
            hit = _derivation(value, unit, pool) or _local(value, unit, a.get("context", ""), pool)
        if hit:
            derived.append({**a, "from": hit})
            found.setdefault(unit, set()).add(value)
        else:
            kept.append(a)
    still = []
    for a in kept:
        num, unit = _num_value(a["item"])
        value = _as_float(num)
        hit = _chained(value, unit, found) if value is not None and unit not in STRICT_UNITS else None
        if hit:
            derived.append({**a, "from": hit})
        else:
            still.append(a)
    return still, derived


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
        for it in d.get("derived", []):
            out.append(f"[CHECK] {cat} derived: \"{short(it['item'])}\" = {it['from']} from the source figures; "
                       "confirm the arithmetic and that the reader sees the inputs")
        if not d["lost"] and not d["added"] and d["before_count"]:
            out.append(f"[OK] {cat}: {d['before_count']} unchanged")
    if report["markers_after"]:
        out.append(f"-> {report['markers_after']} [ASK AUTHOR]/[VERIFY]-style marker(s) in AFTER were not compared; "
                   "move the questions to the reply and clear the markers from the edited text unless the author asked for a draft to edit.")
    if report["ok"]:
        out.append("[OK] no mechanical preservation errors found")
    else:
        out.append(f"[FLAG] {report['lost_total']} lost, {report['added_total']} added")
    out.append("-> Mechanical check only. It does not confirm meaning, causality, attribution or certainty. "
               "Review each flagged item against what the user asked for, then read both texts.")
    return "\n".join(out)


def build_report(before_text: str, after_text: str, ignore: set[str] = frozenset()) -> dict:
    """The full report for two texts. The grader calls this instead of re-implementing the comparison."""
    before, after = Extraction(before_text), Extraction(after_text)
    known = before.mid_tokens | after.mid_tokens
    before.finish(known)
    after.finish(known)
    cats = compare(before, after, ignore)
    lost_total = sum(len(d["lost"]) for d in cats.values())
    added_total = sum(len(d["added"]) for d in cats.values())
    return {
        "before": "",
        "after": "",
        "ok": lost_total == 0 and added_total == 0,
        "lost_total": lost_total,
        "added_total": added_total,
        "ignored": sorted(ignore),
        "categories": cats,
        "markers_before": before.markers,
        "markers_after": after.markers,
    }


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
    report = build_report(before_text, after_text, set(args.ignore))
    report["before"] = "<stdin>" if args.before == "-" else args.before
    report["after"] = "<stdin>" if args.after == "-" else args.after
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_human(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
