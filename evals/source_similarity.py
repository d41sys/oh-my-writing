#!/usr/bin/env python3
"""How close each of our skills is to each third-party source corpus, at three levels.

  uv run --with sentence-transformers --with numpy python3 evals/source_similarity.py --out evals/results/source-similarity.md
  python3 evals/source_similarity.py --out evals/results/source-similarity.md     # TF-IDF fallback, numpy only

The first command runs level 3 with the all-MiniLM-L6-v2 embedding model (downloaded on first use, about 90 MB, then
cached; sentence vectors are cached in evals/results/.similarity-embeddings.npz). The second needs only numpy and
falls back to TF-IDF cosine over sentences, and the report says so. `--semantic embed|tfidf|auto` forces a backend.
`--calibrate FILE` writes sentence pairs across the cosine range for a human to read when choosing the threshold
(`--calibrate-range LO HI --uniform N` draws N pairs uniformly from one band). `--docs FILE` also writes the short
summary committed as docs/SOURCE_SIMILARITY.md.

The report has three parts. Part 1 keeps the first version's scope: Markdown prose only. For a source, every SKILL.md
plus the Markdown under that skill's folder (references/, assets/, rules/, ...), or, for guide and prompt collections,
their content files. For us, SKILL.md, references/, assets/ (no eval.md, no agents/). README, LICENSE, CHANGELOG,
non-English files, tests, release notes, mirrors for other hosts, whole-file bundles (source_duplication.
whole_file_copies) and fenced code are left out. Part 2 widens both sides to every text file in the skill folder
(scripts, YAML, CSS, HTML, JSON, TeX, ...; see similarity_assets.py), split into prose (comments, docstrings, string
values, text nodes, Markdown outside fences) and code (other lines and fenced blocks). Prose is measured at the levels
below; code is measured as normalised lines (whitespace and comments removed, 20+ characters) found verbatim in a
source and as runs of 5+ consecutive lines. It also breaks down every skill by asset type. Part 3 is the rule
inventory for anti-slop-editing / avoid-ai-writing and author-voice / humanizer, in both directions
(similarity_rules.py).

Levels, all as shares of OUR words or sentences (a sentence has 6+ words):
  1 verbatim          share of our words covered by 8-word runs that also occur in the source
  2 close paraphrase  share of our sentences, not already verbatim, whose best source sentence has word-trigram
                      Jaccard >= 0.5. A sentence is verbatim for a source when half its words sit in shared 8-word
                      runs or the sentence occurs there word for word.
  3 same idea         share of our sentences whose best source sentence has cosine >= THRESHOLD (includes 1 and 2)
Control: the same three measures against jezweb dev-tools skills, which have nothing to do with writing; it is the
noise floor of level 3.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import math
import random
import re
import statistics
import sys
import types
from array import array
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import similarity_assets as sa  # noqa: E402
import similarity_rules as sr  # noqa: E402
import source_duplication as sd  # noqa: E402

ROOT = HERE.parent
CACHE = ROOT / ".cache" / "omw_sources"
RESULTS = HERE / "results"
GRAM = sd.GRAM
MIN_WORDS = sd.MIN_WORDS
JACCARD = 0.5
VERBATIM_SENTENCE = 0.5     # share of a sentence's words inside shared 8-word runs that makes it verbatim
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Cosine cut chosen by reading sample pairs (see CALIBRATION in the report). TF-IDF cosines sit on a different scale.
THRESHOLD = {"embed": 0.75, "tfidf": 0.60}
SENSITIVITY = {"embed": (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85), "tfidf": (0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70)}
CALIBRATION = {
    "embed": (
        "Calibration read 96 pairs in two samples (`--calibrate`: 56 pairs spread over cosine 0.40 to 0.90, then 40 pairs "
        "over 0.62 to 0.86; each pair is one of our sentences and its best sentence in any real source, with verbatim and "
        "close paraphrases removed). Reading them: below about 0.60 the pairs share a topic word at most; from 0.60 to "
        "0.75 about 1 pair in 9 (4 of 38) states the same rule, the rest share a topic or a shape (\"Process: ...\", "
        "\"Reader: ...\", \"cap at N rounds\" with different values) without the same instruction; from 0.75 up, "
        "30 of 36 pairs state the same rule (for example \"Skip easy-to-reverse choices\" / \"If a decision is easy to "
        "reverse, skip it\"; \"Distinguish missing, not measured, not applicable, and zero\"). The misses above the cut "
        "are mostly clipped source fragments and bare labels. So 0.75 is the lowest cut where a pair is more likely than "
        "not to be the same rule; it still has about 1 false pair in 6, and a lower cut would admit mostly topic overlap."),
    "tfidf": (
        "TF-IDF fallback: 40 pairs read, spread over cosine 0.30 to 0.80 (same sampling as above, one sample). Below 0.60 "
        "1 pair in 24 states the same rule; from 0.60 up, 13 of 16 do (for example \"Imperative mood (add feature not "
        "added feature)\"; \"Convert local paths to repo-relative paths\"). TF-IDF only sees shared words, so it misses "
        "rewordings that the embedding model catches: its shares are lower bounds on the same-idea share, and the two "
        "backends' numbers are not comparable."),
}

METHOD = (
    "Corpora: for each of 17 sources, every SKILL.md and the text files in that skill's folder (references, assets, rules, "
    "scripts, agents), or, for guide and prompt collections, their content files; README, LICENSE, CHANGELOG, "
    "translations, tests, whole-file bundles and hidden files are left out, and so are non-English files. Our side is "
    "every text file in `skills/<name>/` except `eval.md`. Each file is split into prose (Markdown outside fences, "
    "comments and docstrings, YAML and JSON string values, HTML and TeX text) and code. Prose levels: *verbatim* is the "
    "share of our words covered by {gram}-word runs that also occur in the source; *close paraphrase* is the share of our "
    "sentences of 6+ words, not already verbatim, whose best source sentence has word-trigram Jaccard of 0.5 or more; "
    "*same idea* is the share of our sentences whose best source sentence has cosine of {model} at or above {threshold}, "
    "a cut set by reading 96 sample pairs (30 of 36 pairs at or above the cut stated the same rule); a separate uniform "
    "random sample of 60 pairs from the band just below the cut (0.60 to 0.75) gave 15 pairs that stated the same rule, "
    "which is the recall adjustment. Code: lines with comments and all whitespace removed, "
    "dropped under {code_min} characters, matched exactly, plus runs of {code_run}+ consecutive kept lines. The control is "
    "the same measurement against unrelated jezweb skills (dev-tools, cloudflare, shopify, wordpress, frontend, "
    "integrations, design-assets); it sets the noise floor, since advice such as *cut filler* recurs in any writing "
    "guide and semantic overlap on writing advice is partly unavoidable. Verbatim and code-line figures are the "
    "copying measures; same-idea figures are not evidence of copying."
)

PIECE_SPLIT = re.compile(r"(?<=[.!?])\s+|\s*\|\s*")
LANG = r"(?:zh|ja|ko|es|fr|de|pt|ru|tr|vi|it|ar|hi|pl|th|uk|ur|id|nl|cs|sv|he|fa|bn|el|hu|ro)"
LANG_DIR = re.compile(rf"^{LANG}(?:[-_][A-Za-z]{{2,4}})?$", re.I)
LANG_FILE = re.compile(rf"(?:\.|[-_]){LANG}(?:[-_][A-Za-z]{{2,4}})?\.(?:md|txt|rst)$", re.I)
EXCLUDE_DIRS = (sd.SKIP_DIRS | {"scripts", "agents", "dist", "plugins", "archive", "pi", "submission", "cursor-rules",
                                "corpus", "detector", "bin", "release", "releases", "release-notes", "demo", "website",
                                "node_modules", "build", "vendor", "fixtures", "assets-src", "ecc2"})
ROOT_SKILL_SUBDIRS = {"references", "reference", "assets", "rules", "modes", "core", "templates"}
ASSET_ROOT_SUBDIRS = ROOT_SKILL_SUBDIRS | {"scripts", "agents"}
ASSET_EXCLUDE_DIRS = EXCLUDE_DIRS - {"scripts", "agents"}
OUR_SUBDIRS = {"references", "assets"}
CODE_RUN = 5                # consecutive code lines that make a shared code run


# ---------------------------------------------------------------- corpus model

@dataclass
class Sent:
    tokens: tuple
    text: str
    start: int      # word offset in its doc
    line: int


@dataclass
class Doc:
    path: Path
    rel: str
    words: list
    lines: array
    sents: list
    skill: str = ""
    kind: str = "md"        # file type: md, py, yaml, ...
    legacy: bool = True     # a Markdown file of the first report's selection


@dataclass
class CodeDoc:
    """Normalised code lines of one file: `words` holds one hash per kept line, `lines` its line number in the file."""
    path: Path
    rel: str
    words: list
    lines: array
    skill: str = ""
    kind: str = "py"
    norm: list = field(default_factory=list)    # the normalised text of each kept line (our side only)


@dataclass
class Corpus:
    name: str
    docs: list = field(default_factory=list)
    code: list = field(default_factory=list)
    skipped: list = field(default_factory=list)    # (relative path, reason)
    note: str = ""

    def legacy_view(self) -> "Corpus":
        """The Markdown selection of the first report: no code, no non-Markdown prose."""
        return Corpus(self.name, [d for d in self.docs if d.legacy], [], self.skipped, self.note)

    @property
    def code_lines(self) -> int:
        return sum(len(d.words) for d in self.code)

    @property
    def words(self) -> int:
        return sum(len(d.words) for d in self.docs)

    @property
    def sentences(self) -> int:
        return sum(len(d.sents) for d in self.docs)

    def unique_sents(self) -> list[Sent]:
        seen, out = set(), []
        for d in self.docs:
            for s in d.sents:
                if s.tokens not in seen:
                    seen.add(s.tokens)
                    out.append(s)
        return out


def clean_text(s: str) -> str:
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[`*_#>~]+", "", s)
    s = re.sub(r"^\s*(?:[-+]|\d+[.)])\s+", "", s)
    return re.sub(r"\s+", " ", s).strip()[:400]


def rst_to_text(text: str) -> str:
    out = []
    for ln in text.split("\n"):
        if ln.startswith(".. ") or re.fullmatch(r"\s*([=\-~^\"'#*+`])\1{3,}\s*", ln):
            out.append("")
        else:
            out.append(re.sub(r":\w+:`([^`<]*?)(?:\s*<[^>]*>)?`", r"\1", ln))
    return "\n".join(out)


def not_english(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and sum(ord(c) > 0x24F for c in letters) / len(letters) > 0.2


def build_doc(path: Path, rel: str, skill: str = "", legacy: bool = True) -> Doc | None:
    """A Markdown, text or reStructuredText file as prose (fenced code blanked); None for non-English text."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not_english(text):
        return None   # not English (a translation, or a Chinese-language skill)
    if path.suffix == ".rst":
        text = rst_to_text(text)
    text = sd.FENCE.sub(lambda m: "\n" * m.group().count("\n"), text)
    return doc_from_text(text, path, rel, skill, sa.kind_of(path), legacy)


