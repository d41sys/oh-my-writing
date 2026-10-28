"""Tests for the placebo condition (variant-placebo: our skills' names, descriptions and layout with generic bodies of
about the same word count, in whole sentences) and for --prereg (pre-registration copied into the results directory);
no agent runs."""

import json
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import run  # noqa: E402
from test_stats import GOOD  # noqa: E402
from test_variants import CASE_ID, args, case_of  # noqa: E402

GENERIC = ("Write for one reader. Say the main point early. Keep sentences short. Cut what does no work. "
           "Read the draft aloud. Revise after a break.")
FRONT = ('---\nname: demo\ndescription: Does the demo thing. Use when asked about "demos".\nlicense: MIT\n'
         'metadata:\n  version: "1.2"\n---\n')


@pytest.fixture
def skills(tmp_path):
    """Two skills with frontmatter, a reference, an eval.md, a script, an asset and a yaml file."""
    root = tmp_path / "src"
    for name, ref_words in (("demo", 40), ("other", 7)):
        folder = root / name
        (folder / "references").mkdir(parents=True)
        (folder / "scripts").mkdir()
        (folder / "assets").mkdir()
        (folder / "agents").mkdir()
        (folder / "SKILL.md").write_text(FRONT.replace("demo", name) + "\n# Title\n\nSECRETMETHOD " + "word " * 30 + "\n")
        (folder / "references" / "r.md").write_text("# Ref\n\n- " + " ".join(f"SECRETMETHOD{i}" for i in range(ref_words)) + "\n")
        (folder / "eval.md").write_text("one two three\n")
        (folder / "scripts" / "tool.py").write_text("print('x')\n")
        (folder / "assets" / "t.md").write_text("template text here\n")
        (folder / "assets" / "logo.png").write_bytes(b"\x89PNG")
        (folder / "agents" / "openai.yaml").write_text("interface: {}\n")
    source = tmp_path / "generic.md"
    source.write_text(GENERIC + "\n")
    return {"root": root, "paths": [root / "demo", root / "other"], "source": source, "cache": tmp_path / "cache"}


def words_of(path):
    return len(run.split_frontmatter(path.read_text())[1].split())


GENERIC_SENTENCES = {s.strip() + "." for s in GENERIC.split(".") if s.strip()}
HALF_SENTENCE = max(len(s.split()) for s in GENERIC_SENTENCES) / 2


def sentences_of(body):
    return [s.strip() + "." for s in " ".join(body.split()).split(".") if s.strip()]


def build(skills, **kw):
    return run.export_placebo(skills["paths"], skills["cache"], skills["source"], **kw)


# ---------------------------------------------------------------- generation

def test_placebo_keeps_frontmatter_and_word_counts_and_drops_other_files(skills):
    v = build(skills)
    assert v["name"] == "placebo" and v["ref"] == "placebo" and v["placebo"] is True
    assert v["root"] == skills["cache"] / v["sha"] / "skills" and v["skills"] == ["demo", "other"]
    assert v["versions"] == {"demo": "1.2", "other": "1.2"}
    for src in skills["paths"]:
        dest = v["root"] / src.name
        real_md = sorted(p.relative_to(src) for p in src.rglob("*.md"))
        assert sorted(p.relative_to(dest) for p in dest.rglob("*") if p.is_file()) == real_md  # layout of Markdown files
        for rel in real_md:
            assert abs(words_of(dest / rel) - words_of(src / rel)) <= HALF_SENTENCE, rel
            assert "SECRETMETHOD" not in (dest / rel).read_text()
        real_front = run.split_frontmatter((src / "SKILL.md").read_text())[0]
        assert (dest / "SKILL.md").read_text().startswith(real_front)  # frontmatter byte for byte
        assert not (dest / "scripts").exists() and not (dest / "agents").exists()
        assert not (dest / "assets" / "logo.png").exists()


