import json
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "results-visualization" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True
import plotstyle as ps  # noqa: E402


@pytest.fixture(autouse=True)
def style():
    ps.apply_style("paper-double", tex=False)


def _line_props(ax):
    return {l.get_label(): (l.get_color(), l.get_marker(), l.get_linestyle()) for l in ax.get_lines()}


def test_a_method_looks_the_same_in_every_panel_even_when_series_order_differs():
    panels = [
        {"title": "A", "x": [1, 2], "series": {"Base": [0.5, 0.6], "Ours": [0.7, 0.8], "Other": [0.4, 0.5]}},
        {"title": "B", "x": [1, 2], "series": {"Other": [0.3, 0.4], "Ours": [0.6, 0.9], "Base": [0.2, 0.3]}},
    ]
    fig, _ = ps.method_lines(panels, highlight="Ours")
    left, right = (_line_props(ax) for ax in fig.axes)
    assert left == right
    assert left["Ours"][1] == ps.HIGHLIGHT_MARKER
    # the highlighted method is drawn last, on top of the baselines
    assert fig.axes[0].get_lines()[-1].get_label() == "Ours"


def test_baselines_differ_by_marker_not_only_by_colour():
    styles = ps.series_styles(["A", "B", "C", "Ours"], highlight="Ours")
    markers = [s["marker"] for s in styles.values()]
    assert len(set(markers)) == len(markers)
    assert all(s["color"] != ps.HIGHLIGHT_COLOR for n, s in styles.items() if n != "Ours")


def test_zoomed_axis_warns_and_full_scale_axis_does_not():
    narrow = [{"x": [1, 2, 3], "series": {"A": [0.998, 0.999, 0.9985], "B": [0.9992, 0.9995, 0.9999]}}]
    _, warnings = ps.method_lines(narrow)
    assert len(warnings) == 1 and "caption" in warnings[0]
    wide = [{"x": [1, 2, 3], "series": {"A": [0.6, 0.8, 0.9]}, "ylim": [0, 1]}]
    _, warnings = ps.method_lines(wide)
    assert warnings == []


def test_series_length_mismatch_is_an_error_not_a_silent_truncation():
    with pytest.raises(ValueError, match="2 values for 3 x points"):
        ps.method_lines([{"x": [1, 2, 3], "series": {"A": [0.1, 0.2]}}])


def test_stacked_parts_sit_on_top_of_each_other():
    fig, warnings = ps.stacked_bars([{"categories": ["x", "y"], "parts": {"p1": [2, 3], "p2": [5, 1]}}])
    ax = fig.axes[0]
    tops = sorted(round(r.get_y() + r.get_height(), 9) for r in ax.patches)
    assert tops == [2.0, 3.0, 4.0, 7.0]  # x: 2 then 2+5; y: 3 then 3+1
    assert ax.get_ylim()[0] == 0 and warnings == []


def test_confusion_shading_makes_errors_in_a_small_class_visible():
    m = [[90000, 0], [5, 5]]
    fig, _ = ps.confusion_grid([{"labels": ["big", "small"], "matrix": m}])
    shade = fig.axes[0].images[0].get_array()
    assert shade[1, 0] == pytest.approx(0.5) and shade[0, 0] == pytest.approx(1.0)
    texts = {t.get_text() for t in fig.axes[0].texts}
    assert "90,000" in texts  # the cell still shows the count


def test_count_shading_on_imbalanced_classes_warns():
    _, warnings = ps.confusion_grid([{"labels": ["big", "small"], "matrix": [[90000, 0], [5, 5]]}], color_by="count")
    assert any("50x" in w for w in warnings)


def test_confusion_labels_must_match_matrix():
    with pytest.raises(ValueError, match="does not match 3 labels"):
        ps.confusion_grid([{"labels": ["a", "b", "c"], "matrix": [[1, 0], [0, 1]]}])


def test_bubble_area_is_proportional_to_count_and_has_a_size_key():
    counts = np.array([[100, 400], [0, 25]])
    fig, warnings = ps.bubble_matrix(["r1", "r2"], [0, 1], counts, "client", "class")
    ax = fig.axes[0]
    sizes = np.concatenate([c.get_sizes() for c in ax.collections])
    plotted = sizes[:4]
    assert plotted[1] / plotted[0] == pytest.approx(4.0)
    legend = ax.get_legend()
    assert legend is not None and legend.get_title().get_text() == "count"
    assert any("zero" in w for w in warnings)


@pytest.mark.parametrize("missing", ["latex", "dvipng", "type1cm", "type1ec"])
def test_partial_tex_install_falls_back_instead_of_crashing(monkeypatch, missing):
    # usetex with latex but no cm-super (BasicTeX) makes every render raise, so detection needs every piece
    monkeypatch.setattr(ps.shutil, "which", lambda name: None if name == missing else f"/bin/{name}")
    monkeypatch.setattr(ps, "_has_tex_package", lambda name: name != missing)
    assert ps.tex_available() is False


