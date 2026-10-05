# Sentence-Level Style

## Reader expectations
1. Subject and verb close together; no long insertions between them.
2. Topic position (sentence start): old information that links back, and the person or thing the story is about.
3. Stress position (sentence end): the new, important information. "When using attention, accuracy rises by 15%." not "Accuracy rises by 15% when using attention."
4. Context before new material: "To address X, we introduce Y."
5. One unit, one function: a sentence makes one point; a paragraph does one job.
6. Actions in verbs, characters as subjects: "we analyzed", not "we performed an analysis of"; "the system fails", not "failure of the system occurs". Watch zombie nouns (-tion, -ment, -ity, -ance made from verbs and adjectives).
7. Set the stage: say why an equation, table, or result matters before showing it.

## The curse of knowledge
You cannot easily imagine not knowing what you know. Symptoms: undefined lab shorthand (internal condition codes, "cell", "route"), skipped steps, abstractions without an example. Fix: define at first use, give a concrete example before the general case, and test on a reader outside the project. Don't overcorrect into talking down; assume a smart reader who lacks your context.

## Voice and tense
- **Active by default.** Passive is fine in method and setup sentences where the agent does not matter or the object is the topic ("Each state is solved to a fixed horizon"). Never use passive to hide who made a choice.
- **Tense:** past for what we did and observed in this study ("We evaluated five models", "the shortlist condition returned 120 correct answers"); present for what holds and for the paper itself ("The error is concentrated in long-horizon tasks", "Table 2 shows", "Section 4 describes"). Never future tense for the paper ("we will show" → "we show"). Don't switch tense inside a paragraph without a reason.

## Precision
- Replace vague with measured: "performance" → the metric; "improves" → "raises X from a to b"; "large/fast" → the number; "better" → better at what, by how much, why.
- One name per concept across the whole paper, including figure labels and table headers. Elegant variation is a defect.
- Absolutes only when proven: "always", "never", "eliminate", "optimal" (means proven optimal), "significant" (means statistically significant), "first" (means checked). Otherwise give the count: "in all 100 states", "in none of the 400 trials".
- Overloaded words: say "time complexity" or "intricate", not bare "complexity"; "robust" only with the perturbation and the measurement.
- Explain a named component right where you name it.
- Pronouns: replace an ambiguous "this/it/they" with the noun ("These ablations show ..."). No non-referential "this".
- Prefer "is/are/has" to "serves as / stands as / represents / features / boasts".
- Verbs that signal contribution (develop, introduce, characterize, identify) over verbs that signal assembly (combine, modify, extend), only when true.
- No "etc." unless the rest is obvious; no "for various reasons" (give them); no "In this paper" (where else?).
- Formal register: no contractions; "of" over possessive 's for inanimate things.
- Split sentences over about 35–40 words. Don't start consecutive sentences with "This" or "We".

## Concision
After the first full draft, cut about one third of the words. Targets:
- Fillers: actually, very, really, quite, basically, essentially, importantly, it is worth noting that, it should be noted that.
- Clutter: due to the fact that → because; in order to → to; a number of → several; has an effect on → affects; on the basis of → based on.
- Weak verbs: "can be reformulated as" → "is"; "we attempt to approximate" → "we approximate"; "is able to" → "can" or the verb itself.
- Metadiscourse that narrates the paper's layout ("In this section, we will discuss ..."). Keep sentences that tell the reader how the evidence is organized ("We assign each failure to the step where it occurs"): they reduce confusion and are not filler.

## Calibration: confident and honest
- Pick the claim level the evidence supports (existence / systematic / narrow / guarantee) and write it plainly.
- **Hedge words (can, may, might, could, potentially, attempt, seems) are deleted unless the uncertainty is real.** When it is real, state it once, specifically ("on one dataset", "one run per cell"), not with a modal verb.
- Keep claim-defining qualifiers attached to the claim ("in the 80 matched pairs, ..."). A qualifier is part of the claim if removing it makes the claim false or broader than the evidence; keep it and keep it short. Reviewer-required qualifiers always stay.
- Generic caveats ("may not generalize", "should be interpreted with caution") live only in Limitations.
- No self-defence or arguing with an imagined reviewer: "we do not claim", "this is not evidence of", "our goal is merely". State what the paper establishes.
- No drafting or revision history in the manuscript ("unrun pilot", "added in revision", "Neither was run here").
- Quantify instead of quantifier words: "almost entirely" → "57 of 63".

## Scholarship hygiene
- **Explanation vs speculation**: label speculation as such and keep it apart from claims the experiments support.
- **Source of gains**: when several changes are bundled, do not attribute the effect to one of them without an ablation.
- **Mathiness**: equations must clarify; don't add formalism to look rigorous; don't let a formal term silently mean something looser.
- **Language misuse**: no anthropomorphic labels ("understands", "commits", "verifies", "plans internally") for claims about internal processes inferred only from outputs; don't overload established technical terms ("p-value", "significant", "causal"); avoid suitcase words that bundle several meanings. Prefer observable labels: "legal nonoptimal final action", "no parser-accepted action". Established field or product terms used descriptively ("reasoning traces" returned by an API, "planning benchmark") are fine.

## Logic connectives
| Relation | Use | Misuse to avoid |
|---|---|---|
| cause/effect | because, therefore, thus, as a result | "To this end" without a stated goal |
| contrast | however, in contrast, although, yet | "However" with no real opposition |
| addition | also, similarly | "Moreover/Furthermore/Additionally" chains as filler |
| example | for example, such as | "e.g." without comma |
| sequence | first, then, finally | numbering items that have no order |
| summary | thus, in short | paragraph-final restatement of the same paragraph |

Logic lives in the content; connectives only make it visible.

## Grammar myths (do not "fix" these)
Splitting an infinitive, ending a sentence with a preposition, starting a sentence with "And" or "But", singular "they", and first-person "we" are all acceptable in academic English. Correcting them adds stiffness, not quality.
