# Pre-registration: v-review112-limit

Written before any run on the case below. The rules decide what this run means; they do not change after the results are known.

## Background

In `v-review110-date` the independent-review reviewer prompt put the author's limit for the review ("one page") on the document instead, as `Hard constraint: the proposal must fit on one page`, in 19 of 20 skill runs across both skill versions; with no skills, 10 of 10 prompts said "Keep your review to one page". Six of the nine judge wins for no skills named that error. The likely cause: the template's only length slot is `Hard constraints: {{LENGTH_FORMAT_VENUE_STYLE_RULES}}`, a rule for the document, and it has no slot for limits on the review.

Version 1.12 makes one change: the template names that slot as constraints on the document, adds an optional line for limits the writer set on the review, and the placeholder notes say which goes where.

## Design

- Case: `independent-review/heldout6-community-fridge-reviewer-prompt`, written and committed with this file before the fix. A grant application where the form's 300-word limit is a rule for the application and "a short table, no more than half a page" is the author's limit for the review.
- Measure: the case's second check (`not_regex`), which flags a sentence stating the half-page limit without saying it is about the review. Seven controls were graded before the run and behave as expected. The checks were also tried on the 30 outputs of `v-review110-date` and the 15 of `v-review18-date` with "one page" replaced by "half a page"; after two false positives on no-skills wording were fixed ("Return no more than…", "In no more than…, assess"), they flag 0 of 15 no-skills prompts and 22 of 30 skill prompts, matching a hand reading.
- Conditions: skill (independent-review 1.12) and variant-r111 (all skills at the commit that adds this file; independent-review 1.11). Baseline (no skills) is run and reported but decides nothing. Ten repetitions each. Host omp, default model.
- Judge: omp, blind, pairs skill:variant-r111 (decides) and skill:baseline (reported).
- Every output is also read by hand for where the half-page limit lands. Decisions use the checks as run; any disagreement with the hand reading is reported beside it as a post-hoc correction and does not change the decision.

## Decision rules

1. **The fix works.** variant-r111 puts the limit on the application in at least 3 of 10 runs, and the skill condition does so in at most 3 of 10 and in at least 3 fewer runs than variant-r111. If variant-r111 does so in 2 or fewer runs, the case did not show the defect: the run is inconclusive and 1.12 is reverted.
2. **The judge does not reject it.** Count the decided pairs between the skill condition and variant-r111 (ties and inconsistent verdicts are not decided). The fix is reverted if variant-r111 wins so many that a fair coin would give a split at least that lopsided, in either direction, with probability 0.11 or less (two-sided binomial): at 10 decided pairs, 8 or more; at 9, 8 or more; at 8, 7 or more; at 7, 7; at 6, 6; at 5, 5; with 4 or fewer decided pairs it cannot trigger.
3. **No harm on the other checks.** The number of skill-condition runs failing any check other than the measure is at most one more than for variant-r111.

1.12 stays only if rules 1, 2 and 3 all hold. Otherwise the docs say which rule failed and version 1.13 restores the 1.11 text.

## What does not count

- Host errors are excluded. More than 5% host errors in any condition makes the run inconclusive; it is resumed, not read.
- Earlier reviewer-prompt cases are not rerun: their outputs and judge reasons have been read.
- Baseline numbers, prompt length and the skill:baseline judge result are reported for context only. The skill's prompts are about 2.5 times longer than with no skills; 1.12 does not try to change that.
