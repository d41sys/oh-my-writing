# Shapes, blocks and material inventory

Load when: choosing a shape for a draft, building the block pattern, weighting blocks, taking the material inventory, or deciding how much of a longer source to keep.

Contents: [Material inventory](#material-inventory) | [Core test](#core-test) | [Choosing a shape](#choosing-a-shape) | [The five shapes](#the-five-shapes) | [Combining and repackaging](#combining-and-repackaging) | [Weight, openings, endings](#weight-openings-endings) | [Form of a block](#form-of-a-block) | [Gain test](#gain-test)

## Material inventory

Goal: know exactly what you have, where each piece came from, and what is missing, before choosing any order.

1. Read the whole pile first, end to end. Do not outline from the first third.
2. Split into units: one claim, example, datum, story, opinion, definition, or quote per unit. A unit stays small enough to be placed in exactly one block.
3. Label each unit with its kind and its source (file and place, speaker and time, or "author's head" when it was said in conversation and has no document). The source label is what later lets a reviewer check a claim.
4. Mark duplicates (keep the clearest), contradictions (do not resolve silently; keep both values with their sources and ask, or state in the draft that the material does not settle which is right when the author cannot be asked), and units that only make sense to the author. For notes and transcripts also mark status: decided, proposed, unconfirmed, open. A hedge ("about", "I think", "if legal agrees") stays attached to its unit.
5. Group by the reader's questions, not by where the material came from. A draft that mirrors the order of the sources is a summary of the sources, not an answer to the reader.
6. List the gaps: the example the argument needs but the pile lacks, the number a claim implies, the counter-case, the definition. Write each as a question. A gap is filled by the author, a real source, or a cut; never by a plausible-sounding addition. In the draft a gap that stays open is stated plainly or left out ([gaps in the draft](gaps-in-the-draft.md)).
7. Note what was normalised: facts already supported by the material, items that still need checking, and open questions. Do not restart analysis from zero when the author already supplied findings.

Inventory line format (one per unit; the inventory is author-facing, so source labels and `ask author` stay here and never enter the draft):

```
U7 | example | "Nightly job failed 3 times in April" | source: ops-notes.md, entry 12 | status: supported
U8 | opinion | "We should drop the manual review" | source: author, call | status: author's view, label as such
U9 | gap   | need: cost of one failed run | ask author
```

For small tasks the inventory is a mental pass; show it only when units conflict or gaps matter.

## Core test

State the core in one or two sentences before outlining. A usable core is a position with a condition, not a topic and not a consensus line.

- Negation test: could a knowledgeable person reasonably argue the opposite? If the opposite is absurd ("monitoring matters"), the core is a platitude. Look for the trade-off, the condition, or the number in the material that makes it specific.
- Boundary test: where does it stop being true? A core with no boundary is usually broader than the evidence.
- Shift test (for arguments): what changed that makes this claim worth making now?
- Size test: if it needs three sentences and an "and also", the piece may be two pieces, or the core is not yet found.
- Change test: what does the piece change about what the reader currently believes or will do? If nothing, there is no reason for the piece yet; look for the tension in the material. If the material holds none, say so and use the plain message of the segment instead of inventing a hook.

If the material cannot support a specific core, say so. Offer the nearest supported core and ask; do not manufacture novelty or drop inconvenient material to force a tidy line.

## Choosing a shape

Pick by what the reader must do with the piece, then use the matching block pattern. The document label (report, guide, post) is not the shape.

| Reader job | Shape | Signal words in the request |
|---|---|---|
| Be persuaded or take a position seriously | Argument | "make the case", "why we should", op-ed, position, proposal rationale |
| Understand how something works or why | Explanation | "explain", explainer, background, mechanism |
| Follow what happened and what it meant | Narrative | story, case study, incident, postmortem, journey |
| Choose between options or approve something | Decision | recommendation, memo, "should we", proposal, brief for a leader |
| Do something and succeed | Instruction | how to, guide, setup, runbook, tutorial |

When the label and the reader job disagree, the reader job wins. A "report" for an approver is a decision piece; a "report" for an archive is closer to explanation with navigation. When the request is truly ambiguous, ask one question.

## The five shapes

Each pattern lists blocks in default order, weight, the usual failure, and the ending that fits. Reorder when the material demands it, and record why.

### Argument

Blocks: tension or problem the reader recognises -> the claim (the core, stated early) -> strongest reason with evidence -> second reason or the mechanism -> the best objection, answered honestly -> boundary (where the claim stops) -> implication.
Weight: most room to the reasons and the objection; little to background the reader already has.
Failure: a list of points that could be reshuffled; objections invented only to knock them down; claims stronger than the evidence.
Ending: the implication the argument has earned for what the reader does or believes.

### Explanation

Blocks: the question or confusion -> the simplest working picture of the mechanism -> one concrete worked example -> how it behaves at the edges, or where people go wrong -> when it applies and when it does not.
Weight: most room to the worked example and the edge cases; a short top picture.
Failure: definitions in a pile before any example; an analogy standing in for the mechanism instead of pointing at it; every concept explained at the same depth.
Ending: when to use it and when not to, or the next thing the reader can now understand.

### Narrative

Blocks: situation and stakes -> what was tried or expected -> the turn (surprise, failure, discovery) -> consequence -> what it changes for the reader, stated only as far as the events support.
Weight: most room to the turn; set-up as short as comprehension allows.
Failure: chronology for its own sake; meaning announced instead of shown; invented scenes, quotes or feelings.
Ending: the last event or the lesson the events support. If the material gives no lesson, stop at the last event.

### Decision

Blocks: the decision and its deadline -> the recommendation -> why (the two or three reasons that decide it) -> options considered and why each loses -> risks and what would change the recommendation -> what is needed from the reader, by whom, by when.
Weight: most room to the reasons and rejected options; the recommendation up front, readable in half a minute.
Failure: background first and the answer last; "it depends" with no recommendation; options listed without a verdict; an audit trail missing, so the reader cannot see why alternatives lost.
Ending: owners, dates, and the trigger to revisit. Keep deeper evidence below the recommendation or in an appendix for specialists.

### Instruction

Blocks: outcome and who this is for -> prerequisites -> numbered steps, each with a check that tells the reader it worked -> common failures and fixes -> where to go next.
Weight: even across steps; extra weight on the step where people usually fail.
Failure: skipped steps, "..." in place of commands, explanations tangled into the steps, no way to tell success from failure.
Ending: the verification that the whole thing works, then the next task.

If the request mixes teaching a newcomer with serving an expert lookup, use `technical-docs`; it separates these on purpose.

## Combining and repackaging

- **Mixed readers.** Layer the piece: outcome first, one sentence of mechanism, then deeper sections specialists can jump to. Put implementation detail below or in an appendix, not in the lead.
- **Mixed shapes.** Choose a primary shape for the spine and label secondary blocks (for example an instruction piece with one explanation block). Do not interleave shapes block by block.
- **Repackaging a longer source** (transcript, report, long post into an article). Decide, and tell the author, how much is kept. Defaults, not rules: a faithful long-form keeps nearly all of it; a formal report keeps the summary, findings, data, limits and recommendations and trims derivations; an explainer keeps the mechanism and examples; a decision brief keeps the recommendation, key facts and trade-offs; an essay keeps the argued line. Name must-keep items (each pointing to a place in the source) and may-cut items (each with a reason) so that the kept share matches what was declared. Never compress silently, and never let a reduced version read like a shrunken copy; an edited article has its own order. Compression must not turn an opinion or a guess into a stated fact, and a paraphrase is never presented as a transcript. For dialogue sources keep speakers explicit and do not alter what a speaker meant when trimming filler.
- **Fixed templates and venues.** When structure is fixed, skip shape choice: gather the material against the template and use the block tests as a revision pass.

## Weight, openings, endings

- **Uneven on purpose.** Decide which section carries the piece and which is a short bridge. Shrink what the reader knows or can work out; expand what is surprising or central. If every section has the same size and internal pattern, the emphasis is invisible. Any percentage split is a working heuristic, not a quota.
- **Openings by purpose.** Decision: the call and the deadline. Instruction: the outcome and prerequisites. Argument or post: a concrete tension from the material, or the claim itself. Narrative: the situation at the moment it mattered. Research-type writing: the specific problem and what is not yet known. Never open with a sweeping statement that could precede any piece in the field, or with a fact the author did not supply.
- **Endings by next need.** Decide what the reader does or believes next and end there. Cut closers that only pretend to conclude, recaps in short pieces, engagement questions that serve a template rather than the reader, and forward-looking lines with nothing checkable in them. Add a call to action or discussion question only when the author wants one and it serves a real next step.
- **Name the central idea.** If the conversation keeps circling an idea, offer a plain word or phrase for it; prefer an existing word. A coinage costs definition space and must be grounded where it first appears.

## Form of a block

Choose each block's form deliberately.

- Prose carries reasoning and cause. A list carries parallel items only. A run of bullets that are not really parallel is a structural problem: say so, and recast as prose when the author's scope allows restructuring.
- Use a table when the same fields repeat for several items (a working threshold is three or more); otherwise prose with a bold lead-in per item.
- Put a tip or warning in a callout only when leaving it inline would derail the main line.
- Quote when the exact wording is the point; paraphrase when only the idea matters.
- Real lists stay lists: steps, parameters, feature comparisons, changelog entries.
- Formatting never replaces the argument: bulleted claims still need the connecting logic.

## Gain test

Apply to the whole piece and to each block.

- Whole piece: what does this give the reader that they cannot get quickly elsewhere (original material, a real example, a clearer answer, a decision, a position)? If the author cannot name it, ask before writing a long piece.
- Each block: what does the reader lose if it is removed? "Nothing" means cut or merge. "A transition" means shorten to one sentence inside a neighbour.
- Reshuffle: swap two body blocks. If nothing breaks, the blocks are a list; find the through-line (usually a question the previous block raises) or reorder.
- Drift: does the ending deliver what the opening promised? If the piece drifted, change the opening or re-thread the blocks.
- Skeleton read: read the headings or block lines only, as a reader who lacks your context. The main argument should still be graspable.
