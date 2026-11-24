"""Tests for the benchmark runner's workspace, repetition and judging plumbing (no agent is started)."""

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

BLOB = bytes(range(256)) * 4


@pytest.fixture
def case(tmp_path, monkeypatch):
    fixtures = tmp_path / "fixtures" / "sample"
    (fixtures / "docs").mkdir(parents=True)
    (fixtures / "docs" / "report.pdf").write_bytes(BLOB)
    (fixtures / "docs" / "notes.txt").write_text("Budget 100.\n")
    skill = tmp_path / "skills" / "demo"
    (skill / "scripts" / "__pycache__").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: demo\n---\n")
    (skill / "scripts" / "tool.py").write_text("print(1)\n")
    (skill / "scripts" / "__pycache__" / "tool.pyc").write_bytes(b"x")
    monkeypatch.setattr(run, "SKILLS", [skill])
    return {"id": "project-report/sample", "skill": "project-report", "prompt": "Save to out/report.md.",
            "files": {"extra/in.txt": "inline"}, "fixtures": str(fixtures), "output": "out/report.md",
            "deliverables": ["out/report.md", "out/report.html"], "checks": [{"type": "word_count", "min": 1}]}


def args(**kw):
    base = dict(repeat=1, resume=False, timeout=600, seed=7, judge="codex", codex_model=None, codex_effort=None,
                claude_model=None)
    return argparse.Namespace(**{**base, **kw})


def test_workspace_copies_fixtures_and_skills_without_links(case):
    ws = run.make_workspace(case, "codex", "skill")
    try:
        assert (ws / "docs" / "report.pdf").read_bytes() == BLOB
        assert (ws / "docs" / "notes.txt").read_text() == "Budget 100.\n"
        assert (ws / "extra" / "in.txt").read_text() == "inline"
        assert (ws / "out").is_dir()
        assert (ws / ".agents" / "skills" / "demo" / "scripts" / "tool.py").read_text() == "print(1)\n"
        assert not (ws / ".agents" / "skills" / "demo" / "scripts" / "__pycache__").exists()
        assert not any(p.is_symlink() for p in ws.rglob("*"))
        (ws / ".agents" / "skills" / "demo" / "SKILL.md").write_text("changed")
        assert "changed" not in (run.SKILLS[0] / "SKILL.md").read_text()  # no write-through to the source
    finally:
        import shutil
        shutil.rmtree(ws)


def test_baseline_workspace_has_no_skills(case):
    ws = run.make_workspace(case, "claude", "baseline")
    try:
        assert not (ws / ".claude").exists() and not (ws / ".agents").exists()
        assert (ws / "docs" / "report.pdf").is_file()
    finally:
        import shutil
        shutil.rmtree(ws)


def test_slug_gets_a_rep_suffix_only_when_repeating(case):
    assert run.slug_of(case, "codex", "skill", 1, 1) == "project-report__sample__codex__skill"
    assert run.slug_of(case, "codex", "skill", 2, 3) == "project-report__sample__codex__skill__r2"


def fake_execute(seen):
    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None):
        seen.append({"host": host, "timeout": timeout, "ws": ws})
        (ws / "out").mkdir(exist_ok=True)
        (ws / "out" / "report.md").write_text(f"report from {out_dir.name}")
        (ws / "out" / "report.html").write_text(f"<p>{out_dir.name}</p>")
        (out_dir / "reply.md").write_text("done")
        return {"log": "", "exit_code": 0, "error": None, "duration_s": 0.1}
    return execute


