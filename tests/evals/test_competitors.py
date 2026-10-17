"""Tests for competitor conditions: installing third-party skills, case mapping, pairing and judging (no agent runs)."""

import argparse
import json
import shutil
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import grade  # noqa: E402
import run  # noqa: E402


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """A fake source cache with two competitors and a competitors.json pointing at it."""
    root = tmp_path / "cache"
    humanizer = root / "owner__humanizer"
    (humanizer / ".git").mkdir(parents=True)
    (humanizer / ".git" / "HEAD").write_text("x")
    (humanizer / "scripts").mkdir()
    (humanizer / "scripts" / "__pycache__").mkdir()
    (humanizer / "SKILL.md").write_text("---\nname: humanizer\n---\n")
    (humanizer / "LICENSE").write_text("MIT License\n")
    (humanizer / "scripts" / "x.py").write_text("print(1)\n")
    cover = root / "owner__cover"
    (cover / "skills" / "cover-letter").mkdir(parents=True)
    (cover / "skills" / "cover-letter" / "SKILL.md").write_text("---\nname: cover-letter\n---\n")
    (cover / "shared").mkdir()
    (cover / "shared" / "notes.md").write_text("shared\n")
    (root / "SHAS.txt").write_text("owner__humanizer abc123def456\nguides: not a pin\n")
    spec = {"cache": str(root), "competitors": {
        "humanizer": {"repo": "owner__humanizer", "license": "MIT", "license_file": "LICENSE",
                      "install": [{"from": ".", "to": "humanizer"}], "competes_on": ["anti-slop-editing"],
                      "style": True},
        "cover": {"repo": "owner__cover", "license": "MIT (README)", "license_file": None,
                  "install": [{"from": "skills/cover-letter", "to": "cover-letter"},
                              {"from": "shared", "to": "shared"}], "competes_on": ["career-documents"],
                  "style": False}}}
    path = tmp_path / "competitors.json"
    path.write_text(json.dumps(spec))
    monkeypatch.setattr(run, "COMPETITORS_FILE", path)
    skill = tmp_path / "skills" / "ours"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: ours\n---\n")
    monkeypatch.setattr(run, "SKILLS", [skill])
    return root


def case_of(skill="anti-slop-editing", cid="anti-slop-editing/x"):
    return {"id": cid, "skill": skill, "prompt": "Save to out/a.md.", "files": {"in.txt": "hello"},
            "output": "out/a.md", "checks": [{"type": "word_count", "min": 1}]}


def args(**kw):
    base = dict(repeat=1, resume=False, timeout=600, seed=7, judge="omp", codex_model=None, codex_effort=None,
                claude_model=None, judge_mode="auto")
    return argparse.Namespace(**{**base, **kw})


def test_shipped_competitors_map_to_real_skills_and_unique_folders():
    specs = run.load_competitors()
    ours = {p.name for p in run.SKILLS}
    assert specs
    for name, spec in specs.items():
        assert set(spec["competes_on"]) <= ours, name
        targets = [item["to"] for item in spec["install"]]
        assert len(targets) == len(set(targets)), name
        assert not set(targets) & ours, f"{name} would overwrite one of our skills"
        assert "/" not in name and ":" not in name


def test_competitor_workspace_has_only_their_skill_not_ours(cache):
    ws = run.make_workspace(case_of(), "omp", "competitor-humanizer")
    try:
        folder = ws / ".agents" / "skills"
        assert (folder / "humanizer" / "SKILL.md").is_file() and (folder / "humanizer" / "scripts" / "x.py").is_file()
        assert not (folder / "ours").exists()
        assert not (folder / "humanizer" / ".git").exists()
        assert not (folder / "humanizer" / "scripts" / "__pycache__").exists()
        assert not any(p.is_symlink() for p in ws.rglob("*"))
        (folder / "humanizer" / "SKILL.md").write_text("changed")
        assert "changed" not in (cache / "owner__humanizer" / "SKILL.md").read_text()  # a copy, no write-through
    finally:
        shutil.rmtree(ws)


