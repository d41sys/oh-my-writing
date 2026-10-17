#!/usr/bin/env python3
"""Deterministic statistics benchmark for the Oh My Writing outputs.

Usage:
  python3 evals/stats.py RUN_DIR [--json OUT]                         metrics for every run, aggregates, skill-minus-baseline
  python3 evals/stats.py --compare RUN_A RUN_B --condition skill      same condition in two runs, paired on (case, host, rep)

Every output a run produced gets the same fixed set of metrics (METRICS below; rules versioned by METRICS_VERSION).
No model is involved: the same files always give the same numbers. Aggregates are means, medians and bootstrap 95%
confidence intervals (fixed seed, 2000 resamples) over cases; a case's repetitions are averaged first because
repetitions of one case are not independent cases. Differences are paired on (case, host, rep) and carry a sign-test
p-value. Metric definitions: evals/README.md ("Statistics benchmark") and the METRICS table in this file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True
EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
import grade  # noqa: E402  (loads fact_diff and slop_scan with bytecode off; reused here)

REPO = grade.REPO
METRICS_VERSION = "1"
BOOTSTRAP_SEED = 20261017
BOOTSTRAP_RESAMPLES = 2000
CONFIDENCE = 0.95
SHORT_TEXT_WORDS = 400
# Fewer paired cases than this and there is no verdict ('few'). At 3 to 5 cases the interval is only indicative: three
# same-signed case differences always exclude 0, and the sign test cannot reach p < 0.05 below 6 cases.
MIN_CASES = 3

# ---------------------------------------------------------------- metric table
# direction: "lower" or "higher" is better; None is reported but has no better/worse (it depends on the case).

METRICS: dict[str, dict] = {
    "invented_facts": {
        "direction": "lower", "unit": "count",
        "definition": "Numbers, URLs, citations (and names, where the case's own no_added_facts check covers names) in "
                      "the output that appear in none of the case's inputs, input file names or prompt "
                      "(fact_diff 'added'; the case's allow list for derived figures applies).",
        "why": "A reader acts on figures and links; an invented one is a lie they cannot see."},
    "invented_facts_per_1000w": {
        "direction": "lower", "unit": "per 1000 words",
        "definition": "invented_facts divided by output length in words, times 1000.",
        "why": "Same, but a long report is not punished for being long."},
    "lost_required_facts": {
        "direction": "lower", "unit": "count",
        "definition": "Facts the case marks as required that the output lost: misses in the case's facts_recalled list "
                      "plus source numbers/negations lost per its preserves checks. Skipped when the case names none.",
        "why": "The reader needs the facts the source thought important; a dropped 'not' reverses the meaning."},
    "slop_per_1000w": {
        "direction": "lower", "unit": "per 1000 words",
        "definition": "slop_scan findings (the case's own profile, else professional) per 1000 prose words, on the "
                      "text with gap markers removed. Not computed for analysis outputs, which quote the patterns.",
        "why": "Stock vocabulary, empty framing, staged contrasts and chatbot residue make a reader stop trusting the text."},
    "stock_phrases_per_1000w": {
        "direction": "lower", "unit": "per 1000 words",
        "definition": "Hits of a fixed list of well-known stock phrases (STOCK_PHRASES), independent of slop_scan, per "
                      "1000 words. Not computed for analysis outputs.",
        "why": "An independent cross-check: these are the phrases readers name when they say 'a chatbot wrote this'."},
    "gap_markers_leaked": {
        "direction": "lower", "unit": "count",
        "definition": "Unresolved placeholders a reader would see as unfinished work: [ASK AUTHOR ...], [VERIFY ...], "
                      "[UNTESTED ...], [TODO]/[TBD]/[INSERT ...], [Your name]-style fills, {{field}}, lorem ipsum, "
                      "XXX, bare TBD/TODO, except text that is already in the sources.",
        "why": "A letter, email or post that goes out with '[Your Name]' in it is not finished; the gate fails it in "
               "reader-facing cases (CASE_KIND)."},
    "headings_per_1000w": {
        "direction": None, "unit": "per 1000 words",
        "definition": "Markdown headings (# lines outside code) per 1000 words.",
        "why": "Context for the next metric: long documents need headings, short ones do not."},
    "short_text_headings": {
        "direction": "lower", "unit": "count",
        "definition": f"Number of markdown headings in an output under {SHORT_TEXT_WORDS} words; skipped for longer "
                      "outputs and for analysis outputs.",
        "why": "A heading on an email or a 200-word note is template scaffolding the reader has to wade through."},
    "repeated_sentences": {
        "direction": "lower", "unit": "count",
        "definition": "Sentences of 6+ words that repeat an earlier sentence: identical after lower-casing, or word "
                      "3-shingle Jaccard similarity of 0.6 or more.",
        "why": "Saying the same thing twice costs the reader time and is a mark of padding."},
    "hedge_per_1000w": {
        "direction": "lower", "unit": "per 1000 words",
        "definition": "Hedge and caveat words and phrases (HEDGES) per 1000 words.",
        "why": "Fog slows the reader and hides the claim. Some hedges are correct (the source hedged), so this is "
               "tracked but not gated by default."},
    "sentence_length_cv": {
        "direction": "higher", "unit": "ratio",
        "definition": "Standard deviation / mean of words per sentence in running prose (headings, list items, code "
                      "and quotes excluded). Needs 3 or more sentences.",
        "why": "Uniform sentence length reads as monotone and machine-made; human prose varies."},
    "mean_sentence_length": {
        "direction": None, "unit": "words",
        "definition": "Mean words per sentence in running prose. Needs 3 or more sentences.",
        "why": "Context for readability; the right length depends on the genre."},
    "flesch_reading_ease": {
        "direction": "higher", "unit": "points",
        "definition": "206.835 - 1.015 * words/sentence - 84.6 * syllables/word over running prose "
                      "(vowel-group syllable counter). Needs 3 or more sentences.",
        "why": "A direct reading-effort estimate; higher is easier."},
    "list_line_ratio": {
        "direction": None, "unit": "ratio",
        "definition": "Bullet and numbered lines divided by non-blank, non-heading, non-code lines.",
        "why": "Context: lists suit steps and reference, but a reasoning memo cut into bullets loses its reasoning."},
    "length_ratio": {
        "direction": None, "unit": "ratio",
        "definition": "Output words divided by the midpoint of the case's word_count check (min and max both set).",
        "why": "Context for the next metric."},
    "length_deviation": {
        "direction": "lower", "unit": "ratio",
        "definition": "abs(length_ratio - 1): how far the output is from the middle of the length the case asks for.",
        "why": "'Three sentences' or 'one page' is part of the request; padding and truncation both cost the reader."},
    "process_talk": {
        "direction": "lower", "unit": "count",
        "definition": "Meta-talk about the writing process inside the deliverable ('I ran', 'I rewrote', 'this report was "
                      "generated', 'as an AI', 'here is your', skill and script names), except text already in the "
                      "sources. Not computed for analysis outputs, which describe their own review.",
        "why": "The reader of the email or report does not care how it was produced."},
    "check_pass_rate": {
        "direction": "higher", "unit": "ratio",
        "definition": "Share of the case's own deterministic checks (grade.py, including 'output written') that passed.",
        "why": "The case author's definition of a correct result for this request."},
    "case_passed": {
        "direction": "higher", "unit": "0/1",
        "definition": "1 when every one of the case's checks passed.",
        "why": "A run with one broken requirement is a failed run."},
    "words": {
        "direction": None, "unit": "words",
        "definition": "Whitespace-separated tokens of the output file (the way the word_count check counts).",
        "why": "Context for every rate."},
}

# What kind of text a case's output is. Rules about it live here (versioned with the metrics):
#   reader   finished text that goes to another person as it is. A gap marker left in it is a leak.
#   draft    text the author must still finish or read (reports with open gaps, drafts whose case requires gap
#            markers): a marker is intended, so it is counted but never fails the gate.
#   analysis text about text (audits, reviews, triage, voice profiles, reviewer prompts): it quotes the patterns and
#            talks about its own review, so slop, stock-phrase, rhythm and process-talk metrics do not apply.
CASE_KIND: dict[str, str] = {
    "anti-slop-editing/clean-text-no-edit": "reader",
    "anti-slop-editing/detect-only-report": "analysis",
    "anti-slop-editing/edit-announcement-keeps-facts": "reader",
    "anti-slop-editing/protected-regions-survive": "reader",
    "author-voice/draft-in-voice-no-invention": "reader",
    "author-voice/profile-from-samples-no-biography": "analysis",
    "author-voice/single-sample-low-confidence": "analysis",
    "career-documents/cold-email-professor": "reader",
    "career-documents/resume-numbers-request": "draft",
    "career-documents/tailor-missing-skill": "reader",
    "evidence-grounded-writing/causal-overclaim-fix": "draft",
    "evidence-grounded-writing/citation-audit-unsupported-ref": "analysis",
    "evidence-grounded-writing/concise-keeps-hedge-and-scope": "reader",
    "independent-review/reviewer-prompt-no-leak": "analysis",
    "independent-review/self-review-not-independent": "analysis",
    "independent-review/triage-rejects-unsupported-fix": "analysis",
    "post-writing/blog-to-x-thread-keeps-conditions": "reader",
    "post-writing/launch-post-story-requested-none-given": "draft",
    "post-writing/newsletter-one-idea-three-tangents": "reader",
    "project-report/folder-conflict-owner-gap-embedded-instruction": "draft",
    "project-report/mixed-formats-status": "draft",
    "project-report/noisy-folder-final-report": "draft",
    "project-report/real-project-docs": "draft",
    "project-report/small-folder-short-report-no-padding": "draft",
    "project-report/system-migration-architecture": "draft",
    "report-writing/exec-summary-no-stated-recommendation": "draft",
    "report-writing/postmortem-blameless-from-blame-notes": "draft",
    "report-writing/vendor-comparison-mismatched-windows": "reader",
    "structured-drafting/meeting-notes-no-recommendation": "reader",
    "structured-drafting/tiny-email-no-scaffolding": "reader",
    "structured-drafting/transcript-contradicting-figures": "draft",
    "style/article-800-from-outline": "reader",
    "style/client-email-from-notes": "reader",
    "style/cover-letter-from-background": "reader",
    "style/decision-memo-from-notes": "reader",
    "style/incident-apology-email": "reader",
    "style/linkedin-post-from-notes": "reader",
    "style/project-update-from-notes": "reader",
    "style/revise-slop-heavy-announcement": "reader",
    "technical-docs/mixed-tutorial-and-reference-request": "reader",
    "technical-docs/pr-body-no-invented-results": "reader",
    "technical-docs/readme-from-cli-script": "reader",
}


def case_kind(case: dict) -> str:
    """Kind of a case's output; an unlisted case counts as 'draft' (never fails a reader-only rule)."""
    return CASE_KIND.get(case["id"], "draft")


