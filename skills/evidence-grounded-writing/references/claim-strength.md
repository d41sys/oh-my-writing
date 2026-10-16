Load when: rewriting a partial claim, judging causal or comparative wording, deciding how strongly to state a result, or placing uncertainty.

# Claim strength

A claim has two parts: what it says happens, and how widely. Evidence supports a certain width. Writing too wide is overclaiming; writing narrower than the evidence is sandbagging. Both mislead.

## 1. The four levels

Ordered by how much generalisation the sentence asserts.

| Level | What the sentence asserts | Evidence that earns it | Typical wording |
| --- | --- | --- | --- |
| Existence | It happened or is possible, at least once | One verified case, a working demo, one reproduced observation | "We observed...", "In one run...", "It is possible to..." |
| Narrow scope | It holds under stated conditions | A result in a named setting (data, version, population, period, configuration) | "On dataset X with setting Y...", "In the 2023 cohort..." |
| Systematic | It tends to hold across a range of conditions | Repeated across varied settings, with spread reported; not one lucky setting | "Across five datasets...", "On average...", "In most of the 40 cases..." |
| Guarantee | It always holds, for all inputs or everyone | A proof, an exhaustive check, or a mechanism that rules out exceptions | "For every input of type T...", "cannot exceed..." |

How to choose:

1. Write down what the evidence actually covers: how many cases, which conditions, which period, how much variation.
2. Choose the highest level the evidence covers. If it covers one setting, the claim is narrow scope, even if the author believes it is general.
3. State the scope in the sentence itself (the setting, the count), not in a vague hedge.
4. If the author wants a higher level, name the missing evidence ("a second dataset", "a longer period") instead of softening with "may".

Hedges versus levels:

| Hedge version | Level version |
| --- | --- |
| "This may possibly improve speed in some cases." | "Median latency fell 20% on the read-heavy benchmark; write-heavy loads were not tested." |
| "Results suggest the method might generalise." | "The method beat the baseline on all three tested datasets; no other datasets were tried." |
| "It could be argued that users prefer X." | "14 of 20 interviewed users chose X." |

A hedge is right when the uncertainty is real and about the effect itself (for example, a confidence interval that spans zero). It is wrong when it hides that the author does not know what the evidence covers.

Stacked hedges collapse to one: "may possibly be able to reduce" becomes "may reduce". Keep the single hedge that carries the real uncertainty (a preclinical result, an interval that spans zero); never collapse to none when the evidence is that weak.

Guarantee claims deserve extra suspicion. Words like "always", "never", "all", "guarantees", "proven" ask for a proof or exhaustive check. A benchmark, however large, is a systematic claim. If you cannot find the proof, downgrade the wording and keep the number.

## 2. Claim types and the verbs that fit

Classify before choosing verbs.

| Type | Says | Safe verbs | Needs |
| --- | --- | --- | --- |
| Descriptive | What was observed | observed, measured, recorded, counted | A defined sample and a stated source |
| Associational | Two things move together | is associated with, co-occurs with, is higher among | Both measured; the direction and size stated |
| Predictive | One thing forecasts another | predicts, forecasts (with error) | Out-of-sample test, not only fit on known data |
| Causal | One thing produces another | causes, leads to, reduces, drives | A design that isolates the cause (see section 3) |
| Mechanistic | How it works inside | works by, through, via | Direct process evidence, not only an effect |

Rules of thumb:

- Pick the verb for the type the evidence supports, not the type the author hopes for.
- A good prediction score does not show a cause. An effect after an intervention does not show the proposed pathway.
- A proposal or hypothesis is labeled as such. Do not present it in the grammar of a finding.
- Match the evidence to the claim type: causal needs a design that isolates the part (ablation, randomisation, a comparison group); generalisation needs varied settings, not one; improvement needs a fair baseline; descriptive needs a defined sample; scoping needs stated bounds. One experiment rarely covers two of these.
- A plausible mechanism says how an effect could happen; it is not a measurement that it does. Use a mechanism in place of a slogan only if the source describes it; never invent one to make a sentence sound explained.
- Keep the statement class: a measured fact, an estimate, a calculation from stated inputs, a forecast under assumptions, an opinion and a recommendation are different things. Do not rewrite an estimate as a fact, a scenario as a prediction, an interview theme as a prevalence, or a recommendation as an evidence claim.
- The kind of evaluation sets a ceiling: real ground truth allows the full claim; a synthetic proxy allows claims about proxy consistency only; a simulation needs "in simulation"; human judgments need an agreement statistic. Scores divided by the model's own maximum, or references built from model output, do not count as ground truth; show raw and normalised scores side by side and treat a score near 100% from self-normalisation as a flag.
- Observation first, interpretation after: say what was seen, in what population, over what period, then what it might mean.

