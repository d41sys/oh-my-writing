#!/usr/bin/env python3
"""Measure observable writing traits in one or more samples.

Usage:
    python voice_stats.py FILE [FILE ...]          human-readable report
    python voice_stats.py --json FILE [FILE ...]   machine-readable report
    cat draft.md | python voice_stats.py -         read one sample from stdin

Every file is one sample. The report has per-sample figures, pooled figures for
all samples together, how far the samples spread apart, and 2-3 word phrases
that recur in at least two different samples.

These are observations, not targets. The script never rewrites the text and
never says what a writer should do. Use it as evidence for a voice profile, or
as a yardstick when comparing a draft with one.

What is measured
    words, sentences, paragraphs          prose only (see below)
    sentence length                       mean, median, population stdev, min, max
    paragraph length                      mean words and mean sentences
    questions / exclamations              per 100 sentences
    I/me/my, we/us/our, you/your          per 1000 words
    contractions                          per 1000 words
    em dash, semicolon, colon, "("        per 1000 words
    bullet_line_ratio                     bullet items / (bullet items + paragraphs)
    recurring phrases                     2-3 word phrases found in >= 2 samples

What counts as prose
    Dropped: YAML front matter, fenced code, inline code, URLs, HTML tags,
    block quotes, tables, headings (counted separately), horizontal rules.
    Each bullet item is one sentence unit. A line ending in a colon that sits
    directly above a bullet list is a lead-in: its words count, but it is not
    a paragraph. Link text is kept; the link target is dropped.

Limits
    Pronoun, contraction and phrase-filter lists are English only. A sample of
    30+ words in which fewer than 8% of words are common English function words
    is treated as not English: the English-only rates become null (n/a).
    Counting is whitespace based, so Vietnamese counts syllables as words and CJK text is
    not segmented; compare numbers only between samples in the same language.
    Em dash counts the em dash character, a spaced "--" and a spaced en dash. Sentences are
    split on . ! ? followed by whitespace, with common abbreviations
    (Dr., Mr., e.g., U.S., vs., Fig.) protected.

Exit codes: 0 report produced (flags are observations, not failures);
2 usage error or unreadable file.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field

SHORT_SAMPLE_WORDS = 100
MIN_SAMPLES_FOR_PROFILE = 5
MIN_TOTAL_WORDS_FOR_PROFILE = 1000
SPREAD_MIN_WORDS = 100
ENGLISH_SHARE_FLOOR = 0.08
LEXICAL_MIN_WORDS = 30

FIRST_SINGULAR = {"i", "i'm", "i've", "i'll", "i'd", "me", "my", "mine", "myself"}
FIRST_PLURAL = {"we", "we're", "we've", "we'll", "we'd", "us", "our", "ours", "ourselves"}
SECOND_PERSON = {"you", "you're", "you've", "you'll", "you'd", "your", "yours",
                 "yourself", "yourselves", "y'all"}
CONTRACTED_S = {"let's", "it's", "that's", "what's", "there's", "here's", "he's",
                "she's", "who's", "where's", "how's", "when's", "why's"}
_CONTRACTION_SUFFIX = re.compile(r"n't$|'(?:re|ve|ll|d|m)$")

STOPWORDS = frozenset(
    """a an the and or but nor so yet of to in on at by for from with without into onto
    about over under as if than then that this these those there here it its is are was
    were be been being am do does did done have has had having not no can could will would
    shall should may might must i me my mine we us our ours you your yours he him his she
    her hers they them their theirs what which who whom whose when where why how also just
    very too up out off""".split()
)
# Common English function words used only to judge whether the sample is English.
ENGLISH_FUNCTION_WORDS = frozenset(
    """the a an and or of to in is are was it that this for on with as be not but at by from
    have has had i you we they he she his her their our will would can could do does""".split()
)

_WORD = re.compile(r"[^\W_]+(?:['\-][^\W_]+)*")
_FENCE = re.compile(r"^\s{0,3}(```|~~~)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}(?:\s|$)")
_RULE = re.compile(r"^\s*([-*_=])(?:\s*\1){2,}\s*$")
_BULLET = re.compile(r"^\s*(?:[-*+\u2022]|\d{1,3}[.)])\s+(\S.*)$")
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_URL = re.compile(r"(?:https?://|www\.)\S+")
_TAG = re.compile(r"<[^>\n]+>")
_ABBREV = re.compile(r"\b(?:mr|mrs|ms|dr|prof|vs|fig|eq|cf)\.", re.IGNORECASE)
_INITIALISM = re.compile(r"(?<![A-Za-z])(?:[A-Za-z]\.){2,}")
_SENT_SPLIT = re.compile(r"(?<=[.!?\u2026])[\"')\]\u201d\u2019\u00bb]*\s+(?=[\"'(\[\u201c\u2018\u00ab]*[^\W_])")
_TERMINAL = re.compile(r"[.!?\u2026]+$")
_COLON = re.compile(r"(?<!\d):|:(?!\d)")
_DASH_SPACED = re.compile(r"(?<=\s)(?:--|\u2013)(?=\s)")
_CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]")


@dataclass
class Raw:
    """Raw counts for one sample (or a pool of samples)."""

    name: str = ""
    sentence_lengths: list[int] = field(default_factory=list)
    para_words: list[int] = field(default_factory=list)
    para_sentences: list[int] = field(default_factory=list)
    items: int = 0
    headings: int = 0
    questions: int = 0
    exclamations: int = 0
    counts: Counter = field(default_factory=Counter)
    cjk_chars: int = 0
    nonspace_chars: int = 0
    ngrams: Counter = field(default_factory=Counter)

    @property
    def words(self) -> int:
        return sum(self.sentence_lengths)

    def merge(self, other: "Raw") -> None:
        self.sentence_lengths += other.sentence_lengths
        self.para_words += other.para_words
        self.para_sentences += other.para_sentences
        self.items += other.items
        self.headings += other.headings
        self.questions += other.questions
        self.exclamations += other.exclamations
        self.counts.update(other.counts)
        self.cjk_chars += other.cjk_chars
        self.nonspace_chars += other.nonspace_chars
        self.ngrams.update(other.ngrams)


def _strip_front_matter(lines: list[str]) -> list[str]:
    if lines and lines[0].strip() == "---" and len(lines) > 1 and re.match(r"^[\w-]+\s*:", lines[1]):
        for i in range(1, min(len(lines), 60)):
            if lines[i].strip() in ("---", "..."):
                return lines[i + 1:]
    return lines


def _clean_inline(text: str) -> str:
    text = _INLINE_CODE.sub(" ", text)
    text = _LINK.sub(r"\1", text)
    text = _URL.sub(" ", text)
    text = _TAG.sub(" ", text)
    return text.replace("\u2019", "'").replace("\u2018", "'")


def parse_blocks(text: str) -> tuple[list[str], list[str], list[str], int]:
    """Split text into (paragraphs, bullet items, lead-ins, heading count)."""
    lines = _strip_front_matter(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
    paras: list[str] = []
    items: list[str] = []
    lead_ins: list[str] = []
    headings = 0
    para: list[str] = []
    item: list[str] | None = None
    in_fence = False

    def flush_para(next_is_bullet: bool = False) -> None:
        if not para:
            return
        joined = " ".join(para)
        para.clear()
        if next_is_bullet and joined.rstrip().endswith(":"):
            lead_ins.append(joined)
        else:
            paras.append(joined)

    def flush_item() -> None:
        nonlocal item
        if item is not None:
            items.append(" ".join(item))
            item = None

    for line in lines:
        if _FENCE.match(line):
            flush_para()
            flush_item()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            flush_para()
            flush_item()
            continue
        if _HEADING.match(line):
            flush_para()
            flush_item()
            headings += 1
            continue
        stripped = line.lstrip()
        if stripped.startswith((">", "|")) or _RULE.match(line):
            flush_para()
            flush_item()
            continue
        match = _BULLET.match(line)
        if match:
            flush_para(next_is_bullet=True)
            flush_item()
            item = [match.group(1).strip()]
            continue
        if item is not None and line[:1] in " \t":
            item.append(line.strip())
            continue
        flush_item()
        para.append(line.strip())
    flush_para()
    flush_item()
    return paras, items, lead_ins, headings


def split_sentences(text: str) -> list[str]:
    protected = _ABBREV.sub(lambda m: m.group(0)[:-1] + "\x00", text)
    protected = _INITIALISM.sub(lambda m: m.group(0).replace(".", "\x00"), protected)
    parts = _SENT_SPLIT.split(protected.strip())
    return [p.replace("\x00", ".").strip() for p in parts if p.strip()]


def _tokens(sentence: str) -> list[str]:
    return _WORD.findall(sentence)


def _is_contraction(token: str) -> bool:
    return token in CONTRACTED_S or bool(_CONTRACTION_SUFFIX.search(token))


def analyze_text(text: str, name: str = "") -> Raw:
    raw = Raw(name=name)
    paras, items, lead_ins, raw.headings = parse_blocks(text)
    raw.items = 0

    def consume(segment: str) -> int:
        """Count one block; return its number of sentences (0 if no words)."""
        segment = _clean_inline(segment)
        sentences = []
        for sentence in split_sentences(segment):
            tokens = _tokens(sentence)
            if tokens:
                sentences.append((sentence, tokens))
        if not sentences:
            return 0
        raw.counts["em_dash"] += segment.count("\u2014") + len(_DASH_SPACED.findall(segment))
        raw.counts["semicolon"] += segment.count(";")
        raw.counts["colon"] += len(_COLON.findall(segment))
        raw.counts["parenthesis"] += segment.count("(")
        compact = re.sub(r"\s+", "", segment)
        raw.nonspace_chars += len(compact)
        raw.cjk_chars += len(_CJK.findall(compact))
        for sentence, tokens in sentences:
            raw.sentence_lengths.append(len(tokens))
            terminal = _TERMINAL.search(sentence.rstrip("\"')]\u201d\u2019\u00bb"))
            if terminal:
                raw.questions += "?" in terminal.group(0)
                raw.exclamations += "!" in terminal.group(0)
            lowered = [t.lower() for t in tokens]
            for original, low in zip(tokens, lowered):
                if low in FIRST_SINGULAR:
                    raw.counts["first_singular"] += 1
                elif low in FIRST_PLURAL and original != "US":
                    raw.counts["first_plural"] += 1
                elif low in SECOND_PERSON:
                    raw.counts["second"] += 1
                if _is_contraction(low):
                    raw.counts["contraction"] += 1
                if low in ENGLISH_FUNCTION_WORDS:
                    raw.counts["function_words"] += 1
            for n in (2, 3):
                for i in range(len(lowered) - n + 1):
                    gram = lowered[i:i + n]
                    if any(t.isdigit() for t in gram) or all(t in STOPWORDS for t in gram):
                        continue
                    raw.ngrams[" ".join(gram)] += 1
        return len(sentences)

    for segment in lead_ins:
        consume(segment)
    for segment in items:
        if consume(segment):
            raw.items += 1
    for segment in paras:
        before = len(raw.sentence_lengths)
        count = consume(segment)
        if count:
            raw.para_sentences.append(count)
            raw.para_words.append(sum(raw.sentence_lengths[before:]))
    return raw


def _round(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)


def _rate(count: int, base: int, scale: int) -> float | None:
    return round(count * scale / base, 2) if base else None


def _lexical_rate(count: int, words: int, english: bool | None) -> float | None:
    """English-only rate; None when the sample clearly is not English."""
    return None if english is False else _rate(count, words, 1000)


def sentence_stats(lengths: list[int]) -> dict:
    if not lengths:
        return {"mean": None, "median": None, "stdev": None, "min": None, "max": None}
    return {
        "mean": round(statistics.fmean(lengths), 2),
        "median": round(statistics.median(lengths), 2),
        "stdev": round(statistics.pstdev(lengths), 2),
        "min": min(lengths),
        "max": max(lengths),
    }


def metrics_from_raw(raw: Raw) -> dict:
    words = raw.words
    sentences = len(raw.sentence_lengths)
    paragraphs = len(raw.para_words)
    c = raw.counts
    denominator = raw.items + paragraphs
    share = round(c["function_words"] / words, 3) if words else None
    english = (share >= ENGLISH_SHARE_FLOOR) if (words >= LEXICAL_MIN_WORDS and share is not None) else None
    metrics = {
        "name": raw.name,
        "words": words,
        "sentences": sentences,
        "paragraphs": paragraphs,
        "headings": raw.headings,
        "sentence_length": sentence_stats(raw.sentence_lengths),
        "paragraph_length": {
            "words_mean": _round(statistics.fmean(raw.para_words)) if raw.para_words else None,
            "sentences_mean": _round(statistics.fmean(raw.para_sentences)) if raw.para_sentences else None,
        },
        "questions_per_100_sentences": _rate(raw.questions, sentences, 100),
        "exclamations_per_100_sentences": _rate(raw.exclamations, sentences, 100),
        "per_1000_words": {
            "first_person_singular": _lexical_rate(c["first_singular"], words, english),
            "first_person_plural": _lexical_rate(c["first_plural"], words, english),
            "second_person": _lexical_rate(c["second"], words, english),
            "contractions": _lexical_rate(c["contraction"], words, english),
            "em_dash": _rate(c["em_dash"], words, 1000),
            "semicolon": _rate(c["semicolon"], words, 1000),
            "colon": _rate(c["colon"], words, 1000),
            "parenthesis": _rate(c["parenthesis"], words, 1000),
        },
        "bullet_items": raw.items,
        "bullet_line_ratio": round(raw.items / denominator, 3) if denominator else None,
        "english_function_word_share": share,
        "lexical_lists_apply": english,
    }
    metrics["warnings"] = sample_warnings(raw, metrics)
    return metrics


def sample_warnings(raw: Raw, metrics: dict) -> list[str]:
    warnings = []
    words = metrics["words"]
    if words == 0:
        warnings.append("no prose words found (empty, or only code, quotes, tables or headings)")
        return warnings
    if words < SHORT_SAMPLE_WORDS:
        warnings.append(f"short sample (under {SHORT_SAMPLE_WORDS} words): rates are unstable")
    if metrics["lexical_lists_apply"] is False:
        warnings.append("does not look like English: pronoun and contraction figures are "
                        "left blank (n/a) and the phrase filter is unreliable; structural figures still apply")
    if raw.nonspace_chars and raw.cjk_chars / raw.nonspace_chars > 0.3:
        warnings.append("mostly CJK characters: words are not segmented, so length figures are not comparable")
    return warnings


SPREAD_SPECS = [
    ("mean sentence length", lambda m: m["sentence_length"]["mean"], 1.5, 6.0),
    ("contractions per 1000 words", lambda m: m["per_1000_words"]["contractions"], 2.0, 5.0),
    ("I/me/my per 1000 words", lambda m: m["per_1000_words"]["first_person_singular"], 2.0, 5.0),
    ("you/your per 1000 words", lambda m: m["per_1000_words"]["second_person"], 2.0, 5.0),
    ("em dashes per 1000 words", lambda m: m["per_1000_words"]["em_dash"], 2.0, 5.0),
    ("bullet_line_ratio", lambda m: m["bullet_line_ratio"], 1.0, 0.4),
]


def spread(samples: list[dict]) -> list[dict]:
    eligible = [m for m in samples if m["words"] >= SPREAD_MIN_WORDS]
    if len(eligible) < 2:
        return []
    out = []
    for label, getter, min_ratio, min_diff in SPREAD_SPECS:
        pairs = [(getter(m), m["name"]) for m in eligible if getter(m) is not None]
        if len(pairs) < 2:
            continue
        low, high = min(pairs, key=lambda p: p[0]), max(pairs, key=lambda p: p[0])
        diff = high[0] - low[0]
        ratio_ok = low[0] == 0 or high[0] / low[0] >= min_ratio
        out.append({
            "metric": label,
            "min": low[0], "min_sample": low[1],
            "max": high[0], "max_sample": high[1],
            "split": bool(diff >= min_diff and ratio_ok),
        })
    return out


def recurring_phrases(raws: list[Raw], min_samples: int, top: int) -> list[dict]:
    membership: dict[str, list[str]] = {}
    totals: Counter = Counter()
    for raw in raws:
        for gram, count in raw.ngrams.items():
            membership.setdefault(gram, []).append(raw.name)
            totals[gram] += count
    kept = {g: names for g, names in membership.items() if len(names) >= min_samples}
    trigrams = [g for g in kept if g.count(" ") == 2]
    result = []
    for gram, names in kept.items():
        if gram.count(" ") == 1:
            covered = any(
                (f" {gram} " in f" {t} ") and totals[t] == totals[gram] and len(kept[t]) == len(names)
                for t in trigrams
            )
            if covered:
                continue
        result.append({"phrase": gram, "samples": len(names), "count": totals[gram], "in": sorted(names)})
    result.sort(key=lambda r: (-r["samples"], -r["count"], r["phrase"]))
    return result[:top]


def build_report(named_texts: list[tuple[str, str]], top: int, min_samples: int) -> dict:
    raws = [analyze_text(text, name) for name, text in named_texts]
    pooled = Raw(name="aggregate")
    for raw in raws:
        pooled.merge(raw)
    samples = [metrics_from_raw(r) for r in raws]
    aggregate = metrics_from_raw(pooled)
    aggregate["sample_count"] = len(raws)
    notes = []
    if len(raws) < MIN_SAMPLES_FOR_PROFILE:
        notes.append(f"fewer than {MIN_SAMPLES_FOR_PROFILE} samples: treat every trait as provisional")
    if aggregate["words"] < MIN_TOTAL_WORDS_FOR_PROFILE:
        notes.append(f"under {MIN_TOTAL_WORDS_FOR_PROFILE} words in total: treat every trait as provisional")
    notes.append("observations from these samples, not targets")
    return {
        "samples": samples,
        "aggregate": aggregate,
        "spread": spread(samples),
        "recurring_phrases": recurring_phrases(raws, min_samples, top) if len(raws) >= min_samples else [],
        "notes": notes,
    }


def _fmt(value: object) -> str:
    return "n/a" if value is None else str(value)


def render_metrics(m: dict, lines: list[str]) -> None:
    sl, pl, rates = m["sentence_length"], m["paragraph_length"], m["per_1000_words"]
    lines.append(f"  -> sentence length: mean {_fmt(sl['mean'])}, median {_fmt(sl['median'])}, "
                 f"stdev {_fmt(sl['stdev'])}, range {_fmt(sl['min'])}-{_fmt(sl['max'])}")
    lines.append(f"  -> paragraph: {_fmt(pl['words_mean'])} words, {_fmt(pl['sentences_mean'])} sentences on average")
    lines.append(f"  -> per 100 sentences: questions {_fmt(m['questions_per_100_sentences'])}, "
                 f"exclamations {_fmt(m['exclamations_per_100_sentences'])}")
    lines.append(f"  -> per 1000 words: I/me/my {_fmt(rates['first_person_singular'])}, "
                 f"we/us/our {_fmt(rates['first_person_plural'])}, you/your {_fmt(rates['second_person'])}, "
                 f"contractions {_fmt(rates['contractions'])}")
    lines.append(f"  -> per 1000 words: em dash {_fmt(rates['em_dash'])}, semicolon {_fmt(rates['semicolon'])}, "
                 f"colon {_fmt(rates['colon'])}, parenthesis {_fmt(rates['parenthesis'])}")
    lines.append(f"  -> bullets: {m['bullet_items']} items, bullet_line_ratio {_fmt(m['bullet_line_ratio'])}; "
                 f"headings: {m['headings']}")


def render_human(report: dict) -> str:
    lines = ["Voice statistics (observations from these samples, not targets)"]
    for m in report["samples"] + [report["aggregate"]]:
        label = m["name"] if m["name"] != "aggregate" else f"aggregate of {report['aggregate']['sample_count']} sample(s)"
        lines.append(f"[OK] {label}: {m['words']} words, {m['sentences']} sentences, {m['paragraphs']} paragraphs")
        if m["words"]:
            render_metrics(m, lines)
        for warning in m["warnings"]:
            lines.append(f"[FLAG] {label}: {warning}")
    for entry in report["spread"]:
        if entry["split"]:
            lines.append(f"[FLAG] spread: {entry['metric']} runs {entry['min']} ({entry['min_sample']}) to "
                         f"{entry['max']} ({entry['max_sample']}); samples may mix channels or registers, "
                         "so consider profiling them as separate sets")
        else:
            lines.append(f"[OK] spread: {entry['metric']} runs {entry['min']} to {entry['max']}")
    phrases = report["recurring_phrases"]
    if phrases:
        lines.append("Recurring phrases (found in several samples)")
        for p in phrases:
            lines.append(f'  -> "{p["phrase"]}" ({p["samples"]} samples, {p["count"]} uses: {", ".join(p["in"])})')
    elif report["aggregate"]["sample_count"] < 2:
        lines.append("[FLAG] recurring phrases need at least 2 samples")
    else:
        lines.append("[OK] no 2-3 word phrase recurs across samples")
    for note in report["notes"]:
        lines.append(f"[FLAG] {note}" if note.startswith(("fewer", "under")) else f"-> {note}")
    return "\n".join(lines)


def read_sample(path: str) -> tuple[str, str]:
    if path == "-":
        return "<stdin>", sys.stdin.read()
    with open(path, encoding="utf-8-sig") as handle:
        return path, handle.read()


def _min_two(value: str) -> int:
    number = int(value)
    if number < 2:
        raise argparse.ArgumentTypeError("must be at least 2")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure observable voice traits (sentence length, person, contractions, "
                    "punctuation, bullets, recurring phrases) in writing samples. "
                    "Observations only; never rewrites text.",
    )
    parser.add_argument("files", nargs="*", metavar="FILE",
                        help="sample files, one sample each; '-' reads stdin (also the default when stdin is piped)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of the text report")
    parser.add_argument("--top", type=int, default=15, help="max recurring phrases to list (default 15)")
    parser.add_argument("--min-samples", type=_min_two, default=2,
                        help="a phrase must appear in this many samples (default 2)")
    args = parser.parse_args(argv)

    paths = args.files
    if not paths:
        if sys.stdin.isatty():
            parser.error("give at least one FILE, or pipe text on stdin")
        paths = ["-"]
    try:
        named_texts = [read_sample(p) for p in paths]
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read sample: {exc}", file=sys.stderr)
        return 2

    report = build_report(named_texts, top=max(args.top, 0), min_samples=args.min_samples)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_human(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
