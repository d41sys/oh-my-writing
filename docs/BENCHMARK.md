# Benchmark and tests

## Summary

On realistic writing tasks, an agent with these skills passed **89%** of tuned runs; the same agent with no skills passed **42%**. Against seven public writing-skill packs, it passed more runs than each of them. A blind model judge preferred our output to every pack except Humanizer. Against no skills at all, the judge split close to even. So the skills make output reliably more faithful to the material, but not clearly better-sounding.

## Setup

- **Host and model:** omp with gpt-6-sol. Judges also use gpt-6-sol. Results directory `v-final2-omp`.
- **Cases:** 59 tasks across the ten writing skills, each run 3 times (177 runs per condition). Each case has:
  - a prompt and material files: notes, transcripts, drafts, and real document folders with docx, xlsx, pptx, pdf, eml and csv files;
  - mechanical checks.
- **Checks** grade what matters for trust:
  - invented facts (any number, name, date or URL not in the material);
  - lost negations, hedges and scope;
  - missing gap markers;
  - stock AI phrasing;
  - leaked context;
  - task-specific requirements.
- **Conditions:**
  - *skills*: the current skills;
  - *no skills*: the same agent and model;
  - *old skills*: an earlier version, for A/B;
  - *competitor*: the agent with one public writing pack installed in place of ours, on the cases that pack targets.
- **Judge:** a blind pairwise judge sees both outputs in both orders. A pick that flips when the order is swapped counts as *inconsistent* (I), not as a win.
- **Case groups:**
  - *Tuned* (42 cases): used while improving the skills.
  - *Held-out 1* (7 cases): written before the last two rounds and never tuned on.
  - *Held-out 2* (10 cases): written by a separate agent with no access to results. Their checks were later audited on real outputs of all conditions, so they now separate the conditions only weakly.

## Pass rates

| Case group | With skills | Old skills | No skills |
|---|---|---|---|
| Tuned (126 runs) | **112 (89%)** | 84 (67%) | 53 (42%) |
| Held-out 1 (21 runs) | **17 (81%)** | 13 (62%) | 12 (57%) |
| Held-out 2 (30 runs) | 29 (97%) | 29 (97%) | 26 (87%) |

## Against other writing-skill packs

Runs are the same case and repeat for both sides.