## 3. Causal versus correlational wording

Ask these in order. Each "no" lowers the wording by a step.

1. Was the supposed cause actually varied (by the author, or by an experiment) while other things were held steady or balanced?
2. Did the cause come before the effect?
3. Are the main alternative explanations ruled out or addressed (other changes at the same time, who chose to take part, natural recovery or drift, regression to the mean, measurement change)?
4. Does the effect follow when the cause is removed or dose changes?
5. If several things changed together (a bundle), were they separated?

Wording ladder, strongest to weakest:

- "X causes Y" / "X reduced Y": controlled design, alternatives handled.
- "X appears to reduce Y; we could not rule out Z": decent design with a named gap.
- "Y was lower after X": before and after, no control.
- "Y is lower among people who do X": cross-section, selection unaddressed.
- "X and Y moved together": co-movement only.

Special cases:

- Technology and product changes: if two improvements shipped in the same release, claim the release, not one part. To credit one part, show the part removed or switched off.
- Experiments are not automatic proof: if many participants dropped out, the groups were not comparable, or the treatment was bundled, say so and soften.
- Observational work can support causal wording when the design and assumptions are stated and checked. Say which design, and what would break it.
- Not significant is not "no effect". Write "no difference was detected (interval X to Y)" and say whether the study was able to detect an effect of the size that matters.
- A single p-value is not the probability the claim is true; it measures how surprising the data are under a null model. Report effect size and interval next to it.
- Post-hoc patterns are exploratory. Label them so; do not present them as pre-planned tests.
- Equivalence needs its own test. "No meaningful difference" rests on a stated margin and an equivalence or non-inferiority test, not on a p-value above 0.05.
- Inference traps worth a quick check, each with the fix in brackets:
  - the outcome may drive the exposure (reverse direction) [say the design cannot tell the direction];
  - improvement after an intervention may be recovery, drift or regression to the mean [name the rival, or add a comparison group];
  - several things changed together (hardware, load, release) [credit the bundle, not one part];
  - a group-level pattern is not a statement about one person [keep the claim at group level];
  - a handful of cases or one anecdote is not a rate [report the count; a single safety signal is still worth reporting as a signal];
  - "no harm found" is not "safe" unless the search could have found it [say what could and could not be detected];
  - many comparisons make chance hits likely: with k independent tests at the 5% level the chance of at least one false positive is 1 - 0.95^k, about 64% for k = 20 [say how many were run, label unplanned ones exploratory];
  - only the successful runs, a truncated axis or a favourable subset are shown [report the rest, or say what was left out].

## 4. Comparison validity

"Better", "faster", "cheaper", "beats", "outperforms" are comparisons. Check five things:

1. **Same baseline.** Is the thing compared against current and fairly set up? A weak, untuned or outdated baseline makes any result look good.
2. **Same metric.** Same definition, unit and direction (higher is better, or lower?). If the author's metric differs from the source's, say so.
3. **Same conditions.** Same data, hardware, time window, population, tuning effort, budget. If conditions differ, state the difference; matching everything is often impossible and is not required, but hiding the gap is.
4. **Same time.** Prices, versions, rankings and benchmarks age. Give the date or version of both sides.
5. **Same amount of evidence.** One run against a ten-run average is not a fair comparison. Report spread or number of runs where the gap is small.

Also:

