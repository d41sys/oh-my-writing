# Learning from an Example Paper

Goal: understand how the authors turned an idea into a convincing paper, so we can see what our paper does, does not say, or does not have. Read the full paper including the appendix list. Write `paper/EXEMPLAR_NOTES.md` with the sections below, in this order. Sentences and wording come last.

## 1. The question and why it was open
- The one research question, in one sentence.
- What prior evidence existed, and exactly why it could not answer the question (the flaw or gap in prior designs, not "little work exists").
- Why the question matters to the field (who changes what they do if the answer is X).

## 2. The design lever
- The single design decision that makes the question answerable (e.g. counterfactual images + neutral prompts separate "the image causes the error" from "the prompt causes it").
- Which simpler design they could have used and why it would not isolate the effect.
- What is held fixed and what is varied.

## 3. The argument chain
A table, in the paper's order:

| Step | Experiment / analysis | Role | Skeptic question it closes | Claim it licenses (level) |
|---|---|---|---|---|

Roles to look for: **precondition / sanity check** (the model has the needed knowledge or ability), **main measurement**, **discriminating test** (separates the main explanation from the obvious alternative), **manipulation / ablation** (change one factor, see the effect), **new metric** (turns a vague notion into a number that separates explanations), **breadth** (many domains to block "it's one quirky dataset"), **robustness** (prompts, models, resolutions), **mechanism probe** (what drives it), **boundary** (where it stops holding). Note which roles are missing.

## 4. How the benchmark or data was built
- Generation pipeline (manual / automated / model-assisted) and why.
- Quality control (human review, rejection rules) and contamination / memorization controls.
- How items are organized so comparisons are clean (factorial design, matched pairs, difficulty levels).
- What is released.

## 5. Claims versus evidence
For each headline claim: the evidence, the claim level it actually supports (existence / systematic / narrow / guarantee), and any place the paper's wording goes beyond it. This section protects us from copying overreach.

## 6. Story and structure
- Opening → Challenge → Action → Resolution, one line each.
- How the sections map to the argument chain (findings as section titles? sanity check first?).
- Figure 1: what it shows and why it convinces in five seconds.
- Running example used throughout.

## 7. Writing moves (brief)
Abstract sentence roles, how the gap is phrased, how contributions are listed, where limitations go. At most ten lines.

## 8. Transfer to our paper
Two tables.

**Research design transfer**

| Their role (from §3) | Their version | Our equivalent | Status |
|---|---|---|---|

Status is one of: **have and say it** / **have but don't say it** (a writing fix: surface it) / **lack it** (an experiment gap: list for the author; writing cannot fix it) / **not applicable** (say why).

**Writing transfer**

| Move | Borrow / adapt / don't borrow | Why |
|---|---|---|

Never borrow claim strength, title assertiveness, or hedging level; those follow our evidence. Never copy sentences or invented terms.
