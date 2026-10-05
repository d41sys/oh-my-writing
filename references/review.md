# Review (used by the external reviewer in Step 4b)

The reviewer is a different model from the writer. It reads the files itself and answers the questions below with evidence from the paper, marking each issue `CRITICAL`, `MAJOR`, or `MINOR`.

## External reviewer prompt
Fill the paths; save to a file and send it as a fresh Codex CLI session (`codex exec`, see SKILL.md Step 4b). Do not add any summary of earlier rounds or fixes.

```
You are a senior area chair reviewing one part of a paper before submission.
Read these files directly:
- Draft to review: <path, e.g. paper/drafts/0_abstract.tex>
- Story card the draft must serve: paper/STORY.md
- Sources of every fact: <results files / existing sections / NARRATIVE_REPORT.md>
- Reviewer history (wording earlier reviewers required), if any: <e.g. paper/PAPER_IMPROVEMENT_LOG.md>; project lessons: paper/WRITING_LESSONS.md if present
- Writing rules for this part: <skill dir>/references/sections.md (section "<name>") and references/review.md

Review the draft for:
1. Faithfulness: any number, claim, scope, or qualifier that differs from the sources, or a pre-specified result that was dropped.
2. Calibration: claims stronger or weaker than the evidence; causal verbs without a design that identifies them; needless hedges or self-defence.
3. Story: does it state the challenge with its reason, the insight, the evidence, and a takeaway that answers the challenge? Would a reviewer be able to write "X is good for Y in the context of Z" after reading it?
4. Clarity: undefined terms, overloaded sentences, jargon a non-specialist ML reviewer cannot decode on first read.
5. Voice: wording that reads as LLM-generated.

Rank issues by how much they would cost with a real reviewer. For each: severity, location (quote), what is wrong, the fix. A well-written part gets "no CRITICAL/MAJOR issues". Do not invent problems; do not propose claims the sources do not support.
End with one line: VERDICT: ready | revise
```

A reply without the VERDICT line counts as `revise`.

## Why papers get rejected
| Dimension | Signals |
|---|---|
| Contribution | targeted failure is trivial; idea well explored; gain predictable; "most of it is known" |
| Clarity | not reproducible; a module/step lacks motivation; messy structure |
| Empirical strength | marginal gain; absolute level weak; results contradict common sense |
| Evaluation completeness | missing ablation, baseline, metric; data too easy; setup differs from prior work |
| Method/design soundness | unrealistic setting; per-case tuning; net benefit negative; disrespect or misrepresentation of prior work |

## Questions
**Contribution**: What does a reader know after this paper that they did not before? Is the failure case meaningful? Is the result non-obvious? Which single contribution type is it?

**Clarity**: Can an expert reproduce it from the paper plus appendix? Is every operational definition (parser, predicate, estimand) stated as the code implements it? Does each module/step have explicit motivation? Are terms and notation stable?

**Empirical strength**: Are differences meaningful against strong, recent baselines under the same protocol? Is uncertainty reported with the right interpretation (no p-value language for non-inferential summaries)?

**Completeness**: One ablation per key design or factor? Standard metrics? Hard enough data? Protocols documented?

**Soundness**: Realistic setting? Does each causal-sounding verb ("lifts", "yields", "determines") have a design that identifies it? Benefits outweigh complexity?

**Skim test**: From title, abstract, Figure 1, and topic sentences alone, can a reader state the central claim and its evidence?

**Story test**: Does every section advance gap → question → insight → evidence → implication? Does the conclusion claim exactly what the evidence establishes?

## How to report a review
- Rank issues by how much they would cost with a reviewer; report the ones that matter, not every rule that could apply.
- A well-written paragraph gets "no issues". Do not invent problems to look thorough; defensible stylistic choices are not defects.
- Each issue: location, what is wrong, why it matters to a reader, the fix.

## Lessons from real review rounds
Patterns that repeatedly cost points in multi-round external reviews. Check each; apply only where the pattern actually appears. If the project has `paper/WRITING_LESSONS.md`, apply its project-specific lessons too.

1. **Defensive prose**: "not a causal effect", "we draw no conclusion about", captions saying what a result is not. Fix: one estimand definition plus Limitations; elsewhere state what the paper establishes.
2. **Mechanism words for output observations**: "verification", "commitment", "the model plans" when only outputs are observed. Fix: observable labels; say where the origin is not identified.
3. **Impossible arithmetic**: a percentage that no integer numerator over the stated denominator can produce. Fix: report numerator/denominator when denominators vary, regenerated from the results file.
4. **Quantifier words instead of counts**: "almost entirely", "most". Fix: the fraction.
5. **Inferential costume on descriptive numbers**: labeling a descriptive diagnostic "p=" or "not distinguishable from noise". Fix: name what was computed; report the observed counts.
6. **Mixed axes in one table**: two different classifications in one column. Fix: a cross-tab.
7. **Operational names that drift from code**: "parseable", "returned" for a specific parser rule. Fix: name the rule exactly; report sensitivity to it.
8. **Causal verbs on bundled interventions**: "X lifts", "yields" when several things changed at once. Fix: verbs that match the design; report the observed counts.
9. **Process leakage**: unrun pilots, credential failures, "added in revision". Fix: delete.
10. **Design ceilings**: single run per cell, narrow novelty. Writing cannot fix them; state once in Limitations and stop rewording.
11. **Reviewer-required qualifiers are not hedges**: before deleting a qualifier in the abstract or a claim, search the review history; if a reviewer asked for it, keep its content (wording may change if meaning, scope, and strength stay identical).