- Report where the thing does worse, ties, or was not tested, in proportion to how much it matters to the reader. A promotional text may emphasize strengths, but it must not hide a failure that affects the reader's decision.
- Where the gain is small, show raw numbers next to the relative change so the reader can judge scale.
- Each metric shows one property. A metric for accuracy says nothing about cost or fairness; state which property the claim is about.
- Baseline numbers say where they came from: reproduced by the author, or taken from a paper.
- Report ties and parity as results. When a metric exists in raw and adjusted form, give both; showing only the flattering one is a credibility failure.
- Do not blend figures that use different definitions, windows, currencies or price bases into one number without converting and saying so. Do not average two conflicting measurements into a made-up midpoint.

## 5. Placing uncertainty

- State a limit where it changes what the reader should do or believe, directly beside the claim it limits.
- State it once. If a limit applies to the whole result, put it in one clear place (a limits paragraph or the sentence introducing the result), not on every line.
- Make it specific: what is unknown, why, and in which direction it could move the result. "Results may vary" tells the reader nothing; "we tested one dataset, so the gain on noisier data is unknown" does.
- Keep real uncertainty (an interval, a disagreement between sources) in the text; do not smooth it into confident prose.
- Do not apologise for a solid result. If the evidence is strong, say it plainly.
- Null, unexpected and inconclusive findings stay in, with the prominence they deserve. If two credible sources disagree, report both and the likely reason (conditions, workload, population, period).
- A limit followed straight away by a sweeping superlative ("systems differ, but ours is the best overall") cancels the limit. Keep the claim inside the tested boundary and name where the method degrades or was not tried.
- Do not close with a blanket "more research is needed". Name the specific missing evidence, or say nothing.

## 6. Editing without upgrading

When revising any text, never raise strength unless new evidence is in the ledger. Frequent silent upgrades:

| Source says | Bad edit | Why |
| --- | --- | --- |
| "in 2 of 5 trials" | "in trials" or "often" | count and scope lost |
| "may reduce" | "reduces" | qualifier dropped |
| "no significant difference" | "no difference" | detection limit dropped |
| "associated with" | "leads to" | type changed |
| "we observed" (one run) | "the method achieves" | level raised from existence to systematic |
| "up to 40%" | "40%" | best case presented as typical |
| "among 120 respondents" | "users say" | sample presented as population |
| "not tested on X" | (sentence removed) | limit erased |
| "in mice" / "in vitro" / "in adults over 65" | "in animals" / "in cells" / "in people", or the scope dropped | population or species widened |
| "the cohort showed" | "you should" / "people can" | group result turned into individual advice |
| "no harm was observed in 40 patients" | "safe" | absence of detection written as safety |
| "under these assumptions" / "forecast" | "will" | scenario written as prediction |

If tightening for length, shorten words, not scope. When two edits conflict (shorter versus accurate), accuracy wins.

Concision trap: collapse stacked hedges to one and cut filler around the claim ("it is important to note that", "in the context of"), but keep the scope words (species, population, setting, period), the numbers and the hedge that carries real uncertainty. "may reduce X in mice" stays "may reduce X in mice", not "reduces X". Removing an unsupported claim is an honest edit, but list it in the change list; do not reword a sentence so that the problem merely stops being visible.

## 7. High-stakes domains

For health, legal, financial, safety or security statements:

- Report what the supplied source says and cite it; do not add dosage, legal conclusions, tax or investment guidance, or safety assurances from memory.
- Do not turn group-level findings into advice for an individual ("the cohort showed..." is not "you should...").
- Log `[VERIFY: qualified source for <statement>]` in the ledger and reply when the author wants to publish something that could change someone's health, rights or money; in the reader's text the statement stays attributed to the supplied source and carries no marker.
- Keep jurisdiction and date: laws, guidelines and prices differ by place and expire.
- Required disclaimers stay as the author wrote them.

## 8. Quick rewrite recipes

1. Find the level the evidence earns (section 1).
2. Put scope words in: how many, which condition, which period.
3. Replace the verb with the one that fits the type (section 2).
4. Add the one limit the reader needs, beside the claim.
5. If the result still reads too weak to publish, the answer is more evidence, not stronger words: say in the text what the evidence does not show, and list the missing evidence as `[ASK AUTHOR: ...]` in the reply.