def test_support_folders_are_installed_beside_the_skill(cache):
    ws = run.make_workspace(case_of("career-documents", "career-documents/x"), "claude", "competitor-cover")
    try:
        assert (ws / ".claude" / "skills" / "cover-letter" / "SKILL.md").is_file()
        assert (ws / ".claude" / "skills" / "shared" / "notes.md").is_file()
    finally:
        shutil.rmtree(ws)
    spec = run.load_competitors()["cover"]
    assert run.competitor_skill_names(spec) == ["cover-letter"]  # 'shared' holds no SKILL.md


def test_missing_cache_fails_clearly(cache, tmp_path, capsys):
    shutil.rmtree(cache / "owner__humanizer")
    problems = run.competitor_problems(run.load_competitors()["humanizer"])
    assert len(problems) == 1 and "owner__humanizer" in problems[0] and "missing" in problems[0]
    with pytest.raises(RuntimeError, match="missing"):
        run.make_workspace(case_of(), "omp", "competitor-humanizer")
    code = run.main(["--host", "omp", "--cases", "anti-slop-editing/clean-text-no-edit",
                     "--condition", "competitor:humanizer", "--out", str(tmp_path / "o")])
    assert code == 2 and "cannot be installed" in capsys.readouterr().err
    assert not (tmp_path / "o" / "run.json").exists()


def test_broken_install_entries_are_reported(cache):
    shutil.rmtree(cache / "owner__cover" / "skills" / "cover-letter")
    problems = run.competitor_problems(run.load_competitors()["cover"])
    assert any("skills/cover-letter" in p for p in problems)


def test_competitor_runs_only_on_mapped_cases_and_style(cache):
    spec = run.load_competitors()
    assert run.condition_applies("competitor-humanizer", case_of(), spec)
    assert not run.condition_applies("competitor-humanizer", case_of("post-writing", "post-writing/x"), spec)
    assert run.condition_applies("competitor-humanizer", case_of("post-writing", "style/x"), spec)  # style: true
    assert not run.condition_applies("competitor-cover", case_of("post-writing", "style/x"), spec)
    assert run.condition_applies("competitor-cover", case_of("career-documents", "style/cover"), spec)  # its own skill
    assert run.condition_applies("skill", case_of("post-writing", "post-writing/x"), spec)
    assert run.condition_applies("baseline", case_of("post-writing", "post-writing/x"), spec)


def test_resolve_conditions(cache):
    spec = run.load_competitors()
    assert run.resolve_conditions(None, False, spec) == (["skill", "baseline"], None)
    assert run.resolve_conditions(["competitor:humanizer"], False, spec) == (["competitor-humanizer"], None)
    both = run.resolve_conditions(["both", "competitor:cover"], True, spec)[0]
    assert both == ["skill", "baseline", "competitor-cover", "competitor-humanizer"]
    assert run.resolve_conditions(["skill"], True, spec)[0] == ["skill", "competitor-humanizer", "competitor-cover"]
    assert "unknown competitor" in run.resolve_conditions(["competitor:nope"], False, spec)[1]
    assert "must be" in run.resolve_conditions(["both-ish"], False, spec)[1]


