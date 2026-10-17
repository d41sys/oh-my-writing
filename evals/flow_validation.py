#!/usr/bin/env python3
"""Validate the flow metrics of evals/stats.py against reader evidence, and compare duplication across conditions.

Usage:
  python3 evals/flow_validation.py RUN_DIR [--out-dir DIR]

Writes RUN_DIR/flow-validation.md and RUN_DIR/duplication.md (or into --out-dir) and prints compact tables.

Two checks decide which metrics the gate may use (evals/gate/config.json):
  (a) order sensitivity: every non-analysis output is rebuilt with its sentences in a seeded random order (paragraph
      sizes kept). A metric that measures how sentences connect must score the shuffled copy worse in most runs.
  (b) agreement with the blind judge: for every judged pair with a clear verdict ('reads human' on style pairs, the
      pairwise winner on text pairs; ties, inconsistent and error verdicts are left out) the share of pairs where the
      metric prefers the judge's winner, with a bootstrap CI over cases (cases resampled, all their pairs together).
A new metric is gated only when (a) holds where it applies and the lower CI bound of (b) is above 0.5.

No model is involved: the same run directory always gives the same files.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True
EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
import stats  # noqa: E402

grade = stats.grade

SHUFFLE_METRICS = ("adjacent_cohesion", "abrupt_jump_rate", "given_new_carry")
SHUFFLES = 9  # seeded shuffles per output; the first is the single fixed-seed shuffle
DUPLICATION_METRICS = ("repeated_sentences", "repeated_trigram_rate", "near_duplicate_pairs_per_1000w",
                       "repeated_caveats", "source_copy_rate")
NEW_METRICS = ("adjacent_cohesion", "abrupt_jump_rate", "given_new_carry", "stock_transition_rate", "long_sentence_share",
               "interruption_density", "nominalization_per_1000w", "passive_voice_rate", "paragraph_length_cv",
               "one_sentence_paragraph_share", "repeated_trigram_rate", "near_duplicate_pairs_per_1000w",
               "repeated_caveats", "source_copy_rate")


# ---------------------------------------------------------------- outputs of a run


def read_outputs(run_dir: Path) -> list[dict]:
    """One item per run with a written output: key (host, case, condition, rep), kind, paragraphs of running prose."""
    cases = {c["id"]: c for c in grade.load_cases()}
    items = []
    for meta_path in sorted((run_dir / "runs").glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        case = cases.get(meta["case"])
        if case is None or (meta.get("error") and not (meta_path.parent / "workspace" / case["output"]).is_file()):
            continue
        out_path = meta_path.parent / "workspace" / case["output"]
        if not out_path.is_file():
            continue
        text = grade.strip_markers(out_path.read_text(encoding="utf-8", errors="replace"))
        items.append({"key": (meta["host"], meta["case"], meta["condition"], meta.get("rep") or 1),
                      "kind": stats.case_kind(case), "paragraphs": stats.prose_paragraphs(text)})
    return items


# ---------------------------------------------------------------- clustered share with bootstrap CI


def cluster_share(rows: list[tuple[str, bool]], label: str) -> dict:
    """rows: (case, success). Pooled share of successes; CI by resampling cases (all rows of a case together)."""
    by_case: dict[str, list[int]] = {}
    for case, ok in rows:
        w_n = by_case.setdefault(case, [0, 0])
        w_n[0] += bool(ok)
        w_n[1] += 1
    clusters = [tuple(v) for _, v in sorted(by_case.items())]
    n = sum(c[1] for c in clusters)
    if not n:
        return {"n": 0, "cases": 0, "share": None, "ci": None}
    share = sum(c[0] for c in clusters) / n
    ci = stats.bootstrap_ci(clusters, label, stat=lambda xs: sum(x[0] for x in xs) / max(1, sum(x[1] for x in xs)))
    return {"n": n, "cases": len(clusters), "share": share, "ci": ci}


# ---------------------------------------------------------------- (a) order sensitivity


def shuffle_test(items: list[dict], metric: str, shuffles: int = SHUFFLES, value=None, direction: str | None = None) -> dict:
    """Original vs sentence-shuffled copies of each output. Two readings per kind group: 'single' (the first seeded
    shuffle) and 'mean' (mean of all seeded shuffles, which removes the luck of one order). A copy is 'worse' when it
    scores worse than the original in the metric's own direction."""
    direction = direction or stats.METRICS[metric]["direction"]
    value = value or (lambda paragraphs: stats.flow_metrics(paragraphs).get(metric))
    sign = 1 if direction == "higher" else -1  # sign * (original - shuffled) > 0: the shuffled copy is worse
    groups: dict[str, list] = {"reader": [], "draft": [], "all non-analysis": []}
    for it in items:
        if it["kind"] == "analysis":
            continue
        orig = value(it["paragraphs"])
        seed = f"{stats.BOOTSTRAP_SEED}:shuffle:" + ":".join(map(str, it["key"]))
        copies = [value(stats.shuffled_paragraphs(it["paragraphs"], f"{seed}:{k}")) for k in range(shuffles)]
        copies = [c for c in copies if c is not None]
        if orig is None or not copies:
            continue
        row = (it["key"][1], orig, copies[0], statistics.fmean(copies))
        groups[it["kind"]].append(row)
        groups["all non-analysis"].append(row)
    out: dict[str, dict] = {}
    for name, rows in groups.items():
        out[name] = {"runs": len(rows)}
        for reading, idx in (("single", 2), ("mean", 3)):
            diffs = [(r[0], sign * (r[1] - r[idx])) for r in rows]
            worse = [(c, d > 1e-12) for c, d in diffs]
            res = cluster_share(worse, f"shuffle {reading} {metric} {name}")
            out[name][reading] = {"worse": sum(w for _, w in worse), "better": sum(d < -1e-12 for _, d in diffs),
                                  "share": res["share"], "ci": res["ci"], "shuffled_mean": (
                                      statistics.fmean(r[idx] for r in rows) if rows else None)}
        out[name]["orig_mean"] = statistics.fmean(r[1] for r in rows) if rows else None
    return out


