"""Repository-wide structural contract for every skill under skills/.

Run: uv run --with pytest --with pyyaml python -m pytest tests/_meta -q
"""

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"
SKILL_DIRS = sorted(p for p in SKILLS.iterdir() if p.is_dir()) if SKILLS.is_dir() else []
IDS = [p.name for p in SKILL_DIRS]

ALLOWED_KEYS = {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
INTERNAL_ID_RE = re.compile(r"\bK-[A-Z]+-\d+\b|\bSLOP-[A-Z]+-\d+\b")
# Skills are written in our own words; source projects are thanked in README only.
# Owner handles and repository slugs only, matched as whole tokens, so ordinary words stay usable.
SOURCE_FINGERPRINTS = [
    "conorbronsdon", "avoid-ai-writing", "blader", "affaan", "everything-claude-code",
    "d-wwei", "great-writer", "greatwriter", "mattpocock", "wanshuiyin", "auto-claude-code",
    "k-dense", "garden-skills", "conardli", "resumeskills", "paramchoudhary", "proficientlyjobs",
    "jezweb", "leey21", "orchestra-research", "coreyhaines", "marketingskills", "no-ai-slop",
]
FINGERPRINT_RE = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, SOURCE_FINGERPRINTS)) + r")(?![\w-])")


def split_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    end = text.index("\n---\n", 4)
    return text[4:end], text[end + 5:]


def skill_files(skill: Path):
    return [p for p in skill.rglob("*") if p.is_file()]


@pytest.fixture(params=SKILL_DIRS, ids=IDS)
def skill(request):
    return request.param


def test_skills_exist():
    assert SKILL_DIRS, "skills/ must contain at least one skill"


def test_frontmatter_contract(skill):
    raw, _ = split_frontmatter(skill / "SKILL.md")
    assert "{" not in raw and "[" not in raw, "use block-style YAML, not flow style"
    meta = yaml.safe_load(raw)
    assert set(meta) <= ALLOWED_KEYS, f"unexpected keys: {set(meta) - ALLOWED_KEYS}"
    assert meta["name"] == skill.name and NAME_RE.match(meta["name"]) and len(meta["name"]) <= 64
    assert 1 <= len(meta["description"]) <= 1024
    assert "Use when" in meta["description"], "description must say when to use the skill"
    metadata = meta.get("metadata") or {}
    assert isinstance(metadata.get("version"), str), "metadata.version must be a quoted string"
    assert re.search(r'^\s+version:\s*"[0-9.]+"\s*$', raw, re.M), "quote metadata.version"
    assert all(isinstance(v, str) for v in metadata.values()), "metadata values must be strings"


def test_body_limits_and_sections(skill):
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 500, "keep SKILL.md under 500 lines"
    for heading in ("## When to use", "## Workflow"):
        assert heading in text, f"SKILL.md needs a '{heading}' section"


def test_eval_and_codex_metadata(skill):
    evals = (skill / "eval.md").read_text(encoding="utf-8")
    assert re.search(r"^1\. ", evals, re.M), "eval.md needs numbered pass/fail checks"
    ui = yaml.safe_load((skill / "agents" / "openai.yaml").read_text(encoding="utf-8"))["interface"]
    assert ui["display_name"] and ui["short_description"]
    assert f"${skill.name}" in ui["default_prompt"]


