import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))

import similarity_assets as sa  # noqa: E402
import similarity_rules as sr  # noqa: E402


def test_python_docstrings_and_comments_are_prose_and_everything_else_is_normalised_code():
    src = ('"""Module docstring that says what this script does for the reader."""\n'
           "import os\n"
           "# a comment explaining why the next line exists at all\n"
           "value = compute_something(os.environ['HOME'], 'a # not a comment')  # trailing remark here\n"
           "def f():\n"
           '    """Function docstring text that is also prose for the comparison."""\n'
           "    return 1\n")
    e = sa.extract_text(src, ".py")
    prose = [l for l in e.prose.split("\n") if l.strip()]
    assert prose[0].startswith("Module docstring")
    assert any(l.startswith("a comment explaining") for l in prose) and any("trailing remark" in l for l in prose)
    assert any(l.startswith("Function docstring") for l in prose)
    assert e.code == [(4, "value=compute_something(os.environ['HOME'],'a#notacomment')")]


def test_markdown_fences_become_code_with_comments_stripped_by_language():
    md = "Intro line.\n```bash\n# setup comment\nexport OUTPUT_DIR=/tmp/report-output-dir\n```\n```\n# kept heading in a template block\n```\n"
    e = sa.extract_text(md, ".md")
    assert e.code == [(4, "exportOUTPUT_DIR=/tmp/report-output-dir"), (7, "#keptheadinginatemplateblock")]
    assert "export" not in e.prose


def test_yaml_and_json_give_string_values_and_html_gives_text_nodes():
    y = sa.extract_text('interface:\n  display_name: "Short"\n  default_prompt: "Use the skill to tighten this draft."\n# note: kept as prose\n', ".yaml")
    assert "Use the skill to tighten this draft." in y.prose and "default_prompt" not in y.prose
    j = sa.extract_text('{\n  "name": "x",\n  "description": "Remove empty openers from a post"\n}\n', ".json")
    assert "Remove empty openers from a post" in j.prose and "description" not in j.prose
    h = sa.extract_text("<style>\nbody { margin: 0; padding: 10px; }\n</style>\n<p class=\"a\">Lead with the result.</p>\n", ".html")
    assert "Lead with the result." in h.prose and "margin" not in h.prose
    assert h.code == [(2, "body{margin:0;padding:10px;}")]


def test_css_comments_are_prose_and_binary_files_are_skipped(tmp_path):
    e = sa.extract_text("/* Page size is injected by the build script */\n.page { width: 210mm; height: 297mm; }\n", ".css")
    assert "Page size" in e.prose and e.code == [(2, ".page{width:210mm;height:297mm;}")]
    b = tmp_path / "x.bin"
    b.write_bytes(b"\x00\x01\x02 binary")
    assert sa.extract(b) is None
    (tmp_path / ".hidden").write_text("secret", encoding="utf-8")
    assert sa.extract(tmp_path / ".hidden") is None


MD = """# Doc

## Rules

1. **Never invent.** Do not add facts, numbers or quotes the author did not give you in the material.
2. **Keep structure.** Change the span, not the paragraph, and keep the argument as it was written.

### Hollow intensifiers (`hollow-intensifier`)

- Looks like: "genuinely", "truly", "quite frankly".
"""


def test_units_cover_sections_items_and_rows(tmp_path):
    f = tmp_path / "a.md"
    f.write_text(MD + "\n| Trait | What to look at | How to evidence |\n|---|---|---|\n| Openings | How a piece begins in the sample | Quote three openings |\n",
                 encoding="utf-8")
    us = sr.units_of(f, "a.md")
    kinds = [(u.kind, u.heading) for u in us]
    assert ("section", "Hollow intensifiers ( hollow-intensifier )") in kinds
    assert ("item", "Never invent.") in kinds and ("item", "Keep structure.") in kinds
    assert ("row", "Openings") in kinds and not any(k == "row" and h == "Trait" for k, h in kinds)
    assert [u.heading for u in sr.rules_items(us)] == ["Never invent.", "Keep structure."]
    assert next(u for u in us if u.heading == "Never invent.").bold


def test_headings_name_the_same_thing_by_stems_and_pattern_ids():
    assert sr.same_heading("Hollow intensifiers", "Performed reaction (stock-reaction, hollow-intensifier)")
    assert sr.same_heading("Copula avoidance", "Copula avoidance ( copula-avoidance )")
    assert sr.same_heading("Hedging", "Parenthetical hedges")
    assert not sr.same_heading("Smallest effective edit.", "effective / effectively")
    assert not sr.same_heading("Numbered list inflation", "Formatting the reader relies on (heading levels, list order, numbered steps)")
    assert not sr.same_heading("Closings", "One-line closers and dramatic fragments")


def test_rule_match_grades_follow_the_cuts_and_a_same_named_heading_wins():
    class Backend:
        def match(self, ours, pools):
            return {"pool": ([0.58, 0.52, 0.30], [0, 1, 2])}

    pool = [sr.Unit("alpha unit", "alpha", "alpha", "x.md", 1, "section"),
            sr.Unit("beta unit", "beta", "beta", "x.md", 2, "section"),
            sr.Unit("Copula avoidance", "gamma", "gamma", "x.md", 3, "section")]
    rules = [sr.Unit("one thing", "t", "t", "y.md", 1, "section"), sr.Unit("two thing", "t", "t", "y.md", 2, "section"),
             sr.Unit("Copula avoidance ( copula-avoidance )", "t", "t", "y.md", 3, "section")]
    ms = sr.match_rules(Backend(), rules, pool, 0.55, 0.50)
    assert [m.grade for m in ms] == ["strong", "covered", "strong"]
    assert ms[2].named and ms[2].best.heading == "Copula avoidance"
    assert sr.share(ms) == 1.0 and abs(sr.share(ms, firm_only=True) - 2 / 3) < 1e-9
