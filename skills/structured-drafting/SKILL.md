---
name: structured-drafting
description: Turns raw material (notes, meeting notes, source excerpts, interview transcripts, bullet ideas, or an existing rough draft) into a first draft, short update, email or article through explicit, size-scaled stages - brief, material inventory, core message, grounding order, shape, outline, block-by-block drafting - and offers a section-by-section co-authoring mode when the author wants to steer. Use when asked to "turn these notes into a draft", "turn my meeting notes into an update", "write a short email from these notes", "write a first draft from this", "outline this for me", "structure this document", "help me write this together", "draft from my transcript", "write an article from this interview", or "organize my rough ideas into an article".
license: MIT
metadata:
  version: "1.3"
  skill-author: d41sys
---

# Structured Drafting

Turns loose material into a first draft that a reader can follow. The skill works from the reader backwards: who reads, what they already know, what they should walk away with. It then picks a shape, orders the blocks so nothing is used before it is explained, and drafts one block at a time. The draft is built from the author's material; gaps become questions, never inventions.

## When to use

- The author has notes, sources, a transcript, bullets, or a rough draft and wants a first draft or a restructure.
- The author wants an outline before any prose, or wants to write a document together, section by section.
- A draft exists but the order is wrong: points are used before they are explained, or the pieces could swap places unnoticed.

Not for: polishing sentence-level AI patterns (use `anti-slop-editing`); matching or building a personal voice (use `author-voice`); verifying claims, numbers and citations (use `evidence-grounded-writing`); a cold read of a finished draft (use `independent-review`); genre specifics for posts (`post-writing`), reports (`report-writing`), documentation (`technical-docs`), or CVs and letters (`career-documents`). For ML paper sections use `academic-writing` if installed; otherwise this skill for structure plus `evidence-grounded-writing` for claims.

## Inputs

Read first: everything the author supplied (files, pasted text, links they named). Treat it as read-only; write the draft in a separate place.

Needed for the brief (fill from the request and material before asking anything):

- Reader: who, what they already know, what they will do with the piece.
- Purpose: the one thing they should understand, decide, or do afterwards.
- Constraints: channel, length, deadline, required sections, house template, language.

Ask at most three questions, fewer for short tasks, and only when the answer changes the structure (for example, who the reader is, or which of two conflicting goals wins). In non-interactive runs proceed on stated assumptions and list them in the brief (or in one line of the reply for short tasks). If the type of document is ambiguous, ask once rather than guess the form.

No material at all, and no way to ask: do not draft content. Return the questions or an outline of what is needed (a skeleton with `[ASK AUTHOR: ...]` slots) and say so. That skeleton is an author-facing artifact, not a draft, so the markers stay.

## Workflow

Choose a mode, then run the stages that fit the size of the task.

Modes:

- **Solo (default):** the skill runs the stages and returns an outline (when warranted) and a draft.
- **Co-author:** the author wants to steer. Triggered by "write this together", "let's go section by section", or by a large, high-stakes document with the author present. Follow [the co-authoring protocol](references/co-authoring.md) for stages 6 onward.
- **Explore:** the angle is still open and the material is loose. Collect fragments first (see the co-authoring file), commit to a shape later.

### Scale the stages to the task

Size by the length of the deliverable, not of the material. On a boundary, pick the smaller row.

| Task | Stages to run |
|---|---|
| Message, email, caption, up to ~200 words | Brief (3 lines, in your head or one line shown) -> draft |
| Short piece, ~200-1,200 words (post, update, short memo) | Brief -> core message -> one-line-per-block outline in the reply -> draft |
| Standard piece, ~1,200-4,000 words (article, report, long doc) | All stages; show the outline and keep/cut/merge decisions; draft after the author confirms, unless told "just write it" |
| Large or high-stakes, multi-section, several sources, or several authors | All stages, ledger written down, co-author mode offered, fresh-reader test at the end |

A stage that adds no decision for this task is skipped and not mentioned. Never run the full ceremony on a short request; the extra questions cost the author more than they give back.

### Stages

