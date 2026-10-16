---
name: structured-drafting
description: Turns raw material (notes, source excerpts, transcripts, bullet ideas, or an existing rough draft) into a first draft through explicit, size-scaled stages - brief, material inventory, core message, grounding order, shape, outline, block-by-block drafting - and offers a section-by-section co-authoring mode when the author wants to steer. Use when asked to "turn these notes into a draft", "write a first draft from this", "outline this for me", "structure this document", "help me write this together", "draft from my transcript", or "organize my rough ideas into an article".
metadata:
  version: "1.0"
  skill-author: d41sys
---

# Structured Drafting

Turns loose material into a first draft that a reader can follow. The skill works from the reader backwards: who reads, what they already know, what they should walk away with. It then picks a shape, orders the blocks so nothing is used before it is explained, and drafts one block at a time. The draft is built from the author's material; gaps become questions, never inventions.

## When to use

- The author has notes, sources, a transcript, bullets, or a rough draft and wants a first draft or a restructure.
- The author wants an outline before any prose, or wants to write a document together, section by section.
- A draft exists but the order is wrong: points are used before they are explained, or the pieces could swap places unnoticed.

Not for: polishing sentence-level AI patterns (use `anti-slop-editing`); matching or building a personal voice (use `author-voice`); verifying claims, numbers and citations (use `evidence-grounded-writing`); a cold read of a finished draft (use `independent-review`); genre specifics for posts (`post-writing`), reports (`report-writing`), documentation (`technical-docs`), or CVs and letters (`career-documents`). For ML paper sections use `academic-writing`.

## Inputs

Read first: everything the author supplied (files, pasted text, links they named). Treat it as read-only; write the draft in a separate place.

Needed for the brief (fill from the request and material before asking anything):

- Reader: who, what they already know, what they will do with the piece.
- Purpose: the one thing they should understand, decide, or do afterwards.
- Constraints: channel, length, deadline, required sections, house template, language.

