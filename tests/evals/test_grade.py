"""Tests for the benchmark grader. Run: uv run --with pytest python -m pytest tests/evals -q"""

import json
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
import grade  # noqa: E402

CASE = {
    "id": "anti-slop-editing/sample",
    "skill": "anti-slop-editing",
    "description": "sample",
    "prompt": "Clean up draft.md and save it to out/draft.md.",
    "files": {"draft.md": "In today's fast-paced world, latency fell from 40 ms to 12 ms. It did not fall on Monday. "
                          "It did not fall on Tuesday either."},
    "output": "out/draft.md",
    "checks": [],
}


def run_check(check, output, reply=""):
    result = grade.grade_case({**CASE, "checks": [check]}, output, reply)
    return result["checks"][1]


@pytest.mark.parametrize("case", grade.load_cases(), ids=lambda c: c["id"])
def test_every_case_file_is_valid(case):
    assert grade.validate_case(case) == []


def test_validation_rejects_broken_cases():
    bad = {**CASE, "_path": "evals/cases/anti-slop-editing/other.json",
           "prompt": "Use anti-slop-editing on draft.md.",
           "checks": [{"type": "nope"}, {"type": "preserves", "source": "missing.md", "categories": ["vibes"]}]}
    errs = " | ".join(grade.validate_case(bad))
    for expected in ("should be", "must not name the skill", "must say where to save", "unknown type",
                     "unknown categories", "not an input file"):
        assert expected in errs


def test_missing_output_fails_the_case():
    result = grade.grade_case({**CASE, "checks": [{"type": "word_count", "max": 100}]}, None, "done")
    assert result["passed"] is False
    assert result["checks"][0]["type"] == "output_present" and not result["checks"][0]["passed"]


def test_invented_number_is_caught_and_source_numbers_pass():
    check = {"type": "no_added_facts"}
    assert not run_check(check, "Latency fell from 40 ms to 9 ms.")["passed"]
    assert run_check(check, "Latency fell from 40 ms to 12 ms, and 12 ms held.")["passed"]


def test_markers_and_allowlist_do_not_count_as_added_facts():
    check = {"type": "no_added_facts", "allow": ["99 ms"]}
    out = "Latency fell to 12 ms [ASK AUTHOR: p95 for 2025?]. Target 99 ms."
    assert run_check(check, out)["passed"]


NAMES_CASE = {**CASE, "prompt": "Write to Prof. Marchetti and save it to out/email.md.",
              "files": {"about.md": "Final-year BSc Environmental Science student at Riverbend University. "
                                    "Wants the MSc Marine Ecology at Westbrook University.\n"}}


def names_check(output, **extra):
    check = {"type": "no_added_facts", "categories": ["names"], **extra}
    return grade.grade_case({**NAMES_CASE, "checks": [check]}, output, "")["checks"][1]


def test_names_are_compared_word_by_word_not_as_whole_phrases():
    reworded = "Subject: Westbrook MSc Marine Ecology.\n\nI’m an Environmental Science student at Riverbend University."
    assert names_check(reworded)["passed"]
    invented = "I study Environmental Science at Riverbend University and admire Terraform Labs."
    result = names_check(invented)
    assert not result["passed"] and "Terraform Labs" in result["detail"]


def test_names_allow_lists_single_words_of_a_phrase():
    out = "Dear Professor Marchetti,\n\nI want the MSc Marine Ecology."
    assert not names_check(out)["passed"]
    assert names_check(out, allow=["Dear", "Professor"])["passed"]


def test_link_to_an_input_file_is_not_an_added_url():
    check = {"type": "no_added_facts", "categories": ["urls"]}
    run = lambda text: grade.grade_case({**NAMES_CASE, "checks": [check]}, text, "")["checks"][1]
    assert run("See [the notes](../about.md).")["passed"]
    assert not run("See [the notes](../other.md).")["passed"]


def test_preserves_counts_negations_but_treats_numbers_as_a_set():
    check = {"type": "preserves", "source": "draft.md", "categories": ["numbers", "negations"]}
    kept = "Latency fell from 40 ms to 12 ms. It did not fall on Monday or, not, on Tuesday."
    assert run_check(check, kept)["passed"]
    dropped = "Latency fell from 40 ms to 12 ms. It fell on Monday. It did not fall on Tuesday."
    result = run_check(check, dropped)
    assert not result["passed"] and "negations:not" in result["detail"]


