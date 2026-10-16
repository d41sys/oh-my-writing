Load when: testing whether a reader with no background gets the main point, before or alongside an independent review.

# Fresh-reader prompt

The reader sees the text and, optionally, one line about who it is for. Nothing else: no summary, no purpose statement, no earlier versions, no hint about weak spots. The reader is not asked to judge quality or rewrite anything; it reports what happened to it while reading.

## Preparation (you, before sending)

1. Write down, privately and in a file the reader cannot see, what a real reader should take away in two sentences, and which 3 to 10 questions a real reader would bring to the text. Mix retrieval questions ("what is the deadline?") with application questions ("given X, what should I do?"). The count is a guide, not a quota; short texts need fewer.
2. Write test questions so they do not contain the answer and do not hint at the section where it sits.
3. Start a fresh session. Send only the prompt below, with the text.

## The prompt

```
You are a reader of the document below. {{OPTIONAL_ONE_LINE_ABOUT_WHO_THIS_READER_IS}}
You have no other information about it. Read it once, in order, as a real
reader would. Do not use outside research. If you rely on your own knowledge
to understand something, mark it "(my knowledge)".

Do not rewrite the text and do not give general quality opinions. Report what
happened while you read:

1. Main point. In at most two sentences: what is this document telling me or
   asking me to do?
2. After reading. What would I believe, decide, or do next?
3. Stalls. List each place you slowed down, misread, or had to guess. For each:
   a short quote, what was unclear, and what you guessed.
4. Assumed knowledge. List terms, acronyms, steps, or background the text takes
   for granted without giving.
5. Contradictions. List places where the text disagrees with itself, or where
   a term seems to change meaning.
6. Next questions. List up to three questions you would ask the writer next,
   in the order you would ask them.
7. Stopping point. If you would have stopped reading before the end, say where
   and why.
{{OPTIONAL_TEST_QUESTIONS_BLOCK}}
```

Optional test-questions block, added after item 7:

```
8. Answer each question below using only the document. Give the answer, the
   quote it comes from, and any wording you found unclear. If the document does
   not say, write "not stated". Questions:
   {{QUESTION_LIST}}
```

## After the run (you)

1. Compare the reader's main point with your private two-sentence version: match, partly, or misses. A miss on a stated goal is a text defect even if every individual sentence was understood.
2. Compare the reader's next questions with the questions you expected. Unexpected questions point to gaps; expected questions that the text should have answered point to order problems.
3. Sort each stall and each "not stated" answer: text defect (fix), audience boundary (the brief says the reader already knows this; no change), reader limitation (the reader was wrong although the text was clear; no change), or question outside the document's scope (no change).
4. Do not paste your analysis back to the reader or ask it to defend answers; that contaminates the session. To test a fix, start another fresh session with the revised text.
5. Done when a fresh reader restates the main point correctly and raises no new text defects. Cap at two rounds by default.

Limits: this test finds missing context and unclear structure. It does not show that facts, figures, proofs or advice are correct.
