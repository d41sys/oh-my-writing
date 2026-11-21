# Pre-registration: v-review-brief2

Written before any run of a skill condition on the case below. It decides whether independent-review 1.23 replaces 1.21. The rules do not change after the results are known.

## Background

`v-review-brief` (heldout14, claude-opus-5-5, 10 repeats) tested 1.22, the reviewer prompt as a plain brief. The prompt judge preferred it over 1.21 10 to 0 and over no skills 8 to 1; the review judge preferred its reviews over 1.21's 7 to 2. Two guards fired and 1.21 stayed: must-tell over the screened items was 10 of 30 for 1.22 against 17 for 1.21 and 21 for no skills, and the outside-fact count was 44 for 1.22 against 20 for 1.21 (144 for no skills).

Both losses trace to two things 1.22 dropped from 1.21: the second reading as someone experienced in the task ("what would that person make sure this reader knows before starting"), and the rule that the reviewer uses what it knows to see what is missing and never to supply the value or the procedure. 1.23 keeps the 1.22 brief and puts both back as plain sentences, with no named persona and no list of what to check.

heldout14 was read while writing 1.23, so it counts as tuned for it. Only the case below decides.

## Design

- Case: `independent-review/heldout15-jam-morning-reviewer-prompt`, committed with this file before any run on it. A one-page kitchen sheet for members of a preserving circle who have never made jam. Four planted problems (ten 340 g jars given as 2.4 kg, the jars washed after they are filled, 15 against 8 minutes of hard boil, "the flake test" unexplained) and eight candidate must-tell omissions written before any run: scalds, hot-jars, seal, not-set, oven, label, hygiene, contact. The notes ask a general question and name none of them.
- Pilot (calibration only, no skill condition): 5 no-skills runs through both stages (`evals/results/pilot-heldout15`). Screening rule: an item enters the decision count when the pilot's reviews ask for it in 1 to 4 of 5. If fewer than two items screen in, every item that is not 0 of 5 enters. The screened list is added to this file, in its own commit, before any skill run.
- Conditions: skill (independent-review 1.23, the commit holding this file), variant-r121 (1.21 at `68baece`), baseline (no skills). Ten repetitions, host omp, `claude-opus-5-5` as writer, reviewer, grader and judge.
- Stage 1: `run.py --judge omp --variant r121=68baece --judge-pairs skill:baseline,skill:variant-r121`. Stage 2: `review_stage.py --judge omp --pairs skill:variant-r121,skill:baseline --outside-facts`.
- Every errored call is resumed (`--resume`) until none remain, whatever the content.

## Decision rules

The same as `v-review-brief`. Counts use reviews that ran and were graded on every list. "Preferred" means, over decided judge pairs (ties and inconsistent verdicts excluded), a split a fair coin gives with probability 0.11 or less, two-sided: at 10 decided pairs 8 or more, 9 → 8, 8 → 7, 7 → 7, 6 → 6, 5 → 5, 4 or fewer cannot decide. "Ahead on must-tell" means a total over the screened items at least 15% of the maximum above the other's. Hint and leak failures are the case's `not_regex` and `not_contains` checks as run.

1.23 ships if (A) the prompt judge prefers 1.23's prompts over 1.21's, or (B) the review judge prefers 1.23's reviews over 1.21's; and none of these holds:

1. The review judge prefers 1.21's reviews.
2. 1.21 is ahead of 1.23 on must-tell.
3. 1.23 finds fewer planted problems than 1.21 by 4 or more of 40.
4. 1.23's stage-1 hint and leak failures exceed 1.21's by 2 or more.
5. 1.23's outside-fact total exceeds 1.21's by 7 or more.

Otherwise 1.21 stays: `skills/independent-review/` is reverted to its 1.21 text in the write-up commit, and the case and this file stay. No further brief variant is tried in this round.

## Reported, not decided

- The gap to no skills for 1.23 and for 1.21 at both stages: prompt judge, review judge, must-tell, planted problems found, outside facts.
- Must-tell per item over the screened items and over all eight, for each condition.
- Prompt and review lengths per condition.
- Hint and leak failures per condition, each read by hand.
- Check corrections, if any, beside the as-run numbers.