# ---------------------------------------------------------------- lexicons

STOCK_PHRASES = [
    r"in today's (?:fast-paced|digital|ever-changing|ever-evolving|rapidly (?:evolving|changing)) (?:world|landscape|age|environment)",
    r"in the (?:ever-evolving|ever-changing|rapidly evolving) (?:world|landscape) of",
    r"(?:it'?s|it is) (?:important|worth|crucial|essential) (?:to note|noting|to remember|to mention)",
    r"(?:it'?s|it is) worth (?:mentioning|pointing out)",
    r"i hope this (?:email|message|note) finds you well",
    r"(?:i am|i'm|we are|we're) (?:thrilled|excited|delighted|proud|pleased|happy) to (?:announce|share|introduce)",
    r"(?:we are|we're) (?:thrilled|excited) to (?:announce|share|introduce)",
    r"\bdelve[sd]? (?:into|deeper)\b", r"\bdive (?:deep )?into\b", r"\bunlock(?:s|ed|ing)? the (?:power|potential|secrets?)\b",
    r"\bgame[- ]chang(?:er|ing)\b", r"\bgroundbreaking\b", r"\bcutting-edge\b", r"\bstate-of-the-art\b",
    r"\brich tapestry\b", r"\btapestry of\b", r"\bnavigat(?:e|ing) the (?:complexities|landscape|challenges)\b",
    r"\bat the end of the day\b", r"\bin conclusion\b", r"\bin summary\b", r"\bto summari[sz]e\b",
    r"\bin the realm of\b", r"\bplays? a (?:crucial|vital|pivotal|key|significant) role\b",
    r"\bstands? as a testament\b", r"\ba testament to\b", r"\bpave[sd]? the way\b",
    r"\bseamless(?:ly)?\b", r"\bsynerg(?:y|ies)\b",
    r"\bholistic\b", r"\btransformative\b", r"\bparadigm shift\b", r"\bmultifaceted\b",
    r"\bembark(?:s|ed|ing)? on (?:a|this) journey\b",
    r"\bfoster(?:s|ed|ing)? (?:a )?(?:culture|sense|collaboration|innovation)\b",
    r"\bnot (?:just|only) [^.!?\n]{1,60}, but (?:also )?\b",
    r"\blet'?s (?:dive|unpack|break it down|explore)\b", r"\bhere'?s the (?:thing|kicker|catch)\b",
    r"\bthe (?:best|good|real|hard|kicker) part\?",
    r"\bI'?d be (?:happy|glad) to (?:help|assist)\b", r"\bfeel free to (?:reach out|contact)\b",
    r"\bdon'?t hesitate to (?:reach out|contact)\b", r"\bplease (?:do not|don't) hesitate\b",
    r"\bin an? (?:increasingly|rapidly|ever) (?:\w+ )?(?:world|landscape)\b",
    r"\bat its core\b", r"\bbeacon of\b", r"\bvibrant\b(?= (?:community|ecosystem))",
]
STOCK_RES = [re.compile(p, re.I) for p in STOCK_PHRASES]

