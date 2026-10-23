# JSON chart spec

Render a figure without writing Python:

```bash
uv run --with matplotlib --with numpy python scripts/plotstyle.py render spec.json --out figures/accuracy
```

The command writes `figures/accuracy.pdf` and `figures/accuracy.png` and prints each warning as `check: …`. The exit code is 0 when there are no warnings, 1 when warnings were printed, and 2 when the spec is wrong. `--preset` picks the size (`paper-single`, `paper-double`, `notebook`, `slide`). `--no-tex` skips LaTeX text.

Paths to CSV files are relative to the spec file.

## Lines

```json
{
  "type": "lines",
  "highlight": "Proposed",
  "panels": [
    {"title": "IID", "xlabel": "Number of clients", "ylabel": "Accuracy",
     "x": [10, 20, 30],
     "series": {"Baseline A": [0.91, 0.90, 0.88], "Proposed": [0.95, 0.95, 0.94]}},
    {"title": "Non-IID", "xlabel": "Number of clients", "ylabel": "Accuracy",
     "csv": "noniid.csv", "x": "clients", "series": ["Baseline A", "Proposed"],
     "ylim": [0.5, 1.0]}
  ]
}
```

A panel takes inline `x` and `series`, or a `csv` file with `x` naming a column and `series` listing columns. With more than one panel, the letters (a), (b) are added to the titles.

## Stacked bars

```json
{
  "type": "stacked_bars",
  "panels": [
    {"title": "Computation time", "xlabel": "Encryption ratio ($\\rho$)", "ylabel": "Time (s per round)",
     "categories": [1.0, 0.5, 0.2],
     "parts": {"Decryption": [2.0, 1.1, 0.5], "Aggregation": [8.0, 4.2, 1.6]}}
  ]
}
```

One part gives plain bars.

## Confusion matrices

```json
{
  "type": "confusion",
  "color_by": "row-share",
  "matrices": [
    {"title": "Dataset A", "labels": ["Normal", "Attack"], "matrix": [[950, 3], [7, 40]]}
  ]
}
```

`color_by` is `row-share` (default) or `count`.

## Bubble matrix

```json
{
  "type": "bubbles",
  "rows": ["Class 1", "Class 2"],
  "cols": [0, 1, 2],
  "counts": [[500, 20, 0], [40, 300, 90]],
  "xlabel": "Client",
  "ylabel": "Class"
}
```

`counts` has one row per entry in `rows`.
