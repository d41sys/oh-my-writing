# Oh My Writing benchmark

Measures whether each skill changes agent behavior on realistic writing tasks, compared with the same agent and prompt without the skills installed. Every case is graded by deterministic checks; an optional blind pairwise judge adds a quality preference.

```text
evals/
├── cases/<skill>/<case>.json   # one task per file
├── fixtures/<case-slug>/       # document folders copied into a case's workspace (binary files allowed)
├── run.py                      # runs cases on agent hosts (with repetitions), then grades
├── grade.py                    # deterministic checks; re-grades a results directory
├── review_pairs.py             # one-file blind A/B page for rating pairs yourself
└── results/<run-id>/           # git-ignored: workspaces, replies, logs, results.json, report.md
```

## Run

```bash
python3 evals/run.py --host codex --host claude --jobs 4          # all cases, with and without skills
python3 evals/run.py --host codex --cases 'anti-slop-editing/*'    # one skill
python3 evals/run.py --host codex --judge codex                    # add blind pairwise preference
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

- `id` equals `<skill>/<file name without .json>`; `skill` is a directory under `skills/`.
- `files` are written into the workspace; keep inputs short (under about 500 words) and fictional.
- `output` is the deliverable file the agent must write. A missing output file fails the case.
- Each check may set `"target"`: `output` (default), `reply` (the agent's final message) or `both`.
- Optional `fixtures`: `"evals/fixtures/<case-slug>"`, a folder copied verbatim (binary-safe, relative paths and modification times kept) into the workspace root. `files` may then be `{}`, or both may be used. For text checks the grader extracts the fixtures' text (docx, xlsx, pptx, pdf via `pdftotext`, eml, html, csv ... through `skills/project-report/scripts/inventory.py`), so `no_added_facts`, `preserves` and `similarity` see Office and PDF content; a fixture is named in `source`/`sources` by its path inside the folder (`docs/budget.xlsx`). `no_added_facts` also treats the input file names, and relative links to inputs or into the output folder, as known. CSV/TSV sources are read cell by cell so `14,171` is not one number.
- Optional `timeout` (seconds) overrides `--timeout` for this case (report cases use 2400).
- Optional `deliverables`: files the agent is asked to write, e.g. `["out/report.md", "out/report.html"]`. `output` stays the primary text file; the grader records in `results.json` which deliverables exist.
- Optional `judge`: `{"mode": "visual", "render": "out/report.html"}` switches the blind judge for this case to the visual judge (below). `render` must be listed in `deliverables`. Other cases keep the text judge.

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

## Visual judge and review page

`--judge` runs a blind pairwise judge in both presentation orders. For a case with `judge.mode` `visual` the judge also sees page images: the report HTML is printed to PDF with headless Chrome (`CHROME` overrides the path) and the first six pages are rasterised with `pdftoppm -r 60`. Codex receives them with `codex exec -i`; Claude Code is told to open them with the Read tool. The prompt holds the task, the extracted source text (each file cut to 5000 characters, 60000 in total, with the cut stated), both report texts (cut at 30000 characters) and asks for 1-5 scores on accuracy against the sources, covering what the reader needs, professional tone, diagram usefulness and design, and layout, then a verdict. If rendering fails for either side the judge falls back to text only for both, and `judge.json` says so (`render_note`). Scores are stored in `judge.json` per pair and averaged per condition in `report.md`.

`python3 evals/review_pairs.py <run_dir>` writes `review/<run-id>.html`, a self-contained page for you to rate the same pairs blind: per (case, repetition) the task, the source documents (expandable) and report A and B side by side (the HTML report in a sandboxed iframe, or the markdown as text), in seeded random order. Rate each pair A better / Tie / B better, add a note; ratings persist in the browser (localStorage); Export JSON downloads them with the A/B mapping. Reveal unlocks once every pair is rated and shows which side had the skills. `review/` is a local folder: do not commit it.

## What the numbers mean

A case passes when all its checks pass. The report gives, per skill, host and condition: the pass rate, the mean score (per run, the share of checks passed, averaged, with the lowest and highest run), the skill-minus-baseline difference, how often the skill was actually loaded, and per-check failure counts; with `--repeat` it also lists each repetition. The checks are mechanical: they catch invented numbers, lost negations, missing markers, leftover stock phrases, leaked context, missed facts, wrong or invented diagram content and unsafe HTML. They do not measure prose quality, argument strength, voice or visual design; the judge gives a preference, not proof. Case counts are small and repetitions of one case are not independent cases, so treat differences of one or two cases as noise.

A host error (the CLI exits or times out without writing the output file) is shown as `ERROR`, not `FAIL`. The (case, repetition) is then left out of both conditions for that host, so the difference always compares the same runs.

Claude Code must be able to run `claude -p` non-interactively with its configured model. If it reports `unrecognized_model` (a gateway model name its catalog does not know), update Claude Code or map the name in its settings, or pass a known model with `--claude-model`; until then every Claude run is a host error.