def test_full_tex_install_is_detected(monkeypatch):
    monkeypatch.setattr(ps.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(ps, "_has_tex_package", lambda name: True)
    assert ps.tex_available() is True


def _narrow_spec(tmp_path):
    spec = {"type": "lines", "panels": [{"x": [1, 2], "series": {"A": [0.998, 0.999]}}]}
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    return ["render", str(tmp_path / "spec.json"), "--out", str(tmp_path / "fig"), "--no-tex"]


def test_cli_writes_files_and_succeeds_with_checks_unless_strict(tmp_path, capsys):
    argv = _narrow_spec(tmp_path)
    assert ps.main(argv) == 0
    assert "check:" in capsys.readouterr().out
    assert (tmp_path / "fig.pdf").stat().st_size > 0 and (tmp_path / "fig.png").stat().st_size > 0
    assert ps.main([*argv, "--strict"]) == 1


def test_cli_reads_series_from_csv(tmp_path):
    (tmp_path / "r.csv").write_text("n,A,Ours\n10,0.5,0.7\n20,0.6,0.9\n", encoding="utf-8")
    spec = {"type": "lines", "highlight": "Ours",
            "panels": [{"title": "t", "csv": "r.csv", "x": "n", "series": ["A", "Ours"], "ylim": [0, 1]}]}
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    assert ps.main(["render", str(tmp_path / "spec.json"), "--out", str(tmp_path / "fig"), "--no-tex", "--strict"]) == 0
    fig, _ = ps.method_lines([ps._resolve_panel(spec["panels"][0], tmp_path)], highlight="Ours")
    plotted = {l.get_label(): list(l.get_ydata()) for l in fig.axes[0].get_lines()}
    assert plotted == {"A": [0.5, 0.6], "Ours": [0.7, 0.9]}


def test_share_axis_stops_at_one_and_keeps_markers_whole():
    fig, _ = ps.method_lines([{"x": [1, 2, 3], "series": {"A": [0.90, 0.95, 1.0]}}])
    ax = fig.axes[0]
    assert ax.get_ylim()[1] == 1.0
    assert not ax.get_lines()[0].get_clip_on()
    # a metric that is not a share keeps its autoscaled headroom
    fig, _ = ps.method_lines([{"x": [1, 2], "series": {"loss": [0.5, 1.4]}}])
    assert fig.axes[0].get_ylim()[1] > 1.4


def test_bubble_key_works_without_apply_style():
    import matplotlib
    matplotlib.rcParams.update(matplotlib.rcParamsDefault)  # legend.fontsize is the string "medium" here
    fig, _ = ps.bubble_matrix(["a"], [0, 1], [[5, 50]], "x", "y")
    assert fig.axes[0].get_legend() is not None


def test_cli_names_a_missing_csv_column(tmp_path, capsys):
    (tmp_path / "r.csv").write_text("n,A\n1,2\n", encoding="utf-8")
    spec = {"type": "lines", "panels": [{"csv": "r.csv", "x": "n", "series": ["B"]}]}
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    code = ps.main(["render", str(tmp_path / "spec.json"), "--out", str(tmp_path / "fig"), "--no-tex"])
    assert code == 2
    assert "no column ['B']" in capsys.readouterr().err


def test_grouped_bars_keep_each_method_look_across_panels_and_start_at_zero():
    panels = [
        {"categories": ["w1", "w2"], "series": {"Base": [5, 4], "Ours": [3, 2]}},
        {"categories": ["w1", "w2"], "series": {"Ours": [9, 8], "Base": [7, 6]}},
    ]
    fig, warnings = ps.grouped_bars(panels, highlight="Ours", hatch=True)
    looks = []
    for ax in fig.axes:
        looks.append({c.get_label(): (c.patches[0].get_facecolor(), c.patches[0].get_hatch()) for c in ax.containers})
        assert ax.get_ylim()[0] == 0
    assert looks[0]["Ours"] == looks[1]["Ours"] and looks[0]["Base"] == looks[1]["Base"]
    assert looks[0]["Ours"][1] == "///" and looks[0]["Base"][1] not in (None, "///")  # greyscale-safe cue
    assert warnings == []


def test_grouped_bars_default_to_the_plain_soft_look():
    import matplotlib.colors as mc
    fig, _ = ps.grouped_bars([{"categories": ["w"], "series": {"Base": [1], "Ours": [2]}}], highlight="Ours")
    bars = {c.get_label(): c.patches[0] for c in fig.axes[0].containers}
    assert all(b.get_hatch() is None for b in bars.values())
    assert mc.to_hex(bars["Ours"].get_facecolor()) == ps.HIGHLIGHT_COLOR
    assert mc.to_hex(bars["Base"].get_facecolor()) == ps.DEEP[0]


def test_grouped_bars_with_negative_values_draw_a_zero_line_instead_of_warning():
    fig, warnings = ps.grouped_bars([{"categories": ["a", "b"], "series": {"delta": [-3, 2]}}])
    assert warnings == []
    assert any(l.get_ydata()[0] == 0 for l in fig.axes[0].get_lines())


def test_tex_escaping_leaves_math_alone():
    ps.apply_style("paper-double", tex=True)
    try:
        out = ps.plain(r"cost_total (50% of k€) at $\rho_1$")
        assert r"cost\_total" in out and r"50\%" in out and r"$\rho_1$" in out
        assert "€" not in out
    finally:
        ps.apply_style("paper-double", tex=False)
