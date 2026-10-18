"""Rule inventory: which of a source's rules our skill files cover, and which of our rules trace to the source.

A *unit* is one statement a reader could act on: a Markdown section (heading plus its first 70 words), a list item, or a
table row. A *rule* is a unit picked from the files by the pair's spec (pattern headings, numbered rules, trait rows).
Coverage and tracing both compare a rule's text with every unit on the other side: cosine of sentence embeddings (TF-IDF
cosine in the fallback), or a heading that names the same thing (shared stems, pattern ids included). The cuts were set by
reading 70 rule/best-match pairs (see CUTS).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FENCE = re.compile(r"^```.*?^```", re.S | re.M)
HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
ITEM = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+(.*)")
BOLD_LEAD = re.compile(r"^\*\*(.+?)\*\*")
BODY_WORDS = 70
QUOTED = re.compile(r"`([^`]{3,40})`|[\"“]([^\"”]{4,50})[\"”]|\*\*([^*]{3,40})\*\*")


@dataclass
class Unit:
    heading: str
    text: str           # heading and first words of the body, markdown marks removed
    full: str           # everything the unit says, for quoted examples
    rel: str
    line: int
    kind: str           # section | item | row
    level: int = 0      # heading level for sections
    parent: str = ""    # nearest heading above
    bold: bool = False  # item that opens with a bold name

    @property
    def label(self) -> str:
        return f"{self.rel}:{self.line}"

    @property
    def shown(self) -> str:
        """The heading, with its parent heading in front when the heading alone is a generic label."""
        return f"{self.parent} › {self.heading}" if self.parent and len(self.heading.split()) <= 2 else self.heading


def plain(s: str) -> str:
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[`*_#>~|]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def first_words(s: str, n: int = BODY_WORDS) -> str:
    return " ".join(s.split()[:n])


def units_of(path: Path, rel: str) -> list[Unit]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = FENCE.sub(lambda m: "\n" * m.group().count("\n"), raw).split("\n")
    heads = [(i, m.group(1), m.group(2)) for i, ln in enumerate(lines) if (m := HEAD.match(ln))]
    out: list[Unit] = []
    for k, (i, hashes, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = " ".join(plain(x) for x in lines[i + 1:end] if x.strip() and not re.fullmatch(r"[\s|:\-]+", x))
        parent = next((t for j, h, t in reversed(heads[:k]) if len(h) < len(hashes)), "")
        ctx = f"{plain(parent)}. " if parent and len(hashes) >= 4 else ""
        out.append(Unit(plain(title), first_words(f"{ctx}{plain(title)}. {body}"), f"{plain(title)}. {body}", rel,
                        i + 1, "section", len(hashes), plain(parent)))
    parent = ""
    hp = {i: t for i, _, t in heads}
    i = 0
    while i < len(lines):
        ln = lines[i]
        if i in hp:
            parent = plain(hp[i])
        m = ITEM.match(ln)
        if m:
            parts = [m.group(1)]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not ITEM.match(lines[j]) and lines[j].startswith("  "):
                parts.append(lines[j].strip())
                j += 1
            body = " ".join(parts)
            if len(plain(body).split()) >= 6:
                lead = BOLD_LEAD.match(body)
                head = plain(lead.group(1)) if lead else " ".join(plain(re.split(r"[:.—]", body)[0]).split()[:12])
                ctx = f"{parent}. " if parent else ""
                out.append(Unit(head, first_words(f"{ctx}{plain(body)}"), plain(body), rel, i + 1, "item", 0, parent,
                                bool(lead)))
            i = j
            continue
        if ln.lstrip().startswith("|") and not re.fullmatch(r"[\s|:\-]+", ln):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not re.fullmatch(r"[\s|:\-]+", nxt) and len(plain(ln).split()) >= 6:   # skip header rows
                ctx = f"{parent}. " if parent else ""
                out.append(Unit(plain(cells[0]), first_words(f"{ctx}{plain(ln)}"), plain(ln), rel, i + 1, "row", 0, parent))
        i += 1
    return out


STOP = {"and", "the", "for", "with", "when", "from", "that", "this", "are", "not", "found", "reading", "avoid", "fix",
        "phrases", "phrase", "patterns", "pattern", "words", "word"}


def stems(heading: str) -> set[str]:
    """Stemmed words of a heading, pattern ids such as `hollow-intensifier` included."""
    out = set()
    for w in re.findall(r"[a-z]{3,}", heading.lower()):
        if w in STOP:
            continue
        out.add((re.sub(r"(ies|ing|ive|ed|es|s|ly|ion|al|y|e)$", "", w) if len(w) > 4 else w)[:6])
    return out


def names(heading: str) -> list[set[str]]:
    """The stem sets a heading answers to: the whole heading, and each clause or pattern id inside it."""
    parts = [heading] + [p for p in re.split(r"[(),/:]| and | or ", heading) if p.strip()]
    return [st for st in (stems(p) for p in parts) if 0 < len(st) <= 6]


def same_heading(rule: str, other: str) -> bool:
    """The headings name the same thing: some name of one shares two or more stems covering 60% of the shorter name, or
    the rule heading is one word and the other contains it."""
    one = len(stems(rule)) == 1 and len(rule.split()) == 1
    for sa in names(rule):
        for sb in names(other):
            shared = sa & sb
            small = min(len(sa), len(sb))
            if (len(shared) >= 2 and len(shared) / small >= 0.6) or (one and shared and len(next(iter(shared))) >= 4):
                return True
    return False


# ---------------------------------------------------------------- what counts as a rule

GENERIC_HEADINGS = {"formatting", "sentence structure", "words and phrases to replace", "what to remove or fix"}


def humanizer_rules(units: list[Unit]) -> list[Unit]:
    return [Unit(re.sub(r"^\d+\.\s*", "", u.heading), u.text, u.full, u.rel, u.line, u.kind, u.level, u.parent)
            for u in units if u.kind == "section" and u.level == 3 and re.match(r"^\d+\.", u.heading)]


def avoid_rules(units: list[Unit]) -> list[Unit]:
    cut = next((u.line for u in units if u.kind == "section" and u.heading == "Context profiles"), 10 ** 9)
    out = []
    for u in units:
        if u.line >= cut:
            continue
        if u.kind == "section" and u.level == 3 and u.heading.lower() not in GENERIC_HEADINGS:
            out.append(u)
        elif u.kind == "section" and u.level in (4, 5) and u.heading.startswith("Tier "):
            out.append(u)
        elif u.kind == "item" and u.bold and u.parent in ("Formatting", "Sentence structure"):
            out.append(u)
    return out


def catalog_headings(units: list[Unit]) -> list[Unit]:
    return [u for u in units if u.kind == "section" and u.level == 3]


def rules_items(units: list[Unit]) -> list[Unit]:
    return [u for u in units if u.kind == "item" and u.parent == "Rules"]


def trait_rows(units: list[Unit]) -> list[Unit]:
    """Rows of the Measured traits and Move traits tables (not the strength rubric, register or kind tables)."""
    return [u for u in units if u.kind == "row" and u.parent.startswith(("Measured traits", "Move traits"))]


# Cosine cuts (embedding backend, TF-IDF fallback). `strong` or a same-named heading marks a firm match, `ok` a likely
# one. Set on 70 hand-labelled rule/best-match pairs (39 of them truly covered): firm matches alone were right 27 of 29
# times and found 27 of the 39; firm or likely found 35 of the 39 and were right 35 of 41 times. The labels were made
# before the cuts were fixed and the same pairs were used to fix them, so the figures are in-sample. The TF-IDF cuts are
# not calibrated.
CUTS = {"embed": (0.55, 0.50), "tfidf": (0.35, 0.30)}


@dataclass
class Match:
    rule: Unit
    best: Unit | None
    cos: float
    named: bool = False     # a heading on the other side names the same thing
    grade: str = "no"       # strong | covered | no


def match_rules(backend, rules: list[Unit], pool: list[Unit], strong: float, ok: float) -> list[Match]:
    """Each rule's best unit in `pool` (a same-named heading wins over a higher cosine), graded by the cuts."""
    if not rules or not pool:
        return [Match(r, None, 0.0) for r in rules]
    best, arg = backend.match([r.text for r in rules], {"pool": [u.text for u in pool]})["pool"]
    out = []
    for r, b, a in zip(rules, best, arg):
        unit, cos = pool[int(a)], float(b)
        named = next((u for u in pool if same_heading(r.heading, u.heading)), None)
        if named is not None:
            unit = named if not same_heading(r.heading, unit.heading) else unit
        grade = "strong" if (named is not None or cos >= strong) else "covered" if cos >= ok else "no"
        out.append(Match(r, unit, cos, named is not None, grade))
    return out


