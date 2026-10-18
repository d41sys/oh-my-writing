import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS))

import source_similarity as ss  # noqa: E402


def words(text):
    return text.lower().split()


def tokens(text):
    return tuple(ss.sd.WORD.findall(text.lower()))


SOURCE = ("Always keep every figure the author gave, with its unit and its period, when you edit a paragraph. "
          "Cut filler words before you cut any claim.")


def test_verbatim_share_counts_words_inside_shared_eight_word_runs():
    ours = tokens("Intro words here. Keep every figure the author gave, with its unit and its period, in the edit.")
    shared = len(tokens("keep every figure the author gave with its unit and its period"))
    assert sum(ss.covered_positions(ours, [tokens(SOURCE)])) == shared
    assert ss.verbatim_share([ours], [tokens(SOURCE)]) == shared / len(ours)


def test_seven_shared_words_are_not_verbatim():
    ours = words("keep every figure the author gave with")        # 7 words from the source, no 8-word run
    assert ss.verbatim_share([ours], [words("keep every figure the author gave with its unit")]) == 0.0
    assert ss.verbatim_share([words("a b c d e f g h")], [words("a b c d e f g h")]) == 1.0
    assert ss.verbatim_share([], [words(SOURCE)]) == 0.0


def test_close_paraphrase_finds_light_edit_but_not_unrelated_sentence():
    src = [tokens("Keep every figure the author gave, with its unit and its period."),
           tokens("Name the source of a claim beside the claim, not in a closing list.")]
    edited = tokens("Keep every figure the author gave, with its unit and its date.")
    unrelated = tokens("Open the file and read the first failing test before you change any code.")
    (jac, idx), (none_jac, none_idx) = ss.close_matches([edited, unrelated], src)
    assert idx == 0 and jac >= 0.5
    assert (none_jac, none_idx) == (0.0, -1)


def test_close_paraphrase_threshold_and_exact_twin():
    base = tokens("Keep every figure the author gave, with its unit and its period.")
    assert ss.close_matches([base], [base])[0] == (1.0, 0)
    half = tokens("Keep every figure the author gave, then cite where each number came from.")
    jac, idx = ss.close_matches([half], [base], threshold=0.2)[0]
    assert idx == 0 and 0.2 <= jac < 0.5
    assert ss.close_matches([half], [base])[0] == (0.0, -1)


def test_build_doc_skips_fenced_code_and_splits_table_cells(tmp_path):
    f = tmp_path / "SKILL.md"
    f.write_text("Keep every figure the author gave, with its unit.\n```\nprint one two three four five six seven\n```\n"
                 "| a rule about checking every number | another rule about naming the reader |\n", encoding="utf-8")
    d = ss.build_doc(f, "SKILL.md")
    texts = [s.text for s in d.sents]
    assert texts[0].startswith("Keep every figure")
    assert not any("print" in t for t in texts)
    assert "a rule about checking every number" in texts and "another rule about naming the reader" in texts
    assert d.lines[0] == 1 and d.sents[1].line == 5


def test_non_english_file_is_skipped(tmp_path):
    f = tmp_path / "zh.md"
    f.write_text("这是一个关于如何写作的指南，请保持每个数字的单位和时间范围。" * 5, encoding="utf-8")
    assert ss.build_doc(f, "zh.md") is None


def test_skill_folder_files_take_references_but_not_scripts_or_nested_skills(tmp_path):
    for rel in ("SKILL.md", "references/a.md", "scripts/b.md", "sub/SKILL.md", "sub/references/c.md", "README.md",
                "extra.md"):
        p = tmp_path / "skill" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("text", encoding="utf-8")
    got = sorted(str(p.relative_to(tmp_path / "skill")) for p in ss.skill_folder_files(tmp_path / "skill", tmp_path))
    assert got == ["SKILL.md", "extra.md", "references/a.md"]


def test_verbatim_pass_finds_longest_run_with_lines(tmp_path):
    ours = tmp_path / "ours.md"
    theirs = tmp_path / "theirs.md"
    shared = "keep every figure the author gave with its unit and its period when you edit"
    ours.write_text(f"First line has other words.\n{shared} today.\n", encoding="utf-8")
    theirs.write_text(f"Unrelated heading line here.\nMore. {shared} always.\n", encoding="utf-8")
    od = ss.build_doc(ours, "ours.md", "s")
    corpus = ss.Corpus("src", docs=[ss.build_doc(theirs, "theirs.md")])
    index = {}
    for p, h in enumerate(ss.gram_hashes(od.words)):
        index.setdefault(h, []).append((0, p))
    cov, runs = ss.verbatim_pass(corpus, [od], index)
    n = len(shared.split())
    assert sum(cov[0]) == n
    assert runs[0].length == n and runs[0].src_line == (2, 2) and runs[0].our_start == 5
