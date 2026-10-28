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
├── flow_validation.py          # checks the flow metrics against sentence shuffles and the blind judge; writes flow-validation.md and duplication.md
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
python3 evals/run.py --host codex --cases 'reader/*' --judge codex  # reader track: fit, flow and fidelity judged apart
python3 evals/run.py --host omp --omp-model <writer> --judge omp --judge-omp-model gpt-6.1-sol  # writers on one model, judge on another
python3 evals/run.py --host codex --cases 'project-report/*' --repeat 3 --jobs 4 \
    --judge codex --out evals/results/project-report-bench          # report benchmark: 3 repetitions, visual judge
python3 evals/review_pairs.py evals/results/project-report-bench    # blind A/B page for you -> review/<run-id>.html
python3 evals/grade.py evals/results/<run-id>                       # re-grade without re-running
python3 evals/grade.py --validate                                  # check every case file
```

Conditions:

- `skill`: every skill under `skills/` is copied (not linked) into the temporary workspace (`.agents/skills/` for Codex, `.claude/skills/` for Claude Code), so the agent can neither write through to the repository nor see its path. The prompt never names a skill, so the run also tests whether the description triggers.
- `baseline`: the same workspace, prompt and host with no skills copied.
- `variant-<name>` (`--variant NAME=GITREF`): our skills as committed at another git ref, on every case; see "A/B testing skill revisions".

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

## A/B testing skill revisions

`--variant NAME=GITREF` (repeatable) adds the condition `variant-NAME`: the same agent, prompt and cases, with our skills exactly as committed at `GITREF` instead of the working tree. The runner resolves the ref to its full sha, exports `skills/` with `git archive` into `.cache/variants/<full-sha>/skills` (git-ignored, reused by every later run of that commit) and copies those folders into the run's workspace like the `skill` condition does. A variant runs on every case, loads and is isolation-checked like `skill` (any of our skill names may be opened, nothing else), and its runs are `<case>__<host>__variant-<name>[__r<k>]` with `variant` and `variant_sha` in `meta.json`. `run.json` records per variant the ref as given, the full sha and every skill's `metadata.version` at that commit. A warning is printed when the ref has no skill for some selected case, because those runs then measure the bare model.

`--variant` alone runs `skill`, `baseline` and the variant. `--condition variant:NAME` selects only the variant (no default `skill` and `baseline`), which is what you want to add one revision to a finished run:

```bash
python3 evals/run.py --host omp --cases 'structured-drafting/*' --condition variant:pre --variant pre=21cd881 --out /tmp/ab-smoke
```

Reading the result:

- `grade.py` / the run's `report.md` get one table per variant, "A/B: skill vs variant-NAME": pass rate and mean score of `skill` and of the variant, the difference, n and both load rates, on the (case, host, repetition) triples where both sides produced a gradable run (the competitor pairing, so a variant that covers fewer cases or crashed on some never removes pairs from the main table). `results.json` carries it under `summary.by["<host>/<skill>"].variants`.
- `--judge-pairs skill:variant-NAME` (or `skill:variant` for every variant of the run) judges the two blind, like a competitor pair: its own `pair` entries in `judge.json`, own judge folders and order seed, own report section, with the style questions (reads human, faithful) tallied separately on style cases.
- `stats.py <run-dir>` prints our skill minus each variant, paired on (host, case, rep), like it does for competitors.
- `gate.py check <run-dir> --reference-condition variant-NAME` gates the run's `skill` runs against that variant inside the same run, with the tolerances of `gate/config.json` and no frozen file, so one A/B run is a regression test of HEAD against the ref. The variant is the reference, `skill` the revision under test; the frozen-reference `check` (`--against reference.json`) works as before.

`--adopt-runs SRC=variant-NAME` (repeatable; needs `--out DIR` of an existing run, `--resume`, and `--variant NAME=...` for the ref the runs stand for) relabels the finished runs of condition `SRC` as `variant-NAME` before anything runs: run folders and `meta.json` are renamed (with `variant`, `variant_sha`, `adopted_from`), and every judge verdict and judge folder that has `SRC` as a side is relabelled too (the default verdict becomes `variant-NAME:baseline`). That turns the `skill` runs of an earlier clean run into the variant of the commit they were made with without paying for them again. `run.json` lists what was adopted and the same command run again adopts nothing twice. Adopt only runs made with the skills of the ref you declare.

Example: the isolated run `v-iso-omp` was made with the skills of `f0a07bf`; test HEAD and the older `21cd881` against it, keeping the baseline and competitor runs and the finished verdicts:

```bash
cp -R evals/results/v-iso-omp evals/results/v-ab-omp
python3 evals/run.py --host omp --repeat 3 --jobs 4 --judge omp --condition both --competitors \
  --variant iso=f0a07bf --variant pre=21cd881 --adopt-runs skill=variant-iso \
  --judge-pairs skill:baseline,skill:variant-iso,skill:variant-pre,skill:competitor \
  --resume --out evals/results/v-ab-omp
