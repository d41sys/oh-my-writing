"""Behavior tests for skills/author-voice/scripts/voice_stats.py (run as a subprocess)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "author-voice"
SCRIPT = SKILL_ROOT / "scripts" / "voice_stats.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin, capture_output=True, text=True, cwd=FIXTURES,
    )


def stats(*files):
    result = run("--json", *files)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def stats_text(text):
    result = run("--json", "-", stdin=text)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["samples"][0]


def test_help_mentions_observations():
    result = run("--help")
    assert result.returncode == 0
    assert "FILE" in result.stdout and "--json" in result.stdout


def test_known_counts_on_plain_fixture():
    sample = stats("plain.md")["samples"][0]
    assert (sample["words"], sample["sentences"], sample["paragraphs"]) == (28, 4, 2)
    assert sample["sentence_length"] == {"mean": 7.0, "median": 5.5, "stdev": 2.92, "min": 5, "max": 12}
    assert sample["paragraph_length"] == {"words_mean": 14.0, "sentences_mean": 2.0}
    assert sample["questions_per_100_sentences"] == 25.0
    assert sample["exclamations_per_100_sentences"] == 25.0
    rates = sample["per_1000_words"]
    assert rates["first_person_singular"] == 35.71  # I
    assert rates["first_person_plural"] == 35.71  # We
    assert rates["second_person"] == 71.43  # you, You'd
    assert rates["contractions"] == 107.14  # can't, You'd, it's
    assert rates["em_dash"] == rates["semicolon"] == rates["colon"] == rates["parenthesis"] == 35.71
    assert sample["bullet_line_ratio"] == 0.0


def test_structure_excludes_code_quotes_headings_and_links():
    sample = stats("structure.md")["samples"][0]
    assert sample["words"] == 26  # code, quote, heading, front matter, link target not counted
    assert sample["sentences"] == 5
    assert sample["headings"] == 1
    assert sample["bullet_items"] == 3
    # lead-in line above the list is not a paragraph; only the closing paragraph is
    assert sample["paragraphs"] == 1
    assert sample["bullet_line_ratio"] == 0.75
    assert sample["sentence_length"]["mean"] == 5.2
    assert sample["per_1000_words"]["colon"] == 38.46


def test_recurring_phrases_need_two_samples_and_drop_subsumed_ones():
    report = stats("phrases-1.md", "phrases-2.md", "phrases-3.md")
    phrases = {p["phrase"]: p for p in report["recurring_phrases"]}
    assert list(phrases) == ["the cache", "in practice", "ship it", "the cache fails"]
    assert phrases["the cache"]["samples"] == 3 and phrases["the cache"]["count"] == 3
    assert phrases["in practice"]["in"] == ["phrases-1.md", "phrases-2.md"]
    assert "cache fails" not in phrases  # contained in the equally frequent "the cache fails"
    assert "of the" not in phrases


def test_single_sample_has_no_recurring_phrases_and_says_so():
    report = stats("phrases-1.md")
    assert report["recurring_phrases"] == []
    human = run("phrases-1.md").stdout
    assert "[FLAG] recurring phrases need at least 2 samples" in human


def test_min_samples_and_top_options():
    report = json.loads(run("--json", "--min-samples", "3", "phrases-1.md", "phrases-2.md", "phrases-3.md").stdout)
    assert [p["phrase"] for p in report["recurring_phrases"]] == ["the cache"]
    report = json.loads(run("--json", "--top", "1", "phrases-1.md", "phrases-2.md", "phrases-3.md").stdout)
    assert len(report["recurring_phrases"]) == 1
    assert run("--min-samples", "1", "plain.md").returncode == 2


def test_json_shape():
    report = stats("plain.md", "structure.md")
    assert set(report) == {"samples", "aggregate", "spread", "recurring_phrases", "notes"}
    assert [s["name"] for s in report["samples"]] == ["plain.md", "structure.md"]
    expected = {"name", "words", "sentences", "paragraphs", "headings", "sentence_length", "paragraph_length",
                "questions_per_100_sentences", "exclamations_per_100_sentences", "per_1000_words",
                "bullet_items", "bullet_line_ratio", "english_function_word_share", "lexical_lists_apply",
                "warnings"}
    assert expected <= set(report["samples"][0])
    assert report["aggregate"]["sample_count"] == 2
    assert report["aggregate"]["words"] == 54  # pooled, not averaged
    assert report["aggregate"]["sentences"] == 9


def test_human_output_uses_ascii_markers_and_is_observational():
    out = run("plain.md").stdout
    assert out.startswith("Voice statistics (observations")
    assert "[OK] plain.md: 28 words" in out and "  -> sentence length: mean 7.0" in out
    assert "[FLAG] plain.md: short sample" in out
    assert "not targets" in out
    out.encode("ascii")  # output is ASCII for these inputs


def test_output_is_deterministic():
    first = run("--json", "phrases-1.md", "phrases-2.md", "phrases-3.md").stdout
    second = run("--json", "phrases-1.md", "phrases-2.md", "phrases-3.md").stdout
    assert first == second


def test_stdin_default_and_dash():
    explicit = json.loads(run("--json", "-", stdin="I agree. You do too.").stdout)
    implicit = json.loads(run("--json", stdin="I agree. You do too.").stdout)
    assert explicit["samples"][0]["name"] == "<stdin>"
    assert explicit["samples"][0]["words"] == implicit["samples"][0]["words"] == 5


def test_missing_file_exits_2_without_report():
    result = run("--json", "does-not-exist.md")
    assert result.returncode == 2
    assert result.stdout == "" and "cannot read" in result.stderr


def test_script_never_modifies_inputs():
    before = (FIXTURES / "plain.md").read_bytes()
    run("plain.md")
    assert (FIXTURES / "plain.md").read_bytes() == before


# --- documented exceptions and false-positive guards -------------------------------------------

def test_abbreviations_decimals_and_initialisms_do_not_split_sentences():
    text = "Dr. Smith met Mr. Jones, e.g. at noon in the U.S. office. They scored 3.5 points. Done."
    sample = stats_text(text)
    assert sample["sentences"] == 3
    assert stats_text("Version 2. Next steps follow.")["sentences"] == 2


def test_lowercase_sentence_starts_still_split():
    assert stats_text("ok that works. so we ship it. fine by me.")["sentences"] == 3


def test_question_and_exclamation_endings_including_quotes_and_combined():
    sample = stats_text('She asked "why?" He said stop! Really?! Fine.')
    assert sample["sentences"] == 4
    assert sample["questions_per_100_sentences"] == 50.0  # "why?" and "Really?!"
    assert sample["exclamations_per_100_sentences"] == 50.0  # "stop!" and "Really?!"


def test_dash_variants_count_but_ranges_do_not():
    text = "One \u2014 two. Three -- four. Five \u2013 six. Pages 10\u201320 and 3-4 are fine."
    assert stats_text(text)["per_1000_words"]["em_dash"] == pytest.approx(3 * 1000 / 13, abs=0.01)


def test_colon_in_times_is_not_counted_but_labels_are():
    text = "Meet at 10:30 today. Note: bring notes."
    assert stats_text(text)["per_1000_words"]["colon"] == pytest.approx(1000 / 8, abs=0.01)


def test_possessive_s_is_not_a_contraction_but_n_t_and_let_s_are():
    sample = stats_text("The author's draft isn't done. Let's go. It's late.")
    assert sample["per_1000_words"]["contractions"] == pytest.approx(3 * 1000 / 9, abs=0.01)


def test_uppercase_US_is_not_a_pronoun_but_lowercase_us_is():
    assert stats_text("The US market grew. Join us today.")["per_1000_words"]["first_person_plural"] == pytest.approx(
        1000 / 7, abs=0.01)


def test_lowercase_i_counts_for_casual_writers():
    assert stats_text("i think i can. my plan is fine.")["per_1000_words"]["first_person_singular"] == pytest.approx(
        3 * 1000 / 8, abs=0.01)


def test_fenced_code_inline_code_urls_and_quotes_are_ignored():
    text = "Real words only.\n\n```\ncode here is ignored\n```\n\n> quoted line ignored\n\nSee `code` and https://example.com/a/b now."
    sample = stats_text(text)
    assert sample["words"] == 3 + 3  # "Real words only" + "See and now"


def test_numbered_and_star_bullets_count_as_items():
    sample = stats_text("Intro paragraph here.\n\n1. first\n2. second\n3) third\n* fourth\n")
    assert sample["bullet_items"] == 4
    assert sample["paragraphs"] == 1
    assert sample["bullet_line_ratio"] == 0.8


def test_hard_wrapped_paragraph_is_one_paragraph_and_wrapped_items_merge():
    sample = stats_text("This paragraph is wrapped\nacross two lines.\n\n- an item that\n  wraps too\n")
    assert sample["paragraphs"] == 1 and sample["bullet_items"] == 1
    assert sample["sentences"] == 2


# --- boundaries ---------------------------------------------------------------------------------

def test_empty_input_is_flagged_not_an_error():
    result = run("--json", "-", stdin="")
    assert result.returncode == 0
    sample = json.loads(result.stdout)["samples"][0]
    assert sample["words"] == 0 and sample["sentence_length"]["mean"] is None
    assert sample["bullet_line_ratio"] is None
    assert any("no prose words" in w for w in sample["warnings"])


def test_short_sample_boundary_at_100_words():
    ninety_nine = ("The cat sat. " * 33).strip()  # 33 sentences x 3 words
    hundred = ninety_nine + " Go."
    assert stats_text(ninety_nine)["words"] == 99
    assert any("short sample" in w for w in stats_text(ninety_nine)["warnings"])
    assert stats_text(hundred)["words"] == 100
    assert not any("short sample" in w for w in stats_text(hundred)["warnings"])


def test_non_english_sample_blanks_english_only_rates_but_keeps_structure():
    sample = stats("vietnamese.md")["samples"][0]
    assert sample["lexical_lists_apply"] is False
    rates = sample["per_1000_words"]
    assert rates["first_person_singular"] is None and rates["contractions"] is None
    assert sample["sentences"] == 4 and sample["questions_per_100_sentences"] == 25.0
    assert any("does not look like English" in w for w in sample["warnings"])


def test_english_sample_is_marked_english():
    sample = stats_text("The plan is clear and we will ship it. You can see that it is for the team. " * 3)
    assert sample["lexical_lists_apply"] is True


def test_aggregate_notes_warn_about_thin_sample_sets():
    notes = stats("plain.md", "structure.md")["notes"]
    assert any("fewer than 5 samples" in n for n in notes)
    assert any("under 1000 words" in n for n in notes)


def test_spread_flags_split_between_registers(tmp_path):
    formal = " ".join(["The committee reviewed the proposal and concluded that further evidence was required."] * 12)
    casual = " ".join(["I can't wait. It's fine. We'll go. You'd like it."] * 12)
    (tmp_path / "formal.txt").write_text(formal)
    (tmp_path / "casual.txt").write_text(casual)
    result = subprocess.run([sys.executable, str(SCRIPT), "--json", "formal.txt", "casual.txt"],
                            capture_output=True, text=True, cwd=tmp_path)
    report = json.loads(result.stdout)
    by_metric = {e["metric"]: e for e in report["spread"]}
    assert by_metric["mean sentence length"]["split"] is True
    assert by_metric["mean sentence length"]["max_sample"] == "formal.txt"
    assert by_metric["contractions per 1000 words"]["split"] is True
    human = subprocess.run([sys.executable, str(SCRIPT), "formal.txt", "casual.txt"],
                           capture_output=True, text=True, cwd=tmp_path).stdout
    assert "[FLAG] spread: mean sentence length" in human


def test_spread_ignores_short_samples():
    report = stats("plain.md", "structure.md")  # both under 100 words
    assert report["spread"] == []
