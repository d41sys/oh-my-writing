# Oh My Writing benchmark

Measures whether each skill changes agent behavior on realistic writing tasks, compared with the same agent and prompt without the skills installed. Every case is graded by deterministic checks; an optional blind pairwise judge adds a quality preference.

```text
evals/
├── cases/<skill>/<case>.json   # one task per file; cases/style/ is the style track (below)
├── fixtures/<case-slug>/       # document folders copied into a case's workspace (binary files allowed)
├── run.py                      # runs cases on agent hosts (with repetitions), then grades
├── grade.py                    # deterministic checks; re-grades a results directory
├── review_pairs.py             # one-file blind A/B page for rating pairs yourself
├── stats.py                    # deterministic statistics benchmark: fixed metrics on every output, CIs, paired comparisons
├── gate.py                     # regression gate: freeze a reference, fail when a skill revision is worse on the statistics
├── gate/                       # config.json (tolerances), reference.json (frozen reference run), weak_spots.json (where the reference is weaker)
└── results/<run-id>/           # git-ignored: workspaces, replies, logs, results.json, report.md
```

## Run

```bash
python3 evals/run.py --host codex --host claude --jobs 4          # all cases, with and without skills
python3 evals/run.py --host codex --cases 'anti-slop-editing/*'    # one skill
python3 evals/run.py --host codex --judge codex                    # add blind pairwise preference
python3 evals/run.py --host codex --cases 'style/*' --judge codex   # style track: human register and fidelity judged apart
python3 evals/run.py --host codex --judge codex --judge-mode style  # judge every selected case on those two questions
python3 evals/run.py --host codex --cases 'project-report/*' --repeat 3 --jobs 4 \
    --judge codex --out evals/results/project-report-bench          # report benchmark: 3 repetitions, visual judge
python3 evals/review_pairs.py evals/results/project-report-bench    # blind A/B page for you -> review/<run-id>.html
python3 evals/grade.py evals/results/<run-id>                       # re-grade without re-running
python3 evals/grade.py --validate                                  # check every case file
```

Conditions:

- `skill`: every skill under `skills/` is copied (not linked) into the temporary workspace (`.agents/skills/` for Codex, `.claude/skills/` for Claude Code), so the agent can neither write through to the repository nor see its path. The prompt never names a skill, so the run also tests whether the description triggers.
- `baseline`: the same workspace, prompt and host with no skills copied.

Skills installed at user level that are not part of this repository (for example `~/.agents/skills/diagram-design`) are visible to both conditions on purpose: the benchmark then measures what the repository's skills add. `run.json` records the installed diagram-design `metadata.version` and the Codex and Claude Code versions.

The runner refuses to run when a skill with the same name is installed at user level (`~/.agents/skills`, `~/.claude/skills`), because the baseline would then also see it. `--allow-contaminated` overrides and marks the run, but the baseline is then not a true baseline. If you installed the skills with the README loop, move those links aside while benchmarking.

`--repeat N` runs every (case, host, condition) N times; run folders get an `__r<k>` suffix and `meta.json` records `rep`. The grader pairs skill and baseline per (case, host, repetition), so a crash in one repetition excludes only that pair. `--timeout` is the default per-run limit; a case's own `timeout` wins.

`--resume` with the same `--out` keeps finished runs and judge verdicts (per repetition) and redoes only errored or missing ones. When a host refuses for usage limits, the remaining runs on that host are skipped immediately (recorded as host errors) so `--resume` can finish them after the limit resets.

## Competitor skills

Besides `skill` and `baseline`, the runner can install a third-party skill in place of ours (`--condition competitor:<name>`, repeatable; `--competitors` adds every competitor). The names, source folders, license, case mapping and install layout are in `evals/competitors.json`; the skills themselves are read from the local source cache (`.cache/omw_sources/<owner>__<repo>/`, git-ignored) and copied into the run's temporary workspace only. Nothing from the cache is copied into this repository or committed. The runner fails before any run when a cache folder or listed path is missing.