def test_placebo_bodies_are_generic_valid_markdown_that_wrap_around(skills):
    v = build(skills)
    body = run.split_frontmatter((v["root"] / "demo" / "references" / "r.md").read_text())[1]
    assert abs(len(body.split()) - words_of(skills["paths"][0] / "references" / "r.md")) <= HALF_SENTENCE
    assert not body.startswith("#") and "- " not in body  # no heading or bullet markers carried over
    assert set(sentences_of(body)) <= GENERIC_SENTENCES  # whole source sentences only, never a cut one
    assert body.endswith(".\n")
    assert all(par.strip() for par in body.strip().split("\n\n"))  # paragraphs, no empty ones
    assert len(body.split()) > len(GENERIC.split())  # the 20-word source was reused more than once


def test_placebo_paragraphs_break_only_at_sentence_ends(skills):
    (skills["paths"][0] / "references" / "r.md").write_text("# Ref\n\n" + "word " * 400 + "\n")
    body = run.split_frontmatter((build(skills)["root"] / "demo" / "references" / "r.md").read_text())[1]
    paragraphs = body.strip().split("\n\n")
    assert len(paragraphs) > 1 and all(p.endswith(".") for p in paragraphs)


def test_placebo_identity_is_deterministic_and_tracks_its_inputs(skills):
    a, b = build(skills), build(skills)
    assert a["sha"] == b["sha"] and len(a["sha"]) == 64
    assert run.placebo_identity(skills["paths"], skills["source"]) == a["sha"]
    before = a["sha"]
    skills["source"].write_text(GENERIC + " Another sentence appears here.\n")
    assert build(skills)["sha"] != before  # other generic text
    skills["source"].write_text(GENERIC + "\n")
    assert build(skills)["sha"] == before
    skill_md = skills["paths"][0] / "SKILL.md"
    skill_md.write_text(skill_md.read_text().replace("Does the demo thing", "Does another thing"))
    described = build(skills)["sha"]
    assert described != before  # description changed
    (skills["paths"][0] / "references" / "r.md").write_text("# Ref\n\nshort\n")
    assert build(skills)["sha"] != described  # word count changed


def test_placebo_is_built_once_per_identity(skills):
    v = build(skills)
    marker = v["root"] / "demo" / "SKILL.md"
    marker.write_text(marker.read_text() + "\nedited in cache\n")
    assert "edited in cache" in (build(skills)["root"] / "demo" / "SKILL.md").read_text()  # reused, not rebuilt


def test_generic_advice_is_long_enough_and_free_of_our_methods():
    text = run.PLACEBO_SOURCE.read_text(encoding="utf-8")
    assert len(text.split()) >= 2500
    lowered = text.lower()
    for term in ("ledger", "gap marker", "[ask author", "[verify", "[untested", "diátaxis", "diataxis", "voice profile",
                 "claim strength", "slop", "pattern catalog", "preservation check", "reverse outline"):
        assert term not in lowered, term


def test_placebo_of_the_real_skills_matches_every_markdown_file(tmp_path):
    v = run.export_placebo(cache=tmp_path)
    assert v["skills"] == [s.name for s in run.SKILLS] and all(v["versions"].values())
    words, longest, n = run.placebo_words(), 0, 0
    for w in words:  # longest sentence of the generic text bounds how far a body can be off
        n += 1
        if w.endswith((".", "?", "!")):
            longest, n = max(longest, n), 0
    for skill in run.SKILLS:
        for real, rel in run.placebo_files([skill]):
            fake = v["root"] / skill.name / rel
            assert fake.is_file() and abs(words_of(fake) - words_of(real)) <= longest / 2, (skill.name, rel)
        assert not (v["root"] / skill.name / "scripts").exists()


def test_missing_generic_text_is_a_clear_error(skills, tmp_path):
    with pytest.raises(ValueError, match="not found"):
        run.export_placebo(skills["paths"], skills["cache"], tmp_path / "nope.md")


# ---------------------------------------------------------------- conditions

