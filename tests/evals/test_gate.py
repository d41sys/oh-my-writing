"""Tests for the regression gate. Run: uv run --with pytest python -m pytest tests/evals -q"""

import copy
import json
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import gate  # noqa: E402
import stats  # noqa: E402
from test_stats import GOOD, make_run  # noqa: E402

CONFIG = json.loads((EVALS / "gate" / "config.json").read_text())
N_CASES = 8


def run(case_id, skill, rep, kind="reader", **metrics):
    base = {"invented_facts": 0.0, "check_pass_rate": 1.0, "gap_markers_leaked": 0.0, "slop_per_1000w": 1.0,
            "hedge_per_1000w": 3.0, "case_passed": 1.0}
    base.update(metrics)
    return {"case": case_id, "skill": skill, "kind": kind, "host": "h", "rep": rep, "metrics": base}


def suite(skill="s", n=N_CASES, reps=2, **metrics):
    return [run(f"{skill}/c{i}", skill, r, **metrics) for i in range(n) for r in range(1, reps + 1)]


def verdicts(result, scope="ALL"):
    return {r["metric"]: r["verdict"] for r in result["rows"] if r["scope"] == scope}


def test_identical_run_passes_and_is_deterministic():
    ref = suite()
    a = gate.evaluate(ref, copy.deepcopy(ref), CONFIG)
    assert not a["failed"] and a["pairs"] == {"s": 16, "ALL": 16}
    assert a == gate.evaluate(ref, copy.deepcopy(ref), CONFIG)


def test_a_stray_invented_fact_is_noise_but_a_systematic_rise_fails_in_skill_and_all():
    ref, stray = suite(), suite()
    stray[3]["metrics"]["invented_facts"] = 1.0  # one run in sixteen: a rerun can do that
    assert not gate.evaluate(ref, stray, CONFIG)["failed"]
    result = gate.evaluate(ref, suite(invented_facts=1.0), CONFIG)  # every run: the skill changed
    assert result["failed"]
    assert verdicts(result, "s")["invented_facts"] == "FAIL" and verdicts(result)["invented_facts"] == "FAIL"


def test_invented_facts_below_reference_passes_and_tolerance_is_configurable():
    ref = suite(invented_facts=2.0)
    assert not gate.evaluate(ref, suite(invented_facts=1.0), CONFIG)["failed"]
    loose = {**CONFIG, "metrics": {**CONFIG["metrics"], "invented_facts": {"tolerance": 1.0}}}
    assert not gate.evaluate(suite(), suite(invented_facts=1.0), loose)["failed"]  # +1 per run, tolerance 1
    tight = {**CONFIG, "metrics": {**CONFIG["metrics"], "invented_facts": {"tolerance": 0.9}}}
    assert gate.evaluate(suite(), suite(invented_facts=1.0), tight)["failed"]


def test_leaked_marker_run_rate_is_absolute_and_only_for_reader_facing_output():
    ref = suite()
    new = suite()
    new[0]["metrics"]["gap_markers_leaked"] = 1.0
    result = gate.evaluate(ref, new, CONFIG)
    assert result["failed"] and verdicts(result)["leaked marker run rate (reader-facing)"] == "FAIL"
    row = next(r for r in result["rows"] if r["scope"] == "ALL" and r["rule"] == "absolute")
    assert row["new"] == 1 / 16 and "1 of 16" in row["detail"]
    draft = suite(kind="draft")
    draft[0]["metrics"]["gap_markers_leaked"] = 2.0
    assert not gate.evaluate(suite(kind="draft"), draft, CONFIG)["failed"]  # drafts may carry markers for the author


def test_leaked_markers_count_runs_not_markers_and_do_not_need_the_reference_to_be_clean():
    ref = suite()
    ref[0]["metrics"]["gap_markers_leaked"] = 1.0
    assert gate.evaluate(ref, copy.deepcopy(ref), CONFIG)["failed"]  # absolute: any run with a leak fails
    many = suite()
    many[0]["metrics"]["gap_markers_leaked"] = 5.0  # five markers in one run is still one run of sixteen
    loose = {**CONFIG, "absolute": {"leaked_marker_run_rate_max": 0.07}}
    assert not gate.evaluate(suite(), many, loose)["failed"]
    assert gate.evaluate(suite(), many, {**CONFIG, "absolute": {"leaked_marker_run_rate_max": 0.05}})["failed"]


