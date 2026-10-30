# Pre-registration: v-review-must-tell

Written before any run of a skill condition on the case below. This run ships no skill version. It tests a new measure for reviewer prompts and decides what the next change to independent-review must target. The rules do not change after the results are known.

## Background

On three held-out cases (`v-review-slim`, `v-review-question`, `v-review-checklist`) the reviews from no-skills prompts were preferred over those from the skill's prompts, and the planted-problem count sat at the ceiling for every condition, so it could not say why. In the last run the judge's reasons were not missed problems but what a careful reader was told: the river-level check before launch, a landing point and carry route at the weir. The planted list did not score that.

This run adds `review_stage.must_tell`: things the reader must be told before acting that the draft omits, written from the reader's job before any run. A grader marks each review `TOLD <id>: yes|no`; a bundled mention counts. `evals/review_stage.py` and `evals/grade.py` were extended and tested in the same commit as this file.

## Design

- Case: `independent-review/heldout12-kiln-firing-reviewer-prompt`, committed with this file. A one-page sheet for firing a pottery group's kiln; the reader has never run a firing. Four planted problems (a total that does not add up, Start pressed before the lid is closed, "stilt" and "batt-washed" unexplained, 2 cm against 4 cm) and five must-tell omissions (when it is safe to open the kiln, how to stop it, who to call, how to get in during a 9am-to-9am slot, whether it may run with nobody there). The notes ask a general question and name none of them. Stage 1 checks the reader, leaks, and hints that point at a planted problem or tell the reviewer what the sheet lacks ("the sheet never says when to open it"). Reader-role questions ("who do I call if something goes wrong?") are allowed: the skill's template derives them from the reader's job, and whether that mechanism helps is part of what this run measures. The hint pattern was tested before any run against the 1.16 to 1.18 templates and 60 earlier prompts; it matched none.
- Pilot (calibration only, no skill condition): 3 no-skills runs through both stages (`evals/results/pilot-heldout12`). Reviews found 9 of 12 planted problems and asked for 9 of 15 must-tell items (cool-down, stop and who-to-call 3 of 3 each; access and unattended 0 of 3). All 27 grader verdicts were read by hand and hold. One pilot prompt wrapped the sheet in `--- DRAFT NOTICE ---`, which the `no_added_facts` allow-list did not cover; the list was widened for every condition before any skill run. The pilot is not part of the results.
- Conditions: skill (independent-review 1.18, this commit) and baseline (no skills). Ten repetitions, host omp, default model throughout.
- Stage 1: `run.py --judge omp --judge-pairs skill:baseline`. Stage 2: `review_stage.py --judge omp --pairs skill:baseline`.

## Decision rules

Counts use reviews that ran and were graded on both lists; more than 2 errors in a condition means the stage is resumed before it is read; stage 1 host errors above 5% in a condition make the run inconclusive and it is resumed. "Preferred" means, over decided judge pairs (ties and inconsistent verdicts excluded), a split a fair coin gives with probability 0.11 or less, two-sided: at 10 decided pairs 8 or more, 9 → 8, 8 → 7, 7 → 7, 6 → 6, 5 → 5, 4 or fewer cannot decide. "Ahead on must-tell" means a total of must-tell items asked for (0 to 50 per condition) at least 7 above the other's. If both conditions ask for 45 or more of 50, the measure is at the ceiling on this case and no conclusion below is drawn from it.

Exactly one of these is recorded as the result:

1. No skills is ahead on must-tell. Then the reviewer prompt underperforms no skills on what the reader must be told, and the next change to independent-review's reviewer prompt must target must-tell coverage; it is judged by this measure on a fresh case, with the review judge reported.
2. 1.18 is ahead on must-tell. Then the judge's preference for no skills, if it recurs here, is not about what the reader is told; the next step is to score what the judge's reasons name instead.
3. Neither is ahead. Then must-tell does not separate the two on this case; the per-item counts and the judge are reported, and no template change follows from this run.

## Reported, not decided

- Review judge and prompt judge for skill against no skills, each stage on its own.
- Agreement between must-tell and the review judge: per repetition, whether the review the judge preferred is the one that asked for more must-tell items.
- Must-tell per item and per condition; planted problems found per condition (expected at or near the ceiling).
- Reader-role questions in prompts that correspond to a must-tell item, counted by hand per condition, and the must-tell totals with and without the runs whose prompts carry one.
- Hint-check and leak-check failures per condition, each read by hand; every prompt read by hand, with the sheet's own text removed, for hints the check misses.
- Prompt and review lengths; misquote spans, each read by hand; grader answers checked by hand on every disagreement with a first reading and on a sample of the rest. Check corrections, if any, are reported beside the as-run numbers (`report-as-run.md`, `results-as-run.json`).
