#!/usr/bin/env python3
"""How much of a skill's own instruction text repeats itself, for our skills and the competitor skills.

The text measured is what an agent reads when the skill loads: SKILL.md and the Markdown or text files beside it.
Repository files no agent loads (README, LICENSE, CHANGELOG, CONTRIBUTING, eval.md, tests) are left out, and so is
fenced code, which repeats by nature. Every figure is a property of the files, not a sample, so it has no interval.

  python3 evals/source_duplication.py                 # print the table
  python3 evals/source_duplication.py --out FILE.md   # also write it

Metrics, all per skill (one row per installed skill folder) and pooled per side:
  dup_sentence_share  share of sentences (6+ words) whose normalised text occurs more than once
  near_dup_share      share of the remaining sentences with a near twin (word-trigram Jaccard >= 0.6)
  repeated_8gram      share of word positions covered by an 8-word run that occurs more than once
  cross_skill_8gram   (library row only) share of positions whose 8-word run also occurs in another skill
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_NAMES = {"readme.md", "license", "license.md", "license.txt", "changelog.md", "contributing.md", "eval.md",
              "code_of_conduct.md", "security.md", "notice", "notice.md"}
SKIP_DIRS = {"tests", "test", ".git", ".github", "node_modules", "__pycache__", "evals", "examples-output", "docs"}
COPY_SHARE = 0.8  # a file whose 8-word runs mostly occur in its sibling files is a whole-file copy (a bundle)
TEXT_SUFFIXES = {".md", ".txt", ".markdown"}
FENCE = re.compile(r"^```.*?^```", re.S | re.M)
WORD = re.compile(r"[a-z0-9']+")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
MIN_WORDS = 6
NEAR = 0.6
GRAM = 8


def skill_files(folder: Path) -> list[Path]:
    out = []
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder).parts
        if (not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES or p.name.lower() in SKIP_NAMES
                or p.name.lower().startswith("readme")
                or any(part in SKIP_DIRS for part in rel[:-1])):
            continue
        out.append(p)
    return out


def text_of(files: list[Path]) -> str:
    return "\n\n".join(FENCE.sub("", p.read_text(encoding="utf-8", errors="replace")) for p in files)


def sentences(text: str) -> list[tuple[str, ...]]:
    out = []
    for raw in SENT_SPLIT.split(text):
        words = tuple(WORD.findall(raw.lower()))
        if len(words) >= MIN_WORDS:
            out.append(words)
    return out


def _trigrams(words: tuple[str, ...]) -> set[tuple[str, ...]]:
    return {words[i:i + 3] for i in range(len(words) - 2)}


def duplication(text: str) -> dict:
    sents = sentences(text)
    counts = Counter(sents)
    exact = [s for s in sents if counts[s] > 1]
    unique = [s for s in counts if counts[s] == 1]
    grams = [_trigrams(s) for s in unique]
    index: dict[tuple, list[int]] = defaultdict(list)
    for i, g in enumerate(grams):
        for t in g:
            index[t].append(i)
    near = set()
    for i, g in enumerate(grams):
        seen = Counter(j for t in g for j in index[t] if j != i)
        for j, shared in seen.items():
            if shared / (len(g) + len(grams[j]) - shared) >= NEAR:
                near.update((i, j))
    words = WORD.findall(text.lower())
    runs = Counter(tuple(words[i:i + GRAM]) for i in range(len(words) - GRAM + 1))
    covered = [False] * len(words)
    for i in range(len(words) - GRAM + 1):
        if runs[tuple(words[i:i + GRAM])] > 1:
            covered[i:i + GRAM] = [True] * GRAM
    return {"words": len(words), "sentences": len(sents),
            "dup_sentence_share": len(exact) / len(sents) if sents else 0.0,
            "near_dup_share": len(near) / len(sents) if sents else 0.0,
            "repeated_8gram": sum(covered) / len(words) if words else 0.0}


def whole_file_copies(files: list[Path]) -> list[Path]:
    """Files at least COPY_SHARE of whose 8-word runs also occur in another file of the same skill. Of two
    mutual copies, the larger one (the bundle) is reported."""
    runs = {}
    for p in files:
        w = WORD.findall(FENCE.sub("", p.read_text(encoding="utf-8", errors="replace")).lower())
        runs[p] = {tuple(w[i:i + GRAM]) for i in range(len(w) - GRAM + 1)}
    copies = []
    for p in sorted(files, key=lambda f: -len(runs[f])):
        others = set().union(*(runs[q] for q in files if q != p and q not in copies)) if len(files) > 1 else set()
        if runs[p] and len(runs[p] & others) / len(runs[p]) >= COPY_SHARE:
            copies.append(p)
    return copies


def cross_skill(texts: dict[str, str]) -> float:
    """Share of all word positions whose 8-word run also occurs in a different skill of the same side."""
    owners: dict[tuple, set[str]] = defaultdict(set)
    toks = {k: WORD.findall(t.lower()) for k, t in texts.items()}
    for k, w in toks.items():
        for i in range(len(w) - GRAM + 1):
            owners[tuple(w[i:i + GRAM])].add(k)
    total = covered_total = 0
    for k, w in toks.items():
        covered = [False] * len(w)
        for i in range(len(w) - GRAM + 1):
            if len(owners[tuple(w[i:i + GRAM])]) > 1:
                covered[i:i + GRAM] = [True] * GRAM
        total += len(w)
        covered_total += sum(covered)
    return covered_total / total if total else 0.0


def units() -> dict[str, dict[str, list[Path]]]:
    """side -> skill name -> files. Our side is every folder in skills/; a competitor is what the benchmark installs."""
    sides: dict[str, dict[str, list[Path]]] = {"ours": {}}
    for d in sorted((ROOT / "skills").iterdir()):
        if (d / "SKILL.md").is_file():
            sides["ours"][d.name] = skill_files(d)
    spec = json.loads((ROOT / "evals" / "competitors.json").read_text(encoding="utf-8"))
    cache = ROOT / spec.get("cache", ".cache/omw_sources")
    for name, comp in spec["competitors"].items():
        repo = cache / comp["repo"]
        if not repo.is_dir():
            continue
        side = {}
        for item in comp.get("install", []):
            folder = repo / item["from"]
            for skill_md in sorted(folder.rglob("SKILL.md")):
                if any(part in SKIP_DIRS for part in skill_md.relative_to(folder).parts[:-1]):
                    continue
                side[skill_md.parent.name if skill_md.parent != repo else name] = skill_files(skill_md.parent)
            if not any(folder.rglob("SKILL.md")) and folder.is_dir():  # shared material a skill reads
                side[f"{item['from']} (shared)"] = skill_files(folder)
        if side:
            sides[name] = side
    return sides


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def report() -> str:
    lines = ["# Duplication inside skill sources", "",
             "Measured on the text an agent loads (SKILL.md and Markdown beside it; no README, LICENSE, eval.md, "
             "tests or fenced code). Pooled = all of a side's skills as one corpus.", "",
             "| side | skills | words | duplicate sentences | near-duplicate sentences | repeated 8-word runs | "
             "8-word runs shared across its skills | whole-file copies |", "|---|---|---|---|---|---|---|---|"]
    detail = ["", "## Per skill", "", "| side | skill | words | duplicate sentences | near-duplicate sentences | "
              "repeated 8-word runs |", "|---|---|---|---|---|---|"]
    all_units = units()
    rows = []
    for side, skills in all_units.items():
        copies = {k: whole_file_copies(v) for k, v in skills.items()}
        rows.append((side, skills, copies, False))
        if any(copies.values()):
            rows.append((f"{side} without copies", {k: [f for f in v if f not in copies[k]] for k, v in skills.items()},
                         {k: [] for k in skills}, True))
    for side, skills, copies, _ in rows:
        texts = {k: text_of(v) for k, v in skills.items() if v}
        copy_names = ", ".join(f.name for v in copies.values() for f in v) or "none"
        pooled = duplication("\n\n".join(texts.values()))
        within = sum(duplication(t)["repeated_8gram"] * len(WORD.findall(t.lower())) for t in texts.values())
        within /= max(1, pooled["words"])
        cross = cross_skill(texts) if len(texts) > 1 else 0.0
        lines.append(f"| {side} | {len(texts)} | {pooled['words']} | {_pct(pooled['dup_sentence_share'])} | "
                     f"{_pct(pooled['near_dup_share'])} | {_pct(within)} within skills | "
                     f"{_pct(cross) if len(texts) > 1 else 'n/a'} | {copy_names} |")
        for k, t in texts.items():
            d = duplication(t)
            detail.append(f"| {side} | {k} | {d['words']} | {_pct(d['dup_sentence_share'])} | "
                          f"{_pct(d['near_dup_share'])} | {_pct(d['repeated_8gram'])} |")
    return "\n".join(lines + detail) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", help="also write the Markdown table here")
    args = p.parse_args()
    text = report()
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
