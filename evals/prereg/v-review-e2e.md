# Pre-registration: v-review-e2e

Written before any run on the cases below. The rules decide what this run means; they do not change after the results are known. Nothing in the skills changes for this run: it measures.

## Background

On reviewer-prompt cases the judge has preferred prompts written without skills to independent-review's in every recent run (10-0 against 1.14 in `v-review114-paste`). Its reasons there: the no-skills prompt centres on the author's own question, while the skill's prompt sets that question inside a fixed review protocol (six review areas, severity levels, a verdict line) and is about twice as long. But that judge reads only the prompt, never the review the prompt produces. This run asks whether the prompt-level loss carries over to the reviews.

New tool: `evals/review_stage.py`. For each finished run it sends the saved reviewer prompt, as its whole input, to a fresh omp session with no skills and read-only tools, in a workspace holding only the draft. The reply is the review. A grader call then says, for each problem planted in the draft, whether the review identifies it, and a blind judge compares the reviews in pairs, in both orders. Before this file was written, the grader was tried on three hand-written reviews of the primary case: one naming all five problems (5 of 5 found), one naming none (0), and one touching the topics but calling them fine (0).

## Design

- Primary case: `independent-review/heldout8-farm-trip-reviewer-prompt`, written and committed with this file before any run. A school trip letter with five planted problems a parent would hit, fixed in the case: the slip's £15 against the £12 trip cost, no return or collection time, a consent deadline the day after the trip, an unexplained "PLP scheme", and "pay the usual way". The author's notes do not mention any of them.
- Conditions: skill (independent-review 1.14, all skills at the commit that adds this file) and baseline (no skills). Ten repetitions each. Host omp, default model, for the writers, the reviewers, the grader and the judges.
- Stage 1 (`run.py --judge omp`): the prompts, judged skill:baseline as before. Stage 2 (`review_stage.py --judge omp --pairs skill:baseline`): the reviews.
- Secondary, reported only: the review stage on the finished runs of `v-review114-paste` (case heldout7, no planted problems), pairs skill:baseline, skill:variant-r113 and variant-r113:baseline.

## Questions and decision rules

Counts use the reviews that ran and were graded; errored ones are excluded. More than 2 errors in a condition means the stage is resumed before it is read.

1. **Planted problems found.** Total over the ten reviews (0 to 50 per condition). One side "finds more" if its total is at least 5 above the other's (half a problem per review); otherwise no difference is shown.
2. **Judge on the reviews.** Decided pairs (ties and inconsistent verdicts excluded). One side is preferred if a fair coin would give a split at least that lopsided with probability 0.11 or less (two-sided binomial): at 10 decided pairs, 8 or more; at 9, 8; at 8, 7; at 7, 7; at 6, 6; at 5, 5; 4 or fewer cannot decide.

What follows:

- **No skills better** on 1 or 2, and the skill better on neither: the protocol makes reviews worse, not only prompts longer. Next step: a pre-registered slimmer reviewer template.
- **Skill better** on 1 or 2, and no skills better on neither: the prompt-level judge loss does not carry over to reviews. BENCHMARK says so, and the review stage becomes the main measure for independent-review's reviewer prompts.
- **Each better on one, or neither better on either**: no template change is justified by the prompt-level judge result alone; BENCHMARK reports the numbers.

## Reported, not decided

- The stage 1 prompt verdicts beside the review verdicts.
- Review length per condition.
- Every reviewer prompt is read by hand for hints of the planted problems (a prompt that points the reviewer at one would inflate its count). Runs with hints are reported, and question 1 is reported with and without them; the decision uses all runs.
- The stage 1 checks (leaks, reader, invented facts) per condition.

## What does not count

- Host errors in stage 1 are excluded; more than 5% in a condition makes the run inconclusive and it is resumed.
- The grader is one model's reading. Its answers on a sample of reviews are checked by hand and disagreements are reported; they do not change the decision.