def doc_from_text(text: str, path: Path, rel: str, skill: str, kind: str, legacy: bool) -> Doc:
    words: list = []
    lines = array("I")
    sents: list[Sent] = []
    for ln, line in enumerate(text.split("\n"), 1):
        for piece in PIECE_SPLIT.split(line):
            toks = [sys.intern(w) for w in sd.WORD.findall(piece.lower())]
            if not toks:
                continue
            if len(toks) >= MIN_WORDS:
                sents.append(Sent(tuple(toks), clean_text(piece), len(words), ln))
            words.extend(toks)
            lines.extend([ln] * len(toks))
    return Doc(path, rel, words, lines, sents, skill, kind, legacy)


def code_doc(pairs: list, path: Path, rel: str, skill: str, kind: str, keep_text: bool) -> CodeDoc | None:
    if not pairs:
        return None
    return CodeDoc(path, rel, [hash(n) for _, n in pairs], array("I", [ln for ln, _ in pairs]), skill, kind,
                   [n for _, n in pairs] if keep_text else [])


def load_file(path: Path, rel: str, skill: str, legacy: bool, keep_text: bool = False):
    """(prose Doc or None, CodeDoc or None, skip reason or None) for any file of a skill folder."""
    kind = sa.kind_of(path)
    if path.suffix.lower() in (".md", ".txt", ".rst"):
        doc = build_doc(path, rel, skill, legacy)
        if doc is None:
            return None, None, "non-English"
        pairs = sa.md_fences(path.read_text(encoding="utf-8", errors="replace")) if path.suffix.lower() == ".md" else []
        return (doc if doc.words else None), code_doc(pairs, path, rel, skill, "md-fence", keep_text), None
    ex = sa.extract(path)
    if ex is None:
        return None, None, "binary, hidden, lock file or over 1.5 MB"
    if ex.prose and not_english(ex.prose):
        return None, None, "non-English"
    doc = doc_from_text(ex.prose, path, rel, skill, kind, False)
    return (doc if doc.words else None), code_doc(ex.code, path, rel, skill, ex.code_kind or kind, keep_text), None


def excluded_part(parts) -> bool:
    return any(p.startswith(".") or p in EXCLUDE_DIRS or p.startswith("skills-codex") or LANG_DIR.match(p)
               for p in parts)


def usable_name(p: Path) -> bool:
    n = p.name.lower()
    return (n not in sd.SKIP_NAMES and not n.startswith("readme") and not LANG_FILE.search(n)
            and not n.endswith(("-bundled.md", ".full.md")))


def skill_folder_files(folder: Path, repo: Path) -> list[tuple[Path, bool]]:
    """(file, legacy) for SKILL.md and every text asset under a skill folder; `legacy` marks the Markdown files the
    first report used. A skill at the repo root takes only its known content folders; nested skills' files belong to
    those skills. README, LICENSE, translations, tests, dist and similar are left out."""
    at_root = folder == repo
    out = [(folder / "SKILL.md", True)]
    for p in sorted(folder.rglob("*")):
        if p.name == "SKILL.md" or not p.is_file() or not usable_name(p) or p.name.startswith("."):
            continue
        inner = p.relative_to(folder).parts[:-1]
        if any((folder.joinpath(*inner[:i + 1]) / "SKILL.md").is_file() for i in range(len(inner))):
            continue
        top = inner[0] if inner else None
        legacy = (p.suffix.lower() == ".md" and not excluded_part(inner)
                  and not (at_root and top not in ROOT_SKILL_SUBDIRS))
        asset = (not any(part.startswith(".") or part in ASSET_EXCLUDE_DIRS or part.startswith("skills-codex")
                         or LANG_DIR.match(part) for part in inner)
                 and not (at_root and top not in ASSET_ROOT_SUBDIRS))
        if legacy or asset:
            out.append((p, legacy))
    return out


@dataclass
class Source:
    name: str
    repo: str
    skill_roots: tuple | None = ()          # folders to search for SKILL.md; None = the whole repo; () = none
    content_dirs: tuple = ()                # folders whose .md files are content (no SKILL.md structure)
    content_files: tuple = ()               # explicit files (relative to the repo)
    content_globs: tuple = ()
    note: str = ""


SOURCES = [
    Source("avoid-ai-writing", "conorbronsdon__avoid-ai-writing", skill_roots=None),
    Source("humanizer", "blader__humanizer", skill_roots=None),
    Source("great-writer", "d-wwei__great-writer", skill_roots=None),
    Source("marketingskills", "coreyhaines31__marketingskills", skill_roots=("skills",)),
    Source("ECC", "affaan-m__everything-claude-code", skill_roots=("skills",),
           content_dirs=("agents", "commands", "rules", "contexts"),
           content_files=("the-longform-guide.md", "the-shortform-guide.md", "the-security-guide.md"),
           note="skills/, agents/, commands/, rules/, contexts/ and three root guides; mirrors for other hosts, "
                "docs/ and pi/ left out"),
    Source("K-Dense", "K-Dense-AI__scientific-agent-skills", skill_roots=None),
    Source("Orchestra", "Orchestra-Research__AI-Research-SKILLs", skill_roots=None),
    Source("anthropic-skills", "anthropics__skills", skill_roots=("skills",)),
    Source("diataxis", "evildmp__diataxis-documentation-framework", content_globs=("source/*.rst",),
           note="the framework's reStructuredText pages (no news, colophon or translation page)"),
    Source("storm", "stanford-oval__storm",
           note="no loadable guidance text: the repository is Python code and its README; nothing to compare"),
    Source("ARIS", "wanshuiyin__Auto-claude-code-research-in-sleep", skill_roots=None),
    Source("garden", "ConardLi__garden-skills", skill_roots=("skills",)),
    Source("ResumeSkills", "Paramchoudhary__ResumeSkills", skill_roots=None),
    Source("proficiently", "proficientlyjobs__proficiently-claude-skills", skill_roots=None),
    Source("jezweb-writing", "jezweb__claude-skills", skill_roots=("plugins/writing",)),
    Source("mattpocock", "mattpocock__skills", skill_roots=("skills",)),
    Source("career-guides", "guides", content_globs=("*.txt",),
           note="university and agency web guides saved as text (cuny-sop fetch was blocked, 138 bytes)"),
    Source("Leey21", "Leey21__awesome-ai-research-writing", content_files=("README.md",),
           note="a prompt collection whose content is its README"),
]
CONTROL_ROOTS = tuple(f"plugins/{p}" for p in
                      ("dev-tools", "cloudflare", "shopify", "wordpress", "frontend", "integrations", "design-assets"))
CONTROL_REPO = "jezweb__claude-skills"


def collect_files(src: Source, repo: Path) -> list[tuple[str, list[tuple[Path, bool]]]]:
    """(group key, [(file, legacy)]) pairs. Skill folders form their own group so bundles are detected among siblings."""
    groups: list[tuple[str, list[tuple[Path, bool]]]] = []
    seen: set[Path] = set()
    roots = [repo] if src.skill_roots is None else [repo / r for r in src.skill_roots]
    for base in roots:
        if not base.is_dir():
            continue
        for skill_md in sorted(base.rglob("SKILL.md")):
            if excluded_part(skill_md.relative_to(base).parts[:-1]):
                continue
            files = [(f, leg) for f, leg in skill_folder_files(skill_md.parent, repo) if f not in seen]
            seen.update(f for f, _ in files)
            groups.append((str(skill_md.parent.relative_to(repo)), files))
    extra: list[Path] = []
    for d in src.content_dirs:
        for p in sorted((repo / d).rglob("*")):
            rel = p.relative_to(repo).parts[:-1]
            if (p.is_file() and p.suffix.lower() in {".md", ".txt"} and usable_name(p) and not excluded_part(rel[1:])
                    and p not in seen):
                extra.append(p)
    for g in src.content_globs:
        extra += [p for p in sorted(repo.glob(g)) if p.is_file() and usable_name(p) and p.stem not in
                  {"news", "colophon", "translation", "LICENSE"}]
    extra += [repo / f for f in src.content_files if (repo / f).is_file()]
    if extra:
        groups.append(("", [(p, True) for p in extra]))
    return groups


