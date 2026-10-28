"""Tests for the controls mechanism (`grade.py --controls`). Run: uv run --with pytest python -m pytest tests/evals -q"""

import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
import grade  # noqa: E402

GOOD = "Latency fell from 40 ms to 12 ms. It did not fall on Monday."
SOURCE = "Latency fell from 40 ms to 12 ms. It did not fall on Monday."


def make_case(checks=None, controls=None, **extra):
    case = {
        "id": "anti-slop-editing/sample", "skill": "anti-slop-editing", "description": "sample",
        "prompt": "Clean up draft.md and save it to out/draft.md.",
        "files": {"draft.md": SOURCE}, "output": "out/draft.md",
        "checks": checks if checks is not None else [{"type": "preserves", "source": "draft.md"},
                                                     {"type": "not_contains", "values": ["synergy"]}],
        "_path": "evals/cases/anti-slop-editing/sample.json", **extra,
    }
    case["controls"] = controls if controls is not None else [
        {"name": "good", "expect": "pass", "output": GOOD, "reply": "Done."},
        {"name": "drops-negation", "expect": "fail", "fails": ["preserves"],
         "output": "Latency fell from 40 ms to 12 ms. It fell on Monday.", "reply": "Done."},
    ]
    return case


def errs(**kw):
    return grade.validate_case(make_case(**kw))


# ---------------------------------------------------------------- mechanism

def test_pass_control_passes_and_fail_control_is_caught():
    case = make_case()
    good, trap = (grade.grade_control(case, c) for c in case["controls"])
    assert good["ok"] and good["passed"] and good["failing"] == []
    assert trap["ok"] and not trap["passed"] and "preserves" in trap["failing"]


def test_fail_control_with_wrong_fails_type_is_reported():
    case = make_case()
    case["controls"][1]["fails"] = ["not_contains"]  # the trap trips preserves, not this one
    got = grade.grade_control(case, case["controls"][1])
    assert not got["ok"] and "not_contains" in got["problem"]


def test_fail_control_that_passes_and_pass_control_that_fails_are_reported():
    case = make_case()
    case["controls"][1]["output"] = GOOD
    assert "every check passed" in grade.grade_control(case, case["controls"][1])["problem"]
    case["controls"][0]["output"] = "Latency fell to 12 ms. It did not fall on Monday. The synergy was clear."
    got = grade.grade_control(case, case["controls"][0])
    assert not got["ok"] and "expected pass" in got["problem"]


def test_null_output_fails_output_present():
    case = make_case(controls=[
        {"name": "good", "expect": "pass", "output": GOOD, "reply": ""},
        {"name": "no-file", "expect": "fail", "fails": ["output_present"], "output": None, "reply": "Done."},
    ])
    got = grade.grade_control(case, case["controls"][1])
    assert got["ok"] and "output_present" in got["failing"]


def test_control_files_land_in_the_workspace_for_a_workspace_check():
    check = {"type": "html_deliverable", "path": "out/report.html", "no_script": True, "min_figures": 1}
    page = "<html><body><svg><text>a</text></svg></body></html>"
    case = make_case(checks=[check], controls=[
        {"name": "good", "expect": "pass", "output": GOOD, "reply": "", "files": {"out/report.html": page}},
        {"name": "scripted", "expect": "fail", "fails": ["html_deliverable"], "output": GOOD, "reply": "",
         "files": {"out/report.html": page.replace("<svg>", "<script>1</script><svg>")}},
        {"name": "absent", "expect": "fail", "fails": ["html_deliverable"], "output": GOOD, "reply": ""},
    ])
    assert all(grade.grade_control(case, c)["ok"] for c in case["controls"])


def test_open_questions_file_counts_as_reply_like_real_grading():
    check = {"type": "contains", "values": ["[ASK AUTHOR"], "target": "reply"}
    case = make_case(checks=[check], controls=[
        {"name": "good", "expect": "pass", "output": GOOD, "reply": "Done.",
         "files": {"out/open-questions.md": "[ASK AUTHOR: which quarter?]"}},
        {"name": "silent", "expect": "fail", "fails": ["contains"], "output": GOOD, "reply": "Done."},
    ])
    assert all(grade.grade_control(case, c)["ok"] for c in case["controls"])


