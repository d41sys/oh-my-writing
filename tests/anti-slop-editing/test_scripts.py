"""Consumer-visible behavior of the anti-slop-editing helper scripts.

The scripts run as subprocesses, the way an agent or a user runs them.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "anti-slop-editing"
SCAN = SKILL_ROOT / "scripts" / "slop_scan.py"
DIFF = SKILL_ROOT / "scripts" / "fact_diff.py"
FIX = Path(__file__).resolve().parent / "fixtures"


def run(script, *args, stdin=None):
    return subprocess.run([sys.executable, str(script), *args], input=stdin,
                          capture_output=True, text=True, timeout=60)


def scan_json(path_or_none, *args, stdin=None):
    cmd = [*args, "--json"]
    if path_or_none is not None:
        cmd.append(str(path_or_none))
    proc = run(SCAN, *cmd, stdin=stdin)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def patterns(result):
    return {f["pattern"] for f in result["findings"]}


# ---------------------------------------------------------------- slop_scan


def test_true_positives_cover_the_families():
    result = scan_json(FIX / "slop_sample.md")
    families = {f["family"] for f in result["findings"]}
    assert {"lexical", "framing", "contrast", "puffery", "ending", "residue"} <= families
    by_pattern = {f["pattern"]: f for f in result["findings"]}
    assert by_pattern["delve"]["line"] == 3 and by_pattern["delve"]["text"].lower() == "delve"
    assert by_pattern["era-opener"]["line"] == 3
    assert by_pattern["not-just"]["line"] == 5
    assert by_pattern["vague-attribution"]["line"] == 7
    assert by_pattern["closing-formula"]["line"] == 9
    assert by_pattern["chat-closer"]["line"] == 11
    assert "game-changer" in {f["text"] for f in result["findings"] if f["pattern"] == "promo-wording"}


def test_every_finding_names_the_exception_to_consider():
    result = scan_json(FIX / "slop_sample.md")
    for f in result["findings"]:
        assert set(f) >= {"line", "col", "family", "pattern", "text", "consider", "strength"}
        assert f["consider"].strip() and f["line"] >= 1 and f["col"] >= 1
        assert f["strength"] in {"strong", "weak"}


def test_json_shape_and_exit_code_with_findings():
    proc = run(SCAN, "--json", str(FIX / "slop_sample.md"))
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert set(data) >= {"profile", "words", "findings", "summary", "notes", "file"}
    assert set(data["summary"]) == {"total", "per_1000_words", "by_family"}
    assert data["summary"]["total"] == len(data["findings"])
    assert data["profile"] == "professional"


def test_human_output_uses_ascii_markers():
    proc = run(SCAN, str(FIX / "slop_sample.md"))
    assert proc.returncode == 0
    assert "[FLAG]" in proc.stdout and "-> consider:" in proc.stdout
    assert "candidates, not verdicts" in proc.stdout
    proc.stdout.encode("ascii")


def test_protected_regions_are_not_scanned():
    result = scan_json(FIX / "protected.md")
    assert result["findings"] == [], result["findings"]


def test_chat_residue_inside_quotes_and_code_is_also_skipped(tmp_path):
    path = write(tmp_path, "q.md", 'He wrote "I hope this helps!" in the margin.\n\n`Certainly!` is a string.\n')
    assert scan_json(path)["findings"] == []


def test_clean_text_is_a_no_op():
    proc = run(SCAN, str(FIX / "clean.md"))
    assert proc.returncode == 0
    assert "[OK]" in proc.stdout and "[FLAG]" not in proc.stdout
    result = scan_json(FIX / "clean.md")
    assert result["findings"] == [] and result["summary"]["total"] == 0 and result["summary"]["by_family"] == {}


def test_profile_effect_on_engineering_vocabulary(tmp_path):
    path = write(tmp_path, "eng.md", "We leverage a seamless pipeline. The proxy serves as a gateway.\n")
    professional = patterns(scan_json(path, "--profile", "professional"))
    technical = patterns(scan_json(path, "--profile", "technical"))
    assert {"leverage-verb", "seamless", "copula-avoidance"} <= professional
    assert not ({"leverage-verb", "seamless", "copula-avoidance"} & technical)


def test_casual_profile_reports_only_chat_residue(tmp_path):
    path = write(tmp_path, "c.md", "We delve into the pivotal tapestry. In conclusion, it's not just a plan, it's a shift.\n\n[Insert name]\n")
    assert patterns(scan_json(path, "--profile", "professional")) >= {"delve", "closing-formula", "not-just", "placeholder"}
    assert patterns(scan_json(path, "--profile", "casual")) == {"placeholder"}


def test_academic_profile_adds_paper_openers(tmp_path):
    path = write(tmp_path, "a.md", "In recent years, the field has grown quickly.\n")
    assert "academic-opener" in patterns(scan_json(path, "--profile", "academic"))
    assert "academic-opener" not in patterns(scan_json(path, "--profile", "professional"))


def test_documented_exceptions_are_not_reported(tmp_path):
    text = (
        "In today's meeting we agreed to ship on Friday. "
        "The test harness runs nightly. "
        "The effect was statistically significant. "
        "That was a crucial step.\n\n"
        "Studies show that sleep matters (Walker, 2017). "
        "Moreover, the second run was faster.\n"
    )
    result = scan_json(write(tmp_path, "e.md", text))
    assert result["findings"] == [], result["findings"]


def test_stock_phrases_are_reported_when_the_exception_does_not_apply(tmp_path):
    text = "We harness the power of data. Studies show that sleep matters. In today's fast-paced world, speed wins.\n"
    found = patterns(scan_json(write(tmp_path, "p.md", text)))
    assert {"harness-verb", "vague-attribution", "era-opener"} <= found


def test_tier2_words_count_only_as_a_cluster(tmp_path):
    single = scan_json(write(tmp_path, "s.md", "This is a crucial decision for the team.\n"))
    assert "tier2-word" not in patterns(single)
    cluster = scan_json(write(tmp_path, "c.md", "This crucial decision offers valuable insights and effectively helps the team.\n"))
    assert [f["text"].lower() for f in cluster["findings"] if f["pattern"] == "tier2-word"] == [
        "crucial", "valuable", "insights", "effectively"]


def test_transition_openers_need_three(tmp_path):
    two = scan_json(write(tmp_path, "t2.md", "Moreover, it ran. Furthermore, it passed.\n"))
    three = scan_json(write(tmp_path, "t3.md", "Moreover, it ran. Furthermore, it passed. Additionally, it shipped.\n"))
    assert "transition-opener" not in patterns(two)
    assert sum(1 for f in three["findings"] if f["pattern"] == "transition-opener") == 3


def test_em_dash_density_threshold_and_profiles(tmp_path):
    many = write(tmp_path, "many.md", "The launch \u2014 delayed twice \u2014 finally shipped \u2014 and the team \u2014 tired but proud \u2014 went home.\n")
    one = write(tmp_path, "one.md", "We shipped late \u2014 twice \u2014 and said so in the notes we published after the release went out to everyone.\n")
    assert sum(1 for f in scan_json(many)["findings"] if f["pattern"] == "em-dash-density") == 5
    assert "em-dash-density" not in patterns(scan_json(one))
    assert "em-dash-density" not in patterns(scan_json(many, "--profile", "casual"))


def test_em_dash_in_bold_term_list_is_exempt(tmp_path):
    text = "- **Alpha** \u2014 first\n- **Beta** \u2014 second\n- **Gamma** \u2014 third\n- **Delta** \u2014 fourth\n"
    assert "em-dash-density" not in patterns(scan_json(write(tmp_path, "l.md", text)))


def test_rhythm_patterns_and_technical_skip(tmp_path):
    opener = write(tmp_path, "o.md", "We tested the cache. We measured the latency. We compared the results. We wrote the report.\n")
    assert "same-opener-run" in patterns(scan_json(opener))
    frag = write(tmp_path, "f.md", "Fast. Cheap. Reliable. Done.\n")
    assert "fragment-run" in patterns(scan_json(frag))
    uniform = write(tmp_path, "u.md", (
        "The first batch of records arrived late on Monday after the upstream export failed twice. "
        "The second batch of records arrived early on Tuesday once the upstream export was fixed properly. "
        "The third batch of records arrived late on Wednesday because the network link dropped again. "
        "The fourth batch of records arrived on Thursday after the manual import finally succeeded.\n"))
    assert "uniform-length-run" in patterns(scan_json(uniform))
    assert not {f["family"] for f in scan_json(uniform, "--profile", "technical")["findings"]} & {"rhythm"}
    assert not {f["family"] for f in scan_json(FIX / "clean.md")["findings"]} & {"rhythm"}


def test_format_patterns(tmp_path):
    text = (
        "## \U0001F680 What this means\n\n"
        "We think **speed**, **safety** and **cost** all matter here.\n\n"
        "- **Speed**: fast\n- **Safety**: safe\n- **Cost**: low\n\n"
        "#ai #tech #future #growth #innovation\n"
    )
    path = write(tmp_path, "fmt.md", text)
    found = patterns(scan_json(path))
    assert {"heading-emoji", "decorative-bold", "label-bullet-list", "hashtag-block"} <= found
    tech = patterns(scan_json(path, "--profile", "technical"))
    assert "decorative-bold" not in tech and "label-bullet-list" not in tech


def test_residue_family_details(tmp_path):
    text = (
        "Here is a revised version of your paragraph:\n\n"
        "As of my last knowledge update, the API was stable. See the source:oaicite:0 for more.\n\n"
        "Read more at https://example.com/post?utm_source=chatgpt.com and https://example.com/post.\n\n"
        "Zero\u200bwidth here.\n"
    )
    result = scan_json(write(tmp_path, "r.md", text))
    found = {f["pattern"]: f for f in result["findings"]}
    assert {"rewrite-wrapper", "assistant-self-reference", "citation-leak", "ai-referral-parameter", "hidden-character"} <= set(found)
    assert found["ai-referral-parameter"]["line"] == 5


RHETORICAL_SETUPS = [
    ("The best part? It runs offline.", "colon-reveal"),
    ("We're thrilled to announce Tidewater 2.4.", "announced-feeling"),
    ("Lumen isn't just a search tool, it's a movement.", "not-just"),
    ("Let us know in the comments what you think.", "engagement-bait"),
    ("The best part: it learns from every correction.", "colon-reveal"),
    ("We tried it. Plot twist: it was faster.", "colon-reveal"),
    ("Here's the thing: nobody reads changelogs.", "staged-reveal"),
    ("The kicker: they still break builds.", "staged-reveal"),
    ("The result? Faster builds.", "staged-reveal"),
    ("What if I told you the cache was the problem?", "scenario-opener"),
    ("Why does this matter? Because every second counts.", "self-answered-question"),
    ("What changed? Nothing.", "self-answered-fragment"),
    ("So why should you care?", "rhetorical-question"),
    ("The release underscored our commitment to developer productivity.", "underscore-verb"),
    ("The release underscored our commitment to developer productivity.", "commitment-claim"),
    ("We shipped on time, underscoring our commitment to quality.", "trailing-rider"),
    ("Sit with that for a moment.", "performed-insight"),
    ("Meet Flowdesk, your new favorite dashboard.", "launch-intro"),
    ("This is a major step forward for AI infrastructure.", "madlib-step"),
    ("I want to be upfront: the sample was small.", "narrated-candor"),
    ("While the results are impressive, accuracy remains a challenge.", "false-concession"),
    ("Trust is the currency of good teams.", "aphorism-formula"),
    ("We conducted an analysis of the logs.", "nominalization"),
    ("He is associated with the leadership of ExampleCorp.", "vague-association"),
    ("The tool replaces the old one (and, increasingly, the new one).", "parenthetical-hedge"),
    ("It has sane defaults and ships batteries included.", "dev-slogan"),
]


@pytest.mark.parametrize("text,expected", RHETORICAL_SETUPS)
def test_rhetorical_setups_and_puffery_are_reported(tmp_path, text, expected):
    assert expected in patterns(scan_json(write(tmp_path, "s.md", text + "\n")))


@pytest.mark.parametrize("profile", ["technical", "academic"])
def test_underscore_verb_is_reported_where_the_character_is_skipped(tmp_path, profile):
    path = write(tmp_path, "u.md", "The release underscored our commitment to developers.\n\nUse an underscore_name here.\n")
    found = [f for f in scan_json(path, "--profile", profile)["findings"] if f["pattern"] == "underscore-verb"]
    assert [f["line"] for f in found] == [1]


def test_rhetorical_exceptions_are_not_reported(tmp_path):
    text = (
        "Do you want the short version or the long one? I can do either.\n\n"
        "The best part of the trip was the ferry. Result: 42 ms. Pro tip: back up first.\n\n"
        "What changed? The cache size, from 64 MB to 128 MB.\n\n"
        "What do you need from finance before Friday? Who owns the rollout?\n\n"
        "We kept our commitment: every refund went out within 30 days.\n\n"
        "## Performance\n\nSpeed matters most for checkout pages, where each 100 ms cost 1% of orders.\n"
    )
    result = scan_json(write(tmp_path, "e.md", text))
    assert result["findings"] == [], result["findings"]


def test_question_runs_and_heading_echo(tmp_path):
    runs = write(tmp_path, "q.md", "Do I know how it works? Where it breaks? Which corners it cut?\n")
    assert "question-run" in patterns(scan_json(runs))
    assert "question-run" not in patterns(scan_json(runs, "--profile", "technical"))
    echo = write(tmp_path, "h.md", "## Performance\n\nSpeed matters.\n\nWhen users hit a slow page, they leave.\n")
    assert "heading-echo" in patterns(scan_json(echo))
    real = write(tmp_path, "h2.md", "## Performance\n\nSpeed matters.\n")
    assert "heading-echo" not in patterns(scan_json(real))


def test_affective_adverbs_count_only_as_a_cluster(tmp_path):
    one = scan_json(write(tmp_path, "a1.md", "Surprisingly, the old build was faster.\n"))
    two = scan_json(write(tmp_path, "a2.md", "Surprisingly, it ran. Interestingly, it passed.\n"))
    assert "affective-adverb" not in patterns(one) and "affective-adverb" in patterns(two)


def test_vague_association_is_professional_only(tmp_path):
    path = write(tmp_path, "v.md", "Smoking is associated with lung cancer.\n")
    assert "vague-association" in patterns(scan_json(path))
    assert "vague-association" not in patterns(scan_json(path, "--profile", "academic"))


def test_document_ask_markers_are_not_placeholders(tmp_path):
    result = scan_json(write(tmp_path, "m.md", "The budget was [ASK AUTHOR: amount] last year. See [VERIFY: source].\n"))
    assert "placeholder" not in patterns(result)


def test_density_summary(tmp_path):
    result = scan_json(write(tmp_path, "d.md", "We delve into five topics today.\n"))
    assert result["words"] == 6
    assert result["summary"]["total"] == 1
    assert result["summary"]["per_1000_words"] == 166.7
    assert result["summary"]["by_family"]["lexical"] == {"count": 1, "per_1000_words": 166.7}


def test_non_english_text_gets_a_note(tmp_path):
    vi = "Ch\u00fang t\u00f4i \u0111\u00e3 ho\u00e0n th\u00e0nh vi\u1ec7c di chuy\u1ec3n d\u1eef li\u1ec7u trong ba ng\u00e0y v\u00e0 ki\u1ec3m tra t\u1eebng l\u00f4 b\u1eb1ng checksum.\n"
    result = scan_json(write(tmp_path, "vi.md", vi))
    assert any("English only" in n for n in result["notes"])
    assert scan_json(FIX / "clean.md")["notes"] == []


def test_reads_stdin_and_never_modifies_input(tmp_path):
    path = write(tmp_path, "orig.md", "We delve into it.\n")
    before = path.read_bytes()
    result = scan_json(None, stdin=path.read_text(encoding="utf-8"))
    assert result["file"] == "<stdin>" and "delve" in patterns(result)
    scan_json(path)
    assert path.read_bytes() == before


def test_input_errors_exit_2(tmp_path):
    proc = run(SCAN, str(tmp_path / "missing.md"))
    assert proc.returncode == 2 and "error" in proc.stderr
    assert run(SCAN, str(tmp_path)).returncode == 2
    assert run(SCAN, "--profile", "nonsense", str(FIX / "clean.md")).returncode == 2


def test_help_exits_zero():
    for script in (SCAN, DIFF):
        proc = run(script, "--help")
        assert proc.returncode == 0 and "usage" in proc.stdout.lower()


# ---------------------------------------------------------------- fact_diff


def diff_json(before, after, *args, stdin=None):
    proc = run(DIFF, "--json", *args, str(before), str(after), stdin=stdin)
    return proc, (json.loads(proc.stdout) if proc.stdout.strip() else None)


def edit(tmp_path, old, new, name="after.md"):
    text = (FIX / "before.md").read_text(encoding="utf-8")
    assert old in text, old
    return write(tmp_path, name, text.replace(old, new))


def lost_items(report, cat):
    return {i["item"] for i in report["categories"][cat]["lost"]}

def test_number_quoted_in_source_and_restated_unquoted_is_not_added(tmp_path):
    before = write(tmp_path, "before.md", 'The status email said "we have spent $104,300 so far".\n')
    after = write(tmp_path, "after.md", "Spend to date is $104,300 according to the status email.\n")
    _, report = diff_json(before, after)
    added = {i["item"] for i in report["categories"]["numbers"]["added"]}
    assert added == set()
    invented = write(tmp_path, "invented.md", "Spend to date is $110,000 according to the status email.\n")
    _, report = diff_json(before, invented)
    assert {i["item"] for i in report["categories"]["numbers"]["added"]} == {"110000 usd"}

def test_bare_figure_restated_with_unit_is_the_same_figure(tmp_path):
    before = write(tmp_path, "before.md", "Backoff caps at 512.0 and jitter is 0.1.\n")
    after = write(tmp_path, "after.md", "Backoff caps at 512 seconds with 0.1 seconds of jitter.\n")
    _, report = diff_json(before, after)
    assert report["categories"]["numbers"]["added"] == [] and report["categories"]["numbers"]["lost"] == []
    swapped = write(tmp_path, "swapped.md", "Backoff caps at 512.0 ms and jitter is 0.1.\n")
    unit_change = write(tmp_path, "unit.md", "Backoff caps at 512 s and jitter is 0.1.\n")
    _, report = diff_json(swapped, unit_change)
    assert added_items(report, "numbers") == {"512 s"}
    pct_before = write(tmp_path, "pct_before.md", "MAE fell by 12 points.\n")
    pct_after = write(tmp_path, "pct_after.md", "MAE fell by 12%.\n")
    _, report = diff_json(pct_before, pct_after)
    assert added_items(report, "numbers") == {"12%"}
    zero_tail = write(tmp_path, "zero_tail.md", "MAE fell by 12.0%.\n")
    _, report = diff_json(zero_tail, pct_after)
    assert report["categories"]["numbers"]["added"] == [] and report["categories"]["numbers"]["lost"] == []




def added_items(report, cat):
    return {i["item"] for i in report["categories"][cat]["added"]}


def test_pure_reword_passes():
    proc, report = diff_json(FIX / "before.md", FIX / "after_reword.md")
    assert proc.returncode == 0, proc.stdout
    assert report["ok"] is True and report["lost_total"] == 0 and report["added_total"] == 0
    human = run(DIFF, str(FIX / "before.md"), str(FIX / "after_reword.md"))
    assert human.returncode == 0 and "[OK] no mechanical preservation errors found" in human.stdout
    assert "does not confirm meaning" in human.stdout


def test_identical_text_passes():
    proc, report = diff_json(FIX / "before.md", FIX / "before.md")
    assert proc.returncode == 0 and report["ok"]


def test_dropped_negation_is_caught(tmp_path):
    after = edit(tmp_path, "did not confirm it", "confirmed it")
    proc, report = diff_json(FIX / "before.md", after)
    assert proc.returncode == 1
    assert "not" in lost_items(report, "negations")
    assert report["lost_total"] >= 1
    human = run(DIFF, str(FIX / "before.md"), str(after))
    assert human.returncode == 1 and "[FLAG] negations lost" in human.stdout


def test_changed_number_is_caught(tmp_path):
    after = edit(tmp_path, "12%", "21%")
    proc, report = diff_json(FIX / "before.md", after)
    assert proc.returncode == 1
    assert lost_items(report, "numbers") == {"12%"} and added_items(report, "numbers") == {"21%"}


def test_changed_currency_amount_is_caught(tmp_path):
    after = edit(tmp_path, "$1,000", "$100")
    _, report = diff_json(FIX / "before.md", after)
    assert lost_items(report, "numbers") == {"1000 usd"} and added_items(report, "numbers") == {"100 usd"}


def test_added_citation_is_caught(tmp_path):
    after = edit(tmp_path, "Only 3 of 5 sites are affected.", "Only 3 of 5 sites are affected [12].")
    proc, report = diff_json(FIX / "before.md", after)
    assert proc.returncode == 1 and added_items(report, "citations") == {"[12]"}
    assert report["categories"]["citations"]["lost"] == []


def test_dropped_citation_and_author_year_are_caught(tmp_path):
    after = edit(tmp_path, " [4]", "")
    assert lost_items(diff_json(FIX / "before.md", after)[1], "citations") == {"[4]"}
    after = edit(tmp_path, "According to Smith (2020), ", "")
    assert lost_items(diff_json(FIX / "before.md", after)[1], "citations") == {"Smith (2020)"}


def test_weakened_certainty_is_caught(tmp_path):
    after = edit(tmp_path, "may reduce", "reduces")
    proc, report = diff_json(FIX / "before.md", after)
    assert proc.returncode == 1 and lost_items(report, "certainty") == {"may"}


def test_changed_scope_word_is_caught(tmp_path):
    after = edit(tmp_path, "Only 3 of 5", "All 3 of 5")
    _, report = diff_json(FIX / "before.md", after)
    assert lost_items(report, "scope") == {"only"} and added_items(report, "scope") == {"all"}


def test_lost_name_url_code_and_quote_are_caught(tmp_path):
    cases = [
        ("Acme Corp reported", "The company reported", "names", "Acme Corp"),
        ("https://example.com/report", "the report page", "urls", "https://example.com/report"),
        ("`make audit`", "the audit command", "code", "make audit"),
        ('"costs never fall quickly"', '"costs rarely fall quickly"', "quotes", "costs never fall quickly"),
    ]
    for old, new, cat, item in cases:
        proc, report = diff_json(FIX / "before.md", edit(tmp_path, old, new))
        assert proc.returncode == 1, (cat, proc.stdout)
        assert item in lost_items(report, cat), (cat, report["categories"][cat])


def test_unit_change_is_caught(tmp_path):
    before = write(tmp_path, "b.md", "Latency fell to 10 ms on average.\n")
    after = write(tmp_path, "a.md", "Latency fell to 10 s on average.\n")
    proc, report = diff_json(before, after)
    assert proc.returncode == 1
    assert lost_items(report, "numbers") == {"10 ms"} and added_items(report, "numbers") == {"10 s"}


def test_equivalent_spellings_do_not_flag(tmp_path):
    pairs = [
        ("It does not work.", "It doesn't work."),
        ("It cannot work.", "It can't work."),
        ("We shipped 1,000 units.", "We shipped 1000 units."),
        ("Growth was 5 percent.", "Growth was 5%."),
        ("There were three failures.", "There were 3 failures."),
        ("It costs $5.", "It costs 5 dollars."),
    ]
    for old, new in pairs:
        proc, report = diff_json(write(tmp_path, "b.md", old + "\n"), write(tmp_path, "a.md", new + "\n"))
        assert proc.returncode == 0, (old, new, proc.stdout)


def test_spelled_number_change_is_caught(tmp_path):
    proc, _ = diff_json(write(tmp_path, "b.md", "There were three failures.\n"), write(tmp_path, "a.md", "There were four failures.\n"))
    assert proc.returncode == 1


def test_decimal_precision_change_is_caught(tmp_path):
    proc, report = diff_json(write(tmp_path, "b.md", "The score was 0.50.\n"), write(tmp_path, "a.md", "The score was 0.5.\n"))
    assert proc.returncode == 1 and lost_items(report, "numbers") == {"0.50"}


def test_sentence_initial_capitals_are_not_names(tmp_path):
    proc, _ = diff_json(write(tmp_path, "b.md", "Moreover, the run finished. Overall it was fine.\n"),
                        write(tmp_path, "a.md", "The run finished and it was fine.\n"))
    assert proc.returncode == 0


def test_spelled_and_hyphenated_numbers_match_their_digit_forms(tmp_path):
    pairs = [
        ("The rehearsal took 6 minutes.", "The rehearsal took six minutes."),
        ("It was 3 weeks of work.", "It was three-week work."),
        ("A 49-minute outage.", "The outage lasted 49 minutes."),
        ("The gateway cut requests off at 60 seconds.", "A 60-second gateway cutoff."),
        ("Support runs around the clock, 24/7.", "Support runs 24/7, around the clock."),
    ]
    for old, new in pairs:
        proc, report = diff_json(write(tmp_path, "b.md", old + "\n"), write(tmp_path, "a.md", new + "\n"))
        assert proc.returncode == 0, (old, new, proc.stdout)


def test_changed_unit_on_spelled_number_is_caught(tmp_path):
    proc, report = diff_json(write(tmp_path, "b.md", "The rehearsal took six minutes.\n"),
                             write(tmp_path, "a.md", "The rehearsal took six hours.\n"))
    assert proc.returncode == 1 and lost_items(report, "numbers") == {"6 min"}


def test_split_ratio_is_one_number(tmp_path):
    _, report = diff_json(write(tmp_path, "b.md", "Open 24/7.\n"), write(tmp_path, "a.md", "Open 24/7.\n"))
    assert report["categories"]["numbers"]["before_count"] == 1


def test_contractions_of_pronoun_i_are_not_names(tmp_path):
    proc, report = diff_json(write(tmp_path, "b.md", "Khanh Le writes to Prof. Marchetti.\n"),
                             write(tmp_path, "a.md", "I’m Khanh Le. Because I’d like to write, I’ll write to Prof. Marchetti.\n"))
    assert added_items(report, "names") == set(), report["categories"]["names"]


def names_diff(tmp_path, before, after):
    _, report = diff_json(write(tmp_path, "b.md", before + "\n"), write(tmp_path, "a.md", after + "\n"))
    return lost_items(report, "names"), added_items(report, "names")


def test_names_regrouped_from_words_already_present_are_not_added(tmp_path):
    cases = [
        ("Khanh Le writes to Prof. Marchetti.", "Dear Professor Marchetti,\n\nKhanh Le here."),
        ("We run Jenkins and CI on Linux.", "We run Jenkins CI on Linux."),
        ("Applying as a prospective student for the MSc Marine Ecology.", "Prospective MSc Marine Ecology student here."),
        ("Thanks to O'Brien for the review.", "Thanks to O\u2019Brien\u2019s team for the review."),
        ("Khanh Le wrote this.", "Khanh Le wrote this, and They\u2019re Khanh Le."),
        ("Khanh Le met Prof. Marchetti.", "Hello Dr Marchetti, Hi Khanh Le."),
    ]
    for before, after in cases:
        lost, added = names_diff(tmp_path, before, after)
        assert (lost, added) == (set(), set()), (before, after, lost, added)


def test_invented_name_word_is_still_added_and_reported_as_written(tmp_path):
    _, added = names_diff(tmp_path, "Khanh Le writes to Prof. Marchetti.", "Dear Professor Marchetti Rossi,\n\nKhanh Le here.")
    assert added == {"Dear Professor Marchetti Rossi"}
    _, added = names_diff(tmp_path, "We run Jenkins on Linux.", "We run Jenkins CI and Terraform on Linux.")
    assert added == {"Jenkins CI", "Terraform"}


def test_dropped_real_name_word_is_still_lost(tmp_path):
    lost, _ = names_diff(tmp_path, "Khanh Le met Dr Marchetti.", "Khanh Le met the professor.")
    assert lost == {"Dr Marchetti"}
    lost, _ = names_diff(tmp_path, "Khanh Le writes to Dear Professor Marchetti Rossi.", "Khanh Le writes to Dear Professor Marchetti.")
    assert lost == {"Dear Professor Marchetti Rossi"}


def test_fenced_code_change_is_caught(tmp_path):
    before = write(tmp_path, "b.md", "Run this:\n\n```sh\nmake test\n```\n")
    after = write(tmp_path, "a.md", "Run this:\n\n```sh\nmake check\n```\n")
    proc, report = diff_json(before, after)
    assert proc.returncode == 1
    assert lost_items(report, "code_blocks") == {"make test"} and added_items(report, "code_blocks") == {"make check"}


def test_numbers_inside_code_and_urls_are_not_double_counted(tmp_path):
    before = write(tmp_path, "b.md", "Use `retry(3)` and https://example.com/v2/items.\n")
    after = write(tmp_path, "a.md", "Call `retry(3)` and https://example.com/v2/items.\n")
    proc, report = diff_json(before, after)
    assert proc.returncode == 0
    assert report["categories"]["numbers"]["before_count"] == 0


def test_ignore_category(tmp_path):
    after = edit(tmp_path, "Acme Corp reported", "The company reported")
    assert diff_json(FIX / "before.md", after)[0].returncode == 1
    proc, report = diff_json(FIX / "before.md", after, "--ignore", "names")
    assert proc.returncode == 0 and report["ignored"] == ["names"] and "names" not in report["categories"]


def test_json_shape(tmp_path):
    after = edit(tmp_path, "12%", "21%")
    _, report = diff_json(FIX / "before.md", after)
    assert set(report) == {"before", "after", "ok", "lost_total", "added_total", "ignored", "categories",
                           "markers_before", "markers_after"}
    assert set(report["categories"]["numbers"]) == {"before_count", "after_count", "lost", "added"}
    entry = report["categories"]["numbers"]["lost"][0]
    assert set(entry) == {"item", "before", "after", "context"} and entry["before"] == 1 and entry["after"] == 0
    assert "12%" in entry["context"]


def test_inserted_author_markers_are_not_counted_as_added_facts(tmp_path):
    before = write(tmp_path, "b.md", "This was a cultural shift. Studies show builds matter.\n")
    after = write(tmp_path, "a.md", "This was a cultural shift. [ASK AUTHOR: What changed beyond run time?] "
                                    "Studies show builds matter. [VERIFY: Cite the study.]\n")
    proc, report = diff_json(before, after)
    assert proc.returncode == 0, proc.stdout
    assert report["markers_after"] == 2 and report["markers_before"] == 0
    assert "not compared" in run(DIFF, str(before), str(after)).stdout


def test_stdin_for_one_side_and_error_exits(tmp_path):
    after_text = (FIX / "after_reword.md").read_text(encoding="utf-8")
    proc = run(DIFF, "--json", str(FIX / "before.md"), "-", stdin=after_text)
    assert proc.returncode == 0 and json.loads(proc.stdout)["after"] == "<stdin>"
    assert run(DIFF, str(tmp_path / "nope.md"), str(FIX / "before.md")).returncode == 2
    assert run(DIFF, "-", "-", stdin="x").returncode == 2


def test_never_modifies_inputs(tmp_path):
    after = edit(tmp_path, "12%", "21%")
    snapshot = (after.read_bytes(), (FIX / "before.md").read_bytes())
    run(DIFF, str(FIX / "before.md"), str(after))
    assert snapshot == (after.read_bytes(), (FIX / "before.md").read_bytes())


@pytest.mark.parametrize("script", [SCAN, DIFF])
def test_scripts_are_stdlib_only_and_documented(script):
    source = script.read_text(encoding="utf-8")
    assert source.startswith("#!/usr/bin/env python3") and '"""' in source[:200]
    assert 'if __name__ == "__main__":' in source


