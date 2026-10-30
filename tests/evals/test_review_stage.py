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