def test_local_links_resolve_inside_skill(skill):
    for f in skill_files(skill):
        if f.suffix != ".md":
            continue
        for target in LINK_RE.findall(f.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            resolved = (f.parent / path).resolve()
            assert resolved.is_relative_to(skill.resolve()), f"{f}: link leaves the skill: {target}"
            assert resolved.exists(), f"{f}: broken link {target}"


def test_ships_only_loadable_files(skill):
    for f in skill_files(skill):
        rel = f.relative_to(skill).as_posix()
        assert "__pycache__" not in rel and not rel.startswith("tests/") and f.suffix != ".pyc", rel
        assert "/Users/" not in f.read_text(encoding="utf-8", errors="ignore"), f"hardcoded local path in {rel}"
    if (skill / "scripts").is_dir():
        assert (REPO / "tests" / skill.name).is_dir(), "skills with scripts/ need tests/<name>/"


def test_own_words_without_source_fingerprints(skill):
    for f in skill_files(skill):
        if f.suffix not in {".md", ".yaml", ".py"}:
            continue
        text = f.read_text(encoding="utf-8")
        assert not INTERNAL_ID_RE.search(text), f"internal library ID in {f.relative_to(skill)}"
        hits = sorted(set(FINGERPRINT_RE.findall(text.lower())))
        assert not hits, f"source-repository name {hits} in {f.relative_to(skill)}"


def test_license_is_mit_except_diataxis_adaptation(skill):
    raw, _ = split_frontmatter(skill / "SKILL.md")
    expected = "CC-BY-SA-4.0" if skill.name == "technical-docs" else "MIT"
    assert yaml.safe_load(raw).get("license") == expected


def test_plugin_manifests_agree():
    versions = {}
    for rel in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
        data = json.loads((REPO / rel).read_text(encoding="utf-8"))
        assert data["name"] == "oh-my-writing"
        versions[rel] = data["version"]
    assert len(set(versions.values())) == 1, versions
    codex = json.loads((REPO / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert (REPO / codex["skills"]).resolve() == SKILLS.resolve()


# ---- benchmark isolation: a skill must not carry the benchmark's own material ----------------------------------

CASES = REPO / "evals" / "cases"
FIXTURES = REPO / "evals" / "fixtures"
CASE_TEXT_SUFFIXES = {".md", ".txt", ".csv", ".eml", ".html", ".json"}
# Capitalized words that occur in cases and are ordinary vocabulary in the skills, not names from a scenario.
ORDINARY_CAPITALIZED = {
    "Analyst", "ArgumentParser", "Classify", "Dual", "Ecology", "European", "Integrity", "LinkedIn", "Nightly",
    "Observational", "Retrieve", "Retry", "Validate",
    "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
    "December", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
}


def _case_texts() -> list[str]:
    texts = []
    for path in CASES.rglob("*.json"):
        case = json.loads(path.read_text(encoding="utf-8"))
        texts += [case["prompt"], *case.get("files", {}).values()]
    texts += [p.read_text(encoding="utf-8", errors="replace") for p in FIXTURES.rglob("*")
              if p.is_file() and p.suffix in CASE_TEXT_SUFFIXES]
    return texts


def _skill_texts(skill: Path) -> dict[str, str]:
    return {str(p.relative_to(REPO)): p.read_text(encoding="utf-8", errors="replace") for p in skill.rglob("*")
            if p.is_file() and p.suffix in {".md", ".yaml", ".py"}}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


@pytest.mark.parametrize("skill", SKILL_DIRS, ids=lambda p: p.name)
def test_skill_holds_no_benchmark_scenario(skill):
    """A name or a seven-word run from a benchmark case inside a skill lets the skill pass that case by recall, not by
    the behavior it teaches: examples in skills use invented scenarios."""
    case_texts = _case_texts()
    grams = set()
    for text in case_texts:
        w = _words(text)
        grams |= {tuple(w[i:i + 7]) for i in range(len(w) - 6)}
    names = set(re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)?\b", "\n".join(case_texts))) - ORDINARY_CAPITALIZED
    vocabulary = {w for s in SKILL_DIRS for text in _skill_texts(s).values() for w in _words(text)}
    found = []
    for rel, text in _skill_texts(skill).items():
        w = _words(text) if not rel.endswith(".py") else []  # script boilerplate is shared by any Python file
        found += [f"{rel}: '{' '.join(w[i:i + 7])}'" for i in range(len(w) - 6) if tuple(w[i:i + 7]) in grams]
        found += [f"{rel}: name {n}" for n in names
                  if len(n) >= 4 and n.lower() not in vocabulary and re.search(rf"\b{n}\b", text)]
    assert not found, "benchmark material inside the skill:\n" + "\n".join(sorted(set(found))[:20])


@pytest.mark.parametrize("skill", SKILL_DIRS, ids=lambda p: p.name)
def test_description_does_not_quote_a_benchmark_prompt(skill):
    """The description decides whether a skill loads. A five-word run from a case prompt inside it makes the skill
    load because it recalls the test, so routing results on that case measure nothing."""
    prompts = [json.loads(p.read_text(encoding="utf-8"))["prompt"] for p in CASES.rglob("*.json")]
    grams = {tuple(w[i:i + 5]) for text in prompts for w in [_words(text)] for i in range(len(w) - 4)}
    front = yaml.safe_load((skill / "SKILL.md").read_text(encoding="utf-8").split("---")[1])
    words = _words(front["description"])
    shared = {" ".join(words[i:i + 5]) for i in range(len(words) - 4) if tuple(words[i:i + 5]) in grams}
    assert not shared, f"description quotes case prompts: {sorted(shared)}"
