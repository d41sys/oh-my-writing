---
name: independent-review
description: Reviews a finished or near-finished draft through a reader or reviewer who does not share the writer's context, so the verdict is not contaminated by what the writer meant. Covers fresh-reader tests, independent reviewer prompts, rubric calibration against human-chosen examples, blind pairwise comparison of two versions, finding triage by reader impact, point-by-point responses to reviewer comments, and stop rules. Use when the user asks to review, critique, test or sanity-check a draft, wants a fresh pair of eyes or a second opinion, asks whether a reader will understand it, wants to choose between two versions, has reviewer or editor comments to sort or answer, or asks you to grade your own writing.
license: MIT
metadata:
  version: "1.8"
  skill-author: d41sys
---

# Independent Review

A writer cannot be the final judge of its own prose: it fills every gap from memory of what it meant. This skill sets up a review where the judge sees only what a real reader would see, then turns the judge's findings into accepted fixes, reasoned rejections, and open questions for the author. It does not rewrite the draft; it decides what is worth changing and when to stop.

## When to use

- A draft is essentially complete and needs a check before it goes out.
- The user asks "does this make sense to someone new?", "review this", "audit this draft as a reader", "second opinion", "which version is better?", or "score this". ("Audit" aimed at AI phrasing is `anti-slop-editing`; aimed at claims, numbers or citations it is `evidence-grounded-writing`.)
- You (the model) just wrote or edited the text and are about to call it good.
- A reviewer's comments arrived (human or model) and need sorting into do / skip / ask.
- A response letter, rebuttal or point-by-point reply to reviewer, editor or client comments has to be drafted or checked; see [responding to reviews](references/responding-to-reviews.md). This skill owns the "rebuttal" and "response to reviewers" requests; for an ML paper, `academic-writing` (if installed) handles the manuscript revision through its own revision guide.

Not for: detecting or removing machine-sounding patterns (use `anti-slop-editing`); building a voice profile (`author-voice`); checking claims, numbers and citations against sources line by line (`evidence-grounded-writing`); writing the first draft (`structured-drafting`); editing an ML paper's sections once comments are accepted (use `academic-writing` if installed; otherwise `structured-drafting` for structure plus `evidence-grounded-writing` for claims). If one of those is unavailable, apply its checks from this skill's `eval.md` instead.

## Inputs

Read or collect:

- The artifact itself, as text or a file path.
- Reader brief: who reads it, what they already know, why they open it, what they must do or decide afterwards. This is a fact about the reader, not the writer's hopes.
- Constraints a real reader or venue imposes: length, format, house style, deadline for a decision.
- Source material the artifact must agree with (data, notes, a spec), when faithfulness matters. Sources are artifacts too; hand them over as files, not as your summary.
- Optional: a rubric, and good/bad example texts the human picked.

Ask at most three questions, fewer for short tasks, and only if the answer changes the review: who the reader is (if the draft does not show it), how high the stakes are, whether a different model or session is available and whether the text may be sent to it. In non-interactive runs proceed on stated assumptions; for the sending question, assume "no" and say so.

## Workflow

1. **Set depth by stakes.** Pick one and say which:
   - *Light* (internal note, chat message, low risk): one fresh-reader test, one round.
   - *Standard* (published post, report, README, application): fresh-reader test plus one independent review, up to two rounds.
   - *High* (decision memo, submission, legal/medical/financial exposure, hard to retract): standard plus a second reviewer from another model family, calibrated rubric, and a named human or specialist sign-off. A reader-style review does not verify technical correctness; keep that check separate.