def test_run_one_uses_case_timeout_rep_slug_and_resume(case, tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(run, "execute", fake_execute(seen))
    run_dir = tmp_path / "results"
    a = args(repeat=2)
    meta = run.run_one({**case, "timeout": 2400}, "codex", "skill", 2, run_dir, a)
    assert meta["rep"] == 2 and meta["timeout"] == 2400 and seen[0]["timeout"] == 2400
    out = run_dir / "runs" / "project-report__sample__codex__skill__r2"
    assert (out / "workspace" / "out" / "report.html").is_file()
    assert not (out / "workspace" / ".agents").exists() and (out / "workspace" / "docs" / "report.pdf").is_file()
    assert json.loads((out / "meta.json").read_text())["rep"] == 2
    run.run_one(case, "codex", "baseline", 1, run_dir, args(repeat=2))
    assert seen[1]["timeout"] == 600  # no case timeout: the command-line value
    again = run.run_one(case, "codex", "skill", 2, run_dir, args(repeat=2, resume=True))
    assert again["rep"] == 2 and len(seen) == 2  # finished run reused, not executed again
    assert not Path(seen[0]["ws"]).exists()  # temporary workspace removed


def test_host_error_reads_omp_error_fields_and_spots_provider_limits():
    capacity = ('{"type":"message_end","stopReason":"error","errorMessage":"503 No available channel for model '
                'gpt-5.6-luna under group auto (distributor)"}\n')
    rate = '{"stopReason":"error","errorMessage":"Cloud Code Assist API error (429): {\\n  \\"error\\": 1}"}\n'
    crash = '{"stopReason":"error","errorMessage":"Request was aborted"}\n'
    other_crash = '{"stopReason":"error","errorMessage":"Tool failed"}\n'
    event = '{"type": "error", "message": "You have hit your usage limit"}\n'
    for log in (capacity, rate, event):
        assert run.host_error(log, "")[1]
    # the fallback chain ends with a generic error after the refusal: the refusal still counts and is the one kept
    assert run.host_error(rate + crash, "") == (run.host_error(rate, "")[0], True)
    assert run.host_error(rate, "")[0].startswith("Cloud Code Assist API error (429)")
    assert run.host_error(crash + other_crash, "") == ("Tool failed", False)  # no refusal: the last error
    assert run.host_error('{"errorMessage":""}\n', "Boom\n") == ("Boom", False)  # an empty field is not a message
    assert run.host_error("no json here", "Traceback ...\nBoom\n") == ("Traceback ...\nBoom", False)


def test_only_the_requested_models_refusal_stops_the_host():
    def err(model, text):
        return '{"type":"message_end","message":{"model":"%s","stopReason":"error","errorMessage":"%s"}}\n' % (model, text)

    def retry(text):  # omp's auto_retry_start repeats the last error without naming a model
        return '{"type":"auto_retry_start","errorMessage":"%s"}\n' % text

    # gpt-6-sol drops a connection; omp falls back to models that refuse: a plain host error, not a quota stop
    dropped = err("gpt-6-sol", "ECONNRESET: socket closed") + err("gpt-5.6-luna", "503 No available channel") + \
        retry("503 No available channel") + err("gemini-3.8-flash", "Cloud Code Assist API error (429)")
    assert run.host_error(dropped, "", "gpt-6-sol") == ("ECONNRESET: socket closed", False)
    # the requested model's own usage limit stops it, named with or without a provider prefix, retried or not
    limited = err("gpt-6-sol", "You have hit your ChatGPT usage limit") + err("gpt-5.6-luna", "503 No available channel")
    assert run.host_error(limited, "", "openai/gpt-6-sol") == ("You have hit your ChatGPT usage limit", True)
    assert run.host_error(retry("You have hit your usage limit"), "", "gpt-6-sol")[1]  # before any model is named
    # without a requested model (codex, claude) every refusal counts, as before
    assert run.host_error(dropped, "")[1]


def test_parse_scores_keeps_known_criteria_in_range():
    reply = ("reasons\nSCORES A: accuracy=4 needs=3 tone=5 diagrams=2 layout=4\n"
             "SCORES B: accuracy=2 needs=9 bogus=3 tone=3\nVERDICT: A")
    scores = run.parse_scores(reply)
    assert scores["A"] == {"accuracy": 4, "needs": 3, "tone": 5, "diagrams": 2, "layout": 4}
    assert scores["B"] == {"accuracy": 2, "tone": 3}
    assert run.parse_scores("VERDICT: TIE") == {}


def test_diagram_design_version_comes_from_metadata(tmp_path, monkeypatch):
    (tmp_path / "SKILL.md").write_text('---\nname: diagram-design\nmetadata:\n  version: "2.6"\n---\n# x\n')
    monkeypatch.setattr(grade, "DIAGRAM_SKILL", tmp_path)
    assert run.diagram_design_version() == "2.6"
    monkeypatch.setattr(grade, "DIAGRAM_SKILL", tmp_path / "missing")
    assert run.diagram_design_version() is None


def make_runs(case, run_dir, reps):
    for rep in reps:
        for cond in ("skill", "baseline"):
            ws = run_dir / "runs" / run.slug_of(case, "codex", cond, rep, 2) / "workspace" / "out"
            ws.mkdir(parents=True)
            (ws / "report.md").write_text(f"{cond} text rep {rep}")
            (ws / "report.html").write_text(f"<p>{cond}</p>")


def test_judge_pairs_each_rep_and_stores_visual_scores(case, tmp_path, monkeypatch):
    case = {**case, "judge": {"mode": "visual", "render": "out/report.html"}}
    make_runs(case, tmp_path, [1, 2])
    png = tmp_path / "p.png"
    png.write_bytes(b"png")
    monkeypatch.setattr(run, "render_pages", lambda html, dest, prefix, **kw: ([png], None))
    calls = []

    def judge_once(case_, a, b, host, run_dir, tag, a_args, shots=None, shot_note="", figures=None):
        calls.append((tag, a, b, shots is not None))
        # order 1 and 2 swap sides; the skill report always gets the higher scores
        a_is_skill = a.startswith("skill")
        return ("A" if a_is_skill else "B"), "ok", {"A": {"accuracy": 5 if a_is_skill else 3},
                                                    "B": {"accuracy": 3 if a_is_skill else 5}}

    monkeypatch.setattr(run, "judge_once", judge_once)
    a = args(repeat=2)
    entries = [run.judge_pair(case, "codex", rep, tmp_path, a) for rep in (1, 2)]
    assert [e["rep"] for e in entries] == [1, 2]
    assert all(e["winner"] == "skill" and e["visual"] for e in entries)
    assert entries[0]["scores"] == {"skill": {"accuracy": 5}, "baseline": {"accuracy": 3}}
    assert len(calls) == 4 and {c[0].split("__")[1] for c in calls} == {"r1", "r2"}
    assert all(c[3] for c in calls)
    texts = {c[1][:8] for c in calls} | {c[2][:8] for c in calls}
    assert texts == {"skill te", "baseline"}


def test_visual_judge_falls_back_to_text_when_rendering_fails(case, tmp_path, monkeypatch):
    case = {**case, "judge": {"mode": "visual", "render": "out/report.html"}}
    make_runs(case, tmp_path, [1, 2])
    monkeypatch.setattr(run, "render_pages", lambda *a, **k: ([], "Chrome not found"))
    seen = []
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: seen.append((k["shots"], k["shot_note"])) or ("TIE", "", {}))
    entry = run.judge_pair(case, "codex", 1, tmp_path, args(repeat=2))
    assert entry["winner"] == "tie" and entry["visual"] is False and "Chrome not found" in entry["render_note"]
    assert seen[0][0] is None and "Chrome not found" in seen[0][1]


