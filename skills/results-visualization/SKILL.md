---
name: results-visualization
description: "Turns experiment and measurement results into publication-ready charts in one consistent paper style: method comparisons over rounds, clients or a parameter, cost or time breakdowns, confusion matrices, and per-group distributions such as samples per class on each client. Reads the numbers from result files, keeps each method's colour and marker the same across panels and figures, flags axes that exaggerate small gaps, and writes a caption that states the finding. Matches the author's own plotting template when one is given. Use when asked to plot, chart or visualise results, make figures for a paper, thesis, report or slides, redo figures in a house style, compare methods in a figure, or draw confusion matrices or data-distribution plots. Not for architecture or flow diagrams, dashboards, or decorative graphics."
license: MIT
metadata:
  version: "1.3"
  skill-author: d41sys
---

# Results visualization

A results figure answers one question a reader has, such as "does the proposed method stay ahead as clients grow?". Draw the comparison that answers it. Use numbers taken from the result files and a style that looks the same in every figure of the document.

## When to use

- Plotting results for a paper, thesis, report or talk: accuracy or loss over rounds, scores against a parameter, run-time or cost breakdowns, confusion matrices, class or sample distributions across clients or sites.
- Restyling existing figures so they share one look, or matching the author's own notebook or plotting script.
- Checking a draft figure for misleading axes, mismatched units or unreadable text.

For boxes-and-arrows diagrams use a diagram skill. For the table-or-figure decision inside a report, `report-writing` covers that choice. This skill takes over once a chart is the answer.

## Workflow

1. **Find the question and the source.**
   - Name the one comparison the figure must show and who reads it (paper reviewer, committee, slide audience).
   - Locate where the numbers live: CSV, JSON, logs, a results table, a notebook cell.
   - Read them from that source. When the only source is a table you must retype, copy it once into a CSV beside the script and check every value against the source before plotting.
   - Never invent, smooth or "fill in" a value. A missing run is a gap in the line or a `[ASK AUTHOR: …]` note, not an estimate.
2. **Find the house style.**
   - If the author has a plotting template (a notebook, a script, earlier figures from the same paper), read it and match its fonts, colours, marker per method, panel layout and label style. Report what you matched.
   - Otherwise use the bundled style in [scripts/plotstyle.py](scripts/plotstyle.py), described in [references/house-style.md](references/house-style.md).
3. **Choose the chart from the question.** Use [references/chart-choice.md](references/chart-choice.md). The common ones:
   - trend of several methods over rounds, clients or a parameter: line panels, one panel per setting (IID and non-IID, dataset A and B);
   - several methods compared at a few fixed settings (windows, datasets), often one panel per metric such as error and cost: grouped bars;
   - parts that add to a total (encryption, aggregation, decryption time): stacked bars;
   - per-class errors: confusion matrices, one per dataset, side by side;
   - how much data each group holds (samples per class per client): bubble matrix with a size key.
4. **Build it as a script.**
   - Write a short, rerunnable script or JSON spec next to the figure. Without an author template, build on `plotstyle.py`: render a JSON spec, or import it and call `apply_style`, `series_styles` and the chart helpers. Do not restyle by hand, so every figure gets the same look and the same warnings. The JSON format is in [references/spec-format.md](references/spec-format.md); `plotstyle.py` needs matplotlib and numpy (`uv run --with matplotlib --with numpy python …`).
   - When the figure lives in another project, copy `plotstyle.py` next to the figure script and import it from there. The figure must rebuild on a machine without this skill installed.
   - Give each method one colour, marker and line style and reuse that mapping in every panel and figure. The proposed method stands out; baselines stay quieter.
   - Size the figure for where it lands: a single paper column, the full page width, or a slide. Text must be readable at that printed size, not only on screen.
   - Save a vector PDF for the document and a 300-dpi PNG for review.
5. **Check before showing it.** Run [eval.md](eval.md). In particular:
   - units in axis labels match the data (a variable holding minutes must not be labelled seconds);
   - an axis cut to a narrow band, such as 0.997 to 1.000, is stated in the caption, because it makes tiny gaps look large;
   - bars start at zero;
   - colour is not the only cue on line charts (markers or line styles also separate the methods); bars that may be printed in greyscale get hatches;
   - every warning the script prints is fixed or stated in the caption.
6. **Write the caption and the sentence in the text.** The caption says what is plotted and what to notice, plus the setting the reader needs to read it: dataset, number of runs and what a band means when those are known. Facts you do not have go into the hand-over as `[ASK AUTHOR: …]`, not into the caption as an apology. The sentence in the body states the finding with the numbers that support it, and claims no more than the figure shows.
7. **Hand over.** Give the figure paths, the script or spec path, the data source of every series, and the checks still open.

## Rules

- **The data source wins.** If a number in the figure and the source disagree, the source is right and the figure is rebuilt. Note any value that was retyped instead of read.
- **One look per document.** Fonts, sizes, colours and the method-to-marker mapping stay fixed across figures. A reader who has learned "orange diamonds are ours" in Figure 3 should not relearn it in Figure 5.
- **Match the author's template before improving it.** Keep their look. Change it only where it misleads (wrong unit, unlabeled bubble sizes, colour hiding a small class), and say what you changed.
- **Axes are honest, and each panel still shows its point.** Bars and areas start at zero. Choose each panel's range from the comparison it carries. If the reader compares values across panels (method A in setting 1 against method A in setting 2), share the scale. If each panel's point is the order of methods within it, and one setting's gaps are a hundred times smaller than the other's, give that panel its own range: a shared scale would flatten it to one line. Name the ranges in the caption once ("note the different y-scales"); do not add sentences explaining what cannot be seen.
- **Show variation when it exists.** If several seeds or runs were made, plot mean with a band or error bars and say what the band is. Do not hide a run that went the other way.
- **Label for a reader without the code.** Axis titles in words with units ("Computation time (s per round)"), not variable names. Method names as they appear in the text. Panel letters (a), (b) match the caption.
- **Less ink, same facts.** No 3D, no shadows, no decorative colour, no legend that repeats a single series. Gridlines light.
- **Markers in prose and code comments** are only `[ASK AUTHOR: …]`, `[VERIFY: …]` and `[UNTESTED]`.

## Output format

- The figure files (PDF and PNG) and the script or spec that rebuilds them.
- A caption for each figure, and the one-sentence finding for the text.
- A short list: data source per series, style matched (template or house style), changes made to the author's template, warnings left in the caption.

## Resources

- [scripts/plotstyle.py](scripts/plotstyle.py): house style, method encodings, line, grouped-bar, stacked-bar, confusion and bubble helpers, honest-axis warnings, JSON spec rendering.
- [references/house-style.md](references/house-style.md): the style rules the script applies, and the presets for column, page and slide.
- [references/chart-choice.md](references/chart-choice.md): which chart answers which question, and the traps of each.
- [references/spec-format.md](references/spec-format.md): JSON spec format for rendering without writing Python.
- [eval.md](eval.md): pass/fail checks for a finished figure.
