Load when: sending a draft to an independent reviewer (fresh session, ideally a different model family).

# Reviewer prompt

Fill every required `{{placeholder}}`. A line marked *(optional)* stays only when the author's request or the material states its value; otherwise delete the whole line. Never fill it from a guess, from today's date, or from what such documents usually need. Send the text inside the fence as the reviewer's whole prompt, in a new session, with read-only access.

## Before you send

Check the filled prompt against this list. Remove anything that matches.

- A statement of what the writer wants, hopes, or meant the text to do.
- A summary or paraphrase of the draft written by you.
- Earlier versions, earlier findings, or a list of changes and fixes.
- Any hint of the verdict you want, or reassurance or warnings about weak spots.
- Leading questions ("is the opening strong?", "isn't this clear?").
- Anything about the writer's process, tools, or model.
- A rule or warning that names a kind of gap you saw in the draft ("do not assume a form exists", "internal committee names"): it is a finding written in advance, however general it sounds.
- An experienced-reader role that arrives with a list of things to check ("an accountant who will look at the VAT figures"): give the role only.
- Confidential or unpublished material the owner has not cleared to leave this session (see step 3 of the skill).

Allowed: who reads the text, what that reader knows and needs, the role of someone experienced in the task (the role only), the author's own question about what the reader can understand or do, what the reader must be able to answer after reading, a reading date and hard constraints (length, format, venue, house style) when the request or the material states them, sources the text must agree with, the rubric, and the output format below. Not allowed: the draft's known weak spots, even as "check X carefully"; derive the reader's questions from the reader's job, not from what you already see missing.

## The prompt

```
You are reviewing this document on behalf of its intended reader, as
{{EXPERIENCED_READER}} would: someone who knows this kind of task well and is
checking whether this reader, with only what they already know, could act on
the document safely and correctly. You have not seen how it was written.
Judge only what is on the page.

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
Hard constraints (optional): {{LENGTH_FORMAT_VENUE_STYLE_RULES}}
The reader reads this on (optional): {{READING_DATE}}
Review in this language: {{REVIEW_LANGUAGE}}

Open your reply with one line: Reviewer-Model: <your own model id, or unknown>

Do not edit any file or rewrite the document. Use what you know to see what is
missing or risky, never to fill a gap: when the reader needs a fact the page
does not give (a limit, a time, a contact, a safety step), say what the author
must supply; do not state the value or the procedure yourself.

1. Answer the review question above first, in one or two plain sentences.
2. Read the whole document once more for what a careful reader would catch:
   sections that disagree with each other, figures and totals that do not
   add up, a weekday that does not match its date, steps in an order the
   reader cannot follow, and steps that need something the reader will not
   have yet.
3. Then ask what someone experienced in this task would make sure this reader
   knows before starting, and whether the page says it. A beginner may not
   know to ask; an omission that could hurt them or waste their work is a
   problem even if no reader question names it.
4. List the problems this reader would actually hit, worst first: what stops
   them acting at all, then what makes them act wrongly, then what slows them
   down. For each, give a short exact quote (or the section), what goes wrong
   for the reader, and the smallest fix. A problem that one fix solves is one
   item, even if it shows in two places. A reader question the page does not
   answer is a problem in this list; so is a date without a year or a relative
   date the reading date cannot place. Call a full date past only after
   comparing its day, month and year with the reading date. Name date
   problems; do not repair them. A fix adds no fact the document does not
   contain; if something is missing, say what the author must supply. If
   sources were given, include anything that differs from them; if a rubric
   was given, score each criterion with a reason.
   Report only real problems. If none would make the reader act wrongly or
   stall, say "no critical or major findings".
5. Then one line: Read: <all of the document | the sections you read>
   Finish with one line, exactly:
   VERDICT: ready | revise
```

## Placeholder notes

| Placeholder | Fill with | Do not fill with |
|---|---|---|
| `WHO_THEY_ARE_AND_WHAT_THEY_ALREADY_KNOW` | role, background, vocabulary they have | what you wish they believed |
| `EXPERIENCED_READER` | a role, not a person: whoever normally does this task for this reader, trains them in it, or answers their questions about it ("a payroll clerk who handles new starters", "a shift supervisor who trains new staff") | a role followed by what to check, or a role chosen to match a weakness you saw in the draft |
| `READER_NEXT_ACTION_OR_DECISION` | the concrete act: approve, run, apply, reply | the conclusion you want them to reach |
| `REVIEW_QUESTION` | the author's own question about the reader, in the author's words, when it asks what the reader can understand or do from the page ("could a new volunteer do this from the page alone?"); if the author gave none: could this reader take the next action using only this document, and where would they go wrong? | a question that names a part of the draft or a suspected weak spot, the writer's hopes, or the verdict wanted |
| `READER_NEEDS` | three to five questions anyone in that role would ask before acting, in plain words, one per line (funding call: what it costs, what it commits us to, by when, how success is judged; instructions: what to have ready, what each step does, how to know it worked) | questions that name the draft's gaps, the writer's worries or an expected answer |
| `ARTIFACT_FILE_NAME` | the document's file name or path, so findings can be traced back to it | a description of the document |
| `ARTIFACT_TEXT_VERBATIM` | the whole document, copied character for character, so a reviewer in a new session needs none of your files. Only when it is too long to paste or is not text, replace the BEGIN/END block with its path and tell the reviewer to open it | an excerpt, a summary, or a tidied copy |
| `READING_DATE` | the day the reader reads the text, only when the request or the material fixes that day (a dated letter, a notice sent on a known day) and the text has dates without a year or relative dates; when readers get it on different days or nobody states the day, delete the line, and the reviewer flags relative dates it cannot place | today's date by default, the date you are working, or a guess |
| `LENGTH_FORMAT_VENUE_STYLE_RULES` | limits the author or the material states: word or page limit, format, venue, house style | rules you think suit the genre or the reader ("plain English", "keep it short") |
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