2. **Build the review packet.** Include: the artifact, the reader brief, the constraints, the sources if relevant, the rubric if any, and today's date when the text carries dates without a year. Add what the reader needs to be able to act: three to five questions a person in that role would ask before deciding (for a funding call: what it costs, what it commits us to, by when, how success is judged), taken from the reader's job, not from the draft's known gaps. Exclude: the writer's intent or thesis, what the writer hopes the reader will conclude, the drafting conversation, earlier versions, what was fixed or changed, the requested verdict, the writer's worries, and praise or warnings about weak spots. Test: could a stranger who found this document on the web be given exactly this packet? If something in it only the writer would know, remove it or put it in the document where a reader would find it. Placeholders are in [reviewer prompt](assets/reviewer-prompt.md).
3. **Get a fresh context.** First check that the text may leave this session: confidential, unpublished-under-review, client or personal material must not go to another vendor's model or a hosted tool unless the owner has agreed; if that is unclear, ask, or treat it as "no fresh context". Then start a new session, subagent, or process for every round. Prefer a different model family from the writer's; the biggest gain is from one reviewer to two. The host commands below are untested in this skill; check flags against the installed version. Options:
   - Claude Code: a subagent through the Task tool with the packet as its whole prompt; for a different family, call a locally installed other CLI if the user has one.
   - Codex: `codex exec --ephemeral -s read-only -` with the prompt on stdin, so the session starts blank and cannot edit files. Check `codex exec --help` for flags in your version.
   - omp: a task subagent whose only input is the packet; read-only agent type if offered.
   - Any other host: a new chat or process with no shared history.
   Ask the reviewer to open its reply with `Reviewer-Model: <its own model id, or unknown>`. Record the family as reported. If it is unknown, or the same family as the writer, say so in the report; that review still finds problems but cannot be cited as the cross-family check.
   If no fresh context exists (none available, or the text may not be sent), write `Independent review: not run` and the reason; prepare the packet anyway so the author can run a real review elsewhere. You may still run the checks in `eval.md` as a self-check, labelled "self-check" in the first line. Use it to revise: cut what it finds in your own draft (facts restated in a closing paragraph, stock thanks) before you hand it over, and name what only the author can confirm (a date with no year or weekday, a place readers may not know, a number the brief leaves open). Report in the writer's voice only what you found and what you cannot see; do not say `ready` or "this is good", and do not cite the self-check as evidence for the draft.
4. **Run the fresh-reader test** (always, unless the user declined). Send [fresh-reader prompt](assets/fresh-reader-prompt.md). The reader restates the main point, lists where it stalled and what the text assumes, and says what it would ask next. Before reading the reply, write down your own expected main point and expected reader questions from the brief, so comparison is honest. Then compare. Classify each stall as a text defect, an audience boundary (the brief says the reader already knows this), or a reader limitation. Fix only text defects.
5. **Run the independent review** (Standard and High). Send [reviewer prompt](assets/reviewer-prompt.md) with the rubric if you have one. For subjective criteria, calibrate first; see [calibration](references/calibration.md). Run any deterministic checks (numbers match sources, links resolve, terms stay consistent) as plain pass/fail with evidence, not as scores. At High depth, or when a previous reviewer approved everything, add the rejection-memo variant from the reviewer prompt: one session writes the strongest short case for rejecting, a different session judges which attacks the text already answers.
6. **Compare two versions** when the question is "which is better". Use the blind pairwise procedure in [calibration](references/calibration.md): anonymous labels, random order, swap and repeat, reasons before verdict, unblind only afterwards.
7. **Triage every finding** as accept, reject (one-line, evidence-based reason), or needs author. Severity comes from reader impact, not reviewer tone. Full procedure, the severity table and how to contest a finding are in [triage](references/triage.md). A finding that would add a claim, number, quote, or example the material does not support is rejected as written; if the gap is real, it becomes one plain question to the author in the findings, never text inside the artifact.
8. **Apply accepted fixes** as the smallest edits that remove the defect, keeping the author's voice, claims, qualifiers and numbers. Any revised draft or rewritten passage you hand back is reader-ready: no `[ASK AUTHOR]`, `[VERIFY]` or `[UNTESTED]` markers, no review notes, round history, finding IDs or "changed to…" remarks. Where a fix would need a fact the material lacks, leave that spot as it was, drop the sentence, or state the gap plainly ("The notes do not give a date.") and put the question in the findings. Report changed spots as a list or marked edits instead of reprinting the document. If a genre skill is available, hand the fix list to it.
9. **Round two (Standard and High, only if a critical or major finding was accepted).** New session, new reviewer, same packet shape with the revised artifact only. Do not say what changed or what the first round found. Afterwards you compare the two finding lists yourself and check the diff for drift: small softenings that add up to a changed claim.
10. **Stop and report.** Stop when no accepted critical or major findings remain, when the second round is done, or when what remains needs evidence you do not have. Two rounds is the default cap; extra rounds need the user's say-so. Report what remains, honestly, instead of continuing until the reviewer goes quiet.

