# House style

The default look for result figures. `scripts/plotstyle.py` applies it with `apply_style(preset)`. If the author has their own plotting template, match that instead and use this page only to fill gaps.

## Contents

1. Type
2. Presets
3. Colour and method encodings
4. Panels
5. Chart details
6. Export

## 1. Type

- Computer Modern **Sans** for words: axis titles, panel titles, legend and tick labels set in text. With a complete LaTeX install (latex, dvipng and the cm-super fonts), text is set by LaTeX (`text.usetex`) in its sans family, and tick numbers on line charts come out in Computer Modern maths digits. Otherwise, including a partial install such as BasicTeX, a sans fallback with Computer Modern maths.
- Axis titles and panel titles bold; tick labels and legend entries regular.
- Under LaTeX, bold needs `\textbf{…}` because the font-weight setting is ignored. `bold()` in the script handles both modes.
- Math in labels uses `$…$`, for example `Encryption ratio ($\rho$)`.
- Under LaTeX, `%`, `&`, `#`, `_` and `€` are escaped outside `$…$` only, so math keeps its subscripts. `€` uses the eurosym package when installed, because Computer Modern has no euro glyph.

## 2. Presets

| Preset | Width | Ticks / labels / titles (pt) | Use |
|---|---|---|---|
| `paper-single` | 3.5 in | 8 / 9 / 9.5 | one column of a two-column paper |
| `paper-double` | 7.16 in | 9 / 10 / 11 | full page width, two or three panels |
| `notebook` | 12 in | 18 / 20 / 22 | large on-screen figures, scaled down later |
| `slide` | 10 in | 16 / 18 / 20 | talks and posters |

Pick the preset for where the figure is printed. A 12-inch figure shrunk to one column turns 18-pt labels into about 5 pt.

## 3. Colour and method encodings

- Soft "deep" palette: blue `#4c72b0`, orange `#dd8452`, green `#55a868`, red `#c44e52`, purple `#8172b3`, then brown, pink, grey, olive, cyan. No seaborn needed; the hex values are in `plotstyle.DEEP`.
- Baselines take the palette in order, skipping its orange: blue, green, red, purple…
- The highlighted method, usually the proposed one, is plain orange `#ffa500`, with diamond markers and a dashed line on line charts, drawn on top.
- Stacked parts take the palette in order, orange included (blue, orange, green).
- Bubbles use tab10 at 70% opacity on white, which gives the light pastel look.
- On line charts each baseline also gets its own marker (square, circle, triangle…) and alternates solid and dashed lines, so a greyscale print or a colour-blind reader can still tell the methods apart. Bars are plain fills with white edges; pass `hatch=True` (spec `"hatch": true`) when the figure may be printed in greyscale.
- `series_styles(names, highlight)` returns the mapping. Build it once per document from the full method list and pass the same list to every figure.

## 4. Panels

- Related settings sit side by side in one figure: (a) IID, (b) non-IID; or one confusion matrix per dataset.
- Panel titles carry the letter and the setting: `(a) IID`. The caption refers to the same letters.
- Panels that a reader compares across share the y-scale. When each panel's point is the order of methods within it and the gaps differ by orders of magnitude between settings, each panel gets its own range, and the caption names that once. A panel that shows only one flat line has failed.

## 5. Chart details

- **Lines:** light grid (alpha 0.3), x-limits set to the data, legend inside the plot where it covers no data. A share such as accuracy stops at 1.0 instead of padding past it.
- **Bars:** zero baseline, white edges, dashed horizontal grid only. Stacked bars keep the legend in stack order. Grouped bars share one legend across panels and draw a zero line when values go negative. Value axes from 1,000 up use thousands separators, matching the value labels.
- **Confusion matrices:** purple-red sequential map (`PuRd`), the count in every cell, predicted on x and true on y. Shading is by share of the true class, so a small class with errors is visible next to a large one. Use count shading only when classes are of similar size.
- **Bubble matrices:** one colour per row, area proportional to count, dash-dot grid, and a size key that shows what a bubble of each size means.
- **Frame:** black axes, no top-right removal tricks unless the template does it.

## 6. Export

- `save(fig, "figures/name")` writes `name.pdf` (vector, for LaTeX `\includegraphics`) and `name.png` (300 dpi, for review and slides). The bounding box is tight.
- Keep the script or spec next to the figure so the figure can be rebuilt when results change.
