#!/usr/bin/env python3
"""How close each of our skills is to each third-party source corpus, at three levels.

  uv run --with sentence-transformers --with numpy python3 evals/source_similarity.py --out evals/results/source-similarity.md
  python3 evals/source_similarity.py --out evals/results/source-similarity.md     # TF-IDF fallback, numpy only

The first command runs level 3 with the all-MiniLM-L6-v2 embedding model (downloaded on first use, about 90 MB, then
cached; sentence vectors are cached in evals/results/.similarity-embeddings.npz). The second needs only numpy and
falls back to TF-IDF cosine over sentences, and the report says so. `--semantic embed|tfidf|auto` forces a backend.
`--calibrate FILE` writes sentence pairs across the cosine range for a human to read when choosing the threshold.

Text compared: for a source, every SKILL.md plus the Markdown under that skill's folder (references/, assets/,
rules/, ...), or, for guide and prompt collections, their content files. For us, SKILL.md, references/, assets/ (no
eval.md, no agents/). README, LICENSE, CHANGELOG, non-English files, tests, scripts, release notes, mirrors for other
hosts, whole-file bundles (source_duplication.whole_file_copies) and fenced code are left out.

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
from array import array
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import source_duplication as sd  # noqa: E402

ROOT = HERE.parent
CACHE = ROOT / ".cache" / "omw_sources"
RESULTS = HERE / "results"
GRAM = sd.GRAM
MIN_WORDS = sd.MIN_WORDS
JACCARD = 0.5
VERBATIM_SENTENCE = 0.5     # share of a sentence's words inside shared 8-word runs that makes it verbatim
RUN_MIN_REPORT = GRAM       # shortest verbatim run kept for the longest-runs list
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

PIECE_SPLIT = re.compile(r"(?<=[.!?])\s+|\s*\|\s*")
LANG = r"(?:zh|ja|ko|es|fr|de|pt|ru|tr|vi|it|ar|hi|pl|th|uk|ur|id|nl|cs|sv|he|fa|bn|el|hu|ro)"
LANG_DIR = re.compile(rf"^{LANG}(?:[-_][A-Za-z]{{2,4}})?$", re.I)
LANG_FILE = re.compile(rf"(?:\.|[-_]){LANG}(?:[-_][A-Za-z]{{2,4}})?\.(?:md|txt|rst)$", re.I)
EXCLUDE_DIRS = (sd.SKIP_DIRS | {"scripts", "agents", "dist", "plugins", "archive", "pi", "submission", "cursor-rules",
                                "corpus", "detector", "bin", "release", "releases", "release-notes", "demo", "website",
                                "node_modules", "build", "vendor", "fixtures", "assets-src", "ecc2"})
ROOT_SKILL_SUBDIRS = {"references", "reference", "assets", "rules", "modes", "core", "templates"}
OUR_SUBDIRS = {"references", "assets"}


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


@dataclass
class Corpus:
    name: str
    docs: list = field(default_factory=list)
    skipped: list = field(default_factory=list)    # (relative path, reason)
    note: str = ""

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


def build_doc(path: Path, rel: str, skill: str = "") -> Doc | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    letters = [c for c in text if c.isalpha()]
    if letters and sum(ord(c) > 0x24F for c in letters) / len(letters) > 0.2:
        return None   # not English (a translation, or a Chinese-language skill)
    if path.suffix == ".rst":
        text = rst_to_text(text)
    text = sd.FENCE.sub(lambda m: "\n" * m.group().count("\n"), text)
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
    return Doc(path, rel, words, lines, sents, skill)


def excluded_part(parts) -> bool:
    return any(p.startswith(".") or p in EXCLUDE_DIRS or p.startswith("skills-codex") or LANG_DIR.match(p)
               for p in parts)


def usable_name(p: Path) -> bool:
    n = p.name.lower()
    return (n not in sd.SKIP_NAMES and not n.startswith("readme") and not LANG_FILE.search(n)
            and not n.endswith(("-bundled.md", ".full.md")))


def skill_folder_files(folder: Path, repo: Path) -> list[Path]:
    """SKILL.md plus the Markdown under a skill folder. A skill at the repo root takes only its known content folders;
    nested skills' files belong to those skills."""
    at_root = folder == repo
    out = [folder / "SKILL.md"]
    for p in sorted(folder.rglob("*")):
        if p.suffix.lower() != ".md" or p.name == "SKILL.md" or not p.is_file() or not usable_name(p):
            continue
        inner = p.relative_to(folder).parts[:-1]
        if excluded_part(inner):
            continue
        if at_root and (not inner or inner[0] not in ROOT_SKILL_SUBDIRS):
            continue
        if any((folder.joinpath(*inner[:i + 1]) / "SKILL.md").is_file() for i in range(len(inner))):
            continue
        out.append(p)
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


