Load when: sorting reviewer findings into accept, reject or needs-author, defining severity, choosing fixes, or deciding whether to run another round.

# Finding triage and stop rules

A review is a list of proposals, not orders. Every finding gets one decision and a reason you could defend to the reviewer.

## 1. Severity by reader impact

Judge by what happens to the stated reader, not by how loud the reviewer sounds.

| Level | Reader impact | Examples | Default action |
|---|---|---|---|
| Critical | The reader reaches a wrong conclusion, acts wrongly, or cannot tell what the document claims or asks. Also: a claim, number or quote the sources do not support; a contradiction between sections. | Number differs from source; missing step that breaks a procedure; main point absent | Fix before release |
| Major | The reader stalls, misreads an important part, or loses trust in the document. | Undefined term the brief does not cover; conclusion stronger than the evidence; answer buried under background | Fix before release, or record why not |
| Minor | The reader notices friction but recovers on their own. | Repeated example narrative; slightly loose heading; one long paragraph | Fix if cheap |
| Nit | A preference; the document works either way. | Synonym choice, comma habit, rhythm taste | Skip unless the author agrees |

Notes:

- A presentation problem and a structural flaw have different fixes. Do not label a missing experiment, source, or decision as a wording problem; wording cannot repair it. Name it, state it once, and stop rewording.
- Taste findings ("make it punchier") are nits unless tied to a reader consequence. Where a real author sample disagrees with a reviewer's taste, the sample wins.
- A severity you disagree with can be changed in triage; write the new level and why.

## 2. The three decisions

For each finding, choose exactly one.

**Accept.** The finding is true of the text, matters to the stated reader, and has a fix that stays within the material. Write the planned smallest edit.

**Reject.** Write one line with evidence. Valid reasons:

- The text already says it, at a quoted location.
- The finding contradicts the source; cite the source line.
- The reader brief says the reader already knows this (audience boundary).
- The fix would add a claim, number, quote, name, credential or example the material does not support.
- The finding is a style preference against the author's sample or stated style.
- The reviewer misread: quote the passage and say how.
- The finding is out of scope for the document type or the length limit.
- The author has already confirmed this choice (give where).

Invalid reasons: "I disagree", "that was intended" (a reader cannot see intent), "too much work" (that is a cost decision: accept it and list it under remaining), "the reviewer is a model".

**Needs author.** The finding is plausible but only the author can answer: a missing fact, a choice between two reasonable framings, an unstated audience, a claim the author must confirm. Write one plain question that names exactly what is missing and what would settle it ("Do you have an approved resident quote and a savings figure with its basis? If not, leave the benefit out."). Ask only for the evidence, not for a wider decision about the document's purpose. Use an `[ASK AUTHOR: <question>]` or `[VERIFY: <what, against which source>]` line only when the question has to travel inside a file the author will edit. Never put a marker, or the question, in the artifact or in any revised text: leave the spot as it was, drop the sentence, or state the gap plainly in reader language ("The notes do not give a date."). Do not fill the gap yourself.

## 3. Findings that would add unsupported content

Reviewers, especially models, like to propose "add a concrete example", "include a statistic", "mention the benefit". When the example or number is not in the material:

1. Reject the fix as written.
2. If the gap is real (the reader would stall), convert it to needs-author in the findings with the exact missing item. The artifact gets no placeholder.
3. If the author supplies it, accept the finding then.

Specificity comes from the user's material, never from the reviewer or from you.

## 4. Choosing and ordering fixes

1. Fix in dependency order: purpose and structure, then claims and evidence, then paragraph flow, then sentences, then surface. Do not polish a paragraph that may be cut.
2. Make the smallest edit that removes the defect. Keep the author's voice, claims, qualifiers, negations, numbers, names and structure unless one of those is the defect.
3. One finding, one edit. Do not bundle a "while I was there" rewrite.
4. Prefer deleting a repeated passage to rewording it. A repeated example is told fully once and called back briefly later.
5. Reviewer-required qualifiers (a hedge a reviewer asked for earlier) stay unless the reader impact changed; wording may change if meaning, scope and strength stay identical.
6. After fixes, diff the text against the version the reviewer saw. Small softenings across rounds can add up to a changed claim; undo any that changed meaning.

## 5. Multiple reviewers and repeated findings

