"""Tests for the review stage's grading plumbing: grader replies, summaries and case validation (no agent is started)."""

import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True
import grade  # noqa: E402
import review_stage  # noqa: E402

IDS = ["cost", "return-time", "plp"]


def test_parse_found_needs_an_answer_for_every_problem():
    reply = "Reasoning first.\nFOUND cost: yes\nFOUND return-time: no\n"
    assert review_stage.parse_found(reply, IDS) is None
    full = reply + "found PLP: Yes\nFOUND plp: yes\n"
    assert review_stage.parse_found(full, IDS) == {"cost": True, "return-time": False, "plp": True}


def test_parse_found_takes_the_last_answer_and_ignores_unknown_ids():
    reply = "FOUND cost: yes\nFOUND cost: no\nFOUND return-time: yes\nFOUND plp: no\nFOUND other: yes\n"
    assert review_stage.parse_found(reply, IDS) == {"cost": False, "return-time": True, "plp": False}


def test_misquotes_flags_only_quotes_absent_from_the_document():
    doc = "# Trip\n\nThe trip costs **£12 per child**, which covers the coach.\nPlease pay the usual way.\n"
    review = ("- \u201cThe trip costs £12 per child\u201d is clear.\n"            # exact, markdown and curly quotes
              "- \"costs £12 per child, \u2026 the coach\" is fine.\n"          # ellipsis: each piece found
              "- \"Please pay the normal way\" is vague.\n"                    # one word changed
              "- \"usual way\" and \"Trip\" are too short to count.\n")
    assert review_stage.misquotes(review, doc) == ["Please pay the normal way"]


def test_summary_counts_failed_or_ungraded_reviews_as_errors_not_as_zero_found():
    reviews = [
        {"case": "c", "condition": "skill", "rep": 1, "error": None, "words": 100,
         "found": {"cost": True, "return-time": True, "plp": False}},
        {"case": "c", "condition": "skill", "rep": 2, "error": None, "words": 300, "found": None},
        {"case": "c", "condition": "skill", "rep": 3, "error": "timeout", "words": 0, "found": None},
        {"case": "c", "condition": "baseline", "rep": 1, "error": None, "words": 50,
         "found": {"cost": False, "return-time": False, "plp": False}},
    ]
    verdicts = [{"case": "c", "pair": "skill:baseline", "winner": "baseline"},
                {"case": "c", "pair": "skill:baseline", "winner": "baseline"}]
    s = review_stage.summarise(reviews, verdicts, {"c": IDS})["c"]
    skill = s["conditions"]["skill"]
    assert (skill["reviews"], skill["errors"], skill["mean_found"], skill["mean_words"]) == (1, 2, 2.0, 100)
    assert skill["by_defect"] == {"cost": 1, "return-time": 1, "plp": 0}
    assert s["conditions"]["baseline"]["mean_found"] == 0.0
    assert s["pairs"] == {"skill:baseline": {"baseline": 2}}


def test_review_stage_validation():
    files = {"draft.md": "text", "notes.md": "private"}
    good = {"files": ["draft.md"], "brief": "What a reader would trip on.",
            "defects": [{"id": "cost", "description": "The amounts disagree."}]}
    assert grade._validate_review_stage(good, files) == []
    assert grade._validate_review_stage({**good, "defects": []}, files) == []
    bad = {"files": ["missing.md"], "brief": " ", "defects": [{"id": "a b", "description": "x"},
                                                             {"id": "c", "description": "y"},
                                                             {"id": "c", "description": "z"}], "extra": 1}
    errors = " | ".join(grade._validate_review_stage(bad, files))
    for part in ("unknown fields", "files must", "brief must", "defects[0]", "ids must be unique"):
        assert part in errors


def test_must_tell_validation_is_optional_but_strict():
    files = {"draft.md": "text"}
    stage = {"files": ["draft.md"], "brief": "b", "defects": []}
    assert grade._validate_review_stage(stage, files) == []
    assert grade._validate_review_stage({**stage, "must_tell": [{"id": "stop", "description": "How to stop it."}]},
                                        files) == []
    errors = " | ".join(grade._validate_review_stage(
        {**stage, "must_tell": [{"id": "stop", "description": ""}, {"id": "x", "description": "y"},
                                {"id": "x", "description": "z"}]}, files))
    assert "must_tell[0]" in errors and "must_tell ids must be unique" in errors


def test_parse_found_takes_a_keyword_and_ignores_the_other_list():
    reply = "FOUND cost: yes\nTOLD stop: no\nTOLD access: yes\n"
    assert review_stage.parse_found(reply, ["stop", "access"], "TOLD") == {"stop": False, "access": True}
    assert review_stage.parse_found(reply, ["cost"], "TOLD") is None


def test_summary_counts_told_separately_and_treats_a_missing_told_grade_as_an_error():
    reviews = [
        {"case": "c", "condition": "skill", "rep": 1, "error": None, "words": 100,
         "found": {"cost": True}, "told": {"stop": True, "access": False}},
        {"case": "c", "condition": "skill", "rep": 2, "error": None, "words": 100, "found": {"cost": True}, "told": None},
        {"case": "d", "condition": "skill", "rep": 1, "error": None, "words": 80, "found": {"cost": False}},
    ]
    s = review_stage.summarise(reviews, [], {"c": ["cost"], "d": ["cost"]}, {"c": ["stop", "access"]})
    skill = s["c"]["conditions"]["skill"]
    assert (skill["reviews"], skill["errors"], skill["mean_found"], skill["mean_told"]) == (1, 1, 1.0, 1.0)
    assert skill["by_item"] == {"stop": 1, "access": 0}
    other = s["d"]["conditions"]["skill"]
    assert (other["errors"], other["mean_told"], other["by_item"]) == (0, None, {})
    text = review_stage.report(s)
    assert "| Mean told | Per item |" in text and "stop 1/1, access 0/1" in text
    assert text.count("Mean told") == 1


def test_parse_outside_counts_fact_lines_not_fragments_and_needs_a_total():
    reply = ('Thinking.\nFACT: "Wait until the kiln reads below 100°C."\nFACT: \u201cFixer must not go down the drain.\u201d\n'
             'FACT: "safelight"\nTOTAL: 3\n')
    assert review_stage.parse_outside(reply) == ["Wait until the kiln reads below 100°C.",
                                                 "Fixer must not go down the drain."]
    assert review_stage.parse_outside("TOTAL: 0\n") == []
    assert review_stage.parse_outside('FACT: "Something."\n') is None


def test_summary_outside_facts_counts_statements_and_reviews_and_needs_a_grade():
    reviews = [
        {"case": "c", "condition": "skill", "rep": 1, "error": None, "words": 10, "found": {}, "outside": ["a", "b"]},
        {"case": "c", "condition": "skill", "rep": 2, "error": None, "words": 10, "found": {}, "outside": []},
        {"case": "c", "condition": "skill", "rep": 3, "error": None, "words": 10, "found": {}, "outside": None},
    ]
    s = review_stage.summarise(reviews, [], {"c": []}, outside=True)["c"]["conditions"]["skill"]
    assert (s["reviews"], s["errors"], s["outside"], s["outside_reviews"]) == (2, 1, 2, 1)
    plain = review_stage.summarise(reviews[:2], [], {"c": []})["c"]["conditions"]["skill"]
    assert "outside" not in plain
    text = review_stage.report(review_stage.summarise(reviews, [], {"c": []}, outside=True))
    assert "Outside facts |" in text and "| 1 / 2 |" in text