def test_check_pass_rate_is_a_paired_ci_rule_with_tolerance():
    ref = suite()
    just_inside = suite(check_pass_rate=0.99)   # 0.01 below, tolerance 0.02
    outside = suite(check_pass_rate=0.9)
    assert not gate.evaluate(ref, just_inside, CONFIG)["failed"]
    result = gate.evaluate(ref, outside, CONFIG)
    assert result["failed"] and verdicts(result)["check_pass_rate"] == "FAIL"
    one_bad = suite()
    one_bad[0]["metrics"]["check_pass_rate"] = 0.0  # one run of sixteen failed every check: noise, not a verdict
    assert not gate.evaluate(ref, one_bad, CONFIG)["failed"]


def test_statistical_regression_needs_tolerance_and_ci_excluding_zero():
    ref = suite()
    # consistent +2.0 on every case: beyond the 0.5 tolerance and the CI excludes zero
    bad = gate.evaluate(ref, suite(slop_per_1000w=3.0), CONFIG)
    assert bad["failed"] and verdicts(bad)["slop_per_1000w"] == "FAIL"
    # consistent but small (+0.1, within tolerance): the CI excludes zero, still fine
    small = gate.evaluate(ref, suite(slop_per_1000w=1.1), CONFIG)
    assert not small["failed"] and verdicts(small)["slop_per_1000w"] == "ok"
    # beyond tolerance on average but noisy, CI includes zero: a warning, not a failure
    noisy = suite()
    for i, r in enumerate(noisy):
        r["metrics"]["slop_per_1000w"] = 1.0 + (6.0 if i < 2 else 0.0)  # two runs jump, the rest unchanged
    warn = gate.evaluate(ref, noisy, CONFIG)
    assert not warn["failed"] and verdicts(warn)["slop_per_1000w"] == "warn"


def test_fail_needs_the_whole_ci_beyond_tolerance_not_just_excluding_zero():
    ref = suite(reps=1)
    new = suite(reps=1)
    for i, r in enumerate(new):  # per-case worsening 0.1 ... 1.8: mean beyond the 0.5 tolerance, CI starts below it
        r["metrics"]["slop_per_1000w"] = 1.0 + [0.1, 0.2, 0.3, 0.4, 0.5, 1.6, 1.7, 1.8][i]
    result = gate.evaluate(ref, new, CONFIG)
    row = next(r for r in result["rows"] if r["scope"] == "ALL" and r["metric"] == "slop_per_1000w")
    assert row["delta"] > 0.5 and row["ci"][0] > 0 and row["ci"][0] < 0.5  # excludes zero, reaches inside the tolerance
    assert row["verdict"] == "warn" and not result["failed"]
    strict = {**CONFIG, "metrics": {**CONFIG["metrics"], "slop_per_1000w": {"tolerance": 0.1}}}
    assert verdicts(gate.evaluate(ref, new, strict))["slop_per_1000w"] == "FAIL"  # whole CI above 0.1


def test_improvement_is_reported_not_failed():
    result = gate.evaluate(suite(), suite(slop_per_1000w=0.2), CONFIG)
    assert not result["failed"] and verdicts(result)["slop_per_1000w"] == "better"


def test_direction_higher_is_better_metric():
    ref = suite(flesch_reading_ease=70.0)
    worse = gate.evaluate(ref, suite(flesch_reading_ease=60.0), CONFIG)
    assert worse["failed"] and verdicts(worse)["flesch_reading_ease"] == "FAIL"
    assert verdicts(gate.evaluate(ref, suite(flesch_reading_ease=80.0), CONFIG))["flesch_reading_ease"] == "better"


def test_ungated_metric_and_few_cases():
    result = gate.evaluate(suite(), suite(hedge_per_1000w=9.0), CONFIG)
    assert "hedge_per_1000w" not in verdicts(result) and not result["failed"]  # configured gated: false
    result = gate.evaluate(suite(n=2), suite(n=2, slop_per_1000w=9.0), CONFIG)
    assert verdicts(result)["slop_per_1000w"] == "few" and not result["failed"]  # 2 cases: no verdict


def test_unpaired_runs_are_left_out_and_no_overlap_is_reported():
    ref = suite()
    new = suite()[:8]  # only the first four cases, both reps
    assert gate.evaluate(ref, new, CONFIG)["pairs"]["ALL"] == 8
    other = [run("x/c0", "x", 1)]
    result = gate.evaluate(ref, other, CONFIG)
    assert verdicts(result, "x")["-"] == "n/a" and not result["failed"]


def test_tolerances_come_from_config():
    ref = suite()
    strict = {**CONFIG, "metrics": {**CONFIG["metrics"], "slop_per_1000w": {"tolerance": 0.05}}}
    assert gate.evaluate(ref, suite(slop_per_1000w=1.1), strict)["failed"]


