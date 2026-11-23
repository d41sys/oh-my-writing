Load when: drafting or checking a point-by-point reply to reviewer, editor or client comments (rebuttal, response letter, revision cover note), or planning revisions against such comments.

# Responding to reviews

Triage ([triage](triage.md)) decides which comments are worth acting on. This file turns that decision into the reply itself. The reply is an artifact like any other: the reader is the reviewer or editor, and every claim in it must trace to something the author has confirmed. The reply is reader-facing: it holds no `[ASK AUTHOR]`, `[VERIFY]` or `[UNTESTED]` markers and no notes to the author (unless the author asked for a draft to edit). The working file, issue list and hand-off in section 10 are author-facing, and markers stay there. Editing the manuscript text once comments are accepted belongs to the genre skill, or, for ML papers, to `structured-drafting` for structure plus `evidence-grounded-writing` for claims; checking numbers and citations against sources belongs to `evidence-grounded-writing`.

## 1. Read the contract before drafting

Collect, and ask the author for anything missing:

- Format (single document, one thread per reviewer, form field), hard length or character limit, anonymity rules, whether links or attachments are allowed.
- Whether new experiments, data or a revised manuscript are allowed at this stage, and the deadline.
- Which reviewers are friendly, undecided or hostile, only if the author knows.

Venue rules differ by year and track and change without notice. Do not quote a limit or policy from memory: record `[VERIFY: current rules for <venue, year, track>]` in the hand-off and, until the author confirms, write the reply to the limit the author gave, or say nothing about the rule in the letter.

## 2. Split the comments into single issues

1. Copy each review verbatim into a working file. Never edit the reviewer's words.
2. Split into atomic issues with stable IDs (`R1.1`, `R1.2`, `R2.1`). One question or complaint per issue.
3. For each issue record: the quote that anchors it; the kind (misunderstanding, unclear exposition, method problem, request for more scope); severity by what it does to the reviewer's decision; whether text alone can fix it (yes, partly, no); status (open, answered, deferred, needs author).
4. Give more drafting care to reviewers who are undecided and whose concerns are answerable. A concern that is purely a difference of philosophy gets one polite, evidence-based answer and no more.
5. Keep a list of blocked claims: points a reviewer raised that the material cannot back. In the reply they become concessions or plain statements of what the material does not show; the question for the author goes in the hand-off as `[ASK AUTHOR: ...]`. They never become new claims.

## 3. Choose the response mode per issue

| Situation | Mode |
|---|---|
| Reviewer misread, or the text was unclear | Clarify, and treat it as the author's communication defect: thank the reviewer, say what was rewritten, show the new wording. Do not write "as we already stated". |
| The answer already exists in the material | Point to it with the exact location, quote the evidence. |
| The comment is right but the claim is wider than the evidence | Narrow the claim in place and add the matching scope sentence. |
| New work requested | First check whether a lighter route meets the concern: narrower claim, clearer text, a limit sentence, a correction, an analysis the author already has. Offer new work only if the central claim needs it and the author confirms it is done or approved. |
| Comment is right and cannot be fixed now | Concede narrowly, say what remains true, record it as future work or a stated limit. |
| "It reduces to X" or "this is just Y" | Agree on what does reduce, name the structural feature that remains different, and back it with a mechanism the material contains. Without a mechanism, concede. |
| Evidence the author hoped for failed or came out unclear | Switch to a concession or future-work boundary. Never rewrite the result to fit the answer. |

A reviewer's generic "add more experiments" does not override the venue's rules or the paper's scope.

## 4. The response block

One block per material issue. In tight limits, shorten the quote to the issue ID and start with sentence 1.

```
R1.2 — "<verbatim quote of the reviewer's point>"
Answer: <sentence 1: agree / clarify / disagree, stated directly>
Evidence: <existing result, quoted passage, or a new analysis that was actually completed and is allowed>
Change: <section, page or table where the text changed, only if revisions are allowed>
Remaining limit: <what the evidence still does not establish>
```

Rules for the block:

