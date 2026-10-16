"""Tests for the blind A/B review page generator."""

import json
import re
import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import grade  # noqa: E402
import review_pairs  # noqa: E402

CASE = {"id": "project-report/sample", "skill": "project-report", "description": "d", "prompt": "Save to out/report.md.",
        "files": {"docs/a.txt": "Budget 100 </script> <b>x</b>"}, "output": "out/report.md",
        "deliverables": ["out/report.md", "out/report.html"], "checks": []}


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(grade, "load_cases", lambda patterns=None: [CASE])
    for rep in (1, 2, 3):
        for cond in ("skill", "baseline"):
            d = tmp_path / "runs" / f"project-report__sample__codex__{cond}__r{rep}"
            (d / "workspace" / "out").mkdir(parents=True)
            (d / "workspace" / "out" / "report.md").write_text(f"{cond} markdown rep {rep} <tag>")
            if rep == 1:  # only rep 1 has an HTML report, with a local image to inline
                (d / "workspace" / "out" / "report.html").write_text(
                    f'<html><body><h1>{cond} html</h1><img src="fig.png"></body></html>')
                (d / "workspace" / "out" / "fig.png").write_bytes(b"\x89PNG")
            if rep == 3 and cond == "baseline":  # no output at all: the pair cannot be reviewed
                (d / "workspace" / "out" / "report.md").unlink()
            (d / "meta.json").write_text(json.dumps({"case": CASE["id"], "skill": "project-report", "host": "codex",
                                                     "condition": cond, "rep": rep}))
    return tmp_path


def test_pairs_are_built_per_rep_and_unpaired_ones_are_skipped(run_dir):
    pairs, skipped = review_pairs.collect_pairs(run_dir, seed=7)
    assert [p["rep"] for p in pairs] == [1, 2] and len(skipped) == 1 and "r3" in skipped[0]
    assert pairs[0]["a"][0] == "html" and pairs[1]["a"][0] == "text"
    assert "data:image/png;base64," in pairs[0]["a"][1]  # local image inlined for srcdoc


def test_order_is_seeded_and_covers_both_assignments(run_dir):
    first = [p["a_is"] for p in review_pairs.collect_pairs(run_dir, seed=7)[0]]
    again = [p["a_is"] for p in review_pairs.collect_pairs(run_dir, seed=7)[0]]
    assert first == again
    seen = {p["a_is"] for seed in range(20) for p in review_pairs.collect_pairs(run_dir, seed=seed)[0]}
    assert seen == {"skill", "baseline"}


def test_page_embeds_each_side_once_and_escapes_sources(run_dir):
    page, n, _ = review_pairs.build_page(run_dir, seed=7)
    assert n == 2 and page.count("<iframe") == 4 and page.count("srcdoc=") == 4
    assert page.count('class="pair"') == 2
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1))
    assert [p["id"] for p in data["pairs"]] == ["p0", "p1"] and all(p["a_is"] in ("skill", "baseline") for p in data["pairs"])
    assert "</script> <b>x</b>" not in page  # source text is escaped, so it cannot close the data script


def test_reveal_is_locked_and_export_and_storage_are_wired(run_dir):
    page = review_pairs.build_page(run_dir)[0]
    assert 'id="reveal" disabled' in page and "localStorage" in page and 'id="export"' in page
    assert "rated() < DATA.pairs.length" in page


def test_main_writes_the_page_and_fails_without_pairs(run_dir, tmp_path, capsys):
    out = tmp_path / "review" / "x.html"
    assert review_pairs.main([str(run_dir), "--out", str(out)]) == 0 and out.is_file()
    empty = tmp_path / "empty"
    (empty / "runs").mkdir(parents=True)
    assert review_pairs.main([str(empty), "--out", str(tmp_path / "y.html")]) == 1