python3 evals/gate.py check evals/results/v-ab-omp --reference-condition variant-iso
```

Only `skill` (HEAD) and `variant-pre` execute; baseline, competitor and `variant-iso` runs are reused. Verdicts of the old skills against baseline and competitors stay as `variant-iso:<other>` pairs; the pairs against HEAD are judged anew.

### Placebo: does this content help, or does any long prompt?

`--placebo` adds the condition `variant-placebo` (the placebo is an ordinary variant, so the A/B table, `--judge-pairs skill:variant-placebo`, `stats.py` and `gate.py check --reference-condition variant-placebo` work unchanged). For every skill it installs a copy with the same name, description, frontmatter and Markdown file layout, but each file's body is replaced by generic writing advice of about the same word count: whole consecutive sentences from `evals/placebo/generic-advice.md` (our own deliberately unremarkable advice about audience, structure, revision and concision, with none of the skills' methods), stopping where the length is closest to the original, so a body never starts or ends mid-sentence and is off by at most half a sentence. Scripts, assets and every other non-Markdown file are dropped. It controls for "any longer prompt helps": the model sees a skill with the same name, trigger text and size, so a gap between `skill` and `variant-placebo` is attributable to what the skill says, not to having a skill. The placebo is built into `.cache/placebo/<id>/skills`, where `<id>` is a sha256 of the generator version, the generic text and each skill's name, description and per-file word counts; `run.json` records it under `variants.placebo` (`ref` and `placebo: true`, `sha` is that id), and `--resume` redoes placebo runs whose id changed. The name `placebo` is reserved and cannot be given to `--variant`.

`--prereg FILE` pre-registers the decision rule. Before any run the file is copied into the results directory as `prereg.md`, and its sha256 and the UTC time go into `run.json` under `prereg`; `report.md` starts with the pre-registered text, and grading the directory again with `grade.py` keeps it there. On `--resume` a different file is refused (so is registering a file in a directory that already holds runs).

```bash
cat > /tmp/prereg.md <<'EOF'
# Pre-registration
Hypothesis: our skills beat a same-size placebo. Decision: ship only if skill minus placebo is at least +10 points of pass rate overall.
EOF
python3 evals/run.py --host omp --repeat 3 --jobs 4 --placebo --prereg /tmp/prereg.md \
  --judge omp --judge-pairs skill:variant-placebo --out evals/results/v-placebo-omp
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

