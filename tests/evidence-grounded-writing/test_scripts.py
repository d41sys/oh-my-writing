"""Consumer-visible tests for skills/evidence-grounded-writing/scripts/claim_ledger.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "evidence-grounded-writing"
SCRIPT = SKILL_ROOT / "scripts" / "claim_ledger.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample.md"


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def ledger(tmp_path, text):
    path = tmp_path / "doc.md"
    path.write_text(text, encoding="utf-8")
    proc = run(str(path), "--json")
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def by_sentence(data):
    return {c["sentence"]: c for c in data["claims"]}


# --- each reason fires ------------------------------------------------------

REASON_CASES = [
    ("number", "The service handled 1,200 requests."),
    ("number", "Throughput rose 3x after the rewrite."),
    ("number", "Usage doubled over the summer."),
    ("percent", "Churn dropped by 8 percent."),
    ("percent", "Conversion reached 12.5% on mobile."),
    ("currency", "The plan costs $20 per seat."),
    ("currency", "The contract was worth 3 million euros."),
    ("date", "The launch happened on March 3, 2023."),
    ("date", "The report was filed on 2022-11-05."),
    ("date", "Sales peaked in 2019."),
    ("date", "Results improved in Q3 2024."),
    ("comparative", "The new parser is faster than the old one."),
    ("comparative", "Errors decreased after the patch."),
    ("superlative", "This is the largest dataset in the field."),
    ("superlative", "It was the first tool of its kind."),
    ("superlative", "Ours is the only option."),
    ("causal", "Delays occur because the queue is full."),
    ("causal", "The change leads to fewer crashes."),
    ("causal", "Outages are due to the cache layer."),
    ("causal", "Heavy load results in timeouts."),
    ("causal", "Training drives the improvement."),
    ("absolute", "Users never read the manual."),
    ("absolute", "Every customer gets the same result."),
    ("absolute", "The method guarantees a correct answer."),
    ("absolute", "None of the tests failed."),
    ("vague-attribution", "Studies show that caching helps."),
    ("vague-attribution", "Experts say the market will grow."),
    ("vague-attribution", "Research suggests the effect is small."),
    ("vague-attribution", "Many believe the tool is safe."),
    ("vague-attribution", "It is widely known that sleep matters."),
]


@pytest.mark.parametrize("reason,sentence", REASON_CASES)
def test_reason_fires(tmp_path, reason, sentence):
    data = ledger(tmp_path, sentence + "\n")
    claims = by_sentence(data)
    assert sentence in claims, f"not flagged: {sentence!r}"
    assert reason in claims[sentence]["reasons"]


def test_specific_signal_is_not_double_counted_as_number(tmp_path):
    claims = by_sentence(ledger(tmp_path, "Churn fell 8%. The fee is $5. It ended on March 3, 2023.\n"))
    assert claims["Churn fell 8%."]["reasons"] == ["percent"]
    assert claims["The fee is $5."]["reasons"] == ["currency"]
    assert claims["It ended on March 3, 2023."]["reasons"] == ["date"]


def test_several_reasons_on_one_sentence(tmp_path):
    sentence = "Experts say that sales always grow 40% faster because of ads."
    reasons = by_sentence(ledger(tmp_path, sentence + "\n"))[sentence]["reasons"]
    for expected in ("percent", "comparative", "causal", "absolute", "vague-attribution"):
        assert expected in reasons


# --- documented exceptions and false-positive guards ------------------------

QUIET_SENTENCES = [
    "The team met on Tuesday and walked through the agenda.",
    "The result may differ between runs.",
    "She has an interest in birds.",
    "We ran the test again.",
    "The tool runs on GPT-4 and v3.2.",
    "Figure 3 shows the layout.",
    "See Section 2 for the setup.",
    "Open the file named `report-2024.txt` and read it.",
    "The report says the budget is under review.",
    "Install the package and restart the shell.",
]


@pytest.mark.parametrize("sentence", QUIET_SENTENCES)
def test_sentence_without_signals_is_not_listed(tmp_path, sentence):
    data = ledger(tmp_path, sentence + "\n")
    assert data["claims"] == [], data
    assert data["sentences_total"] == 1


def test_clean_text_reports_ok(tmp_path):
    path = tmp_path / "clean.md"
    path.write_text("The team met on Tuesday.\n", encoding="utf-8")
    proc = run(str(path))
    assert proc.returncode == 0
    assert proc.stdout.startswith("[OK]")
    assert "|" not in proc.stdout


# --- structure of the input is respected ------------------------------------

def test_fenced_code_is_skipped():
    proc = run(str(FIXTURE), "--json")
    data = json.loads(proc.stdout)
    sentences = " ".join(c["sentence"] for c in data["claims"])
    assert "100 % 7" not in sentences and "5 times faster" not in sentences
    assert 'print("never")' not in sentences


def test_tilde_fences_and_unclosed_fence(tmp_path):
    text = "~~~\nUsers always win by 90%.\n~~~\n\nKeep it simple.\n\n```\nStudies show 40%.\n"
    data = ledger(tmp_path, text)
    assert data["claims"] == []


def test_front_matter_and_headings_are_skipped():
    data = json.loads(run(str(FIXTURE), "--json").stdout)
    sentences = [c["sentence"] for c in data["claims"]]
    assert not any("Release 2024" in s or "99%" in s for s in sentences)


def test_fixture_flags_expected_sentences_and_only_those():
    data = json.loads(run(str(FIXTURE), "--json").stdout)
    sentences = [c["sentence"] for c in data["claims"]]
    assert sentences == [
        "Latency fell by 40% after the change [3].",
        "Studies show that caching helps.",
        "The cache is the cause of the speedup.",
        "Revenue reached $4.2M in March 2023.",
        "Our tool is the best on the market.",
        "Every user always wins (Smith, 2021).",
        "p95 latency | 120 ms",
        "[VERIFY: confirm the figure with finance] Support is faster than before.",
    ]
    assert data["flagged"] == len(sentences)
    assert data["sentences_total"] > data["flagged"]


def test_line_numbers_point_at_the_source_line():
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    data = json.loads(run(str(FIXTURE), "--json").stdout)
    for claim in data["claims"]:
        probe = claim["sentence"].split(" | ")[0][:12]
        assert probe in lines[claim["line"] - 1], claim


def test_sentence_line_is_where_the_sentence_starts(tmp_path):
    data = ledger(tmp_path, "Opening line has\nno signals here. The second sentence says 40% more\nusers came.\n")
    assert data["claims"][0]["line"] == 2


def test_abbreviation_does_not_split_sentence(tmp_path):
    data = ledger(tmp_path, "Dr. Lee measured 40 samples. Nothing else happened here.\n")
    assert [c["sentence"] for c in data["claims"]] == ["Dr. Lee measured 40 samples."]


def test_decimal_numbers_do_not_split_sentence(tmp_path):
    data = ledger(tmp_path, "Accuracy was 91.5 percent on the held-out set. Done here.\n")
    assert [c["sentence"] for c in data["claims"]] == ["Accuracy was 91.5 percent on the held-out set."]


def test_each_list_item_is_its_own_sentence(tmp_path):
    data = ledger(tmp_path, "- Alpha point is fine\n- Beta point grew 5%\n- Gamma point is fine\n")
    assert data["sentences_total"] == 3
    assert [c["line"] for c in data["claims"]] == [2]


def test_list_numbering_is_not_a_number(tmp_path):
    data = ledger(tmp_path, "1. Install the package\n2. Restart the shell\n")
    assert data["claims"] == []


# --- citation column ---------------------------------------------------------

def test_citation_states():
    claims = by_sentence(json.loads(run(str(FIXTURE), "--json").stdout))
    cited = claims["Latency fell by 40% after the change [3]."]
    assert cited["citation_present"] is True and cited["pending_marker"] is False
    author_year = claims["Every user always wins (Smith, 2021)."]
    assert author_year["citation_present"] is True
    uncited = claims["Studies show that caching helps."]
    assert uncited["citation_present"] is False and uncited["pending_marker"] is False
    pending = claims["[VERIFY: confirm the figure with finance] Support is faster than before."]
    assert pending["citation_present"] is False and pending["pending_marker"] is True


@pytest.mark.parametrize(
    "marker",
    ["[1-3]", "[@smith2020]", "\\cite{smith2020}", "[Smith et al., 2020]", "([source](https://example.org/a))", "doi:10.1000/xyz123"],
)
def test_citation_marker_forms(tmp_path, marker):
    sentence = f"Sales grew 12% last year {marker}."
    claims = by_sentence(ledger(tmp_path, sentence + "\n"))
    assert claims[sentence]["citation_present"] is True


def test_citation_year_and_index_are_not_read_as_figures(tmp_path):
    sentence = "The method was introduced earlier (Lopez, 2018) [4]."
    assert ledger(tmp_path, sentence + "\n")["claims"] == []


@pytest.mark.parametrize(
    "marker",
    [
        "[VERIFY: find a source for the 12% figure]",
        "[ASK AUTHOR: which survey?]",
        "[UNTESTED]",
        "[CITATION NEEDED: a source for the 12% figure]",
        "[Source needed]",
        "[UNVERIFIED]",
    ],
)
def test_gap_markers_count_as_pending(tmp_path, marker):
    """The three standard markers and the older placeholders all read as pending, never as cited."""
    sentence = f"Sales grew 12% last year {marker}."
    claim = by_sentence(ledger(tmp_path, sentence + "\n"))[sentence]
    assert claim["pending_marker"] is True
    assert claim["citation_present"] is False


def test_marker_text_is_not_read_as_a_figure(tmp_path):
    sentence = "[VERIFY: check the 2021 figure against the filing] The report is on file."
    assert ledger(tmp_path, sentence + "\n")["claims"] == []


# --- markdown output ---------------------------------------------------------

def test_markdown_table_shape():
    proc = run(str(FIXTURE))
    assert proc.returncode == 0
    out = proc.stdout.splitlines()
    assert out[0].startswith("[FLAG] 8 of ")
    header = next(l for l in out if l.startswith("| id"))
    assert header == "| id | line | sentence | reasons | citation | status |"
    rows = [l for l in out if l.startswith("| C")]
    assert len(rows) == 8
    assert rows[0].startswith("| C1 | ")
    assert all(r.rstrip().endswith("|  |") for r in rows), "status column must stay blank"
    assert any("| pending |" in r for r in rows)


def test_pipe_in_sentence_is_escaped(tmp_path):
    path = tmp_path / "pipes.md"
    path.write_text("The a|b filter removed 40% of rows.\n", encoding="utf-8")
    row = next(l for l in run(str(path)).stdout.splitlines() if l.startswith("| C1"))
    assert "a\\|b" in row


# --- JSON shape and exit codes ----------------------------------------------

def test_json_shape():
    data = json.loads(run(str(FIXTURE), "--json").stdout)
    assert set(data) == {"file", "sentences_total", "flagged", "claims"}
    assert data["file"].endswith("sample.md")
    for i, claim in enumerate(data["claims"], start=1):
        assert set(claim) == {"id", "line", "sentence", "reasons", "citation_present", "pending_marker", "status"}
        assert claim["id"] == f"C{i}"
        assert isinstance(claim["line"], int) and claim["line"] >= 1
        assert isinstance(claim["reasons"], list) and claim["reasons"]
        assert claim["status"] == ""
        assert isinstance(claim["citation_present"], bool)


def test_reads_stdin():
    proc = run("-", "--json", stdin="Sales grew 12% last year.\n")
    data = json.loads(proc.stdout)
    assert data["file"] == "<stdin>"
    assert data["flagged"] == 1


def test_missing_file_exits_2(tmp_path):
    proc = run(str(tmp_path / "nope.md"))
    assert proc.returncode == 2
    assert "not found" in proc.stderr


def test_strict_exit_codes(tmp_path):
    uncited = tmp_path / "uncited.md"
    uncited.write_text("Sales grew 12% last year.\n", encoding="utf-8")
    cited = tmp_path / "cited.md"
    cited.write_text("Sales grew 12% last year [2].\n", encoding="utf-8")
    assert run(str(uncited)).returncode == 0
    assert run(str(uncited), "--strict").returncode == 1
    assert run(str(cited), "--strict").returncode == 0


def test_help_exits_0():
    proc = run("--help")
    assert proc.returncode == 0
    assert "--json" in proc.stdout and "--strict" in proc.stdout


def test_script_never_modifies_input(tmp_path):
    path = tmp_path / "keep.md"
    original = "Sales grew 12% last year.\n"
    path.write_text(original, encoding="utf-8")
    run(str(path))
    run(str(path), "--json")
    assert path.read_text(encoding="utf-8") == original


def test_output_is_deterministic():
    assert run(str(FIXTURE), "--json").stdout == run(str(FIXTURE), "--json").stdout