### Variant: answering reviewer comments

When the job is a reply to reviewers rather than a review of a draft, follow [responding to reviews](references/responding-to-reviews.md): read the venue or client contract, split the comments into single issues with IDs, answer each in a fixed block, run the provenance, commitment and coverage gates, then have a fresh reader check that the reply answers what was asked. Nothing is promised, run, quoted or cited that the author has not confirmed. The reply is read by the reviewer or editor, so it carries no markers or notes to the author; those go in the hand-off.

## Rules

- **The review report is for the author; anything delivered onward is clean.** Questions to the author are plain sentences in the report or hand-off; use an `[ASK AUTHOR: …]` or `[VERIFY: …]` line only when the question has to sit in a file next to text the author will edit. A revised draft, rewritten passage or response letter holds no markers or process narration ("fixed per F3", "needs author"); it is read by someone else, and a placeholder there reads as unfinished. A response letter still answers the reviewer's own comments by name. Exception: the author asked for a draft to edit; then markers may stay in that draft.
- **The writer does not clear its own text.** Its memory completes sentences the page does not, and a same-context score shares its blind spots. A self-score may rank which fixes to try first; only a review that passed the independence rules can say the text is ready. Light-depth chat messages may ship after a labelled self-check, and the report says it was not independent.
- **The artifact leaves this session only with the owner's consent.** Reason: sending an unpublished manuscript, a client document or personal data to another model is a disclosure. Exception: material already public or the author's own non-sensitive text. For a referee report on someone else's unpublished work, check the venue's tool policy first; the accountable human reads, verifies and writes the report.
- **Give the reviewer the artifact and what a real reader would have, nothing else.** Reason: any statement of intent, history, or desired outcome pulls the judgment toward it. Exception: facts the reviewer needs to do the job (audience, length limit, venue rules, the sources to check against) are brief, not intent, and belong in the packet.
- **Never say what was fixed or changed.** Reason: it invites the reviewer to check the fix instead of reading the text. Exception: a separate verification job ("is this quoted passage still present in this text?") may carry the reviewer's own earlier words verbatim, but it is labelled verification and never counts as a fresh review.
- **Ask open questions, not leading ones.** "What is the main point?" not "Is the intro compelling?" or "Isn't this clear?". Reason: leading questions coach a favourable answer.
- **A new session for every round, and a different model family when possible.** Reason: a reused session anchors on its own earlier judgments; same-family review shares blind spots. Exception: none for the session; if only one family exists, say so in the report.
- **Audience prerequisites are not defects.** If the brief says the reader knows X and the reader stalls on X, the audience is wrong, not the text. If the brief does not say, treat the stall as a defect.
- **Anchor every finding in a quote and a reader consequence.** Reason: findings without location or impact cannot be triaged. Exception: whole-document findings (structure, missing section) name the section instead.
- **A clean result is a valid result.** A reviewer who finds nothing important says so; you do not hunt for something to change. Empty feedback means no findings were raised in that review, not that the text is proven correct.
- **A verdict counts only for what the reviewer actually read.** The reply must be complete (it ends on the verdict line, not cut off by a length or time limit) and must say it covered the whole artifact you sent, not a subset. Reason: a reviewer that stopped halfway or skimmed one section says nothing about the rest. A bare `ready` with no findings list, or with no scores against the threshold you set, is not a pass either. Treat an incomplete or label-only reply as no review, rerun it in a new session, and until then do not report the text as reviewed.
- **Reviewer fixes are suggestions.** Taste-only findings are nits and are skipped when a real author sample or the user's stated style disagrees. Reason: a real author sample outranks a generic reviewer preference.
- **Never loop "edit, re-review, repeat until clean".** Reason: the editor learns to please the reviewer, and the text drifts. Re-run only to confirm a specific accepted finding is gone, in a new session.
- **Do not average disagreements away.** When two reviewers differ on severity or score, find the cause (different reading of the criterion, different evidence, different reader assumed) and record it. Reason: the disagreement is usually the finding.
- **Cost and specialists.** Report the number of sessions used; High depth justifies the extra reviewer. A smooth read says nothing about whether a proof, number, medical or legal statement is right; route those to a domain check or a human.
- **Language.** Review in the language of the document. English pattern lists do not transfer; structure, evidence and clarity checks do.
- **Write like the person, not the process.** A revised draft, passage or response letter keeps the author's person, register and structure: no heading added to an email, letter, reply or short post (a newsletter or notice item keeps the short headline its genre uses); no signposting ("In summary"); each caveat once at its claim; no closing paragraph that restates the body; prose for fewer than about four items. The review report reads like one colleague's notes: plain sentences, each point said once (not again in a verdict, remaining and not-covered line), no framework labels. Reason: the author has to live with this prose, and a report that says everything three times buries the one thing to do. Exception: the fixed fields in Output are required at Standard and High depth.