def test_text_judge_entry_has_no_visual_fields(case, tmp_path, monkeypatch):
    make_runs(case, tmp_path, [1, 2])
    monkeypatch.setattr(run, "judge_once", lambda *a, **k: ("A", "r", {}))
    entry = run.judge_pair(case, "codex", 2, tmp_path, args(repeat=2))
    assert entry["rep"] == 2 and "visual" not in entry and "scores" not in entry


def test_text_judge_shows_the_figure_files_a_report_links(case, tmp_path, monkeypatch):
    case = {k: v for k, v in case.items() if k != "fixtures"}
    make_runs(case, tmp_path, [1])
    out = tmp_path / "runs" / run.slug_of(case, "codex", "skill", 1, 2) / "workspace" / "out"
    (out / "diagrams").mkdir()
    (out / "diagrams" / "s.svg").write_text("<svg/>")
    (out / "photo.png").write_bytes(b"png")
    (tmp_path / "outside.png").write_bytes(b"png")
    (out / "report.md").write_text(
        "skill text\n![Schedule](diagrams/s.svg)\n![remote](https://example.org/a.png)\n"
        "![outside](../../../../outside.png)\n![gone](missing.svg)\n![again](diagrams/s.svg \"title\")\n"
        "![photo](<photo.png>)\n[a link, not an image](diagrams/s.svg)\n")
    # only local, existing files inside the workspace, shown as images, once each, in reading order
    assert run.linked_figures(case, out.parent) == [(out / "diagrams" / "s.svg").resolve(), (out / "photo.png").resolve()]

    rendered = tmp_path / "rendered.png"
    rendered.write_bytes(b"png")
    monkeypatch.setattr(run, "render_pages", lambda html, dest, prefix, **kw: ([rendered], None))
    seen = []

    def execute(host, prompt, ws, out_dir, a, read_only=False, timeout=None, images=None, **kw):
        seen.append((prompt, [p.name for p in images or []]))
        (out_dir / "reply.md").write_text("VERDICT: TIE")
        return {"log": "", "exit_code": 0, "error": None, "duration_s": 0}

    monkeypatch.setattr(run, "execute", execute)
    entry = run.judge_pair(case, "codex", 1, tmp_path, args(repeat=2))
    assert entry["winner"] == "tie" and len(seen) == 2
    for prompt, images in seen:
        assert sorted(images) == ["A-fig1.png", "A-fig2.png"] or sorted(images) == ["B-fig1.png", "B-fig2.png"]
        side = images[0][0]
        other = "B" if side == "A" else "A"
        assert f"Response {other}: links no figure file" in prompt
        # the figures are listed before the judging instructions, which still end the prompt
        assert prompt.index(f"Response {side}: {side}-fig1.png") < prompt.index("Judge which response")
        assert prompt.rstrip().endswith("VERDICT: TIE")

    # no linked figure on either side: the prompt is the plain text prompt
    (out / "report.md").write_text("skill text\n")
    seen.clear()
    run.judge_pair(case, "codex", 1, tmp_path, args(repeat=2))
    assert all(images == [] and "links no figure" not in prompt for prompt, images in seen)