Ask at most 1-3 questions, and only when the answer changes the structure (for example, who the reader is, or which of two conflicting goals wins). Otherwise proceed and list the assumptions at the top of the brief. If the type of document is ambiguous, ask once rather than guess the form.

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
3. **Inventory the material.** Split the material into units and label each by kind (claim, example, datum, story, opinion, definition, quote) and by source (file, speaker, page, "author's head"). Note duplicates and contradictions. Write each gap the draft will need as a question (an example, a number, a counter-case), not as filler. See the mechanics in [shapes and blocks](references/shapes.md#material-inventory).
4. **State the core.** Write the main message in one or two sentences. Test it: could a knowledgeable reader sensibly argue the opposite, and where does it stop holding? If the core is a platitude, find the trade-off or the condition that makes it specific, using only what the material supports. If no core can be stated, say that and ask; do not outline around an inventory of topics.
5. **Build the grounding ledger.** List the concepts the reader already has (prerequisites) and the concepts the draft must introduce. Decide the prerequisite boundary from the reader in the brief: too high shuts people out, too low buries the opening in definitions. Order blocks so each block only leans on concepts that are already on the ledger. A block that needs an ungrounded concept gets a grounding block before it, or that concept is promoted to a stated prerequisite.
6. **Choose the shape.** Pick by purpose: argument, explanation, narrative, decision, or instruction (see [shapes](references/shapes.md)). Mixed purposes get a primary shape with a labelled secondary one. Do not impose one template on every task. If the document is a repackaging of a longer source, also decide how much of it is kept (default: keep everything that serves the purpose and say what was cut).
7. **Outline.** Use [the outline template](assets/outline-template.md). One line per block, each line a complete message, so that reading the lines alone tells the story. Give blocks unequal weight on purpose: more room for what is new or central, less for what the reader knows or can infer. Note for each block its source units and what it grounds.
8. **Test each block and decide keep/cut/merge.** For every block ask: what does the reader lose if this is removed? If nothing, cut it or fold it into a neighbour. Check that headings alone carry the argument, and that swapping two body blocks would break something. Record the decisions where the author can see them: kept, cut (with the reason), merged, and left over. Surplus material is expected; the piece ends when its argument is complete, not when the pile is used up.
9. **Draft block by block.** Per block: the message first (or when the shape needs a different order, such as a story that turns), then the evidence from the inventory, then a hand-off to the next block. Paraphrase, split or merge the material so the piece reads in one voice; quote only when the original wording is the point. Choose the form of each block deliberately (prose for reasoning, a list for parallel items, a table when the same fields repeat). Sentence-level craft is in [paragraphs and sentences](references/paragraph-and-sentence.md). When a block needs something the material lacks, insert `[ASK AUTHOR: ...]` or `[VERIFY: ...]` and keep going.
10. **Close and hand off.** Make the ending serve the reader's next need (a decision, an action, a verified result, an earned implication), not a template. Run the checks in [eval.md](eval.md). Then route: sentence-level polish to `anti-slop-editing`, voice to `author-voice`, factual and number checks to `evidence-grounded-writing`, a cold read to `independent-review`. If those skills are absent, apply the matching checks in eval.md yourself and say what was not checked.

## Rules

- **Brief before prose.** Without a reader and a purpose, every structural choice is a coin flip. Exception: for a tiny message the brief is two lines of thinking, not a form.
- **Reader path, not discovery path.** The order in which the author learned things is rarely the order the reader needs. Order by what the reader lacks. Exception: a narrative whose point is the discovery itself.
- **No invention.** Missing example, number, quote, source, credential, or opinion becomes a marker or a question. A slot the chosen shape expects but the material cannot fill (for example the recommendation in a decision piece) also becomes a marker, never a guess. Reason: an invented detail is a fabricated claim in the author's name. No exception.
- **One block, one message.** Two points need two blocks. Exception: a short list of genuinely parallel items can share a block.
- **Ground before use.** A concept used before it is introduced loses the reader, even if no jargon is visible. Exception: a deliberate hook that names a puzzle the piece will resolve, said to be a puzzle.
- **Shape follows purpose, not genre label.** The word "report" or "guide" does not give an outline. Exception: a venue or house template that fixes the structure; then gather material against that template.
- **Keep decisions visible.** Cut, merged, and left-over material is reported in a line or two. Reason: silent cuts erase things the author wanted; silent keeps bury the point.
- **Do not shuffle the author's claims.** Restructuring may reorder and merge; it must not strengthen, weaken, or drop qualifiers, numbers, names, or negations. Exception: the author asks for a stronger or softer claim.
- **Bridge only real relations.** Add connective tissue only where the relationship exists in the material. If it does not, report a missing through-line instead of papering over it.
- **Scale the process.** More stages are not more quality. If the author signals "just write it", write; list assumptions at the top.
- **Language.** Structure, grounding and evidence checks apply in any language. Lexical word lists and English sentence-position advice do not transfer automatically; when drafting in another language (for example Vietnamese), keep the structural stages and write sentence-level choices by that language's own norms.

## Output

Return, in this order, only the parts the task size calls for:

1. **Brief**, as filled fields with assumptions marked (omit for tiny tasks beyond a one-line restatement).
2. **Decisions**: kept / cut (reason) / merged / leftover, and the open questions the author must answer.
3. **Outline**: one line per block.
4. **Draft**, with `[ASK AUTHOR: ...]` and `[VERIFY: ...]` markers in place.
5. **Short note**: what the draft depends on that was not verified, and which sibling skill to run next.

Label the draft so it can be used as is (for example "Draft (ready to post)"); brief, decisions, outline and note are scaffolding for the author and never appear inside it. When the author cannot be asked, proceed with stated assumptions and markers instead of questions.

In co-author mode the deliverable is one section at a time, each followed by the next question, not the whole document.

## Examples

Outline lines that carry the story alone (a decision piece from meeting notes):

- Weak: "Background", "Options", "Discussion", "Next steps".
- Strong: "Support tickets doubled after the March release", "Three fixes were considered; two fail the staffing limit", "Recommend the smaller patch, reviewed in two weeks", "Decision needed by Friday; owner and trigger for revisiting".

Gap handling:

- Weak: adding "a recent survey found most users prefer shorter forms".
- Strong: `[ASK AUTHOR: one real example or number showing users abandon the long form]` and continue with the next block.

## Reference files

| File | Load when |
|---|---|
| [shapes.md](references/shapes.md) | Choosing a shape (stage 6), building block patterns, weighting blocks, doing the material inventory |
| [co-authoring.md](references/co-authoring.md) | The author wants to write together, the angle is open (explore mode), or the document is large |
| [paragraph-and-sentence.md](references/paragraph-and-sentence.md) | Drafting blocks (stage 9), or fixing paragraphs that read as lists of points |
| [brief-template.md](assets/brief-template.md) | Writing the brief (stage 2) |
| [outline-template.md](assets/outline-template.md) | Writing the outline and ledger (stages 5-8) |
| [eval.md](eval.md) | Before returning any output |
