# Pre-registration: v-review-slim

Written before any run on the case below. The rules decide which reviewer template independent-review ships; they do not change after the results are known.

## Background

In `v-review-e2e` the reviews produced by independent-review 1.14's reviewer prompts lost to the reviews from no-skills prompts 10-0, with the same planted problems found (49 and 50 of 50). The judge preferred reviews that group related problems into one fix and are shorter; 1.14's reviews follow the template's fixed protocol (a two-sentence restatement, six review areas, a severity scale, a per-finding form, a keep list). On the `v-review114-paste` runs, the reviews from 1.13's prompts also beat 1.14's 8-1, so pasting the document into the prompt may itself make the reviews thinner. Neither result was a pre-registered decision.

The slim template (this commit) keeps the reader brief, the leak rules, the `Reviewer-Model`, `Read:` and `VERDICT` lines and the "no critical or major findings" phrase that triage relies on. It drops the restatement, the six review areas, the severity scale and its definitions, the per-finding form and the keep list. The reviewer answers each reader question in one line (yes, partly, no), then lists the problems the reader would hit, worst first, one item per fix. Genre and the reader's reason for opening the document are no longer separate lines.

## Conditions

All at host omp, default model, 10 repetitions, on the fresh held-out case `independent-review/heldout9-hall-booking-reviewer-prompt` (written and committed with this file). The case is a hall-booking page with six planted problems: a wrong worked cost (£62 for four hours at £18), two notice periods (two weeks, ten days), two finishing times (11pm, 10:30pm), an unexplained "HMC", a booking form the page says is attached but is not, and a contact with no address. Unlike `heldout8`, the author's notes ask only the general question (could a new member book and use the hall from this page alone?) and name none of the problems.

- skill: 1.16, the slim template with the document copied in (this commit).
- variant-path: 1.15 at `745cf7b`, the same slim template with the document given by path.
- variant-r114: the 1.14 template at `ceab553`.
- baseline: no skills.

Stage 1: `run.py --judge omp --judge-pairs skill:baseline,skill:variant-path,skill:variant-r114`. Stage 2: `review_stage.py --judge omp --pairs skill:variant-path,skill:variant-r114,variant-path:variant-r114,skill:baseline,variant-path:baseline`. The reviewer gets only `draft.md`; for the path version that is where the document is.

## Decision rules

Counts use reviews that ran and were graded. More than 2 errors in a condition means the stage is resumed before it is read. "Preferred" means, over decided review-judge pairs (ties and inconsistent verdicts excluded), a split a fair coin gives with probability 0.11 or less, two-sided: at 10 decided pairs 8 or more, 9 → 8, 8 → 7, 7 → 7, 6 → 6, 5 → 5, 4 or fewer cannot decide. "Finds more" means a total of planted problems found (0 to 60 per condition) at least 6 above the other's.

1. **Paste or path.** The path version is chosen if its reviews are preferred over the pasted version's, or it finds more. Otherwise the pasted version is chosen: a reviewer in a fresh session then needs none of the writer's files.
2. **Slim or 1.14.** The version chosen in rule 1 ships unless 1.14's reviews are preferred over it, or 1.14 finds more. If either holds, the 1.14 template is restored.
3. **No new leaks.** The version chosen in rule 1 also fails rule 2 if its prompts fail the stage 1 leak check (`not_contains`) in more runs than 1.14's plus one.

Outcome: pasted version ships → 1.16 stays. Path version ships → 1.17 carries the path text. Rule 2 or 3 fails → 1.17 restores the 1.14 template.

## Reported, not decided

- Reviews against no skills (judge, planted problems found), for both slim versions.
- Stage 1 prompt verdicts and checks per condition, and prompt and review lengths.
- Misquotes: double-quoted spans of three words or more in a review that occur in neither the document nor the prompt. Every flagged span is read by hand and sorted into misquote or proposed wording (on 60 earlier reviews the check flagged 2 spans, both proposed wording).
- Every reviewer prompt is read by hand, with the page's own text removed, for hints of a planted problem. Runs with hints are listed and the found totals are given with and without them; the decision uses all runs.
- A sample of grader answers is checked by hand; disagreements are reported and do not change the decision.

## What does not count

Host errors in stage 1 are excluded; more than 5% in a condition makes the run inconclusive and it is resumed.