- `id` equals `<folder>/<file name without .json>`; the folder is the skill's name, or `style` or `reader` for those tracks. `skill` is a directory under `skills/` and is what the report groups by.
- `files` are written into the workspace; keep inputs short (under about 500 words) and fictional.
- `output` is the deliverable file the agent must write. A missing output file fails the case.
- Each check may set `"target"`: `output` (default), `reply` (the agent's final message) or `both`.
- Optional `fixtures`: `"evals/fixtures/<case-slug>"`, a folder copied verbatim (binary-safe, relative paths and modification times kept) into the workspace root. `files` may then be `{}`, or both may be used. For text checks the grader extracts the fixtures' text (docx, xlsx, pptx, pdf via `pdftotext`, eml, html, csv ... through `skills/project-report/scripts/inventory.py`), so `no_added_facts`, `preserves` and `similarity` see Office and PDF content; a fixture is named in `source`/`sources` by its path inside the folder (`docs/budget.xlsx`). `no_added_facts` also treats the input file names, and relative links to inputs or into the output folder, as known. CSV/TSV sources are read cell by cell so `14,171` is not one number.
- Optional `timeout` (seconds) overrides `--timeout` for this case (report cases use 2400).
- Optional `deliverables`: files the agent is asked to write, e.g. `["out/report.md", "out/report.html"]`. `output` stays the primary text file; the grader records in `results.json` which deliverables exist.
- Optional `judge`: `{"mode": "visual", "render": "out/report.html"}` switches the blind judge for this case to the visual judge (below). `render` must be listed in `deliverables`. `{"mode": "style"}` switches it to the style judge and `{"mode": "reader"}` to the reader judge (both below); neither takes a `render`. Other cases keep the text judge.
- Optional `style_ref`: the name of one of the case's `files`, the example or guide whose style the output must match. The reader judge is told to judge fit against it; `--validate` rejects a name that is not in `files`.
- Required `controls`: sample answers that prove the checks work. Each is `{"name", "expect", "fails", "output", "reply", "files"}`:

  ```json
  {"name": "good", "expect": "pass", "output": "<deliverable text>", "reply": "<final message>"}
  {"name": "drops-negation", "expect": "fail", "fails": ["preserves"], "output": "...", "reply": "...", "files": {"out/x.html": "..."}}
  ```

  `name` is unique within the case. `output` is the text written to the case's `output` path, or `null` for "file not written". `reply` is the agent's final message. `files` (optional) are extra workspace files on top of the case's own `files` and `fixtures` (an HTML deliverable, an SVG); relative paths only, never the `output` path. `expect: "pass"` means every check passes. `expect: "fail"` means the grade fails and, for each check type in `fails` (`output_present` counts), at least one check of that type fails: the trap is caught by the check meant for it, not by accident. Every case needs at least one `pass` and one `fail` control. A pass control is a good answer; a fail control is a plausible wrong one (the mistake the case exists for), never an empty string. `--validate` rejects a case without both.

  ```bash
  python3 evals/grade.py --controls [GLOB]    # GLOB matches case ids (default all); one line per control; exit 1 on any mismatch
  ```

  The workspace is built by the runner's `make_workspace` (case `files`, `fixtures` verbatim), then the control's `files` and `output` are written, and `grade_case` runs with `open-questions.md` files appended to the reply as in real grading. No run date is set. The `diagrams` check's optional `self_check` needs the user-level `diagram-design` skill and is skipped (passes) when it is not installed; a control must not rely on it.

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

### Reader judge

`judge.mode: "reader"` in a case, or `--judge-mode reader` for every case in the run, answers three separate questions in both presentation orders, with gap markers stripped as for the style judge:

1. **Fit**: which reads like the document that was asked for, in the style of the case's `style_ref` file, or of the genre, house style and reader the task names?
2. **Flow**: which is coherent, concise and tells one clear story in plain sentences? Stacked caveats, "X, not Y" contrasts, untranslated internal shorthand, piled-up numbers, inline arithmetic, template headings where prose would do, uniform sentence shapes and a missing author voice count against a response; length is not a virtue.
3. **Faithful**: which invents nothing and drops nothing the reader needs? Leaving out a detail the reader does not need is not a fault.

The case ids are `reader/<name>`; held-out ones are `reader/heldout-<name>`. Each question is combined over both orders like the style judge (`combine_picks`). `judge.json` stores `fit`, `flow` and `faithful` per entry with `mode: "reader"` and both pick lists; `winner` is `reader`, or `error` when any answer is missing. The report has a "Blind reader judge" section with one row per question (skill, baseline, tie, inconsistent, error), and reader entries are never added to the overall pairwise tally; other judged pairs get the same table in their own section. `flow_validation.py` only reads style and text verdicts and leaves reader entries out.

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
python3 evals/gate.py check  evals/results/<ab-run-id> --reference-condition variant-<name>   # same rules, reference = a variant of the same run
python3 evals/gate.py aa     evals/results/<run-id>                                      # noise test: relabelled repetitions must pass
python3 evals/gate.py weak   evals/results/<other-run-id>                                # record where the reference is worse than another run
python3 evals/flow_validation.py evals/results/<run-id>                                  # validate flow metrics; our duplication against baseline and competitors
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
| `repeated_trigram_rate` | lower | REPEATS ITSELF: share of content-word 3-grams (three consecutive non-stopword stems in one sentence) that occurred earlier in the same output; 20+ 3-grams | the reader meets the same phrases again and again |
| `near_duplicate_pairs_per_1000w` | lower | REPEATS ITSELF: sentence pairs with content-stem Jaccard 0.5 or more (each with 5+ content stems), per 1000 words | the same point twice in other words |
| `repeated_caveats` | lower | REPEATS ITSELF: hedge or uncertainty sentences (`HEDGES`, `CAVEAT_PHRASES`; 3+ content stems) that near-duplicate an earlier one | one caveat where it applies is honest, the same one pasted everywhere is noise |
| `source_copy_rate` | - | COPIES THE INPUT: share of output words inside a verbatim run of 8+ words found in the case's sources or prompt | context: an edit must keep its source, a report must not paste it |
| `hedge_per_1000w` | lower | hedge and caveat words per 1000 words (`HEDGES`) | fog; but a correct hedge is not a defect, so the gate does not use it by default |
| `sentence_length_cv` | higher | standard deviation / mean of words per sentence in running prose (3+ sentences) | uniform sentences read as machine-made |
| `mean_sentence_length` | - | mean words per sentence in running prose | context |
| `flesch_reading_ease` | higher | 206.835 - 1.015 w/s - 84.6 syl/w over running prose (vowel-group syllables; 3+ sentences) | reading effort |
| `adjacent_cohesion` | higher | mean content-stem overlap (shared / smaller set) between consecutive sentences of one paragraph; running prose, 3+ pairs | each sentence picks up what the last one set up |
| `abrupt_jump_rate` | lower | share of consecutive same-paragraph pairs with no shared content stem and no connective or referential opener (but, so, however, it, this, ...) | a sentence with no bridge is a jolt |
| `given_new_carry` | higher | share of pairs where the opening half of the second sentence holds a stem of the first, or it opens with a connective or referential word | old before new |
| `stock_transition_rate` | lower | share of prose sentences opening with Moreover, Furthermore, Additionally, In addition, Overall, Ultimately, Notably, In conclusion, ... | the opener announces a link instead of making one |
| `long_sentence_share` | lower | share of prose sentences over 30 words | the subject is gone before the verb arrives |
| `interruption_density` | lower | parentheticals of 2+ words plus pairs of dashes, per prose sentence | each aside must be resumed from |
| `nominalization_per_1000w` | lower | words of 7+ letters ending -tion, -sion, -ment, -ness, -ity, -ance, -ence (concrete nouns excluded) per 1000 prose words | verbs turned into nouns hide who does what |
| `passive_voice_rate` | lower | share of prose sentences with be/get plus a regular -ed or listed irregular participle | the reader asks who did it |
| `paragraph_length_cv` | higher | standard deviation / mean of words per prose paragraph (3+ paragraphs) | identical paragraphs read as a template |
| `one_sentence_paragraph_share` | lower | share of prose paragraphs holding one sentence (3+ paragraphs) | staccato slogans, reasoning left out |
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

**Skill against competitors.** When a run has `competitor-*` or `variant-*` conditions, `stats.py <run-dir>` also prints, and `--json` stores under `skill_minus_competitor` (key `host/NAME/scope`, NAME without the prefix), our skill minus each competitor or variant, paired on (host, case, rep) over the cases it ran (`diff` = skill - competitor; `better` / `worse` refer to the skill, CI over cases). Every row comes twice with its n (paired runs / cases): `all` pairs, and `loaded` pairs only, where `meta.json` says `skill_loaded` is true for the competitor's run and for ours, because a run that never read its skill measures the bare model. `loaded` has fewer pairs, so it often reads `few`.

**Flow metrics and what was validated.** The flow metrics are rules about how text reads, not proof that it reads well, so `flow_validation.py <run-dir>` tests them on a finished run before the gate may use one (it writes `flow-validation.md` and `duplication.md` into the run directory). (a) Order sensitivity: every non-analysis output is rebuilt with its sentences in a seeded random order (paragraph sizes kept, 9 shuffles, mean); a metric that reads sentence order (`adjacent_cohesion`, `abrupt_jump_rate`, `given_new_carry`) must score the shuffled copy worse in most reader outputs, CI lower bound above 0.5. (b) Agreement with the blind judge: for every judged pair with a clear verdict (the 'reads human' answer on style pairs, the pairwise winner on text pairs; ties, inconsistent and error verdicts and visual entries left out) the share of pairs where the metric prefers the judge's winner, with a bootstrap CI that resamples cases. A new metric is `gated` only when it passes (a) where it applies and the lower CI bound of (b) is above 0.5; otherwise `config.json` says `gated: false` with the measured reason. On v-iso-omp (206 judged pairs, 22 to 24 cases) `abrupt_jump_rate` (shuffle worse in 78%) and `given_new_carry` (70%) pass (a), `adjacent_cohesion` does not (61%, CI [0.46, 0.73]), and no new metric agrees with the judge beyond chance (every CI includes 0.5), so none is gated. The existing `sentence_length_cv` agrees with the judge less than chance (0.38, CI [0.29, 0.48]). A candidate `flow_score` (mean of the three order-sensitive metrics) did not validate better than its parts and is not in the table. `repeated_caveats` and `stock_transition_rate` are zero or near zero in current outputs, so they guard against a return of the problem and tell nothing today. The numbers in this paragraph are those of the run named; rerun the command after a metrics change.

**Repeats itself and copies the input.** `repeated_sentences`, `repeated_trigram_rate`, `near_duplicate_pairs_per_1000w` and `repeated_caveats` look only inside the output; `source_copy_rate` compares the output with the case's sources and has no direction because an edit must keep its source. `flow_validation.py` prints and writes our skill minus the baseline and minus each `competitor-*` or `variant-*` condition for these metrics, all pairs and loaded-only pairs.

## What the numbers mean

A case passes when all its checks pass. The report gives, per skill, host and condition: the pass rate, the mean score (per run, the share of checks passed, averaged, with the lowest and highest run), the skill-minus-baseline difference, how often the skill was actually loaded, and per-check failure counts; with `--repeat` it also lists each repetition. The checks are mechanical: they catch invented numbers, lost negations, missing markers, leftover stock phrases, leaked context, missed facts, wrong or invented diagram content and unsafe HTML. They do not measure prose quality, argument strength, voice or visual design; the judge gives a preference, not proof. Case counts are small and repetitions of one case are not independent cases, so treat differences of one or two cases as noise.

A host error (the CLI exits or times out without writing the output file) is shown as `ERROR`, not `FAIL`. The (case, repetition) is then left out of both conditions for that host, so the difference always compares the same runs.

Read `skill` against `variant-placebo` before reading it against `baseline`: if the placebo scores about as well, the gain came from having a longer prompt, not from the skill's content. Fix the decision threshold in a `--prereg` file before the first run, so the number is not chosen after the results are known.

Claude Code must be able to run `claude -p` non-interactively with its configured model. If it reports `unrecognized_model` (a gateway model name its catalog does not know), update Claude Code or map the name in its settings, or pass a known model with `--claude-model`; until then every Claude run is a host error.

## omp host

`--host omp` (and `--judge omp`) runs `omp -p --mode json --no-session --no-rules --no-lsp --auto-approve --model <--omp-model, default gpt-6-sol>`. `--judge-omp-model` sets the model of omp judge calls (default: `--omp-model`), so writers can run on one model while another judges; the model-fallback check compares each call with the model it requested. Skills are copied into the workspace's `.agents/skills` in the `skill` condition; user rules and session history are off in both conditions. A skill counts as loaded when the event log shows a `skill://<name>` read. The visual judge receives page screenshots as PNG files in its workspace and opens them with the read tool.
