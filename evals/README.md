# Oh My Writing benchmark

Measures whether each skill changes agent behavior on realistic writing tasks, compared with the same agent and prompt without the skills installed. Every case is graded by deterministic checks; an optional blind pairwise judge adds a quality preference.

```text
evals/
├── cases/<skill>/<case>.json   # one task per file
├── run.py                      # runs cases on agent hosts, then grades
├── grade.py                    # deterministic checks; re-grades a results directory
└── results/<run-id>/           # git-ignored: workspaces, replies, logs, results.json, report.md
```

## Run

```bash
python3 evals/run.py --host codex --host claude --jobs 4          # all cases, with and without skills
python3 evals/run.py --host codex --cases 'anti-slop-editing/*'    # one skill
python3 evals/run.py --host codex --judge codex                    # add blind pairwise preference
python3 evals/grade.py evals/results/<run-id>                       # re-grade without re-running
python3 evals/grade.py --validate                                  # check every case file
```

Conditions:

- `skill`: all skills under `skills/` are linked into the temporary workspace (`.agents/skills/` for Codex, `.claude/skills/` for Claude Code). The prompt never names a skill, so the run also tests whether the description triggers.
- `baseline`: the same workspace, prompt and host with no skills linked.

The runner refuses to run when a skill with the same name is installed at user level (`~/.agents/skills`, `~/.claude/skills`), because the baseline would then also see it. `--allow-contaminated` overrides and marks the run, but the baseline is then not a true baseline. If you installed the skills with the README loop, move those links aside while benchmarking.

`--resume` with the same `--out` keeps finished runs and judge verdicts and redoes only errored or missing ones. When a host refuses for usage limits, the remaining runs on that host are skipped immediately (recorded as host errors) so `--resume` can finish them after the limit resets.

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

fact_diff categories: `numbers`, `negations`, `certainty`, `scope`, `names`, `urls`, `code`, `code_blocks`, `quotes`, `citations`. Inserted `[ASK AUTHOR]`/`[VERIFY]` markers are never counted as facts.

## What the numbers mean

A case passes when all its checks pass. The report gives pass rates per skill, host and condition, the skill-minus-baseline difference, how often the skill was actually loaded, and per-check failure counts. The checks are mechanical: they catch invented numbers, lost negations, missing markers, leftover stock phrases and leaked context. They do not measure prose quality, argument strength or voice; the optional judge gives a preference, not proof. Case counts are small, so treat differences of one or two cases as noise.

A host error (the CLI exits or times out without writing the output file) is shown as `ERROR`, not `FAIL`. The case is then left out of both conditions for that host, so the difference always compares the same cases.

Claude Code must be able to run `claude -p` non-interactively with its configured model. If it reports `unrecognized_model` (a gateway model name its catalog does not know), update Claude Code or map the name in its settings, or pass a known model with `--claude-model`; until then every Claude run is a host error.
