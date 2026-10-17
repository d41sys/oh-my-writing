# anti-slop-editing eval

Answer each check pass or fail. Fix every failure before returning.

## Mode and scope

1. Did you work in the mode the user asked for (or `edit` by default), and say so when you assumed it?
2. In `detect` mode, is the source text left unrewritten and byte-identical (any saved report written to a separate file), and free of an authorship verdict?
3. Did every change stay inside the scope the user authorized, with untouched paragraphs left exactly as they were?
4. If the text needed no justified edit, did you say so and return it unchanged instead of making cosmetic changes?

## Findings quality

5. Does every finding quote the exact span, name the pattern, and say what it costs the reader?
6. Did you check each candidate against its exception (technical sense, genre norm, deliberate rhetoric, author habit) before calling it a finding?
7. Are findings ranked by impact and grouped by shared cause, with weak single hits left out or labelled as judgment calls?
8. Did you avoid padding the report with "scanned, nothing found" categories or invented concerns?
9. Did you leave alone the habits the author shows in their own text or sample (dashes, fragments, hedges, asides, bold)?
10. Did you avoid treating a count (dashes, bullets, bold, word hits) as a target to reach?
11. Did you leave a genuine question to the reader, a real label ("Result: 42 ms", "Steps to reproduce:") and an FAQ alone, and cut only staging such as "The best part?", "Here's the thing:", "Plot twist:" or a question answered at once?

## Preservation

12. Do all claims, scope words, numbers with units, names, dates and conditions in the source still appear in the output, unless a justified finding or a requested change removed them?
13. Are negations, certainty levels and hedges the same as in the source, with no hedge deleted that the claim needs and none added?
14. Are causal links, ordering, ranking and attribution unchanged, including after any merged or split sentences?
15. Are quotes, citations, code, inline code, URLs, paths, frontmatter and data tables byte-identical, unless the user asked to change them?
16. Did you add nothing new: no fact, number, quote, source, experience, reaction, opinion, stake or confidence that the source or the user did not provide?
17. Where a fix needed a missing fact, did you leave the original span or cut it (listed in What changed), without inventing a value and without a marker in the edited text, and put the question in the reply as an `[ASK AUTHOR: ...]` or `[VERIFY: ...]` line?
18. Did you delete without a question only framing that asserts nothing checkable (a staged setup, "a testament to", a bare value claim), keep the fact such framing rode on, and list each removed span in What changed?
19. Did you run the two-way check (what was lost, what was added) and tie every changed span to a finding or a requested change?
20. In `edit` and `rewrite` mode, is the edited text free of gap markers (`[ASK AUTHOR]`, `[VERIFY]`, `[UNTESTED]`), notes to the author, process narration ("I removed", "as requested") and `[source: ...]` tags, with gaps left as written or cut, and every question in the reply (also in `open-questions.md` beside a saved file)? Exception: the user asked for a draft to edit.

## Voice and no new fingerprint

21. Would the author still recognize their voice, with register, rhythm and quirks intact?
22. Did you avoid swapping stock words for other stock words, adding staccato fragments, forced slang or invented asides?
23. Did you vary your fixes so the edit does not repeat one new formula?

## Honesty of the report

24. Does the What changed list match the delivered text, with no phrase listed as removed that is still present?
25. Does the report say which checks did not run, labelling reading-only checks as model-only, and call a clean script run "no mechanical errors" rather than "meaning verified", without padding the report with process claims the reader cannot use?
26. Are residuals (kept, protected, source-blocked, pass limit) listed with a one-line reason each?
27. Did you stay within two editing passes, and state how many were used and why you stopped?
28. For non-English text, did you skip the English word lists and say that lexical lists do not transfer?
29. Did the output avoid any claim or hint about who wrote the text?

## Reads like a person

30. Does the output avoid adding what the audit removes: no new headings, lists, bold, transitions or repeated caveats, no point stated twice, and the author's person and register kept? In `detect`, does the reply answer what was asked in plain sentences, without a severity scheme, an editing plan or a summary the user did not need?

## Final read

Read the result once as the author. Would they accept every change, find nothing of theirs missing, and see nothing they did not say? If any answer is no, go back and fix it.