| competitor | source | competes on (our skill) | also `style/*` |
|---|---|---|---|
| `humanizer` | blader/humanizer | anti-slop-editing | yes |
| `avoid-ai-writing` | conorbronsdon/avoid-ai-writing (`skills/avoid-ai-writing`) | anti-slop-editing | yes |
| `great-writer` | d-wwei/great-writer | post-writing | yes |
| `marketing-copywriting` | coreyhaines31/marketingskills (`skills/copywriting`) | post-writing | no |
| `proficiently-cover-letter` | proficientlyjobs/proficiently-claude-skills (`skills/cover-letter` + `shared`) | career-documents | no |
| `resumeskills` | Paramchoudhary/ResumeSkills (cover-letter-generator, cold-email-writer, resume-tailor, resume-bullet-writer) | career-documents | no |
| `doc-coauthoring` | anthropics/skills (`skills/doc-coauthoring`) | structured-drafting | no |

A competitor runs only on the cases whose `skill` is in its `competes_on` list, plus every `style/*` case when it has `style: true`. Its workspace holds only its own skill folders, so the competitor sees none of ours, and the prompt is the same as in the other conditions. Run folders are named `<case>__<host>__competitor-<name>[__r<k>]`; `meta.json` records `condition: competitor-<name>`, `competitor: <name>` and whether any of the installed skills was opened (`skill_loaded`, by folder name: a `skill://<name>` read on omp, a `skills/<name>/SKILL.md` read or `Skill` call elsewhere). `run.json` records, per competitor, the repository, the commit pinned in `.cache/omw_sources/SHAS.txt` (null when unlisted), the license, the installed skills and the mapping. Two caveats apply: these skills were written for other tasks, so low scores on checks such as "no added facts" say how well a skill fits this benchmark, not how good it is elsewhere; and the proficiently skills expect a job-search data folder and a job URL fetcher that the workspace does not have.