def test_slop_checks_use_the_scanner():
    assert not run_check({"type": "slop_absent", "patterns": ["era-opener"]}, CASE["files"]["draft.md"])["passed"]
    assert run_check({"type": "slop_absent", "patterns": ["era-opener"]}, "Latency fell to 12 ms.")["passed"]
    assert run_check({"type": "max_slop", "max": 0}, "Latency fell to 12 ms.")["passed"]


def test_markers_target_both_by_default():
    check = {"type": "markers", "min": 2}
    assert run_check(check, "Draft [VERIFY: source].", "Note [ASK AUTHOR: date]")["passed"]
    assert not run_check(check, "Draft [VERIFY: source].", "")["passed"]


def test_similarity_and_word_count_bounds():
    same = CASE["files"]["draft.md"]
    assert run_check({"type": "similarity", "source": "draft.md", "min": 0.97}, same)["passed"]
    assert not run_check({"type": "similarity", "source": "draft.md", "min": 0.97}, "Latency fell.")["passed"]
    assert not run_check({"type": "word_count", "max": 3}, "one two three four")["passed"]


def test_text_checks_are_case_and_quote_insensitive():
    assert run_check({"type": "contains", "values": ["It's Done"]}, "it\u2019s done")["passed"]
    assert not run_check({"type": "not_contains", "values": ["airtight"]}, "The argument is Airtight.")["passed"]
    assert run_check({"type": "contains", "values": ["x"], "target": "reply"}, "", "x")["passed"]


def test_grade_run_reports_difference_between_conditions(tmp_path, monkeypatch):
    case = {**CASE, "checks": [{"type": "no_added_facts"}]}
    monkeypatch.setattr(grade, "load_cases", lambda patterns=None: [case])
    outputs = {"skill": "Latency fell from 40 ms to 12 ms.", "baseline": "Latency fell from 40 ms to 3 ms."}
    for cond, text in outputs.items():
        d = tmp_path / "runs" / f"x__codex__{cond}"
        (d / "workspace" / "out").mkdir(parents=True)
        (d / "workspace" / "out" / "draft.md").write_text(text)
        (d / "reply.md").write_text("")
        (d / "meta.json").write_text(json.dumps({"case": case["id"], "skill": case["skill"], "host": "codex",
                                                 "condition": cond, "skill_loaded": cond == "skill"}))
    results = grade.grade_run(tmp_path)
    total = results["summary"]["by"]["codex/ALL"]
    assert total["skill_pass"] == 1.0 and total["baseline_pass"] == 0.0 and total["delta"] == 1.0
    report = (tmp_path / "report.md").read_text()
    assert "+100 pts" in report and "anti-slop-editing/sample | codex | FAIL | PASS" in report


def test_host_errors_are_excluded_from_both_rates(tmp_path, monkeypatch):
    case = {**CASE, "checks": [{"type": "no_added_facts"}]}
    other = {**case, "id": "anti-slop-editing/other"}
    monkeypatch.setattr(grade, "load_cases", lambda patterns=None: [case, other])
    rows = [(case, "skill", "Latency fell from 40 ms to 12 ms.", None),
            (case, "baseline", "Latency fell from 40 ms to 3 ms.", None),
            (other, "skill", None, "exit 1: unrecognized model"),
            (other, "baseline", "Latency fell from 40 ms to 12 ms.", None)]
    for c, cond, text, error in rows:
        d = tmp_path / "runs" / f"{c['id'].replace('/', '__')}__claude__{cond}"
        (d / "workspace" / "out").mkdir(parents=True)
        if text is not None:
            (d / "workspace" / "out" / "draft.md").write_text(text)
        (d / "meta.json").write_text(json.dumps({"case": c["id"], "skill": c["skill"], "host": "claude",
                                                 "condition": cond, "skill_loaded": cond == "skill", "error": error}))
    total = grade.grade_run(tmp_path)["summary"]["by"]["claude/ALL"]
    assert (total["skill_n"], total["baseline_n"], total["errors"]) == (1, 1, 1)
    assert total["delta"] == 1.0
    assert "| ERROR |" in (tmp_path / "report.md").read_text()
