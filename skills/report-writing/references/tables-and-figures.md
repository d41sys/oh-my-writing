Load when: choosing, building, captioning, or auditing a table, chart, or diagram in a report, or applying the report-specific Markdown rules in section 9.

# Tables and figures

A visual earns its place when it shows a relationship, distribution, or contrast that prose conveys less clearly. If it does not answer a specific question the reader has, use a sentence. A report must remain complete if every figure is removed; the key numbers are always also in the text or a table.

To build a chart from result data in a consistent paper style, with the plotting script and honest-axis checks, use the `results-visualization` skill when it is installed.

## Contents

- 1. Pick by the relationship shown
- 2. Chart forms to avoid or handle with care
- 3. Table craft
- 4. Time, forecasts, and scenarios in charts
- 5. Captions
- 6. Accessibility and honesty
- 7. Figure suggestion format
- 8. Diagrams as code
- 9. Document conventions in Markdown
- 10. Visual audit before delivery

## 1. Pick by the relationship shown

| The reader's question | Use | Notes |
|---|---|---|
| What are the exact values across several metrics or candidates? | Table | Best for lookup. Keep to about five columns; split or transpose otherwise |
| How do categories compare in size? | Bar chart, sorted | Horizontal bars for long labels or many categories; vertical for few. Start the axis at zero |
| How did something change over ordered time? | Line chart | Few series; label directly; mark forecast and breaks. Two points can be a sentence or a small table |
| What is the make-up of a whole? | Stacked bar, or a table for few parts; waterfall for a bridge | A pie is acceptable only with about three to six clearly different parts and a meaningful whole; group the tail into "Other" |
| How are two quantities related, or what is the trade-off? | Scatter, or a labeled 2 by 2 | Axes must be measurable and defined; see below |
| How is something distributed? | Histogram, or box plot (violin if shape matters) | Show the group sizes |
| Which scenarios and which period are history? | Line with a ribbon or separate scenario lines | See section 4 |
| How does one step lead to the next, or who talks to whom? | Flowchart, sequence diagram, timeline | Two or three linear steps are better as a numbered list |
| Do many candidates meet many criteria? | Matrix with cell statuses, optionally shaded | A heat shade must still carry text |
| How does one number reconcile to another (for example two market sizes)? | Bridge or waterfall | Show the gap |
| How are many small items distributed? | Small multiples with shared axes | Rather than one crowded frame |

If three or more things are compared across criteria, suggest a table. If it is one data point, use a sentence. If the relationship is already obvious in the text, skip the chart.

## 2. Chart forms to avoid or handle with care

- Pie or donut with many slices, near-equal slices, or no meaningful whole.
- Dual axes (a reader can make two lines cross anywhere); if two quantities truly have different units, say so and consider two panels.
- Three-dimensional effects and area scaling that implies precision it does not have (concentric circles for market sizes: use a table or nested bar).
- Radar charts for precise comparison; they suit only a rough shape of balanced capability.
- Unlabeled quadrant scores. A positioning map needs measurable, defined axes, the scoring rule, the evidence for each point, and what to do with unknowns. Never place firms by impression.
- Normalized heat color presented as density.
- Plotting differently defined values on one axis without normalizing and recording the conversion.
- Truncated axes on bar charts; if a large gap between groups hides the small ones, choose a stated remedy: a broken axis, a log scale for orders of magnitude, or a normalization when the claim is relative.
- Decorative imagery used as evidence, or sizing and placement of logos implying share.
- Treating projection or proximity as proof. Clusters or distances in reduced-dimension plots are descriptive only, and a multi-objective plot is an approximation of a trade-off.

## 3. Table craft

- **Units in header cells,** scope in the caption. Do not put a percent beside a currency unlabeled.
- Right-align numbers; left-align text; one precision per column; precision should not exceed the evidence.
- Mark the baseline row or the best value. Put baselines in the same table as the candidates (a result that cannot beat a simple baseline is not a positive result).
- Order rows by something meaningful (value, tier, time), not by arrival.
- Use real numbers where they exist; avoid vague cells ("fast", "moderate").
- Status cells use a fixed small vocabulary (for example yes, partial, no, unknown, not applicable). Unknown is never shown as no. Never rely on color alone; the text label must carry the meaning.
- If a metric has a direction (higher is better, lower is better), say so in the header.
- A table with more than about five columns on a narrow medium becomes unreadable: split it or flip it.
- Show missing values as missing, never as zero.
- Narrative does not belong in cells; interpretation goes below the table, one or two sentences per row that matters.

## 4. Time, forecasts, and scenarios in charts

