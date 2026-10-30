# Pre-registration: v-review-checklist

Written before any run of a skill condition on the case below. The rules decide whether independent-review 1.18 ships; they do not change after the results are known.

## Background

In `v-review-question`, 1.17 narrowed the gap to no skills (prompts 1-9, reviews 2-8; 1.16 had 0-10 and 0-10) without closing it. The judge's reasons were the same at both stages: eight of the ten no-skills prompts direct the reviewer to "contradictions, impossible sequences, and dates or amounts that do not add up", and their reviews caught the hosepipe contradiction and the Sunday date that 1.17's reviews missed. The slim template (1.16) had dropped its list of what to look for. One 1.17 review also called a 2027 date "already past" on a 2026 reading date.

1.18 (this commit) adds one general step before the problem list: read the document once more for sections that disagree, figures and totals that do not add up, a weekday that does not match its date, steps in an order the reader cannot follow, and steps that need something the reader will not have yet. It also says a reading date places dates without a year and relative dates, and that a full date is called past only after comparing day, month and year with the reading date.

## Design

- Case: `independent-review/heldout11-canoe-hire-reviewer-prompt`, committed with this file. A canoe-hire guide with six planted problems: three of kinds the new step names (a family price that does not add up, two capacities, the safety briefing listed after launching) and three it does not (a capsize procedure never given, "portage" unexplained, no deposit amount). The notes ask a general question and name none of them. Stage 1 checks the reader, leaks, and hints that point at a planted problem (`not_regex`; general rules allowed). The hint pattern was tested before any run against the 1.16, 1.17 and 1.18 templates and 30 earlier skill prompts: it matched none except one real pointed hint from `v-review-slim`.
- Pilot (calibration only, no skill condition): 3 no-skills runs through both stages (`evals/results/pilot-heldout11`). Their reviews found 16 of 18 planted problems (89%: all but the deposit amount twice), just under the 90% at which the case would have been reworked. One pilot prompt numbered the guide's lines past 20, which the `no_added_facts` allow-list did not cover; the list now runs to 40 for every condition. The pilot is not part of the results.
- Conditions: skill (1.18, this commit), variant-r117 (1.17 at `ed43a70`), baseline (no skills). Ten repetitions, host omp, default model throughout.
- Stage 1: `run.py --judge omp --variant r117=ed43a70 --judge-pairs skill:baseline,skill:variant-r117,variant-r117:baseline`. Stage 2: `review_stage.py --judge omp --pairs skill:variant-r117,skill:baseline,variant-r117:baseline`.

## Decision rules

Counts use reviews that ran and were graded; more than 2 errors in a condition means the stage is resumed before it is read; stage 1 host errors above 5% in a condition make the run inconclusive and it is resumed. "Preferred" means, over decided judge pairs (ties and inconsistent verdicts excluded), a split a fair coin gives with probability 0.11 or less, two-sided: at 10 decided pairs 8 or more, 9 → 8, 8 → 7, 7 → 7, 6 → 6, 5 → 5, 4 or fewer cannot decide. "Finds more" means a total of planted problems found (0 to 60 per condition) at least 6 above the other's.

1.18 ships unless any of these holds; if one does, 1.19 restores the 1.17 text.

1. 1.17's reviews are preferred over 1.18's, or 1.17 finds more.
2. 1.17's prompts are preferred over 1.18's at stage 1.
3. 1.18's prompts fail the hint check (`not_regex`) in more runs than 1.17's plus one, or the leak check (`not_contains`) in more runs than 1.17's plus one.

## Reported, not decided

- Gap to no skills at each stage, for 1.18 and 1.17: closed on this case if the judge prefers no skills at neither stage; narrowed if 1.18's record against no skills is better than 1.17's at both stages.
- Planted problems found per condition and per problem, split into the three kinds the new step names and the three it does not. If every condition finds 54 or more of 60 (90%), the count is at the ceiling and said to be uninformative.
- Reviews that call a date past or wrong when it is not, read by hand.
- Hint-check and leak-check failures per condition; found totals with and without runs that fail the hint check; every prompt read by hand, with the guide's own text removed, for hints the check misses.
- Prompt and review lengths; misquote spans, each read by hand; a sample of grader answers checked by hand. Check corrections, if any, are reported beside the as-run numbers (`report-as-run.md`, `results-as-run.json`).
