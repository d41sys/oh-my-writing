# Pre-registration: v-review110-date

Written before any run on the case below. The rules decide what this run means; they do not change after the results are known.

## Background

The independent-review reviewer prompt sometimes tells the reviewer, in advance, that the draft's dates lack a year. That is a finding written for the reviewer, which the skill's independence rules forbid. Version 1.8 added "a remark about the draft's own content, such as which dates lack a year" to the template's list of things to remove before sending. It was reverted as pre-registered in `v-review18-date`: as run, its check could not see the remark; corrected afterwards, the remark appeared in 1.7 in 2 of 5 runs and in 1.8 in 0 of 5; and the judge preferred 1.7, 4-1, mostly over an unrelated error. Five runs could not separate the change from noise.

This run repeats the test with the 1.8 text as version 1.10, on a fresh case and at twice the size.

## Design

- Case: `independent-review/heldout5-rowing-club-reviewer-prompt`, written and committed with this file before the run. Its third check (`not_regex`) is the measure: it catches a remark about this draft's dates and a missing year whether or not the dates are named ("both dates", "the meeting date", "these dates", "the dates have no year", "a year for the dates", "28 May has no year"). It allows a general instruction to flag dates without a year. Nine controls, including two pass controls written in the skill template's own general wording, were graded before the run and behave as expected.
- Conditions: skill (independent-review 1.10, the 1.8 text) and variant-r19 (all skills at the commit that adds this file; independent-review 1.9, the 1.7 text). Baseline (no skills) is run and reported but decides nothing. Ten repetitions each. Host omp, default model.
- Judge: omp, blind, pairs skill:variant-r19 (decides) and skill:baseline (reported).
- Every output is also read by hand for the date remark. Decisions use the check as run; any disagreement with the hand reading is reported beside it as a post-hoc correction and does not change the decision.

## Decision rules

1. **The fix works.** variant-r19 writes the date remark in at least 3 of 10 runs, and the skill condition writes it in at least 2 fewer runs than variant-r19. If variant-r19 writes it in 2 or fewer runs, the case did not show the defect and the run is inconclusive for the fix: 1.10 is reverted, and the docs say why.
2. **The judge does not reject it.** Count the decided pairs between the skill condition and variant-r19 (ties and inconsistent verdicts are not decided). The fix is reverted if variant-r19 wins so many that a fair coin would give a split at least that lopsided, in either direction, with probability 0.11 or less (two-sided binomial). At 10 decided pairs that means 8 or more wins for variant-r19; at 9, 8 or more; at 8, 7 or more; at 7, 7; at 6, 6; at 5, 5; with 4 or fewer decided pairs it cannot trigger. A split such as 6-4 or 7-3 is treated as noise.
3. **No harm on the other checks.** The number of skill-condition runs failing any check other than the date check is at most one more than for variant-r19.

1.10 stays only if rules 1, 2 and 3 all hold. Otherwise the docs say which rule failed and version 1.11 restores the 1.9 text.

## What does not count

- Host errors are excluded. More than 5% host errors in any condition makes the run inconclusive; it is resumed, not read.
- The food-bank and homework-club cases are not rerun: their outputs and judge reasons have been read.
- Baseline numbers are reported for context only.