def load_corpus(src: Source, repo: Path | None = None) -> Corpus:
    """Every prose and code file of the source's skills (see skill_folder_files). Whole-file bundles among a skill's
    Markdown files are dropped, as in source_duplication."""
    repo = repo or CACHE / src.repo
    c = Corpus(src.name, note=src.note)
    if not repo.is_dir():
        c.note = c.note or "repository not in cache"
        return c
    for key, files in collect_files(src, repo):
        legacy_files = [f for f, leg in files if leg]
        dropped = sd.whole_file_copies(legacy_files) if key and len(legacy_files) > 1 else []
        for f, legacy in files:
            rel = str(f.relative_to(CACHE)) if f.is_relative_to(CACHE) else str(f)
            if f in dropped:
                c.skipped.append((rel, "whole-file copy of sibling files"))
                continue
            doc, code, why = load_file(f, rel, "", legacy)
            if why:
                c.skipped.append((rel, why))
            if doc:
                c.docs.append(doc)
            if code:
                c.code.append(code)
    return c


_OURS: dict = {}


def load_ours_all() -> tuple[dict[str, list[Doc]], dict[str, list[CodeDoc]]]:
    """Per skill: prose docs and code docs of every text file in skills/<name>/ except eval.md."""
    if _OURS:
        return _OURS["prose"], _OURS["code"]
    prose, code = {}, {}
    for sk in sorted((ROOT / "skills").iterdir()):
        if not (sk / "SKILL.md").is_file():
            continue
        prose[sk.name], code[sk.name] = [], []
        for f in [sk / "SKILL.md"] + [p for p in sorted(sk.rglob("*")) if p.is_file() and p.name != "SKILL.md"
                                      and "__pycache__" not in p.parts]:
            if f.name == "eval.md" or f.name.startswith("."):
                continue
            rel = f.relative_to(sk).parts
            legacy = f.suffix.lower() == ".md" and (f.name == "SKILL.md" or rel[0] in OUR_SUBDIRS)
            doc, cd, _ = load_file(f, str(f.relative_to(ROOT)), sk.name, legacy, keep_text=True)
            if doc:
                prose[sk.name].append(doc)
            if cd:
                code[sk.name].append(cd)
    _OURS.update(prose=prose, code=code)
    return prose, code


def load_ours() -> dict[str, list[Doc]]:
    """Our Markdown prose, the selection of the first report."""
    return {sk: [d for d in docs if d.legacy] for sk, docs in load_ours_all()[0].items()}


def truncate(d: Doc, n: int) -> Doc:
    return Doc(d.path, d.rel, d.words[:n], d.lines[:n], [s for s in d.sents if s.start + len(s.tokens) <= n], d.skill,
               d.kind, d.legacy)


def sample_corpus(pool: Corpus, target: int, seed: int, name: str) -> Corpus:
    """A random subset of the pool's documents with `target` words (the last document is cut to fit)."""
    docs = list(pool.docs)
    random.Random(seed).shuffle(docs)
    out = Corpus(name, note=f"random {target} words of the control pool")
    for d in docs:
        left = target - out.words
        if left <= 0:
            break
        out.docs.append(d if len(d.words) <= left else truncate(d, left))
    return out


# ---------------------------------------------------------------- level 1: verbatim

def gram_hashes(words: list, n: int = GRAM) -> list[int]:
    return [hash(tuple(words[i:i + n])) for i in range(len(words) - n + 1)]


def covered_positions(words: list, source_words: list[list], n: int = GRAM) -> list[bool]:
    """Which of `words` sit inside an n-word run that occurs in any of the source word lists."""
    have = {h for sw in source_words for h in gram_hashes(sw, n)}
    mask = [False] * len(words)
    for i, h in enumerate(gram_hashes(words, n)):
        if h in have:
            mask[i:i + n] = [True] * n
    return mask


def verbatim_share(our_words: list[list], source_words: list[list], n: int = GRAM) -> float:
    """Share of our words covered by n-word runs that also occur in the source."""
    total = sum(len(w) for w in our_words)
    covered = sum(sum(covered_positions(w, source_words, n)) for w in our_words)
    return covered / total if total else 0.0


@dataclass
class Run:
    length: int
    source: str
    our_doc: int
    our_start: int
    src_rel: str
    src_start: int
    src_line: tuple
    words: tuple = ()


def verbatim_pass(corpus: Corpus, our_docs: list, our_index: dict, keep_runs: int = 40, n: int = GRAM, docs=None):
    """One pass over the source (`docs`, default its prose): per our doc, a coverage mask of positions inside an n-token
    run found in the source; plus the longest shared runs of at least n tokens. Tokens are words for prose and
    normalised code lines for code."""
    docs = corpus.docs if docs is None else docs
    cov = [bytearray(len(d.words)) for d in our_docs]
    runs: list[tuple] = []
    block = b"\x01" * n

    def close(o, key, a, sdoc):
        runs.append((a[1] - a[0] + n, o, key[1] + a[0], sdoc, a[0], a[1]))

    for si, sdoc in enumerate(docs):
        active: dict = {}
        for j, h in enumerate(gram_hashes(sdoc.words, n)):
            hits = our_index.get(h)
            if not hits:
                continue
            for o, p in hits:
                cov[o][p:p + n] = block
                key = (o, p - j)
                a = active.get(key)
                if a is not None and a[1] == j - 1:
                    a[1] = j
                else:
                    if a is not None:
                        close(o, key, a, si)
                    active[key] = [j, j]
        for key, a in active.items():
            close(key[0], key, a, si)
    top = heapq.nlargest(keep_runs, runs, key=lambda r: r[0])
    out = []
    for length, o, p, si, j0, j1 in top:
        sdoc = docs[si]
        out.append(Run(length, corpus.name, o, p, sdoc.rel, j0,
                       (sdoc.lines[j0], sdoc.lines[j1 + n - 1]), tuple(sdoc.words[j0:j1 + n])))
    return cov, out


# ---------------------------------------------------------------- level 2: close paraphrase

def trigrams(tokens: tuple) -> frozenset:
    return frozenset(hash(tokens[i:i + 3]) for i in range(len(tokens) - 2))


def close_matches(our: list[tuple], source: list[tuple], threshold: float = JACCARD) -> list[tuple[float, int]]:
    """For each of our token tuples, (Jaccard, index) of the best source sentence by word-trigram Jaccard when that is
    >= threshold, else (0.0, -1). Candidates come from the rarest k trigrams (prefix filter), exact for >= threshold."""
    sets = [trigrams(t) for t in source]
    postings: dict[int, list[int]] = defaultdict(list)
    for i, s in enumerate(sets):
        for g in s:
            postings[g].append(i)
    out = []
    for toks in our:
        g = trigrams(toks)
        need = max(1, math.ceil(threshold * len(g) - 1e-9))   # a pair shares at least threshold * |g| trigrams
        probe = sorted(g, key=lambda x: len(postings.get(x, ())))[:len(g) - need + 1]
        cand = {i for x in probe for i in postings.get(x, ())}
        best, arg = 0.0, -1
        for i in cand:
            inter = len(g & sets[i])
            jac = inter / (len(g) + len(sets[i]) - inter)
            if jac > best:
                best, arg = jac, i
        out.append((best, arg) if best >= threshold else (0.0, -1))
    return out


# ---------------------------------------------------------------- level 3: semantic backends

class EmbedBackend:
    kind = "embed"

    def __init__(self, model_name: str, cache_path: Path):
        import numpy as np
        from sentence_transformers import SentenceTransformer
        self.np = np
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.label = f"{model_name} embeddings (cosine)"
        self.cache_path = cache_path
        self.keys: dict[str, int] = {}
        self.vecs = np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        if cache_path.is_file():
            z = np.load(cache_path, allow_pickle=False)
            if str(z["model"]) == model_name:
                self.vecs = z["vecs"]
                self.keys = {k: i for i, k in enumerate(z["keys"].tolist())}

    @staticmethod
    def _key(t: str) -> str:
        return hashlib.sha1(t.encode("utf-8")).hexdigest()

    def _save(self):
        self.np.savez(self.cache_path, model=self.model_name, keys=self.np.array(list(self.keys)), vecs=self.vecs)

    def vectors(self, texts: list[str]):
        np = self.np
        missing = list({self._key(t): t for t in texts if self._key(t) not in self.keys}.items())
        for lo in range(0, len(missing), 20000):
            chunk = missing[lo:lo + 20000]
            v = self.model.encode([t for _, t in chunk], batch_size=128, normalize_embeddings=True,
                                  show_progress_bar=True, convert_to_numpy=True).astype(np.float32)
            base = len(self.keys)
            for i, (k, _) in enumerate(chunk):
                self.keys[k] = base + i
            self.vecs = np.concatenate([self.vecs, v]) if len(self.vecs) else v
            self._save()
        return self.vecs[[self.keys[self._key(t)] for t in texts]]

    def match(self, our: list[str], sources: dict[str, list[str]]) -> dict[str, tuple]:
        np = self.np
        O = self.vectors(our)
        out = {}
        for name, texts in sources.items():
            n = len(our)
            best = np.zeros(n, dtype=np.float32)
            arg = np.full(n, -1, dtype=np.int64)
            if texts:
                S = self.vectors(texts)
                for lo in range(0, n, 256):
                    sims = O[lo:lo + 256] @ S.T
                    arg[lo:lo + 256] = sims.argmax(axis=1)
                    best[lo:lo + 256] = sims[np.arange(len(sims)), arg[lo:lo + 256]]
            out[name] = (best, arg)
        return out