# ---------------------------------------------------------------- (b) agreement with the blind judge


def judged_pairs(entries: list[dict]) -> list[dict]:
    """Clear verdicts of judge.json: {source, host, case, rep, winner, loser}. source is 'style' ('reads human' answer of a
    style entry) or 'text' (pairwise winner). Visual entries (rendered pages) are not text pairs and are left out."""
    out = []
    for e in entries:
        if "visual" in e or "scores" in e:
            continue
        pair = e.get("pair") or "skill:baseline"
        x, y = pair.split(":", 1)
        verdict, source = (e.get("human"), "style") if e.get("mode") == "style" else (e.get("winner"), "text")
        if verdict not in {x, y}:
            continue
        out.append({"source": source, "host": e["host"], "case": e["case"], "rep": e["rep"],
                    "winner": verdict, "loser": y if verdict == x else x})
    return out


def agreement(records: list[dict], pairs: list[dict], metric: str, source: str | None = None,
              direction: str | None = None) -> dict:
    """Share of judged pairs where the metric prefers the judge's winner (ties and missing values left out).
    Without a direction the metric 'prefers' the higher value (reported as context only)."""
    direction = direction or stats.METRICS[metric]["direction"] or "higher"
    index = {(r["host"], r["case"], r["condition"], r["rep"]): r["metrics"].get(metric)
             for r in records if not r["host_error"]}
    rows, ties = [], 0
    for p in pairs:
        if source and p["source"] != source:
            continue
        w, l = (index.get((p["host"], p["case"], c, p["rep"])) for c in (p["winner"], p["loser"]))
        if w is None or l is None:
            continue
        if w == l:
            ties += 1
            continue
        rows.append((p["case"], (w > l) == (direction == "higher")))
    res = cluster_share(rows, f"agreement {metric} {source or 'all'}")
    res["ties"] = ties
    return res


# ---------------------------------------------------------------- decisions


def decide(metric: str, shuffle: dict | None, agree: dict) -> tuple[str, str]:
    """('gated' | 'info', reason) for a new metric."""
    spec = stats.METRICS[metric]
    if spec["direction"] is None:
        return "info", "no direction: depends on the case, so there is no better or worse to gate"
    if shuffle is not None:
        row = shuffle["reader"]["mean"]
        if row["share"] is None or row["ci"] is None or row["ci"][0] <= 0.5:
            return "info", (f"fails order sensitivity: shuffled copies worse in {row['share']:.0%} of reader runs, CI "
                            f"{_ci(row['ci'])}, lower bound not above 0.5" if row["share"] is not None
                            else "order sensitivity not computable")
    if agree["ci"] is None or agree["share"] is None:
        return "info", "judge agreement not computable (too few judged pairs with a value)"
    lo = agree["ci"][0]
    if lo <= 0.5:
        return "info", f"judge agreement {agree['share']:.2f}, CI lower bound {lo:.2f} is not above 0.5"
    return "gated", f"judge agreement {agree['share']:.2f}, CI lower bound {lo:.2f} above 0.5" + (
        f"; shuffled copies worse in {shuffle['reader']['mean']['share']:.0%} of reader runs"
        if shuffle is not None else "")