def test_case_files_and_fixtures_are_in_the_control_workspace():
    case = make_case(checks=[{"type": "html_deliverable", "path": "draft.md"}], controls=[
        {"name": "good", "expect": "pass", "output": GOOD, "reply": ""},
        {"name": "bad", "expect": "fail", "fails": ["output_present"], "output": None, "reply": ""},
    ])
    assert grade.grade_control(case, case["controls"][0])["ok"]  # draft.md written from case["files"]
    fx = next(c for c in grade.load_cases() if c.get("fixtures"))
    ws = grade._control_workspace(fx, {"output": None})
    try:
        assert all((ws / p.relative_to(grade.fixture_root(fx))).is_file()
                   for p in grade.fixture_files(grade.fixture_root(fx)))
    finally:
        import shutil
        shutil.rmtree(ws, ignore_errors=True)


def test_run_controls_prints_a_line_per_control_and_exits_nonzero_on_mismatch(monkeypatch, capsys):
    case = make_case()
    monkeypatch.setattr(grade, "load_cases", lambda patterns=None: [case])
    assert grade.run_controls(["*"]) == 0
    out = capsys.readouterr().out
    assert "sample good expected=pass got=pass" in out
    assert "sample drops-negation expected=fail got=fail failing=preserves" in out
    assert "2 controls behave as expected" in out
    case["controls"][1]["fails"] = ["not_contains"]
    assert grade.run_controls(["*"]) == 1
    assert "[FAIL]" in capsys.readouterr().out


def test_cli_controls_flag_takes_an_optional_glob(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(grade, "run_controls", lambda patterns=None: seen.append(patterns) or 0)
    assert grade.main(["--controls"]) == 0 and grade.main(["--controls", "style/*"]) == 0
    assert seen == [["*"], ["style/*"]]


# ---------------------------------------------------------------- validation

def test_valid_controls_validate():
    assert errs() == []
    assert grade.validate_real_case(make_case()) == []


def test_validate_case_checks_shape_only_and_the_rule_is_for_real_cases():
    no_controls = make_case()
    no_controls.pop("controls")
    assert grade.validate_case(no_controls) == []
    assert any("required" in e for e in grade.validate_real_case(no_controls))
    only_pass = make_case()
    only_pass["controls"].pop(1)
    assert grade.validate_case(only_pass) == []
    assert any("'fail'" in e for e in grade.validate_real_case(only_pass))
    broken = make_case()
    broken["controls"][0]["expect"] = "maybe"
    assert any("expect must be" in e for e in grade.validate_case(broken))


@pytest.mark.parametrize("mutate, expected", [
    (lambda c: c.pop("controls"), "controls are required"),
    (lambda c: c.__setitem__("controls", []), "non-empty list"),
    (lambda c: c["controls"].pop(0), "at least one 'pass'"),
    (lambda c: c["controls"].pop(1), "at least one 'fail'"),
    (lambda c: c["controls"][1].__setitem__("name", "good"), "repeats"),
    (lambda c: c["controls"][0].__setitem__("expect", "maybe"), "expect must be"),
    (lambda c: c["controls"][1].pop("fails"), "needs `fails`"),
    (lambda c: c["controls"][1].__setitem__("fails", ["rhythm"]), "does not have"),
    (lambda c: c["controls"][0].__setitem__("fails", ["preserves"]), "must not set `fails`"),
    (lambda c: c["controls"][0].__setitem__("output", 5), "output must be"),
    (lambda c: c["controls"][0].pop("output"), "output must be"),
    (lambda c: c["controls"][0].__setitem__("reply", None), "reply must be"),
    (lambda c: c["controls"][0].__setitem__("files", {"../x": "t"}), "relative paths"),
    (lambda c: c["controls"][0].__setitem__("files", {"/abs": "t"}), "relative paths"),
    (lambda c: c["controls"][0].__setitem__("files", {"a.txt": 3}), "relative paths"),
    (lambda c: c["controls"][0].__setitem__("files", {"out/draft.md": "t"}), "case output"),
    (lambda c: c["controls"][0].__setitem__("extra", 1), "unknown fields"),
])
def test_validation_rejects_malformed_controls(mutate, expected):
    case = make_case()
    mutate(case)
    assert expected in " | ".join(grade.validate_real_case(case))


def test_fails_may_name_output_present():
    case = make_case()
    case["controls"][1].update(fails=["output_present"], output=None)
    assert grade.validate_real_case(case) == []


# ---------------------------------------------------------------- the real cases

def test_every_control_of_every_case_behaves(capsys):
    code = grade.run_controls(["*"])
    out = capsys.readouterr().out
    assert code == 0, out