HEDGES = [
    r"may", r"might", r"could", r"perhaps", r"possibly", r"probably", r"arguably", r"seems?", r"seemingly",
    r"appears?", r"apparently", r"somewhat", r"relatively", r"fairly", r"potentially", r"presumably",
    r"likely", r"unlikely", r"generally", r"typically", r"usually", r"tends? to", r"to some extent",
    r"in some cases", r"it is possible", r"it'?s possible", r"it should be noted", r"it is worth noting",
    r"it'?s worth noting", r"that said", r"with that said", r"to be fair", r"of course",
]
HEDGE_RE = re.compile(r"\b(?:" + "|".join(HEDGES) + r")\b", re.I)

PROCESS_TALK = [
    r"\bI(?:'ve| have)? (?:rewrote|rewritten|edited|revised|tightened|trimmed|polished|scanned|audited|proofread|"
    r"cleaned up|took out|removed|preserved) (?:the|this|your|that|it|all|every|each)\b",
    r"\bI (?:ran|used) (?:the |a |an )?(?:scan|check|checks|audit|fact[- ]?diff|slop[- ]?scan|script|tool|linter)\b",
    r"\bthis (?:report|document|draft|email|text|post|memo|letter|update|article|summary|readme) (?:was|has been) "
    r"(?:generated|written|produced|drafted|created|edited|revised|prepared) (?:by|with|using)\b",
    r"\bas an ai\b", r"\blanguage model\b", r"\b(?:chatgpt|claude|codex|gpt-?\d)\b",
    r"\b(?:here is|here's|below is|attached is) (?:the|your|a) (?:revised|edited|updated|final|improved|cleaned|rewritten)",
    r"\bper your request\b", r"\bchanges? made\b", r"\bwhat i changed\b",
    r"\b(?:anti-slop-editing|evidence-grounded-writing|author-voice|career-documents|independent-review|post-writing|"
    r"project-report|report-writing|structured-drafting|technical-docs)\b",
    r"\bSKILL\.md\b", r"\bfact_diff\b", r"\bslop_scan\b",
]
PROCESS_RES = [re.compile(p, re.I) for p in PROCESS_TALK]

PLACEHOLDERS = [
    r"\[(?:ASK AUTHOR|VERIFY|UNTESTED)\b[^\]\n]*\]",
    r"\[(?:TODO|TBD|TBC|FIXME|INSERT|PLACEHOLDER|XX+)\b[^\]\n]*\]",
    r"\[(?:your|insert|add|fill in|company|recipient|hiring manager|job title|position|date|name|number|x+)\b[^\]\n]{0,40}\]",
    r"\{\{[^}\n]+\}\}", r"<(?:YOUR|INSERT|PLACEHOLDER)[A-Z _-]*>", r"\blorem ipsum\b",
    r"\bX{3,}\b", r"\b(?:TBD|TODO|FIXME)\b",
]
PLACEHOLDER_RES = [re.compile(p, re.I if p.startswith(r"\[(?:your") or "lorem" in p else 0) for p in PLACEHOLDERS]

# ---------------------------------------------------------------- text primitives


def words_of(text: str) -> int:
    return len(grade._words(text))