class TfidfBackend:
    """Sparse TF-IDF cosine over sentences (stop-word-like terms, df above 3% of all sentences, are dropped)."""
    kind = "tfidf"
    label = "TF-IDF cosine over sentences (sentence-transformers unavailable)"

    def __init__(self):
        import numpy as np
        self.np = np

    @staticmethod
    def _terms(t: str) -> list[str]:
        return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in sd.WORD.findall(t.lower())]

    def match(self, our: list[str], sources: dict[str, list[str]]) -> dict[str, tuple]:
        np = self.np
        everything = set(our)
        for t in sources.values():
            everything.update(t)
        df = Counter()
        for t in everything:
            df.update(set(self._terms(t)))
        n_docs = len(everything)
        idf = {w: math.log((1 + n_docs) / (1 + c)) + 1 for w, c in df.items() if c <= 0.03 * n_docs}

        def vec(t: str) -> dict[str, float]:
            tf = Counter(w for w in self._terms(t) if w in idf)
            v = {w: (1 + math.log(c)) * idf[w] for w, c in tf.items()}
            norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
            return {w: x / norm for w, x in v.items()}

        ours = [vec(t) for t in our]
        out = {}
        for name, texts in sources.items():
            post: dict[str, list] = defaultdict(list)
            for i, t in enumerate(texts):
                for w, x in vec(t).items():
                    post[w].append((i, x))
            best = np.zeros(len(our), dtype=np.float32)
            arg = np.full(len(our), -1, dtype=np.int64)
            for k, v in enumerate(ours):
                acc: dict[int, float] = defaultdict(float)
                for w, x in v.items():
                    for i, y in post.get(w, ()):
                        acc[i] += x * y
                if acc:
                    i = max(acc, key=acc.get)
                    best[k], arg[k] = acc[i], i
            out[name] = (best, arg)
        return out


def make_backend(kind: str, cache_path: Path):
    if kind in ("auto", "embed"):
        try:
            return EmbedBackend(MODEL, cache_path)
        except Exception as exc:  # noqa: BLE001 - model cannot load or download
            if kind == "embed":
                raise
            print(f"embedding backend unavailable ({type(exc).__name__}: {exc}); using TF-IDF", file=sys.stderr)
    return TfidfBackend()


# ---------------------------------------------------------------- the analysis

@dataclass
class Result:
    name: str
    verbatim: dict           # skill -> word share
    verb_flag: object        # bool array over our sentences: verbatim for this corpus
    jac: list                # per our sentence (jaccard, source sentence index)
    cos: object
    cos_arg: object
    sents: list              # the corpus's unique sentences (Sent)
    sent_doc: list           # doc of each unique sentence
    runs: list
    cov: list = field(default_factory=list)   # per our doc, bytearray: word covered by a shared 8-word run


def analyse(ours: dict[str, list[Doc]], corpora: list[Corpus], backend, threshold: float) -> tuple[dict, list]:
    np = backend.np
    our_docs = [d for docs in ours.values() for d in docs]
    our_sents = [(s, di) for di, d in enumerate(our_docs) for s in d.sents]
    our_index: dict[int, list] = defaultdict(list)
    for di, d in enumerate(our_docs):
        for p, h in enumerate(gram_hashes(d.words)):
            our_index[h].append((di, p))

    pool: dict[str, list[str]] = {}
    uniq: dict[str, list] = {}
    for c in corpora:
        us, docs_of = [], []
        seen = set()
        for d in c.docs:
            for s in d.sents:
                if s.tokens not in seen:
                    seen.add(s.tokens)
                    us.append(s)
                    docs_of.append(d)
        uniq[c.name] = (us, docs_of)
        pool[c.name] = [s.text for s in us]
    sem = backend.match([s.text for s, _ in our_sents], pool)

    results = {}
    for c in corpora:
        cov, runs = verbatim_pass(c, our_docs, our_index)
        by_skill_cov = Counter()
        for d, m in zip(our_docs, cov):
            by_skill_cov[d.skill] += sum(m)
        verb = {sk: by_skill_cov[sk] / max(1, sum(len(d.words) for d in docs)) for sk, docs in ours.items()}
        us, docs_of = uniq[c.name]
        known = {s.tokens for s in us}
        flag = np.zeros(len(our_sents), dtype=bool)
        for k, (s, di) in enumerate(our_sents):
            n = len(s.tokens)
            if sum(cov[di][s.start:s.start + n]) / n >= VERBATIM_SENTENCE or s.tokens in known:
                flag[k] = True
        jac = close_matches([s.tokens for s, _ in our_sents], [s.tokens for s in us]) if us else [(0.0, -1)] * len(our_sents)
        best, arg = sem[c.name]
        results[c.name] = Result(c.name, verb, flag, jac, best, arg, us, docs_of, runs, cov)
    return results, [(s, our_docs[di]) for s, di in our_sents]


def shares(res: Result, our_sents: list, skill: str, threshold: float) -> tuple[float, float, float]:
    idx = [k for k, (_, d) in enumerate(our_sents) if d.skill == skill]
    n = len(idx)
    c = sum(1 for k in idx if not res.verb_flag[k] and res.jac[k][0] >= JACCARD)
    s = sum(1 for k in idx if res.cos[k] >= threshold)
    return res.verbatim[skill], c / n, s / n


# ---------------------------------------------------------------- studies over all assets

# Share of our sentences with cosine in [BAND_LO, threshold) that state the same rule, from a uniform random sample read
# by hand (see the report's calibration section): (same rule, pairs read).
BAND = {"embed": (0.60, 15, 60), "tfidf": None}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a rate read from k hits in n sampled pairs."""
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


class Study:
    """One analyse() run with the per-skill figures the report reads from it."""

    def __init__(self, ours, corpora, names, backend, threshold):
        self.ours, self.names, self.threshold, self.np = ours, names, threshold, backend.np
        self.skills = list(ours)
        self.results, self.our_sents = analyse(ours, corpora, backend, threshold)
        self.docs = [d for ds in ours.values() for d in ds]
        self.S = {c.name: {sk: shares(self.results[c.name], self.our_sents, sk, threshold) for sk in self.skills}
                  for c in corpora}
        self.idx = {sk: [k for k, (_, d) in enumerate(self.our_sents) if d.skill == sk] for sk in self.skills}
        self.words = {sk: sum(len(d.words) for d in ds) for sk, ds in ours.items()}

    def best(self, sk: str, level: int) -> tuple[float, str]:
        n = max(self.names, key=lambda n: self.S[n][sk][level])
        return self.S[n][sk][level], n

    def band_share(self, name: str, sk: str, lo: float) -> float:
        cos = self.results[name].cos
        return sum(1 for k in self.idx[sk] if lo <= cos[k] < self.threshold) / len(self.idx[sk])

    def adjusted(self, sk: str, band) -> tuple[float, str]:
        """Highest same-idea share over sources once the sampled band [lo, threshold) is added at its hit rate."""
        lo, hit, n = band
        n_ = max(self.names, key=lambda m: self.S[m][sk][2] + self.band_share(m, sk, lo) * hit / n)
        return self.S[n_][sk][2] + self.band_share(n_, sk, lo) * hit / n, n_

    def any_same_idea(self, sk: str, lo: float) -> tuple[float, float]:
        """Over the real sources together: (share of our sentences whose best sentence anywhere is at or above the cut,
        share whose best is in [lo, cut)). This is how the band sample was drawn, so the band rate applies to it."""
        np = self.np
        cos = np.max(np.stack([np.asarray(self.results[n].cos) for n in self.names]), axis=0)[self.idx[sk]]
        return float(np.mean(cos >= self.threshold)), float(np.mean((cos >= lo) & (cos < self.threshold)))

    def any_verbatim(self, sk: str) -> float:
        covered = total = 0
        for i, d in enumerate(self.docs):
            if d.skill != sk:
                continue
            total += len(d.words)
            covered += sum(1 for j in range(len(d.words)) if any(self.results[n].cov[i][j] for n in self.names))
        return covered / total

    def by_kind(self, sk: str) -> dict[str, tuple[int, str, float]]:
        """kind -> (words, source with the highest verbatim share, that share) for the skill's prose of that kind."""
        out = {}
        for kind in sorted({d.kind for d in self.docs if d.skill == sk}):
            ids = [i for i, d in enumerate(self.docs) if d.skill == sk and d.kind == kind]
            words = sum(len(self.docs[i].words) for i in ids)
            share_by = {n: sum(sum(self.results[n].cov[i]) for i in ids) / words for n in self.names}
            top = max(share_by, key=share_by.get)
            out[kind] = (words, top, share_by[top])
        return out


class CodeStudy:
    """Normalised code lines of ours against each source's code lines: single lines found, and runs of CODE_RUN lines."""

    def __init__(self, ours_code: dict[str, list[CodeDoc]], real: list[Corpus], control: Corpus):
        self.docs = [d for ds in ours_code.values() for d in ds]
        self.names = [c.name for c in real]
        index: dict[int, list] = defaultdict(list)
        for di, d in enumerate(self.docs):
            for p, h in enumerate(gram_hashes(d.words, CODE_RUN)):
                index[h].append((di, p))
        self.keys = sorted({(d.skill, d.kind) for d in self.docs})
        self.total = Counter()
        for d in self.docs:
            self.total[(d.skill, d.kind)] += len(d.words)
        sets = {c.name: {h for cd in c.code for h in cd.words} for c in real + [control]}
        self.hit: dict[str, Counter] = {}
        self.run: dict[str, Counter] = {}
        self.runs: list[Run] = []
        for c in real + [control]:
            self.hit[c.name] = Counter()
            for d in self.docs:
                self.hit[c.name][(d.skill, d.kind)] += sum(1 for h in d.words if h in sets[c.name])
            cov, runs = verbatim_pass(c, self.docs, index, keep_runs=25, n=CODE_RUN, docs=c.code)
            self.run[c.name] = Counter()
            for d, m in zip(self.docs, cov):
                self.run[c.name][(d.skill, d.kind)] += sum(m)
            if c is not control:
                self.runs += runs
        self.any_hit = Counter()
        self.boiler = Counter()
        for d in self.docs:
            for h in d.words:
                if any(h in sets[n] for n in self.names):
                    self.any_hit[(d.skill, d.kind)] += 1
                    if h in sets[control.name]:
                        self.boiler[(d.skill, d.kind)] += 1
        self.control = control.name
        # the matched lines themselves, one example per distinct line, commonest across our files first
        ours_at: dict[int, tuple[int, int]] = {}
        count: Counter = Counter()
        for di, d in enumerate(self.docs):
            for p, h in enumerate(d.words):
                if any(h in sets[n] for n in self.names):
                    ours_at.setdefault(h, (di, p))
                    count[h] += 1
        where: dict[int, tuple[str, str, int]] = {}
        for c in real:
            for cd in c.code:
                for j, h in enumerate(cd.words):
                    if h in ours_at and h not in where:
                        where[h] = (c.name, cd.rel, cd.lines[j])
        self.examples = [(count[h], self.docs[di], p, where[h]) for h, (di, p) in ours_at.items()]
        self.examples.sort(key=lambda e: (-e[0], e[1].rel, e[2]))

    def skill_total(self, sk: str) -> int:
        return sum(v for (s, _), v in self.total.items() if s == sk)

    def max_hit(self, sk: str, key=None) -> tuple[float, str]:
        """(share of the skill's code lines found verbatim in one source, that source)."""
        t = self.skill_total(sk)
        if not t:
            return 0.0, ""
        best = max(self.names, key=lambda n: sum(v for (s, _), v in self.hit[n].items() if s == sk))
        return sum(v for (s, _), v in self.hit[best].items() if s == sk) / t, best

    def sum_for(self, counter: Counter, sk: str) -> int:
        return sum(v for (s, _), v in counter.items() if s == sk)


