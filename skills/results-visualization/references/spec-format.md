# JSON chart spec

Render a figure without writing Python:

```bash
uv run --with matplotlib --with numpy python scripts/plotstyle.py render spec.json --out figures/accuracy
```

The command writes `figures/accuracy.pdf` and `figures/accuracy.png` and prints each warning as `check: …`; fix it or state it in the caption. The exit code is 0 once the files are written, even with checks printed, and 2 when the spec is wrong (invalid JSON, a missing field, a missing or non-numeric CSV column). `--strict` exits 1 when checks were printed, for pipelines that must stop on them. `--preset` picks the size (`paper-single`, `paper-double`, `notebook`, `slide`); a `"preset"` field in the spec overrides it. `--no-tex` skips LaTeX text.

Paths to CSV files are relative to the spec file.

A missing value is `null` inline, or an empty or `NA` cell in a CSV. Lines and grouped bars draw a gap there and print a `check:` line, so the caption can say which run is missing. Stacked bars refuse a missing part, because the stack total would be wrong.

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

## Grouped bars

```json
{
  "type": "grouped_bars",
  "highlight": "Proposed",
  "value_labels": false,
  "panels": [
    {"title": "Error", "ylabel": "MAE (kWh/h)", "csv": "error.csv", "x": "window", "series": ["Baseline", "Proposed"]},
    {"title": "Cost", "ylabel": "Cost (k€)", "categories": ["W1", "W2"],
     "series": {"Baseline": [2.9, 1.4], "Proposed": [2.5, 1.5]}}
  ]
}
```

Methods sit side by side in each category. A panel takes `categories` and `series` inline, or a `csv` with `x` naming the category column.

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

One part gives plain bars. A panel can also read a `csv`: `x` names the category column and `series` lists the part columns.

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