def test_resolve_pairs(cache):
    spec = run.load_competitors()
    conds = ["skill", "baseline", "competitor-humanizer", "competitor-cover"]
    assert run.resolve_pairs(None, conds, spec) == ([("skill", "baseline")], None)
    assert run.resolve_pairs(None, ["competitor-humanizer"], spec) == ([], None)
    assert run.resolve_pairs(["skill:competitor"], conds, spec)[0] == [
        ("skill", "competitor-humanizer"), ("skill", "competitor-cover")]
    assert run.resolve_pairs(["skill:humanizer,baseline:competitor:cover"], conds, spec)[0] == [
        ("skill", "competitor-humanizer"), ("baseline", "competitor-cover")]
    assert run.resolve_pairs(["competitor:humanizer:skill"], conds, spec)[0] == [("competitor-humanizer", "skill")]
    # one rerun judges the baseline pair and every competitor pair; repeats and comma lists mix and never duplicate
    assert run.resolve_pairs(["skill:baseline,skill:competitor"], conds, spec) == (
        [("skill", "baseline"), ("skill", "competitor-humanizer"), ("skill", "competitor-cover")], None)
    assert run.resolve_pairs(["skill:baseline, skill:competitor", "skill:baseline"], conds, spec)[0] == [
        ("skill", "baseline"), ("skill", "competitor-humanizer"), ("skill", "competitor-cover")]
    assert run.resolve_pairs(["skill:baseline,skill:humanizer"], ["skill", "baseline"], spec)[0] == [
        ("skill", "baseline"), ("skill", "competitor-humanizer")]
    assert "A:B" in run.resolve_pairs(["skill:baseline,skill"], conds, spec)[1]
    # judging an existing run: the named competitor need not run now
    assert run.resolve_pairs(["skill:humanizer"], ["skill"], spec)[0] == [("skill", "competitor-humanizer")]
    assert "no competitor condition" in run.resolve_pairs(["skill:competitor"], ["skill", "baseline"], spec)[1]
    assert "unknown pair side" in run.resolve_pairs(["skill:ghost"], conds, spec)[1]
    assert "A:B" in run.resolve_pairs(["skill"], conds, spec)[1]


def test_competitor_loaded_by_folder_name_on_each_host(cache):
    c = case_of()
    assert run.condition_loaded("omp", "competitor-humanizer", c, "read skills/humanizer/SKILL.md")
    assert run.condition_loaded("omp", "competitor-humanizer", c, "skill://humanizer")
    assert run.condition_loaded("claude", "competitor-humanizer", c,
                                '{"name": "Skill", "input": {"skill": "humanizer"}}')
    assert not run.condition_loaded("omp", "competitor-humanizer", c, "skills/ours/SKILL.md skill://ours")
    assert not run.condition_loaded("omp", "baseline", c, "skill://humanizer")
    assert run.condition_loaded("omp", "skill", c, "skills/anti-slop-editing/SKILL.md")
    # a support folder is not a skill: only cover-letter counts for the cover competitor
    assert run.condition_loaded("omp", "competitor-cover", c, "skill://cover-letter")
    assert not run.condition_loaded("omp", "competitor-cover", c, "skill://shared")


def test_run_one_records_competitor_and_slug(cache, tmp_path, monkeypatch):
    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None):
        assert (ws / ".agents" / "skills" / "humanizer" / "SKILL.md").is_file()
        (ws / "out" / "a.md").write_text("done text")
        (out_dir / "reply.md").write_text("ok")
        return {"log": "opened skill://humanizer", "exit_code": 0, "error": None, "duration_s": 0.1}

    monkeypatch.setattr(run, "execute", execute)
    meta = run.run_one(case_of(), "omp", "competitor-humanizer", 2, tmp_path, args(repeat=3))
    assert meta["competitor"] == "humanizer" and meta["condition"] == "competitor-humanizer"
    assert meta["skill_loaded"] is True
    out = tmp_path / "runs" / "anti-slop-editing__x__omp__competitor-humanizer__r2"
    assert (out / "workspace" / "out" / "a.md").read_text() == "done text"
    assert not (out / "workspace" / ".agents").exists()


def test_run_record_has_commit_and_license(cache):
    spec = run.load_competitors()
    record = run.competitor_record(spec["humanizer"])
    assert record["commit"] == "abc123def456" and record["license"] == "MIT" and record["skills"] == ["humanizer"]
    assert run.competitor_record(spec["cover"])["commit"] is None  # not listed in SHAS.txt
    assert run.competitor_record(spec["cover"])["license_file"] is None


def make_pair_runs(case, run_dir, conds):
    for cond in conds:
        ws = run_dir / "runs" / run.slug_of(case, "omp", cond, 1, 1) / "workspace" / "out"
        ws.mkdir(parents=True)
        (ws / "a.md").write_text(f"{cond} text")


