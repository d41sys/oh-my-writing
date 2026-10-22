"""Tests for the reader judge: three-axis verdict parsing, case validation, the judge-model override, reporting.
Run: uv run --with pytest python -m pytest tests/evals -q"""

import argparse
import json
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import grade  # noqa: E402
import run  # noqa: E402

CASE = {
    "id": "reader/sample",
    "skill": "post-writing",
    "description": "sample",
    "prompt": "Write the update from notes.md in the style of example.md and save it to out/update.md.",
    "files": {"notes.md": "Launch moves to 10 November.", "example.md": "We moved the launch. Here is why."},
    "output": "out/update.md",
    "checks": [{"type": "word_count", "min": 1}],
    "judge": {"mode": "reader"},
    "style_ref": "example.md",
}
READER_REPLY = "FIT: A\nFLOW: B\nFAITHFUL: tie\nVERDICT FIT: A\nVERDICT FLOW: B\nVERDICT FAITHFUL: TIE"


def args(**kw):
    base = dict(repeat=1, resume=False, timeout=600, seed=7, judge="codex", codex_model=None, codex_effort=None,
                claude_model=None, judge_mode="auto", omp_model="writer-model", omp_thinking=None,
                judge_omp_model=None)
    return argparse.Namespace(**{**base, **kw})


def make_runs(case, run_dir, texts):
    for cond, text in texts.items():
        ws = run_dir / "runs" / run.slug_of(case, "codex", cond, 1, 1) / "workspace" / "out"
        ws.mkdir(parents=True)
        (ws / "update.md").write_text(text)


# ---------------------------------------------------------------- parsing

def test_parse_reader_verdicts_reads_three_axes_and_the_last_line_of_each():
    reply = "VERDICT FIT: B\nlater thought\nverdict fit: **a**\nVERDICT FLOW : TIE\nVERDICT FAITHFUL: B"
    assert run.parse_style_verdicts(reply, run.JUDGE_AXES["reader"]) == {"fit": "A", "flow": "TIE", "faithful": "B"}


def test_parse_reader_verdicts_leaves_out_a_missing_or_invalid_axis():
    axes = run.JUDGE_AXES["reader"]
    assert run.parse_style_verdicts("VERDICT FIT: A\nVERDICT FAITHFUL: B", axes) == {"fit": "A", "faithful": "B"}
    assert run.parse_style_verdicts("VERDICT FIT: A\nVERDICT FLOW: maybe\nVERDICT FAITHFUL: B", axes) == {
        "fit": "A", "faithful": "B"}
    # the style default is unchanged
    assert run.parse_style_verdicts("VERDICT HUMAN: A\nVERDICT FAITHFUL: B") == {"human": "A", "faithful": "B"}


def execute_returning(reply, seen=None):
    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None, omp_model=None):
        if seen is not None:
            seen.append((host, omp_model))
        (out_dir / "reply.md").write_text(reply)
        return {"log": "", "exit_code": 0, "error": None, "duration_s": 0.1}
    return execute


def test_judge_once_reader_returns_the_three_verdicts_and_errors_on_a_missing_one(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "execute", execute_returning(READER_REPLY))
    verdict, _, extra = run.judge_once(CASE, "text A", "text B", "codex", tmp_path, "t", args())
    assert verdict == "READER" and extra == {"fit": "A", "flow": "B", "faithful": "TIE"}
    monkeypatch.setattr(run, "execute", execute_returning("VERDICT FIT: A\nVERDICT FAITHFUL: B"))
    verdict, _, extra = run.judge_once(CASE, "a", "b", "codex", tmp_path, "t2", args())
    assert verdict == "ERROR" and "flow" not in extra


def test_reader_prompt_carries_the_style_reference_only_when_the_case_names_one(tmp_path, monkeypatch):
    prompts = []
    monkeypatch.setattr(run, "execute", lambda host, prompt, *a, **k: (
        prompts.append(prompt), execute_returning(READER_REPLY)(host, prompt, *a, **k))[1])
    run.judge_once(CASE, "text A", "text B", "codex", tmp_path, "t", args())
    run.judge_once({k: v for k, v in CASE.items() if k != "style_ref"}, "text A", "text B", "codex", tmp_path, "t2", args())
    assert "example.md" in prompts[0] and "style" in prompts[0] and "We moved the launch." in prompts[0]
    assert "No style reference was given" in prompts[1] and "text A" in prompts[1] and "text B" in prompts[1]


