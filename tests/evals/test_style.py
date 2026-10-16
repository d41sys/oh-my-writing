"""Tests for the style track: slop_density and rhythm checks, marker stripping, and the two-verdict style judge.
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

PYCACHE = grade.SCRIPTS / "__pycache__"
PYCACHE_EXISTED = PYCACHE.exists()

CASE = {
    "id": "style/sample",
    "skill": "structured-drafting",
    "description": "sample",
    "prompt": "Write the email from notes.md and save it to out/email.md.",
    "files": {"notes.md": "Launch moves to 10 November. The fee stays at 4,800 EUR."},
    "output": "out/email.md",
    "checks": [],
}

SLOPPY = ("In today's fast-paced world, we are thrilled to announce a seamless, robust solution. "
          "It is important to note that the launch may potentially move.")
PLAIN = "The launch moves to 10 November. The fee stays at 4,800 EUR."
VARIED = ("The launch moves. It needs another full test pass, which takes four working days, and the fee does not "
          "change. Questions? Ask. We start on Tuesday and expect no further delay unless the fix fails in testing. "
          "Done.")
UNIFORM = ("The team met to discuss the plan for the next quarter of work. The group agreed on the main goals for the "
           "coming period ahead. The lead wrote down the key points from the whole discussion today. The notes were "
           "sent to every person who had joined the meeting. The plan will be reviewed again by the same group soon.")


def run_check(check, output, reply=""):
    return grade.grade_case({**CASE, "checks": [check]}, output, reply)["checks"][1]


# ---------------------------------------------------------------- slop_density

def test_slop_density_is_findings_per_thousand_words():
    result = run_check({"type": "slop_density", "max": 5}, SLOPPY)
    assert not result["passed"] and "per 1000" in result["detail"]
    assert run_check({"type": "slop_density", "max": 5}, PLAIN)["passed"]
    # the same text passes once the allowed density is high enough
    assert run_check({"type": "slop_density", "max": 500}, SLOPPY)["passed"]


def test_slop_density_scales_with_length_not_count():
    long_plain = " ".join([PLAIN] * 60)  # 1,000+ words around a single stock phrase: low density
    text = "In today's fast-paced world, we moved. " + long_plain
    result = run_check({"type": "slop_density", "max": 2}, text)
    assert result["passed"], result["detail"]
    assert not run_check({"type": "slop_density", "max": 2}, "In today's fast-paced world, we moved. " + PLAIN)["passed"]


def test_slop_density_fails_text_with_no_prose():
    result = run_check({"type": "slop_density", "max": 5}, "```\ncode only\n```\n")
    assert not result["passed"] and "no prose" in result["detail"]


def test_slop_density_honours_profile():
    chat = "Great question! Here is the answer."
    assert not run_check({"type": "slop_density", "max": 1, "profile": "casual"}, chat)["passed"]


def test_slop_scan_is_imported_without_writing_bytecode():
    assert run_check({"type": "slop_density", "max": 500}, SLOPPY)["passed"]
    assert not PYCACHE.exists() or PYCACHE_EXISTED
    assert sys.dont_write_bytecode is True  # restored to the caller's value


# ---------------------------------------------------------------- rhythm

def test_rhythm_fails_uniform_sentence_lengths_and_passes_varied_ones():
    bad = run_check({"type": "rhythm", "min_cv": 0.35}, UNIFORM)
    assert not bad["passed"] and "cv" in bad["detail"]
    assert run_check({"type": "rhythm", "min_cv": 0.35}, VARIED)["passed"]


def test_rhythm_is_not_judged_on_very_short_text():
    result = run_check({"type": "rhythm", "min_cv": 0.9}, "One short line. Another one.")
    assert result["passed"] and "not judged" in result["detail"]
    assert not run_check({"type": "rhythm", "min_cv": 0.9, "min_sentences": 2}, "One short line. Another one.")["passed"]


def test_rhythm_ignores_headings_lists_and_code():
    text = "# Heading with many many words in it\n\n- a list item with several words in it too\n\n" + VARIED
    assert grade.sentence_lengths(text) == grade.sentence_lengths(VARIED)


def test_validation_of_the_new_checks():
    def errs(check):
        return grade.validate_case({**CASE, "_path": "evals/cases/style/sample.json", "checks": [check]})
    assert errs({"type": "slop_density", "max": 5}) == []
    assert any("needs" in e for e in errs({"type": "slop_density"}))
    assert any("non-negative" in e for e in errs({"type": "slop_density", "max": -1}))
    assert any("profile" in e for e in errs({"type": "slop_density", "max": 3, "profile": "chatty"}))
    assert errs({"type": "rhythm"}) == [] and errs({"type": "rhythm", "min_cv": 0.4, "min_sentences": 6}) == []
    assert any("min_cv" in e for e in errs({"type": "rhythm", "min_cv": "high"}))
    assert any("min_sentences" in e for e in errs({"type": "rhythm", "min_sentences": 1}))


def test_judge_block_validation():
    def errs(judge, **extra):
        case = {**CASE, "_path": "evals/cases/style/sample.json", "checks": [{"type": "word_count", "min": 1}],
                "judge": judge, **extra}
        return grade.validate_case(case)
    assert errs({"mode": "style"}) == []
    assert any("render" in e for e in errs({"mode": "style", "render": "out/x.html"}))
    assert any("'visual' or 'style'" in e for e in errs({"mode": "loud"}))
    assert errs({"mode": "visual", "render": "out/x.html"}, deliverables=["out/email.md", "out/x.html"]) == []


# ---------------------------------------------------------------- marker stripping

def test_strip_markers_removes_inline_tokens_and_keeps_the_sentence():
    text = "The launch is on 3 November [VERIFY: date]. The fee is [ASK AUTHOR: amount] for the year."
    assert grade.strip_markers(text) == "The launch is on 3 November. The fee is for the year."


def test_strip_markers_drops_marker_lines_bullets_and_emptied_headings():
    text = ("# Update\n\nBody text here.\n\n- [ASK AUTHOR: who owns this?]\n- Real item\n\n"
            "## Questions for the author\n\n[ASK AUTHOR: x]\n[VERIFY: y]\n\n## Next\n\nDone.\n")
    assert grade.strip_markers(text) == "# Update\n\nBody text here.\n\n- Real item\n\n## Next\n\nDone.\n"


def test_strip_markers_handles_bold_wrapped_untested_and_markers_without_text():
    assert grade.strip_markers("Works on Linux **[UNTESTED]** and macOS.") == "Works on Linux and macOS."
    assert grade.strip_markers("[UNTESTED]\nRun it twice.") == "Run it twice."
    assert grade.strip_markers("[UNTESTED - not run on Windows]") == ""


def test_strip_markers_leaves_other_brackets_and_marker_free_text_alone():
    text = "See [1] and [the docs](https://example.com). A [VERIFYING step] is not a marker.\n\n  Indented.\n"
    assert grade.strip_markers(text) == text


def test_strip_markers_keeps_a_heading_that_still_has_content():
    text = "## Notes\n\nReal line.\n[VERIFY: y]\n"
    assert grade.strip_markers(text) == "## Notes\n\nReal line.\n"


# ---------------------------------------------------------------- style verdict parsing

def test_parse_style_verdicts_reads_the_last_line_per_question():
    reply = ("HUMAN: A is plainer.\nVERDICT HUMAN: B\nFAITHFUL: both ok\n"
             "VERDICT HUMAN: A\nVERDICT FAITHFUL: tie")
    assert run.parse_style_verdicts(reply) == {"human": "A", "faithful": "TIE"}
    assert run.parse_style_verdicts("verdict human: **b**\nVERDICT FAITHFUL : A") == {"human": "B", "faithful": "A"}


def test_parse_style_verdicts_leaves_out_a_question_without_a_verdict():
    assert run.parse_style_verdicts("VERDICT HUMAN: A\nVERDICT FAITHFUL: maybe") == {"human": "A"}
    assert run.parse_style_verdicts("VERDICT: A") == {}  # the single-verdict format is not a style answer


def test_combine_picks_over_both_orders():
    assert run.combine_picks(["skill", "skill"]) == "skill"
    assert run.combine_picks(["skill", "baseline"]) == "inconsistent"
    assert run.combine_picks(["skill", "tie"]) == "tie"
    assert run.combine_picks(["skill", "error"]) == "error"


# ---------------------------------------------------------------- style judging

def args(**kw):
    base = dict(repeat=1, resume=False, timeout=600, seed=7, judge="codex", codex_model=None, codex_effort=None,
                claude_model=None, judge_mode="auto")
    return argparse.Namespace(**{**base, **kw})


def make_runs(case, run_dir, texts):
    for cond, text in texts.items():
        ws = run_dir / "runs" / run.slug_of(case, "codex", cond, 1, 1) / "workspace" / "out"
        ws.mkdir(parents=True)
        (ws / "email.md").write_text(text)


MARKED = {"skill": "Hi Marta,\n\nLaunch is 10 November.\n\n[ASK AUTHOR: who signs off?]\n",
          "baseline": "Hi Marta,\n\nLaunch is on 10 November [VERIFY: date].\n"}


def test_style_judge_strips_markers_from_both_texts_and_stores_two_verdicts(tmp_path, monkeypatch):
    case = {**CASE, "judge": {"mode": "style"}}
    make_runs(case, tmp_path, MARKED)
    seen = []

    def judge_once(case_, a, b, host, run_dir, tag, a_args, shots=None, shot_note=""):
        seen.append((a, b))
        a_is_skill = a.startswith("Hi Marta,\n\nLaunch is 10 November.")
        # the skill text reads more human but is less faithful, whichever side it is on
        return "STYLE", "reasons", {"human": "A" if a_is_skill else "B", "faithful": "B" if a_is_skill else "A"}

    monkeypatch.setattr(run, "judge_once", judge_once)
    entry = run.judge_pair(case, "codex", 1, tmp_path, args())
    assert all("[" not in t and "ASK AUTHOR" not in t and "VERIFY" not in t for pair in seen for t in pair)
    assert entry["mode"] == "style" and entry["human"] == "skill" and entry["faithful"] == "baseline"
    assert entry["winner"] == "style"
    assert set(entry["picks"]) == {"human", "faithful"} and all(len(v) == 2 for v in entry["picks"].values())
    assert "visual" not in entry and "scores" not in entry
    assert len(seen) == 2  # both presentation orders


def test_style_judge_reports_inconsistent_and_error_per_question(tmp_path, monkeypatch):
    case = {**CASE, "judge": {"mode": "style"}}
    make_runs(case, tmp_path, MARKED)
    replies = iter([("STYLE", "r", {"human": "A", "faithful": "TIE"}), ("STYLE", "r", {"human": "A", "faithful": "B"})])
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: next(replies))
    entry = run.judge_pair(case, "codex", 1, tmp_path, args())
    # "A" in both orders means two different conditions won: inconsistent. TIE then a side: tie.
    assert entry["human"] == "inconsistent" and entry["faithful"] == "tie"
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: ("ERROR", "", {"human": "A"}))
    entry = run.judge_pair(case, "codex", 1, tmp_path, args())
    assert entry["winner"] == "error" and entry["faithful"] == "error"


def test_judge_mode_flag_applies_style_to_every_case(tmp_path, monkeypatch):
    plain = dict(CASE)  # no judge block
    make_runs(plain, tmp_path, MARKED)
    assert run.judge_mode(plain, args()) == "text"
    assert run.judge_mode(plain, args(judge_mode="style")) == "style"
    assert run.judge_mode({**plain, "judge": {"mode": "visual", "render": "out/r.html"}}, args()) == "visual"
    assert run.judge_mode({**plain, "judge": {"mode": "visual", "render": "out/r.html"}},
                          args(judge_mode="style")) == "style"
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: ("STYLE", "r", {"human": "TIE", "faithful": "TIE"}))
    entry = run.judge_pair(plain, "codex", 1, tmp_path, args(judge_mode="style"))
    assert entry["mode"] == "style" and entry["human"] == "tie"
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: ("A", "r", {}))
    assert "mode" not in run.judge_pair(plain, "codex", 1, tmp_path, args())


def test_text_judge_still_sees_markers(tmp_path, monkeypatch):
    make_runs(CASE, tmp_path, MARKED)
    seen = []
    monkeypatch.setattr(run, "judge_once", lambda c, a, b, *r, **k: seen.append((a, b)) or ("A", "r", {}))
    run.judge_pair(CASE, "codex", 1, tmp_path, args())
    assert any("ASK AUTHOR" in t for pair in seen for t in pair)


def test_judge_once_style_prompt_asks_two_questions_and_parses_both(tmp_path, monkeypatch):
    prompts = []

    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None):
        prompts.append(prompt)
        (out_dir / "reply.md").write_text("HUMAN reasons.\nFAITHFUL reasons.\nVERDICT HUMAN: B\nVERDICT FAITHFUL: TIE")
        return {"log": "", "exit_code": 0, "error": None, "duration_s": 0.1}

    monkeypatch.setattr(run, "execute", execute)
    case = {**CASE, "judge": {"mode": "style"}}
    verdict, reply, extra = run.judge_once(case, "text A", "text B", "codex", tmp_path, "t", args())
    assert verdict == "STYLE" and extra == {"human": "B", "faithful": "TIE"}
    prompt = prompts[0]
    for expected in ("Question 1, HUMAN", "Question 2, FAITHFUL", "skilled human professional", "fewer AI tells",
                     "hedging fog", "symmetric lists", "openers", "more faithful to the input",
                     "VERDICT HUMAN:", "VERDICT FAITHFUL:", "text A", "text B", "Launch moves to 10 November"):
        assert expected in prompt, expected
    # a reply without both verdicts is an error, not a guess
    monkeypatch.setattr(run, "execute", lambda host, prompt, ws, out_dir, a, **k: (
        (out_dir / "reply.md").write_text("VERDICT HUMAN: A\n"), {"log": "", "exit_code": 0, "error": None, "duration_s": 0})[1])
    assert run.judge_once(case, "a", "b", "codex", tmp_path, "t2", args())[0] == "ERROR"


# ---------------------------------------------------------------- reporting

def test_summary_and_report_keep_the_two_style_verdicts_apart(tmp_path, monkeypatch):
    case = {**CASE, "checks": [{"type": "word_count", "min": 1}]}
    monkeypatch.setattr(grade, "load_cases", lambda patterns=None: [case])
    for cond in ("skill", "baseline"):
        d = tmp_path / "runs" / f"style__sample__codex__{cond}"
        (d / "workspace" / "out").mkdir(parents=True)
        (d / "workspace" / "out" / "email.md").write_text("x y z")
        (d / "meta.json").write_text(json.dumps({"case": case["id"], "skill": case["skill"], "host": "codex",
                                                 "condition": cond, "skill_loaded": cond == "skill"}))
    judge = [
        {"case": "style/sample", "host": "codex", "rep": 1, "judge": "codex", "mode": "style", "winner": "style",
         "human": "skill", "faithful": "baseline", "reason": "plainer / but dropped a figure"},
        {"case": "style/other", "host": "codex", "rep": 1, "judge": "codex", "mode": "style", "winner": "style",
         "human": "skill", "faithful": "tie", "reason": "r"},
        {"case": "style/third", "host": "codex", "rep": 1, "judge": "codex", "mode": "style", "winner": "error"},
        {"case": "x/plain", "host": "codex", "rep": 1, "judge": "codex", "winner": "baseline", "picks": [], "reason": "r"},
    ]
    (tmp_path / "judge.json").write_text(json.dumps(judge))
    summary = grade.grade_run(tmp_path)["summary"]
    assert summary["judge"]["baseline"] == 1 and summary["judge"]["skill"] == 0  # style entries stay out of the tally
    style = summary["judge_style"]
    assert style["human"]["skill"] == 2 and style["human"]["error"] == 1
    assert style["faithful"]["baseline"] == 1 and style["faithful"]["tie"] == 1 and style["faithful"]["error"] == 1
    report = (tmp_path / "report.md").read_text()
    assert "## Blind style judge" in report and "| reads human | faithful |" in report
    assert "| style/sample | codex | 1 | codex | skill | baseline |" in report
    assert "## Blind pairwise judge" in report  # the plain pair keeps its own section


def test_report_has_no_style_section_without_style_verdicts(tmp_path, monkeypatch):
    summary = grade.summarize([], [{"case": "a/b", "host": "codex", "rep": 1, "judge": "codex", "winner": "tie"}])
    assert summary["judge_style"] == {}
    report = grade.render_report({"run": {}, "runs": [], "judge": [{"case": "a/b", "host": "codex", "rep": 1,
                                                                      "judge": "codex", "winner": "tie"}],
                                  "summary": summary})
    assert "Blind style judge" not in report


# ---------------------------------------------------------------- the case files

STYLE_CASES = grade.load_cases(["style/*"])


def test_the_style_track_has_about_eight_cases_on_existing_skills():
    assert 8 <= len(STYLE_CASES) <= 10
    assert {c["skill"] for c in STYLE_CASES} <= {p.name for p in grade.SKILLS_DIR.iterdir() if p.is_dir()}


@pytest.mark.parametrize("case", STYLE_CASES, ids=lambda c: c["id"])
def test_every_style_case_measures_slop_register_and_gap_markers(case):
    kinds = [c["type"] for c in case["checks"]]
    assert "slop_density" in kinds and "rhythm" in kinds and "word_count" in kinds and "no_added_facts" in kinds
    marker_checks = [c for c in case["checks"] if c["type"] == "markers"]
    assert any(c.get("max") == 0 and c.get("target") == "output" for c in marker_checks), \
        "a reader-facing deliverable must contain no gap markers"
    for c in case["checks"]:
        if c["type"] == "slop_density":
            assert 0 < c["max"] <= 10
    assert case["skill"] not in case["prompt"]