def test_judge_pair_between_skill_and_competitor(cache, tmp_path, monkeypatch):
    case = case_of()
    make_pair_runs(case, tmp_path, ["skill", "baseline", "competitor-humanizer"])
    calls = []

    def judge_once(case_, a, b, host, run_dir, tag, a_args, shots=None, shot_note=""):
        calls.append((tag, a, b))
        return ("A" if a.startswith("skill") else "B"), "reasons", {}

    monkeypatch.setattr(run, "judge_once", judge_once)
    entry = run.judge_pair(case, "omp", 1, tmp_path, args(), ("skill", "competitor-humanizer"))
    assert entry["winner"] == "skill" and entry["pair"] == "skill:competitor-humanizer"
    assert {c[1] for c in calls} | {c[2] for c in calls} == {"skill text", "competitor-humanizer text"}
    assert all("skill-vs-competitor-humanizer" in c[0] for c in calls)  # separate judge folder per pair
    default = run.judge_pair(case, "omp", 1, tmp_path, args())
    assert "pair" not in default and default["winner"] == "skill"
    # competitor wins when it is the side the judge prefers
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: ("A" if a[1].startswith("competitor") else "B", "r", {}))
    assert run.judge_pair(case, "omp", 1, tmp_path, args(),
                          ("skill", "competitor-humanizer"))["winner"] == "competitor-humanizer"
    # a side that never ran gives no verdict
    assert run.judge_pair(case, "omp", 1, tmp_path, args(), ("skill", "competitor-cover")) is None


def test_style_judge_between_skill_and_competitor(cache, tmp_path, monkeypatch):
    case = case_of()
    make_pair_runs(case, tmp_path, ["skill", "competitor-humanizer"])
    monkeypatch.setattr(run, "judge_once", lambda c, a, b, *r, **k: (
        "STYLE", "x", {"human": "A" if a.startswith("competitor") else "B", "faithful": "TIE"}))
    entry = run.judge_pair(case, "omp", 1, tmp_path, args(judge_mode="style"), ("skill", "competitor-humanizer"))
    assert entry["mode"] == "style" and entry["human"] == "competitor-humanizer" and entry["faithful"] == "tie"
    assert entry["pair"] == "skill:competitor-humanizer"


# ---------------------------------------------------------------- grading

def result(case, cond, passed, score=None, loaded=False, error=None, skill="anti-slop-editing", rep=1):
    return {"case": case, "skill": skill, "host": "omp", "condition": cond, "rep": rep, "skill_loaded": loaded,
            "exit_code": 0, "duration_s": 1, "error": error, "deliverables": {},
            "passed": passed, "score": (1.0 if passed else 0.5) if score is None else score,
            "checks": [{"type": "output_present", "passed": error is None, "detail": ""},
                       {"type": "word_count", "passed": passed, "detail": "n"}]}


def three_condition_runs():
    runs = []
    for case, (s, b, c) in {"a/1": (True, False, False), "a/2": (True, True, True), "a/3": (False, False, None),
                            "a/4": (True, True, None)}.items():
        runs.append(result(case, "skill", s, loaded=True))
        runs.append(result(case, "baseline", b))
        if c is not None:  # the competitor ran only two of the four cases
            runs.append(result(case, "competitor-humanizer", c, loaded=True))
    return runs


def test_competitor_does_not_unpair_skill_and_baseline():
    by = grade.summarize(three_condition_runs(), [])["by"]["omp/ALL"]
    assert by["skill_n"] == 4 and by["baseline_n"] == 4 and by["excluded"] == 0
    assert by["skill_pass"] == 0.75 and by["baseline_pass"] == 0.5


