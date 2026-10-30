# Pre-registration: v-review114-paste

Written before any run on the case below. The rules decide what this run means; they do not change after the results are known.

## Background

In `v-review112-limit` the judge preferred no skills to independent-review 9-0. In 6 of those 9 verdicts the reason was that the no-skills prompt pasted the application into the prompt, so a reviewer in a fresh session can read it without the writer's files; the skill's prompts pointed to `draft.md`. On that run's outputs, no skills carried the draft verbatim in 10 of 10 prompts, the skill in 3 of 10 and 1.11 in 4 of 10. Yet between the two skill versions, 3 of 7 decided verdicts rewarded telling the reviewer to read `draft.md` directly.

The template's slot `{{ARTIFACT_PATH_OR_PASTED_TEXT}}` allows either. Version 1.14 makes one change: the reviewer prompt carries the document copied exactly between `BEGIN DOCUMENT` and `END DOCUMENT` lines and also names its file; a path alone is used only when the document is too long to paste or is not text. A verbatim copy is not a summary, so the independence rules stand.

## Design

- Case: `independent-review/heldout7-tool-library-reviewer-prompt`, written and committed with this file before the change. A short volunteer how-to; no dates and no length limits, so neither earlier defect can confound it.
- Measure: the case's first check (`contains`), which needs three full sentences of the draft, copied exactly. Five controls were graded before the run and behave as expected (a path-only prompt and a tidied copy both fail it).
- Conditions: skill (independent-review 1.14), variant-r113 (all skills at the commit that adds this file; independent-review 1.13) and baseline (no skills). Ten repetitions each. Host omp, default model.
- Judge: omp, blind, pairs skill:variant-r113, skill:baseline and variant-r113:baseline.

## Decision rules

1. **The change is followed.** The skill condition passes the measure in at least 8 of 10 runs and in at least 3 more runs than variant-r113. If variant-r113 already passes it in 8 or more runs, the case did not show the gap: the run is inconclusive and 1.14 is reverted.
2. **The judge does not reject it.** Count the decided pairs between the skill condition and variant-r113 (ties and inconsistent verdicts are not decided). 1.14 is reverted if variant-r113 wins so many that a fair coin would give a split at least that lopsided, in either direction, with probability 0.11 or less (two-sided binomial): at 10 decided pairs, 8 or more; at 9, 8 or more; at 8, 7 or more; at 7, 7; at 6, 6; at 5, 5; with 4 or fewer decided pairs it cannot trigger.
3. **No harm on the other checks.** The number of skill-condition runs failing any check other than the measure is at most one more than for variant-r113.

1.14 stays only if rules 1, 2 and 3 all hold. Otherwise the docs say which rule failed and version 1.15 restores the 1.13 text.

## Reported, not decided

- The judge results against no skills for both versions (skill:baseline and variant-r113:baseline), and the reasons given. Whether pasting closes the gap to no skills is the question behind this change, but one case and ten pairs cannot settle it, so it is reported only.
- Prompt length per condition.
- Every output is read by hand for whether the document was copied exactly. Decisions use the checks as run; any disagreement is reported beside them as a post-hoc correction.

## What does not count

- Host errors are excluded. More than 5% host errors in any condition makes the run inconclusive; it is resumed, not read.
- Earlier reviewer-prompt cases are not rerun: their outputs and judge reasons have been read.
