"""Tests for A/B variants: our skills exported from a git ref as the condition variant-NAME, adopting finished runs as a
variant, pairing in grade.py and the same-run gate (no agent runs)."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import gate  # noqa: E402
import grade  # noqa: E402
import run  # noqa: E402
from test_stats import GOOD, make_run  # noqa: E402

CASE_ID = "structured-drafting/tiny-email-no-scaffolding"


def git(repo, *cmd):
    out = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *cmd],
                         cwd=repo, check=True, capture_output=True, text=True)
    return out.stdout.strip()


def write_skill(root, name, version, body="text"):
    folder = root / "skills" / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(f"---\nname: {name}\nmetadata:\n  version: \"{version}\"\n---\n{body}\n")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A git repository with two commits of skills/ (old, new); the working tree is ahead of both."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    write_skill(root, "structured-drafting", "1.0", "old body")
    (root / "skills" / "structured-drafting" / "extra.md").write_text("only in old\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "old")
    old = git(root, "rev-parse", "HEAD")
    write_skill(root, "structured-drafting", "1.1", "new body")
    write_skill(root, "second", "2.0")
    (root / "skills" / "structured-drafting" / "extra.md").unlink()
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "new")
    new = git(root, "rev-parse", "HEAD")
    write_skill(root, "structured-drafting", "9.9", "uncommitted body")  # must never reach a variant
    monkeypatch.setattr(run, "REPO", root)
    monkeypatch.setattr(run, "VARIANT_CACHE", tmp_path / "cache")
    monkeypatch.setattr(run, "USER_SKILL_DIRS", [])
    monkeypatch.setattr(run, "SKILLS", [root / "skills" / "structured-drafting", root / "skills" / "second"])
    monkeypatch.setattr(run, "VARIANTS", {})
    return {"root": root, "old": old, "new": new}


def case_of(skill="structured-drafting", cid=CASE_ID):
    return {"id": cid, "skill": skill, "prompt": "Save to out/a.md.", "files": {"in.txt": "hello"},
            "output": "out/a.md", "checks": [{"type": "word_count", "min": 1}]}


def args(**kw):
    base = dict(repeat=1, resume=False, timeout=600, seed=7, judge="omp", codex_model=None, codex_effort=None,
                claude_model=None, judge_mode="auto")
    return argparse.Namespace(**{**base, **kw})


# ---------------------------------------------------------------- export

def test_export_variant_holds_the_skills_of_the_ref_only(repo, tmp_path):
    v = run.export_variant("pre", repo["old"][:8])
    assert v["sha"] == repo["old"] and v["ref"] == repo["old"][:8]  # the full sha is recorded, the ref as given
    assert v["root"] == tmp_path / "cache" / repo["old"] / "skills"
    assert v["skills"] == ["structured-drafting"] and v["versions"] == {"structured-drafting": "1.0"}
    assert "old body" in (v["root"] / "structured-drafting" / "SKILL.md").read_text()
    assert (v["root"] / "structured-drafting" / "extra.md").is_file()  # a file the newer commit deleted
    assert not list((tmp_path / "cache").glob(".*"))  # no half-written temp folder left behind
    new = run.export_variant("cur", "HEAD")
    assert new["sha"] == repo["new"] and new["versions"] == {"structured-drafting": "1.1", "second": "2.0"}
    assert "new body" in (new["root"] / "structured-drafting" / "SKILL.md").read_text()  # not the uncommitted working tree


def test_export_is_cached_per_full_sha(repo):
    first = run.export_variant("a", repo["old"])
    marker = first["root"] / "structured-drafting" / "marker.txt"
    marker.write_text("kept")
    again = run.export_variant("b", repo["old"][:10])  # another name, another spelling of the same commit
    assert again["root"] == first["root"] and marker.read_text() == "kept"  # reused, not exported again


def test_export_rejects_unknown_ref_and_ref_without_skills(repo):
    with pytest.raises(ValueError, match="not a commit"):
        run.export_variant("x", "no-such-ref")
    git(repo["root"], "checkout", "-q", "--orphan", "bare")
    git(repo["root"], "rm", "-rfq", ".")
    (repo["root"] / "README").write_text("x")
    git(repo["root"], "add", "README")
    git(repo["root"], "commit", "-q", "-m", "no skills")
    with pytest.raises(ValueError, match="no skills/ folder"):
        run.export_variant("x", "HEAD")


def test_parse_variants():
    assert run.parse_variants(["pre=21cd881", "iso=f0a07bf"]) == ({"pre": "21cd881", "iso": "f0a07bf"}, None)
    assert run.parse_variants(None) == ({}, None)
    for bad in ("pre", "pre=", "=abc", "a b=abc", "bad__x=abc", "-x=abc"):
        assert run.parse_variants([bad])[1], bad
    assert "twice" in run.parse_variants(["a=x", "a=y"])[1]


# ---------------------------------------------------------------- conditions and workspace

def test_condition_names_and_slug():
    assert run.variant_condition("pre") == "variant-pre" and run.variant_name("variant-pre") == "pre"
    assert run.variant_name("skill") is None and run.variant_name("competitor-x") is None
    assert run.competitor_name("variant-pre") is None
    assert run.slug_of(case_of(), "omp", "variant-pre", 2, 3) == f"{CASE_ID.replace('/', '__')}__omp__variant-pre__r2"
    assert run.slug_of(case_of(), "omp", "variant-pre", 1, 1).endswith("__omp__variant-pre")


def test_variant_runs_on_every_case():
    assert run.condition_applies("variant-pre", case_of("post-writing", "post-writing/x"), {})
    assert run.condition_applies("variant-pre", case_of("career-documents", "style/x"), {})


def test_variant_workspace_has_the_exported_skills_not_the_working_tree(repo):
    run.VARIANTS["pre"] = run.export_variant("pre", repo["old"])
    ws = run.make_workspace(case_of(), "omp", "variant-pre")
    skill = ws / ".agents" / "skills" / "structured-drafting"
    assert "old body" in (skill / "SKILL.md").read_text() and (skill / "extra.md").is_file()
    assert sorted(p.name for p in (ws / ".agents" / "skills").iterdir()) == ["structured-drafting"]  # 'second' did not exist then
    assert not skill.is_symlink()
    claude = run.make_workspace(case_of(), "claude", "variant-pre")
    assert (claude / ".claude" / "skills" / "structured-drafting" / "SKILL.md").is_file()
    plain = run.make_workspace(case_of(), "omp", "skill")  # the plain skill condition still copies the current skills
    assert sorted(p.name for p in (plain / ".agents" / "skills").iterdir()) == ["second", "structured-drafting"]
    assert "uncommitted body" in (plain / ".agents" / "skills" / "structured-drafting" / "SKILL.md").read_text()


def test_undeclared_variant_fails_clearly(repo):
    with pytest.raises(RuntimeError, match="not declared"):
        run.make_workspace(case_of(), "omp", "variant-ghost")


def test_variant_loaded_like_skill_and_isolation_allows_our_skill_names(repo):
    run.VARIANTS["pre"] = run.export_variant("pre", repo["old"])
    c = case_of("structured-drafting")
    assert run.condition_loaded("omp", "variant-pre", c, "skill://structured-drafting")
    assert run.condition_loaded("claude", "variant-pre", c, "read skills/structured-drafting/SKILL.md")
    assert not run.condition_loaded("omp", "variant-pre", c, "skill://second")  # only the case's own skill counts
    assert not run.isolation_problems("omp", "variant-pre", c, "skill://structured-drafting skill://second skill://" + run.grade.DIAGRAM_SKILL.name)
    assert "skills outside the condition: stranger" in run.isolation_problems("omp", "variant-pre", c, "skill://stranger")[0]
    assert "skills outside" in run.isolation_problems("omp", "baseline", c, "skill://structured-drafting")[0]


def test_resolve_conditions_with_variants():
    v = {"pre": "21cd881", "iso": "f0a07bf"}
    assert run.resolve_conditions(None, False, {}, v) == (["skill", "baseline", "variant-pre", "variant-iso"], None)
    assert run.resolve_conditions(["skill"], False, {}, v)[0] == ["skill", "variant-pre", "variant-iso"]
    assert run.resolve_conditions(["variant:pre"], False, {}, {"pre": "x"}) == (["variant-pre"], None)  # only the variant
    assert "unknown variant" in run.resolve_conditions(["variant:nope"], False, {}, v)[1]
    assert run.resolve_conditions(None, False, {}) == (["skill", "baseline"], None)  # nothing declared: as before


def test_resolve_pairs_with_variants():
    v = {"pre": "x", "iso": "y"}
    conds = ["skill", "baseline", "variant-pre", "variant-iso"]
    assert run.resolve_pairs(["skill:variant-pre"], conds, {}, v) == ([("skill", "variant-pre")], None)
    assert run.resolve_pairs(["skill:variant:pre"], conds, {}, v)[0] == [("skill", "variant-pre")]
    assert run.resolve_pairs(["skill:baseline,skill:variant-iso,skill:variant-pre"], conds, {}, v)[0] == [
        ("skill", "baseline"), ("skill", "variant-iso"), ("skill", "variant-pre")]
    assert run.resolve_pairs(["skill:variant"], conds, {}, v)[0] == [("skill", "variant-pre"), ("skill", "variant-iso")]
    assert run.resolve_pairs(["variant-pre:skill"], conds, {}, v)[0] == [("variant-pre", "skill")]
    assert "unknown pair side" in run.resolve_pairs(["skill:variant-zzz"], conds, {}, v)[1]
    assert "no variant condition" in run.resolve_pairs(["skill:variant"], ["skill"], {}, {})[1]


def test_run_one_records_variant_and_resume_checks_the_commit(repo, tmp_path, monkeypatch):
    run.VARIANTS["pre"] = run.export_variant("pre", repo["old"])
    calls = []

    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None):
        calls.append((ws / ".agents" / "skills" / "structured-drafting" / "SKILL.md").read_text())
        (ws / "out" / "a.md").write_text("done text")
        (out_dir / "reply.md").write_text("ok")
        return {"log": "opened skill://structured-drafting", "exit_code": 0, "error": None, "duration_s": 0.1}

    monkeypatch.setattr(run, "execute", execute)
    c = case_of("structured-drafting")
    meta = run.run_one(c, "omp", "variant-pre", 2, tmp_path, args(repeat=3))
    assert meta["condition"] == "variant-pre" and meta["variant"] == "pre" and meta["variant_sha"] == repo["old"]
    assert meta["skill_loaded"] is True and meta["error"] is None  # no isolation error
    out = tmp_path / "runs" / (run.slug_of(c, "omp", "variant-pre", 2, 3))
    assert (out / "workspace" / "out" / "a.md").read_text() == "done text" and not (out / "workspace" / ".agents").exists()
    run.run_one(c, "omp", "variant-pre", 2, tmp_path, args(repeat=3, resume=True))
    assert len(calls) == 1 and "old body" in calls[0]  # finished run of the same commit is reused
    run.VARIANTS["pre"] = run.export_variant("pre", repo["new"])  # the name now means another commit
    run.run_one(c, "omp", "variant-pre", 2, tmp_path, args(repeat=3, resume=True))
    assert len(calls) == 2 and "new body" in calls[1]


def test_run_json_record_has_ref_sha_and_versions(repo):
    v = run.export_variant("pre", repo["old"][:7])
    assert run.variant_record(v) == {"ref": repo["old"][:7], "sha": repo["old"], "skills": {"structured-drafting": "1.0"}}


# ---------------------------------------------------------------- adopting finished runs

def fake_run(run_dir, repeat=3):
    """Finished skill + baseline + competitor runs of one case with their judge verdicts and folders."""
    cid = "post-writing/a"
    stem = cid.replace("/", "__")
    for cond in ("skill", "baseline", "competitor-humanizer"):
        for rep in range(1, repeat + 1):
            d = run_dir / "runs" / f"{stem}__omp__{cond}__r{rep}"
            (d / "workspace").mkdir(parents=True)
            (d / "meta.json").write_text(json.dumps({"case": cid, "skill": "post-writing", "host": "omp", "condition": cond,
                                                     "rep": rep, "skill_loaded": cond == "skill", "error": None}))
    judge = []
    for rep in range(1, repeat + 1):
        judge.append({"case": cid, "host": "omp", "rep": rep, "judge": "omp", "winner": "skill", "picks": ["skill", "skill"]})
        judge.append({"case": cid, "host": "omp", "rep": rep, "judge": "omp", "pair": "skill:competitor-humanizer",
                      "winner": "competitor-humanizer", "picks": ["competitor-humanizer", "tie"]})
        judge.append({"case": cid, "host": "omp", "rep": rep, "judge": "omp", "pair": "skill:competitor-humanizer",
                      "mode": "style", "winner": "style", "human": "skill", "faithful": "tie",
                      "picks": {"human": ["skill", "skill"], "faithful": ["tie", "skill"]}})
        judge.append({"case": cid, "host": "omp", "rep": rep, "judge": "omp", "pair": "baseline:competitor-humanizer",
                      "winner": "baseline"})
        for tail in (f"omp__r{rep}__order1", f"omp__r{rep}__order2", f"omp__r{rep}__shots",
                     f"omp__r{rep}__skill-vs-competitor-humanizer__order1", f"omp__r{rep}__baseline-vs-competitor-humanizer__order1"):
            (run_dir / "judge" / f"{stem}__{tail}").mkdir(parents=True)
    (run_dir / "judge" / f"{stem}__omp__r1__shots" / "skill-1.png").write_text("png")
    (run_dir / "judge" / f"{stem}__omp__r1__shots" / "baseline-1.png").write_text("png")
    (run_dir / "judge.json").write_text(json.dumps(judge))
    return stem


def test_adopt_runs_relabels_runs_meta_and_judge(repo, tmp_path):
    stem = fake_run(tmp_path)
    variant = run.export_variant("iso", repo["old"])
    assert run.adopt_runs(tmp_path, "skill", "variant-iso", variant) == 3
    runs = sorted(p.name for p in (tmp_path / "runs").iterdir())
    assert runs == sorted(f"{stem}__omp__{c}__r{k}" for c in ("baseline", "competitor-humanizer", "variant-iso")
                          for k in (1, 2, 3))
    meta = json.loads((tmp_path / "runs" / f"{stem}__omp__variant-iso__r2" / "meta.json").read_text())
    assert meta["condition"] == "variant-iso" and meta["variant"] == "iso" and meta["variant_sha"] == repo["old"]
    assert meta["rep"] == 2 and meta["adopted_from"] == "skill" and meta["skill_loaded"] is True
    assert json.loads((tmp_path / "runs" / f"{stem}__omp__baseline__r1" / "meta.json").read_text())["condition"] == "baseline"

    judge = json.loads((tmp_path / "judge.json").read_text())
    pairs = [j.get("pair") for j in judge[:4]]
    assert pairs == ["variant-iso:baseline", "variant-iso:competitor-humanizer", "variant-iso:competitor-humanizer",
                     "baseline:competitor-humanizer"]  # the default verdict got its pair; the baseline-only one is untouched
    assert judge[0]["winner"] == "variant-iso" and judge[0]["picks"] == ["variant-iso", "variant-iso"]
    assert judge[1]["winner"] == "competitor-humanizer" and judge[1]["picks"] == ["competitor-humanizer", "tie"]
    assert judge[2]["human"] == "variant-iso" and judge[2]["faithful"] == "tie"
    assert judge[2]["picks"]["human"] == ["variant-iso", "variant-iso"]
    assert judge[3]["winner"] == "baseline"

    folders = {p.name for p in (tmp_path / "judge").iterdir()}
    assert f"{stem}__omp__r1__variant-iso-vs-baseline__order1" in folders  # the default pair's folders
    assert f"{stem}__omp__r1__variant-iso-vs-baseline__shots" in folders
    assert f"{stem}__omp__r2__variant-iso-vs-competitor-humanizer__order1" in folders
    assert f"{stem}__omp__r1__baseline-vs-competitor-humanizer__order1" in folders  # unrelated pair kept
    assert f"{stem}__omp__r1__order1" not in folders and not any("__skill-vs-" in n for n in folders)
    shots = tmp_path / "judge" / f"{stem}__omp__r1__variant-iso-vs-baseline__shots"
    assert sorted(p.name for p in shots.iterdir()) == ["baseline-1.png", "variant-iso-1.png"]
    # a new skill:baseline verdict is now missing, so a resumed run judges it again
    assert not [j for j in judge if run.pair_key(run.DEFAULT_PAIR) == (j.get("pair") or "skill:baseline")]


def test_adopt_refuses_when_the_target_exists_and_changes_nothing(repo, tmp_path):
    fake_run(tmp_path, repeat=1)
    variant = run.export_variant("iso", repo["old"])
    assert run.adopt_runs(tmp_path, "skill", "variant-iso", variant) == 1
    fake_skill = tmp_path / "runs" / sorted(p.name for p in (tmp_path / "runs").iterdir())[0]
    (tmp_path / "runs" / "post-writing__a__omp__skill").mkdir()  # a new skill run next to the adopted one
    (tmp_path / "runs" / "post-writing__a__omp__skill" / "meta.json").write_text(json.dumps(
        {"case": "post-writing/a", "skill": "post-writing", "host": "omp", "condition": "skill", "rep": 1}))
    before = sorted(p.name for p in (tmp_path / "runs").iterdir())
    with pytest.raises(ValueError, match="already holds variant-iso"):
        run.adopt_runs(tmp_path, "skill", "variant-iso", variant)
    assert sorted(p.name for p in (tmp_path / "runs").iterdir()) == before and fake_skill.exists()


def test_parse_adoptions():
    v = {"iso": "f0a07bf"}
    assert run.parse_adoptions(["skill=variant-iso"], v, True, "/d") == ([("skill", "variant-iso")], None)
    assert run.parse_adoptions(None, v, False, None) == ([], None)
    assert "--out DIR and --resume" in run.parse_adoptions(["skill=variant-iso"], v, False, "/d")[1]
    assert "--out DIR and --resume" in run.parse_adoptions(["skill=variant-iso"], v, True, None)[1]
    assert "declare the variant" in run.parse_adoptions(["skill=variant-other"], v, True, "/d")[1]
    assert "wants SRC_CONDITION=variant-NAME" in run.parse_adoptions(["skill=baseline"], v, True, "/d")[1]
    assert "wants SRC_CONDITION=variant-NAME" in run.parse_adoptions(["skill"], v, True, "/d")[1]


def test_main_adopts_once_runs_the_new_skill_and_judges_the_new_pairs(repo, tmp_path, monkeypatch, capsys):
    """The whole A/B recipe on a tiny finished run: relabel old skill runs, run new skill and a second variant,
    judge the requested pairs; a repeated command adopts nothing twice and reruns nothing."""
    cid = CASE_ID
    stem = cid.replace("/", "__")
    out = tmp_path / "ab"
    for cond, text in (("skill", "old skill text"), ("baseline", "baseline text")):
        d = out / "runs" / f"{stem}__omp__{cond}"
        (d / "workspace" / "out").mkdir(parents=True)
        (d / "workspace" / "out" / "email.md").write_text(text)
        (d / "reply.md").write_text("ok")
        (d / "meta.json").write_text(json.dumps({"case": cid, "skill": "structured-drafting", "host": "omp",
                                                 "condition": cond, "rep": 1, "skill_loaded": True, "error": None}))
    (out / "judge.json").write_text(json.dumps([{"case": cid, "host": "omp", "rep": 1, "judge": "omp", "winner": "skill",
                                                 "picks": ["skill", "skill"]}]))
    executed = []

    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None):
        executed.append(out_dir.name)
        (ws / "out").mkdir(exist_ok=True)
        (ws / "out" / "email.md").write_text(GOOD)
        (out_dir / "reply.md").write_text("ok")
        return {"log": "skill://structured-drafting", "exit_code": 0, "error": None, "duration_s": 0.1}

    judged = []

    def judge_once(case, a, b, host, run_dir, tag, a_args, shots=None, shot_note="", figures=None):
        judged.append(tag)
        return "TIE", "same", {}

    monkeypatch.setattr(run, "execute", execute)
    monkeypatch.setattr(run, "judge_once", judge_once)
    monkeypatch.setattr(run.shutil, "which", lambda name: "/bin/" + name)
    monkeypatch.setattr(run, "cli_version", lambda cmd: "test")
    monkeypatch.setattr(run, "diagram_design_version", lambda: None)
    monkeypatch.setattr(run, "SKILLS", [repo["root"] / "skills" / "structured-drafting"])
    cmd = ["--host", "omp", "--cases", cid, "--condition", "both", "--variant", f"iso={repo['old']}",
           "--variant", f"pre={repo['new']}", "--adopt-runs", "skill=variant-iso", "--resume", "--out", str(out),
           "--judge", "omp", "--judge-pairs", "skill:baseline,skill:variant-iso,skill:variant-pre"]
    assert run.main(cmd) == 0
    assert sorted(executed) == [f"{stem}__omp__skill", f"{stem}__omp__variant-pre"]  # baseline and variant-iso were not rerun
    info = json.loads((out / "run.json").read_text())
    assert info["conditions"] == ["skill", "baseline", "variant-iso", "variant-pre"]
    assert info["variants"]["iso"] == {"ref": repo["old"], "sha": repo["old"], "skills": {"structured-drafting": "1.0"}}
    assert info["adopted"] == [{"from": "skill", "to": "variant-iso", "runs": 1}]
    meta = json.loads((out / "runs" / f"{stem}__omp__variant-iso" / "meta.json").read_text())
    assert meta["variant_sha"] == repo["old"]
    assert (out / "runs" / f"{stem}__omp__variant-iso" / "workspace" / "out" / "email.md").read_text() == "old skill text"
    judge = json.loads((out / "judge.json").read_text())
    assert sorted(j.get("pair", "skill:baseline") for j in judge) == [
        "skill:baseline", "skill:variant-iso", "skill:variant-pre", "variant-iso:baseline"]
    assert next(j for j in judge if j.get("pair") == "variant-iso:baseline")["winner"] == "variant-iso"  # the old verdict
    assert len(judged) == 6  # three new pairs x two orders
    report = (out / "report.md").read_text()
    assert "## A/B: skill vs variant-iso" in report and "## A/B: skill vs variant-pre" in report
    assert "## Blind judge: skill vs variant-pre" in report and "## Blind judge: variant-iso vs baseline" in report

    executed.clear()
    judged.clear()
    assert run.main(cmd) == 0
    assert not executed and not judged  # same command again: nothing adopted twice, nothing rerun
    assert json.loads((out / "run.json").read_text())["adopted"] == info["adopted"]
    assert "already adopted" in capsys.readouterr().out


def test_main_rejects_bad_variant_options(repo, tmp_path, capsys):
    base = ["--host", "omp", "--cases", CASE_ID, "--out", str(tmp_path / "o")]
    assert run.main([*base, "--variant", "pre=no-such-ref"]) == 2
    assert "not a commit" in capsys.readouterr().err
    assert run.main([*base, "--adopt-runs", "skill=variant-iso", "--resume"]) == 2  # variant not declared
    assert "declare the variant" in capsys.readouterr().err
    assert run.main([*base, "--variant", f"iso={repo['old']}", "--adopt-runs", "skill=variant-iso"]) == 2
    assert "--out DIR and --resume" in capsys.readouterr().err


# ---------------------------------------------------------------- grading

def result(case, cond, passed, loaded=False, error=None, skill="post-writing", rep=1, score=None):
    return {"case": case, "skill": skill, "host": "omp", "condition": cond, "rep": rep, "skill_loaded": loaded,
            "exit_code": 0, "duration_s": 1, "error": error, "deliverables": {},
            "passed": passed, "score": (1.0 if passed else 0.5) if score is None else score,
            "checks": [{"type": "output_present", "passed": error is None, "detail": ""},
                       {"type": "word_count", "passed": passed, "detail": "n"}]}


def ab_runs():
    runs = []
    for case, (s, b, v, w) in {"a/1": (True, False, False, True), "a/2": (True, True, True, None),
                               "a/3": (False, False, True, True), "a/4": (True, True, None, None)}.items():
        runs.append(result(case, "skill", s, loaded=True))
        runs.append(result(case, "baseline", b))
        for cond, value in (("variant-pre", v), ("variant-iso", w)):
            if value is not None:  # the variants ran only some of the cases (resumed or errored)
                runs.append(result(case, cond, value, loaded=(cond == "variant-pre")))
    return runs


def test_variants_are_paired_with_skill_on_host_case_rep_and_do_not_unpair_the_main_comparison():
    by = grade.summarize(ab_runs(), [])["by"]["omp/ALL"]
    assert by["skill_n"] == 4 and by["baseline_n"] == 4 and by["excluded"] == 0 and by["skill_pass"] == 0.75
    pre, iso = by["variants"]["pre"], by["variants"]["iso"]
    assert pre["n"] == 3 and pre["skill_pass"] == pytest.approx(2 / 3) and pre["variant_pass"] == pytest.approx(2 / 3)
    assert pre["delta"] == pytest.approx(0) and pre["skill_loaded"] == 1.0 and pre["variant_loaded"] == 1.0
    assert iso["n"] == 2 and iso["skill_pass"] == 0.5 and iso["variant_pass"] == 1.0 and iso["delta"] == -0.5
    assert iso["score_delta"] == pytest.approx(-0.25) and iso["variant_loaded"] == 0.0
    assert "competitors" not in by


def test_variant_pairing_uses_reps_and_drops_host_errors():
    runs = [result("a/1", "skill", True, loaded=True, rep=r) for r in (1, 2)]
    runs += [result("a/1", "variant-pre", False, loaded=True, rep=1), result("a/1", "variant-pre", True, rep=2, error="timeout")]
    runs[-1]["checks"][0]["passed"] = False  # no output: a host error, drops only its pair
    pre = grade.summarize(runs, [])["by"]["omp/ALL"]["variants"]["pre"]
    assert pre["n"] == 1 and pre["skill_pass"] == 1.0 and pre["variant_pass"] == 0.0
    alone = grade.summarize([r for r in ab_runs() if r["condition"] != "skill"], [])["by"]["omp/ALL"]
    assert "variants" not in alone  # no skill side, nothing to compare


def test_judge_pairs_with_variants_are_tallied_and_reported_like_competitor_pairs():
    judge = [
        {"case": "a/1", "host": "omp", "rep": 1, "judge": "omp", "winner": "skill"},
        {"case": "a/1", "host": "omp", "rep": 1, "judge": "omp", "pair": "skill:variant-pre", "winner": "variant-pre"},
        {"case": "a/2", "host": "omp", "rep": 1, "judge": "omp", "pair": "skill:variant-pre", "winner": "skill"},
        {"case": "a/3", "host": "omp", "rep": 1, "judge": "omp", "pair": "skill:variant-pre", "winner": "tie"},
        {"case": "a/2", "host": "omp", "rep": 1, "judge": "omp", "pair": "skill:variant-pre",
         "mode": "style", "winner": "style", "human": "skill", "faithful": "variant-pre"},
    ]
    summary = grade.summarize([], judge)
    assert summary["judge"]["skill"] == 1  # the default tally is skill:baseline only
    info = summary["judge_pairs"]["skill:variant-pre"]
    assert info["verdicts"]["variant-pre"] == 1 and info["verdicts"]["skill"] == 1 and info["verdicts"]["tie"] == 1
    assert info["style"]["human"]["skill"] == 1 and info["style"]["faithful"]["variant-pre"] == 1
    report = grade.render_report({"run": {}, "runs": [], "judge": judge, "summary": summary})
    assert "## Blind judge: skill vs variant-pre" in report and report.count("## Blind pairwise judge") == 1


def test_report_shows_ab_table_cases_column_and_provenance():
    runs = ab_runs()
    info = {"id": "r", "started": "now", "hosts": ["omp"], "cases": 4,
            "variants": {"pre": {"ref": "21cd881", "sha": "21cd881cc6a401e2f0c3ac5ea0e93b3eb3afad81", "skills": {}}}}
    report = grade.render_report({"run": info, "runs": runs, "judge": [], "summary": grade.summarize(runs, [])})
    assert "variant-pre = 21cd881 @ 21cd881cc6" in report
    assert "## A/B: skill vs variant-pre" in report and "## A/B: skill vs variant-iso" in report
    assert "| host / skill | skill | variant-pre | skill minus variant | n | skill loaded | variant loaded |" in report
    row = next(l for l in report.splitlines() if l.startswith("| **omp/ALL** |") and "| 3 |" in l)
    assert "67% (0.83)" in row and "+0 pts" in row
    assert "| variant-pre |" in report and "| variant-iso |" in report  # case-table columns
    assert "## Competitors" not in report
    plain = grade.render_report({"run": {}, "runs": runs[:2], "judge": [], "summary": grade.summarize(runs[:2], [])})
    assert "## A/B" not in plain


# ---------------------------------------------------------------- same-run gate

def ab_dir(tmp_path, skill_text, variant_text=GOOD, **info):
    root = tmp_path / "ab"
    make_run(root, skill_text, condition="skill")
    make_run(root, variant_text, condition="variant-pre")
    run_json = json.loads((root / "run.json").read_text())
    run_json["variants"] = {"pre": {"ref": "21cd881", "sha": "21cd881cc6a401e2f0c3ac5ea0e93b3eb3afad81", "skills": {}}}
    (root / "run.json").write_text(json.dumps(run_json))
    return root


def test_gate_check_against_a_variant_of_the_same_run(tmp_path, capsys):
    root = ab_dir(tmp_path, GOOD)
    assert gate.main(["check", str(root), "--reference-condition", "variant-pre"]) == 0
    out = capsys.readouterr().out
    assert "GATE PASSED" in out and "variant-pre = 21cd881 @ 21cd881cc6" in out
    assert "Known weak spots" not in out  # a frozen reference's list does not apply to a run-internal reference
    assert "ab / skill" in out  # the revision under test is the skill side

    leaky = ab_dir(tmp_path / "x", GOOD.replace("Sam", "[Your name]"))
    assert gate.main(["check", str(leaky), "--reference-condition", "variant-pre"]) == 1  # same rules: a leaked marker fails
    out = capsys.readouterr().out
    assert "GATE FAILED" in out and "leaked marker run rate" in out
    # the other way round the variant is the one that leaks, which is not the revision under test
    ok = ab_dir(tmp_path / "y", GOOD, GOOD.replace("Sam", "[Your name]"))
    assert gate.main(["check", str(ok), "--reference-condition", "variant-pre"]) == 0


def test_gate_in_run_uses_the_same_tolerance_config(tmp_path, capsys):
    root = ab_dir(tmp_path, GOOD)
    result_ = gate.check_in_run(root, "variant-pre", gate.CONFIG)
    assert result_[0] == 0
    config = json.loads(gate.CONFIG.read_text())
    config["absolute"]["leaked_marker_run_rate_max"] = 1.0
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    leaky = ab_dir(tmp_path / "x", GOOD.replace("Sam", "[Your name]"))
    assert gate.check_in_run(leaky, "variant-pre", gate.CONFIG)[0] == 1
    assert gate.check_in_run(leaky, "variant-pre", path)[0] == 0  # --config tolerances apply


def test_gate_in_run_errors(tmp_path):
    only_skill = tmp_path / "s"
    make_run(only_skill, GOOD)
    code, text = gate.check_in_run(only_skill, "variant-pre", gate.CONFIG)
    assert code == 2 and "no 'variant-pre' runs" in text
    only_variant = tmp_path / "v"
    make_run(only_variant, GOOD, condition="variant-pre")
    code, text = gate.check_in_run(only_variant, "variant-pre", gate.CONFIG)
    assert code == 2 and "no 'skill' runs" in text
    code, text = gate.check_in_run(only_skill, "baseline", gate.CONFIG)
    assert code == 2 and "variant-NAME" in text


def test_check_against_reference_json_still_works(tmp_path, capsys):
    run_dir = tmp_path / "r"
    make_run(run_dir, GOOD)
    reference = tmp_path / "reference.json"
    assert gate.main(["freeze", str(run_dir), "--out", str(reference)]) == 0
    assert gate.main(["check", str(run_dir), "--against", str(reference)]) == 0
    assert "Known weak spots" in capsys.readouterr().out