| Pack | Runs | Ours passed | Theirs passed | Their skill loaded | Judge: ours W-L-T-I |
|---|---|---|---|---|---|
| [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | 42 | **37** | 21 | 42/42 | 10-3-3-2 |
| [humanizer](https://github.com/blader/humanizer) | 42 | **37** | 17 | 26/42 | 1-7-3-7 |
| [great-writer](https://github.com/d-wwei/great-writer) | 39 | **35** | 17 | 39/39 | 9-5-0-1 |
| doc-coauthoring ([Anthropic skills](https://github.com/anthropics/skills)) | 24 | **22** | 18 | 20/24 | 5-3-0-7 |
| marketing copywriting ([marketingskills](https://github.com/coreyhaines31/marketingskills)) | 21 | **18** | 12 | 21/21 | 9-4-0-2 |
| cover letter ([proficiently](https://github.com/proficientlyjobs/proficiently-claude-skills)) | 15 | **15** | 8 | 6/15 | 8-3-0-1 |
| [ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills) | 15 | **15** | 9 | 15/15 | 7-2-0-3 |

How to read this table:
- When a pack did not load, that run was effectively a no-skills run. On loaded runs only, humanizer passed 8/26 and we passed 22/26; proficiently passed 5/6 and we passed 6/6.
- The judge preferred Humanizer's output (1-7) even though ours passed far more checks.

## Judge against no skills

| Question | With skills preferred | No skills preferred | Inconsistent or tie |
|---|---|---|---|
| Which serves the reader better (all cases) | 52 | 58 | 43 |
| Which sounds more like a person | 14 | 7 | 3 |
| Which stays more faithful to the material | 18 | 2 | 4 |

## Reader track

Added after real use showed correct but defensive, fact-dense text: a caveat on many sentences, internal shorthand copied verbatim, template sections instead of a story. Fourteen synthetic cases (`evals/cases/reader/`, 4 held out and never tuned on) give raw notes plus an example of the required document. A blind judge answers three questions in both orders: does it read like the required document (fit), is it coherent, concise and one story (flow), and is it faithful. Mechanical checks only guard facts and length.

Judge W-L (ties and order-inconsistent picks left out). Writers on omp, judge gpt-6.1-sol. Rules v1 is `a46dfed`; rules v2 (`5203466`) adds the storyline and shorthand rules to post-writing and technical-docs; previous is `628a925`.

| Writer model | Comparison | Cases | Fit | Flow | Faithful |
|---|---|---|---|---|---|
| gpt-6.1-sol | rules v1 vs previous | all 14, 2 repeats | **16-3** | **14-7** | 0-3 |
| gpt-6.1-sol | rules v1 vs no skills | tuned 10, 2 repeats | 6-9 | 8-12 | 4-2 |
| gpt-6.1-sol | rules v1 vs no skills | held-out 4, 2 repeats | 6-2 | 6-2 | 1-1 |
| gpt-6.1-sol | rules v2 vs no skills | 3 tuned, 2 repeats | 1-3 | 1-2 | 2-0 |
| claude-opus-5-5 | rules v2 vs no skills | held-out 4, 1 repeat | 2-2 | 3-1 | 2-0 |
| claude-fable-5-1 | rules v2 vs no skills | held-out 4, 1 repeat | 1-2 | 1-2 | 3-1 |

- **Against previous skills:** fit and flow improved clearly, while faithfulness went 0-3. That is the expected cost of moving from "keep every stated value" to "keep the values the point depends on".
- **Fidelity regression on existing cases** (rules v2 against previous, gpt-6.1-sol, 1 repeat, all 26 report-writing, structured-drafting, evidence-grounded-writing, career-documents and style cases): both passed 20 of 26. No `preserves` check failed on either side, and invented facts were level at 2 each. The two runs that differ swap one wording check each way.
- **Against no skills:** style is at parity and faithfulness slightly ahead. The samples are too small to call either way.
- **Tuned-set runs:** in about half, the case's own skill did not load but neighbouring skills of ours did (structured-drafting, author-voice), so those losses still count against our rules.
- **Judge reasons for no-skill wins:** our output "ends like a measurement report", keeps more technical detail, and uses exact figures where the house style uses everyday proportions. Every condition ran longer than the style reference in about 40% of runs.
- **Rules v3** (`6938abb`): the self-check lists (`eval.md`) were brought in line with the new rules after a real revision still added "targets, not results" sentences. Tested on 2 held-out cases, 2 repeats, gpt-6.1-sol. Against no skills: fit 3-0, flow 1-1, faithful 2-0. Against rules v2: fit 1-3, flow 1-3, faithful 1-0. Four pairs are too few to tell v3 from v2.

## Placebo control (pre-registered)

Run `v-upstream-omp`: omp/18.13.3 with its default model, 3 repeats, after the skill revisions that followed the upstream review (anti-slop-editing 1.16, evidence-grounded-writing 1.9, independent-review 1.5, author-voice 1.5). It covers those four skills' 28 cases, including 8 new edit/keep pairs, plus the 5 style and reader cases that belong to them. The decision rules were committed before the first run (`evals/prereg/v-upstream-omp.md`, commit `c49e7e4`).

The placebo installs every skill with its real name, description and file layout, but each file's text is replaced by generic writing advice of about the same length. A gain over the placebo comes from what the skills say, not from having a longer prompt.

| Skill | With skills | Placebo | No skills | Runs per condition |
|---|---|---|---|---|
| anti-slop-editing | **76%** | 13% | 13% | 45 |
| author-voice | **80%** | 40% | 60% | 15 |
| evidence-grounded-writing | **57%** | 38% | 52% | 21 |
| independent-review | **83%** | 50% | 67% | 18 |
| All | **74%** | 29% | 38% | 99 |

Blind judge on text cases, wins and losses for our skills (ties and order-inconsistent picks left out):

| Skill | Against no skills | Against placebo |
|---|---|---|
| anti-slop-editing | 15-12 | 12-16 |
| author-voice | 7-6 | 7-7 |
| evidence-grounded-writing | 4-5 | 7-2 |
| independent-review | 2-11 | 1-9 |
| All | 28-34 | 27-34 |

The pre-registered rules, answered:

1. **No regression: met.** `gate.py check` against the frozen reference passed, so the revisions stay.
2. **The content helps, not the length: not met.** The pass rate is 45 points above the placebo, well over the 10 points required. But the blind judge preferred the placebo's output (34 to 27), and the rule needed both. So the checks show a gain from the skills' content and the judge does not.
3. **Edit/keep pairs: met.** With skills, 15 of 24 runs passed; the placebo and no skills passed none. On the keep cases (the text was already fine) we passed 9 of 12 and both others 0 of 12. Of those 24 other runs, 23 rewrote the text (similarity 0.42 to 0.95, below the 0.97 floor), most losing a protected phrase on the way; one left it unchanged but did not say so in the reply.

What else the run showed:

- **independent-review loses the judge** to both no skills and the placebo. The judge calls the other reviewer prompts and triage notes tighter and more focused on the decision the reader must make. Earlier runs leaned the same way on 3 cases.
  - Follow-up, version 1.6 (not pre-registered; run `v-review16-omp`, same 6 cases, 3 repeats). The reviewer prompt now opens on whether the reader could act on the document as written, and caps findings at seven. A triage of someone else's findings is now the table alone. Pass rate 14 of 18 (was 15 of 18).
  - The judge moved only on the tuned cases, the ones whose judge reasons shaped 1.6. Against no skills, tuned went from 2-6 to 6-2, held-out from 0-5 to 0-6. Against the placebo, tuned went from 1-5 to 3-2, held-out from 0-4 to 1-4. So 1.6 is not shown to help on unseen tasks.
  - Held-out triage lost 0-3 to no skills. Both sides reach the same four decisions; the judge prefers the findings grouped under the user's three headings (act, skip, answer yourself), while triage section 8 says to keep the reviewer's order. One run also added a condition the letter does not state (council approval to publish the reason). Changing section 8 now would tune on this held-out case, so it waits for a new held-out case.
  - Held-out reviewer prompt lost 0-3 to no skills and to the placebo. Some judge reasons favour what the skill rules out on purpose: steering the reviewer to gaps the writer already knows, passing on the author's wish to go easy on costs, and leaving out the `Reviewer-Model` and `Read:` lines that show the review was independent and complete. The judge prompt (`JUDGE_PROMPT` in `evals/run.py`) never asks whether a reviewer prompt keeps the reviewer independent, so it cannot score the property this skill exists for. The leak checks still pass in both prompt cases.
  - **New held-out cases, pre-registered** (`evals/prereg/v-review16-heldout.md`, run `v-review16-heldout`, 2 cases written after 1.6, 5 repeats). Conditions: 1.6, 1.5 (`80c1cc6`), the placebo and no skills. Judge wins and losses for 1.6: 2-5 against 1.5, 1-8 against no skills, 1-6 against the placebo. As run, the checks gave 1.6 10 of 10, 1.5 9 of 10, no skills 6 of 10 and the placebo 5 of 10. Most of that gap was check error: 10 failures outside the skill condition came from a refund hand-back worded in ways the check did not list ("Author must answer", "Do not promise a full refund") and from a line number and paste delimiters counted as facts. Corrected after the run, every condition passes 10 of 10 except the placebo (9 of 10, a missing decision date). Rule 1 failed: 1.6 is not shown to help on unseen tasks, and the judge prefers 1.5.
  - Most of the judge's reasons there have nothing to do with independence:
    - **Triage.** The judge's verdicts rest mainly on F1. The booking gives a 7:45 *pick-up*, but the finding calls it the "departure time" (and so does this case's own pass control). 1.6 adopted that framing and wrote 7:45 as the departure in 4 of 5 runs; 1.5, no skills and the placebo did so in 2 of 5 each. That is partly a case-design ambiguity. The F1 check was not changed after the run.
    - **Reviewer prompt.** No skills won 5-0 by carrying over the author's own three questions, which are about what the reader needs and so are allowed in the packet; 1.6 rewrote them in its own words. Only its `Reviewer-Model`/`Read:`/verdict lines come from the independence rules.
    - **A skill defect older than 1.6.** In 3 of 5 runs, both 1.6 and 1.5 told the reviewer that the meeting date has no year. That is a finding written in advance, which the independence rules forbid. The likely cause is the `READING_DATE` placeholder note together with the reviewer instruction to flag dates without a year.
    - One steering regex in the food-bank case was narrowed afterwards because it also matched a fair reader question; no run was affected.
  - **Reverted.** Version 1.7 restores the 1.5 text: the reviewer prompt, the triage report format and the self-check list. The missing-year defect above is still present and needs a fresh held-out case before any fix is claimed.
- **evidence-grounded-writing loaded in only 57% of its runs.** In 8 of the 9 misses a sibling skill loaded instead, so the row was measured partly with a sibling skill rather than with no skill.
  - Six of the misses were the two reader cases that write an abstract from notes (`repair-cafe-grant-abstract`, `tree-ring-conference-abstract`). Their prompts match structured-drafting's description, and structured-drafting loaded in all six. Both cases are now labelled `structured-drafting`.
  - The other three were `concise-keeps-hedge-and-scope` ("tighten this paragraph for our abstract"). There, structured-drafting, anti-slop-editing or no skill loaded. Its description now names that request ("make this abstract shorter"), and anti-slop-editing (1.17) and structured-drafting (1.10) each hand it over in their own descriptions.
  - Run `v-routing-omp` (skill condition only, 3 repeats, every case of the three skills, 0 host errors): evidence-grounded-writing loaded in 15 of 15 runs (12 of 15 on the same cases before; the tighten case went from 0 of 3 to 3 of 3), anti-slop-editing in 42 of 42. The gate passed.
  - structured-drafting still loads in only about half of its own cases (7 of 15 here; 1 of 9 to 9 of 12 in earlier runs). When it does not, post-writing or evidence-grounded-writing loads instead, and its cases pass 14 of 15. That gap is older than this change.
- **One new rule is not followed.** In `edit-contrast-keeps-both-sides` no condition reported that "retention remains a challenge" stays vague after the edit, which the anti-slop residuals list now asks for.
- **One check was corrected after the run.** In `edit-punchline-keeps-every-except` the stranded-auxiliary check also flagged ordinary ellipsis inside a longer sentence ("came up cleanly, but the replica didn't."). Narrowed to a short clause standing alone, the case passes 3 of 3 with skills, 3 of 3 with the placebo and 1 of 3 without skills, and the totals become 77%, 32% and 39%. The pre-registered answers above use the numbers as run (`report-as-run.md` in the results folder).

## Limits

- **The checks and the skills were written by the same team.** Some checks were corrected after reading outputs. Each fix was justified in the check's note and applied to every condition. The fixes still lean toward the outputs we read most, which were ours. Treat the judge columns as the less biased signal.
- **Results come from one model.** In a run that silently fell back to gemini-3.8-flash, the same skills passed 21 of 36 runs, against 29 of 36 for gpt-6-sol.
- **The current version was not benchmarked as a whole.** The numbers above come from the commit before the last two edits:
  - generic routing descriptions;
  - six passages reworded away from source wording.

  A partial clean run of those edits scored slightly lower (tuned 78 vs 81 of 86 matched runs). That gap is within run-to-run noise (p≈0.06).
- **Three repeats per case.** Differences of one run per case are noise.

## Unit tests

All test suites pass:

| Suite | Tests | What it covers |
|---|---|---|
| `tests/_meta` | 92 | Every skill follows the shared contract: frontmatter, version, 500-line limit, `eval.md`, `agents/openai.yaml`, links, no source names, no benchmark scenarios in skill text, no case-prompt wording in descriptions |
| `tests/anti-slop-editing` | 99 | `slop_scan.py` and `fact_diff.py`: numbers, dates, negations, names, derived figures |
| `tests/author-voice` | 30 | `voice_stats.py` |
| `tests/evidence-grounded-writing` | 77 | `claim_ledger.py` |
| `tests/project-report` | 32 | `inventory.py`, `build_report.py` |
| `tests/evals` | 343 | Grader, statistics gate, run harness, duplication and similarity tools |
| `tests/installer` | 21 | The npx installer, run in a temporary HOME |

## Reproduce

```bash
python3 evals/grade.py --validate
python3 evals/run.py --host omp --repeat 3 --jobs 6 --judge omp --condition both --competitors \
  --variant iso=<old commit> --judge-pairs skill:baseline,skill:variant-iso,skill:competitor --out evals/results/<name>
for t in tests/*/; do uv run --with pytest --with pyyaml python -m pytest "$t" -q; done
```

See [evals/README.md](../evals/README.md) for hosts (Codex, Claude Code, omp), case format and the gate.
