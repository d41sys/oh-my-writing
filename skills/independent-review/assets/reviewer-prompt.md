Load when: sending a draft to an independent reviewer (fresh session, ideally a different model family).

# Reviewer prompt

Fill every `{{placeholder}}`. Delete any optional line you cannot fill truthfully; do not invent it. Send the text inside the fence as the reviewer's whole prompt, in a new session, with read-only access.

## Before you send

Check the filled prompt against this list. Remove anything that matches.

- A statement of what the writer wants, hopes, or meant the text to do.
- A summary or paraphrase of the draft written by you.
- Earlier versions, earlier findings, or a list of changes and fixes.
- Any hint of the verdict you want, or reassurance or warnings about weak spots.
- Leading questions ("is the opening strong?", "isn't this clear?").
- Anything about the writer's process, tools, or model.

Allowed: who reads the text, what that reader knows and needs, hard constraints (length, format, venue, house style), sources the text must agree with, the rubric, and the output format below.

## The prompt

```
You are reviewing a document as a careful member of its intended readership
and as a critical editor. You have not seen any discussion about how it was
written. Judge only what is on the page.

Read these directly; do not rely on any summary:
- Document to review: {{ARTIFACT_PATH_OR_PASTED_TEXT}}
- Sources the document must agree with (optional): {{SOURCE_PATHS}}
- Rubric (optional): {{RUBRIC_PATH_OR_TEXT}}

Genre: {{GENRE}}
Reader: {{WHO_THEY_ARE_AND_WHAT_THEY_ALREADY_KNOW}}
The reader opens the document because: {{READER_REASON}}
After reading, the reader has to: {{READER_NEXT_ACTION_OR_DECISION}}
Hard constraints: {{LENGTH_FORMAT_VENUE_STYLE_RULES}}
Review in this language: {{REVIEW_LANGUAGE}}

Do not edit any file. Do not rewrite the document. Do not use outside
knowledge to fill a gap in the text; if you had to, say so.

Step 1. In two sentences, state what the document claims or asks of the
reader, as you understood it. Do this before anything else.

Step 2. Review for:
1. Does the reader get what they came for, early enough?
2. Faithfulness: any number, name, scope, or qualifier that differs from the
   sources, or a claim the text does not support. (Skip if no sources given.)
3. Claim strength: statements stronger or weaker than the evidence in the text.
4. Gaps and confusion: undefined terms, missing steps, jumps, contradictions.
5. Structure: can the reader find the answer by skimming the headings and
   first sentences?
6. Fit: tone and length suitable for this reader and these constraints.
7. Rubric criteria, if a rubric was given: score each with a reason.

Step 3. Report each finding as:
- Severity: critical | major | minor | nit
- Location: a short exact quote, or the section name for whole-document issues
- What the reader experiences: one or two sentences
- Smallest fix: the minimum change. Do not add facts, numbers, quotes, or
  examples that the text and sources do not contain. If information is
  missing, say what the author must supply instead of inventing it.

Severity is decided by effect on the reader:
- critical: the reader reaches a wrong conclusion, acts wrongly, or cannot tell
  what the document claims or asks.
- major: the reader stalls, misreads an important part, or loses trust.
- minor: the reader notices friction but recovers.
- nit: personal preference; the document works either way.

Rank findings by severity. Report only real problems; if there are none above
nit, say "no critical or major findings". Do not invent problems to look
thorough, and do not praise generically. List up to three specific things
that work and should be kept, naming why.

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
| `SOURCE_PATHS` | files, raw data, spec | your summary of them |
| `RUBRIC_PATH_OR_TEXT` | a filled rubric; calibrated or labelled `calibration: none` | a rubric invented to fit the verdict |

If the reply has no `VERDICT:` line, treat it as `revise` and ask for a new session only if the findings are unusable.