# ---------------------------------------------------------------- the two pairs

THEIRS = {
    "avoid-ai-writing": ("conorbronsdon__avoid-ai-writing", ("skills/avoid-ai-writing/SKILL.md", "references/patterns.md")),
    "humanizer": ("blader__humanizer", ("SKILL.md",)),
}
PAIRS = [("anti-slop-editing", "avoid-ai-writing"), ("author-voice", "humanizer")]


def md_units(files: list[Path], base: Path) -> dict[str, list[Unit]]:
    return {str(f.relative_to(base)): units_of(f, str(f.relative_to(base))) for f in files}


def inventory(backend, root: Path, cache: Path, cuts: tuple[float, float]) -> list[dict]:
    """For each pair: how many of the source's pattern rules our paired skill (and any of our skills) covers, and how many
    of our rules trace to the source's files."""
    strong, ok = cuts
    skills = {d.name: d for d in sorted((root / "skills").iterdir()) if (d / "SKILL.md").is_file()}

    def skill_units(name: str) -> dict[str, list[Unit]]:
        files = [f for f in sorted(skills[name].rglob("*.md")) if f.name != "eval.md"]
        return md_units(files, root)

    all_ours = {sk: skill_units(sk) for sk in skills}
    flat_all = [u for sk in all_ours.values() for us in sk.values() for u in us]
    out = []
    for ours, theirs in PAIRS:
        repo, rels = THEIRS[theirs]
        their_units = md_units([cache / repo / r for r in rels], cache)
        flat_theirs = [u for us in their_units.values() for u in us]
        if theirs == "humanizer":
            their_rules = humanizer_rules(flat_theirs)
        else:
            their_rules = avoid_rules(their_units[f"{repo}/references/patterns.md"])
        own = all_ours[ours]
        flat_own = [u for us in own.values() for u in us]
        if ours == "anti-slop-editing":
            our_rules = (catalog_headings(own[f"skills/{ours}/references/pattern-catalog.md"])
                         + rules_items(own[f"skills/{ours}/SKILL.md"]))
        else:
            our_rules = (rules_items(own[f"skills/{ours}/SKILL.md"])
                         + trait_rows(own[f"skills/{ours}/references/trait-catalog.md"]))
        out.append({
            "ours": ours, "theirs": theirs,
            "their_rules": their_rules, "our_rules": our_rules,
            "covered": match_rules(backend, their_rules, flat_own, strong, ok),
            "covered_any": match_rules(backend, their_rules, flat_all, strong, ok),
            "traced": match_rules(backend, our_rules, flat_theirs, strong, ok),
        })
    return out


def share(ms: list[Match], firm_only: bool = False) -> float:
    ok = [m for m in ms if m.grade == "strong" or (m.grade == "covered" and not firm_only)]
    return len(ok) / len(ms) if ms else 0.0
