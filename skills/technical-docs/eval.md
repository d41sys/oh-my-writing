# technical-docs eval

Answer each check pass or fail. Fix every failure before returning.

## Type and scope

1. Is the page type (tutorial, how-to, reference, explanation, or a named artifact such as README, PR body, commit message or ADR) decided and consistent with the reader's stated need?
2. Does the page serve one reader state, with material for other states moved into links instead of pasted in?
3. If the request mixed types (for example a tutorial that also asks for every option), did you write one page per type and link them, or, only on the user's explicit wish for one file, keep clearly labeled sections and say it is a compromise?
4. Is any inline rationale limited to a sentence that protects the reader from an error?
5. Does the page avoid describing its own edit history, except in a changelog, release note, migration guide, commit message or decision record?
6. Do links to the neighbouring page types exist where the reader would need them, and does every linked page exist or get created with real content (no stubs)?

## Type contracts

7. If tutorial: is there one path with no optional tools or menus, a fixed environment, and an expected result after each step (or a statement that silence means success)?
8. If tutorial: does it open with one sentence in the first person plural that says what we will build or do ("In this guide we will ..."), and close by saying what the learner has accomplished and where to go next?
9. If how-to: is the title "How to ..." with a single goal, prerequisites listed, real variations and likely failures covered, and no re-teaching of basics?
10. If reference: is every entry in the same layout, free of teaching, selling and design arguments, and shaped like the thing it describes? For a CLI or script: are streams, files written or overwritten, and exit codes stated as the code behaves?
11. If explanation: does it answer a "why" question with context, alternatives and trade-offs, tied to specific examples, without procedures or parameter tables?
12. If README: does it say what it is, why, and a quick start before anything else, and link into deeper pages instead of duplicating them?
13. If PR body: does it state what changed, why, evidence of before and after, a `Door:` line (two-way or one-way) and a `Blast radius:` line naming who or what breaks, reviewer focus only where the notes name a place to read slowly, no mention of rollout mechanisms the change lacks, no preamble, the title as the first line of the file, and a title that describes the change in about 70 characters or fewer?
14. If commit message: is the subject imperative, specific and about 50 characters (72 at most), with a body that gives the cause rather than restating the diff?
15. If ADR: do all three conditions hold (hard to reverse, surprising without context, real trade-off), and are context, options, decision and consequences present, with negatives listed and every reason taken from the author or the repo?
16. If changelog or release note: is every entry user-facing, grouped under consistent headings, with each breaking change stating what changed and what to do?
17. If code walkthrough: does it follow the execution path, with every file and range anchor checked, and explain reasons and gotchas instead of restating code?

## Truth and verification

18. Has every command and code sample been run? If not, is it left out of the page or described in plain words as not run (never marked with a tag in the page), with the reason in the reply?
19. Are versions and platforms stated, and taken from the source files rather than memory or your own test environment (that version goes in the reply, not the page)?
20. Does every path, flag, field, endpoint and status code mentioned exist in the source (including each flag and default in a README or CLI page)?
21. Are there any invented facts: endpoints, defaults, benchmarks, adoption numbers, quotes, install steps, or "supports X" claims the source does not show?
22. Is the page free of `[ASK AUTHOR]`, `[VERIFY]` and `[UNTESTED]` markers, TODO or TBD text, empty template slots and meta-notes (process narration such as "as requested" or "I ran", per-paragraph source notes, `[source: ...]` tags)? Is every missing fact stated plainly as a gap in the material ("No license is stated in this repository.") or omitted, never filled in? Do the author's questions appear only as `[VERIFY: ...]`, `[ASK AUTHOR: ...]` or `[UNTESTED]` lines in the reply (and in `open-questions.md` when files are written)? Exception: the author asked for a draft, or the output is an author-facing artifact (a comment review, a staleness report).
23. Are test results reported as actual run results with the scope the author gave, or "Not run", never implied (no "all tests pass" or "CI is green" without a result)?
24. Does every "never", "always" or "at most" match the code's order of operations and edge cases, and is a changed default called out as a behaviour change?
25. Do numbers come from the source or the change, with any conversion shown, and is no new figure (a sum, ratio or total) used where naming the source's own parts would do?

## Form and safety

26. Is there one H1, no skipped heading levels, and descriptive headings?
27. Do all code fences carry a language tag, and are tables used for reference data with a header row and about five columns or fewer?
28. Do links use meaningful text and resolve?
29. Is the text free of absolute local paths, credentials, private hostnames and account names?
30. Are sentences short and active, with no filler openers and no marketing adjectives in reference, changelog or commit text?
31. When editing existing docs, did you keep hand-written content and generated sections intact and report what changed?

## Final read

32. Could a new teammate follow the page without asking a question?
33. Read only the title and first paragraph: does the reader know what the page is, who it is for, and what to do first?
34. Does the closing reply list what was verified, what is untested, and what is still open, and does `open-questions.md` hold the same open lines when files were written?
35. Does the page read as one colleague wrote it (the author's person and register, plain transitions, no signposting, prose for a few items), with each default, limit or "not run" stated once at its line, and no empty or invented section in a short page such as a small PR body?