def _rate(count: float, words: int) -> float | None:
    return None if not words else count * 1000 / words


def strip_code(text: str) -> str:
    text = re.sub(r"(?ms)^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$", "", text)
    return re.sub(r"`[^`\n]+`", "", text)


def prose_sentences(text: str) -> list[list[str]]:
    """Words of each sentence in running prose (the same selection as grade.sentence_lengths)."""
    scan = grade._slop_scan()
    masked = scan.mask_protected(text)
    out = []
    for start, end in scan.prose_blocks(masked):
        for s, e in scan._sentences(masked[start:end], start):
            words = scan.WORD_RE.findall(masked[s:e])
            if words:
                out.append(words)
    return out


def syllables(word: str) -> int:
    """Vowel-group syllable count: silent final 'e' dropped, 'le' after a consonant kept, at least one."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    groups = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and groups > 1:
        groups -= 1
    elif w.endswith("es") and groups > 1 and not w.endswith(("ses", "xes", "zes", "ches", "shes", "ges", "ces")):
        groups -= 1
    elif w.endswith("ed") and groups > 1 and not w.endswith(("ted", "ded")):
        groups -= 1
    return max(1, groups)


def sentence_stats(text: str, min_sentences: int = 3) -> dict:
    """n sentences, mean words, coefficient of variation and Flesch reading ease over running prose."""
    sents = prose_sentences(text)
    if len(sents) < min_sentences:
        return {"n": len(sents), "mean": None, "cv": None, "flesch": None}
    lengths = [len(s) for s in sents]
    mean = sum(lengths) / len(lengths)
    cv = (sum((x - mean) ** 2 for x in lengths) / len(lengths)) ** 0.5 / mean
    total_words = sum(lengths)
    syl = sum(syllables(w) for s in sents for w in s)
    flesch = 206.835 - 1.015 * (total_words / len(sents)) - 84.6 * (syl / total_words)
    return {"n": len(sents), "mean": mean, "cv": cv, "flesch": flesch}


def headings(text: str) -> int:
    return len(re.findall(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+\S", strip_code(text)))


def list_line_ratio(text: str) -> float | None:
    lines = [l for l in strip_code(text).split("\n") if l.strip()]
    lines = [l for l in lines if not re.match(r"^[ \t]{0,3}#{1,6}[ \t]", l)]
    if not lines:
        return None
    items = [l for l in lines if re.match(r"^\s*(?:[-*+\u2022]|\d+[.)])\s+\S", l)]
    return len(items) / len(lines)


def _shingles(words: list[str]) -> set:
    return {tuple(words[i:i + 3]) for i in range(len(words) - 2)}


def repeated_sentences(text: str, min_words: int = 6, threshold: float = 0.6) -> int:
    """Sentences (any line, markdown marks removed, code excluded) that repeat an earlier one."""
    scan = grade._slop_scan()
    masked = scan.mask_protected(strip_code(text))
    seen: list[tuple[list[str], set]] = []
    repeats = 0
    for line in masked.split("\n"):
        line = re.sub(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|\|)", "", line)
        for s, e in scan._sentences(line, 0):
            words = [w.lower() for w in scan.WORD_RE.findall(line[s:e])]
            if len(words) < min_words:
                continue
            sh = _shingles(words)
            dup = any(words == w or (sh and sh2 and len(sh & sh2) / len(sh | sh2) >= threshold) for w, sh2 in seen)
            repeats += dup
            seen.append((words, sh))
    return repeats


def count_matches(regexes, text: str, sources_lower: str = "") -> int:
    """Matches of any regex; text that appears verbatim (case-insensitive) in the sources is not counted.
    A match inside a longer match of an earlier regex counts once."""
    taken: list[tuple[int, int]] = []
    n = 0
    for rx in regexes:
        for m in rx.finditer(text):
            if any(a <= m.start() < b for a, b in taken):
                continue
            taken.append((m.start(), m.end()))
            if sources_lower and m.group(0).lower() in sources_lower:
                continue
            n += 1
    return n


def stock_phrase_count(text: str) -> int:
    return count_matches(STOCK_RES, text)


def hedge_count(text: str) -> int:
    return len(HEDGE_RE.findall(text))


def placeholder_count(text: str, sources: str = "") -> int:
    return count_matches(PLACEHOLDER_RES, strip_code(text), sources.lower())


def process_talk_count(text: str, sources: str = "") -> int:
    return count_matches(PROCESS_RES, strip_code(text), sources.lower())


# ---------------------------------------------------------------- facts


def _case_checks(case: dict, kind: str) -> list[dict]:
    return [c for c in case["checks"] if c["type"] == kind]


def invented_facts(case: dict, text: str) -> int:
    """Items fact_diff reports as added in the case's categories (default numbers, citations, urls), against all
    sources, file names and the prompt, minus the case's own allow list. Same rule as the no_added_facts check."""
    checks = _case_checks(case, "no_added_facts")
    cats: list[str] = []
    for c in checks:
        cats += [x for x in c.get("categories", ["numbers", "citations", "urls"]) if x not in cats]
    cats = cats or ["numbers", "citations", "urls"]
    allow = {a.casefold() for c in checks for a in c.get("allow", [])}
    sources = grade.sources_blob(case)
    report = grade.fact_diff(sources, grade.TITLED_LINK.sub(r"](\1)", text))
    lexicon = grade.FACT.word_set(sources)
    n = 0
    for cat in cats:
        for it in grade._items(report, cat, "added"):
            if it["before"] != 0 or it["item"].casefold() in allow:
                continue
            if cat == "names" and not [w for w in grade.FACT.new_name_words(it["item"], lexicon) if w not in allow]:
                continue
            if cat == "urls" and grade._is_input_file_link(it["item"], case):
                continue
            n += 1
    return n