def test_exact_calculation_from_source_figures_is_derived_not_added(tmp_path):
    before = write(tmp_path, "before.md", "Licences cost €5,800 and €612. Relay is €0.035 per request; "
                                          "we send 52,000 requests and 40 tickets.\n")
    after = write(tmp_path, "after.md", "Licences total €6,412; requests cost €1,820. "
                                        "That is €6,500 overall, 92 tickets in 2027.\n")
    _, report = diff_json(before, after)
    derived = {i["item"]: i["from"] for i in report["categories"]["numbers"].get("derived", [])}
    assert set(derived) == {"6412 eur", "1820 eur"}
    # a round guess, a bare count and a year are not calculations
    assert {"6500 eur", "92", "2027"} <= added_items(report, "numbers")


def test_rate_times_volume_and_the_gap_between_two_costs_are_derived(tmp_path):
    before = write(tmp_path, "before.md", "Load is 40,000 requests per day. Quote A: 0.042 per request. "
                                          "Quote B: 0.051 per request.\n")
    after = write(tmp_path, "after.md", "That is 1,680 a day for A and 2,040 for B, a gap of 360. "
                                        "Over 365 days that is 131,400.\n")
    _, report = diff_json(before, after)
    derived = {i["item"] for i in report["categories"]["numbers"].get("derived", [])}
    assert derived == {"1680", "2040", "360"}
    # annualising assumes a 365-day year the source never states: still flagged
    assert {"131400", "365 day"} <= added_items(report, "numbers")


