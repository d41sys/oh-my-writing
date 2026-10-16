---
name: independent-review
description: Reviews a finished or near-finished draft through a reader or reviewer who does not share the writer's context, so the verdict is not contaminated by what the writer meant. Covers fresh-reader tests, independent reviewer prompts, rubric calibration against human-chosen examples, blind pairwise comparison of two versions, finding triage by reader impact, and stop rules. Use when the user asks to review, critique, test or sanity-check a draft, wants a fresh pair of eyes or a second opinion, asks whether a reader will understand it, wants to choose between two versions, or asks you to grade your own writing.
metadata:
  version: "1.0"
  skill-author: d41sys
---

# Independent Review

A writer cannot be the final judge of its own prose: it fills every gap from memory of what it meant. This skill sets up a review where the judge sees only what a real reader would see, then turns the judge's findings into accepted fixes, reasoned rejections, and open questions for the author. It does not rewrite the draft; it decides what is worth changing and when to stop.

## When to use

- A draft is essentially complete and needs a check before it goes out.
- The user asks "does this make sense to someone new?", "review this", "second opinion", "which version is better?", or "score this".
- You (the model) just wrote or edited the text and are about to call it good.
- A reviewer's comments arrived (human or model) and need sorting into do / skip / ask.

Not for: detecting or removing machine-sounding patterns (use `anti-slop-editing`); building a voice profile (`author-voice`); checking claims against sources line by line (`evidence-grounded-writing`); writing the first draft (`structured-drafting`). If one of those is unavailable, apply its checks from this skill's `eval.md` instead.

## Inputs

Read or collect:

- The artifact itself, as text or a file path.
- Reader brief: who reads it, what they already know, why they open it, what they must do or decide afterwards. This is a fact about the reader, not the writer's hopes.
- Constraints a real reader or venue imposes: length, format, house style, deadline for a decision.
- Source material the artifact must agree with (data, notes, a spec), when faithfulness matters. Sources are artifacts too; hand them over as files, not as your summary.
- Optional: a rubric, and good/bad example texts the human picked.

Ask at most three questions, and only if the answer changes the review: who the reader is (if the draft does not show it), how high the stakes are, whether a different model or session is available. Otherwise proceed and state the assumption.

## Workflow

1. **Set depth by stakes.** Pick one and say which:
   - *Light* (internal note, chat message, low risk): one fresh-reader test, one round.
   - *Standard* (published post, report, README, application): fresh-reader test plus one independent review, up to two rounds.
   - *High* (decision memo, submission, legal/medical/financial exposure, hard to retract): standard plus a second reviewer from another model family, calibrated rubric, and a named human or specialist sign-off. A reader-style review does not verify technical correctness; keep that check separate.
2. **Build the review packet.** Include: the artifact, the reader brief, the constraints, the sources if relevant, the rubric if any. Exclude: the writer's intent or thesis, what the writer hopes the reader will conclude, the drafting conversation, earlier versions, what was fixed or changed, the requested verdict, and praise or warnings about weak spots. Test: could a stranger who found this document on the web be given exactly this packet? If something in it only the writer would know, remove it or put it in the document where a reader would find it. Write the packet's reader brief in plain facts; see the placeholders in [reviewer prompt](assets/reviewer-prompt.md).
3. **Get a fresh context.** Start a new session, subagent, or process for every round. Prefer a different model family from the writer's; the biggest gain is from one reviewer to two. Options:
   - Claude Code: a subagent through the Task tool with the packet as its whole prompt; for a different family, call a locally installed other CLI if the user has one.
   - Codex: `codex exec --ephemeral -s read-only -` with the prompt on stdin, so the session starts blank and cannot edit files. Check `codex exec --help` for flags in your version.
   - omp: a task subagent whose only input is the packet; read-only agent type if offered.
   - Any other host: a new chat or process with no shared history.
   If no fresh context exists, write `Independent review: not run` and the reason. You may still run the checks in `eval.md` as a self-check, but label it as a self-check, never as a review, and do not cite it as evidence that the draft is good.
4. **Run the fresh-reader test** (always, unless the user declined). Send [fresh-reader prompt](assets/fresh-reader-prompt.md). The reader restates the main point, lists where it stalled and what the text assumes, and says what it would ask next. Before reading the reply, write down your own expected main point and expected reader questions from the brief, so comparison is honest. Then compare. Classify each stall as a text defect, an audience boundary (the brief says the reader already knows this), or a reader limitation. Fix only text defects.
5. **Run the independent review** (Standard and High). Send [reviewer prompt](assets/reviewer-prompt.md) with the rubric if you have one. For subjective criteria, calibrate first; see [calibration](references/calibration.md). Run any deterministic checks (numbers match sources, links resolve, terms stay consistent) as plain pass/fail with evidence, not as scores.
6. **Compare two versions** when the question is "which is better". Use the blind pairwise procedure in [calibration](references/calibration.md): anonymous labels, random order, swap and repeat, reasons before verdict, unblind only afterwards.
7. **Triage every finding** as accept, reject (one-line, evidence-based reason), or needs author. Severity comes from reader impact, not reviewer tone. Full procedure and the severity table are in [triage](references/triage.md). A finding that would add a claim, number, quote, or example the material does not support is rejected as written; turn it into `[ASK AUTHOR: ...]` if the gap is real.
8. **Apply accepted fixes** as the smallest edits that remove the defect, keeping the author's voice, claims, qualifiers and numbers. If a genre skill is available, hand the fix list to it.
9. **Round two (Standard and High, only if a critical or major finding was accepted).** New session, new reviewer, same packet shape with the revised artifact only. Do not say what changed or what the first round found. Afterwards you compare the two finding lists yourself and check the diff for drift: small softenings that add up to a changed claim.
10. **Stop and report.** Stop when no accepted critical or major findings remain, when the second round is done, or when what remains needs evidence you do not have. Two rounds is the default cap; extra rounds need the user's say-so. Report what remains, honestly, instead of continuing until the reviewer goes quiet.