def test_placebo_name_is_reserved_and_the_condition_is_a_variant():
    assert run.parse_variants(["placebo=HEAD"])[1] == "--variant placebo: that name is reserved for --placebo"
    conditions, err = run.resolve_conditions(None, False, {}, {"placebo": "placebo"})
    assert err is None and conditions == ["skill", "baseline", "variant-placebo"]
    pairs, err = run.resolve_pairs(["skill:variant-placebo"], conditions, {}, {"placebo": "placebo"})
    assert err is None and pairs == [("skill", "variant-placebo")]
    assert run.variant_record({"ref": "placebo", "sha": "ab", "versions": {"x": "1"}, "placebo": True}) == {
        "ref": "placebo", "sha": "ab", "skills": {"x": "1"}, "placebo": True}


def test_placebo_workspace_holds_the_placebo_skills_and_may_load_our_skill_names(skills, tmp_path, monkeypatch):
    v = build(skills)
    monkeypatch.setattr(run, "VARIANTS", {"placebo": v})
    monkeypatch.setattr(run, "SKILLS", skills["paths"])
    case = {**case_of("demo"), "files": {"in.txt": "hello"}}
    ws = run.make_workspace(case, "omp", "variant-placebo")
    installed = ws / run.SKILL_FOLDER["omp"]
    assert sorted(p.name for p in installed.iterdir()) == ["demo", "other"]
    assert not (installed / "demo" / "scripts").exists()
    assert "SECRETMETHOD" not in (installed / "demo" / "SKILL.md").read_text()
    assert run.condition_loaded("omp", "variant-placebo", case, "opened skills/demo/SKILL.md")
    assert {"demo", "other"} <= run.allowed_skills("variant-placebo", case)


# ---------------------------------------------------------------- main: --placebo and --prereg

@pytest.fixture
def harness(tmp_path, monkeypatch):
    """main() with a fake host: every run writes GOOD; `seen` records what each run saw."""
    source = tmp_path / "generic.md"
    source.write_text(GENERIC + "\n")
    monkeypatch.setattr(run, "PLACEBO_CACHE", tmp_path / "placebo-cache")
    monkeypatch.setattr(run, "PLACEBO_SOURCE", source)
    monkeypatch.setattr(run, "USER_SKILL_DIRS", [])
    monkeypatch.setattr(run, "VARIANTS", {})
    monkeypatch.setattr(run.grade, "validate_real_case", lambda case: [])  # controls are not what these tests are about
    monkeypatch.setattr(run.shutil, "which", lambda name: "/bin/" + name)
    monkeypatch.setattr(run, "cli_version", lambda cmd: "test")
    monkeypatch.setattr(run, "diagram_design_version", lambda: None)
    seen = []

    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None):
        info = (out_dir.parents[1] / "run.json")
        seen.append({"run": out_dir.name, "run_json": json.loads(info.read_text()) if info.is_file() else None,
                     "prereg": (out_dir.parents[1] / "prereg.md").is_file(),
                     "skill": next((f.read_text() for f in sorted((ws / ".agents" / "skills").glob("*/SKILL.md"))), None)})
        (ws / "out").mkdir(exist_ok=True)
        (ws / "out" / "email.md").write_text(GOOD)
        (out_dir / "reply.md").write_text("ok")
        return {"log": "skills/structured-drafting/SKILL.md", "exit_code": 0, "error": None, "duration_s": 0.1}

    monkeypatch.setattr(run, "execute", execute)
    return {"seen": seen, "tmp": tmp_path}


def test_main_placebo_runs_variant_placebo_beside_skill_and_baseline(harness, tmp_path, capsys):
    out = tmp_path / "p"
    assert run.main(["--host", "omp", "--cases", CASE_ID, "--placebo", "--out", str(out)]) == 0
    stem = CASE_ID.replace("/", "__")
    assert sorted(s["run"] for s in harness["seen"]) == sorted(
        f"{stem}__omp__{c}" for c in ("skill", "baseline", "variant-placebo"))
    info = json.loads((out / "run.json").read_text())
    assert info["conditions"] == ["skill", "baseline", "variant-placebo"]
    rec = info["variants"]["placebo"]
    assert rec["ref"] == "placebo" and rec["placebo"] is True and len(rec["sha"]) == 64
    meta = json.loads((out / "runs" / f"{stem}__omp__variant-placebo" / "meta.json").read_text())
    assert meta["variant"] == "placebo" and meta["variant_sha"] == rec["sha"]
    seen = next(s for s in harness["seen"] if s["run"].endswith("variant-placebo"))
    front, body = run.split_frontmatter(seen["skill"])
    assert front.startswith("---\nname: ") and {w.rstrip(".") for w in body.split()} <= {w.rstrip(".") for w in GENERIC.split()}
    assert (run.PLACEBO_CACHE / rec["sha"] / "skills").is_dir()
    assert "A/B skill vs variant-placebo" in capsys.readouterr().out
    assert "## A/B: skill vs variant-placebo" in (out / "report.md").read_text()