def validate(run_dir: Path) -> dict:
    info, records = stats.read_run(run_dir)
    items = read_outputs(run_dir)
    entries = json.loads((run_dir / "judge.json").read_text(encoding="utf-8"))
    pairs = judged_pairs(entries)
    shuffles = {m: shuffle_test(items, m) for m in SHUFFLE_METRICS}
    table = {}
    for m in stats.METRICS:
        a = {"all": agreement(records, pairs, m), "style": agreement(records, pairs, m, "style"),
             "text": agreement(records, pairs, m, "text")}
        table[m] = a
    decisions = {m: decide(m, shuffles.get(m), table[m]["all"]) for m in NEW_METRICS}
    composite = composite_validation(records, items, pairs, table)
    return {"run": info.get("id", run_dir.name), "records": records, "pairs": pairs, "shuffles": shuffles,
            "agreement": table, "decisions": decisions, "composite": composite}


# ---------------------------------------------------------------- composite (candidate)

COMPOSITE_COHESION_SCALE = 0.25  # adjacent_cohesion at or above this counts as fully cohesive


def composite_value(m: dict) -> float | None:
    """Candidate flow_score in [0, 1], higher is better: mean of given_new_carry, 1 - abrupt_jump_rate and the scaled
    adjacent_cohesion; None unless all three exist. Fixed constants, no population statistics."""
    carry, jump, coh = (m.get(k) for k in ("given_new_carry", "abrupt_jump_rate", "adjacent_cohesion"))
    if carry is None or jump is None or coh is None:
        return None
    return (carry + (1 - jump) + min(1.0, coh / COMPOSITE_COHESION_SCALE)) / 3


def composite_validation(records: list[dict], items: list[dict], pairs: list[dict], parts: dict) -> dict:
    """Shuffle test and judge agreement of the candidate; 'adds' only when it validates better than every part it
    is made of: shuffle CI lower bound above 0.5, agreement CI lower bound above 0.5 and a higher agreement than each part."""
    shuffle = shuffle_test(items, "flow_score", value=lambda p: composite_value(stats.flow_metrics(p)), direction="higher")
    aug = [{**r, "metrics": {**r["metrics"], "flow_score": composite_value(r["metrics"])}} for r in records]
    agree = {"all": agreement(aug, pairs, "flow_score", direction="higher"),
             "style": agreement(aug, pairs, "flow_score", "style", "higher"),
             "text": agreement(aug, pairs, "flow_score", "text", "higher")}
    best_part = max(parts[m]["all"]["share"] or 0 for m in ("given_new_carry", "abrupt_jump_rate", "adjacent_cohesion"))
    ci = agree["all"]["ci"]
    adds = (shuffle["reader"]["mean"]["ci"] is not None and shuffle["reader"]["mean"]["ci"][0] > 0.5 and ci is not None
            and ci[0] > 0.5 and agree["all"]["share"] > best_part)
    return {"shuffle": shuffle, "agreement": agree, "best_part_agreement": best_part, "adds": adds}


# ---------------------------------------------------------------- rendering


def _fmt(v, d=2):
    return "n/a" if v is None else f"{v:.{d}f}"


def _ci(ci):
    return "n/a" if ci is None else f"[{ci[0]:.2f}, {ci[1]:.2f}]"


def _cell(a: dict) -> str:
    return "n/a" if a["share"] is None else f"{a['share']:.2f} {_ci(a['ci'])} n={a['n']}/{a['cases']}"


