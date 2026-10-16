# technical-docs eval

Answer each check pass or fail. Fix every failure before returning.

## Type and scope

1. Is the page type (tutorial, how-to, reference, explanation, or a named artifact such as README or PR body) decided and consistent with the reader's stated need?
2. Does the page serve one reader state, with material for other states moved into links instead of pasted in?
3. Is any inline rationale limited to a sentence that protects the reader from an error?
4. Does the page avoid describing its own edit history, except in a changelog, release note, migration guide or decision record?
5. Do links to the neighbouring page types exist where the reader would need them?

## Type contracts

6. If tutorial: is there one path with no optional tools or menus, a fixed environment, and an expected result after each step (or a statement that silence means success)?
7. If tutorial: does it open by saying what will be built, and close by saying what the learner has accomplished and where to go next?
8. If how-to: is the title "How to ..." with a single goal, prerequisites listed, real variations and likely failures covered, and no re-teaching of basics?
9. If reference: is every entry in the same layout, free of teaching, selling and design arguments, and shaped like the thing it describes?
10. If explanation: does it answer a "why" question with context, alternatives and trade-offs, tied to specific examples, without procedures or parameter tables?
11. If README: does it say what it is, why, and a quick start before anything else, and link into deeper pages instead of duplicating them?
12. If PR body: does it state what changed, why, evidence of before and after, door type and blast radius, and reviewer focus, with no preamble?
13. If changelog or release note: is every entry user-facing, grouped under consistent headings, with each breaking change stating what changed and what to do?
14. If code walkthrough: does it follow the execution path, with every file and range anchor checked, and explain reasons and gotchas instead of restating code?

## Truth and verification

15. Has every command and code sample been run, or marked `[UNTESTED]` with the reason?
16. Are versions and platforms stated, and taken from files rather than memory?
17. Does every path, flag, field, endpoint and status code mentioned exist in the source?
18. Are there any invented facts: endpoints, defaults, benchmarks, adoption numbers, quotes, or "supports X" claims the source does not show?
19. Are missing facts marked `[VERIFY: ...]` or `[ASK AUTHOR: ...]` rather than guessed?
20. Are test results reported as actual run results or "Not run", never implied?

## Form and safety

21. Is there one H1, no skipped heading levels, and descriptive headings?
22. Do all code fences carry a language tag, and are tables used for reference data with a header row and about five columns or fewer?
23. Do links use meaningful text and resolve?
24. Is the text free of absolute local paths, credentials, private hostnames and account names?
25. Are sentences short and active, with no filler openers and no marketing adjectives in reference or changelog text?
26. When editing existing docs, did you keep hand-written content and generated sections intact and report what changed?

## Final read

27. Could a new teammate follow the page without asking a question?
28. Read only the title and first paragraph: does the reader know what the page is, who it is for, and what to do first?
29. Does the closing note list what was verified, what is untested, and what is still open?