def lost_required_facts(case: dict, text: str) -> int | None:
    """Misses in facts_recalled plus items lost per preserves; None when the case names no required facts."""
    recall, keep = _case_checks(case, "facts_recalled"), _case_checks(case, "preserves")
    if not recall and not keep:
        return None
    lost = 0
    hay = grade._norm(text, True)
    for c in recall:
        lost += sum(1 for f in c["facts"] if not any(re.search(p, hay, re.I | re.M) for p in f["any"]))
    texts = grade.source_texts(case)
    for c in keep:
        report = grade.fact_diff(texts[c["source"]], text)
        allow = {a.casefold() for a in c.get("allow_lost", [])}
        for cat in c.get("categories", ["numbers", "negations"]):
            for it in grade._items(report, cat, "lost"):
                gone = it["after"] < it["before"] if cat in grade.COUNTED else it["after"] == 0
                lost += bool(gone and it["item"].casefold() not in allow)
    return lost


def slop_profile(case: dict) -> str:
    for c in case["checks"]:
        if c["type"] in {"slop_density", "max_slop", "slop_absent"} and c.get("profile"):
            return c["profile"]
    return "professional"


def length_target(case: dict) -> float | None:
    for c in _case_checks(case, "word_count"):
        if "min" in c and "max" in c:
            return (c["min"] + c["max"]) / 2
    return None


# ---------------------------------------------------------------- per-run metrics


def text_metrics(case: dict, output: str) -> dict:
    """Every text metric (not the case-check ones) for one deliverable. None means not applicable or not computable."""
    kind = case_kind(case)
    prose = grade.strip_markers(output)
    words = words_of(output)
    sources = grade.sources_blob(case)
    m: dict[str, float | None] = dict.fromkeys(METRICS)
    m["words"] = words
    inv = invented_facts(case, output)
    m["invented_facts"] = inv
    m["invented_facts_per_1000w"] = _rate(inv, words)
    m["lost_required_facts"] = lost_required_facts(case, output)
    m["gap_markers_leaked"] = placeholder_count(output, sources)
    m["headings_per_1000w"] = _rate(headings(prose), words)
    m["repeated_sentences"] = repeated_sentences(prose)
    m["hedge_per_1000w"] = _rate(hedge_count(prose), words)
    m["list_line_ratio"] = list_line_ratio(prose)
    target = length_target(case)
    if target and words:
        m["length_ratio"] = words / target
        m["length_deviation"] = abs(words / target - 1)
    if kind != "analysis":
        result = grade.slop_scan_result(prose, slop_profile(case))
        m["slop_per_1000w"] = _rate(result["summary"]["total"], result["words"])
        m["stock_phrases_per_1000w"] = _rate(stock_phrase_count(prose), words)
        m["short_text_headings"] = headings(prose) if 0 < words < SHORT_TEXT_WORDS else None
        stats = sentence_stats(prose)
        m["sentence_length_cv"], m["mean_sentence_length"], m["flesch_reading_ease"] = stats["cv"], stats["mean"], stats["flesch"]
        m["process_talk"] = process_talk_count(prose, sources)
    return m


def run_record(case: dict, meta: dict, output: str | None, reply: str, workspace: Path | None) -> dict:
    """Metrics of one run. A run the host crashed before writing the output (error set, no file) is marked
    host_error and carries no values; a run that wrote nothing without an error scores check_pass_rate 0."""
    graded = grade.grade_case(case, output, reply, workspace)
    host_error = bool(meta.get("error")) and output is None
    metrics: dict[str, float | None] = dict.fromkeys(METRICS)
    if not host_error:
        if output is not None:
            metrics.update(text_metrics(case, output))
        metrics["check_pass_rate"] = graded["score"]
        metrics["case_passed"] = 1.0 if graded["passed"] else 0.0
    return {"case": case["id"], "skill": case["skill"], "kind": case_kind(case), "host": meta["host"],
            "condition": meta["condition"], "rep": meta.get("rep") or 1, "host_error": host_error, "metrics": metrics}


