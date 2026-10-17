"""Tests for evals/flow_validation.py. Run: uv run --with pytest python -m pytest tests/evals -q"""

import json
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import flow_validation as fv  # noqa: E402
import stats  # noqa: E402

WATER = ["The pump fills the tank.", "The tank feeds the filter.", "The filter cleans the valve.", "The valve opens the cooler.",
         "The cooler chills the boiler.", "The boiler heats the mixer.", "The mixer stirs the drain.",
         "The drain empties the sensor."]


def rec(case_id, cond, rep=1, loaded=True, **metrics):
    base = dict.fromkeys(stats.METRICS)
    base.update(metrics)
    return {"case": case_id, "skill": "s", "kind": "reader", "host": "h", "condition": cond, "rep": rep,
            "host_error": False, "skill_loaded": loaded, "metrics": base}


def test_cluster_share_pools_pairs_and_resamples_cases():
    res = fv.cluster_share([("a", True), ("a", False), ("b", True)], "t")
    assert (res["n"], res["cases"]) == (3, 2) and res["share"] == pytest.approx(2 / 3)
    assert res["ci"] == fv.cluster_share([("a", True), ("a", False), ("b", True)], "t")["ci"]  # fixed seed
    assert fv.cluster_share([], "t") == {"n": 0, "cases": 0, "share": None, "ci": None}
    assert fv.cluster_share([("a", True), ("b", True), ("c", True)], "t")["ci"] == (1.0, 1.0)


def test_judged_pairs_keep_clear_verdicts_only():
    entries = [
        {"case": "c1", "host": "h", "rep": 1, "mode": "style", "winner": "style", "human": "skill", "faithful": "baseline"},
        {"case": "c2", "host": "h", "rep": 1, "mode": "style", "winner": "style", "human": "inconsistent", "faithful": "skill"},
        {"case": "c3", "host": "h", "rep": 2, "pair": "skill:competitor-x", "winner": "competitor-x"},
        {"case": "c4", "host": "h", "rep": 1, "winner": "tie"},
        {"case": "c5", "host": "h", "rep": 1, "winner": "baseline"},
        {"case": "c6", "host": "h", "rep": 1, "winner": "skill", "visual": True, "scores": {}},
        {"case": "c7", "host": "h", "rep": 1, "winner": "error"},
    ]
    got = fv.judged_pairs(entries)
    assert [(p["source"], p["case"], p["winner"], p["loser"]) for p in got] == [
        ("style", "c1", "skill", "baseline"),  # the 'reads human' answer, not the 'faithful' one
        ("text", "c3", "competitor-x", "skill"),
        ("text", "c5", "baseline", "skill")]


def test_agreement_is_the_share_of_pairs_where_the_metric_prefers_the_winner():
    # skill is the judge's winner in cases a-d; slop is lower for the skill in a, b, c (agree), higher in d (disagree),
    # equal in e (a tie: left out) and missing in f
    recs = []
    for case, skill_v, base_v in [("a", 1, 3), ("b", 2, 5), ("c", 0, 1), ("d", 4, 2), ("e", 2, 2), ("f", None, 2)]:
        recs += [rec(case, "skill", slop_per_1000w=skill_v, sentence_length_cv=skill_v),
                 rec(case, "baseline", slop_per_1000w=base_v, sentence_length_cv=base_v)]
    pairs = [{"source": "text", "host": "h", "case": c, "rep": 1, "winner": "skill", "loser": "baseline"} for c in "abcdef"]
    a = fv.agreement(recs, pairs, "slop_per_1000w")  # lower is better
    assert (a["n"], a["cases"], a["ties"]) == (4, 4, 1) and a["share"] == pytest.approx(3 / 4)
    higher = fv.agreement(recs, pairs, "sentence_length_cv")  # higher is better: the same data agrees only in d
    assert higher["share"] == pytest.approx(1 / 4)
    assert fv.agreement(recs, pairs, "slop_per_1000w", source="style")["n"] == 0
    # a metric without a direction 'prefers' the higher value
    assert fv.agreement(recs, pairs, "words")["n"] == 0


def paragraphs_items(n=6):
    items = [{"key": ("h", f"s/c{i}", "skill", 1), "kind": "reader", "paragraphs": [WATER]} for i in range(n)]
    items.append({"key": ("h", "s/analysis", "skill", 1), "kind": "analysis", "paragraphs": [WATER]})
    return items


def test_shuffle_test_counts_reader_runs_and_skips_analysis():
    res = fv.shuffle_test(paragraphs_items(), "adjacent_cohesion")
    assert res["reader"]["runs"] == 6 and res["all non-analysis"]["runs"] == 6  # the analysis output is excluded
    assert res["reader"]["mean"]["share"] == 1.0 and res["reader"]["mean"]["worse"] == 6  # every shuffled copy is worse
    assert res["reader"]["orig_mean"] == pytest.approx(1 / 3) and res["reader"]["mean"]["shuffled_mean"] < 1 / 3
    jump = fv.shuffle_test(paragraphs_items(), "abrupt_jump_rate")
    assert jump["reader"]["mean"]["share"] == 1.0 and jump["reader"]["orig_mean"] == 0.0
    assert fv.shuffle_test(paragraphs_items(), "adjacent_cohesion") == res  # deterministic
    assert res["reader"]["single"]["worse"] + res["reader"]["single"]["better"] <= 6