- Separate observed from forecast with a boundary and a different line style plus label, not color alone.
- Label scenarios as conditional paths. Do not draw them as confidence bands unless a model supports it.
- Do not splice series from different definitions or vintages without a break marker; if history ends before the base year, identify the bridge estimate.
- Where revisions matter, show them or the vintage.
- For compound growth show start and end values and number of periods in the caption or text.
- For a market-size visual, prefer a table or nested bar. Show top-down and bottom-up estimates separately, the filters that take the total to the serviceable and obtainable parts, the horizon, downside and upside, and the reconciliation gap. State in the caption that the figures are conditional scenarios.
- Share charts state scope, metric, denominator, period, the unknown or residual share, and whether each figure is reported, estimated, or calculated. If the market definition is uncertain, show alternate definitions rather than one authoritative-looking chart.
- Survey charts need the unweighted base, population or frame, field dates and mode, weighting, and uncertainty (or why it is absent). Overlapping intervals do not prove two groups are equal.
- Regulatory timelines distinguish announced or consulted, enacted, effective, and stayed or repealed, using official dates, not news dates.

## 5. Captions

A caption lets a reader who sees only the figure grasp the finding. Name the finding, not the object.

- Weak: "Figure 2: Benchmark results."
- Better: "Figure 2: Median response time stays under 20 ms until about 5,000 requests per second, then rises as lock contention grows." (Illustrative wording and figures.)

Contents of a full caption: what is shown, scope (geography, population), period and as-of date, measure with unit and denominator, currency and base, observed-through date and the label for forecasts, source references, retrieval cutoff, and the limits that matter. Use plain verbs (shows, compares, summarizes); avoid showcase, boasts, highlights. Keep the title of the plotted quantity exact so direction is not misread. Do not hardcode "Table 1:" if the tool numbers captions.

## 6. Accessibility and honesty

- Color is never the only signal: use labels, direct labels on lines, patterns, and shapes. Avoid red against green alone.
- Provide alt text for each image, and the underlying data as a table when feasible. Keep text legible; check grayscale.
- Make sure values on a figure reproduce from a table the reader can see. Rounding in text and figure must match.
- Do not put identifiers, file paths, or confidential category names in figures.
- Label illustrative, synthetic, or hypothetical data on the figure.
- Without a chart renderer, deliver a Markdown table, a small text diagram, and a short description sufficient to build it by hand.

## 7. Figure suggestion format

When you propose a figure but cannot draw it, give the author enough to build it:

1. Title or finding it shows.
2. Type of chart or diagram.
3. Data and series, with units, source, and period.
4. Why it shows something prose does not.
5. Axes, scale choice, and annotations (baseline, forecast boundary, error bars only where multiple runs or variance exist).
6. A draft: a Markdown table or a diagram-as-code block.

Every major finding gets either a suggestion or a one-line reason none is needed. Recommend one or two best options rather than a menu.

## 8. Diagrams as code

Choose the most specific diagram type for the content: process or decision (flowchart), who talks to whom (sequence), lifecycle (state), roadmap (gantt), prioritization (quadrant), numeric trend (XY chart). Keep to one main direction, short labels (about three to six words), meaningful IDs, and a manageable size: if a diagram has more than about twenty nodes, split it into an overview and per-cluster detail. Give accessible title and description when the renderer supports them; otherwise add a visible text alternative. Meaning must survive without color.

## 9. Document conventions in Markdown

General Markdown conventions are owned by `technical-docs` (its Markdown conventions section). If that skill is not installed, use the standard ones: one H1, no skipped heading levels, sentence-case descriptive headings, sparing bold, parallel lists, meaningful link text, relative links for local files. The report-specific rules:

- Use short typed callouts for evidence that needs flagging (Observed, Calculation, Assumption, Limit, Warning), one to three lines, not nested. Prefer these to a generic "Key insight" box.
- A footnote or reference must actually support the claim, not merely sit near it.
- Use clean semantic Markdown while the draft is unfinished so evidence gaps stay visible to you. Elaborate formatting must not cover missing content.
- A section with a gap is finished before delivery by stating the gap plainly or cutting the claim; never substitute boilerplate to make a document look complete, and never ship a section with a marker or banner in it unless the author asked for a draft.

## 10. Visual audit before delivery

- Does each visual answer a named question, and could prose do it better?
- Is every value reproducible from a visible table?
- Are units, dates, and scope visible? Is missing data shown as missing?
- Are axes honest (zero baseline for bars, same scale across compared panels)?
- Are forecasts and history distinct, and scenarios labeled conditional?
- Does the caption state the finding and the source?
- Does it work in grayscale and for a screen-reader user?
- Does the report still make sense if the figures are removed?