# ---------------------------------------------------------------- report sections for the asset study

def _src_line(r: Run) -> str:
    return f"`{r.src_rel}:{r.src_line[0]}-{r.src_line[1]}`"


def top_runs(runs: list, k: int = 10, step: int = 4) -> list:
    """The k longest runs, one per place in our files (a run found in several sources is listed once)."""
    seen, out = set(), []
    for r in sorted(runs, key=lambda r: -r.length):
        key = (r.our_doc, r.our_start // step)
        if key not in seen:
            seen.add(key)
            out.append(r)
        if len(out) == k:
            break
    return out


def render_assets(w, x) -> None:
    st, cs, band = x.study, x.code, BAND[x.backend.kind]
    skills, names = st.skills, st.names
    md = x.md_S
    w("")
    w("## Part 2. Every asset, not only Markdown")
    w("")
    w("Part 1 compares Markdown prose. Part 2 adds every other text file that ships in a skill folder: on our side "
      "`SKILL.md`, `references/`, `assets/`, `scripts/` and `agents/` (not `eval.md`); on the source side the same "
      "folders of each source skill, with README, LICENSE, CHANGELOG, translations, tests, bundles, `dist/` and hidden "
      "files left out. Each file is split into **prose** and **code**:")
    w("")
    w("- *Prose*: Markdown text outside fences; comments and docstrings of code files; string values of YAML and JSON; the "
      "text nodes of HTML; TeX text. Prose is compared at all three levels (verbatim 8-word runs, close paraphrase, "
      "same idea) exactly as in Part 1, with the non-Markdown prose added on both sides.")
    w(f"- *Code*: every other line of a code, markup or data file (comments removed) and the lines inside Markdown "
      f"fences (type `md-fence`). A line is normalised by deleting all whitespace and kept when it has at least "
      f"{sa.CODE_MIN} characters. Reported: the share of our code lines that occur verbatim in a source, and runs of "
      f"{CODE_RUN} or more consecutive kept lines that occur in the same order in a source. Lines this common (an "
      f"`if __name__ == '__main__':` line, `from __future__ import annotations`) occur in unrelated code too; the control "
      f"column counts them.")
    w("")
    w("### 2.1 What was compared")
    w("")
    w("| source | prose words: Markdown selection | prose words: other file types | code files | code lines |")
    w("|---|---:|---:|---:|---:|")
    for c in x.full:
        lv = c.legacy_view().words
        w(f"| {c.name} | {lv} | {c.words - lv} | {len(c.code)} | {c.code_lines} |")
    for c in (x.control_full, x.control_med):
        lv = c.legacy_view().words
        w(f"| {c.name} | {lv} | {c.words - lv} | {len(c.code)} | {c.code_lines} |")
    ow = Counter()
    ol = Counter()
    for d in st.docs:
        ow[d.kind] += len(d.words)
    for d in cs.docs:
        ol[d.kind] += len(d.words)
    w("")
    w("Ours: prose words " + ", ".join(f"{k} {v}" for k, v in sorted(ow.items())) + "; code lines "
      + ", ".join(f"{k} {v}" for k, v in sorted(ol.items())) + ".")
    w("")
    w("### 2.2 Prose, all file types")
    w("")
    w("Same measures as Part 1 on all prose. *Same idea* is the share of our sentences at or above the cut. The band "
      "estimate adds the sentences just below the cut at the rate a hand-read sample found"
      + (f" ({band[1]} of {band[2]} pairs drawn uniformly from cosine {band[0]:.2f} to {st.threshold:.2f} stated the same "
         f"rule). That sample took each sentence's best match over all sources, so the estimate is design-matched for "
         f"*any source*; for a single source it is an upper bound, because that source's band match is usually weaker than "
         f"the best match anywhere"
         if band else " (not available for the TF-IDF fallback)") + ". The last two columns repeat Part 1's Markdown-only "
      "figures so the effect of the added files is visible.")
    w("")
    w("| skill | prose words (md / other) | max verbatim (source) | verbatim, any source | max close paraphrase (source) | "
      "max same idea, one source (source) | one source, upper estimate | same idea, any source: cut / with band | "
      "control same idea (whole pool) | Part 1: max verbatim | Part 1: max same idea |")
    w("|---|---|---|---:|---|---|---|---|---:|---:|---:|")
    for sk in skills:
        kinds = st.by_kind(sk)
        mdw = kinds.get("md", (0,))[0]
        v, vn = st.best(sk, 0)
        c_, cn = st.best(sk, 1)
        s_, sn = st.best(sk, 2)
        hi = f"{pct(st.adjusted(sk, band)[0])} ({st.adjusted(sk, band)[1]})" if band else "n/a"
        a_cut, a_band = st.any_same_idea(sk, band[0] if band else st.threshold)
        anyr = f"{pct(a_cut)} / {pct(a_cut + a_band * band[1] / band[2])}" if band else f"{pct(a_cut)} / n/a"
        p1v = max(md[n][sk][0] for n in x.md_names)
        p1s = max(md[n][sk][2] for n in x.md_names)
        w(f"| {sk} | {mdw} / {st.words[sk] - mdw} | {pct(v)} ({vn}) | {pct(st.any_verbatim(sk))} | {pct(c_)} ({cn}) | "
          f"{pct(s_)} ({sn}) | {hi} | {anyr} | {pct(st.S['control'][sk][2])} | {pct(p1v)} | {pct(p1s)} |")
    w("")
    w("Differences from Part 1 come from the extra prose (docstrings, comments, YAML values, other file types) entering the "
      "denominator and from the few matches it adds; both sides of every comparison also gain their non-Markdown prose.")
    w("")
    w("### 2.3 Code")
    w("")
    w(f"Share of our normalised code lines (at least {sa.CODE_MIN} characters) found verbatim in one source's code, and "
      f"share inside runs of {CODE_RUN}+ consecutive lines. *Also in control*: of the lines found in any source, the share "
      f"that also occur in the unrelated control skills (generic boilerplate).")
    w("")
    w("| skill | code lines (by type) | max lines in one source (source) | lines in any source | of those, also in control | "
      "control: lines found | max lines inside "
      f"{CODE_RUN}+ line runs (source) |")
    w("|---|---|---|---:|---:|---:|---|")
    tot_lines = tot_any = tot_boiler = 0
    for sk in skills:
        t = cs.skill_total(sk)
        if not t:
            w(f"| {sk} | none | | | | | |")
            continue
        by = ", ".join(f"{k} {cs.total[(sk2, k)]}" for sk2, k in cs.keys if sk2 == sk)
        mh, mn = cs.max_hit(sk)
        any_ = cs.sum_for(cs.any_hit, sk)
        bo = cs.sum_for(cs.boiler, sk)
        ctl = cs.sum_for(cs.hit[cs.control], sk)
        rn = max(cs.names, key=lambda n: cs.sum_for(cs.run[n], sk))
        tot_lines += t
        tot_any += any_
        tot_boiler += bo
        w(f"| {sk} | {by} | {pct(mh)} ({mn}) | {pct(any_ / t)} | {pct(bo / any_) if any_ else 'n/a'} | "
          f"{pct(ctl / t)} | {pct(cs.sum_for(cs.run[rn], sk) / t)} ({rn}) |")
    w("")
    w(f"All skills: {tot_lines} code lines, {pct(tot_any / tot_lines)} found in some source, "
      f"{pct(tot_boiler / tot_lines)} of all code lines are generic lines that the control also has.")
    w("")
    w(f"Longest shared code runs (kept lines, at least {CODE_RUN}):")
    w("")
    runs = top_runs(cs.runs, 10, CODE_RUN)
    if runs:
        w("| # | lines | source | our file (lines) | source file (lines) | first line (whitespace removed) |")
        w("|---:|---:|---|---|---|---|")
        for i, r in enumerate(runs, 1):
            d = cs.docs[r.our_doc]
            w(f"| {i} | {r.length} | {r.source} | `{d.rel}:{d.lines[r.our_start]}-{d.lines[r.our_start + r.length - 1]}` | "
              f"{_src_line(r)} | `{d.norm[r.our_start][:70]}` |")
    else:
        w(f"No run of {CODE_RUN} or more consecutive code lines is shared with any source.")
    w("")
    w("Single lines found in a source (up to 15 distinct lines, commonest first), so a human can judge whether they are "
      "boilerplate or borrowed:")
    w("")
    w("| times in ours | our file:line | line (whitespace removed) | first source file:line |")
    w("|---:|---|---|---|")
    for n, d, p, (sname, srel, sline) in cs.examples[:15]:
        w(f"| {n} | `{d.rel}:{d.lines[p]}` | `{d.norm[p][:80]}` | {sname} `{srel}:{sline}` |")
    w("")
    w("### 2.4 Asset-type breakdown per skill")
    w("")
    w("Words for prose types, kept lines for code types. *Max verbatim* is the highest share over sources: prose words in "
      f"8-word runs found in that source; code lines found verbatim in that source.")
    w("")
    w("| skill | type | role | amount | max verbatim | source |")
    w("|---|---|---|---:|---:|---|")
    for sk in skills:
        for kind, (words, top, share) in st.by_kind(sk).items():
            w(f"| {sk} | {kind} | prose | {words} words | {pct(share)} | {top if share else ''} |")
        for sk2, kind in cs.keys:
            if sk2 != sk:
                continue
            n = max(cs.names, key=lambda m: cs.hit[m][(sk, kind)])
            share = cs.hit[n][(sk, kind)] / cs.total[(sk, kind)]
            w(f"| {sk} | {kind} | code | {cs.total[(sk, kind)]} lines | {pct(share)} | {n if share else ''} |")
    w("")
    w("### 2.5 Longest verbatim runs, all prose types")
    w("")
    w("| # | words | source | our file (lines) | source file (lines) | run |")
    w("|---:|---:|---|---|---|---|")
    for i, r in enumerate(top_runs([r for n in names for r in st.results[n].runs]), 1):
        d = st.docs[r.our_doc]
        text = " ".join(r.words[:45]) + (" ..." if len(r.words) > 45 else "")
        w(f"| {i} | {r.length} | {r.source} | `{d.rel}:{d.lines[r.our_start]}-{d.lines[r.our_start + r.length - 1]}` | "
          f"{_src_line(r)} | {text} |")


def _g(m) -> str:
    return {"strong": "firm", "covered": "likely", "no": "no"}[m.grade]


def render_rules(w, x) -> None:
    w("")
    w("## Part 3. Rule inventory")
    w("")
    w("For the two pairs where one of our skills was written from one source, every pattern or rule heading of the source "
      "is checked against our files, and every rule heading of ours against the source's files. A *unit* is a Markdown "
      "section, list item or table row; a rule matches when its best unit on the other side has cosine at or above the cut "
      "(firm at or above "
      f"{sr.CUTS[x.backend.kind][0]}, likely at or above {sr.CUTS[x.backend.kind][1]}) or a heading there names the same "
      "thing (shared word stems, pattern ids included). The cuts were set on 70 hand-labelled pairs; in that sample firm "
      "matches were right 27 of 29 times and found 27 of the 39 truly covered rules, and firm-or-likely matches were right "
      "35 of 41 times and found 35 of 39 (in-sample; TF-IDF cuts are not calibrated). Read the shares as a count with a "
      "few points of error either way; the per-rule tables below let a human check any line.")
    w("")
    w("What counts as a rule: for avoid-ai-writing, each `###` pattern heading and `Tier` heading of `references/patterns.md` "
      "before its context profiles, plus the bold entries under Formatting and Sentence structure; for humanizer, its 26 "
      "numbered patterns; for anti-slop-editing, each `###` heading of `pattern-catalog.md` and each numbered rule in "
      "`SKILL.md`; for author-voice, each numbered rule in `SKILL.md` and each trait row of `trait-catalog.md`. The source "
      "side of the trace is all units of the source's `SKILL.md` and, for avoid-ai-writing, `patterns.md`.")
    w("")
    w("| our skill | source | source rules | covered by our paired skill: firm / firm+likely | covered by any of our skills | "
      "our rules | our rules that trace to the source: firm / firm+likely |")
    w("|---|---|---:|---|---|---:|---|")
    for r in x.inventory:
        w(f"| {r['ours']} | {r['theirs']} | {len(r['their_rules'])} | {pct(sr.share(r['covered'], True))} / "
          f"{pct(sr.share(r['covered']))} | {pct(sr.share(r['covered_any'], True))} / {pct(sr.share(r['covered_any']))} | "
          f"{len(r['our_rules'])} | {pct(sr.share(r['traced'], True))} / {pct(sr.share(r['traced']))} |")
    for r in x.inventory:
        w("")
        w(f"### {r['theirs']} rules and {r['ours']}")
        w("")
        w(f"Source rules ({len(r['their_rules'])}), best matching unit in `{r['ours']}` and, if different, the best match in "
          f"any of our skills.")
        w("")
        w("| source rule | in " + r["ours"] + " | cos | our unit | any of our skills |")
        w("|---|---|---:|---|---|")
        for m, a in zip(r["covered"], r["covered_any"]):
            other = ""
            if a.best is not None and (a.best.rel != (m.best.rel if m.best else "")) and a.grade != "no":
                other = f"{_g(a)}: {a.best.shown[:50]} (`{a.best.rel.split('/')[1]}`)"
            elif a.grade != "no":
                other = "same"
            w(f"| {m.rule.heading[:70]} | {_g(m)} | {m.cos:.2f} | {m.best.shown[:60] if m.best else ''} "
              f"(`{m.best.label}`) | {other} |")
        w("")
        w(f"Our rules ({len(r['our_rules'])}) and their best matching unit in the source's files.")
        w("")
        w("| our rule | traces to source | cos | source unit |")
        w("|---|---|---:|---|")
        for m in r["traced"]:
            w(f"| {m.rule.heading[:70]} | {_g(m)} | {m.cos:.2f} | {m.best.shown[:60] if m.best else ''} "
              f"(`{m.best.label}`) |")
        miss = [m.rule.heading for m in r["covered"] if m.grade == "no"]
        w("")
        w(f"Source rules our paired skill does not cover ({len(miss)}): " + ("; ".join(miss) if miss else "none") + ".")


def render_docs(x) -> str:
    st, cs, band = x.study, x.code, BAND[x.backend.kind]
    skills = st.skills
    L = []
    w = L.append
    w("# Source similarity")
    w("")
    w("How close each of our skills is to the third-party skills they were written from. Generated by "
      "`evals/source_similarity.py`; the full report (matrices for all sources, per-skill tables, calibration pairs, every "
      "rule) is `evals/results/source-similarity.md` (not committed). Source commits are pinned in "
      "`.cache/omw_sources/SHAS.txt`. Part 1 of the full report keeps the Markdown-only file selection and method of the "
      "first version of this script, so its numbers stay comparable; the figures below cover every asset.")
    w("")
    w("## Copying: verbatim prose and code")
    w("")
    w("Verbatim prose is the share of our words inside 8-word runs that also occur in one source (all text files, not only "
      f"Markdown). Verbatim code is the share of our normalised code lines (at least {sa.CODE_MIN} characters, whitespace "
      "and comments removed) found in one source's code. Both are the highest value over the sources.")
    w("")
    w("| skill | max verbatim prose (source) | max verbatim code lines (source) | code lines |")
    w("|---|---|---|---:|")
    for sk in skills:
        v, vn = st.best(sk, 0)
        t = cs.skill_total(sk)
        mh, mn = cs.max_hit(sk)
        code = f"{pct(mh)} ({mn})" if t and mh else ("0.0%" if t else "no code")
        w(f"| {sk} | {pct(v)} ({vn if v else 'none'}) | {code} | {t} |")
    cv = {n: statistics.fmean(st.S[n][sk][0] for sk in skills) for n in ("control", "control@median")}
    ct = cs.skill_total
    cl = sum(cs.sum_for(cs.hit[cs.control], sk) for sk in skills)
    tl = sum(ct(sk) for sk in skills)
    w(f"| *control (unrelated skills)* | {pct(cv['control'])} mean | {pct(cl / tl)} of {tl} lines | |")
    w("")
    w(f"Longest shared prose runs (words) and code runs ({CODE_RUN}+ lines), for a human to check:")
    w("")
    w("| kind | length | our file | source file |")
    w("|---|---:|---|---|")
    for r in top_runs([r for n in st.names for r in st.results[n].runs], 10):
        d = st.docs[r.our_doc]
        w(f"| prose | {r.length} words | `{d.rel}:{d.lines[r.our_start]}-{d.lines[r.our_start + r.length - 1]}` | {_src_line(r)} |")
    for r in top_runs(cs.runs, 5, CODE_RUN):
        d = cs.docs[r.our_doc]
        w(f"| code | {r.length} lines | `{d.rel}:{d.lines[r.our_start]}-{d.lines[r.our_start + r.length - 1]}` | {_src_line(r)} |")
    w("")
    w("")
    w("Single code lines found in a source, commonest first (judge for yourself whether they are idioms or borrowed logic):")
    w("")
    w("| our file | line (whitespace removed) | found in |")
    w("|---|---|---|")
    for n, d, p, (sname, srel, sline) in cs.examples[:5]:
        w(f"| `{d.rel}:{d.lines[p]}` | `{d.norm[p][:60]}` | {sname} |")
    w("")
    w("## Same idea")
    w("")
    w(f"Share of our sentences whose best sentence has embedding cosine at or above {st.threshold}: the precise cut, which "
      "misses paraphrases that score lower. The estimate adds the sentences between "
      + (f"{band[0]:.2f} and {st.threshold:.2f} at the rate a hand-read uniform sample found ({band[1]} of {band[2]} "
         f"pairs stated the same rule; 95% interval for that rate {pct(wilson(band[1], band[2])[0])} to "
         f"{pct(wilson(band[1], band[2])[1])})" if band else "the bands at the sampled rate")
      + ". The sample took each sentence's best match over all sources, so *any source* is the design-matched estimate; "
      "for one source the estimate is an upper bound. Both count advice two authors reach independently, so they measure "
      "overlap of ideas, not copying; the control rows give the noise floor. The pairs were read generously: general advice "
      "such as cutting filler counted as the same rule.")
    w("")
    w("| skill | one source, at the cut (source) | one source, upper estimate | any source: at the cut | any source: estimate |")
    w("|---|---|---|---:|---:|")
    for sk in skills:
        s_, sn = st.best(sk, 2)
        hi, hn = st.adjusted(sk, band) if band else (None, "")
        a_cut, a_band = st.any_same_idea(sk, band[0] if band else st.threshold)
        w(f"| {sk} | {pct(s_)} ({sn}) | {pct(hi) + f' ({hn})' if hi is not None else 'n/a'} | {pct(a_cut)} | "
          f"{pct(a_cut + a_band * band[1] / band[2]) if band else 'n/a'} |")
    for c in (x.control_med, x.control_full):
        one_hi = [st.S[c.name][sk][2] + (st.band_share(c.name, sk, band[0]) * band[1] / band[2] if band else 0)
                  for sk in skills]
        w(f"| *control: {'median-size' if c is x.control_med else 'whole'} unrelated pool* (mean, max over skills) | "
          f"{pct(statistics.fmean(st.S[c.name][sk][2] for sk in skills))}, "
          f"{pct(max(st.S[c.name][sk][2] for sk in skills))} | "
          f"{pct(statistics.fmean(one_hi))}, {pct(max(one_hi))} | n/a | n/a |")
    w("")
    w("## Rule inventory")
    w("")
    w("| our skill | source | source rules covered by our skill (firm / firm+likely) | covered by any of our skills | "
      "our rules that trace to the source (firm / firm+likely) |")
    w("|---|---|---|---|---|")
    for r in x.inventory:
        w(f"| {r['ours']} | {r['theirs']} ({len(r['their_rules'])} rules) | {pct(sr.share(r['covered'], True))} / "
          f"{pct(sr.share(r['covered']))} | {pct(sr.share(r['covered_any'], True))} / {pct(sr.share(r['covered_any']))} | "
          f"{pct(sr.share(r['traced'], True))} / {pct(sr.share(r['traced']))} of {len(r['our_rules'])} |")
    w("")
    w("A source rule is *covered* when one unit of our files (a section, list item or table row) has cosine at or above "
      "the cut with it or a heading there names the same thing; an *our rule traces* when the same holds in the source's "
      "files. *Firm* is the precise cut, *likely* adds the lower cut.")
    w("")
    w("## Method")
    w("")
    w(x.method)
    w("")
    return "\n".join(L)


# ---------------------------------------------------------------- report

def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def run_report(args) -> str:
    cache = Path(args.cache) if args.cache else RESULTS / ".similarity-embeddings.npz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    backend = make_backend(args.semantic, cache)
    threshold = args.threshold if args.threshold is not None else THRESHOLD[backend.kind]
    ours = load_ours()
    ours_all, ours_code = load_ours_all()
    full = [load_corpus(s) for s in SOURCES]
    sources = [c.legacy_view() for c in full]
    real = [c for c in sources if c.docs]
    control_full = load_corpus(Source("control", CONTROL_REPO, skill_roots=CONTROL_ROOTS,
                                      note="jezweb dev-tools, cloudflare, shopify, wordpress, frontend, integrations "
                                           "and design-assets skills"))
    control_pool = control_full.legacy_view()
    sizes = {c.name: c.words for c in real}
    median = int(statistics.median(sizes.values()))
    controls = [control_pool, sample_corpus(control_pool, min(median, control_pool.words), 1, "control@median")]
    matched = {c.name: sample_corpus(control_pool, min(c.words, control_pool.words), 2, f"control~{c.name}") for c in real}
    corpora = real + controls + list(matched.values())
    results, our_sents = analyse(ours, corpora, backend, threshold)
    np = backend.np

    skills = list(ours)
    S = {c.name: {sk: shares(results[c.name], our_sents, sk, threshold) for sk in skills} for c in corpora}
    n_sent = {sk: sum(1 for _, d in our_sents if d.skill == sk) for sk in skills}
    n_words = {sk: sum(len(d.words) for d in docs) for sk, docs in ours.items()}
    names = [c.name for c in real]

    def top(sk, level, k=3):
        return [n for n in sorted(names, key=lambda n: -S[n][sk][level])[:k] if S[n][sk][level] > 0]

    def top_text(sk, level):
        return ", ".join(f"{n} {pct(S[n][sk][level])}" for n in top(sk, level)) or "none"

    def any_cover(sk, source_names):
        idx = [k for k, (_, d) in enumerate(our_sents) if d.skill == sk]
        hit = 0
        for k in idx:
            if any((not results[n].verb_flag[k] and results[n].jac[k][0] >= JACCARD) or results[n].cos[k] >= threshold
                   for n in source_names):
                hit += 1
        return hit / len(idx)

    our_docs_flat = [d for docs in ours.values() for d in docs]

    def any_verbatim(sk):
        """Share of the skill's words covered by an 8-word run found in at least one real source."""
        covered = total = 0
        for i, d in enumerate(our_docs_flat):
            if d.skill != sk:
                continue
            total += len(d.words)
            for j in range(len(d.words)):
                if any(results[n].cov[i][j] for n in names):
                    covered += 1
        return covered / total

    L = []
    w = L.append
    w("# Source similarity: our skills against the third-party sources they were written from")
    w("")
    w("Part 1 (Markdown prose, the method and file selection of the first report), Part 2 (every asset: prose in any file "
      "type, code lines, asset-type breakdown), Part 3 (rule inventory for anti-slop-editing / avoid-ai-writing and "
      "author-voice / humanizer). The sections up to and including *10 longest verbatim runs* are Part 1.")
    w("")
    w(f"Semantic backend: **{backend.label}**; same-idea threshold **{threshold}**. "
      f"Our side: {sum(n_words.values())} words, {sum(n_sent.values())} sentences in {len(skills)} skills. "
      f"Source commits are pinned in `.cache/omw_sources/SHAS.txt`.")
    w("")
    w("## How to read this")
    w("")
    w("1. **Verbatim is the copying measure.** It is the share of our words inside 8-word runs that also occur in the "
      "source. A value near 0% means no sentence-length text was copied; a value of 5% or more needs a human look at the "
      "runs listed at the end (licence and attribution risk).")
    w("2. **Close paraphrase** catches light edits: our sentence shares at least half its word trigrams with one source "
      "sentence but is not verbatim. It is also a copying-adjacent measure.")
    w("3. **Same idea (semantic) is partly unavoidable.** Writing advice repeats across every source: *cut filler*, "
      "*lead with the point*, *name the reader*, *check every figure*. Two independent authors give the same rule. The "
      "control row shows how much same-idea match an unrelated corpus produces; only the gap above it says anything about "
      "our skills, and even that gap is not proof of copying, since common advice is the cause. Semantic matches also "
      "count the verbatim and close ones (the levels are cumulative).")
    w(f"4. All shares are of **our** words or sentences (a sentence has 6+ words). The best source sentence is "
      f"chosen per our sentence, so a big corpus has more chances to match than a small one: compare a column with "
      f"its size-matched control column (matrix section), not with a smaller source's column.")
    w("")
    w("## Corpora")
    w("")
    w("| source | docs | words | unique sentences | note |")
    w("|---|---:|---:|---:|---|")
    for c in sources:
        n_us = len(results[c.name].sents) if c.name in results else 0
        w(f"| {c.name} | {len(c.docs)} | {c.words} | {n_us} | {c.note or ''} |")
    for c in [control_pool, controls[1]]:
        w(f"| {c.name} | {len(c.docs)} | {c.words} | {len(results[c.name].sents)} | {c.note} |")
    w("")
    w(f"Median real-source size: {median} words; `control@median` is a random subset of that size. Sources larger than "
      f"the control pool ({control_pool.words} words) are matched with the whole pool, so their control is smaller than "
      f"they are.")
    skipped = [(c.name, p, r) for c in sources for p, r in c.skipped]
    if skipped:
        w("")
        w(f"Files left out as whole-file copies or non-English text: {len(skipped)} "
          f"({', '.join(f'{n}: `{Path(p).name}`' for n, p, _ in skipped[:12])}{' ...' if len(skipped) > 12 else ''}).")

    w("")
    w("## Summary per skill")
    w("")
    w("| skill | words | max verbatim (source) | verbatim, any source | max close paraphrase (source) | "
      "max same idea (source) | any source: close or same idea | control same idea (median-size / whole pool) |")
    w("|---|---:|---|---:|---|---|---:|---|")
    for sk in skills:
        mv = max(names, key=lambda n: S[n][sk][0])
        mc = max(names, key=lambda n: S[n][sk][1])
        ms = max(names, key=lambda n: S[n][sk][2])
        w(f"| {sk} | {n_words[sk]} | {pct(S[mv][sk][0])} ({mv}) | {pct(any_verbatim(sk))} | {pct(S[mc][sk][1])} ({mc}) | "
          f"{pct(S[ms][sk][2])} ({ms}) | {pct(any_cover(sk, names))} | "
          f"{pct(S['control@median'][sk][2])} / {pct(S['control'][sk][2])} |")

    def matrix(level, title, control_row=True):
        w("")
        w(f"## {title}")
        w("")
        w("| our skill \\ source | " + " | ".join(names) + " |")
        w("|---|" + "---:|" * len(names))
        for sk in skills:
            vals = [S[n][sk][level] for n in names]
            hi = max(vals)
            w(f"| {sk} | " + " | ".join((f"**{pct(v)}**" if v == hi and v > 0 else pct(v)) for v in vals) + " |")
        mean = [statistics.fmean(S[n][sk][level] for sk in skills) for n in names]
        w("| *mean over our skills* | " + " | ".join(pct(v) for v in mean) + " |")
        if control_row:
            cm = [statistics.fmean(S[f"control~{n}"][sk][level] for sk in skills) for n in names]
            w("| *control, same size as the column (mean)* | " + " | ".join(pct(v) for v in cm) + " |")

    matrix(2, "Matrix: same idea (semantic), share of our sentences")
    matrix(1, "Matrix: close paraphrase (not verbatim), share of our sentences")
    matrix(0, "Matrix: verbatim (8-word runs), share of our words")

    w("")
    w("## Control")
    w("")
    w("Our skills against unrelated skills (jezweb dev-tools and similar). Same measures, same threshold.")
    w("")
    w("| our skill | control | verbatim | close paraphrase | same idea |")
    w("|---|---|---:|---:|---:|")
    for sk in skills:
        for cn in ("control@median", "control"):
            v, c_, s_ = S[cn][sk]
            w(f"| {sk} | {cn} | {pct(v)} | {pct(c_)} | {pct(s_)} |")
    for cn in ("control@median", "control"):
        v = statistics.fmean(S[cn][sk][0] for sk in skills)
        c_ = statistics.fmean(S[cn][sk][1] for sk in skills)
        s_ = statistics.fmean(S[cn][sk][2] for sk in skills)
        w(f"| **mean** | {cn} | {pct(v)} | {pct(c_)} | {pct(s_)} |")

    best_real = np.max([results[n].cos for n in names], axis=0)
    w("")
    w("## Sensitivity to the same-idea threshold")
    w("")
    w("Share of our sentences (all skills pooled) whose best source sentence reaches each cosine. *Any real source* "
      "takes the best of all sources together; *mean single source* averages the per-source shares; the controls are "
      "unrelated skills (whole pool of " + str(control_pool.words) + " words, and the mean of the per-source "
      "size-matched controls). Read the gap between a real column and its control column, not the absolute value.")
    w("")
    w("| cosine | any real source | mean single source | control, whole pool | control, mean size-matched |")
    w("|---:|---:|---:|---:|---:|")
    for tau in SENSITIVITY[backend.kind]:
        w(f"| {tau:.2f}{' (used)' if abs(tau - threshold) < 1e-9 else ''} | {pct(float(np.mean(best_real >= tau)))} | "
          f"{pct(statistics.fmean(float(np.mean(results[n].cos >= tau)) for n in names))} | "
          f"{pct(float(np.mean(results['control'].cos >= tau)))} | "
          f"{pct(statistics.fmean(float(np.mean(results[f'control~{n}'].cos >= tau)) for n in names))} |")

    w("")
    w("## Per skill: top sources")
    for sk in skills:
        w("")
        w(f"### {sk}")
        w("")
        w(f"Top 3 verbatim: {top_text(sk, 0)}. Top 3 close paraphrase: {top_text(sk, 1)}. "
          f"Top 3 same idea: {top_text(sk, 2)}.")
        w("")
        w("| source | verbatim | close paraphrase | same idea |")
        w("|---|---:|---:|---:|")
        order = []
        for lv in (2, 0, 1):
            for n in top(sk, lv):
                if n not in order:
                    order.append(n)
        for n in sorted(order, key=lambda n: -S[n][sk][2]):
            v, c_, s_ = S[n][sk]
            w(f"| {n} | {pct(v)} | {pct(c_)} | {pct(s_)} |")
        for cn in ("control@median", "control"):
            v, c_, s_ = S[cn][sk]
            w(f"| *{cn}* | {pct(v)} | {pct(c_)} | {pct(s_)} |")
        w(f"| *any source (close or same idea)* | | | {pct(any_cover(sk, names))} |")

    # pairs above the threshold
    rng = random.Random(7)
    cand = []
    for k, (s, d) in enumerate(our_sents):
        best_n = max(names, key=lambda n: results[n].cos[k])
        r = results[best_n]
        if r.cos[k] >= threshold and not r.verb_flag[k] and r.jac[k][0] < JACCARD:
            cand.append((float(r.cos[k]), k, best_n))
    cand.sort()
    near = [c for c in cand if c[0] < threshold + 0.05]
    mid = [c for c in cand if threshold + 0.05 <= c[0] < threshold + 0.15]
    w("")
    w("## Threshold and calibration")
    w("")
    w(f"Same-idea threshold: **{threshold}** ({backend.label}). It was chosen by reading sample pairs (our sentence, its "
      f"best source sentence) across the cosine range and picking the cut above which the pair states the same rule.")
    w("")
    w(CALIBRATION[backend.kind] or "(calibration notes not recorded for this backend)")
    for label, pool_ in (("just above the threshold", near), ("0.05 to 0.15 above it", mid)):
        w("")
        w(f"Example pairs {label} (not verbatim, not close paraphrase):")
        w("")
        w("| cos | our sentence | best source sentence | source |")
        w("|---:|---|---|---|")
        for cos, k, n in rng.sample(pool_, min(3, len(pool_))):
            s, d = our_sents[k]
            r = results[n]
            t = r.sents[int(r.cos_arg[k])]
            doc = r.sent_doc[int(r.cos_arg[k])]
            w(f"| {cos:.2f} | {s.text[:200]} ({d.rel}:{s.line}) | {t.text[:200]} | {n}: `{doc.rel}:{t.line}` |")

    all_runs = sorted((r for n in names for r in results[n].runs), key=lambda r: -r.length)
    seen, picked = set(), []
    for r in all_runs:
        key = (r.our_doc, r.our_start // 4)
        if key in seen:
            continue
        seen.add(key)
        picked.append(r)
        if len(picked) == 10:
            break
    w("")
    w("## 10 longest verbatim runs")
    w("")
    w("Longest word runs (lowercased, punctuation dropped) found in both one of our files and one source file; "
      "a run found in several source files is listed once.")
    w("")
    w("| # | words | source | our file (lines) | source file (lines) | run |")
    w("|---:|---:|---|---|---|---|")
    for i, r in enumerate(picked, 1):
        d = our_docs_flat[r.our_doc]
        l0, l1 = d.lines[r.our_start], d.lines[r.our_start + r.length - 1]
        text = " ".join(r.words[:45]) + (" ..." if len(r.words) > 45 else "")
        w(f"| {i} | {r.length} | {r.source} | `{d.rel}:{l0}-{l1}` | `{r.src_rel}:{r.src_line[0]}-{r.src_line[1]}` | {text} |")
    w("")

    # ---- Part 2 and 3
    real_full = [c for c in full if c.docs]
    med_full = int(statistics.median(c.words for c in real_full))
    control_med = sample_corpus(control_full, min(med_full, control_full.words), 1, "control@median")
    control_med.code = []
    control_full.name = "control"
    study = Study(ours_all, real_full + [control_full, control_med], [c.name for c in real_full], backend, threshold)
    code = CodeStudy(ours_code, [c for c in real_full if c.code], control_full)
    inv = sr.inventory(backend, ROOT, CACHE, sr.CUTS[backend.kind])
    x = types.SimpleNamespace(backend=backend, full=real_full, control_full=control_full, control_med=control_med,
                              study=study, code=code, md_S=S, md_names=names, inventory=inv, method="")
    render_assets(w, x)
    render_rules(w, x)
    x.method = METHOD.format(model=backend.label, threshold=threshold, gram=GRAM, code_min=sa.CODE_MIN, code_run=CODE_RUN)
    return "\n".join(L), render_docs(x)


def calibrate(args) -> None:
    """Write sentence pairs across the cosine range for a human to read (not used by the report)."""
    cache = Path(args.cache) if args.cache else RESULTS / ".similarity-embeddings.npz"
    backend = make_backend(args.semantic, cache)
    ours = load_ours()
    real = [c for c in (load_corpus(s).legacy_view() for s in SOURCES) if c.docs]
    results, our_sents = analyse(ours, real, backend, 1.0)
    lo, hi = args.calibrate_range
    rng = random.Random(args.seed)
    pairs = []
    for k, (s, d) in enumerate(our_sents):
        best = max(real, key=lambda c: results[c.name].cos[k])
        r = results[best.name]
        if not r.verb_flag[k] and r.jac[k][0] < JACCARD and lo <= r.cos[k] < hi:
            pairs.append((float(r.cos[k]), s.text, r.sents[int(r.cos_arg[k])].text, best.name))
    bins = defaultdict(list)
    step = (hi - lo) / args.bins
    for p in pairs:
        bins[min(args.bins - 1, int((p[0] - lo) / step))].append(p)
    out = []
    if args.uniform:
        out = rng.sample(pairs, min(args.uniform, len(pairs)))
        print(f"{len(pairs)} pairs in [{lo}, {hi}); sampled {len(out)} uniformly")
    else:
        for b in sorted(bins):
            for p in rng.sample(bins[b], min(args.per_bin, len(bins[b]))):
                out.append(p)
    out.sort()
    lines = [f"# calibration pairs, {backend.label}", ""]
    for i, (cos, a, b, n) in enumerate(out, 1):
        lines += [f"{i}. cos={cos:.3f} [{n}]", f"   OURS: {a}", f"   SRC:  {b}", ""]
    Path(args.calibrate).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", help="write the Markdown report here")
    p.add_argument("--docs", help="write the short committed summary here (docs/SOURCE_SIMILARITY.md)")
    p.add_argument("--semantic", choices=("auto", "embed", "tfidf"), default="auto")
    p.add_argument("--threshold", type=float, help="override the same-idea cosine threshold")
    p.add_argument("--cache", help="embedding cache file (default evals/results/.similarity-embeddings.npz)")
    p.add_argument("--calibrate", help="write calibration pairs to this file and stop")
    p.add_argument("--calibrate-range", type=float, nargs=2, default=(0.4, 0.9), metavar=("LO", "HI"))
    p.add_argument("--bins", type=int, default=10)
    p.add_argument("--per-bin", type=int, default=4)
    p.add_argument("--uniform", type=int, help="with --calibrate: N pairs drawn uniformly from the range, not by bin")
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    if args.calibrate:
        calibrate(args)
        return
    text, docs = run_report(args)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    if args.docs:
        Path(args.docs).write_text(docs, encoding="utf-8")


if __name__ == "__main__":
    main()
