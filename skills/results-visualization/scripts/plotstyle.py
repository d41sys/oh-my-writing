#!/usr/bin/env python3
"""Paper-style result charts: one house style, consistent method encodings, honest-axis warnings.

Python use:
    import plotstyle as ps
    ps.apply_style("paper-double")                      # or "paper-single", "notebook", "slide"
    fig, warnings = ps.method_lines(panels, highlight="Ours")
    ps.save(fig, "out/accuracy")                         # out/accuracy.pdf and out/accuracy.png

Command line (renders a JSON spec; see references/spec-format.md):
    python plotstyle.py render spec.json --out out/fig1 [--preset paper-double] [--no-tex]

Needs matplotlib and numpy (for example `uv run --with matplotlib --with numpy python plotstyle.py ...`).
Every helper returns (figure, warnings); warnings are things a reader could misread, to fix or state in the caption.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
import numpy as np  # noqa: E402

PRESETS = {
    # width in inches, then tick, label and title sizes in points
    "paper-single": {"width": 3.5, "tick": 8, "label": 9, "title": 9.5},
    "paper-double": {"width": 7.16, "tick": 9, "label": 10, "title": 11},
    "notebook": {"width": 12.0, "tick": 18, "label": 20, "title": 22},
    "slide": {"width": 10.0, "tick": 16, "label": 18, "title": 20},
}
MARKERS = ["s", "o", "^", "v", "P", "X", "<", ">"]
LINESTYLES = ["-", "--", "-.", ":"]
# The soft "deep" palette (seaborn's default) used by the author's notebook; no seaborn dependency needed.
DEEP = ["#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b3", "#937860", "#da8bc3", "#8c8c8c", "#ccb974", "#64b5cd"]
HIGHLIGHT_COLOR = "#ffa500"  # plain orange: the proposed method stands out against the soft baselines
BUBBLE_ALPHA = 0.7  # tab10 at 70% on white, the template's pastel bubbles
HIGHLIGHT_MARKER = "D"
CONFUSION_CMAP = "PuRd"
ZOOM_SHARE = 0.02  # a y-range narrower than this share of its top value makes small gaps look large

_STATE = {"preset": "paper-double", "tex": False}


def tex_available() -> bool:
    return bool(shutil.which("latex"))


def apply_style(preset: str = "paper-double", tex: bool | None = None) -> dict:
    """Serif type, bold labels and titles, light grid, black frame. LaTeX text when installed (or forced)."""
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}; choose from {', '.join(PRESETS)}")
    p = PRESETS[preset]
    use_tex = tex_available() if tex is None else tex
    matplotlib.rcParams.update(matplotlib.rcParamsDefault)
    matplotlib.use("Agg")
    plt.rcParams.update({
        "text.usetex": use_tex,
        # Computer Modern Sans for words (LaTeX \sffamily); tick numbers stay in Computer Modern maths digits
        "font.family": "sans-serif",
        "font.sans-serif": ["Computer Modern Sans Serif", "CMU Sans Serif", "DejaVu Sans"],
        "mathtext.fontset": "cm",
        "font.size": p["tick"],
        "axes.labelsize": p["label"],
        "axes.titlesize": p["title"],
        "axes.labelweight": "bold",
        "axes.titleweight": "bold",
        "xtick.labelsize": p["tick"],
        "ytick.labelsize": p["tick"],
        "legend.fontsize": p["tick"],
        "axes.edgecolor": "black",
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.6,
        "lines.linewidth": 2.0 if p["width"] > 6 else 1.4,
        "lines.markersize": 6 if p["width"] > 6 else 4,
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "savefig.bbox": "tight",
        "savefig.dpi": 300,
    })
    # Computer Modern has no euro glyph; textcomp's fallback draws a broken one, so use eurosym when installed
    euro = r"\euro{}" if use_tex and _has_tex_package("eurosym") else r"\texteuro{}"
    if use_tex:
        plt.rcParams["text.latex.preamble"] = r"\usepackage{textcomp}" + (
            r"\usepackage{eurosym}" if euro == r"\euro{}" else "")
    _STATE.update(preset=preset, tex=use_tex, euro=euro)
    return dict(p, tex=use_tex)


def _has_tex_package(name: str) -> bool:
    kpse = shutil.which("kpsewhich")
    if not kpse:
        return False
    found = subprocess.run([kpse, f"{name}.sty"], capture_output=True, text=True)
    return bool(found.stdout.strip())


TEX_ESCAPES = {"%": r"\%", "&": r"\&", "#": r"\#", "_": r"\_", "°": r"\textdegree{}"}


def _tex_escape(text: str) -> str:
    """Escape LaTeX specials outside $...$ only, so math such as $\\rho_1$ keeps its subscript."""
    parts = text.split("$")
    escapes = dict(TEX_ESCAPES, **{"€": _STATE.get("euro", r"\texteuro{}")})
    for k in range(0, len(parts), 2):  # even parts are outside math
        parts[k] = "".join(escapes.get(ch, ch) for ch in parts[k])
    return "$".join(parts)


def bold(text: str) -> str:
    """Bold label text in either mode (LaTeX ignores fontweight, so it needs \\textbf)."""
    if not text:
        return text
    if _STATE["tex"]:
        return r"\textbf{" + _tex_escape(text) + "}"
    return text


def plain(text: str) -> str:
    """Tick and legend text, escaped for LaTeX when it is on."""
    if _STATE["tex"] and text:
        return _tex_escape(text)
    return text


def _thousands(ax) -> None:
    """Thousands separators on the value axis once values reach 1,000, matching the value labels."""
    if max(abs(v) for v in ax.get_ylim()) >= 1000:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))


def figsize(panels: int = 1, aspect: float = 0.42) -> tuple[float, float]:
    """Preset width split across panels; height follows the aspect of one panel row."""
    w = PRESETS[_STATE["preset"]]["width"]
    return w, max(w * aspect, 1.6) if panels > 1 else max(w * aspect * 1.2, 1.6)


def series_styles(names: list[str], highlight: str | None = None) -> dict[str, dict]:
    """One fixed look per method, so a method looks the same in every panel and every figure of a paper.
    The highlighted method (usually the proposed one) gets orange diamonds and is drawn on top."""
    palette = [c for k, c in enumerate(DEEP) if k != 1]  # deep without its orange, which is the highlight's
    styles, k = {}, 0
    for name in names:
        if name == highlight:
            styles[name] = {"color": HIGHLIGHT_COLOR, "marker": HIGHLIGHT_MARKER, "linestyle": "--", "zorder": 5}
            continue
        styles[name] = {"color": palette[k % len(palette)], "marker": MARKERS[k % len(MARKERS)],
                        "linestyle": LINESTYLES[k % 2], "zorder": 3}
        k += 1
    return styles


def zoom_warning(values, ylim, where: str) -> str | None:
    """A y-axis cut to a sliver of its scale makes a small gap look large; the caption must say so."""
    lo, hi = ylim
    top = max(abs(hi), abs(lo), 1e-12)
    if lo > 0 and (hi - lo) / top < ZOOM_SHARE:
        spread = max(values) - min(values)
        return (f"{where}: y-axis spans {lo:g} to {hi:g} ({(hi - lo) / top:.1%} of its top value); the largest gap "
                f"shown is {spread:.4g}. State the range in the caption or add a full-scale inset.")
    return None


def _letter(i: int, title: str | None) -> str:
    if not title:
        return ""
    return title if title.lstrip().startswith("(") else f"({chr(97 + i)}) {title}"


def method_lines(panels: list[dict], highlight: str | None = None, legend: str = "best"):
    """Side-by-side line panels comparing methods over a shared x (rounds, clients, ratio...).
    Each panel: {"title", "x", "series": {name: values}, "xlabel", "ylabel", optional "ylim", "xlim"}."""
    names = list(dict.fromkeys(n for p in panels for n in p["series"]))
    if highlight and highlight in names:
        names = [n for n in names if n != highlight] + [highlight]
    styles = series_styles(names, highlight)
    fig, axes = plt.subplots(1, len(panels), figsize=figsize(len(panels)), squeeze=False)
    warnings = []
    for i, (ax, panel) in enumerate(zip(axes[0], panels)):
        x = panel["x"]
        for name in names:
            if name not in panel["series"]:
                continue
            y = panel["series"][name]
            if len(y) != len(x):
                raise ValueError(f"panel {i + 1}, {name}: {len(y)} values for {len(x)} x points")
            ax.plot(x, y, label=plain(name), **styles[name])
        ax.set_xlabel(bold(panel.get("xlabel", "")))
        ax.set_ylabel(bold(panel.get("ylabel", "")))
        if panel.get("title"):
            ax.set_title(bold(_letter(i, panel["title"]) if len(panels) > 1 else panel["title"]), pad=8)
        ax.set_xlim(*(panel.get("xlim") or (min(x), max(x))))
        values = [v for n in names if n in panel["series"] for v in panel["series"][n]]
        if panel.get("ylim"):
            ax.set_ylim(*panel["ylim"])
        elif 0 <= min(values) and max(values) <= 1 < ax.get_ylim()[1]:
            # a share (accuracy, F1) cannot exceed 1; stop the axis there and let markers at 1.0 draw whole
            ax.set_ylim(top=1.0)
            for line in ax.get_lines():
                line.set_clip_on(False)
        ax.legend(loc=legend)
        w = zoom_warning(values, ax.get_ylim(), f"panel {i + 1}")
        if w:
            warnings.append(w)
    fig.tight_layout()
    return fig, warnings


def stacked_bars(panels: list[dict], legend: str = "best"):
    """Bars per category; a panel with several parts stacks them (a cost or time breakdown).
    Each panel: {"title", "categories", "parts": {name: values}, "xlabel", "ylabel"}."""
    palette = DEEP
    fig, axes = plt.subplots(1, len(panels), figsize=figsize(len(panels)), squeeze=False)
    warnings = []
    for i, (ax, panel) in enumerate(zip(axes[0], panels)):
        cats = [str(c) for c in panel["categories"]]
        x = np.arange(len(cats))
        bottom = np.zeros(len(cats))
        for k, (name, vals) in enumerate(panel["parts"].items()):
            vals = np.asarray(vals, dtype=float)
            if len(vals) != len(cats):
                raise ValueError(f"panel {i + 1}, {name}: {len(vals)} values for {len(cats)} categories")
            if (vals < 0).any():
                warnings.append(f"panel {i + 1}, {name}: negative values cannot stack; use grouped bars")
            ax.bar(x, vals, width=0.6, bottom=bottom, label=plain(name), color=palette[k % len(palette)],
                   edgecolor="white",
                   linewidth=0.6)
            bottom += vals
        ax.set_xticks(x, [plain(c) for c in cats])
        ax.set_xlabel(bold(panel.get("xlabel", "")))
        ax.set_ylabel(bold(panel.get("ylabel", "")))
        ax.grid(True, axis="y", linestyle="--", linewidth=0.5)
        ax.grid(False, axis="x")
        ax.set_axisbelow(True)
        if panel.get("title"):
            ax.set_title(bold(_letter(i, panel["title"]) if len(panels) > 1 else panel["title"]))
        ax.legend(loc=legend)
        _thousands(ax)
        if ax.get_ylim()[0] != 0:
            warnings.append(f"panel {i + 1}: bars must start at zero")
    fig.tight_layout()
    return fig, warnings


HATCHES = ["..", "xx", "\\\\", "++", "oo", "--"]


def grouped_bars(panels: list[dict], highlight: str | None = None, value_labels: bool = False,
                 hatch: bool = False):
    """Methods side by side within each category (window, dataset, setting), one panel per metric.
    Each panel: {"title", "categories" (or "x"), "series": {method: values}, "xlabel", "ylabel"}.
    A method keeps its colour in every panel; the highlighted method is orange. hatch=True adds a pattern per
    method (diagonal for the highlighted one) for figures that may be printed in greyscale.
    One legend serves the whole figure."""
    names = list(dict.fromkeys(n for p in panels for n in p["series"]))
    styles = series_styles(names, highlight)
    patterns, k = {}, 0
    for name in names:
        if not hatch:
            patterns[name] = None
        elif name == highlight:
            patterns[name] = "///"
        else:
            patterns[name], k = HATCHES[k % len(HATCHES)], k + 1
    fig, axes = plt.subplots(1, len(panels), figsize=figsize(len(panels)), squeeze=False)
    warnings = []
    for i, (ax, panel) in enumerate(zip(axes[0], panels)):
        cats = [str(c) for c in panel.get("categories", panel.get("x", []))]
        present = [n for n in names if n in panel["series"]]
        width = 0.8 / max(len(present), 1)
        x = np.arange(len(cats))
        for j, name in enumerate(present):
            vals = np.asarray(panel["series"][name], dtype=float)
            if len(vals) != len(cats):
                raise ValueError(f"panel {i + 1}, {name}: {len(vals)} values for {len(cats)} categories")
            bars = ax.bar(x + (j - (len(present) - 1) / 2) * width, vals, width=width, label=plain(name),
                          color=styles[name]["color"], hatch=patterns[name],
                          edgecolor="black" if hatch else "white", linewidth=0.6,
                          zorder=3)
            if value_labels:
                # three or more bars per group leave no room for horizontal labels; turn them upright
                ax.bar_label(bars, labels=[f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.3g}" for v in vals],
                             padding=2, rotation=90 if len(present) > 2 else 0,
                             fontsize=max(PRESETS[_STATE["preset"]]["tick"] - 1.5, 6))
        if value_labels:
            lo, hi = ax.get_ylim()
            ax.set_ylim(lo, hi + (hi - lo) * (0.18 if len(present) > 2 else 0.08))
        _thousands(ax)
        ax.set_xticks(x, [plain(c) for c in cats])
        ax.set_xlabel(bold(panel.get("xlabel", "")))
        ax.set_ylabel(bold(panel.get("ylabel", "")))
        ax.grid(True, axis="y", linestyle="--", linewidth=0.5)
        ax.grid(False, axis="x")
        ax.set_axisbelow(True)
        if any(v < 0 for n in present for v in panel["series"][n]):
            ax.axhline(0, color="black", linewidth=0.8, zorder=4)
        elif ax.get_ylim()[0] != 0:
            warnings.append(f"panel {i + 1}: bars must start at zero")
        if panel.get("title"):
            ax.set_title(bold(_letter(i, panel["title"]) if len(panels) > 1 else panel["title"]), pad=8)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    return fig, warnings


def confusion_grid(matrices: list[dict], color_by: str = "row-share"):
    """Confusion matrices side by side, counts written in every cell.
    color_by "row-share" shades each cell by its share of the true class, so a 9-sample class is as visible as a
    90,000-sample one; "count" shades by raw count (the majority class then dominates the colour).
    Each item: {"title", "labels", "matrix"}."""
    if color_by not in {"row-share", "count"}:
        raise ValueError("color_by is 'row-share' or 'count'")
    n = len(matrices)
    w = PRESETS[_STATE["preset"]]["width"]
    fig, axes = plt.subplots(1, n, figsize=(w, max(w / n * 0.9, 2.2)), squeeze=False)
    warnings = []
    for i, (ax, item) in enumerate(zip(axes[0], matrices)):
        m = np.asarray(item["matrix"], dtype=float)
        labels = item["labels"]
        if m.shape != (len(labels), len(labels)):
            raise ValueError(f"matrix {i + 1}: shape {m.shape} does not match {len(labels)} labels")
        rows = m.sum(axis=1, keepdims=True)
        shade = np.divide(m, rows, out=np.zeros_like(m), where=rows > 0) if color_by == "row-share" else m
        im = ax.imshow(shade, cmap=CONFUSION_CMAP, vmin=0, vmax=1 if color_by == "row-share" else None)
        cut = shade.max() * 0.6 if shade.max() else 1
        size = max(PRESETS[_STATE["preset"]]["tick"] - (2 if len(labels) > 5 else 0), 6)
        for r in range(m.shape[0]):
            for c in range(m.shape[1]):
                ax.text(c, r, f"{int(m[r, c]):,}" if not _STATE["tex"] else f"{int(m[r, c]):,}".replace(",", "{,}"),
                        ha="center", va="center", fontsize=size, color="white" if shade[r, c] > cut else "black")
        ax.set_xticks(range(len(labels)), [plain(l) for l in labels], fontsize=size)
        ax.set_yticks(range(len(labels)), [plain(l) for l in labels], fontsize=size, rotation=90, va="center")
        ax.set_xlabel(bold("Predicted label"))
        ax.set_ylabel(bold("True label"))
        ax.grid(False)
        if item.get("title"):
            ax.set_title(bold(item["title"]), pad=8)
        bar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        bar.ax.tick_params(labelsize=size)
        if color_by == "row-share":
            bar.set_label(plain("share of true class"), fontsize=size)
        if (rows == 0).any():
            warnings.append(f"matrix {i + 1}: a class has no true samples; its row is blank, not perfect")
        if color_by == "count" and rows.max() > 50 * max(rows[rows > 0].min(), 1):
            warnings.append(f"matrix {i + 1}: class sizes differ more than 50x; colour by count hides errors in "
                            "small classes (use row-share)")
    fig.tight_layout()
    return fig, warnings


def bubble_matrix(rows: list[str], cols: list, counts, xlabel: str, ylabel: str, scale: float | None = None):
    """Count per (row, column) as bubble area, e.g. samples per class on each client. A size key is always drawn,
    because area alone cannot be read as a number."""
    counts = np.asarray(counts, dtype=float)
    if counts.shape != (len(rows), len(cols)):
        raise ValueError(f"counts shape {counts.shape} does not match {len(rows)} rows x {len(cols)} columns")
    cmap = plt.get_cmap("tab10")
    top = counts.max() or 1
    scale = scale or 1500.0 / top  # largest bubble about 1500 pt^2
    w = PRESETS[_STATE["preset"]]["width"]
    fig, ax = plt.subplots(figsize=(w, max(w * 0.45, 2.0)))
    for j, name in enumerate(rows):
        ax.scatter(range(len(cols)), [j] * len(cols), s=counts[j] * scale, color=cmap(j), alpha=BUBBLE_ALPHA,
                   edgecolors="black", linewidths=0.5)
    ax.set_xticks(range(len(cols)), [plain(str(c)) for c in cols])
    ax.set_yticks(range(len(rows)), [plain(r) for r in rows])
    ax.set_xlim(-0.6, len(cols) - 0.4)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.grid(True, linestyle="-.", alpha=0.5, linewidth=0.7)
    ax.set_xlabel(bold(xlabel))
    ax.set_ylabel(bold(ylabel))
    keys = _nice_keys(top)
    handles = [ax.scatter([], [], s=v * scale, color="grey", alpha=0.5, edgecolors="black", linewidths=0.5)
               for v in keys]
    # legend rows are spaced in font-size units; leave room for the largest key bubble's diameter
    diameter_pt = float(np.sqrt(max(keys) * scale))
    legend_pt = FontProperties(size=plt.rcParams["legend.fontsize"]).get_size_in_points()
    spacing = max(1.4, 0.75 * diameter_pt / legend_pt)
    ax.legend(handles, [plain(f"{v:,.0f}") for v in keys], title=plain("count"), loc="upper left",
              bbox_to_anchor=(1.01, 1.0), labelspacing=spacing, borderpad=0.9, handletextpad=1.5,
              frameon=False)
    fig.tight_layout()
    warnings = []
    if (counts == 0).any():
        warnings.append("some cells are zero and draw no bubble; say in the caption that empty means none")
    return fig, warnings


def _nice_keys(top: float) -> list[float]:
    mag = 10 ** np.floor(np.log10(top)) if top > 0 else 1
    first = np.floor(top / mag) * mag
    return [k for k in (first / 10, first / 2, first) if k > 0]


def save(fig, base: str | Path, formats=("pdf", "png")) -> list[Path]:
    """Vector PDF for the paper, 300-dpi PNG for review and slides."""
    base = Path(base)
    base.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for fmt in formats:
        path = base.with_suffix("." + fmt)
        fig.savefig(path)
        out.append(path)
    plt.close(fig)
    return out


# ------------------------------------------------------------------ spec rendering


def _csv_columns(path: Path) -> dict[str, list]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"{path}: no rows")
    cols = {k: [r[k] for r in rows] for k in rows[0]}
    out = {}
    for k, vals in cols.items():
        try:
            out[k] = [float(v) for v in vals]
        except ValueError:
            out[k] = vals
    return out


def _resolve_panel(panel: dict, root: Path) -> dict:
    """A panel may name a CSV instead of inline numbers: {"csv": "file.csv", "x": "col", "series": ["c1", "c2"]}."""
    if "csv" not in panel:
        return panel
    cols = _csv_columns(root / panel["csv"])
    missing = [c for c in [panel["x"], *panel["series"]] if c not in cols]
    if missing:
        raise ValueError(f"{panel['csv']}: no column {missing}; columns are {list(cols)}")
    return {**{k: v for k, v in panel.items() if k not in {"csv", "x", "series"}},
            "x": cols[panel["x"]], "series": {c: cols[c] for c in panel["series"]}}


def render(spec: dict, out: str | Path, root: Path | None = None) -> tuple[list[Path], list[str]]:
    root = root or Path(".")
    kind = spec["type"]
    if kind == "lines":
        fig, warnings = method_lines([_resolve_panel(p, root) for p in spec["panels"]], spec.get("highlight"))
    elif kind == "stacked_bars":
        fig, warnings = stacked_bars(spec["panels"])
    elif kind == "grouped_bars":
        fig, warnings = grouped_bars([_resolve_panel(p, root) for p in spec["panels"]], spec.get("highlight"),
                                     spec.get("value_labels", False), spec.get("hatch", False))
    elif kind == "confusion":
        fig, warnings = confusion_grid(spec["matrices"], spec.get("color_by", "row-share"))
    elif kind == "bubbles":
        fig, warnings = bubble_matrix(spec["rows"], spec["cols"], spec["counts"], spec["xlabel"], spec["ylabel"])
    else:
        raise ValueError(f"unknown type {kind!r}: lines, grouped_bars, stacked_bars, confusion or bubbles")
    return save(fig, out), warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="render a JSON chart spec to PDF and PNG")
    r.add_argument("spec")
    r.add_argument("--out", required=True, help="output path without extension")
    r.add_argument("--preset", default="paper-double", choices=sorted(PRESETS))
    r.add_argument("--no-tex", action="store_true", help="skip LaTeX text even when it is installed")
    r.add_argument("--strict", action="store_true", help="exit 1 when there are checks to fix or state")
    args = ap.parse_args(argv)
    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    apply_style(spec.get("preset", args.preset), tex=False if args.no_tex else None)
    try:
        paths, warnings = render(spec, args.out, spec_path.parent)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for p in paths:
        print(f"wrote {p}")
    for w in warnings:
        print(f"check: {w}")
    return 1 if warnings and args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