def read_run(run_dir: Path, hosts: set[str] | None = None) -> tuple[dict, list[dict]]:
    """Info (run.json) and one record per run in a results directory, sorted by (case, host, condition, rep)."""
    cases = {c["id"]: c for c in grade.load_cases()}
    records = []
    for meta_path in sorted((run_dir / "runs").glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        case = cases.get(meta["case"])
        if case is None or (hosts and meta["host"] not in hosts):
            continue
        workspace = meta_path.parent / "workspace"
        out_path = workspace / case["output"]
        output = out_path.read_text(encoding="utf-8", errors="replace") if out_path.is_file() else None
        reply_path = meta_path.parent / "reply.md"
        reply = reply_path.read_text(encoding="utf-8", errors="replace") if reply_path.is_file() else ""
        for notes in sorted(workspace.glob("**/open-questions.md")) if workspace.is_dir() else []:
            reply += "\n\n" + notes.read_text(encoding="utf-8", errors="replace")
        records.append(run_record(case, meta, output, reply, workspace))
    records.sort(key=lambda r: (r["case"], r["host"], r["condition"], r["rep"]))
    info_path = run_dir / "run.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.is_file() else {}
    return info, records


# ---------------------------------------------------------------- statistics


def percentile(sorted_values: list[float], q: float) -> float:
    pos = q * (len(sorted_values) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def bootstrap_ci(values: list[float], label: str, stat=statistics.fmean) -> tuple[float, float] | None:
    """Percentile bootstrap CI of stat over values (resampled with replacement). The generator is seeded from the
    fixed seed and label, so the same data always gives the same interval."""
    if len(values) < 2:
        return None
    rng = random.Random(f"{BOOTSTRAP_SEED}:{label}")
    n = len(values)
    draws = sorted(stat(rng.choices(values, k=n)) for _ in range(BOOTSTRAP_RESAMPLES))
    tail = (1 - CONFIDENCE) / 2
    return percentile(draws, tail), percentile(draws, 1 - tail)


def sign_test_p(diffs: list[float]) -> float | None:
    """Two-sided exact binomial sign test on the non-zero differences."""
    pos, neg = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
    n = pos + neg
    if not n:
        return None
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def _case_level(pairs: dict[tuple, float]) -> dict[tuple, float]:
    """Average repetitions: {(host, case, rep): v} -> {(host, case): mean v}."""
    groups: dict[tuple, list[float]] = {}
    for (host, case, _rep), v in pairs.items():
        groups.setdefault((host, case), []).append(v)
    return {k: statistics.fmean(v) for k, v in sorted(groups.items())}


def values_by_run(records: list[dict], metric: str, **where) -> dict[tuple, float]:
    """{(host, case, rep): value} of the records matching where (condition=..., skill=...), without host errors."""
    out = {}
    for r in records:
        if r["host_error"] or any(r.get(k) != v for k, v in where.items()):
            continue
        v = r["metrics"].get(metric)
        if v is not None:
            out[(r["host"], r["case"], r["rep"])] = v
    return out


def describe(values: dict[tuple, float], label: str) -> dict:
    """Mean, median and CI over cases (repetitions averaged first)."""
    per_case = _case_level(values)
    vals = list(per_case.values())
    if not vals:
        return {"n_runs": 0, "n_cases": 0, "mean": None, "median": None, "ci": None}
    return {"n_runs": len(values), "n_cases": len(vals), "mean": statistics.fmean(vals), "median": statistics.median(vals),
            "ci": bootstrap_ci(vals, label)}


def paired(a: dict[tuple, float], b: dict[tuple, float], label: str) -> dict:
    """b minus a on the runs both have, with CI, sign-test p and the per-case differences."""
    common = sorted(set(a) & set(b))
    diffs = {k: b[k] - a[k] for k in common}
    per_case = _case_level(diffs)
    vals = list(per_case.values())
    if not vals:
        return {"n_pairs": 0, "n_cases": 0, "a_mean": None, "b_mean": None, "diff": None, "median": None, "ci": None,
                "p": None, "per_case": {}}
    return {"n_pairs": len(common), "n_cases": len(vals),
            "a_mean": statistics.fmean(_case_level({k: a[k] for k in common}).values()),
            "b_mean": statistics.fmean(_case_level({k: b[k] for k in common}).values()),
            "diff": statistics.fmean(vals), "median": statistics.median(vals),
            "ci": bootstrap_ci(vals, label), "p": sign_test_p(vals),
            "per_case": {f"{h}|{c}": v for (h, c), v in per_case.items()}}


def verdict(diff: float | None, ci, direction: str | None, n_cases: int = MIN_CASES, min_cases: int = MIN_CASES) -> str:
    """'better' / 'worse' when the CI excludes zero in that direction, 'same' otherwise, 'info' without a direction,
    'few' when fewer than min_cases cases are paired."""
    if direction is None:
        return "info"
    if diff is None or ci is None:
        return "n/a"
    if n_cases < min_cases:
        return "few"
    lo, hi = ci
    if lo > 0 or hi < 0:
        up = lo > 0
        return "better" if up == (direction == "higher") else "worse"
    return "same"


MARK = {"better": "+", "worse": "-", "same": "=", "few": "?", "n/a": ".", "info": "."}


def _scopes(records: list[dict]) -> list[str]:
    return sorted({r["skill"] for r in records}) + ["ALL"]


def _scope_filter(scope: str) -> dict:
    return {} if scope == "ALL" else {"skill": scope}


def aggregate(records: list[dict]) -> dict:
    """{host/scope/condition: {metric: describe}} and, for every non-baseline condition, the paired difference
    to baseline: {host/scope/condition: {metric: paired + verdict}}."""
    hosts = sorted({r["host"] for r in records})
    conditions = sorted({r["condition"] for r in records})
    scopes = _scopes(records)
    desc: dict[str, dict] = {}
    diffs: dict[str, dict] = {}
    for host in hosts:
        for scope in scopes:
            where = {"host": host, **_scope_filter(scope)}
            for cond in conditions:
                key = f"{host}/{scope}/{cond}"
                desc[key] = {m: describe(values_by_run(records, m, condition=cond, **where), f"{key}:{m}") for m in METRICS}
                if cond == "baseline" or "baseline" not in conditions:
                    continue
                diffs[key] = {}
                for m, spec in METRICS.items():
                    base = values_by_run(records, m, condition="baseline", **where)
                    this = values_by_run(records, m, condition=cond, **where)
                    p = paired(base, this, f"{key}-baseline:{m}")
                    p["verdict"] = verdict(p["diff"], p["ci"], spec["direction"], p["n_cases"])
                    diffs[key][m] = p
    return {"describe": desc, "skill_minus_baseline": diffs}


def compare_runs(a: list[dict], b: list[dict], condition: str) -> dict:
    """b minus a for one condition, paired on (host, case, rep), per scope and metric."""
    out: dict[str, dict] = {}
    hosts = sorted({r["host"] for r in a} & {r["host"] for r in b})
    for host in hosts:
        for scope in sorted({r["skill"] for r in a + b}) + ["ALL"]:
            where = {"host": host, "condition": condition, **_scope_filter(scope)}
            key = f"{host}/{scope}"
            out[key] = {}
            for m, spec in METRICS.items():
                p = paired(values_by_run(a, m, **where), values_by_run(b, m, **where), f"cmp {key}:{m}")
                p["verdict"] = verdict(p["diff"], p["ci"], spec["direction"], p["n_cases"])
                out[key][m] = p
    return out


# ---------------------------------------------------------------- tool fingerprint and skill versions


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def rules_digest() -> str:
    """Digest of the rule data in this file (metric table, lexicons, case kinds, thresholds), not of its code layout."""
    blob = json.dumps([METRICS, STOCK_PHRASES, HEDGES, PROCESS_TALK, PLACEHOLDERS, CASE_KIND, SHORT_TEXT_WORDS],
                      sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def tool_fingerprint() -> dict:
    """Digests of everything whose change makes old and new metric values not comparable: the two helper scripts
    the metrics call, this file's rule data and the case files (their checks decide check_pass_rate)."""
    cases = hashlib.sha256()
    for path in sorted(grade.CASES_DIR.glob("*/*.json")):
        cases.update(path.read_bytes())
    return {"fact_diff.py": file_digest(grade.FACT_DIFF), "slop_scan.py": file_digest(grade.SLOP_SCAN),
            "stats rules": rules_digest(), "cases": cases.hexdigest()[:12]}


def skill_versions() -> dict:
    out = {}
    for path in sorted(grade.SKILLS_DIR.glob("*/SKILL.md")):
        m = re.search(r"(?m)^\s+version:\s*[\"']?([^\"'\n]+)", path.read_text(encoding="utf-8").split("\n---", 2)[0])
        out[path.parent.name] = m.group(1).strip() if m else None
    return out


# ---------------------------------------------------------------- output


def _num(v, digits=2):
    if v is None:
        return "n/a"
    s = f"{v:.{digits}f}"
    return s[1:] if s.startswith("-") and not s.strip("-0.") else s  # no "-0.00"


def _ci(ci, digits=2):
    return "n/a" if ci is None else f"[{_num(ci[0], digits)}, {_num(ci[1], digits)}]"


def _fmt_p(p):
    return "n/a" if p is None else ("<0.001" if p < 0.001 else f"{p:.3f}")


def _digits(metric: str) -> int:
    return 3 if METRICS[metric]["unit"] in {"ratio", "0/1"} else 2


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)] if rows else [len(h) for h in headers]
    fmt = lambda row: "  ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip()
    return [fmt(headers), fmt(["-" * w for w in widths]), *[fmt(r) for r in rows]]


def render_run(info: dict, records: list[dict], agg: dict) -> str:
    n_err = sum(r["host_error"] for r in records)
    lines = [f"Run {info.get('id', '?')}: {len(records)} outputs, {n_err} host errors, METRICS_VERSION {METRICS_VERSION}", ""]
    conditions = sorted({r["condition"] for r in records})
    for host in sorted({r["host"] for r in records}):
        lines += [f"== {host}: all skills, mean over cases (CI 95%, bootstrap {BOOTSTRAP_RESAMPLES}, seed {BOOTSTRAP_SEED})", ""]
        base = f"{host}/ALL/baseline"
        for cond in [c for c in conditions if c != "baseline"]:
            key = f"{host}/ALL/{cond}"
            rows = []
            for m, spec in METRICS.items():
                d = agg["skill_minus_baseline"].get(key, {}).get(m)
                if d is None or d["n_pairs"] == 0:
                    continue
                dg = _digits(m)
                rows.append([m, spec["direction"] or "-", _num(d["a_mean"], dg), _num(d["b_mean"], dg),
                             _num(d["diff"], dg), _ci(d["ci"], dg), _fmt_p(d["p"]), str(d["n_cases"]), d["verdict"]])
            lines += [f"{cond} minus baseline, paired on (case, rep):", ""]
            lines += _table(["metric", "better", "baseline", cond, "diff", "95% CI", "sign p", "cases", "verdict"], rows) + [""]
        if "baseline" not in conditions:
            continue
        cond = next((c for c in conditions if c != "baseline"), None)
        if cond is None:
            continue
        lines += [f"-- {host}: per skill, {cond} minus baseline "
                  "(+ better, - worse when the CI excludes 0; = no clear change; ? too few cases)", ""]
        scopes = _scopes(records)
        gated = [m for m, s in METRICS.items() if s["direction"]]
        rows = []
        for m in gated:
            row = [m]
            for scope in scopes:
                d = agg["skill_minus_baseline"].get(f"{host}/{scope}/{cond}", {}).get(m)
                mark = MARK.get(d["verdict"], ".") if d else "."
                row.append(mark)
            rows.append(row)
        lines += _table(["metric", *[s[:14] for s in scopes]], rows) + [""]
    return "\n".join(lines)


def render_describe(agg: dict, records: list[dict], scope: str = "ALL") -> str:
    """Mean [CI] and median of every metric per host and condition for one scope (a skill name or ALL)."""
    lines = []
    for host in sorted({r["host"] for r in records}):
        conds = sorted({r["condition"] for r in records})
        rows = []
        for m in METRICS:
            row = [m]
            for cond in conds:
                d = agg["describe"][f"{host}/{scope}/{cond}"][m]
                dg = _digits(m)
                row.append("n/a" if d["mean"] is None else f"{d['mean']:.{dg}f} {_ci(d['ci'], dg)} med {d['median']:.{dg}f}")
            rows.append(row)
        lines += [f"== {host}/{scope}: mean [95% CI] and median over cases, per condition", ""]
        lines += _table(["metric", *conds], rows) + [""]
    return "\n".join(lines)


def render_metric_docs() -> str:
    lines = [f"METRICS_VERSION {METRICS_VERSION}", ""]
    for name, spec in METRICS.items():
        better = {"lower": "lower is better", "higher": "higher is better", None: "no direction (context)"}[spec["direction"]]
        lines += [f"{name}  [{spec['unit']}; {better}]", f"  definition: {spec['definition']}", f"  why a reader cares: {spec['why']}", ""]
    kinds = {"reader": [], "draft": [], "analysis": []}
    for cid, kind in CASE_KIND.items():
        kinds[kind].append(cid)
    lines += ["Case kinds (CASE_KIND):"] + [f"  {k}: {len(v)} cases" for k, v in kinds.items()]
    return "\n".join(lines)


def render_compare(label_a: str, label_b: str, condition: str, cmp: dict, where_top: int = 4) -> str:
    lines = [f"Compare {label_a} -> {label_b}, condition '{condition}', difference = {label_b} - {label_a}, paired on "
             f"(host, case, rep). CI: bootstrap over cases, seed {BOOTSTRAP_SEED}, {BOOTSTRAP_RESAMPLES} resamples. "
             f"METRICS_VERSION {METRICS_VERSION}", ""]
    for key in cmp:
        host, scope = key.split("/", 1)
        if scope != "ALL":
            continue
        lines += [f"== {key}", ""]
        rows = []
        for m, spec in METRICS.items():
            d = cmp[key][m]
            if d["n_pairs"] == 0:
                continue
            dg = _digits(m)
            rows.append([m, spec["direction"] or "-", _num(d["a_mean"], dg), _num(d["b_mean"], dg), _num(d["diff"], dg),
                         _ci(d["ci"], dg), _fmt_p(d["p"]), str(d["n_cases"]), d["verdict"]])
        lines += _table(["metric", "better", label_a, label_b, "diff", "95% CI", "sign p", "cases", "verdict"], rows) + [""]
    lines += ["== per skill: which metrics got worse (-) / better (+) with the CI excluding 0; = no clear change", ""]
    hosts = sorted({k.split("/", 1)[0] for k in cmp})
    for host in hosts:
        scopes = [k.split("/", 1)[1] for k in cmp if k.startswith(host + "/")]
        gated = [m for m, s in METRICS.items() if s["direction"]]
        rows = []
        for m in gated:
            row = [m]
            for scope in scopes:
                d = cmp[f"{host}/{scope}"][m]
                row.append(MARK[d["verdict"]]
                           if d["n_pairs"] else ".")
            rows.append(row)
        lines += _table(["metric", *[s[:14] for s in scopes]], rows) + [""]
        lines += ["Per skill, mean difference (CI), only for metrics flagged worse or better:", ""]
        rows = []
        for scope in scopes:
            for m in gated:
                d = cmp[f"{host}/{scope}"][m]
                if d["verdict"] in {"worse", "better"} and scope != "ALL":
                    rows.append([scope, m, _num(d["a_mean"], _digits(m)), _num(d["b_mean"], _digits(m)),
                                 _num(d["diff"], _digits(m)), _ci(d["ci"], _digits(m)), d["verdict"]])
        lines += (_table(["skill", "metric", label_a, label_b, "diff", "95% CI", "verdict"], rows) if rows else ["(none)"]) + [""]
    lines += ["== where: for every metric flagged worse, the cases that moved most in the wrong direction", ""]
    rows = []
    for key in cmp:
        for m, spec in METRICS.items():
            d = cmp[key][m]
            if d["verdict"] != "worse":
                continue
            sign = 1 if spec["direction"] == "lower" else -1
            worst = sorted(d["per_case"].items(), key=lambda kv: -kv[1] * sign)[:where_top]
            rows.append([key, m, "; ".join(f"{c.split('|', 1)[1]} {v:+.2f}" for c, v in worst)])
    lines += (_table(["host/scope", "metric", f"cases (mean diff, {label_b} - {label_a})"], rows)
              if rows else ["(no metric flagged worse)"]) + [""]
    lines += [f"Verdicts need at least {MIN_CASES} paired cases ('?' = fewer, no verdict).", ""]
    return "\n".join(lines)


def _json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run_dir", nargs="?", help="results directory written by run.py")
    parser.add_argument("--json", metavar="OUT", help="write records, aggregates (and comparison) as JSON")
    parser.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"), help="paired comparison of two runs")
    parser.add_argument("--condition", default="skill", help="condition to compare (default: skill)")
    parser.add_argument("--host", action="append", help="limit to this host (repeatable)")
    parser.add_argument("--detail", metavar="SCOPE", nargs="?", const="ALL",
                        help="also print mean/median/CI per condition for a skill name or ALL")
    parser.add_argument("--metrics", action="store_true", help="print every metric's definition, direction and reason, then exit")
    args = parser.parse_args(argv)
    if args.metrics:
        print(render_metric_docs())
        return 0
    hosts = set(args.host or [])
    if args.compare:
        da, db = (Path(p) for p in args.compare)
        info_a, rec_a = read_run(da, hosts)
        info_b, rec_b = read_run(db, hosts)
        cmp = compare_runs(rec_a, rec_b, args.condition)
        print(render_compare(da.name, db.name, args.condition, cmp))
        if args.json:
            Path(args.json).write_text(json.dumps(_json_safe({"metrics_version": METRICS_VERSION, "a": info_a, "b": info_b,
                                                              "condition": args.condition, "compare": cmp}),
                                                  indent=2, ensure_ascii=False), encoding="utf-8")
        return 0
    if not args.run_dir:
        parser.error("give RUN_DIR or --compare RUN_A RUN_B")
    info, records = read_run(Path(args.run_dir), hosts)
    if not records:
        print("no runs found", file=sys.stderr)
        return 1
    agg = aggregate(records)
    print(render_run(info, records, agg))
    if args.detail:
        print(render_describe(agg, records, args.detail))
    if args.json:
        Path(args.json).write_text(json.dumps(_json_safe({"metrics_version": METRICS_VERSION, "run": info, "records": records,
                                                          **agg}), indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
