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


def test_skill_folder_files_take_every_asset_but_not_nested_skills_tests_or_readme(tmp_path):
    for rel in ("SKILL.md", "references/a.md", "scripts/b.py", "scripts/tests/t.py", "agents/openai.yaml", "assets/t.html",
                "sub/SKILL.md", "sub/references/c.md", "README.md", "extra.md", "references/notes.zh.md", "dist/x.md",
                "scripts/b.md"):
        p = tmp_path / "skill" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("text", encoding="utf-8")
    got = {str(p.relative_to(tmp_path / "skill")): legacy
           for p, legacy in ss.skill_folder_files(tmp_path / "skill", tmp_path)}
    assert got == {"SKILL.md": True, "extra.md": True, "references/a.md": True, "scripts/b.py": False,
                   "agents/openai.yaml": False, "assets/t.html": False, "scripts/b.md": False}


def test_code_lines_are_compared_whitespace_and_comment_blind_and_runs_need_five_lines(tmp_path):
    shared = ["total_value = compute_total(items, tax_rate)  # sum", "result_rows = [row for row in table if row.ok]",
              "if not result_rows: raise ValueError('nothing to report')", "report_path = output_dir / 'report.html'",
              "report_path.write_text(render(result_rows), encoding='utf-8')"]
    ours = tmp_path / "ours.py"
    theirs = tmp_path / "theirs.py"
    ours.write_text('"""Docstring prose that explains the whole script in one line."""\nx = 1\n'
                    + "\n".join(shared) + "\n", encoding="utf-8")
    theirs.write_text("# a comment line that is not code at all\n"
                      + "\n".join(l.replace(" = ", "=") for l in shared[:4]) + "\ny = 2\n"
                      + shared[4].strip() + "\n", encoding="utf-8")
    od = ss.load_file(ours, "ours.py", "s", False, keep_text=True)
    td = ss.load_file(theirs, "theirs.py", "", False)
    assert od[0].kind == "py" and "Docstring prose" in " ".join(s.text for s in od[0].sents)   # docstring is prose
    assert len(od[1].words) == 5                                  # `x = 1` is under 20 characters
    assert set(od[1].words) == set(td[1].words)                   # whitespace and the comment do not matter
    index = {}
    for p, h in enumerate(ss.gram_hashes(od[1].words, 5)):
        index.setdefault(h, []).append((0, p))
    corpus = ss.Corpus("src", code=[td[1]])
    cov, runs = ss.verbatim_pass(corpus, [od[1]], index, n=5, docs=corpus.code)
    assert sum(cov[0]) == 5 and runs[0].length == 5               # the stray `y = 2` line is dropped, run stays whole
    short = ss.gram_hashes(od[1].words[:4], 5)
    assert short == []                                            # four lines never make a 5-line run


def test_load_file_splits_markdown_into_prose_and_fenced_code(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("Keep every figure the author gave, with its unit.\n```python\nresult = compute_everything(a, b, c)  # c\n```\n",
                 encoding="utf-8")
    doc, code, why = ss.load_file(f, "a.md", "", True)
    assert why is None and doc.legacy and doc.kind == "md" and "print" not in " ".join(s.text for s in doc.sents)
    assert code.kind == "md-fence" and len(code.words) == 1 and code.lines[0] == 3
    y = tmp_path / "o.yaml"
    y.write_text("interface:\n  short_description: \"Cut filler words before you cut any claim in the draft\"\n",
                 encoding="utf-8")
    ydoc, ycode, _ = ss.load_file(y, "o.yaml", "", False)
    assert ydoc.kind == "yaml" and not ydoc.legacy and ycode is None
    assert "Cut filler words" in ydoc.sents[0].text


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