def agree(share, lo, hi):
    return {"n": 50, "cases": 10, "share": share, "ci": (lo, hi)}


def shuffle_stub(share, lo, hi):
    return {"reader": {"runs": 20, "mean": {"share": share, "ci": (lo, hi)}}}


def test_decision_gates_only_validated_metrics():
    ok = fv.decide("long_sentence_share", None, agree(0.7, 0.6, 0.8))
    assert ok[0] == "gated" and "0.60" in ok[1]
    assert fv.decide("long_sentence_share", None, agree(0.55, 0.45, 0.65))[0] == "info"  # CI includes chance
    assert fv.decide("long_sentence_share", None, {"n": 0, "cases": 0, "share": None, "ci": None})[0] == "info"
    assert fv.decide("source_copy_rate", None, agree(0.9, 0.8, 1.0))[0] == "info"  # no direction
    assert fv.decide("adjacent_cohesion", shuffle_stub(0.6, 0.46, 0.73), agree(0.9, 0.8, 1.0))[0] == "info"  # fails the shuffle
    assert fv.decide("adjacent_cohesion", shuffle_stub(0.8, 0.7, 0.9), agree(0.9, 0.8, 1.0))[0] == "gated"
    assert fv.decide("adjacent_cohesion", shuffle_stub(0.8, 0.7, 0.9), agree(0.52, 0.4, 0.64))[0] == "info"


def test_duplication_tables_filter_loaded_pairs_but_never_the_baseline():
    recs = []
    for i in range(4):
        recs += [rec(f"s/c{i}", "skill", repeated_trigram_rate=0.01, loaded=i != 3),
                 rec(f"s/c{i}", "baseline", repeated_trigram_rate=0.05, loaded=False),
                 rec(f"s/c{i}", "competitor-x", repeated_trigram_rate=0.02, loaded=i != 0)]
    tables = dict(fv.duplication_tables(recs))
    row = lambda title: next(r for r in tables[title] if r[0] == "repeated_trigram_rate")
    assert row("h: skill vs baseline, all pairs")[-1] == "4/4" and row("h: skill vs baseline, loaded-only pairs")[-1] == "3/3"
    assert row("h: skill vs competitor-x, loaded-only pairs")[-1] == "2/2"  # c0 (competitor) and c3 (ours) drop out
    assert row("h: skill vs baseline, all pairs")[3] == "-0.040"  # skill - baseline: the skill repeats less
    assert "h: skill vs competitor-x, all pairs" in tables
    recs += [rec("s/c0", "variant-ref", repeated_trigram_rate=0.03)]
    assert "h: skill vs variant-ref, all pairs" in dict(fv.duplication_tables(recs))  # variants are compared too


def make_run(root: Path):
    cid = "structured-drafting/tiny-email-no-scaffolding"
    texts = {"skill": "Hi Ravi,\n\nThe audit is not done: 2 of 5 vendors are left. I can send it by Wed 22nd. May I share the draft first?\n\nBest,\nSam\n",
             "baseline": "Hi Ravi,\n\nThe audit is not done: 2 of 5 vendors are left.\n\nThe audit is not done: 2 of 5 vendors are left.\n\nBest,\nSam\n"}
    for cond, text in texts.items():
        d = root / "runs" / f"{cid.replace('/', '__')}__omp__{cond}__r1"
        (d / "workspace" / "out").mkdir(parents=True)
        (d / "meta.json").write_text(json.dumps({"case": cid, "skill": "structured-drafting", "host": "omp", "condition": cond,
                                                 "rep": 1, "skill_loaded": cond == "skill", "exit_code": 0, "error": None,
                                                 "duration_s": 1}))
        (d / "workspace" / "out" / "email.md").write_text(text)
    (root / "run.json").write_text(json.dumps({"id": root.name, "hosts": ["omp"], "repeat": 1}))
    (root / "judge.json").write_text(json.dumps([{"case": cid, "host": "omp", "rep": 1, "judge": "omp", "winner": "skill",
                                                  "picks": ["skill", "skill"], "reason": "x"}]))


def test_command_writes_both_reports(tmp_path, capsys):
    run = tmp_path / "mini"
    make_run(run)
    assert fv.main([str(run)]) == 0
    validation = (run / "flow-validation.md").read_text()
    duplication = (run / "duplication.md").read_text()
    assert "Order sensitivity" in validation and "Agreement with the blind judge" in validation
    assert "Composite candidate flow_score" in validation and "Decision for the new metrics" in validation
    assert "REPEATS ITSELF" in duplication and "COPIES THE INPUT" in duplication and "skill vs baseline" in duplication
    out = capsys.readouterr().out
    assert "source_copy_rate" in out and "omp / baseline" in out
    first = (run / "flow-validation.md").read_text()
    assert fv.main([str(run)]) == 0 and (run / "flow-validation.md").read_text() == first  # deterministic
