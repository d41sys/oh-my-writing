# Pre-registration: v-review-brief

Written before any run of a skill condition on the case below. It decides whether independent-review 1.22 replaces 1.21. The rules do not change after the results are known.

## Background

In `v-fix-opus` (claude-opus-5-5, 14 reviewer-prompt cases, 3 repeats) the prompt judge preferred the no-skills prompts over 1.21's 40 to 7. Its reasons named the form: a labelled-field layout, a `Reviewer-Model:` line, a `VERDICT:` line, an experienced-reader persona and a list of reader questions the author never asked for. The median 1.21 prompt ran to 751 words against 452 without a skill.

1.22 turns the template into a plain brief in the author's voice: who reads the document and what they do with it, the author's question, how to read it in one or two general sentences, what to send back, and the document. The persona, the reader-question list and the placeholder table are gone. The `Reviewer-Model:` and `VERDICT:` lines stay only for reviews the skill runs itself. The guards against leaked context and findings written in advance are unchanged.

The brief was written after reading the no-skills prompts of `v-fix-opus` on the earlier reviewer-prompt cases (heldout2 to heldout13), and its "how to read it" sentence resembles several of them. Those cases therefore count as tuned for 1.22. Only the case below decides.

## Design

- Case: `independent-review/heldout14-teaching-hive-reviewer-prompt`, committed with this file before any run on it. A one-page sheet for members of a beekeeping association who have done the theory course and never opened a hive. Four planted problems (a suit count that does not add up, the suit put on after the hive is open, 10 against 20 minutes open, "a Pagden" neither explained nor provided for) and eight candidate must-tell omissions written before any run: sting-reaction, weather, smoker-out, smoker-fuel, defensive, clothing, disease, contact. The notes ask a general question and name none of them.
- Pilot (calibration only, no skill condition): 5 no-skills runs through both stages (`evals/results/pilot-heldout14`). Screening rule: an item enters the decision count when the pilot's reviews ask for it in 1 to 4 of 5. The screened list is added to this file, in its own commit, before any skill run.
  - Pilot result, as graded: sting-reaction 5, weather 5, smoker-out 5, smoker-fuel 5, defensive 4, clothing 3, disease 4, contact 5; planted problems 20 of 20. **Screened items: defensive, clothing, disease** (0 to 30 per condition, so "ahead on must-tell" needs a lead of 5). All five pilot prompts passed every check. The grades were not read by hand. With five of eight items at the ceiling and the other three near it, must-tell has little room to separate the conditions on this model; the judges carry most of the decision.
- Conditions: skill (independent-review 1.22, the commit holding this file), variant-r121 (1.21 at `7cb6355`), baseline (no skills). Ten repetitions, host omp, `claude-opus-5-5` as writer, reviewer, grader and judge.
- Stage 1: `run.py --judge omp --variant r121=7cb6355 --judge-pairs skill:baseline,skill:variant-r121`. Stage 2: `review_stage.py --judge omp --pairs skill:variant-r121,skill:baseline --outside-facts`.
- Every errored call is resumed (`--resume`) until none remain, whatever the content.

## Decision rules

Counts use reviews that ran and were graded on every list. "Preferred" means, over decided judge pairs (ties and inconsistent verdicts excluded), a split a fair coin gives with probability 0.11 or less, two-sided: at 10 decided pairs 8 or more, 9 → 8, 8 → 7, 7 → 7, 6 → 6, 5 → 5, 4 or fewer cannot decide. "Ahead on must-tell" means a total over the screened items at least 15% of the maximum above the other's. Hint and leak failures are the case's `not_regex` and `not_contains` checks as run.

1.22 ships if (A) the prompt judge prefers 1.22's prompts over 1.21's, or (B) the review judge prefers 1.22's reviews over 1.21's; and none of these holds:

1. The review judge prefers 1.21's reviews.
2. 1.21 is ahead of 1.22 on must-tell.
3. 1.22 finds fewer planted problems than 1.21 by 4 or more of 40.
4. 1.22's stage-1 hint and leak failures exceed 1.21's by 2 or more.
5. 1.22's outside-fact total exceeds 1.21's by 7 or more.

Otherwise 1.21 stays: `skills/independent-review/` is reverted to its 1.21 text in the write-up commit, and the case and this file stay.

## Reported, not decided

- The gap to no skills for 1.22 and for 1.21 at both stages: prompt judge, review judge, must-tell, planted problems found.
- Must-tell per item over the screened items and over all eight, for each condition.
- Prompt and review lengths per condition.
- Hint and leak failures per condition, each read by hand; every 1.22 prompt read by hand for the form lines the brief was meant to remove.
- Check corrections, if any, beside the as-run numbers.
