# Results visualization: pass/fail checks

Run these on every finished figure. A failed check is fixed or, where it is a judgement call, stated in the caption.

## Data

1. Every plotted value can be traced to a named source file, table or log, and the hand-over lists that source per series.
2. Spot-check at least three values per figure against the source, including the largest and the smallest; all match.
3. No value is invented, interpolated or smoothed without saying so. Missing runs show as gaps or `[ASK AUTHOR: …]`.
4. Units in axis labels match the data as stored (minutes stay minutes; MB is not labelled GB).

## Honesty

5. Bars and stacked areas start at zero.
6. A zoomed axis (a narrow band such as 0.997–1.000) is stated in the caption with its range.
7. Every panel shows the comparison it is there for: no panel collapses into one indistinguishable line. Panels whose values the reader compares across share a scale; when they do not, the caption names the different scales once.
8. If several runs exist, the spread is shown and the caption says what it is and how many runs. If the run count is unknown, it is an `[ASK AUTHOR: …]` in the hand-over, not a caption sentence.
9. Every warning printed by `plotstyle.py` is fixed or stated in the caption.

## Style

10. When the author gave a template, fonts, colours, markers and layout match it, and every deliberate change is listed.
11. Each method keeps the same colour, marker and line style in every panel and figure.
12. On line charts, methods can be told apart without colour (marker or line style differs). Bar charts that may be printed in greyscale use hatches.
13. Text is readable at the printed size: tick labels at least about 7 pt at final width.
14. Axis titles are words with units, not variable names; method names match the text.
15. Panel letters match the caption.

## Words

16. The caption says what is plotted, the setting the reader needs (dataset, runs, what bands mean, when known), and what to notice. It carries no sentences about what the figure cannot show or what data was not supplied.
17. The body sentence states the finding with supporting numbers and claims nothing the figure does not show.

## Reproducible

18. A script or spec that rebuilds the figure sits next to it, and running it reproduces the files.
19. The figure is saved as vector PDF and 300-dpi PNG.
