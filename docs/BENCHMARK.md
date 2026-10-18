# Benchmark and tests

## Summary

On realistic writing tasks, an agent with these skills passed **89%** of tuned runs; the same agent with no skills passed **42%**. Against seven public writing-skill packs, it passed more runs than each of them. A blind model judge preferred our output to every pack except Humanizer. Against no skills at all, the judge split close to even. So the skills make output reliably more faithful to the material, but not clearly better-sounding.

## Setup

- **Host and model:** omp with gpt-6-sol. Judges also use gpt-6-sol. Results directory `v-final2-omp`.
- **Cases:** 59 tasks across all ten skills, each run 3 times (177 runs per condition). Each case has:
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