def test_config_lists_only_real_metrics():
    for name, rule in CONFIG["metrics"].items():
        assert name in stats.METRICS and stats.METRICS[name]["direction"], name
        assert rule["tolerance"] >= 0


# ---------------------------------------------------------------- freeze and check on a results directory

def test_freeze_and_check_round_trip(tmp_path, capsys):
    run_dir = tmp_path / "ref-run"
    make_run(run_dir, GOOD)
    reference = tmp_path / "reference.json"
    assert gate.main(["freeze", str(run_dir), "--out", str(reference), "--model", "m-1"]) == 0
    ref = json.loads(reference.read_text())
    assert ref["run"]["id"] == "ref-run" and ref["run"]["model"] == "m-1" and ref["metrics_version"] == stats.METRICS_VERSION
    assert ref["skill_versions"]["anti-slop-editing"] and len(ref["runs"]) == 1 and set(ref["tools"]) >= {"fact_diff.py", "slop_scan.py"}
    again = tmp_path / "again.json"
    assert gate.main(["freeze", str(run_dir), "--out", str(again), "--model", "m-1"]) == 0
    assert again.read_text() == reference.read_text()  # frozen file is reproducible

    assert gate.main(["check", str(run_dir), "--against", str(reference)]) == 0
    assert "GATE PASSED" in capsys.readouterr().out

    leaky = tmp_path / "leaky"
    make_run(leaky, GOOD.replace("Sam", "[Your name]"))
    assert gate.main(["check", str(leaky), "--against", str(reference)]) == 1
    out = capsys.readouterr().out
    assert "GATE FAILED" in out and "leaked marker run rate" in out and "tiny-email-no-scaffolding" in out

    invented = tmp_path / "invented"
    make_run(invented, GOOD.replace("2 of 5", "2 of 7"))
    assert gate.main(["check", str(invented), "--against", str(reference)]) == 0  # one case: too few for any verdict
    assert "few" in capsys.readouterr().out


def test_check_rejects_other_metric_version_and_missing_condition(tmp_path, capsys):
    run_dir = tmp_path / "r"
    make_run(run_dir, GOOD)
    reference = tmp_path / "reference.json"
    gate.main(["freeze", str(run_dir), "--out", str(reference)])
    ref = json.loads(reference.read_text())
    ref["metrics_version"] = "0"
    reference.write_text(json.dumps(ref))
    assert gate.main(["check", str(run_dir), "--against", str(reference)]) == 2
    assert "Not comparable" in capsys.readouterr().err
    baseline_only = tmp_path / "b"
    make_run(baseline_only, GOOD, condition="baseline")
    gate.main(["freeze", str(run_dir), "--out", str(reference)])
    assert gate.main(["check", str(baseline_only), "--against", str(reference)]) == 2


# ---------------------------------------------------------------- A/A noise test


def three_rep_runs(skill="s", n=8, noise=0.0):
    """Runs with three repetitions; rep 2 sits `noise` above rep 1 and rep 3 `noise` below it in slop."""
    out = []
    for i in range(n):
        for rep, shift in ((1, 0.0), (2, noise), (3, -noise)):
            out.append(run(f"{skill}/c{i}", skill, rep, slop_per_1000w=2.0 + 0.1 * i + shift))
    return out


def test_aa_pseudo_runs_relabel_reps_and_never_change_values():
    runs = three_rep_runs(n=2)
    pseudo = {name: (ref, ps) for name, ref, ps in gate.aa_pseudo_runs(runs)}
    assert len(pseudo) == 2 + 6  # two shifts, six ordered single-rep pairs
    ref, shifted = pseudo["reps shifted by 1 (r1->r2, r2->r3, r3->r1)"]
    assert ref == runs
    by_rep = lambda rs, rep: {r["case"]: r["metrics"]["slop_per_1000w"] for r in rs if r["rep"] == rep}
    assert by_rep(shifted, 2) == by_rep(runs, 1) and by_rep(shifted, 3) == by_rep(runs, 2) and by_rep(shifted, 1) == by_rep(runs, 3)
    ref, one = pseudo["single rep r3 vs r1"]
    assert {r["rep"] for r in ref + one} == {1} and by_rep(ref, 1) == by_rep(runs, 1) and by_rep(one, 1) == by_rep(runs, 3)
    assert gate.aa_pseudo_runs(suite(reps=1)) == []


def test_aa_passes_on_pure_rerun_noise_and_fails_when_the_gate_is_too_sensitive():
    runs = three_rep_runs(noise=0.2)  # rep-to-rep wobble of at most 0.4 inside the 0.5 tolerance
    code, text = gate.aa_report(runs, CONFIG, "synthetic")
    assert code == 0 and "A/A PASSED" in text and "single rep r2 vs r1" in text
    twitchy = {**CONFIG, "metrics": {**CONFIG["metrics"], "slop_per_1000w": {"tolerance": 0.0}}}
    code, text = gate.aa_report(three_rep_runs(noise=1.0), twitchy, "synthetic")
    assert code == 1 and "A/A FAILED" in text and "slop_per_1000w" in text


