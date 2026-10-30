# Pre-registration: v-review-question

Written before any run on the case below. The rules decide whether independent-review 1.17 ships; they do not change after the results are known.

## Background

`v-review-slim` left three things open. (1) Against no skills, the judge still preferred the no-skills reviewer prompts 8-0 and their reviews 6-1. Its reasons there, and in `v-review114-paste` and `v-review-e2e`, are about focus: the winner answers the author's own question first ("a new member cannot book from this page alone") and leads with what stops the reader acting. 1.16 replaced the author's question with three to five reader questions it wrote itself and ranked problems by "act wrongly" before "slows down", with nothing for "cannot act at all". (2) Three of 1.16's ten prompts told the reviewer where to look ("do not assume that a form, link, address, or contact detail exists", "internal committee names"): findings written in advance, which the case had no check for. (3) Planted problems were found at the ceiling (57 to 59 of 60) in every condition.

1.17 (this commit) carries the author's own question about the reader, in the author's words, in a new `REVIEW_QUESTION` line that the reviewer answers first; the reader questions become optional context, and one the page does not answer is a problem in the list. Problems are ranked: what stops the reader acting at all, then what makes them act wrongly, then what slows them down. "Before you send" and SKILL.md step 2 now name rules that point at a kind of gap seen in the draft as findings written in advance.

## Design

- Case: `independent-review/heldout10-allotment-welcome-reviewer-prompt`, written and committed with this file before any run. An allotment welcome sheet with seven planted problems: the rent instalments do not add up (2 × £20 against £48), the starter pack needs a membership card that is posted up to four weeks later, new holders are not told how to get the gate code before the next monthly text, "Saturday 7 March 2027" is a Sunday, a hosepipe is allowed in July and August but banned May to September, the site rep is never named or reachable, and the online calendar has no link. The author's notes ask only a general question and name none of them. Stage 1 now checks for hints that point the reviewer at a planted problem (`not_regex`; general rules such as "check the arithmetic" or "do not invent contact details" are allowed), with two trap controls.
- Conditions: skill (1.17, this commit), variant-r116 (1.16 at `1ce8161`), baseline (no skills). Ten repetitions, host omp, default model throughout.
- Stage 1: `run.py --judge omp --variant r116=1ce8161 --judge-pairs skill:baseline,skill:variant-r116`. Stage 2: `review_stage.py --judge omp --pairs skill:variant-r116,skill:baseline,variant-r116:baseline`.

## Decision rules

Counts use reviews that ran and were graded; more than 2 errors in a condition means the stage is resumed before it is read; host errors in stage 1 above 5% in a condition make the run inconclusive and it is resumed. "Preferred" means, over decided judge pairs (ties and inconsistent verdicts excluded), a split a fair coin gives with probability 0.11 or less, two-sided: at 10 decided pairs 8 or more, 9 → 8, 8 → 7, 7 → 7, 6 → 6, 5 → 5, 4 or fewer cannot decide. "Finds more" means a total of planted problems found (0 to 70 per condition) at least 7 above the other's.

1.17 ships unless any of these holds; if one does, 1.18 restores the 1.16 text.

1. 1.16's reviews are preferred over 1.17's, or 1.16 finds more.
2. 1.16's prompts are preferred over 1.17's at stage 1.
3. 1.17's prompts fail the hint check (`not_regex`) in more runs than 1.16's plus one, or the leak check (`not_contains`) in more runs than 1.16's plus one.

## Reported, not decided

- Whether the gap to no skills closed: it counts as closed on this case if the judge prefers no skills at neither stage (same threshold), and narrowed if 1.17's record against no skills is better than 1.16's at both stages in this run.
- Planted problems found per condition and per problem. If every condition finds 63 or more of 70 (90%), the count is at the ceiling and said to be uninformative.
- Hint-check and leak-check failures per condition, and the found totals with and without runs that fail the hint check.
- Prompt and review lengths; misquote spans, each read by hand.
- Every prompt read by hand, with the sheet's own text removed, for hints the check misses; a sample of grader answers checked by hand. Disagreements are reported and do not change the decision. Check corrections, if any, are reported beside the as-run numbers (`report-as-run.md`, `results-as-run.json`).
