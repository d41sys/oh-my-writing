# Pre-registration: v-review18-date

Written before any run. The rules below decide what this run means; they do not change after the results are known.

## What is tested

Whether independent-review 1.8 stops the reviewer prompt from telling the reviewer, in advance, that the draft's dates lack a year. In v-review16-heldout both 1.5 and 1.6 did this in 3 of 5 runs of the food-bank case. 1.8 adds that remark to the "Before you send" list of things to remove and to what the `READING_DATE` placeholder must not hold; nothing else changes.

- Case: independent-review/heldout4-homework-club-reviewer-prompt, written and committed with this file before the fix was run. Its third check (`not_regex` on a remark tying 5 or 14 March to a year) is the measure. Neither the skill nor this case changes after the run; a check found wrong afterwards is reported as a post-hoc correction next to the as-run numbers.
- Conditions: skill (1.8), variant-r17 (all skills as at 3d583b3, where independent-review is 1.7, the 1.5 text), baseline. Five repetitions each. Host omp, default model.
- Judge: omp, blind pairs skill:variant-r17 and skill:baseline.

## Hypotheses and decision rules

1. **The fix works (decides whether 1.8 stays).** The skill condition writes the date remark in at most 1 of 5 runs and in fewer runs than variant-r17. If not, 1.8 is reverted and the docs say the fix did not hold.
2. **No harm.** The skill condition passes every other check of the case at least as often as variant-r17, and the judge does not prefer variant-r17 by 3 or more decided pairs. If either fails, the docs say so and 1.8 is reverted.
3. Reported, not decided: the same numbers for baseline, and the food-bank case is not rerun (its judge results were read when 1.6 was written up).

## What does not count

- Five runs per condition: a difference of one run is noise.
- Host errors are excluded. More than 5% host errors in any condition makes the run inconclusive; it is resumed, not read.
- If variant-r17 writes the remark in 0 or 1 of 5 runs, the defect did not show on this case and rule 1 cannot be met; the run is reported as inconclusive for the fix.
