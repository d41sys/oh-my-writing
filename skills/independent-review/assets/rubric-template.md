Load when: writing or filling a rubric for subjective criteria such as clarity, tone fit, persuasiveness, or design quality.

# Rubric template

Copy this file, fill the fields, and attach it to the reviewer prompt. Keep it short: a rubric nobody can hold in mind is not used. See `references/calibration.md` for how to anchor and test it.

## Header

- Document type and reader: `<genre; who reads; what they decide or do>`
- Calibration status: `calibrated | partly calibrated | none`
  - `calibrated`: at least one human-chosen good and one human-chosen bad example were scored and the rubric separated them.
  - `partly calibrated`: examples exist but fewer than planned, or only one genre.
  - `none`: no human-chosen examples. Scores below are opinions and must be reported that way.
- Anchor examples (human-chosen, same genre):
  - Good: `<path or citation>`, `<path or citation>`
  - Bad: `<path or citation>`, `<path or citation>`
- Who chose the examples, and what they were chosen for: `<name/role; one line>`

## Part A: Checks (objective, pass or fail with evidence)

Use for anything that can be verified. Do not score these.

| # | Check | Pass/fail | Evidence (quote, location, source) |
|---|---|---|---|
| A1 | Every number matches its source | | |
| A2 | Every term keeps one meaning | | |
| A3 | Required elements for this genre are present | | |
| A4 | `<add only checks that apply>` | | |

## Part B: Criteria (subjective, scored with a reason)

Use 2 to 7 criteria. Describe what a reader notices at each level; avoid empty adjectives like "good" or "engaging". Weights are optional; if used, they sum to 1.0 and are written down before scoring.

| Criterion | Weight | Level 1 (reader fails) | Level 3 (reader copes) | Level 5 (reader is served) |
|---|---|---|---|---|
| `<e.g. Main point is findable>` | `<0.3>` | `<reader cannot say what it is about>` | `<reader finds it after the second section>` | `<reader can say it after the first screen>` |
| `<e.g. Order matches reader need>` | | | | |
| `<e.g. Tone fits the reader>` | | | | |

Scoring rules:

1. Every score gets a one-sentence reason with a quote or location.
2. Any score at 2 or below is a critical or major finding; say which.
3. A 5 needs a quote showing why. Do not give a 5 for absence of problems alone.
4. Do not reward length, polish, or effort; judge the page.
5. Do not penalize a missing feature the brief did not ask for.

## Part C: Gap note (required when two reviewers or two runs differ)

- Criterion: `<which>`
- Scores: `<reviewer or run 1: x; reviewer or run 2: y>`
- Why they differ: `<different reading of the wording / different evidence quoted / different reader assumed / unclear anchor>`
- Action: `<reword the level descriptions / add an anchor example / ask a human to decide / leave as an open disagreement>`

## Part D: Holistic read

One short paragraph: would the stated reader, reading this, get what they came for? Name the weakest criterion and the one thing worth keeping. Do not average Part B into a single number unless the user asks; a total hides which criterion failed.

## Reporting line

`Rubric: <n> criteria, calibration <status>; scores are judgments by <reviewer family or "unknown">, not measurements.`