1. **Size the task and pick the mode.** Use the table. State the choice in one line only when it is not obvious.
2. **Write the brief.** Fill [the brief template](assets/brief-template.md): reader, what they know, purpose, the one takeaway, constraints, channel, length. Use what the request and material already say. Mark each guess as an assumption.
3. **Inventory the material.** Split the material into units and label each by kind (claim, example, datum, story, opinion, definition, quote), by source (file, speaker, page, "author's head") and, for notes and transcripts, by status (decided, proposed, unconfirmed, open; a speaker's "about" or "I think" belongs to the unit). Note duplicates and contradictions: two values for one thing are both kept with their sources, never merged or picked. Write each gap the draft will need as a question (an example, a number, a counter-case), not as filler. See the mechanics in [shapes and blocks](references/shapes.md#material-inventory).
4. **State the core.** Write the main message in one or two sentences. Test it: could a knowledgeable reader sensibly argue the opposite, and where does it stop holding? If the core is a platitude, find the trade-off or the condition that makes it specific, using only what the material supports. If no core can be stated, say that and ask; do not outline around an inventory of topics.
5. **Build the grounding ledger.** List the concepts the reader already has (prerequisites) and the concepts the draft must introduce. Decide the prerequisite boundary from the reader in the brief: too high shuts people out, too low buries the opening in definitions. Order blocks so each block only leans on concepts that are already on the ledger. A block that needs an ungrounded concept gets a grounding block before it, or that concept is promoted to a stated prerequisite.
6. **Choose the shape.** Pick by purpose: argument, explanation, narrative, decision, or instruction (see [shapes](references/shapes.md)). Mixed purposes get a primary shape with a labelled secondary one. Do not impose one template on every task. If the document is a repackaging of a longer source, also decide how much of it is kept (default: keep everything that serves the purpose and say what was cut).
7. **Outline.** Use [the outline template](assets/outline-template.md). One line per block, each line a complete message, so that reading the lines alone tells the story. Give blocks unequal weight on purpose: more room for what is new or central, less for what the reader knows or can infer. Note for each block its source units and what it grounds.
8. **Test each block and decide keep/cut/merge.** For every block ask: what does the reader lose if this is removed? If nothing, cut it or fold it into a neighbour. Check that headings alone carry the argument, and that swapping two body blocks would break something. Check coverage too: does the outline say who is affected and what could go wrong or be objected to, not only the happy path? Add such a block only when the material supports it; otherwise record it as a gap. Record the decisions where the author can see them: kept, cut (with the reason), merged, and left over. Surplus material is expected; the piece ends when its argument is complete, not when the pile is used up.
9. **Draft block by block.** Per block: the message first (or when the shape needs a different order, such as a story that turns), then the evidence from the inventory, then a hand-off to the next block. Paraphrase, split or merge the material so the piece reads in one voice; quote only when the original wording is the point. Choose the form of each block deliberately (prose for reasoning, a list for parallel items, a table when the same fields repeat). Sentence-level craft is in [paragraphs and sentences](references/paragraph-and-sentence.md). When a block needs something the material lacks, state the gap in the reader's language or leave that sentence out (see [gaps in the draft](references/gaps-in-the-draft.md)), write the author's question as a marker line for the reply, and keep going. The brief, inventory source labels, outline and decisions are for the author; none of their notes go into the draft text.
10. **Close and hand off.** Make the ending serve the reader's next need (a decision, an action, a verified result, an earned implication), not a template. Run the checks in [eval.md](eval.md). Then route: sentence-level polish to `anti-slop-editing`, voice to `author-voice`, factual and number checks to `evidence-grounded-writing`, a cold read to `independent-review`. If those skills are absent, apply the matching checks in eval.md yourself and say what was not checked.

## Rules

- **Brief before prose.** Without a reader and a purpose, every structural choice is a coin flip. Exception: for a tiny message the brief is two lines of thinking, not a form.
- **Reader path, not discovery path.** The order in which the author learned things is rarely the order the reader needs. Order by what the reader lacks. Exception: a narrative whose point is the discovery itself.
- **No invention.** Missing example, number, quote, source, credential, or opinion becomes a stated gap or an omission in the draft, and a question to the author. A slot the chosen shape expects but the material cannot fill (for example the recommendation in a decision piece) is handled the same way, never guessed. A figure you compute from the material (a difference, a ratio, "doubled", an average) is also a new claim: give the inputs as stated, and compute only when the author asked. Reason: an invented detail is a fabricated claim in the author's name. No exception.
- **The draft reads as finished.** Unless the author asked for a draft to edit, the draft the reader receives (the saved file, or the text labelled as ready to use) holds no `[ASK AUTHOR]`, `[VERIFY]` or `[UNTESTED]` marker, no `[source: ...]` tag, no comment lines carrying outline or source notes, and no process narration ("as requested", "based on your notes", "I checked"). A gap is stated as a fact about the material ("The notes give no launch date.") or the sentence is left out. The author's question goes to the reply as a marker line and, when a file was saved, also to `open-questions.md` beside it. Reason: a placeholder in text sent to a reader looks unfinished, and "don't wait for me" means nobody answers before it goes out. Exception: the author asked for a draft to edit; then markers stay in place and the reply says it is a draft. The brief, decisions, outline with its grounding ledger and the no-material skeleton are author-facing and keep their markers and source labels.
- **One block, one message.** Two points need two blocks. Exception: a short list of genuinely parallel items can share a block.
- **Ground before use.** A concept used before it is introduced loses the reader, even if no jargon is visible. Exception: a deliberate hook that names a puzzle the piece will resolve, said to be a puzzle.
- **Shape follows purpose, not genre label.** The word "report" or "guide" does not give an outline. Exception: a venue or house template that fixes the structure; then gather material against that template.
- **Keep decisions visible.** Cut, merged, and left-over material is reported in a line or two. Reason: silent cuts erase things the author wanted; silent keeps bury the point.
- **Do not shuffle the author's claims.** Restructuring may reorder and merge; it must not strengthen, weaken, or drop qualifiers, numbers, names, negations, or status (a tentative plan stays tentative, an unconfirmed partner stays unconfirmed, an attributed opinion stays attributed). Exception: the author asks for a stronger or softer claim.
- **Contradictions stay visible.** When the material gives two values or positions for one thing, ask; when the author cannot be asked, the draft reports both with who gave each and says plainly that the material does not settle which is right ("the interview gives about 40% in one answer and 30% in another"), nothing downstream (totals, percentages, conclusions, "up from X") leans on either, and the question goes to the reply as an `[ASK AUTHOR: which is right]` line. Reason: picking or averaging creates a figure nobody gave. Exception: the material itself says which one supersedes, in the speaker's own words (a stated correction, "the final number is", "I misspoke"). A later restatement, a rounder figure or an answer to a clarifying question is not a correction; when in doubt keep both.
- **Bridge only real relations.** Add connective tissue only where the relationship exists in the material. If it does not, report a missing through-line instead of papering over it.
- **Scale the process.** More stages are not more quality. If the author signals "just write it", write; list assumptions in the reply, not in the deliverable.
- **Language.** Structure, grounding and evidence checks apply in any language. Lexical word lists and English sentence-position advice do not transfer automatically; when drafting in another language (for example Vietnamese), keep the structural stages and write sentence-level choices by that language's own norms.

## Output

Return, in this order, only the parts the task size calls for:

1. **Brief**, as filled fields with assumptions marked (omit for tiny tasks beyond a one-line restatement).
2. **Decisions**: kept / cut (reason) / merged / leftover.
3. **Outline**: one line per block. Brief, decisions and outline are author-facing: they may carry source labels and markers.
4. **Draft**, free of markers and notes as the rule above says. Gaps appear as plain statements or omissions.
5. **Questions for the author**: each `[ASK AUTHOR: ...]` and `[VERIFY: ...]` item in full, with what it blocks and what the draft says meanwhile.
6. **Short note**: what the draft depends on that was not verified, and which sibling skill to run next.

When the request names a file or place to save, that file holds the draft only: no label, brief, outline, decisions, note, marker or source tag. Scaffolding goes in the reply (for short tasks, one line of assumptions). When there is at least one open question, also write `open-questions.md` in the same folder, one numbered item per question with what it blocks and what the draft says instead, and repeat the same items in the reply. A deliverable with no open question needs no such file. Otherwise label the draft so it can be used as is (for example "Draft (ready to post)"); brief, decisions, outline and note are scaffolding for the author and never appear inside it. A short deliverable stays short: a three-sentence email is three sentences, and an unknown the email can ask its recipient about is asked in the email, in plain words. When the author cannot be asked, proceed with stated assumptions and stated gaps instead of questions.

In co-author mode the deliverable is one section at a time, each followed by the next question, not the whole document. The section text is clean like any draft; its gap questions are listed under it in the reply.

## Examples

Outline lines that carry the story alone (a decision piece from meeting notes):

- Weak: "Background", "Options", "Discussion", "Next steps".
- Strong: "Support tickets doubled after the March release", "Three fixes were considered; two fail the staffing limit", "Recommend the smaller patch, reviewed in two weeks", "Decision needed by Friday; owner and trigger for revisiting".

Gap handling:

- Weak: adding "a recent survey found most users prefer shorter forms".
- Weak: leaving `[ASK AUTHOR: one real example showing users abandon the long form]` inside the article that goes to readers.
- Strong, in the draft: "The notes do not say how many users abandon the long form." (or drop the sentence), and in the reply and `open-questions.md`: `[ASK AUTHOR: one real example or number showing users abandon the long form]`. Continue with the next block.

## Reference files

| File | Load when |
|---|---|
| [shapes.md](references/shapes.md) | Choosing a shape (stage 6), building block patterns, weighting blocks, doing the material inventory |
| [gaps-in-the-draft.md](references/gaps-in-the-draft.md) | Stage 9, whenever the material lacks something the draft needs; wording, `open-questions.md` format |
| [co-authoring.md](references/co-authoring.md) | The author wants to write together, the angle is open (explore mode), or the document is large |
| [paragraph-and-sentence.md](references/paragraph-and-sentence.md) | Drafting blocks (stage 9), or fixing paragraphs that read as lists of points |
| [brief-template.md](assets/brief-template.md) | Writing the brief (stage 2) |
| [outline-template.md](assets/outline-template.md) | Writing the outline and ledger (stages 5-8); author-facing |
| [eval.md](eval.md) | Before returning any output |
