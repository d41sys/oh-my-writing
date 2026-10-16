# Gaps in the draft

Load when: drafting (stage 9) and the material lacks something a block needs, or two values conflict, or before returning any draft.

Contents: [What is author-facing](#what-is-author-facing) | [Gap to wording](#gap-to-wording) | [open-questions.md](#open-questionsmd) | [Meta-notes](#meta-notes-stay-out) | [Draft for the author to edit](#draft-for-the-author-to-edit)

A gap is something the material does not say. The draft the reader gets states it as a fact about the material, or leaves the sentence out. The author's question goes to the reply and, for a saved file, to `open-questions.md`. Nothing is filled with a plausible guess.

## What is author-facing

| Artifact | Audience | Markers and source labels |
|---|---|---|
| brief, decisions, outline with grounding ledger, material inventory | the author, shown in the reply | allowed (`[ASK AUTHOR]`, `from: U7`) |
| skeleton returned when there is no material | the author; it is not a draft | allowed |
| co-author mode: brainstorm lists and curation notes | the author, in conversation | allowed |
| the draft, the saved file, a drafted section in co-author mode | the reader | none |

If the outline is saved to a file for the author, it is a separate file from the draft.

## Gap to wording

Pick the wording that fits the genre. State only what the material supports; the statement is about the material or the work, never a reason you made up.

| Gap | In the draft (reader language) | In the reply and `open-questions.md` |
|---|---|---|
| missing number, example or quote | omit the sentence, or "The notes do not give the number of failed uploads." | `[ASK AUTHOR: how many uploads failed in March?]` |
| missing recommendation or decision | "No option has been chosen yet; the team needs to pick one by the date in the notes." | `[ASK AUTHOR: which option do you recommend?]` |
| unconfirmed item | keep the status: "The vendor may help; it has not replied." | `[ASK AUTHOR: has the vendor replied?]` |
| two values for one thing | both values with who gave each, "the interview does not settle which is right"; nothing computed from either | `[ASK AUTHOR: which baseline is right, 30% or 25%?]` |
| claim that needs an outside check | state it as the material states it, attributed ("the vendor says ..."), or omit it | `[VERIFY: vendor's quoted price against the current list]` |
| missing credential, citation or source | omit the claim, or attribute it to the person who said it | `[ASK AUTHOR: source for the 2021 benchmark?]` |
| something not done, in a paper-style piece | "We did not evaluate X." / "X is outside the scope of this study." | `[ASK AUTHOR: was X evaluated anywhere?]` |
| the one question the email can put to its recipient | ask it in the email, in plain words ("Are you happy for legal to see the draft first?") | none, unless the author must also decide |

Rules of thumb:

- A short deliverable that cannot support a section drops the section and says so in the reply; padding to fill it is invention.
- Do not explain why the gap exists ("the author did not provide ...", "the notes were incomplete"). State the fact the reader can use.
- A gap statement keeps the same strength as the material: "not yet confirmed" stays "not yet confirmed".
- When many gaps remain, the piece may be too thin to ship; say so in the reply instead of writing around every hole.

## open-questions.md

Write it beside the saved draft when at least one question is open. Same items, same numbering, as in the reply.

```markdown
# Open questions: upload-failures update

1. [ASK AUTHOR: which fix do you recommend?]
   Blocks: the "What we need" paragraph. The update says: "No option has been chosen yet."
2. [VERIFY: the vendor's role against its reply, once received]
   Blocks: the third paragraph. The update says: "The vendor may help; it has not replied."
```

## Meta-notes stay out

None of these belongs in the saved draft; they go in the reply:

- process narration: "based on your notes", "as requested", "I summarised", "here is a draft";
- source tags and per-block source lists (`[source: notes.md]`, `(from U7)`); attribute inside the prose only where the source matters (a conflict, an opinion, an unconfirmed item);
- outline lines, block labels, brief fields, decision lists;
- comment lines (`%` in LaTeX, `<!-- -->` in Markdown) that hold outline or source notes: the working outline stays in the reply, not in the file.

## Draft for the author to edit

Only when the author asks for a draft to mark up (for example "give me a draft with the gaps flagged"): leave `[ASK AUTHOR: ...]` and `[VERIFY: ...]` in place at the gap, still write `open-questions.md`, and say in the reply that the file is a draft with open markers. Source tags and process narration stay out even then.
