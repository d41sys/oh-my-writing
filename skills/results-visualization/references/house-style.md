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

- Serif type, matching a LaTeX paper. With LaTeX installed, text is set by LaTeX (`text.usetex`). Without it, Computer Modern-like mathtext and a serif fallback.
- Axis titles and panel titles bold; tick labels and legend entries regular.
- Under LaTeX, bold needs `\textbf{…}` because the font-weight setting is ignored. `bold()` in the script handles both modes, and `plain()` escapes `%`, `&`, `#` and `_`.
- Math in labels uses `$…$`, for example `Encryption ratio ($\rho$)`.

## 2. Presets

| Preset | Width | Ticks / labels / titles (pt) | Use |
|---|---|---|---|
| `paper-single` | 3.5 in | 8 / 9 / 9.5 | one column of a two-column paper |
| `paper-double` | 7.16 in | 9 / 10 / 11 | full page width, two or three panels |
| `notebook` | 12 in | 18 / 20 / 22 | large on-screen figures, scaled down later |
| `slide` | 10 in | 16 / 18 / 20 | talks and posters |

Pick the preset for where the figure is printed. A 12-inch figure shrunk to one column turns 18-pt labels into about 5 pt.

## 3. Colour and method encodings

- Baselines take the tab10 palette in order (blue, green, red, purple…), skipping orange.
- The highlighted method, usually the proposed one, is orange with diamond markers and a dashed line, drawn on top.
- Each baseline also gets its own marker (square, circle, triangle…) and alternates solid and dashed lines. A greyscale print or a colour-blind reader can still tell the methods apart.
- `series_styles(names, highlight)` returns the mapping. Build it once per document from the full method list and pass the same list to every figure.

## 4. Panels

- Related settings sit side by side in one figure: (a) IID, (b) non-IID; or one confusion matrix per dataset.
- Panel titles carry the letter and the setting: `(a) IID`. The caption refers to the same letters.
- Panels that a reader compares across share the y-scale. When each panel's point is the order of methods within it and the gaps differ by orders of magnitude between settings, each panel gets its own range, and the caption names that once. A panel that shows only one flat line has failed.

## 5. Chart details

- **Lines:** light grid (alpha 0.3), x-limits set to the data, legend inside the plot where it covers no data.
- **Bars:** zero baseline, white edges between stacked parts, dashed horizontal grid only, legend order matching stack order.
- **Confusion matrices:** purple-red sequential map (`PuRd`), the count in every cell, predicted on x and true on y. Shading is by share of the true class, so a small class with errors is visible next to a large one. Use count shading only when classes are of similar size.
- **Bubble matrices:** one colour per row, area proportional to count, dash-dot grid, and a size key that shows what a bubble of each size means.
- **Frame:** black axes, no top-right removal tricks unless the template does it.

## 6. Export

- `save(fig, "figures/name")` writes `name.pdf` (vector, for LaTeX `\includegraphics`) and `name.png` (300 dpi, for review and slides). The bounding box is tight.
- Keep the script or spec next to the figure so the figure can be rebuilt when results change.