# ---------------------------------------------------------------- judge_pair

def test_judge_pair_stores_three_verdicts_combined_over_both_orders(tmp_path, monkeypatch):
    make_runs(CASE, tmp_path, {"skill": "Short story.\n\n[VERIFY: date]\n", "baseline": "Long list."})
    seen = []

    def judge_once(case, a, b, host, run_dir, tag, a_args, shots=None, shot_note=""):
        seen.append((a, b))
        skill_is_a = a.startswith("Short story.")
        # skill wins fit and flow in whichever slot it is; faithfulness is split by slot, so the orders disagree
        return "READER", "reasons", {"fit": "A" if skill_is_a else "B", "flow": "A" if skill_is_a else "B",
                                     "faithful": "A"}

    monkeypatch.setattr(run, "judge_once", judge_once)
    entry = run.judge_pair(CASE, "codex", 1, tmp_path, args())
    assert all("VERIFY" not in t for pair in seen for t in pair)
    assert entry["mode"] == "reader" and entry["winner"] == "reader"
    assert entry["fit"] == "skill" and entry["flow"] == "skill" and entry["faithful"] == "inconsistent"
    assert set(entry["picks"]) == {"fit", "flow", "faithful"} and all(len(v) == 2 for v in entry["picks"].values())


def test_judge_mode_flag_forces_reader_on_every_case(tmp_path, monkeypatch):
    plain = {k: v for k, v in CASE.items() if k not in ("judge", "style_ref")}
    make_runs(plain, tmp_path, {"skill": "a", "baseline": "b"})
    assert run.judge_mode(plain, args()) == "text"
    assert run.judge_mode(plain, args(judge_mode="reader")) == "reader"
    assert run.judge_mode(CASE, args()) == "reader" and run.judge_mode(CASE, args(judge_mode="style")) == "style"
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: ("READER", "r", {"fit": "TIE", "flow": "TIE", "faithful": "TIE"}))
    entry = run.judge_pair(plain, "codex", 1, tmp_path, args(judge_mode="reader"))
    assert entry["mode"] == "reader" and entry["flow"] == "tie"


def test_judge_pair_marks_an_entry_with_a_missing_axis_as_error(tmp_path, monkeypatch):
    make_runs(CASE, tmp_path, {"skill": "a", "baseline": "b"})
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: ("ERROR", "", {"fit": "A", "faithful": "A"}))
    entry = run.judge_pair(CASE, "codex", 1, tmp_path, args())
    assert entry["winner"] == "error" and entry["flow"] == "error" and entry["fit"] != "error"


# ---------------------------------------------------------------- validation

def test_reader_mode_and_style_ref_validation():
    def errs(**extra):
        case = {**CASE, "_path": "evals/cases/reader/sample.json", **extra}
        return grade.validate_case(case)
    assert errs() == []
    assert any("render" in e for e in errs(judge={"mode": "reader", "render": "out/x.html"}))
    assert any("style_ref" in e for e in errs(style_ref="missing.md"))
    assert any("style_ref" in e for e in errs(style_ref=["example.md"]))
    assert errs(judge={"mode": "reader"}, style_ref="notes.md") == []


# ---------------------------------------------------------------- judge model

def test_omp_command_uses_the_model_it_is_given_else_the_writer_model():
    a = args()
    cmd = run.host_command("omp", "p", Path("."), Path("r"), a)
    assert cmd[cmd.index("--model") + 1] == "writer-model"
    cmd = run.host_command("omp", "p", Path("."), Path("r"), a, omp_model="judge-model")
    assert cmd[cmd.index("--model") + 1] == "judge-model"
    assert a.omp_model == "writer-model"  # the shared args are not touched


