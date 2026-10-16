Load when: judging subjective quality (clarity, tone, persuasion, design), anchoring a rubric with examples, scoring, comparing two versions, or explaining why two reviewers disagree.

# Calibration, scoring and comparison

Subjective criteria need a reference point. Without one, a score is a mood. With one, it is still a judgment, but you can see what it was measured against. This file covers four jobs: building a rubric, anchoring it, scoring with reasons, and choosing between versions.

## 1. Split checks from criteria

- **Checks** are things that can be verified: a number equals its source, a link resolves, a required section exists, a term keeps one meaning. Record pass or fail with evidence. Never turn them into a 1-to-5 score; a script or a careful reading settles them.
- **Criteria** are things a reader experiences: findable main point, fit of tone, order of ideas, persuasiveness, visual hierarchy. These get scored with reasons.
- If a quality is mostly subjective and the piece is small, skip scoring and use a checklist plus one holistic paragraph. A weighted total hides which criterion failed and gives false precision.

## 2. Write the rubric

1. Choose 2 to 7 criteria for this genre and reader. More than seven and no reviewer holds them in mind.
2. Describe levels by what a reader notices, not by adjectives. "Reader can state the point after the first screen" beats "strong opening".
3. Weights are optional. If you use them, write them before scoring, make them sum to 1.0, and let them follow the genre: for a README, findability and accuracy outweigh originality; for an essay, voice and argument outweigh scannability.
4. State what is out of scope. Do not penalize a missing feature nobody asked for; judge the artifact, not the effort.
5. Critique the text, never the writer. Name the mechanism when something works ("the example comes before the rule, so the rule is easy to read"), not just that it works.

Use the layout in `assets/rubric-template.md`.

## 3. Anchor with human-chosen examples

A criterion is anchored when the reviewer has seen what a good and a bad instance look like for this reader.

1. **A human picks the examples.** Ideal set: three good and three bad texts in the same genre. Minimum useful set: one good and one bad. The person who knows the readers chooses them, and says what each was chosen for.
2. **Never generate anchors yourself and call the rubric calibrated.** Texts you invent to illustrate good and bad share your taste; they confirm it. If no human examples exist, set `calibration: none`, still score if useful, and report the scores as uncalibrated opinion.
3. **Sanity test.** Score the anchors blind (a reviewer who does not know which is which, in shuffled order) with the rubric. If any bad example scores at or above any good example, the rubric is broken. Rewrite the criterion wording, not the examples, and test again. Stop after two rewrites and ask the human; the examples may be the problem. When you later score the real target, show the anchors with their good/bad labels so the scorer can place the target between them.
4. **Match the genre.** Anchors for a technical README do not calibrate a personal essay. Keep one anchor set per genre. A narrow set pushes every text toward one taste; when the anchors are narrow, say so and keep the writer's own samples ahead of them.
5. **Calibration is not validation.** Separating six texts shows the rubric can tell those six apart. It does not prove the rubric measures what readers value, and it does not replace reading the text.
6. **Scorer family.** A score from the same model family that wrote the text is the weakest kind of evidence. Prefer a different family; when impossible, say the score is same-family. A same-family or self-score may rank which fixes to try first; it never says the text is ready.
7. **Overrides are a signal.** If the author keeps overriding the calibrated scores, the rubric or the anchors are wrong. Revise them and re-run the sanity test; do not nudge individual scores run by run.

## 4. Score with reasons

Per criterion: score, a quote or location, one sentence on the reader consequence, and, if below the top of the scale, the smallest change that would raise it. Rules that keep scores honest:

- A low score without a quote is rejected in triage.
- A top score needs a quote showing why, not just the absence of problems.
- Hedged confirmations ("seems fine", "probably works") are not evidence; a claim about facts needs a source, a claim about reading needs a quote.
- When there is no gap at all, ask once: "what would annoy the stated reader here?" A perfect sheet is rare; if still nothing, accept it and say so.
- Do not convert scores into a verdict mechanically. The verdict follows from findings by severity (see [triage](triage.md)), with scores as supporting evidence. Scores are ordinal: a 4 is not twice a 2, so averages and weighted totals hide which criterion failed.
- With anchors, end the scoring with a short anchor comparison: which anchors the target falls short of or beats, on which criteria, and why. A bare number is not a result.

## 5. When reviewers disagree

Do not average. Averaging a 2 and a 5 produces a 3.5 that no reader would experience.

1. Line up the two reviews by criterion.
2. For each gap of two or more points on a five-point scale, or a difference of one severity level, find the cause:
   - Different reading of the criterion wording: reword the level descriptions.
   - Different evidence: one quoted a passage the other missed; check which is right.
   - Different reader assumed: restate the reader brief; if the brief is silent, ask the human.
   - Real taste difference: record it as an open disagreement and let the author decide.
3. Write the cause in the gap note (`assets/rubric-template.md`, Part C): reviewers, criterion, why, what you did.
4. If many gaps cluster on one criterion, the criterion is vague; tighten it before more rounds.
5. A finding raised by one reviewer only is not weaker for that; check it against the text.
6. Shared blind spots are possible even across reviewers. For high-stakes work add a human spot-check of the part the reviewers agreed was fine.

## 6. Blind pairwise comparison (choosing between versions)

Use when the question is "which version should we keep", for example two openings, two drafts, or old versus revised.

1. **Hide origin.** Label the versions X and Y. Remove file names, version numbers, tracked changes, authors, dates, and anything that shows which is new or which came from a model.
2. **Randomize order.** Decide which comes first by coin flip or a script, not by habit. Models and people favor the first or the longer version more often than they admit.
3. **Give the reviewer the reader brief and the rubric, not the history.** Ask for per-criterion preference with a quote from each version, then an overall preference and the main reason. Allow "no meaningful difference".
4. **Swap and repeat in a new session** if cost allows. If the preference flips with order, the difference is small or the reviewer is order-sensitive; report a tie.
5. **Check the reasons.** A reason that cites length or polish instead of reader effect is weak. A reason that cites an unsupported claim in one version is strong.
6. **Unblind afterwards** and look at why the winner won: clearer order, fewer unsupported claims, better fit to the reader. Record that; it is how the next draft improves.
7. **Do not let blind preference override facts.** A smoother version that dropped a qualifier or changed a number loses regardless.
8. Blind comparison reduces origin and prestige bias; it does not remove reviewer variance. A single comparison is one opinion.

## 7. Depth and cost

- Light: no rubric, one fresh-reader test, qualitative notes.
- Standard: rubric with 3 to 5 criteria, calibration `none` allowed if reported, one independent reviewer.
- High: anchors chosen by a human, sanity test, two reviewers from different families, written gap notes, human sign-off.
- Track what you spent: sessions, rough tokens or minutes, human time. If the gain from the last round was one nit, the depth was too high.
- Review when the artifact changes, not on a timer.

## 8. Common failure modes

| Failure | Cause | Remedy |
|---|---|---|
| Everything scores 4 or 5 | Vague level wording; same-family scorer | Rewrite levels as reader observations; use a different family |
| Bad example outscores good example | Rubric measures polish, not reader value | Reword criteria; ask the human why the good one is good |
| Reviewer favors one version regardless of content | Order or length bias | Randomize, swap, check reasons |
| Scores drift between rounds | Criterion wording interpreted loosely | Anchor with examples, quote evidence |
| Reviewer invents problems | Prompt demanded findings | Allow "no critical or major findings" |
| Reviewer approves everything | Prompt too friendly or leading | Remove praise and verdict hints; ask for the strongest rejection case |
