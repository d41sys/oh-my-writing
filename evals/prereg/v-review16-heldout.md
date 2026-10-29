# Pre-registration: v-review16-heldout

Written before any run. The rules below decide what this run means; they do not change after the results are known.

## What is tested

Whether independent-review 1.6 (commit 34cb43b) helps on tasks it was not tuned on. 1.6 was shaped by the judge's reasons on the earlier independent-review cases, including the two earlier held-out ones, so those cases can no longer test it.

- Cases: the two new held-out cases, written after 1.6 and committed with this file before any run: independent-review/heldout3-triage-trip-letter and independent-review/heldout3-food-bank-reviewer-prompt. Neither the skill nor these checks change after the run; a check found wrong afterwards is reported as a post-hoc correction next to the as-run numbers.
- Conditions: skill (1.6), variant-r15 (all skills as at 80c1cc6, where independent-review is 1.5), variant-placebo, baseline. Five repetitions each. Host omp, default model.
- Judge: omp, blind pairs skill:variant-r15, skill:baseline, skill:variant-placebo.

## Hypotheses and decision rules

1. **1.6 beats 1.5 on unseen tasks (decides whether 1.6 is described as an improvement).** The judge prefers skill over variant-r15 in more decided pairs than the reverse, over both cases together, and the skill condition passes at least as many runs as variant-r15. If either fails, the docs say 1.6 is not shown to help on unseen tasks.
2. **The skill helps at all on unseen tasks (decides what we claim about the skill).** Same rule against baseline and, separately, against variant-placebo. A loss here is reported as is, with the judge's reasons, and the reasons are sorted into those that conflict with the independence rules and those that do not.

## What does not count

- Ten judged pairs per comparison: a margin of one or two pairs is noise and is reported as a tie in the text.
- Host errors are excluded from both sides. More than 5% host errors in any condition makes the run inconclusive; it is resumed, not read.
- The judge prompt does not ask about reviewer independence, so a reviewer-prompt pair can be lost for keeping the reviewer independent; such reasons are listed, not discounted.