def test_judge_once_passes_the_judge_model_to_omp_calls_and_defaults_to_the_writer_model(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(run, "execute", execute_returning(READER_REPLY, seen))
    run.judge_once(CASE, "a", "b", "omp", tmp_path, "t1", args(judge_omp_model="judge-model"))
    run.judge_once(CASE, "a", "b", "omp", tmp_path, "t2", args())
    run.judge_once(CASE, "a", "b", "codex", tmp_path, "t3", args(judge_omp_model="judge-model"))
    assert seen == [("omp", "judge-model"), ("omp", "writer-model"), ("codex", None)]


class FakeProc:
    returncode = 0
    stderr = ""

    def __init__(self, stdout):
        self.stdout = stdout


@pytest.mark.parametrize("log_model,expect_error", [("judge-model", False), ("writer-model", True)])
def test_fallback_check_compares_with_the_model_the_call_requested(tmp_path, monkeypatch, log_model, expect_error):
    monkeypatch.setattr(run.subprocess, "run", lambda *a, **k: FakeProc(f'{{"model": "x/{log_model}:high"}}'))
    out = tmp_path / "out"
    out.mkdir()
    result = run.execute("omp", "p", tmp_path, out, args(), omp_model="judge-model")
    assert bool(result["error"]) is expect_error
    assert (not expect_error) or result["error"] == "model fallback: x/writer-model:high"
    # without an override the writer model is what is expected
    result = run.execute("omp", "p", tmp_path, out, args())
    assert bool(result["error"]) is (log_model == "judge-model")


# ---------------------------------------------------------------- reporting

def entry(case, fit, flow, faithful, pair=None):
    row = {"case": case, "host": "codex", "rep": 1, "judge": "codex", "mode": "reader", "winner": "reader",
           "fit": fit, "flow": flow, "faithful": faithful, "picks": {}, "reason": "r"}
    return {**row, "pair": pair} if pair else row


def test_summary_and_report_tally_reader_verdicts_per_axis(tmp_path):
    judge = [entry("reader/a", "skill", "baseline", "tie"), entry("reader/b", "skill", "inconsistent", "skill"),
             {"case": "reader/c", "host": "codex", "rep": 1, "judge": "codex", "mode": "reader", "winner": "error"},
             {"case": "x/plain", "host": "codex", "rep": 1, "judge": "codex", "winner": "baseline", "picks": []}]
    summary = grade.summarize([], judge)
    reader = summary["judge_reader"]
    assert reader["fit"]["skill"] == 2 and reader["fit"]["error"] == 1
    assert reader["flow"]["baseline"] == 1 and reader["flow"]["inconsistent"] == 1 and reader["flow"]["error"] == 1
    assert reader["faithful"]["tie"] == 1 and reader["faithful"]["skill"] == 1
    assert summary["judge"]["baseline"] == 1 and summary["judge"]["skill"] == 0  # reader entries stay out of the tally
    assert summary["judge_style"] == {}
    report = grade.render_report({"run": {}, "runs": [], "judge": judge, "summary": summary})
    assert "## Blind reader judge" in report and "| fit | flow | faithful |" in report
    assert "| reader/a | codex | 1 | codex | skill | baseline | tie | r |" in report
    assert "## Blind pairwise judge" in report and "Blind style judge" not in report


def test_report_has_no_reader_section_without_reader_verdicts():
    summary = grade.summarize([], [{"case": "a/b", "host": "codex", "rep": 1, "judge": "codex", "winner": "tie"}])
    assert summary["judge_reader"] == {}
    judge = [{"case": "a/b", "host": "codex", "rep": 1, "judge": "codex", "winner": "tie"}]
    assert "Blind reader judge" not in grade.render_report({"run": {}, "runs": [], "judge": judge, "summary": summary})


def test_reader_entries_of_another_pair_get_their_own_table():
    judge = [entry("reader/a", "competitor-x", "skill", "tie", pair="skill:competitor-x")]
    summary = grade.summarize([], judge)
    info = summary["judge_pairs"]["skill:competitor-x"]
    assert info["reader"]["fit"]["competitor-x"] == 1 and info["reader"]["flow"]["skill"] == 1
    report = grade.render_report({"run": {}, "runs": [], "judge": judge, "summary": summary})
    assert "## Blind judge: skill vs competitor-x" in report
    assert "| reader/a | codex | 1 | codex | competitor-x | skill | tie | r |" in report