def test_prereg_is_recorded_before_any_run_and_heads_the_report(harness, tmp_path):
    prereg = tmp_path / "plan.md"
    prereg.write_text("# Plan\n\nShip only if skill beats placebo by 10 points.\n")
    out = tmp_path / "r"
    assert run.main(["--host", "omp", "--cases", CASE_ID, "--prereg", str(prereg), "--out", str(out)]) == 0
    assert all(s["prereg"] and s["run_json"]["prereg"]["sha256"] for s in harness["seen"])  # on disk before the runs
    rec = json.loads((out / "run.json").read_text())["prereg"]
    assert rec["sha256"] == run.sha256_of(prereg) and rec["registered"].endswith("+00:00")
    assert (out / "prereg.md").read_text() == prereg.read_text()
    report = (out / "report.md").read_text()
    assert report.startswith("<!-- pre-registered text") and rec["sha256"] in report.splitlines()[0]
    assert report.splitlines()[1] == "# Plan" and "Ship only if skill beats placebo" in report
    assert "\n---\n\n" in report
    run.grade.grade_run(out)  # grading again on its own keeps the header
    assert (out / "report.md").read_text() == report


def test_prereg_on_resume_same_file_keeps_time_and_different_file_is_refused(harness, tmp_path, capsys):
    prereg, other = tmp_path / "plan.md", tmp_path / "other.md"
    prereg.write_text("plan one\n")
    other.write_text("plan two\n")
    out = tmp_path / "r"
    base = ["--host", "omp", "--cases", CASE_ID, "--out", str(out)]
    assert run.main([*base, "--prereg", str(prereg)]) == 0
    first = json.loads((out / "run.json").read_text())["prereg"]
    harness["seen"].clear()
    assert run.main([*base, "--prereg", str(prereg), "--resume"]) == 0
    assert json.loads((out / "run.json").read_text())["prereg"] == first  # registration time is not renewed
    assert run.main([*base, "--resume"]) == 0  # resuming without the option keeps the registration
    assert json.loads((out / "run.json").read_text())["prereg"] == first
    assert (out / "report.md").read_text().startswith(run.grade.PREREG_MARK)
    capsys.readouterr()
    assert run.main([*base, "--prereg", str(other), "--resume"]) == 2
    assert "cannot change on --resume" in capsys.readouterr().err
    assert (out / "prereg.md").read_text() == "plan one\n"
    assert json.loads((out / "run.json").read_text())["prereg"] == first
    assert not harness["seen"]  # nothing ran


def test_prereg_cannot_be_added_after_runs_exist_and_a_missing_file_is_an_error(harness, tmp_path, capsys):
    prereg = tmp_path / "plan.md"
    prereg.write_text("late plan\n")
    out = tmp_path / "r"
    base = ["--host", "omp", "--cases", CASE_ID, "--out", str(out)]
    assert run.main(base) == 0
    assert "prereg" not in json.loads((out / "run.json").read_text())
    assert not (out / "report.md").read_text().startswith(run.grade.PREREG_MARK)
    capsys.readouterr()
    assert run.main([*base, "--prereg", str(prereg), "--resume"]) == 2
    assert "not be before any run" in capsys.readouterr().err
    assert not (out / "prereg.md").exists()
    assert run.main([*base, "--prereg", str(tmp_path / "missing.md")]) == 2
    assert "is not a file" in capsys.readouterr().err
