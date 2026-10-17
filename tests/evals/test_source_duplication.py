import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))

import source_duplication as sd  # noqa: E402

RULE = "Keep every figure the author gave, with its unit and its period."
OTHER = "Name the source of a claim beside the claim, not in a closing list."
NEAR_TWIN = "Keep every figure the author gave, with its unit and its date."


def test_exact_repeat_counts_both_copies_and_near_twin_is_separate():
    d = sd.duplication("\n".join([RULE, OTHER, RULE]))
    assert d["dup_sentence_share"] == 2 / 3
    assert d["near_dup_share"] == 0
    near = sd.duplication("\n".join([RULE, OTHER, NEAR_TWIN]))
    assert near["dup_sentence_share"] == 0
    assert near["near_dup_share"] == 2 / 3


def test_fenced_code_is_not_measured(tmp_path):
    (tmp_path / "SKILL.md").write_text(f"{RULE}\n```\n{RULE}\n{RULE}\n```\n{OTHER}\n", encoding="utf-8")
    assert sd.duplication(sd.text_of(sd.skill_files(tmp_path)))["dup_sentence_share"] == 0


def test_bundle_of_sibling_files_is_a_whole_file_copy_but_a_shared_line_is_not(tmp_path):
    a = " ".join(f"alpha{i} rule text about drafting reports clearly" for i in range(20))
    b = " ".join(f"beta{i} rule text about checking every number" for i in range(20))
    (tmp_path / "SKILL.md").write_text(a + "\n" + RULE, encoding="utf-8")
    (tmp_path / "modes.md").write_text(b + "\n" + RULE, encoding="utf-8")
    (tmp_path / "bundled.md").write_text(a + "\n" + b, encoding="utf-8")
    copies = sd.whole_file_copies(sd.skill_files(tmp_path))
    assert [p.name for p in copies] == ["bundled.md"]


def test_readme_license_and_eval_are_not_skill_text(tmp_path):
    for name in ("SKILL.md", "README.zh.md", "LICENSE", "eval.md", "notes.md"):
        (tmp_path / name).write_text(RULE, encoding="utf-8")
    assert sorted(p.name for p in sd.skill_files(tmp_path)) == ["SKILL.md", "notes.md"]