Pairing: skill against baseline is paired exactly as before. Each competitor is paired with the baseline, and with our skills, on the (case, host, repetition) triples where both sides produced a gradable run, so a competitor that covers only some cases never removes pairs from the main table. The report adds a "Competitors" table (competitor minus baseline, ours minus competitor, each with its own n and the competitor's load rate) and one extra column per competitor in the case table; `results.json` carries the same numbers under `summary.by["<host>/<skill>"].competitors`.

`--judge-pairs A:B` (repeatable or comma-separated) chooses which pairs the blind judge compares; each side is `skill`, `baseline`, `competitor` (every competitor of this run) or a competitor name. Without it only `skill:baseline` is judged, as before. Entries for other pairs carry `pair` in `judge.json`, name the winning condition in `winner` (style entries name it in `human` and `faithful`), use their own judge folders and presentation-order seed, and get their own report section; they never enter the `skill:baseline` tally. Judging needs both outputs, so cases a competitor did not run are skipped.

Add competitors to a finished run instead of redoing it (finished runs and judge verdicts are kept, only competitor runs execute):

```bash
python3 evals/run.py --host omp --repeat 3 --competitors --jobs 4 --judge omp --judge-pairs skill:competitor \
  --resume --out evals/results/v-voice-omp
```

## Case format

```json
{
  "id": "anti-slop-editing/edit-keeps-negation",
  "skill": "anti-slop-editing",
  "description": "One line: the behavior this case tests.",
  "prompt": "A natural user request that never names a skill and says where to save the result, e.g. 'Clean up draft.md and save the edited version to out/draft.md.'",
  "files": { "draft.md": "input text" },
  "output": "out/draft.md",
  "checks": [ { "type": "preserves", "source": "draft.md", "categories": ["numbers", "negations"] } ]
}
```

- `id` equals `<folder>/<file name without .json>`; the folder is the skill's name, or `style` for the style track. `skill` is a directory under `skills/` and is what the report groups by.
- `files` are written into the workspace; keep inputs short (under about 500 words) and fictional.
- `output` is the deliverable file the agent must write. A missing output file fails the case.
- Each check may set `"target"`: `output` (default), `reply` (the agent's final message) or `both`.
- Optional `fixtures`: `"evals/fixtures/<case-slug>"`, a folder copied verbatim (binary-safe, relative paths and modification times kept) into the workspace root. `files` may then be `{}`, or both may be used. For text checks the grader extracts the fixtures' text (docx, xlsx, pptx, pdf via `pdftotext`, eml, html, csv ... through `skills/project-report/scripts/inventory.py`), so `no_added_facts`, `preserves` and `similarity` see Office and PDF content; a fixture is named in `source`/`sources` by its path inside the folder (`docs/budget.xlsx`). `no_added_facts` also treats the input file names, and relative links to inputs or into the output folder, as known. CSV/TSV sources are read cell by cell so `14,171` is not one number.
- Optional `timeout` (seconds) overrides `--timeout` for this case (report cases use 2400).
- Optional `deliverables`: files the agent is asked to write, e.g. `["out/report.md", "out/report.html"]`. `output` stays the primary text file; the grader records in `results.json` which deliverables exist.
- Optional `judge`: `{"mode": "visual", "render": "out/report.html"}` switches the blind judge for this case to the visual judge (below). `render` must be listed in `deliverables`. `{"mode": "style"}` switches it to the style judge (below) and takes no `render`. Other cases keep the text judge.

Check types:

| type | fields | passes when |
|---|---|---|
| `contains` | `values`, `case_sensitive` (default false) | every value appears |
| `contains_any` | `values`, `case_sensitive` | at least one value appears |
| `not_contains` | `values`, `case_sensitive` | no value appears |
| `regex` / `not_regex` | `pattern` (Python, multiline) | the pattern matches / does not match |
| `no_added_facts` | `sources` (default: all input files plus the prompt), `categories` (default `numbers`, `citations`, `urls`), `allow` | the output adds no item of those categories that is absent from the sources (fact_diff "added") |
| `preserves` | `source`, `categories`, `allow_lost` | no item of those categories in `source` is lost from the output (fact_diff "lost") |
| `slop_absent` | `patterns` (slop_scan pattern ids), `profile` | none of those patterns is found in the output |
| `max_slop` | `max`, `profile` | slop_scan reports at most `max` findings in the output |
| `slop_density` | `max`, `profile` | slop_scan findings per 1000 prose words is at most `max` (fails when the text has no prose words); use it where length varies |
| `rhythm` | `min_cv` (default 0.4), `min_sentences` (default 5) | the coefficient of variation (standard deviation / mean) of words per sentence in running prose is at least `min_cv`; passes unjudged below `min_sentences` sentences |
| `markers` | `min`, `max`, `kinds` (default `ASK AUTHOR`, `VERIFY`, `UNTESTED`) | the count of `[KIND ...]` markers is within range (target defaults to `both`) |
| `similarity` | `source`, `min`, `max` | word-level similarity ratio (0–1) between source and output is within range |
| `word_count` | `min`, `max` | output word count is within range |
| `facts_recalled` | `facts` (list of `{"id", "any": [regex, ...]}`), `min` (default 0.8) | the share of facts with at least one matching regex (case-insensitive, over the target text) is at least `min`; the detail lists the missed ids |
| `diagrams` | `min`, `max`, `numbers_from_sources`, `allow`, `self_check`, `labels_any` (list of `{"id", "any": [regex]}`), `labels_none` (list of regex) | the count of diagrams is within range, and each enabled option holds (see below) |
| `html_deliverable` | `path`, `no_script`, `self_contained`, `min_figures` | the file exists and each enabled option holds (see below); options are opt-in |

A diagram is any of: an `.svg` file under the output folder (`out/`); an `.html` file under `out/` other than the report HTML that contains a non-decorative `<svg`; a non-decorative inline `<svg` (no `aria-hidden="true"`) in the report HTML; a ` ```mermaid ` block in the output text; a PNG/JPEG/WebP file the report references (`![](x.png)` or `<img>`). Each `<svg>` counts once, and the same diagram reached two ways (a diagram file inlined into the report page) is deduplicated by its visible text (by its markup when it has none). The report HTML is `html_deliverable.path`, the `.html` entries of `deliverables`, or the output path with `.html`.

- `numbers_from_sources`: every number in a diagram's visible text (`<text>`, mermaid labels; never mermaid node ids or identifiers like `Q3`) must appear in the input texts, the input file names, the prompt or `allow`. Units and currency are ignored (`48500` matches `48,500 USD`). Raster diagrams count toward `min`/`max` but are reported as `unverifiable`; the check fails when more than half of the diagrams are unverifiable.
- `self_check`: runs `~/.agents/skills/diagram-design/scripts/self_check.py` on the diagram `.html` files; skipped, with a note in the detail, when the script is absent.
- `labels_any`: each listed label must appear in the visible text of some diagram. `labels_none`: no diagram's text may match any listed regex (use it to catch invented components).
- `html_deliverable.no_script`: no `<script>`, no `on*` attributes, no `javascript:` URLs. `self_contained`: every local `src`/`href`/CSS `url()` resolves to a file inside the workspace, and nothing is loaded from the network except fonts.googleapis.com and fonts.gstatic.com (plain `<a href="https://...">` hyperlinks are not resources). `min_figures`: at least that many visible inline `<svg>`, `<img>` and `<object>` elements.

fact_diff categories: `numbers`, `negations`, `certainty`, `scope`, `names`, `urls`, `code`, `code_blocks`, `quotes`, `citations`. Inserted `[ASK AUTHOR]`/`[VERIFY]` markers are never counted as facts.

## Style track

`cases/style/` holds eight cases about the register of text a reader receives: a client email, a decision memo, a project update, a LinkedIn post, a cover letter and an incident email, each written from the user's notes; an 800-word article written from an outline; and the revision of a slop-heavy announcement. The prompts read like a real user's, never name a skill, and the inputs hold every fact the text needs, so a gap is rare. Each case checks:

- `no_added_facts` (and `preserves` where the deliverable should carry every figure): nothing invented, nothing dropped.
- `slop_density`: slop_scan findings per 1000 words. A short text is allowed one stray finding; the article only about three. The scanner imports with bytecode off.
- `rhythm`: sentence-length variation, which catches the uniform cadence of generated prose.
- Case-specific facts, bans from the user's own prompt (no hashtags, no promise of "never again"), stock openers and closers of the genre, and `markers` with `max` 0 on the output. The notes carry every fact the text needs and the text goes to its reader, so a gap marker in the saved file is a defect; a question for the author goes in the reply.

The mechanical checks find tells that a word list can see and facts that a diff can see. They do not decide which text reads better, so the track also uses the style judge.

### Style judge

`judge.mode: "style"` in a case, or `--judge-mode style` for every case in the run, replaces the single-preference judge with two separate questions answered in both presentation orders:

1. **Human**: which reads as written by a skilled human professional, with fewer AI tells (stock phrases, hedging fog, symmetric lists, empty openers and closers)?
2. **Faithful**: which is more faithful to the inputs (every figure, name, date, limit and commitment kept; nothing invented; nothing material dropped)?

Gap markers (`[ASK AUTHOR: ...]`, `[VERIFY: ...]`, `[UNTESTED ...]`) are stripped from both texts before the judge sees them (`grade.strip_markers`: a marker inside a sentence is cut out, a line or heading left empty is dropped), so a text is neither rewarded nor punished for how it handles a gap; whether a marker belongs in the file is the `markers` check's job. A response can win one question and lose the other. `judge.json` stores `human` and `faithful` (each `skill`, `baseline`, `tie`, `inconsistent` or `error`) and both pick lists per entry; `winner` is `style`, or `error` when either answer is missing. The report has a separate "Blind style judge" section with one column per question, and style entries are never added to the overall pairwise tally. `--judge-mode style` on a visual case judges its extracted text, without page images.

## Visual judge and review page

`--judge` runs a blind pairwise judge in both presentation orders. For a case with `judge.mode` `visual` the judge also sees page images: the report HTML is printed to PDF with headless Chrome (`CHROME` overrides the path) and the first six pages are rasterised with `pdftoppm -r 60`. Codex receives them with `codex exec -i`; Claude Code is told to open them with the Read tool. The prompt holds the task, the extracted source text (each file cut to 5000 characters, 60000 in total, with the cut stated), both report texts (cut at 30000 characters) and asks for 1-5 scores on accuracy against the sources, covering what the reader needs, professional tone, diagram usefulness and design, and layout, then a verdict. If rendering fails for either side the judge falls back to text only for both, and `judge.json` says so (`render_note`). Scores are stored in `judge.json` per pair and averaged per condition in `report.md`.

`python3 evals/review_pairs.py <run_dir>` writes `review/<run-id>.html`, a self-contained page for you to rate the same pairs blind: per (case, repetition) the task, the source documents (expandable) and report A and B side by side (the HTML report in a sandboxed iframe, or the markdown as text), in seeded random order. Rate each pair A better / Tie / B better, add a note; ratings persist in the browser (localStorage); Export JSON downloads them with the A/B mapping. Reveal unlocks once every pair is rated and shows which side had the skills. `review/` is a local folder: do not commit it.

## Statistics benchmark and regression gate

The checks and the judge answer "did this case pass" and "which text is preferred". `stats.py` adds numbers that do not depend on a case's own wording: the same fixed rules (`METRICS_VERSION`) run over every output, so two skill revisions, or a skill and a competitor, can be compared metric by metric. No model is involved: the same files give the same numbers, and the bootstrap uses a fixed seed (20261017, 2000 resamples).

```bash
python3 evals/stats.py evals/results/<run-id> [--json out.json] [--detail ALL|<skill>]   # metrics, aggregates, with-skills minus baseline (and minus each competitor, all and loaded-only)
python3 evals/stats.py --compare <run-A> <run-B> --condition skill                       # did revision B get worse than A, and where
python3 evals/stats.py --metrics                                                          # every definition, direction and reason
python3 evals/gate.py freeze evals/results/<run-id> --model <name>                       # write evals/gate/reference.json
python3 evals/gate.py check  evals/results/<new-run-id> [--all]                          # exit 1 on regression
python3 evals/gate.py aa     evals/results/<run-id>                                      # noise test: relabelled repetitions must pass
python3 evals/gate.py weak   evals/results/<other-run-id>                                # record where the reference is worse than another run
```

**Metrics** (all computed on the deliverable file; prose metrics on the text with gap markers removed; `better` is the direction a reader would call an improvement; `-` means context only):

| metric | better | definition | why a reader cares |
|---|---|---|---|
| `invented_facts` | lower | numbers, URLs, citations (names where the case's `no_added_facts` covers names) in no input, input file name or prompt; fact_diff "added"; the case's `allow` list applies | an invented figure or link is a lie the reader cannot see |
| `invented_facts_per_1000w` | lower | the same, per 1000 words | a long report is not punished for length |
| `lost_required_facts` | lower | misses in the case's `facts_recalled` plus numbers/negations lost per its `preserves` checks; skipped when the case names none | a dropped "not" reverses the meaning |
| `slop_per_1000w` | lower | slop_scan findings per 1000 prose words, the case's own profile (default professional); not for analysis outputs | stock vocabulary and chatbot residue cost trust |
| `stock_phrases_per_1000w` | lower | hits of a fixed list of well-known stock phrases (`STOCK_PHRASES`), independent of slop_scan | an independent check on "a chatbot wrote this" |
| `gap_markers_leaked` | lower | unresolved placeholders: `[ASK AUTHOR ...]`, `[VERIFY ...]`, `[UNTESTED ...]`, `[TODO]`/`[TBD]`/`[INSERT ...]`, `[Your name]`-style fills, `{{field}}`, lorem ipsum, `XXX`, bare TBD/TODO, unless the text is already in the sources; code excluded | an email that goes out signed `[Your name]` is unfinished |
| `headings_per_1000w` | - | markdown headings per 1000 words | context for the next row |
| `short_text_headings` | lower | headings in an output under 400 words | scaffolding on a short note |
| `repeated_sentences` | lower | sentences of 6+ words that repeat an earlier one (identical, or word 3-shingle Jaccard 0.6 or more) | padding |
| `hedge_per_1000w` | lower | hedge and caveat words per 1000 words (`HEDGES`) | fog; but a correct hedge is not a defect, so the gate does not use it by default |
| `sentence_length_cv` | higher | standard deviation / mean of words per sentence in running prose (3+ sentences) | uniform sentences read as machine-made |
| `mean_sentence_length` | - | mean words per sentence in running prose | context |
| `flesch_reading_ease` | higher | 206.835 - 1.015 w/s - 84.6 syl/w over running prose (vowel-group syllables; 3+ sentences) | reading effort |
| `list_line_ratio` | - | bullet and numbered lines / non-blank, non-heading, non-code lines | context |
| `length_ratio` | - | words / midpoint of the case's `word_count` min and max | context |
| `length_deviation` | lower | abs(length_ratio - 1) | the length the reader asked for is part of the request |
| `process_talk` | lower | meta-talk in the deliverable ("I rewrote the", "this report was generated by", "as an AI", "here is the revised", skill and script names), unless already in the sources; not for analysis outputs | the reader does not care how the text was produced |
| `check_pass_rate` | higher | share of the case's own checks that passed (grade.py) | the case author's definition of correct |
| `case_passed` | higher | 1 when every check passed | one broken requirement is a failed run |
| `words` | - | whitespace tokens of the output | context for every rate |

**Case kinds** (`stats.CASE_KIND`, part of the rules): `reader` is finished text that goes to a person as it is (emails, posts, letters, updates, READMEs, PR bodies); a gap marker left in it is a leak. `draft` is text the author must still finish or read (reports with open gaps, drafts whose case requires a marker in the reply or file): markers are counted but never fail the gate. `analysis` is text about text (audits, reviews, triage, voice profiles, reviewer prompts): it quotes the patterns and describes its own review, so the slop, stock-phrase, rhythm and process-talk metrics are not computed. A test keeps every case classified and keeps cases that require markers out of `reader`.

**Statistics.** A metric that does not apply to an output (analysis kind, no required facts, fewer than 3 sentences) is empty, and a pair is formed only where both sides have a value. A case's repetitions are averaged first, then the bootstrap (percentile, 95%) resamples cases, because repetitions of one case are not independent cases. Means, medians and CIs are over cases. Differences are paired on (host, case, rep), with the exact two-sided sign-test p-value over cases. A verdict (`better` / `worse`) needs the CI to exclude zero; with fewer than 3 paired cases the verdict is `few`. At 3 to 5 cases (most skills have 3) three same-signed differences always exclude zero and the sign test cannot reach p < 0.05 below 6, so per-skill flags are leads to inspect, not findings; the all-skills row carries the weight. Host errors are excluded from both sides.

**Gate.** `gate.py freeze` stores the with-skills runs of a results directory (all metrics per case and repetition) with run id, host versions, model, skill versions from each `SKILL.md`, the metric version and a fingerprint of the scoring files (fact_diff.py, slop_scan.py, the rule data in stats.py, the case files). `gate.py check` scores the new run the same way, pairs it with the reference on (host, case, rep) and exits 1 when, for any skill or for all skills together:

- any metric in `metrics` with `gated` not false, which includes `invented_facts` and `check_pass_rate`: the lower bound of the 95% bootstrap CI of the paired worsening (new vs reference, repetitions averaged per case, CI over cases) is above the metric's `tolerance` in its own unit. Worse than tolerance on average with a CI that reaches back inside the tolerance is printed as a warning and does not fail. Rerun noise widens the CI, so noise alone does not fail the gate;
- leaked markers (`absolute.leaked_marker_run_rate_max`, default 0): the share of `reader` runs whose output carries a gap marker or placeholder is above the limit. This is the one rule without statistics, because a placeholder in a finished email is a defect whenever it occurs. It is measured on the new run alone (not against the reference), counts runs rather than markers, and ignores `draft` and `analysis` cases.

Exit codes: 0 pass, 1 regression, 2 not comparable (different `METRICS_VERSION`, no matching runs). If the scoring files changed since the freeze, `check` prints a warning because old and new numbers may not be comparable; re-freeze when the change is intended (and re-freeze from a run scored with the new files). Freeze the reference from the run you accept as the current skill set, never from the candidate being tested; after accepting a revision, freeze again, then run `gate.py aa` and `gate.py weak` again.

**A/A noise test.** `gate.py aa <run-dir>` gates pseudo-runs built from the run's own outputs against the run itself, with no new runs: the repetitions shifted by one and by two (r1 to r2, r2 to r3, r3 to r1, and the reverse), and every ordered pair of single repetitions (r2 against r1, and so on, a harsher test than a rerun of three repetitions because one repetition has more noise than the mean of three). The outputs are identical, so the gate must pass on all of them; the command exits 1 if one fails. The shifted pseudo-runs have exactly zero difference in every case mean, so they only prove the plumbing; the single-repetition pairs carry the noise. The leaked-marker rule has no noise to test: a leak in the run's own outputs is listed under the table as a defect of that run and does not count. The tolerances of `flesch_reading_ease` (5) and `sentence_length_cv` (0.1) were set above the noise floor this test measured on v-voice-omp and v-clean-omp (the largest per-skill lower CI bound of a pure repetition swap: 4.2 points and 0.083); re-run `aa` on the new reference after a re-freeze, and raise a tolerance only to what it shows.

**Known weak spots.** A frozen run can be worse than another run in places, and a gate that only compares against it would bless that. `gate.py weak <other-run-dir>` writes `gate/weak_spots.json`: every metric in `config.json` (gated or not), per skill and ALL, where the reference is worse than the other run with the 95% CI of the difference excluding zero. `check` prints that list after the table, with the row of the new run next to it, and says so when the list was made for another reference. It is a note, never a verdict. Against v-clean-omp the v-voice-omp reference is worse in project-report `lost_required_facts` and `length_deviation` and in report-writing `slop_per_1000w` and `hedge_per_1000w`.

Limits: with 3 to 6 cases per skill the per-skill CIs are wide and approximate, so a per-skill FAIL is a lead to inspect; the all-skills row carries the weight. `invented_facts` has tolerance 0 (any invented figure is a lie), so what protects it from noise is the CI, not a slack: a few stray inventions in a rerun do not fail, a consistent rise does. Gate runs are LLM runs, so judge a failure by the table (which metric, which skill, which cases), not by the exit code alone. `stock_phrases_per_1000w` and `process_talk` are near zero for current models, so they guard against a return of the problem and do not separate revisions today.

**Skill against competitors.** When a run has `competitor-*` conditions, `stats.py <run-dir>` also prints, and `--json` stores under `skill_minus_competitor`, our skill minus each competitor, paired on (host, case, rep) over the cases the competitor ran (`diff` = skill - competitor; `better` / `worse` refer to the skill, CI over cases). Every row comes twice with its n (paired runs / cases): `all` pairs, and `loaded` pairs only, where `meta.json` says `skill_loaded` is true for the competitor's run and for ours, because a run that never read its skill measures the bare model. `loaded` has fewer pairs, so it often reads `few`.

## What the numbers mean

A case passes when all its checks pass. The report gives, per skill, host and condition: the pass rate, the mean score (per run, the share of checks passed, averaged, with the lowest and highest run), the skill-minus-baseline difference, how often the skill was actually loaded, and per-check failure counts; with `--repeat` it also lists each repetition. The checks are mechanical: they catch invented numbers, lost negations, missing markers, leftover stock phrases, leaked context, missed facts, wrong or invented diagram content and unsafe HTML. They do not measure prose quality, argument strength, voice or visual design; the judge gives a preference, not proof. Case counts are small and repetitions of one case are not independent cases, so treat differences of one or two cases as noise.

A host error (the CLI exits or times out without writing the output file) is shown as `ERROR`, not `FAIL`. The (case, repetition) is then left out of both conditions for that host, so the difference always compares the same runs.

Claude Code must be able to run `claude -p` non-interactively with its configured model. If it reports `unrecognized_model` (a gateway model name its catalog does not know), update Claude Code or map the name in its settings, or pass a known model with `--claude-model`; until then every Claude run is a host error.

## omp host

`--host omp` (and `--judge omp`) runs `omp -p --mode json --no-session --no-rules --no-lsp --auto-approve --model <--omp-model, default gpt-6-sol>`. Skills are copied into the workspace's `.agents/skills` in the `skill` condition; user rules and session history are off in both conditions. A skill counts as loaded when the event log shows a `skill://<name>` read. The visual judge receives page screenshots as PNG files in its workspace and opens them with the read tool.