def test_round_fraction_or_time_unit_times_a_count_is_not_a_calculation(tmp_path):
    # 0.5 x 4,000 and 30 min x 100 land on round figures by chance; inventing 2,000 or 3,000 min must stay flagged
    before = write(tmp_path, "before.md", "Ratio 0.5 across 4,000 tickets. Calls last 30 min; 100 calls a week.\n")
    after = write(tmp_path, "after.md", "That is 2,000 tickets and 3,000 min of calls.\n")
    _, report = diff_json(before, after)
    assert report["categories"]["numbers"].get("derived", []) == []
    assert {"2000", "3000 min"} <= added_items(report, "numbers")


def test_bare_restatement_of_a_figure_the_source_gives_with_a_unit_is_not_added(tmp_path):
    before = write(tmp_path, "before.md", "Sizing took 90 minutes. Latency fell from 180 ms to 45 ms. Churn was 12%.\n")
    after = write(tmp_path, "after.md", "Sizing took 25 minutes instead of 90. The 180-to-45 drop held. "
                                        "Churn was 12. A new 70 appears.\n")
    _, report = diff_json(before, after)
    added = added_items(report, "numbers")
    assert "90" not in added and "180" not in added
    assert {"12", "70"} <= added  # a percent stays strict; an unrelated bare figure stays flagged