## Rules

- **The writer does not give the final verdict on its own text.** Reason: the writer's memory completes sentences the page does not. Exception: Light-depth chat messages can ship on a labelled self-check.
- **Give the reviewer the artifact and what a real reader would have, nothing else.** Reason: any statement of intent, history, or desired outcome pulls the judgment toward it. Exception: facts the reviewer needs to do the job (audience, length limit, venue rules, the sources to check against) are brief, not intent, and belong in the packet.
- **Never say what was fixed or changed.** Reason: it invites the reviewer to check the fix instead of reading the text. Exception: a separate verification job ("is this quoted passage still present in this text?") may carry the reviewer's own earlier words verbatim, but it is labelled verification and never counts as a fresh review.
- **Ask open questions, not leading ones.** "What is the main point?" not "Is the intro compelling?" or "Isn't this clear?". Reason: leading questions coach a favourable answer.
- **A new session for every round, and a different model family when possible.** Reason: a reused session anchors on its own earlier judgments; same-family review shares blind spots. Exception: none for the session; if only one family exists, say so in the report.
- **Audience prerequisites are not defects.** If the brief says the reader knows X and the reader stalls on X, the audience is wrong, not the text. If the brief does not say, treat the stall as a defect.
- **Anchor every finding in a quote and a reader consequence.** Reason: findings without location or impact cannot be triaged. Exception: whole-document findings (structure, missing section) name the section instead.
- **A clean result is a valid result.** A reviewer who finds nothing important says so; you do not hunt for something to change. Empty feedback means no findings were raised in that review, not that the text is proven correct.
- **Reviewer fixes are suggestions.** Taste-only findings are nits and are skipped when a real author sample or the user's stated style disagrees. Reason: a real author sample outranks a generic reviewer preference.
- **Never loop "edit, re-review, repeat until clean".** Reason: the editor learns to please the reviewer, and the text drifts. Re-run only to confirm a specific accepted finding is gone, in a new session.
- **Do not average disagreements away.** When two reviewers differ on severity or score, find the cause (different reading of the criterion, different evidence, different reader assumed) and record it. Reason: the disagreement is usually the finding.
- **Match cost to stakes.** Each round costs time, tokens and human attention; report the number of sessions used. Exception: High depth justifies the extra reviewer.
- **Reader review does not replace specialists.** A smooth read says nothing about whether a proof, number, medical or legal statement is right. Route those to a domain check or a human.
- **Languages.** Review in the language of the document. Lexical pattern lists from English do not transfer; structure, evidence and clarity checks do.

## Output

Return a short review report. Do not paste the whole reviewer reply unless asked.

```
Independent review: run | not run (<reason>)
Depth: light | standard | high    Rounds: <n>    Reviewer sessions: <n> (family: <known/unknown>)
Fresh-reader test: main point restated: matches brief | partly | misses
  Stalls: <n text defects / n audience boundary / n reader limitation>
  Next question the reader asked: <quote>
Reviewer verdict (verbatim line): <ready | revise>

Findings
| # | Severity | Location | Reader impact (one line) | Decision | Reason |
Accepted fixes applied: <list, one line each>
Needs author: <list of [ASK AUTHOR] items>
Remaining after stop: <what is unresolved and why>
Not covered: <what this review cannot tell, e.g. technical correctness>
```

If nothing is wrong, the report is two lines: the run line and "no accepted findings".

## Reference files

| File | Load when |
|---|---|
| [assets/reviewer-prompt.md](assets/reviewer-prompt.md) | Sending a draft to an independent reviewer |
| [assets/fresh-reader-prompt.md](assets/fresh-reader-prompt.md) | Testing whether a cold reader gets the main point |
| [assets/rubric-template.md](assets/rubric-template.md) | Writing or filling a rubric for subjective criteria |
| [references/calibration.md](references/calibration.md) | Anchoring a rubric with examples, scoring, comparing two versions, explaining reviewer gaps |
| [references/triage.md](references/triage.md) | Sorting findings, defining severity, choosing fixes, deciding when to stop |

## Examples

Leaking packet and clean packet for the same draft.

Leaking: "Review this launch post. I wanted it to feel confident but not salesy, and I already fixed the weak opening. Isn't the pricing section clear now?"

Clean: "Artifact: launch-post.md. Reader: existing customers of a note-taking app who read the changelog; they know the product, not the new pricing; they will decide this week whether to upgrade. Constraint: under 600 words. Report as instructed."

Fresh-reader result and classification:

- Reader restated: "The app is adding a paid tier with sync." Brief expected: "Sync is free for existing users until March." Result: partly. The deadline is missing from the reader's version, so the date sentence is buried: text defect, major.
- Reader stalled on "workspace seats". Brief says customers know the product and this term is on the current pricing page: audience boundary, no change.