- Sentence 1 answers; it does not thank, apologise or defend.
- Prefer the smallest evidence that answers this reviewer's question over dumping every result.
- Counter-intuitive points get a number or a quoted passage, not an assertion.
- Planned or hypothesised work is labelled as planned; a planned analysis is never written as done.
- Disclose a non-obvious design choice before a hostile reading invents a worse one, but only if it is true that the choice was made that way and when.
- Concede when the reviewer is right. A narrow, honest concession beats a broad denial.
- Answer friendly reviewers too, and keep one tone: respectful, concrete, no sarcasm, no suggestion of bad faith.

## 5. Three gates before the reply leaves

Any failure blocks the reply.

1. **Provenance.** Every factual statement maps to the manuscript, the review, or a result or derivation the author confirmed in this conversation. A statement with no source is deleted from the reply or restated as a limit ("The current results do not cover X."); the question goes to the hand-off as `[ASK AUTHOR: ...]`, not into the letter.
2. **Commitment.** Every promise ("we will add...") is already done, approved by the author for this reply, or labelled future work. Keep a checklist of every manuscript edit the reply implies, each tied to an issue ID. Every promised edit must be on the list and every list item must appear in the reply.
3. **Coverage.** Every issue ends as answered, deferred on purpose with a reason, or needs author. None may disappear. Count each status in the hand-off.

Also check: no invented experiment, number, citation, participant quote or deployment; a citation you add to the reply stays out of the letter until the author has checked that it exists and supports the point, and until then it is listed in the hand-off as `[VERIFY: citation exists and supports the point]`; leftover markers from earlier cycles are stripped from the letter and listed in the hand-off for the author to keep or drop. Before sending, scan the letter for `[ASK`, `[VERIFY`, `[UNTESTED`, "TODO" and notes that address the author instead of the reviewer.

## 6. Keep the letter and the manuscript in sync

- Passages quoted from the manuscript in the reply match the revised text word for word. After every manuscript edit, update the quotes in the same pass, in every copy of the letter.
- Table, figure and section numbers in the reply match the revised manuscript. If a float was added or removed, renumber the reply's references first, then apply the quote updates.
- Never edit the reviewer's own text in the reply.
- Before sending, compare the letter against the previous version; every changed paragraph is an intended change.
- Blind venues: scan the reply and its attachments for identifying details (names, affiliations, lab or tool codenames, self-citation phrasing, mentions of earlier submissions or other venues, repository links).

## 7. Over the limit

Cut in this order: repetition, friendly elaboration, opening padding, then wording. Never drop the answer to a critical concern to save space. If a strict paste version and a fuller version are both wanted, deliver the paste version clean; show the author what was cut as a separate list or as highlighting in an author-facing copy, never as marks inside the paste version.

## 8. Check the reply with a fresh reader

For Standard or High depth, send a new session the reviewer's comments, the reply and the revised text, and nothing about the author's reasoning:

```
Below are one reviewer's comments, the authors' reply, and the revised
document. For each comment: is it answered, partly answered or not answered,
by the reply and the revised text? Quote the passage that answers it. Name any
claim in the reply that the revised document does not support, any promise the
reply makes that the document does not show, and anything in the tone that
could read as dismissive. Do not rewrite the reply.
```

Triage what comes back like any other review. Cap at two rounds; a third needs the author's approval.

## 9. Follow-up rounds

Log the new comments verbatim, attach them to existing issue IDs or open new ones, and draft only the delta. Escalate with evidence, not rhetoric. Stop arguing a point once the reviewer is immovable and no new evidence exists; spend the remaining space on concerns that can still change the decision. Keep reviewer-requested qualifiers unless the reader impact changed.

## 10. Hand-off

Author-facing: markers belong in this hand-off and nowhere in the letter.

```
Issues: <n> (answered <n>, deferred <n>, needs author <n>)
Commitments: already done <n>, approved <n>, future work <n>
Needs author: <list of [ASK AUTHOR: ...] items, each with the issue ID and what the letter says in the meantime>
Unverified: <list of [VERIFY: ...] items, each with where the letter is silent or hedged until checked>
Concessions made: <one line each>
Not covered: <what the reply cannot establish, for example results not yet run>
```