def collect_files(src: Source, repo: Path) -> list[tuple[str, list[Path]]]:
    """(group key, files) pairs. Skill folders form their own group so bundles are detected among siblings."""
    groups: list[tuple[str, list[Path]]] = []
    seen: set[Path] = set()
    roots = [repo] if src.skill_roots is None else [repo / r for r in src.skill_roots]
    for base in roots:
        if not base.is_dir():
            continue
        for skill_md in sorted(base.rglob("SKILL.md")):
            if excluded_part(skill_md.relative_to(base).parts[:-1]):
                continue
            files = [f for f in skill_folder_files(skill_md.parent, repo) if f not in seen]
            seen.update(files)
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
        groups.append(("", extra))
    return groups


def load_corpus(src: Source, repo: Path | None = None, roots: tuple | None = None) -> Corpus:
    repo = repo or CACHE / src.repo
    c = Corpus(src.name, note=src.note)
    if not repo.is_dir():
        c.note = c.note or "repository not in cache"
        return c
    for key, files in collect_files(src, repo):
        dropped = sd.whole_file_copies(files) if key and len(files) > 1 else []
        for f in files:
            rel = str(f.relative_to(CACHE)) if f.is_relative_to(CACHE) else str(f)
            if f in dropped:
                c.skipped.append((rel, "whole-file copy of sibling files"))
                continue
            d = build_doc(f, rel)
            if d is None:
                c.skipped.append((rel, "non-English"))
            elif d.words:
                c.docs.append(d)
    return c


def load_ours() -> dict[str, list[Doc]]:
    out = {}
    for sk in sorted((ROOT / "skills").iterdir()):
        if not (sk / "SKILL.md").is_file():
            continue
        files = [sk / "SKILL.md"] + [p for p in sorted(sk.rglob("*.md")) if p.name != "SKILL.md"
                                      and p.name != "eval.md" and p.relative_to(sk).parts[0] in OUR_SUBDIRS]
        docs = [build_doc(f, str(f.relative_to(ROOT)), sk.name) for f in files]
        out[sk.name] = [d for d in docs if d and d.words]
    return out


def truncate(d: Doc, n: int) -> Doc:
    return Doc(d.path, d.rel, d.words[:n], d.lines[:n], [s for s in d.sents if s.start + len(s.tokens) <= n], d.skill)


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


def verbatim_pass(corpus: Corpus, our_docs: list[Doc], our_index: dict, keep_runs: int = 40):
    """One pass over the source: per our doc, a coverage mask; plus the longest shared runs (any length >= RUN_MIN_REPORT)."""
    cov = [bytearray(len(d.words)) for d in our_docs]
    runs: list[tuple] = []
    block = b"\x01" * GRAM

    def close(o, key, a, sdoc):
        length = a[1] - a[0] + GRAM
        if length >= RUN_MIN_REPORT:
            runs.append((length, o, key[1] + a[0], sdoc, a[0], a[1]))

    for si, sdoc in enumerate(corpus.docs):
        active: dict = {}
        for j, h in enumerate(gram_hashes(sdoc.words)):
            hits = our_index.get(h)
            if not hits:
                continue
            for o, p in hits:
                cov[o][p:p + GRAM] = block
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
        sdoc = corpus.docs[si]
        out.append(Run(length, corpus.name, o, p, sdoc.rel, j0,
                       (sdoc.lines[j0], sdoc.lines[j1 + GRAM - 1]), tuple(sdoc.words[j0:j1 + GRAM])))
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


# ---------------------------------------------------------------- report

def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def run_report(args) -> str:
    cache = Path(args.cache) if args.cache else RESULTS / ".similarity-embeddings.npz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    backend = make_backend(args.semantic, cache)
    threshold = args.threshold if args.threshold is not None else THRESHOLD[backend.kind]
    ours = load_ours()
    sources = [load_corpus(s) for s in SOURCES]
    real = [c for c in sources if c.docs]
    control_pool = load_corpus(Source("control", CONTROL_REPO, skill_roots=CONTROL_ROOTS,
                                      note="jezweb dev-tools, cloudflare, shopify, wordpress, frontend, integrations "
                                           "and design-assets skills"))
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
    return "\n".join(L)


def calibrate(args) -> None:
    """Write sentence pairs across the cosine range for a human to read (not used by the report)."""
    cache = Path(args.cache) if args.cache else RESULTS / ".similarity-embeddings.npz"
    backend = make_backend(args.semantic, cache)
    ours = load_ours()
    real = [c for c in (load_corpus(s) for s in SOURCES) if c.docs]
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
    p.add_argument("--semantic", choices=("auto", "embed", "tfidf"), default="auto")
    p.add_argument("--threshold", type=float, help="override the same-idea cosine threshold")
    p.add_argument("--cache", help="embedding cache file (default evals/results/.similarity-embeddings.npz)")
    p.add_argument("--calibrate", help="write calibration pairs to this file and stop")
    p.add_argument("--calibrate-range", type=float, nargs=2, default=(0.4, 0.9), metavar=("LO", "HI"))
    p.add_argument("--bins", type=int, default=10)
    p.add_argument("--per-bin", type=int, default=4)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    if args.calibrate:
        calibrate(args)
        return
    text = run_report(args)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