def render_validation(result: dict) -> str:
    lines = [f"# Flow metric validation, run {result['run']}", "",
             f"METRICS_VERSION {stats.METRICS_VERSION}; bootstrap seed {stats.BOOTSTRAP_SEED}, {stats.BOOTSTRAP_RESAMPLES} "
             f"resamples, 95% CI over cases (all pairs of a case resampled together). Generated by "
             "`python3 evals/flow_validation.py`; deterministic.", "",
             "## (a) Order sensitivity: sentence-shuffled copy of every output", "",
             "Each non-analysis output is rebuilt with its sentences in a seeded random order (paragraph sizes kept). "
             f"'worse' = the shuffled copy scores worse in the metric's own direction (ties count as neither). 'single' = the first "
             f"seeded shuffle; 'mean' = mean of {SHUFFLES} seeded shuffles (the decision uses 'mean' on reader outputs: "
             "share above 0.5 with the CI lower bound above 0.5). Only metrics that read the order of "
             "sentences can be tested; every other flow metric is a property of single sentences or paragraph sizes and "
             "is invariant under the shuffle by construction.", ""]
    rows = []
    for m, groups in result["shuffles"].items():
        for name, g in groups.items():
            for reading in ("single", "mean"):
                r = g[reading]
                rows.append([m, name, reading, str(g["runs"]), str(r["worse"]), str(r["better"]),
                             "n/a" if r["share"] is None else f"{r['share']:.0%} {_ci(r['ci'])}",
                             _fmt(g["orig_mean"], 3), _fmt(r["shuffled_mean"], 3)])
    lines += ["```"] + stats._table(["metric", "outputs", "shuffle", "runs", "shuffled worse", "better",
                                     "share worse [CI]", "mean original", "mean shuffled"], rows) + ["```", ""]
    n_style = sum(p["source"] == "style" for p in result["pairs"])
    n_text = sum(p["source"] == "text" for p in result["pairs"])
    lines += ["## (b) Agreement with the blind judge", "",
              f"{len(result['pairs'])} judged pairs with a clear verdict ({n_style} style pairs: 'reads human' answer; "
              f"{n_text} text pairs: pairwise winner; ties, inconsistent and error verdicts, and visual-page entries left out). "
              "Each cell: share of pairs where the metric prefers the judge's winner, [95% CI over cases], "
              "n = pairs/cases with a value on both sides and no tie. A metric with no direction 'prefers' the higher value "
              "(context only). 0.5 is chance.", ""]
    rows = []
    for m, spec in stats.METRICS.items():
        a = result["agreement"][m]
        rows.append([m, spec["direction"] or "-", "new" if m in NEW_METRICS else "old", _cell(a["all"]),
                     _cell(a["style"]), _cell(a["text"])])
    lines += ["```"] + stats._table(["metric", "better", "", "all pairs", "style pairs (reads human)",
                                     "text pairs (winner)"], rows) + ["```", ""]
    c = result["composite"]
    sh = c["shuffle"]["reader"]["mean"]
    lines += ["## Composite candidate flow_score", "",
              f"flow_score = mean of given_new_carry, 1 - abrupt_jump_rate and min(1, adjacent_cohesion / {COMPOSITE_COHESION_SCALE}); "
              "needs all three. It would be added to the metric table only if it validates better than its parts: shuffle "
              "(reader outputs, mean of shuffles) CI lower bound above 0.5, judge agreement CI lower bound above 0.5 and an "
              "agreement above that of every part.", "",
              f"- order sensitivity (reader, mean of {SHUFFLES}): shuffled copy worse in "
              f"{'n/a' if sh['share'] is None else f'{sh['share']:.0%}'} {_ci(sh['ci'])}",
              f"- judge agreement: all {_cell(c['agreement']['all'])}; style {_cell(c['agreement']['style'])}; "
              f"text {_cell(c['agreement']['text'])}",
              f"- best part agreement (all pairs): {c['best_part_agreement']:.2f}",
              f"- decision: {'added to METRICS' if c['adds'] else 'not added: it does not validate better than its parts'}", ""]
    lines += ["## Decision for the new metrics", "",
              "Gated = passes (a) where it applies and the lower CI bound of (b, all pairs) is above 0.5. Everything else is "
              "reported and kept info-only (`gated: false` in evals/gate/config.json). Existing metrics keep their own gating "
              "rationale (the facts and slop metrics check correctness and stock vocabulary, not flow).", ""]
    rows = [[m, stats.METRICS[m]["direction"] or "-", d, reason] for m, (d, reason) in result["decisions"].items()]
    lines += ["```"] + stats._table(["metric", "better", "decision", "reason"], rows) + ["```", ""]
    return "\n".join(lines)


