"""Tests for fixture sources, facts_recalled, diagrams, html_deliverable, the new case fields, and score summaries."""

import json
import sys
import zipfile
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
import grade  # noqa: E402

PROMPT = "Write the status report from docs/ and save it to out/report.md and out/report.html."
DOCX = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        '<w:p><w:r><w:t>Approved budget is 48500 USD for plan v2.</w:t></w:r></w:p></w:body></w:document>')
SVG = ('<svg role="img" aria-labelledby="t" viewBox="0 0 200 100"><title id="t">Plan</title>'
       '<text x="1" y="2">Budget 48500</text><text x="1" y="9">Pilot</text></svg>')


def make_case(**extra):
    return {"id": "project-report/sample", "skill": "project-report", "description": "sample", "prompt": PROMPT,
            "files": {}, "output": "out/report.md", "checks": [{"type": "word_count", "min": 1}], **extra}


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A fake repository root with one fixture folder holding a docx, a csv and a note."""
    monkeypatch.setattr(grade, "REPO", tmp_path)
    root = tmp_path / "evals" / "fixtures" / "sample"
    (root / "docs").mkdir(parents=True)
    with zipfile.ZipFile(root / "docs" / "plan-v2.docx", "w") as zf:
        zf.writestr("word/document.xml", DOCX)
    (root / "docs" / "pilot.csv").write_text('date,users,note\n2026-06-29,14,"1,240"\n', encoding="utf-8")
    (root / "docs" / "note.md").write_text("The pilot starts on 29 June.\n", encoding="utf-8")
    return tmp_path


FIXTURES = "evals/fixtures/sample"


def ws_with(tmp_path, files: dict[str, str]) -> Path:
    ws = tmp_path / "ws"
    for rel, text in files.items():
        path = ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return ws


def run_check(case, check, output="", workspace=None, reply=""):
    return grade.grade_case({**case, "checks": [check]}, output, reply, workspace)["checks"][1]


# ---------------------------------------------------------------- validation of the new fields

def test_valid_extended_case_passes(repo):
    case = make_case(fixtures=FIXTURES, timeout=2400, deliverables=["out/report.md", "out/report.html"],
                     judge={"mode": "visual", "render": "out/report.html"},
                     checks=[{"type": "facts_recalled", "facts": [{"id": "budget", "any": ["48,?500"]}], "min": 0.5},
                             {"type": "diagrams", "min": 1, "max": 3, "numbers_from_sources": True,
                              "labels_any": [{"id": "plan", "any": ["plan"]}], "labels_none": ["kafka"]},
                             {"type": "html_deliverable", "path": "out/report.html", "no_script": True,
                              "min_figures": 1},
                             {"type": "preserves", "source": "docs/note.md"}])
    assert grade.validate_case(case) == []


@pytest.mark.parametrize("extra, expected", [
    ({"fixtures": "evals/fixtures/missing"}, "does not exist"),
    ({"fixtures": "elsewhere/sample"}, "fixtures must be a path under"),
    ({"fixtures": "evals/fixtures/../../x"}, "fixtures must be a path under"),
    ({"timeout": 0}, "timeout must be"),
    ({"timeout": "slow"}, "timeout must be"),
    ({"deliverables": []}, "deliverables must be"),
    ({"deliverables": ["/abs/report.md"]}, "deliverables must be"),
    ({"deliverables": ["out/a.md", "out/a.md"]}, "must not repeat"),
    ({"judge": {"mode": "text"}}, "mode 'visual'"),
    ({"judge": {"mode": "visual", "render": "out/report.html"}}, "listed in deliverables"),
])
def test_validation_rejects_bad_extra_fields(repo, extra, expected):
    case = make_case(**extra)
    assert expected in " | ".join(grade.validate_case(case))


@pytest.mark.parametrize("check, expected", [
    ({"type": "facts_recalled", "facts": []}, "non-empty list"),
    ({"type": "facts_recalled", "facts": [{"id": "a", "any": []}]}, "'any' must be"),
    ({"type": "facts_recalled", "facts": [{"id": "a", "any": ["("]}]}, "bad regex"),
    ({"type": "facts_recalled", "facts": [{"id": "a", "any": ["x"]}, {"id": "a", "any": ["y"]}]}, "unique"),
    ({"type": "facts_recalled", "facts": [{"id": "a", "any": ["x"]}], "min": 1.5}, "min must be"),
    ({"type": "diagrams", "min": 3, "max": 1}, "min is greater than max"),
    ({"type": "diagrams", "min": -1}, "non-negative"),
    ({"type": "diagrams", "self_check": "yes"}, "true or false"),
    ({"type": "diagrams", "labels_any": [{"id": "a"}]}, "needs a string id"),
    ({"type": "diagrams", "labels_none": ["["]}, "bad regex"),
    ({"type": "html_deliverable"}, "needs ['path']"),
    ({"type": "html_deliverable", "path": "../x.html"}, "relative path"),
    ({"type": "html_deliverable", "path": "out/r.html", "min_figures": "two"}, "min_figures"),
    ({"type": "preserves", "source": "docs/none.md"}, "not an input file"),
])
def test_validation_rejects_bad_new_checks(repo, check, expected):
    case = make_case(fixtures=FIXTURES, checks=[check])
    assert expected in " | ".join(grade.validate_case(case))


# ---------------------------------------------------------------- fixtures as sources

def test_fixture_texts_extract_office_and_text_files(repo):
    texts = grade.fixture_texts(make_case(fixtures=FIXTURES))
    assert set(texts) == {"docs/plan-v2.docx", "docs/pilot.csv", "docs/note.md"}
    assert "48500 USD" in texts["docs/plan-v2.docx"]


def test_no_added_facts_reads_extracted_fixtures_and_file_names(repo):
    case = make_case(fixtures=FIXTURES)
    check = {"type": "no_added_facts", "categories": ["numbers"]}
    assert run_check(case, check, "Budget 48500 USD, see plan-v2.docx; pilot 14 users on 2026-06-29.")["passed"]
    result = run_check(case, check, "Budget 51000 USD.")
    assert not result["passed"] and "51000" in result["detail"]


def test_csv_cells_are_not_fused_and_quoted_cells_survive(repo):
    check = {"type": "no_added_facts", "categories": ["numbers"]}
    case = make_case(fixtures=FIXTURES)
    assert run_check(case, check, "14 users; the note says 1,240.")["passed"]


def test_titled_markdown_link_target_is_not_an_added_number(repo):
    case = make_case(fixtures=FIXTURES)
    check = {"type": "no_added_facts", "categories": ["numbers", "urls"]}
    assert run_check(case, check, '![Budget](diagrams/fig1.svg "Source: plan-v2.docx")')["passed"]


def test_links_to_inputs_and_outputs_are_not_urls(repo):
    case = make_case(fixtures=FIXTURES)
    check = {"type": "no_added_facts", "categories": ["urls"]}
    assert run_check(case, check, "See [plan](../docs/plan-v2.docx) and [fig](diagrams/schedule.svg).")["passed"]
    assert not run_check(case, check, "See [site](https://example.org/x).")["passed"]


# ---------------------------------------------------------------- facts_recalled

FACTS = {"type": "facts_recalled", "min": 0.6, "facts": [
    {"id": "budget", "any": [r"48,?500"]}, {"id": "launch", "any": [r"29 June", r"June 29"]},
    {"id": "owner", "any": [r"\[ASK AUTHOR"]}]}


def test_facts_recalled_passes_at_threshold_and_lists_misses():
    case = make_case()
    ok = run_check(case, FACTS, "Budget: 48,500. Launch on JUNE 29.")
    assert ok["passed"] and "2/3" in ok["detail"] and "owner" in ok["detail"]
    bad = run_check(case, FACTS, "Nothing useful here.")
    assert not bad["passed"] and "budget" in bad["detail"] and "0/3" in bad["detail"]


# ---------------------------------------------------------------- diagrams

def diagram_case(tmp_path, **check):
    return make_case(files={"docs/a.txt": "Budget 48500 USD. Pilot with 14 users."}), {"type": "diagrams", **check}


def test_diagram_count_range_and_kinds(tmp_path):
    case, check = diagram_case(tmp_path, min=2, max=3)
    ws = ws_with(tmp_path, {"out/a.svg": SVG, "out/report.md": "x"})
    assert not run_check(case, check, "x", ws)["passed"]
    mermaid = "```mermaid\nflowchart LR\n  A1[Phase one] --> B2[Phase two]\n```\n"
    result = run_check(case, check, mermaid, ws)
    assert result["passed"] and "2 diagram" in result["detail"]
    many = "".join(f"```mermaid\nflowchart LR\n A[Step {i}]\n```\n" for i in range(3))
    assert not run_check(case, check, many, ws)["passed"]


def test_same_diagram_reached_two_ways_counts_once(tmp_path):
    case, check = diagram_case(tmp_path, min=1, max=1)
    page = f"<html><body><figure>{SVG}</figure></body></html>"
    ws = ws_with(tmp_path, {"out/diagrams/a.html": f"<html><body>{SVG}</body></html>", "out/report.html": page,
                            "out/diagrams/a.svg": SVG})
    assert run_check(case, check, "", ws)["passed"]


def test_decorative_svg_and_report_html_are_not_standalone_diagrams(tmp_path):
    case, check = diagram_case(tmp_path, min=1)
    page = '<html><svg aria-hidden="true"><text>Icon 1</text></svg></html>'
    ws = ws_with(tmp_path, {"out/report.html": page})
    assert not run_check(case, check, "", ws)["passed"]


def test_numbers_must_come_from_sources(tmp_path):
    case, check = diagram_case(tmp_path, min=1, numbers_from_sources=True)
    ok = ws_with(tmp_path, {"out/a.svg": SVG})
    assert run_check(case, check, "", ok)["passed"]
    bad = ws_with(tmp_path / "bad", {"out/a.svg": SVG.replace("48500", "73900")})
    result = run_check(case, check, "", bad)
    assert not result["passed"] and "73900" in result["detail"]
    allowed = run_check(case, {**check, "allow": ["73900"]}, "", bad)
    assert allowed["passed"]


def test_mermaid_numbers_are_checked_but_node_ids_are_not(tmp_path):
    case, check = diagram_case(tmp_path, min=1, numbers_from_sources=True)
    ws = ws_with(tmp_path, {"out/report.md": "x"})
    ok = "```mermaid\nflowchart LR\n  N77[Budget 48500] --> N88[Pilot]\n```"
    assert run_check(case, check, ok, ws)["passed"]
    bad = "```mermaid\nflowchart LR\n  A[Budget 91111] --> B[Pilot]\n```"
    assert not run_check(case, check, bad, ws)["passed"]


def test_raster_diagrams_are_unverifiable(tmp_path):
    case, check = diagram_case(tmp_path, min=1, numbers_from_sources=True)
    ws = ws_with(tmp_path, {"out/report.md": "x"})
    (ws / "out" / "fig.png").write_bytes(b"\x89PNG\r\n")
    md = "![Figure](fig.png)"
    failed = run_check(case, check, md, ws)
    assert not failed["passed"] and "unverifiable" in failed["detail"]
    plain = run_check(case, {"type": "diagrams", "min": 1}, md, ws)
    assert plain["passed"] and "unverifiable" in plain["detail"]
    mixed = ws_with(tmp_path / "mix", {"out/a.svg": SVG, "out/b.svg": SVG.replace("Pilot", "Other"),
                                       "out/report.md": "x"})
    (mixed / "out" / "fig.png").write_bytes(b"\x89PNG\r\n")
    assert run_check(case, check, md, mixed)["passed"]


def test_labels_required_and_forbidden(tmp_path):
    case, base = diagram_case(tmp_path)
    ws = ws_with(tmp_path, {"out/a.svg": SVG})
    want = {**base, "labels_any": [{"id": "pilot", "any": ["pilot"]}]}
    assert run_check(case, want, "", ws)["passed"]
    missing = {**base, "labels_any": [{"id": "kafka", "any": ["kafka"]}]}
    result = run_check(case, missing, "", ws)
    assert not result["passed"] and "kafka" in result["detail"]
    forbidden = {**base, "labels_none": ["pilot"]}
    result = run_check(case, forbidden, "", ws)
    assert not result["passed"] and "forbidden" in result["detail"]


def test_self_check_runs_the_installed_checker_on_diagram_html(tmp_path, monkeypatch):
    checker = tmp_path / "self_check.py"
    checker.write_text("import sys\nbad = 'BAD' in open(sys.argv[1]).read()\n"
                       "print(('FAIL ' if bad else 'OK ') + sys.argv[1])\n"
                       "if bad: print('  - broken svg')\nsys.exit(1 if bad else 0)\n")
    monkeypatch.setattr(grade, "DIAGRAM_SELF_CHECK", checker)
    case, check = diagram_case(tmp_path, min=1, self_check=True)
    good = ws_with(tmp_path / "good", {"out/diagrams/a.html": f"<html>{SVG}</html>"})
    assert run_check(case, check, "", good)["passed"]
    bad = ws_with(tmp_path / "bad", {"out/diagrams/a.html": f"<html>BAD{SVG}</html>"})
    result = run_check(case, check, "", bad)
    assert not result["passed"] and "broken svg" in result["detail"]
    monkeypatch.setattr(grade, "DIAGRAM_SELF_CHECK", tmp_path / "absent.py")
    skipped = run_check(case, check, "", bad)
    assert skipped["passed"] and "skipped" in skipped["detail"]


# ---------------------------------------------------------------- html_deliverable

PAGE = "<!doctype html><html><head><style>body{{color:#111}}</style>{head}</head><body>{body}</body></html>"


def html_ws(tmp_path, head="", body="", extra=None):
    return ws_with(tmp_path, {"out/report.html": PAGE.format(head=head, body=body), **(extra or {})})


HTML = {"type": "html_deliverable", "path": "out/report.html", "no_script": True, "self_contained": True,
        "min_figures": 1}


def test_html_deliverable_passes_a_clean_page(tmp_path):
    ws = html_ws(tmp_path, head='<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">',
                 body=f'<a href="https://example.org">link</a><a href="#top">top</a>{SVG}'
                      '<img src="fig.png"><img src="data:image/png;base64,AAAA">',
                 extra={"out/fig.png": "x"})
    assert run_check(make_case(), HTML, "", ws)["passed"]


@pytest.mark.parametrize("head, body, expected", [
    ("<script>1</script>", SVG, "<script>"),
    ("", f'<p onclick="x()">a</p>{SVG}', "event handler"),
    ("", f'<a href="javascript:void(0)">a</a>{SVG}', "javascript"),
    ("", f'<img src="https://cdn.example.org/a.png">{SVG}', "remote resource"),
    ("", f'<img src="missing.png">{SVG}', "missing local file"),
    ("", f'<img src="/Users/me/a.png">{SVG}', "absolute path"),
    ("", f'<img src="../../outside.png">{SVG}', "outside the workspace"),
    ('<style>@import url("https://evil.example/x.css");</style>', SVG, "remote resource"),
    ("", "<p>No figure</p>", "figure"),
])
def test_html_deliverable_failures(tmp_path, head, body, expected):
    ws = html_ws(tmp_path, head=head, body=body)
    result = run_check(make_case(), HTML, "", ws)
    assert not result["passed"] and expected in result["detail"]


def test_html_deliverable_options_are_opt_in_and_file_must_exist(tmp_path):
    ws = html_ws(tmp_path, body='<script>1</script>')
    assert run_check(make_case(), {"type": "html_deliverable", "path": "out/report.html"}, "", ws)["passed"]
    missing = run_check(make_case(), {"type": "html_deliverable", "path": "out/none.html"}, "", ws)
    assert not missing["passed"] and "not written" in missing["detail"]


def test_workspace_checks_run_even_without_the_markdown_output(tmp_path):
    ws = html_ws(tmp_path, body=SVG)
    result = grade.grade_case(make_case(checks=[HTML]), None, "", ws)
    assert result["checks"][0]["passed"] is False and result["checks"][1]["passed"] is True


# ---------------------------------------------------------------- scores and repetitions

def row(case, cond, rep, passed, score, host="codex", error=None):
    out = {"case": case, "skill": "project-report", "host": host, "condition": cond, "rep": rep,
           "skill_loaded": cond == "skill", "passed": passed, "score": score, "error": error,
           "checks": [{"type": "output_present", "passed": error is None, "detail": ""}]}
    return out


def test_summary_reports_mean_score_and_range_across_reps():
    runs = [row("c", "skill", 1, True, 1.0), row("c", "baseline", 1, False, 0.5),
            row("c", "skill", 2, False, 0.75), row("c", "baseline", 2, False, 0.25)]
    total = grade.summarize(runs, [])["by"]["codex/ALL"]
    assert total["skill_score"] == pytest.approx(0.875) and total["baseline_score"] == pytest.approx(0.375)
    assert (total["skill_score_min"], total["skill_score_max"]) == (0.75, 1.0)
    assert (total["baseline_score_min"], total["baseline_score_max"]) == (0.25, 0.5)
    assert total["score_delta"] == pytest.approx(0.5)
    assert total["skill_pass"] == 0.5 and total["skill_n"] == 2


def test_pairing_is_per_rep_and_a_broken_rep_excludes_only_itself():
    runs = [row("c", "skill", 1, True, 1.0), row("c", "baseline", 1, False, 0.5),
            row("c", "skill", 2, False, 0.0, error="timeout", ), row("c", "baseline", 2, True, 1.0),
            row("c", "skill", 3, True, 1.0)]  # rep 3 has no baseline: unpaired
    total = grade.summarize(runs, [])["by"]["codex/ALL"]
    assert (total["skill_n"], total["baseline_n"], total["excluded"]) == (1, 1, 2)
    assert total["skill_score"] == 1.0 and total["baseline_score"] == 0.5


def test_judge_scores_are_averaged_per_condition():
    judge = [{"case": "c", "host": "codex", "rep": 1, "winner": "skill",
              "scores": {"skill": {"accuracy": 5, "layout": 4}, "baseline": {"accuracy": 3}}},
             {"case": "d", "host": "codex", "rep": 1, "winner": "tie",
              "scores": {"skill": {"accuracy": 3}, "baseline": {"accuracy": 3, "layout": 2}}},
             {"case": "e", "host": "codex", "rep": 1, "winner": "error"}]
    out = grade.summarize([], judge)["judge_scores"]
    assert out["skill"]["accuracy"] == 4 and out["skill"]["layout"] == 4 and out["skill"]["n"] == 2
    assert out["baseline"]["accuracy"] == 3 and out["baseline"]["layout"] == 2 and out["skill"]["tone"] is None


def test_grade_run_reads_workspace_files_and_reps(tmp_path, monkeypatch):
    case = make_case(files={"docs/a.txt": "Budget 48500 USD."}, deliverables=["out/report.md", "out/report.html"],
                     checks=[{"type": "diagrams", "min": 1}])
    monkeypatch.setattr(grade, "load_cases", lambda patterns=None: [case])
    for cond, svg in (("skill", SVG), ("baseline", "")):
        for rep in (1, 2):
            d = tmp_path / "runs" / f"x__codex__{cond}__r{rep}"
            (d / "workspace" / "out").mkdir(parents=True)
            (d / "workspace" / "out" / "report.md").write_text("report")
            if svg:
                (d / "workspace" / "out" / "a.svg").write_text(svg)
            (d / "meta.json").write_text(json.dumps({"case": case["id"], "skill": case["skill"], "host": "codex",
                                                     "condition": cond, "rep": rep, "skill_loaded": cond == "skill"}))
    results = grade.grade_run(tmp_path)
    total = results["summary"]["by"]["codex/ALL"]
    assert (total["skill_pass"], total["baseline_pass"]) == (1.0, 0.0)
    assert {r["rep"] for r in results["runs"]} == {1, 2}
    assert results["runs"][0]["deliverables"] == {"out/report.md": True, "out/report.html": False}
    report = (tmp_path / "report.md").read_text()
    assert "project-report/sample | codex | 2 |" in report and "score with skills" in report