def test_thread_position_counters_are_not_figures_but_a_mid_sentence_ratio_is(tmp_path):
    before = write(tmp_path, "before.md", "Builds fell from 14 min to 9 min.\n")
    after = write(tmp_path, "after.md", "1/3 Builds fell from 14 min to 9 min.\n\nThe cache did it. 2/3\n\n"
                                        "(3/3) Only 2/5 runners were warm.\n")
    _, report = diff_json(before, after)
    added = added_items(report, "numbers")
    assert not {"1/3", "2/3", "3/3"} & added
    assert added  # the 2/5 inside the sentence is a stated figure


def test_a_date_is_one_fact_in_any_format_and_a_moved_date_is_still_flagged(tmp_path):
    before = write(tmp_path, "before.md", "Go-live is planned for 2026-04-06. Review on 3 March 2026.\n")
    after = write(tmp_path, "after.md", "Go-live is planned for 6 April. The review is on March 3, 2026. "
                                        "Training starts on 9 April.\n")
    _, report = diff_json(before, after)
    numbers = report["categories"]["numbers"]
    assert {"date:--04-09"} == added_items(report, "numbers")  # an invented day is still a new fact
    assert numbers["lost"] == []  # 2026-04-06 -> 6 April and 3 March 2026 -> March 3, 2026 are the same dates