- Two reviewers raise the same finding: raise confidence, not severity automatically.
- Reviewers contradict each other: record both, apply the reader brief and the author's sample, and send the unresolved ones to the author. Do not split the difference in the text.
- A finding repeated in round two that you rejected in round one: reconsider once, and keep the rejection only with a stronger reason.
- Reply with no verdict line, or cut off before it: treat as `revise`, and as a failed review, not a partial pass. Rerun in a new session (the whole artifact, or the part that was missed) before any stop rule counts it.
- Reply says `ready` but lists no findings, no "no critical or major findings" line, and no scores against the stated threshold: not a pass. Ask in a new session for the checked list. If the reply covered only some sections, record those sections in the report and treat the rest as not reviewed.
- Reply with only praise: valid as a result, but check that the prompt did not contain leading language; if it did, rerun in a new session with a cleaned prompt.

## 6. Stop rules

Stop when any of these holds:

1. No accepted critical or major findings remain after a fresh round that finished and covered the whole artifact.
2. The second round is complete. The cap is two by default; a third needs the user's approval.
3. What remains needs evidence, a decision or a specialist you do not have; list it as open.
4. Only minor findings and nits remain; list them, apply the cheap ones, and stop.
5. Three revisions in a row changed nothing substantial; ask whether something can be cut, then stop rewording.
6. The user says stop.

Do not loop on "edit, re-review, repeat until clean". The reviewer is a sensor; using it as a target teaches the editor to please it. Re-run only to confirm that a named accepted finding is gone, in a new session.

If the cap is hit with critical or major findings open, say so plainly, name each with the effort needed, and recommend either manual follow-up or a different approach. Do not claim the text is verified.

## 7. Human gates

Stop for a person when the finding touches:

- Safety, security, medical, legal or financial statements: a domain expert or the author signs off; record what changed, why a human must look, and a risk level.
- Facts only the author can know: credentials, experiences, opinions, quotes.
- Anything that would send the text outside the author's control (publishing, emailing) unless the user asked for it.

## 8. Report format

Short and true. The report is author-facing: findings and questions are plain sentences, one line per decision. For up to about six findings, one table row each (finding, decision, reason or next step) in the reviewer's order is easiest to scan; do not regroup by decision. Any revised text delivered with it is clean: no markers, finding IDs or review notes. List what changed and why; what was rejected and why; what needs the author; what remains. Do not close with a recap of the table.

```
Findings: <n> total (critical <n>, major <n>, minor <n>, nit <n>)
Accepted: <n>   Rejected: <n>   Needs author: <n>
- F2 major, "<short quote>": added the deadline to the first paragraph. Reader impact: could not tell by when to act.
- F5 critical -> reject: "add a customer quote"; no quote exists in the material. Needs author: is there an approved customer quote? The draft is unchanged.
Remaining: <unresolved items, with reason>
Cost: <sessions, rounds>
```

For a clean text: "no accepted findings".

When the user hands you findings to sort and nothing else (no review was run, no draft to revise), the table is the whole output. One row per finding: the decision (act, skip or reject, or answer yourself), one sentence of evidence that quotes or points to the draft or source, and the next step in one sentence. A needs-author row holds one question. Leave out the count lines and the cost line, severity labels unless you changed one, and any closing note on what the triage did not check. The reader asked which findings to act on; everything else in the file delays that answer.

## 9. Contesting a finding and drift

A rejection in triage is a decision for the author, not a ruling on the reviewer. When the author (or user) disputes a finding that matters, or insists on a rejection the reviewer is likely to repeat:

1. Write a short card per contested finding, at most three per round: label (accept / partly accept / reject), the argument (already addressed, based on a misreading, out of scope), and the evidence (a quote, a source line, a section the reviewer can re-read).
2. If a ruling from the reviewer is wanted, run a separate verification job in a new session: the reviewer's own finding verbatim, the card's evidence as locations, and an instruction to open those locations and check them itself. A summary of the argument is not evidence. Label this verification; it never counts as a fresh review.
3. Ruling vocabulary: sustained (the card holds, drop the finding), overruled (the finding stands, keep the action), partly sustained (narrow the finding to what still holds). Withdrawn findings leave the must-fix list.
4. A rebuttal never fabricates evidence or misstates a result. Honest grounds are a factual error in the review or a point outside the document's scope. "Too costly" is not a ground; accept the finding and list it under remaining.
5. Before conceding that a concern cannot be addressed, try two different fixes (narrow the claim; add the limit; reframe). Only then concede, narrowly, and bound what is lost.

Drift: a suggestion that would change what the document is trying to do (a different audience, a different question, an added contribution) is a scope change, not a revision. Name it as drift, argue against it with evidence from the reader brief, or send it to the author as a decision. Do not fold it in as an ordinary fix.
