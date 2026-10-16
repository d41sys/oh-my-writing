# Co-authoring protocol

Load when: the author wants to write a document together section by section, the angle is still open (explore mode), or the document is large enough that the author should steer. Do not load for short pieces: a multi-round dialogue costs the author more than a first draft they can mark up.

Contents: [When co-authoring pays off](#when-co-authoring-pays-off) | [Phase 1: gather context](#phase-1-gather-context) | [Phase 2: build section by section](#phase-2-build-section-by-section) | [Phase 3: fresh-reader test](#phase-3-fresh-reader-test) | [Explore mode](#explore-mode-fragments-first) | [Growing a draft move by move](#growing-a-draft-move-by-move) | [Working-file hygiene](#working-file-hygiene) | [Reply format](#reply-format)

## When co-authoring pays off

- The document is long or high-stakes, and the author holds knowledge the material does not contain.
- The angle is open and the author wants to shape it, not just approve it.
- The author asks for it.

It does not pay off for messages, short posts, or edits to an existing draft. Offer it once if it might help; if the author declines, return to solo mode and do not raise it again.

Counts below (questions, options, rounds) are guides scaled to the section, not quotas. Stop asking when answers reach edge cases instead of basics.

## Phase 1: gather context

Goal: close the gap between what the author knows and what you know, without turning it into a questionnaire.

1. **Meta-context, at most a few questions:** what kind of document, who reads it, what effect it should have, whether a template or house format exists, any constraint on length, tone, or approvals. Skip anything the request already answers.
2. **Free dump.** Invite the author to pour out everything relevant in any order: background, why the document exists, options considered and rejected, politics, deadlines, links to existing material, and things they want to avoid. Do not ask them to organise it. If they point to files or threads, read them; do not ask them to paste what you can read.
3. **Clarifying round.** Read the dump, then ask the frontier: every question whose answer does not depend on another unanswered question. Number them. For each, offer a recommended answer worded so that "yes" accepts it. Shorthand replies are fine. Look up anything findable in the supplied material instead of asking; the author owns decisions, you own fact-finding.
4. **Repeat** with the new frontier until the questions are about edge cases and exceptions, not fundamentals. State the shared understanding in a few lines and ask for a correction before building.

If the author is unsure of the structure, propose a short scaffold (a handful of sections suited to the document type, with shape per [shapes](shapes.md)), confirm it, then create all headings with a placeholder such as `[To be written]` so the author can see the whole.

## Phase 2: build section by section

Order sections by unknowns: start with the section holding the most open decisions (usually the core proposal or the technical approach), then the rest. Write summary-type sections (abstract, executive summary, overview) last, when their content exists.

For each section, run this loop:

1. **Clarify.** A short numbered round of questions specific to this section, aimed at what the context so far leaves unclear. Skip if nothing is unclear.
2. **Brainstorm.** Offer a numbered list of candidate points for the section: items from the dump the author may have forgotten, alternative angles, failure conditions, unstated assumptions. Size the list to the section; a short section gets a handful, a core section more. Number them so the author can answer by number. Offer to produce more if wanted.
3. **Curate.** The author answers with operations on the numbers. Accept freeform feedback and translate it into these operations, then confirm the translation in one line:
   - `Keep 1, 4, 7`
   - `Remove 3 (duplicates 1)`, with a reason, so criteria become shared
   - `Combine 5 and 6`
4. **Gap check.** One question: given the kept items, is any key requirement, caveat, or reader question missing? Add it before drafting.
5. **Draft.** Write the section from the kept items only, replacing the placeholder in place. Use [paragraph-and-sentence.md](paragraph-and-sentence.md) for craft. Mark unsupported specifics `[ASK AUTHOR: ...]` or `[VERIFY: ...]`.
6. **Refine by local edits.** The author reacts ("tighten the second paragraph", "the example is wrong"). Change only what was named, leave the rest untouched, and show what changed. Do not regenerate the section after each comment. If the author's comments are broad ("not quite right"), ask what specifically; do not guess a rewrite.
7. **Move on.** After about three rounds with no substantial change, ask what could be removed without losing anything important, confirm the section is done, and go to the next.

Keep the brainstorm lists and curation notes in the conversation or a scratch file, not in the document. The document holds only drafted text.

**Near the end.** When most sections are done, say you will read the whole document again. Check flow between sections, repeated or contradictory points, terminology that drifted, vague filler, and sentences that carry nothing. Give that feedback on the whole before making further edits.

## Phase 3: fresh-reader test

A draft passes only when someone without the author's context can use it.

1. Hand the document, and only the document, to an independent reader with no conversation history, along with the questions a real reader would ask. If `independent-review` is available, run its fresh-reader protocol; otherwise use a new session or a person, and say which you used.
2. Compare their answers with what the author intended. Where the reader answers wrongly or hesitates, the document is unclear at that spot. Where the reader flags a term, it is undefined or used before it is grounded.
3. Fix the specific gaps with local edits, and re-run the questions that failed.
4. Report honestly: a fresh reader tests self-sufficiency, not whether the content is correct. Facts, numbers and citations still go to `evidence-grounded-writing` or a domain expert.

If no independent reader is possible, read the document yourself question by question and say that the test was weaker because you share the context.

## Explore mode: fragments first

Use when the angle is open and the author is still finding it. Separate exploring from committing.

1. **Capture fragments.** A fragment is anything that might survive into the piece: a sharp sentence with no home yet, a claim with a one-line reason, a scene, an analogy, a half-thought, a quote, a complaint. It must be clear to the author; it need not stand alone for a cold reader and need not be a finished argument. Judge it as good writing, not as a complete claim.
2. **Ask to draw material out**, without pushing structure, phases, or an outline. Ask about what they saw, what surprised them, what they disagreed with, what they would tell a friend. Stop when the author is tired; do not make interviews a ritual.
3. **Capture without interrupting.** Append fragments to a single working file in arrival order, separated by a plain divider, with one working title and no headings or tags. Acknowledge in a few words; do not ask permission for each. Ask for a file location once if none exists.
4. **Look for the leading word.** When one idea keeps returning, offer a plain name for it; prefer an existing word, and only coin a new one when none fits.
5. **Commit when ready.** When the author says the pile is enough, or the core is visible, treat the pile as fixed and go to the stages in SKILL.md (core, ledger, shape, outline). Leftover fragments are normal; the piece ends when its line is complete.
6. Skip explore mode when the author already has a fixed template or venue structure: gather evidence against the template instead.

## Growing a draft move by move

An optional slower loop for essays and argued posts where the author wants to control the line of thought. Do not use for templated reports or short pieces.

1. Read the whole pile first; treat it as read-only; draft in a separate file.
2. **Competing openings.** Offer two or three candidate openings, each implying a different angle. The author picks one or blends. The opening defines what the rest owes the reader.
3. **Next move.** Ask: given what is on the page, what does the reader need next? Offer two or three candidates, each reachable from what is already grounded, each labelled with the concepts it would ground and what that would unlock. Write only the agreed move, then stop.
4. **Size by job.** A move does one thing: sets a scene, lands a point, poses a question, turns the angle. It may be a sentence or several paragraphs. A move that needs its own subheadings is two moves.
5. **Interrogate each block.** What does this give the reader that the last one did not? If it is cut, what breaks? Is this sentence doing two jobs? The opening promised X: have we drifted to Y?
6. **Name gaps** (an example, a number, a counter-case missing from the pile) and either get it from the author or cut the move.
7. Append each agreed block to the article file immediately, so the author sees the piece grow. The author decides when it is done.

## Working-file hygiene

- Re-read the working file before every write. The author may have edited, reordered or deleted things; preserve their edits exactly.
- Treat "cut that", "sharpen it", "merge those" as first-class instructions, not suggestions.
- A substantial author edit to an earlier block can change what comes next; re-check the ledger.
- Add no publishing markup, platform formatting or front matter that was not requested.
- Keep a running glossary line when a concept is named in conversation; update it when a term is sharpened. Use the glossary to hold one term per concept.
- Never overwrite the source material.

## Reply format

Keep each reply short and ready to answer:

- State where you are in one line ("Section 2 of 5: options; curating").
- Present the numbered list or the drafted text.
- End with the single next question or the exact operation you expect ("Keep / remove / combine?").

If the host has no separate reader or sub-session available, say so at the fresh-reader step and fall back to the weaker self-read.