def test_aa_lists_a_defect_in_the_run_itself_without_counting_it_as_noise():
    runs = three_rep_runs()
    runs[0]["metrics"]["gap_markers_leaked"] = 1.0
    code, text = gate.aa_report(runs, CONFIG, "synthetic")
    assert code == 0 and "A/A PASSED" in text and "the run itself carries a defect" in text


def test_aa_command_on_a_results_directory(tmp_path, capsys):
    run_dir = tmp_path / "three"
    for rep in (1, 2, 3):
        make_run(run_dir, GOOD, rep=rep)
    assert gate.main(["aa", str(run_dir)]) == 0  # one case: no verdicts, nothing can fire
    assert "A/A PASSED" in capsys.readouterr().out
    single = tmp_path / "single"
    make_run(single, GOOD)
    assert gate.main(["aa", str(single)]) == 2
    assert "single repetition" in capsys.readouterr().err
    assert gate.main(["aa", str(run_dir), "--condition", "baseline"]) == 2


# ---------------------------------------------------------------- known weak spots of the reference


def test_weak_spots_list_where_the_reference_is_worse_with_ci_excluding_zero():
    ref = suite(slop_per_1000w=3.0)          # the reference is worse than the other run in slop
    other = suite(slop_per_1000w=1.0)
    spots = gate.weak_spots(ref, other, CONFIG)
    assert {(s["scope"], s["metric"]) for s in spots} == {("s", "slop_per_1000w"), ("ALL", "slop_per_1000w")}
    s = next(s for s in spots if s["scope"] == "ALL")
    assert s["reference"] == 3.0 and s["other"] == 1.0 and s["worse_by"] == 2.0 and s["ci"][0] > 0
    assert gate.weak_spots(other, ref, CONFIG) == []  # the reference is better than the other run: nothing to flag
    assert gate.weak_spots(ref, copy.deepcopy(ref), CONFIG) == []


def test_weak_command_and_check_print_the_weak_spots(tmp_path, capsys):
    run_dir, other_dir = tmp_path / "ref-run", tmp_path / "other-run"
    make_run(run_dir, GOOD)
    make_run(other_dir, GOOD)
    reference = tmp_path / "reference.json"
    gate.main(["freeze", str(run_dir), "--out", str(reference)])
    assert gate.main(["weak", str(other_dir), "--against", str(reference), "--out", str(tmp_path / "weak_spots.json")]) == 0
    weak = json.loads((tmp_path / "weak_spots.json").read_text())
    assert weak["reference_run"] == "ref-run" and weak["other_run"] == "other-run" and weak["spots"] == []
    capsys.readouterr()
    assert gate.main(["check", str(run_dir), "--against", str(reference)]) == 0  # weak_spots.json sits next to the reference
    assert "Known weak spots of the reference: none against other-run" in capsys.readouterr().out


def test_check_output_names_weak_spots_and_flags_a_stale_list():
    ref_meta = {"run": {"id": "ref"}, "metrics_version": stats.METRICS_VERSION}
    weak = {"reference_run": "ref", "other_run": "older", "metrics_version": stats.METRICS_VERSION,
            "spots": [{"scope": "ALL", "metric": "slop_per_1000w", "gated": True, "reference": 3.0, "other": 1.0,
                       "worse_by": 2.0, "ci": [1.5, 2.5], "n_cases": 8, "tolerance": 0.5}]}
    result = gate.evaluate(suite(slop_per_1000w=3.0), suite(slop_per_1000w=3.0), CONFIG)
    text = "\n".join(gate.render_weak_spots(weak, ref_meta, result))
    assert "slop_per_1000w" in text and "does not mean these are fine" in text and "older" in text
    assert "regenerate" in "\n".join(gate.render_weak_spots({**weak, "reference_run": "other"}, ref_meta, result))
    assert "none recorded" in gate.render_weak_spots(None, ref_meta, result)[0]


def test_committed_config_has_the_absolute_rule_and_gates_invented_facts_and_check_pass_rate():
    assert CONFIG["absolute"]["leaked_marker_run_rate_max"] == 0
    assert CONFIG["metrics"]["invented_facts"]["tolerance"] >= 0 and CONFIG["metrics"]["check_pass_rate"]["tolerance"] >= 0
    assert "hard" not in CONFIG
