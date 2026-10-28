# Pre-registration: v-upstream-omp

Written before any run. The rules below decide what this run means; they do not change after the results are known.

## What is tested

The skill revisions from the upstream review: anti-slop-editing 1.16, evidence-grounded-writing 1.9, independent-review 1.5, author-voice 1.5 (commits c1c74bd, f3b44e4, fdac11e).

- Cases: every case of those four skills (28, including the 8 new anti-slop edit/keep pairs) and the five style and reader cases that belong to them: style/revise-slop-heavy-announcement, reader/heldout-policy-brief-lead-pipes, reader/repair-cafe-grant-abstract, reader/reviewer-reply-volunteer-survival, reader/tree-ring-conference-abstract. 33 cases.
- Conditions: skill, baseline, variant-placebo. Three repetitions each. Host omp (omp/18.13.3; the reference v-iso-omp ran on omp/18.11.3), default model.
- Judge: omp, blind pairs skill:baseline and skill:variant-placebo.

## Hypotheses and decision rules

1. **No regression (decides whether the revisions stay).** `gate.py check` of this run against the frozen reference (v-iso-omp) has no gated FAIL in anti-slop-editing, evidence-grounded-writing, independent-review, author-voice or ALL. A FAIL in one skill means its revision is held back until the failing cases are read and explained; a WARN is read but does not hold anything back.
2. **The content helps, not the length (decides what we may claim).** On all 33 cases, the skill condition's case pass rate is at least 10 points above variant-placebo, and the blind judge prefers skill over variant-placebo in more decided pairs than it prefers the placebo. Only if both hold do we say the skills' content, not a longer prompt, produces the gain. If either fails, the README says so.
3. **The new edit/keep pairs.** On the 8 anti-slop pair cases, the skill condition passes at least as often as baseline and as variant-placebo. If it passes fewer keep cases than baseline, the anti-slop rules over-edit, and the four changed catalog entries are revised before release.

## What does not count

- Differences of one or two cases in a per-skill row are noise (3 to 14 cases per skill).
- Host errors are excluded from both sides, as the grader does. More than 5% host errors in any condition makes the run inconclusive; it is resumed, not read.
- The A/A noise test already fails on report-writing slop_per_1000w before this work; report-writing is not in this run.