def test_competitor_is_paired_with_baseline_and_with_skill_separately():
    comp = grade.summarize(three_condition_runs(), [])["by"]["omp/ALL"]["competitors"]["humanizer"]
    vb, vs = comp["vs_baseline"], comp["vs_skill"]
    assert vb["n"] == 2 and vb["competitor_pass"] == 0.5 and vb["baseline_pass"] == 0.5 and vb["delta"] == 0
    assert vs["n"] == 2 and vs["skill_pass"] == 1.0 and vs["competitor_pass"] == 0.5 and vs["delta"] == 0.5
    assert vs["score_delta"] == pytest.approx(0.25) and comp["loaded"] == 1.0


def test_competitor_host_failure_drops_only_its_own_pairs():
    runs = three_condition_runs()
    runs[2] = result("a/1", "competitor-humanizer", False, error="timeout", loaded=False)
    runs[2]["checks"][0]["passed"] = False  # no output: a host error
    by = grade.summarize(runs, [])["by"]["omp/ALL"]
    assert by["skill_n"] == 4 and by["excluded"] == 0
    assert by["competitors"]["humanizer"]["vs_baseline"]["n"] == 1


def test_skill_baseline_numbers_unchanged_without_competitors():
    runs = [r for r in three_condition_runs() if r["condition"] != "competitor-humanizer"]
    by = grade.summarize(runs, [])["by"]["omp/ALL"]
    assert "competitors" not in by and by["skill_n"] == 4


def test_unpaired_skill_baseline_still_excluded():
    runs = [r for r in three_condition_runs() if not (r["case"] == "a/4" and r["condition"] == "baseline")]
    by = grade.summarize(runs, [])["by"]["omp/ALL"]
    assert by["skill_n"] == 3 and by["baseline_n"] == 3 and by["excluded"] == 1


def test_judge_pairs_are_tallied_apart_from_skill_vs_baseline():
    judge = [
        {"case": "a/1", "host": "omp", "rep": 1, "judge": "omp", "winner": "skill"},
        {"case": "a/1", "host": "omp", "rep": 1, "judge": "omp", "pair": "skill:competitor-humanizer",
         "winner": "competitor-humanizer"},
        {"case": "a/2", "host": "omp", "rep": 1, "judge": "omp", "pair": "skill:competitor-humanizer",
         "winner": "tie"},
        {"case": "a/2", "host": "omp", "rep": 1, "judge": "omp", "pair": "skill:competitor-humanizer",
         "mode": "style", "winner": "style", "human": "skill", "faithful": "tie"},
    ]
    summary = grade.summarize([], judge)
    assert summary["judge"]["skill"] == 1 and summary["judge"]["baseline"] == 0
    info = summary["judge_pairs"]["skill:competitor-humanizer"]
    assert info["verdicts"]["competitor-humanizer"] == 1 and info["verdicts"]["tie"] == 1
    assert info["style"]["human"]["skill"] == 1 and info["style"]["faithful"]["tie"] == 1
    report = grade.render_report({"run": {}, "runs": [], "judge": judge, "summary": summary})
    assert "## Blind judge: skill vs competitor-humanizer" in report
    assert report.count("## Blind pairwise judge") == 1  # the default section stays skill vs baseline only


def test_report_shows_competitor_table_cases_column_and_provenance():
    runs = three_condition_runs()
    results = {"run": {"id": "r", "started": "now", "hosts": ["omp"], "cases": 4, "competitors": {
        "humanizer": {"repo": "owner__humanizer", "commit": "abc123def456789", "license": "MIT"}}},
        "runs": runs, "judge": [], "summary": grade.summarize(runs, [])}
    report = grade.render_report(results)
    assert "owner__humanizer @ abc123def4, MIT" in report
    assert "## Competitors" in report and "ours minus competitor" in report
    assert "| competitor-humanizer |" in report  # extra column in the case table
    case_row = next(l for l in report.splitlines() if l.startswith("| a/3 |"))
    assert case_row.rstrip().endswith("| - |")  # competitor did not run this case
    plain = grade.render_report({"run": {}, "runs": runs[:2], "judge": [], "summary": grade.summarize(runs[:2], [])})
    assert "## Competitors" not in plain
