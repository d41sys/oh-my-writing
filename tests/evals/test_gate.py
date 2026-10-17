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


def test_one_extra_invented_fact_fails_the_hard_rule_in_skill_and_all():
    ref, new = suite(), suite()
    new[3]["metrics"]["invented_facts"] = 1.0
    result = gate.evaluate(ref, new, CONFIG)
    assert result["failed"]
    assert verdicts(result, "s")["invented_facts (total)"] == "FAIL" and verdicts(result)["invented_facts (total)"] == "FAIL"


def test_invented_facts_below_reference_passes_and_slack_is_configurable():
    ref = suite(invented_facts=2.0)
    assert not gate.evaluate(ref, suite(invented_facts=1.0), CONFIG)["failed"]
    ref2, new2 = suite(), suite()
    new2[0]["metrics"]["invented_facts"] = 1.0
    loose = {**CONFIG, "hard": {**CONFIG["hard"], "invented_facts_slack_per_run": 0.1}}
    assert not gate.evaluate(ref2, new2, loose)["failed"]  # 1 extra over 16 runs <= 0.1 * 16


def test_leaked_marker_fails_only_in_reader_facing_output():
    ref = suite()
    new = suite()
    new[0]["metrics"]["gap_markers_leaked"] = 1.0
    result = gate.evaluate(ref, new, CONFIG)
    assert result["failed"] and verdicts(result)["leaked markers (reader-facing)"] == "FAIL"
    draft = suite(kind="draft")
    draft[0]["metrics"]["gap_markers_leaked"] = 2.0
    assert not gate.evaluate(suite(kind="draft"), draft, CONFIG)["failed"]  # drafts may carry markers for the author


def test_leaked_markers_do_not_need_the_reference_to_be_clean():
    ref = suite()
    ref[0]["metrics"]["gap_markers_leaked"] = 1.0
    new = copy.deepcopy(ref)
    assert gate.evaluate(ref, new, CONFIG)["failed"]  # the rule is absolute: more than zero fails


def test_check_pass_rate_tolerance():
    ref = suite()
    just_inside = suite(check_pass_rate=0.99)   # 0.01 below, tolerance 0.02
    outside = suite(check_pass_rate=0.9)
    assert not gate.evaluate(ref, just_inside, CONFIG)["failed"]
    result = gate.evaluate(ref, outside, CONFIG)
    assert result["failed"] and verdicts(result)["check_pass_rate"] == "FAIL"


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
    assert "GATE FAILED" in out and "leaked markers" in out and "tiny-email-no-scaffolding" in out

    invented = tmp_path / "invented"
    make_run(invented, GOOD.replace("2 of 5", "2 of 7"))
    assert gate.main(["check", str(invented), "--against", str(reference)]) == 1
    assert "invented_facts" in capsys.readouterr().out


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
