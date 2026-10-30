# Pre-registration: v-review-stance

Written before any run of a skill condition on the case below. It decides whether independent-review 1.19 replaces 1.18. The rules do not change after the results are known.

## Background

In `v-review-must-tell` (heldout12, kiln) the review judge preferred the reviews from no-skills prompts over 1.18's 7 to 1 and named expert depth: whether the clay and glaze suit the kiln (10 of 10 against 5 of 10) and the limits of the cheek test (7 of 10 against 0 of 10). Six of ten no-skills prompts cast the reviewer as a safety and usability reviewer; every 1.18 prompt says "you are one of this document's intended readers". A novice reader does not know what to ask, so a reviewer reading as that novice misses what an experienced person would make sure the novice knows.

1.19 changes the stance: the reviewer reads on the reader's behalf, as the person who normally does the task for this reader or trains them (`{{EXPERIENCED_READER}}`, a role only, never a list of what to check), and a new step asks what that person would make sure the reader knows before starting. The rule that a fix adds no fact stays and is restated: use what you know to see what is missing or risky, never to fill a gap. The packet step in SKILL.md and the eval.md packet checks name the role.

An expert stance carries a risk 1.18 did not: a reviewer that knows the domain may fill gaps with its own facts, which the author cannot check against the document and which may be wrong. This round adds a guard for it: `review_stage.py --outside-facts` asks a grader to list each statement in a review that gives, as correct, content the document does not contain (a value, a named product, a rule, how to carry out a step), excluding statements that something is missing, instructions to the author to supply it, named topics without the how, reasons and risks, verdicts on the document, and fixes that reorder what the document says. Quotes under four words are not counted. The grader prompt was calibrated on the saved kiln reviews and the pilot below before this file was committed; it is noisy (it still flags some named topics and reorder fixes), so every flagged statement is read by hand and reported beside the as-run count.

## Design

- Case: `independent-review/heldout13-darkroom-reviewer-prompt`, committed in `b1074cf` before the pilot. A one-page darkroom sheet for photography club members who have only shot digital. Four planted problems (a stop-bath volume that does not add up, the main light switched on before the film is in the closed tank, 9 minutes against 6½ minutes, "hypo clear" unexplained and not among the listed chemicals) and eight candidate must-tell omissions written before any run: disposal, protection, ventilation, first-aid, temperature, reuse, safelight, contact. The notes ask a general question and name none of them.
- Pilot (calibration only, no skill condition): 5 no-skills runs through both stages (`evals/results/pilot-heldout13`). Screening rule, written in the case before the pilot: an item enters the decision count when the pilot's reviews ask for it in 1 to 4 of 5. As graded: disposal 5, protection 3, ventilation 1, first-aid 2, temperature 3, reuse 0, safelight 5, contact 0. **Screened items: protection, ventilation, first-aid, temperature** (0 to 40 per condition). The pilot's 25 planted-problem grades (20 of 20 found) and 40 must-tell grades were read by hand; one credit is lenient (r4 protection, from "no chemical-handling directions"), and protection stays in range either way. All five pilot prompts were read by hand: no leak, no pointed hint; all passed every stage-1 check. The pilot is not part of the results.
- Conditions: skill (independent-review 1.19, the commit holding this file), variant-r118 (independent-review 1.18 at `dc50200`), baseline (no skills). Ten repetitions, host omp, default model throughout.
- Stage 1: `run.py --judge omp --variant r118=dc50200 --judge-pairs skill:baseline,skill:variant-r118,variant-r118:baseline`. Stage 2: `review_stage.py --judge omp --pairs skill:variant-r118,skill:baseline,variant-r118:baseline --outside-facts`.
- Provider errors: the host's provider currently rejects a share of model calls ("model not supported", quota), which shows as a host error or a grader error. Every errored call is resumed (`--resume`) until none remain, whatever the content; a review whose planted-problem grade failed is rerun as a whole (the existing resume behaviour), other failed grades are redone on the saved review. The number of resume passes is reported.

## Decision rules

Counts use reviews that ran and were graded on every list. "Preferred" means, over decided judge pairs (ties and inconsistent verdicts excluded), a split a fair coin gives with probability 0.11 or less, two-sided: at 10 decided pairs 8 or more, 9 → 8, 8 → 7, 7 → 7, 6 → 6, 5 → 5, 4 or fewer cannot decide. "Ahead on must-tell" means a total over the four screened items at least 6 above the other's (15% of the 40 maximum). Stage-1 hint and leak failures are the case's `not_regex` and `not_contains` checks as run. Outside facts are the grader's count as run.

1.19 ships if (A) it is ahead of 1.18 on must-tell, or (B) the review judge prefers 1.19's reviews over 1.18's; and none of these holds:

1. 1.19's outside-fact total exceeds 1.18's by 7 or more.
2. The review judge prefers 1.18's reviews.
3. The prompt judge (stage 1) prefers 1.18's prompts.
4. 1.19's stage-1 hint and leak failures exceed 1.18's by 2 or more.

Otherwise 1.18 stays: the 1.19 text in `skills/independent-review/` is reverted to 1.18 in the write-up commit, and the outside-fact guard, the case and this file stay.

## Reported, not decided

- Must-tell over the four screened items and over all eight, per item, for each condition; gap to no skills for 1.19 and 1.18 at both stages (must-tell, review judge, prompt judge).
- Planted problems found per condition (expected at or near the ceiling).
- Every flagged outside-fact statement, read by hand and classified as supplies content / names a topic / other; the classified totals beside the as-run totals.
- Every 1.19 prompt's `EXPERIENCED_READER` fill, and whether it carries a list of what to check; the reviewer role every no-skills and 1.18 prompt sets.
- Hint-check and leak-check failures per condition, each read by hand; every prompt read by hand, with the sheet's text removed, for hints the check misses.
- Grader answers checked by hand on every disagreement with a first reading and on a sample of the rest; misquote spans; prompt and review lengths. Check corrections, if any, are reported beside the as-run numbers.
