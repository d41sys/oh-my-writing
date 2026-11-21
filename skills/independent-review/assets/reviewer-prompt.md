Load when: writing the prompt for an independent reviewer (a fresh session, ideally a different model family), whether the author will send it or this skill runs it.

# Reviewer prompt

Write the prompt as a short brief from one person to another: plain sentences, built from the author's request and notes, in the author's words. It is not a form. A prompt that reads like a filled-in template gets a template review, and every line the notes do not support is an instruction nobody gave. The brief itself is usually 120 to 250 words; the document follows it.

## What goes in

In this order, each as a sentence or a short paragraph:

1. **What the document is and what is about to happen to it** ("a one-page set-up guide, about to go to stallholders").
2. **Who reads it**: what they know, what they do not, and how and when they get it. Take this from the notes and add no trait the notes do not give.
3. **What the reader has to do or decide after reading**, with its date when the notes give one.
4. **The question**, in the author's own words when the author asked one about the reader. If the author gave none: could this reader do that using only this document, and where would they go wrong?
5. **How to read it**, in two or three general sentences. First as that reader would, through what they would actually do, noting where they would get stuck, be misled or have to guess; that includes parts that disagree with each other, figures that do not add up, a weekday that does not match its date, and a step that needs something the reader does not have yet. Then as someone who has done this task many times and has shown newcomers how: what would that person make sure this reader knew before starting, and does the page say it? A beginner does not know what to ask, so an omission that could hurt them or waste their work counts even when no question names it. Keep both sentences general: name the experienced role by the task only, give it no list of things to check, and do not tailor either sentence to what you saw in the draft.
6. **What to send back**: the form and length the author asked for (a short list, a table, half a page). If the author did not say: the problems this reader would hit, worst first, each with a short quote, what goes wrong for the reader, and a fix when the page allows one. Always add the rule on missing facts: the reviewer uses what it knows to see what is missing or risky, never to fill the gap. When the reader needs something the page does not give (a limit, a time, a contact, a safety step), the reviewer names what the author must supply and does not state the value or the procedure itself. If nothing would stop or mislead the reader, the reviewer says so.
7. **The document**, whole, copied character for character under its file name, after the brief. Give a path instead only when it is too long to paste or is not text.

Add one sentence for each of these only when the request or the notes state it: sources the document must agree with (as paths the reviewer opens, never your summary), a rubric or the criteria the reader judges by, a limit the document must meet (word count, format, venue rule), the day the reader reads it when the text has dates without a year, and the review language when it differs from the document's. Never fill one from a guess, from today's date, or from what such documents usually need.

## What stays out

- What the writer wants, hopes or meant the text to do, and anything else about the writer, their organisation's disputes, process, tools or model.
- A summary or paraphrase of the draft written by you.
- Earlier versions, earlier findings, or a list of changes and fixes.
- Any hint of the verdict you want, and reassurance or warnings about weak spots, even as "check X carefully".
- Leading questions ("is the opening strong?", "isn't this clear?").
- A rule or warning that names a kind of gap you saw in the draft ("do not assume a form exists", "internal committee names"): it is a finding written in advance, however general it sounds.
- A named reviewer persona, a list of questions the reader must be able to answer, or a checklist, unless the notes give it. The reviewer reads as the reader and then as someone experienced in the task; neither role comes with a list.
- Lines for a machine: a model-id line, a language line, a fixed verdict line. They belong only to the run described under "When this skill runs the review".
- Confidential or unpublished material the owner has not cleared to leave this session (see step 3 of the skill).

## Example

Notes say: stallholders new to the market get this guide by email the week before; the author asks "could someone who has never traded here set up on time from this alone?" and wants a short list.

```
I'd like an independent read of the set-up guide below before it goes out to
stallholders.

The people who get it are trading at this market for the first time. It
arrives by email the week before their first Saturday, and they will set up
from it on the day without anyone to ask.

The question is: could someone who has never traded here set up on time from
this guide alone?

Please read it as one of them would, going through what they would actually
do from arriving to opening, and note anywhere they would get stuck, be
misled or have to guess. That includes parts that disagree with each other,
figures that do not add up, a weekday that does not match its date, and a
step that needs something they will not have yet.

Then read it once more as someone who has run a stall here for years and has
helped newcomers through their first morning. What would that person make
sure a first-timer knew before the day, and does the guide say it?

Send back a short list, worst first. For each item quote the line, say what
would go wrong for the stallholder, and suggest a fix if the guide itself
makes one possible. Use what you know to spot what is missing or risky, not
to fill it in: if the guide leaves out something they need, tell me what we
have to add and leave the times, rules and procedures to us, even ones you
are sure of. If nothing would trip them up, say so.

The guide (setup-guide.md):

<the whole guide, copied exactly>
```

## When this skill runs the review

When you send the prompt yourself and must record the result, add these two lines at the end of the brief, before the document. Leave them out of a prompt the author will send, unless the author asks for a verdict line.

```
Open your reply with one line: Reviewer-Model: <your own model id, or unknown>
End with one line saying how much of the document you read, then one line, exactly: VERDICT: ready | revise
```

Give the reviewer read-only access. If the reply has no `VERDICT:` line, or ends before it, treat it as `revise` and a failed review, and rerun it in a new session. If the reviewer read less than the whole document, the verdict covers only those parts. If a rubric was given, the reviewer scores each criterion with a reason.

## Variant: rejection memo (High depth, or after a review that approved everything)

Two separate sessions, neither the writer's. Each gets the same brief (reader, limits, sources) and the document. The writer's defence of the text is never given to either session.

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