def _duplication_row(label: str, other: dict, ours: dict, metric: str) -> list:
    p = stats.paired(other, ours, f"dup {label}:{metric}")
    dg = stats._digits(metric)
    return [metric, stats._num(p["a_mean"], dg), stats._num(p["b_mean"], dg), stats._num(p["diff"], dg),
            stats._ci(p["ci"], dg), stats.verdict(p["diff"], p["ci"], stats.METRICS[metric]["direction"], p["n_cases"]),
            f"{p['n_pairs']}/{p['n_cases']}"]


def duplication_tables(records: list[dict]) -> list[tuple[str, list[list]]]:
    """[(title, rows)] for our skill against baseline and every competitor/variant condition, all pairs and loaded-only
    pairs. Rows: metric, other, ours, diff = ours - other, CI, verdict ('better' = we repeat or copy less), n runs/cases."""
    out = []
    others = ["baseline"] + stats.competitor_conditions(records)
    for host in sorted({r["host"] for r in records}):
        for cond in others:
            for loaded in (False, True):
                # loaded-only: our run must have loaded its skill; so must a competitor's (the baseline has none)
                keep = [r for r in records if not loaded or r["condition"] == "baseline" or r.get("skill_loaded") is True]
                rows = []
                for m in DUPLICATION_METRICS:
                    a = stats.values_by_run(keep, m, condition=cond, host=host)
                    b = stats.values_by_run(keep, m, condition="skill", host=host)
                    rows.append(_duplication_row(f"{host} {cond} {loaded}", a, b, m))
                out.append((f"{host}: skill vs {cond}, {'loaded-only pairs' if loaded else 'all pairs'}", rows))
    return out


def render_duplication(run_id: str, records: list[dict]) -> str:
    lines = [f"# Duplication, run {run_id}", "",
             f"METRICS_VERSION {stats.METRICS_VERSION}. Our skill against the no-skill baseline and each competitor, paired on "
             "(host, case, rep), repetitions averaged per case, 95% bootstrap CI over cases. diff = skill - other; the verdict "
             "refers to the skill ('better' = CI excludes 0 and the skill repeats less). 'all' = every paired run; 'loaded' = "
             "pairs where `meta.json` says the skill was loaded on both sides (the baseline has no skill, so for it only "
             "our side is filtered). The last column is paired runs / cases.", "",
             "Two different things, kept apart:", "",
             "- REPEATS ITSELF (inside one output): repeated_sentences, repeated_trigram_rate, near_duplicate_pairs_per_1000w, "
             "repeated_caveats.",
             "- COPIES THE INPUT (output against the case's sources and prompt): source_copy_rate, share of output words "
             "inside a verbatim run of 8+ words of the sources. It has no better or worse (an edit must keep its source), "
             "so its verdict column is 'info'.", ""]
    for title, rows in duplication_tables(records):
        lines += [f"## {title}", "", "```"] + stats._table(["metric", "other", "skill", "diff", "95% CI", "verdict", "n"], rows) + ["```", ""]
    return "\n".join(lines)


def compact_duplication(records: list[dict]) -> str:
    """One line per comparison and metric: the verdicts for all and loaded-only pairs."""
    tables = duplication_tables(records)
    by_cmp: dict[str, dict] = {}
    for title, trows in tables:
        head, scope = title.rsplit(", ", 1)
        by_cmp.setdefault(head, {})["loaded" if scope.startswith("loaded") else "all"] = trows
    out_rows = []
    for head, both in by_cmp.items():
        for a, b in zip(both["all"], both["loaded"]):
            out_rows.append([head.replace(": skill vs ", " / "), a[0], a[1], a[2], f"{a[3]} {a[4]} {a[5]}", a[6],
                             f"{b[3]} {b[4]} {b[5]}", b[6]])
    return "\n".join(stats._table(["comparison", "metric", "other", "skill", "all: diff CI verdict", "all n",
                                   "loaded: diff CI verdict", "loaded n"], out_rows))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run_dir")
    parser.add_argument("--out-dir", help="where to write flow-validation.md and duplication.md (default: RUN_DIR)")
    args = parser.parse_args(argv)
    run_dir = Path(args.run_dir)
    out_dir = Path(args.out_dir) if args.out_dir else run_dir
    result = validate(run_dir)
    (out_dir / "flow-validation.md").write_text(render_validation(result), encoding="utf-8")
    (out_dir / "duplication.md").write_text(render_duplication(result["run"], result["records"]), encoding="utf-8")
    print(render_validation(result))
    print(compact_duplication(result["records"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
