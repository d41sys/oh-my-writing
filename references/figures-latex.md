# Figures, Tables, LaTeX, English

## Figures
- Figure 1 carries the core idea or the strongest result; a skimmer should get the contribution from title + abstract + Figure 1.
- Caption alone explains what is compared and what to notice; ends with a period. Caption says what the figure is; the text says what it shows. Do not repeat one in the other.
- Caption and labels must match the text exactly (e.g., do not label "p=" what the text calls a "tail fraction").
- Vector output (PDF; `plt.savefig('x.pdf')`; pgfplots). No titles inside plots.
- In-figure font about body size, one font family, consistent across figures.
- ≤ 6 colors; one color family per module type; a darker/brighter module means "more important", so balance otherwise.
- Colorblind- and grayscale-safe: vary line style and marker, not only color; no red–green pairs.
- Diagrams: arrows flow one direction, no isolated boxes, same element type = same style, more drawing and less text.
- Tight margins; place figures at page top.

## Tables
- booktabs (`\toprule \midrule \cmidrule \bottomrule`); no vertical rules, no double rules, few horizontal rules.
- Caption above the table; caption covers setting/protocol/notation, not discussion.
- Metric direction in headers (Acc ↑, Err ↓); units; consistent decimals within a column; numbers right/decimal aligned, text left.
- One table, one message. Do not mix different dimensions (e.g., terminal outcome vs trace status) in one category axis; use a cross-tab.
- Make the intended comparison adjacent; repeat a baseline row if needed. Clarity beats elegance.
- Restrained highlighting of best / key rows only.
- Every percentage traceable to integer numerator/denominator; report "54/96 (56.3%)" when denominators vary.
- Sizing: `\small`/`\footnotesize`, `\setlength{\tabcolsep}{4pt}`, `p{2cm}`, `\multirow`, `\multicolumn`.

## Math
- Scalars lowercase italic; `\ell` instead of `l`; vectors `\mathbf{x}`/`\boldsymbol{\alpha}`; matrices `\mathbf{X}`; sets `\mathcal{X}`; number fields and expectation `\mathbb{R}`, `\mathbb{E}`; element and set symbols correspond.
- Multi-letter names upright: `\operatorname{softmax}`, `\mathrm{enc}`; use built-ins `\exp \log \max \arg`.
- `\left( \right)`, `\middle|`; `align` with `&=`; number only referenced equations.
- Equations are part of sentences: punctuate them (comma or period after); no colon before an equation ("the area is $A = \pi r^2$." not "the area is: ..."); text continuing the sentence starts lowercase.
- Shared macros in `math_commands.tex`; never reuse a symbol for two things.

## Citations and references
- `Figure~\ref{}`, `Table~\ref{}`, `Section~\ref{}`, `word~\cite{}` (non-breaking space; one space before citation).
- `\citet` when the citation is a sentence constituent; `\citep` when parenthetical. Never mix natbib with IEEE `\cite` styles.
- Published version over arXiv; no duplicate versions; consistent venue naming; fetch BibTeX from DBLP/CrossRef, never generate it (ARIS citation-audit).
- Name sub-panels "Figure~\ref{fig:x}(a)".
- Acronym with citation in one go: `proximal policy optimization \citep[PPO;][]{schulman2017ppo}`.
- `\usepackage[backref=page]{hyperref}` in drafts so readers jump from a reference back to where it is cited.

## English mechanics
- No contractions. "e.g.," and "i.e.," with commas; "et al." and "etc." at sentence end take no extra period; "etc." never for people.
- a/an by sound: "an LSTM", "an F1 score", "a U-Net".
- Hyphenated compound before a noun acts as adjective ("state-of-the-art method" vs "the state of the art").
- Field, task, and metric names lowercase (question answering, accuracy); model names exactly as their authors write them (BERT, not Bert).
- LaTeX quotes ``like this''; quotes only for so-called terms, italics for examples.
- Consistent heading capitalization.
- Last line of a paragraph under about 1/4 width: trim, or try `\looseness=-1`.

## Final hours
- Search the PDF for `??` and "Error"; every figure/table referenced in text, in order.
- Re-check copied numbers against result files; all formulas complete after edits.
- No figures past the page limit; page count exact.
- Anonymity: PDF metadata, acknowledgments, self-citations, supplementary code (paths, usernames, `.git`).
- Strip all LaTeX comments (`% TL;DR` notes, reviewer notes, cut text) before arXiv or camera-ready: arXiv publishes the source. `arxiv_latex_cleaner` or `latexpand --empty-comments` does it in one step.
- Title/abstract match the submission form; submit an early version a day before the deadline.