def test_day_ranges_and_a_year_inside_an_iso_date_are_source_facts(tmp_path):
    before = write(tmp_path, "before.md", "Testing 2026-07-13 to 2026-07-31; pilot 2026-08-03 to 2026-08-14.\n")
    after = write(tmp_path, "after.md", "Testing ran 13–31 July and the pilot 3 to 14 August, all in 2026. "
                                        "The review moved to 20-August.\n")
    _, report = diff_json(before, after)
    assert added_items(report, "numbers") == {"date:--08-20"}


def test_a_small_gap_is_a_calculation_only_when_its_operands_sit_beside_it(tmp_path):
    before = write(tmp_path, "before.md", "Limit: 300 ms. Vendor A measured 310 ms. Vendor B measured 240 ms.\n")
    after = write(tmp_path, "after.md", "Vendor A measured 310 ms, 10 ms over the 300 ms limit. "
                                        "Elsewhere in a long paragraph that runs on about other things entirely, "
                                        "Vendor B had a 70 ms margin.\n")
    _, report = diff_json(before, after)
    numbers = report["categories"]["numbers"]
    assert {d["item"] for d in numbers.get("derived", [])} == {"10 ms"}
    assert "70 ms" in added_items(report, "numbers")  # operands not beside it: still a figure to check


