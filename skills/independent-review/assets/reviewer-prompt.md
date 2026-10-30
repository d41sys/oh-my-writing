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
- A rule or warning that names a kind of gap you saw in the draft ("do not assume a form exists", "internal committee names"): it is a finding written in advance, however general it sounds.
- Confidential or unpublished material the owner has not cleared to leave this session (see step 3 of the skill).

Allowed: who reads the text, what that reader knows and needs, the author's own question about what the reader can understand or do, what the reader must be able to answer after reading, the reading date, hard constraints (length, format, venue, house style), sources the text must agree with, the rubric, and the output format below. Not allowed: the draft's known weak spots, even as "check X carefully"; derive the reader's questions from the reader's job, not from what you already see missing.

## The prompt

```
You are one of this document's intended readers, reading it carefully before
you have to act on it. You have not seen how it was written. Judge only what
is on the page.

Document to review ({{ARTIFACT_FILE_NAME}}), copied exactly:

BEGIN DOCUMENT
{{ARTIFACT_TEXT_VERBATIM}}
END DOCUMENT

Read these directly; do not rely on any summary:
- Sources the document must agree with (optional): {{SOURCE_PATHS}}
- Rubric (optional): {{RUBRIC_PATH_OR_TEXT}}

Reader: {{WHO_THEY_ARE_AND_WHAT_THEY_ALREADY_KNOW}}
After reading, the reader has to: {{READER_NEXT_ACTION_OR_DECISION}}
The question this review answers: {{REVIEW_QUESTION}}
Questions the reader must be able to answer from the page (optional):
{{READER_NEEDS}}
Hard constraints: {{LENGTH_FORMAT_VENUE_STYLE_RULES}}
The reader reads this on: {{READING_DATE}}
Review in this language: {{REVIEW_LANGUAGE}}

Open your reply with one line: Reviewer-Model: <your own model id, or unknown>

Do not edit any file or rewrite the document. Do not fill a gap from outside
knowledge; if you had to, say so.

1. Answer the review question above first, in one or two plain sentences.
2. List the problems this reader would actually hit, worst first: what stops
   them acting at all, then what makes them act wrongly, then what slows them
   down. For each, give a short exact quote (or the section), what goes wrong
   for the reader, and the smallest fix. A problem that one fix solves is one
   item, even if it shows in two places. A reader question the page does not
   answer is a problem in this list; so is a date without a year, or one
   already past on the reading date (name it, do not repair it). A fix adds no
   fact the document does not contain; if something is missing, say what the
   author must supply. If sources were given, include anything that differs
   from them; if a rubric was given, score each criterion with a reason.
   Report only real problems. If none would make the reader act wrongly or
   stall, say "no critical or major findings".
3. Then one line: Read: <all of the document | the sections you read>
   Finish with one line, exactly:
   VERDICT: ready | revise
```

## Placeholder notes

| Placeholder | Fill with | Do not fill with |
|---|---|---|
| `WHO_THEY_ARE_AND_WHAT_THEY_ALREADY_KNOW` | role, background, vocabulary they have | what you wish they believed |
| `READER_NEXT_ACTION_OR_DECISION` | the concrete act: approve, run, apply, reply | the conclusion you want them to reach |
| `REVIEW_QUESTION` | the author's own question about the reader, in the author's words, when it asks what the reader can understand or do from the page ("could a new volunteer do this from the page alone?"); if the author gave none: could this reader take the next action using only this document, and where would they go wrong? | a question that names a part of the draft or a suspected weak spot, the writer's hopes, or the verdict wanted |
| `READER_NEEDS` | three to five questions anyone in that role would ask before acting, in plain words, one per line (funding call: what it costs, what it commits us to, by when, how success is judged; instructions: what to have ready, what each step does, how to know it worked) | questions that name the draft's gaps, the writer's worries or an expected answer |
| `ARTIFACT_FILE_NAME` | the document's file name or path, so findings can be traced back to it | a description of the document |
| `ARTIFACT_TEXT_VERBATIM` | the whole document, copied character for character, so a reviewer in a new session needs none of your files. Only when it is too long to paste or is not text, replace the BEGIN/END block with its path and tell the reviewer to open it | an excerpt, a summary, or a tidied copy |
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
