Load when: sending a draft to an independent reviewer (fresh session, ideally a different model family).

# Reviewer prompt

Fill every `{{placeholder}}`. Delete any optional line you cannot fill truthfully (sources, rubric, reading date); do not invent it. Send the text inside the fence as the reviewer's whole prompt, in a new session, with read-only access.

## Before you send

Check the filled prompt against this list. Remove anything that matches.

- A statement of what the writer wants, hopes, or meant the text to do.
- A summary or paraphrase of the draft written by you.
- Earlier versions, earlier findings, or a list of changes and fixes.
- Any hint of the verdict you want, or reassurance or warnings about weak spots.
- Leading questions ("is the opening strong?", "isn't this clear?").
- Anything about the writer's process, tools, or model.
- Confidential or unpublished material the owner has not cleared to leave this session (see step 3 of the skill).

Allowed: who reads the text, what that reader knows and needs, what the reader must be able to answer after reading, the reading date, hard constraints (length, format, venue, house style), sources the text must agree with, the rubric, and the output format below. Not allowed: the draft's known weak spots, even as "check X carefully"; derive the reader's questions from the reader's job, not from what you already see missing.

## The prompt

```
Read the document below as one of the readers it is written for, and as a
critical editor. You have not seen how it was written. Judge only what is on
the page.

Read these directly; do not rely on any summary:
- Document to review: {{ARTIFACT_PATH_OR_PASTED_TEXT}}
- Sources the document must agree with (optional): {{SOURCE_PATHS}}
- Rubric (optional): {{RUBRIC_PATH_OR_TEXT}}

Genre: {{GENRE}}
Reader: {{WHO_THEY_ARE_AND_WHAT_THEY_ALREADY_KNOW}}
The reader opens the document because: {{READER_REASON}}
After reading, the reader has to: {{READER_NEXT_ACTION_OR_DECISION}}
The reader needs to be able to answer: {{READER_NEEDS}}
Hard constraints: {{LENGTH_FORMAT_VENUE_STYLE_RULES}}
The reader reads this on: {{READING_DATE}}
Review in this language: {{REVIEW_LANGUAGE}}

Open your reply with one line: Reviewer-Model: <your own model id, or unknown>

Do not edit any file or rewrite the document. Do not fill a gap from outside
knowledge; if you had to, say so.

1. The decision. In two sentences, say what the document asks of the reader.
   Then say whether this reader could act on it as written: yes, only after
   the changes below, or no. Give the reason in one sentence.
2. Findings, the one that most affects that decision first, at most seven.
   For each: a short exact quote (or the section name), what the reader would
   get wrong or be unable to do, and the smallest fix. Mark each critical
   (the reader acts wrongly or cannot tell what is asked), major (stalls,
   misreads or loses trust), minor (friction they recover from) or nit
   (taste). Look for: a reader question answered late or not at all; a
   number, name or qualifier that differs from the sources; a claim stronger
   or weaker than its evidence; an undefined term, jump or contradiction;
   length or tone that does not fit the constraints. Flag a date without a
   year or one already past on the reading date; do not repair it.
3. Questions for the author: only facts missing from the page whose answers
   would change the reader's decision. Never supply them yourself, and keep
   them apart from edits the author can make without new facts.

If a rubric was given, score each criterion with a reason. If nothing rises
above nit, write "no critical or major findings". Do not invent problems to
look thorough, and do not praise generically.

Before the verdict, one line: Read: <all of the document | the sections you read>.
Finish with one line, exactly:
VERDICT: ready | revise
```

## Placeholder notes

| Placeholder | Fill with | Do not fill with |
|---|---|---|
| `GENRE` | post, report, README, cover letter... | the writer's own label for tone or ambition |
| `WHO_THEY_ARE_AND_WHAT_THEY_ALREADY_KNOW` | role, background, vocabulary they have | what you wish they believed |
| `READER_REASON` | the question or task bringing them to the text | the writer's goal |
| `READER_NEXT_ACTION_OR_DECISION` | the concrete act: approve, run, apply, reply | the conclusion you want them to reach |
| `READER_NEEDS` | three to five questions anyone in that role would ask before acting, in plain words (funding call: what it costs, what it commits us to, by when, how success is judged; instructions: what to have ready, what each step does, how to know it worked) | questions that name the draft's gaps, the writer's worries or an expected answer |
| `READING_DATE` | today's date, when the text has dates without a year or relative dates; otherwise delete the line | a guess |
| `SOURCE_PATHS` | files, raw data, spec | your summary of them |
| `RUBRIC_PATH_OR_TEXT` | a filled rubric; calibrated or labelled `calibration: none` | a rubric invented to fit the verdict |

If the reply has no `VERDICT:` line, or ends before it, treat it as `revise` and a failed review, and rerun it in a new session. If the `Read:` line names less than the whole document, the verdict covers only those parts.

## Variant: rejection memo (High depth, or after a review that approved everything)

Two separate sessions, neither the writer's. Use the same header block as above (reader, constraints, sources). The writer's defence of the text is never given to either session.

Session 1, the attacker:

```
You are a senior reviewer who has decided to recommend rejecting the document.
Write the strongest case for rejection in about 200 words, from what is on the
page and in the sources only. Quote the passage behind each attack. Do not
invent problems and do not attack the author. If no case survives a careful
reading, write "no case for rejection" and stop.
```

Session 2, the adjudicator (not a defender): give it the document, the sources, and the attacker's memo verbatim.

```
For each attack in the memo, decide: answered by the text (quote where),
partly answered (say what is missing), or unresolved (say what evidence or
decision would resolve it). Judge the document and the memo; do not argue for
either side. Finish with one line: VERDICT: ready | revise
```

Unresolved attacks go through triage like any finding. The memo is a stress test, not a rewrite order: an attack that needs evidence the material lacks becomes a needs-author question in the findings (`[ASK AUTHOR: ...]`; findings are author-facing) or a stated limit, not an invented answer and never a marker inside the text.