def test_template_field_labels_and_words_after_a_colon_are_not_new_names(tmp_path):
    before = write(tmp_path, "before.md", "The trustees meet on 19 November about the fee.\n")
    after = write(tmp_path, "after.md", "Constraints: Return one page. Keep quotes exact.\n"
                                        "Open with one line: Reviewer-Model: <id>\nVERDICT: ready\n"
                                        "We will ask Marisol Okafor about the fee.\n")
    _, report = diff_json(before, after)
    names = added_items(report, "names")
    assert not {"VERDICT", "Reviewer-Model", "Return", "Keep"} & names
    assert "Marisol Okafor" in names  # a new person mid-sentence is still flagged


def test_stacked_disclaimers_are_listed_but_a_single_limit_is_not(tmp_path):
    defended = ("The pilot cut wait times by a fifth. This does not establish a cause. The survey is a snapshot, "
                "not a trend. Staffing changed too, so the result does not isolate the new rota. The cost figure "
                "is an estimate rather than an invoice. The model is an illustration, not a forecast. "
                "We ran it for six weeks. Nurses liked it. ")
    found = patterns(scan_json(write(tmp_path, "a.md", defended), "--profile", "professional"))
    assert "caveat-stack" in found
    plain = ("The pilot cut wait times by a fifth over six weeks. Staffing also changed in week three, so part of "
             "the drop may come from that. Nurses asked to keep the new rota, and we will run it through winter.")
    assert "caveat-stack" not in patterns(scan_json(write(tmp_path, "b.md", plain), "--profile", "professional"))


def test_inline_working_is_listed_and_table_placeholders_are_not_dashes(tmp_path):
    text = ("Errors fell by 335 units (5,535 - 5,200) in the second half.\n\n"
            "| Period | Before | After |\n|---|---|---|\n| H1 | 12 | \u2014 |\n| H2 | 10 | \u2014 |\n| H3 | 9 | \u2014 |\n")
    found = patterns(scan_json(write(tmp_path, "c.md", text), "--profile", "academic"))
    assert "inline-arithmetic" in found
    assert "em-dash-density" not in found
