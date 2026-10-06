# Revising a Submitted Paper Against Reviewer Comments

Used when the input is a reviewed manuscript plus a response letter. Applies with "Revising an existing section" in SKILL.md: edit, do not rewrite.

## 1. Coverage matrix first
Before editing a section, list every reviewer comment that touches it: comment → requested item → where the manuscript answers it (sentence, table, figure) → status.
- **done**: the text or table exists; check that it says what the letter claims.
- **not run**: the analysis was not performed. Write one plain sentence in Limitations naming it as future work. Do not say it was "requested" (process leakage), and do not imply it was done.
- **needs author**: the answer needs a number or decision only the author has. Mark `[ASK AUTHOR]`; never fill it.
Every requested item ends in one of these three states before hand-off.

## 2. Provenance order for facts
1. Author confirmation in this conversation.
2. Code and logs from the account and environment that actually ran the experiments.
3. The previously submitted manuscript.

Ask who ran the experiments before reading code. A server account you can reach is not evidence of the environment that produced the results: software versions, hardware, and paths from a different user's account do not count. When code contradicts the manuscript on protocol (splits, thresholds, resampling), list it for the author with both options; do not silently keep the text and do not silently rewrite it into an admission.

## 3. Quote integrity with the response letter
The letter quotes manuscript sentences. Every edit to a quoted sentence is applied to the letter quote in the same pass, in every copy (Markdown, Word, and the duplicate text-box copy Word stores). Use `\ref`/`\eqref`, recompile, and only then update equation, table, and section numbers in the letter. Never edit the reviewer's own text in the letter.

## 4. Mark every change
Wrap every added or changed span in the revision macro (e.g. `\rev{}`), including the abstract and table cells. Deleted text cannot be colored; list deletions in the hand-off.

## 5. Claim and comparison checks that reviewers punish
- A caveat followed by a superlative is a zig-zag ("protocols differ … PRISM achieves the best overall performance"). After a cross-protocol caveat, report the numbers "within this reference comparison".
- Apply the relative-improvement rule (style.md) in the body too, with base rates; ablation and baseline paragraphs give the measured values instead of "clear degradation" or "substantially below".
- A figure or ratio named in the text is defined where it is first used (e.g. a separation ratio), in the code's terms.
- Comparisons of a full model against a baseline attribute the gain to the full objective, not to the components the authors prefer (bundled intervention).
- Name the checkpoint or configuration behind any qualitative figure or efficiency number when more than one exists.

## 6. External review in revision mode
Give the reviewer only sources the author has not overridden, and state which facts are author-confirmed. Otherwise every round re-reports settled provenance issues and spends the review on them instead of on prose.