## Output

Return a short review report. Do not paste the whole reviewer reply unless asked. If the report is saved as a file, the chat reply names the file, the decision and the one open question, and does not repeat the file's content.

```
Independent review: run | not run (<reason>)
Depth: light | standard | high    Rounds: <n>    Reviewer sessions: <n> (family: <Reviewer-Model as reported, or unknown>; same family as writer: yes | no | unknown)
Fresh-reader test: main point restated: matches brief | partly | misses
  Stalls: <n text defects / n audience boundary / n reader limitation>
  Next question the reader asked: <quote>
Reviewer verdict (verbatim line): <ready | revise>    Reviewed: <whole artifact | only these parts: ...>
Rubric: <n> criteria, calibration <calibrated | partly | none> | no rubric used

Findings (a table for more than three; otherwise one plain sentence each: quote, reader impact, decision)
| # | Severity | Location | Reader impact (one line) | Decision | Reason |
Accepted fixes applied: <list, one line each>
Needs author: <one plain question each, with the finding it came from; no marker syntax unless the report is a file the author will edit around>
Remaining after stop: <what is unresolved and why; omit anything already listed as needs author>
Not covered: <only what this review cannot tell and the author might assume it did, e.g. technical correctness; omit when nothing is likely to be assumed>
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
| [references/responding-to-reviews.md](references/responding-to-reviews.md) | Answering reviewer, editor or client comments with a point-by-point reply or rebuttal |

## Examples

Leaking packet and clean packet for the same draft.

Leaking: "Review this launch post. I wanted it to feel confident but not salesy, and I already fixed the weak opening. Isn't the pricing section clear now?"

Clean: "Artifact: launch-post.md. Reader: existing customers of a note-taking app who read the changelog; they know the product, not the new pricing; they will decide this week whether to upgrade. Constraint: under 600 words. Report as instructed."

Fresh-reader result and classification:

- Reader restated: "The app is adding a paid tier with sync." Brief expected: "Sync is free for existing users until March." Result: partly. The deadline is missing from the reader's version, so the date sentence is buried: text defect, major.
- Reader stalled on "workspace seats". Brief says customers know the product and this term is on the current pricing page: audience boundary, no change.