def test_render_pages_reports_a_missing_browser(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "find_chrome", lambda: None)
    pages, note = run.render_pages(tmp_path / "x.html", tmp_path / "shots", "a")
    assert pages == [] and "Chrome" in note


def test_omp_run_that_reached_outside_its_condition_is_rejected():
    clean = '{"type":"tool_execution_start","args":{"path":"skill://anti-slop-editing"}}'
    assert run.isolation_problems("omp", "skill", None, clean) == []
    assert run.isolation_problems("omp", "baseline", None, '{"path":"skill://diagram-design"}') == []
    leaked = run.isolation_problems("omp", "baseline", None, clean)
    assert leaked == ["skills outside the condition: anti-slop-editing"]
    advised = run.isolation_problems("omp", "skill", None, '{"type":"advisor_yielded"}')
    assert advised == ["advisor events in log"]
    streamed = '{"delta":"{\\"path\\": \\"skill://career-"} {"args":{"path":"skill://career-documents"}}'
    assert run.isolation_problems("omp", "skill", None, streamed) == []
    assert run.isolation_problems("omp", "baseline", None, streamed) == ["skills outside the condition: career-documents"]


def test_omp_command_carries_the_isolation_overlay():
    args = argparse.Namespace(omp_model="m", omp_thinking=None)
    cmd = run.host_command("omp", "p", Path("."), Path("r"), args)
    overlay = json.loads(Path(cmd[cmd.index("--config") + 1]).read_text())
    assert overlay["advisor"]["enabled"] is False and overlay["memory"]["backend"] == "off"
    assert overlay["skills"]["enableAgentsUser"] is False


def test_judge_reads_a_split_deliverable_whole_but_not_author_questions(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "guide.md").write_text("Guide.")
    (out / "configuration.md").write_text("Every option.")
    (out / "open-questions.md").write_text("Who owns this?")
    text = run.side_text({"output": "out/guide.md", "files": {}}, tmp_path)
    assert text.startswith("Guide.") and "Every option." in text and "Who owns" not in text


def test_usage_sums_omp_turns_and_takes_claude_totals():
    turn = {"type": "message_end", "message": {"role": "assistant", "content": [],
                                               "usage": {"input": 4, "output": 60, "cacheRead": 100, "cacheWrite": 10,
                                                         "cost": {"total": 0.25}}}}
    omp_log = "\n".join([json.dumps(turn), json.dumps({"type": "turn_end", "message": turn["message"]}),
                         "not json", json.dumps(turn)])
    assert run.parse_usage("omp", omp_log) == {"input": 8, "output": 120, "cache_read": 200, "cache_write": 20,
                                               "cost_usd": 0.5}
    claude_log = json.dumps({"type": "result", "usage": {"input_tokens": 7, "output_tokens": 9},
                             "total_cost_usd": 0.01})
    assert run.parse_usage("claude", claude_log) == {"input": 7, "output": 9, "cost_usd": 0.01}
    assert run.parse_usage("codex", "boom") is None
