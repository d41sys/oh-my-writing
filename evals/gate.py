#!/usr/bin/env python3
"""Regression gate for skill revisions, on the deterministic statistics of evals/stats.py.

Usage:
  python3 evals/gate.py freeze RUN_DIR [--model NAME] [--out evals/gate/reference.json]
  python3 evals/gate.py check  RUN_DIR [--against evals/gate/reference.json] [--config evals/gate/config.json] [--all]
  python3 evals/gate.py check  RUN_DIR --reference-condition variant-NAME [--config evals/gate/config.json] [--all]
  python3 evals/gate.py aa     RUN_DIR [--config evals/gate/config.json]
  python3 evals/gate.py weak   OTHER_RUN_DIR [--against evals/gate/reference.json] [--out evals/gate/weak_spots.json]

`freeze` records the with-skills outputs of a run (every metric, per case and repetition) together with the run id,
model, skill versions and metric version as the reference. `check` scores a new run the same way, pairs it with the
reference on (host, case, rep) and exits 1 when a skill revision is worse. Per skill and over all skills:

  statistical rule, for every metric listed in config.json "metrics" with "gated": true (invented facts and the
  case-check pass rate are among them):
    the run pairs are (new - reference) per (host, case, rep); repetitions of a case are averaged first because
    they are not independent cases; the 95% bootstrap CI is taken over cases.
    FAIL when the lower CI bound of the worsening is above the metric's tolerance, i.e. the whole interval is worse
    than tolerated. Worse than tolerance on average with a CI that reaches back inside the tolerance is a warning.
    Rerun noise widens the interval, so noise alone does not fail the gate.
  absolute rule (config.json "absolute"), the only one without statistics, because any occurrence is a defect:
    leaked markers: the share of reader-facing runs (stats.CASE_KIND = "reader") whose output carries an unresolved
    gap marker or placeholder is above "leaked_marker_run_rate_max" (0 = any run). Measured on the new run alone.

`aa` is the noise test: it relabels the repetitions of one run (shifted by one and by two, and every single
repetition against every other) and gates those pseudo-runs against the run itself. The outputs are the same
outputs, so the gate must pass on all of them; it exits 1 when one fails.

`check --reference-condition variant-NAME` needs no frozen file: inside one A/B run (run.py --variant NAME=GITREF) it
gates the run's `skill` runs against the runs of that variant, with the same rules and tolerances. `skill` is the
revision under test, the variant the reference; hosts are those present on both sides.

`weak` records where the reference is worse than another run (CI of the difference excludes zero) in
config.json's metrics; `check` prints that list so the gate never silently blesses the reference's weak spots.

Exit codes: 0 pass, 1 regression, 2 not comparable (metric version, hosts) or bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
import stats  # noqa: E402

GATE_DIR = EVALS / "gate"
REFERENCE = GATE_DIR / "reference.json"
CONFIG = GATE_DIR / "config.json"
WEAK_SPOTS = GATE_DIR / "weak_spots.json"
SCHEMA = 1
VARIANT_PREFIX = "variant-"  # run.py's A/B condition: our skills at another git ref


def _round(v):
    return None if v is None else round(v, 6)


# ---------------------------------------------------------------- freeze


def _gated_records(records: list[dict], condition: str) -> list[dict]:
    """Run records of one condition without host errors, metrics rounded as in the stored reference."""
    return [{"case": r["case"], "skill": r["skill"], "kind": r["kind"], "host": r["host"], "rep": r["rep"],
             "metrics": {m: _round(v) for m, v in r["metrics"].items()}}
            for r in records if r["condition"] == condition and not r["host_error"]]


def run_skill_versions(records: list[dict]) -> dict | None:
    """Skill versions the given runs installed (meta.json `skill_versions`, which run.py records per run): one version
    per skill, or a sorted list when runs of one results directory used different versions (a --resume after an
    edit). None when any run did not record them (runs made before run.py recorded versions)."""
    if not records or any(not r.get("skill_versions") for r in records):
        return None
    seen: dict[str, set] = {}
    for r in records:
        for name, version in r["skill_versions"].items():
            seen.setdefault(name, set()).add(version)
    return {name: (next(iter(v)) if len(v) == 1 else sorted(v, key=str)) for name, v in sorted(seen.items())}


def freeze(run_dir: Path, condition: str = "skill", model: str | None = None, hosts: set[str] | None = None) -> dict:
    info, records = stats.read_run(run_dir, hosts)
    chosen = [r for r in records if r["condition"] == condition and not r["host_error"]]
    runs = _gated_records(records, condition)
    if not runs:
        raise SystemExit(f"no '{condition}' runs in {run_dir}")
    versions = run_skill_versions(chosen)
    return {
        "schema": SCHEMA, "metrics_version": stats.METRICS_VERSION, "tools": stats.tool_fingerprint(),
        "condition": condition,
        "run": {"id": info.get("id", run_dir.name), "started": info.get("started"),
                "hosts": sorted({r["host"] for r in runs}), "cases": len({r["case"] for r in runs}),
                "repeat": info.get("repeat"), "host_versions": {k: v for k, v in info.items() if k.endswith("_version")},
                "models": info.get("models") or {}, "model": model or "host default"},
        # the versions the frozen runs installed; runs made before run.py recorded them fall back to the repository's
        # versions at freeze time, which match only when the reference is frozen right after its run
        "skill_versions": versions or stats.skill_versions(),
        "skill_versions_from": "runs (meta.json)" if versions else "repository at freeze time",
        "runs": runs,
    }


# ---------------------------------------------------------------- evaluate


def _index(runs: list[dict], metric: str) -> dict[tuple, float]:
    out = {}
    for r in runs:
        v = r["metrics"].get(metric)
        if v is not None:
            out[(r["host"], r["case"], r["rep"])] = v
    return out


def _row(scope, rule, metric, ref, new, delta, ci, verdict, detail="", n=None):
    return {"scope": scope, "rule": rule, "metric": metric, "reference": ref, "new": new, "delta": delta, "ci": ci,
            "verdict": verdict, "detail": detail, "n_cases": n}


def _worsening(delta, ci, direction):
    """(mean worsening, lower CI bound of the worsening, upper CI bound of the worsening); negative = better."""
    sign = 1 if direction == "lower" else -1
    if delta is None or ci is None:
        return None, None, None
    lo, hi = sorted((sign * ci[0], sign * ci[1]))
    return sign * delta, lo, hi


def _paired_rule(scope, metric, rule, a, b, min_cases):
    spec = stats.METRICS[metric]
    p = stats.paired(a, b, f"gate {scope}:{metric}")
    worse_by, worse_lo, worse_hi = _worsening(p["diff"], p["ci"], spec["direction"])
    tol = rule.get("tolerance", 0.0)
    if p["n_cases"] < min_cases or worse_by is None:
        verdict = "few"
    elif worse_lo > tol:
        verdict = "FAIL"
    elif worse_by > tol:
        verdict = "warn"
    elif worse_hi < 0:
        verdict = "better"
    else:
        verdict = "ok"
    detail = f"tolerance {tol:g}, {spec['direction']} is better"
    if worse_lo is not None:
        detail += f"; CI lower bound of the worsening {worse_lo:+.3g}"
    return _row(scope, "stat", metric, p["a_mean"], p["b_mean"], p["diff"], p["ci"], verdict, detail, p["n_cases"])


def evaluate(reference: list[dict], new: list[dict], config: dict) -> dict:
    """reference and new: run records ({case, skill, kind, host, rep, metrics}). Returns {"rows": [...], "failed": bool,
    "pairs": {scope: n}}. Pure function of its inputs, so the result is the same on every call."""
    absolute, soft = config.get("absolute", {}), config["metrics"]
    min_cases = config.get("min_cases_for_ci", stats.MIN_CASES)
    rows: list[dict] = []
    pairs: dict[str, int] = {}
    skills = sorted({r["skill"] for r in new} | {r["skill"] for r in reference})
    for scope in skills + ["ALL"]:
        ref_runs = [r for r in reference if scope == "ALL" or r["skill"] == scope]
        new_runs = [r for r in new if scope == "ALL" or r["skill"] == scope]
        common = ({(r["host"], r["case"], r["rep"]) for r in ref_runs} & {(r["host"], r["case"], r["rep"]) for r in new_runs})
        pairs[scope] = len(common)

        # absolute: gap markers left in reader-facing output, as a share of those runs (new run alone)
        readers = [r for r in new_runs if r["kind"] == "reader"]
        leaking = [r for r in readers if (r["metrics"].get("gap_markers_leaked") or 0) > 0]
        ref_readers = [r for r in ref_runs if r["kind"] == "reader"]
        ref_rate = (sum((r["metrics"].get("gap_markers_leaked") or 0) > 0 for r in ref_readers) / len(ref_readers)
                    if ref_readers else None)
        limit = absolute.get("leaked_marker_run_rate_max", 0.0)
        if readers:
            rate = len(leaking) / len(readers)
            names = sorted({f"{r['case']}#{r['rep']}" for r in leaking})
            rows.append(_row(scope, "absolute", "leaked marker run rate (reader-facing)", ref_rate, rate,
                             None if ref_rate is None else rate - ref_rate, None, "FAIL" if rate > limit else "ok",
                             f"{len(leaking)} of {len(readers)} reader-facing runs; limit {limit:g}"
                             + (": " + ", ".join(names[:4]) + (" ..." if len(names) > 4 else "") if names else ""),
                             len(readers)))
        if not common:
            rows.append(_row(scope, "pairing", "-", None, None, None, None, "n/a", "no (host, case, rep) in both runs"))
            continue

        for metric, rule in soft.items():
            if not rule.get("gated", True) or stats.METRICS[metric]["direction"] is None:
                continue
            a, b = _index(ref_runs, metric), _index(new_runs, metric)
            keys = common & set(a) & set(b)
            if not keys:
                continue
            rows.append(_paired_rule(scope, metric, rule, {k: a[k] for k in keys}, {k: b[k] for k in keys}, min_cases))
    return {"rows": rows, "failed": any(r["verdict"] == "FAIL" for r in rows), "pairs": pairs}


# ---------------------------------------------------------------- weak spots of the reference


def weak_spots(reference: list[dict], other: list[dict], config: dict) -> list[dict]:
    """Where the reference is worse than `other` with the 95% CI of the difference excluding zero, per skill and ALL,
    for every metric in config.json "metrics" (gated or not). Worst relative to the tolerance first."""
    out = []
    for scope in sorted({r["skill"] for r in reference} | {r["skill"] for r in other}) + ["ALL"]:
        ref_runs = [r for r in reference if scope == "ALL" or r["skill"] == scope]
        oth_runs = [r for r in other if scope == "ALL" or r["skill"] == scope]
        for metric, rule in config["metrics"].items():
            direction = stats.METRICS[metric]["direction"]
            if direction is None:
                continue
            a, b = _index(oth_runs, metric), _index(ref_runs, metric)
            keys = set(a) & set(b)
            if not keys:
                continue
            p = stats.paired({k: a[k] for k in keys}, {k: b[k] for k in keys}, f"weak {scope}:{metric}")
            worse_by, worse_lo, _ = _worsening(p["diff"], p["ci"], direction)
            if p["n_cases"] < config.get("min_cases_for_ci", stats.MIN_CASES) or worse_lo is None or worse_lo <= 0:
                continue
            out.append({"scope": scope, "metric": metric, "gated": rule.get("gated", True),
                        "reference": _round(p["b_mean"]), "other": _round(p["a_mean"]), "worse_by": _round(worse_by),
                        "ci": [_round(p["ci"][0]), _round(p["ci"][1])], "n_cases": p["n_cases"],
                        "tolerance": rule.get("tolerance", 0.0)})
    out.sort(key=lambda s: (s["scope"] == "ALL", -s["worse_by"] / (s["tolerance"] or 1.0)))
    return out


def weak_spots_report(ref: dict, other_runs: list[dict], other_id: str, config: dict) -> dict:
    return {"schema": SCHEMA, "metrics_version": stats.METRICS_VERSION, "reference_run": ref["run"]["id"],
            "other_run": other_id, "spots": weak_spots(ref["runs"], other_runs, config)}


# ---------------------------------------------------------------- output


def _fmt(v, digits=3):
    if v is None:
        return "-"
    s = f"{v:.{digits}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in {"", "-0"} else s


def render_weak_spots(weak: dict | None, ref_meta: dict, result: dict) -> list[str]:
    """Lines for the check output; the reference's weak spots are listed, never blessed."""
    if not weak:
        return ["Known weak spots of the reference: none recorded (run: gate.py weak OTHER_RUN)."]
    if weak.get("reference_run") != ref_meta["run"]["id"] or weak.get("metrics_version") != ref_meta["metrics_version"]:
        return [f"Known weak spots: the recorded list is for reference {weak.get('reference_run')} "
                f"(metrics v{weak.get('metrics_version')}), not {ref_meta['run']['id']}; regenerate with gate.py weak."]
    if not weak["spots"]:
        return [f"Known weak spots of the reference: none against {weak['other_run']}."]
    verdict_of = {(r["scope"], r["metric"]): r["verdict"] for r in result["rows"]}
    lines = [f"Known weak spots: the reference is worse than run {weak['other_run']} here (95% CI of the difference "
             "excludes zero). Passing the gate does not mean these are fine.", ""]
    table = []
    for s in weak["spots"]:
        table.append([s["scope"][:18], s["metric"], _fmt(s["reference"]), _fmt(s["other"]), f"{s['worse_by']:+.3g}",
                      f"[{_fmt(s['ci'][0])}, {_fmt(s['ci'][1])}]", "gated" if s["gated"] else "not gated",
                      verdict_of.get((s["scope"], s["metric"]), "-")])
    return lines + stats._table(["scope", "metric", "reference", weak["other_run"][:14], "reference worse by", "95% CI",
                                 "rule", "this run"], table)


def render(result: dict, ref_meta: dict, new_info: dict, show_all: bool = False, weak: dict | None = None) -> str:
    rows = result["rows"]
    run = ref_meta["run"]
    lines = [f"Reference: run {run['id']} ({', '.join(run['hosts'])}; model {run['model']}; {run['cases']} cases x "
             f"{run['repeat']} reps; condition {ref_meta['condition']}; metrics v{ref_meta['metrics_version']})",
             f"New:       run {new_info.get('id', '?')}",
             "Paired runs: " + ", ".join(f"{k} {v}" for k, v in result["pairs"].items()), ""]
    shown = [r for r in rows if show_all or r["scope"] == "ALL" or r["verdict"] in {"FAIL", "warn"}]
    table = []
    for r in shown:
        ci = "" if r["ci"] is None else f"[{_fmt(r['ci'][0])}, {_fmt(r['ci'][1])}]"
        table.append([r["scope"][:18], r["metric"], _fmt(r["reference"]), _fmt(r["new"]),
                      "" if r["delta"] is None else ("0" if abs(r["delta"]) < 5e-7 else f"{r['delta']:+.3g}"), ci, r["verdict"]])
    lines += stats._table(["scope", "metric", "reference", "new", "delta", "95% CI", "verdict"], table) + [""]
    hidden = len(rows) - len(shown)
    if hidden:
        lines.append(f"({hidden} unremarkable per-skill rows hidden; --all shows them)")
    fails = [r for r in rows if r["verdict"] == "FAIL"]
    warns = [r for r in rows if r["verdict"] == "warn"]
    if fails:
        lines += ["", "FAILED:"] + [f"  {r['scope']}: {r['metric']} ({r['rule']}): reference {_fmt(r['reference'])}, new "
                                      f"{_fmt(r['new'])}; {r['detail']}" for r in fails]
    if warns:
        lines += ["", "Warnings (worse than tolerance, CI reaches back inside it):"] + [
            f"  {r['scope']}: {r['metric']}: delta {r['delta']:+.3g}" for r in warns]
    if not ref_meta.get("same_run"):
        lines += ["", *render_weak_spots(weak, ref_meta, result)]
    lines += ["", "GATE FAILED" if fails else "GATE PASSED"]
    return "\n".join(lines)


def _load_reference(reference_path: Path) -> dict | str:
    ref = json.loads(reference_path.read_text(encoding="utf-8"))
    if ref.get("schema") != SCHEMA or ref.get("metrics_version") != stats.METRICS_VERSION:
        return (f"reference was frozen with metrics v{ref.get('metrics_version')} (schema {ref.get('schema')}); this is "
                f"v{stats.METRICS_VERSION}. Not comparable: freeze a new reference.")
    return ref


def _drift_note(ref: dict) -> str:
    drift = {k: (ref["tools"].get(k), v) for k, v in stats.tool_fingerprint().items() if ref["tools"].get(k) != v}
    if not drift:
        return ""
    return ("WARNING: scoring files changed since the reference was frozen (" + ", ".join(sorted(drift)) +
            "); values may not be comparable. Re-freeze if the change is intended.\n\n")


def check(run_dir: Path, reference_path: Path, config_path: Path, show_all: bool = False,
          weak_path: Path | None = None) -> tuple[int, str]:
    ref = _load_reference(reference_path)
    if isinstance(ref, str):
        return 2, ref
    config = json.loads(config_path.read_text(encoding="utf-8"))
    info, records = stats.read_run(run_dir, set(ref["run"]["hosts"]))
    new = _gated_records(records, ref["condition"])
    if not new:
        return 2, f"no '{ref['condition']}' runs on hosts {ref['run']['hosts']} in {run_dir}"
    result = evaluate(ref["runs"], new, config)
    weak_path = weak_path or reference_path.with_name(WEAK_SPOTS.name)
    weak = json.loads(weak_path.read_text(encoding="utf-8")) if weak_path.is_file() else None
    return (1 if result["failed"] else 0), _drift_note(ref) + render(result, ref, info, show_all, weak)


def check_in_run(run_dir: Path, reference_condition: str, config_path: Path, show_all: bool = False,
                 condition: str = "skill") -> tuple[int, str]:
    """Gate the runs of `condition` (default skill) against another condition of the same run (an A/B variant),
    with the rules of config.json. Both sides are paired on (host, case, rep) by evaluate(). Two variants of the
    same ref give a true A/A test: independent reruns of identical skills."""
    if not reference_condition.startswith(VARIANT_PREFIX):
        return 2, f"--reference-condition must be a variant-NAME condition, got {reference_condition!r}"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    info, records = stats.read_run(run_dir)
    reference, new = _gated_records(records, reference_condition), _gated_records(records, condition)
    for name, runs in ((reference_condition, reference), (condition, new)):
        if not runs:
            return 2, f"no '{name}' runs in {run_dir}"
    hosts = sorted({r["host"] for r in reference} & {r["host"] for r in new})
    if not hosts:
        return 2, f"'{reference_condition}' and '{condition}' runs in {run_dir} share no host"
    reference, new = ([r for r in runs if r["host"] in hosts] for runs in (reference, new))
    run_id = info.get("id", run_dir.name)
    variant = (info.get("variants") or {}).get(reference_condition[len(VARIANT_PREFIX):])
    label = f"{run_id} / {reference_condition}" + (f" = {variant['ref']} @ {variant['sha'][:10]}" if variant else "")
    ref_meta = {"condition": reference_condition, "metrics_version": stats.METRICS_VERSION, "same_run": True,
                "run": {"id": label, "hosts": hosts, "cases": len({r["case"] for r in reference}),
                        "repeat": info.get("repeat"), "model": "; ".join(f"{k} {v}" for k, v in (info.get("models") or {}).items())
                        or "host default"}}
    result = evaluate(reference, new, config)
    return (1 if result["failed"] else 0), render(result, ref_meta, {"id": f"{run_id} / {condition}"}, show_all)


# ---------------------------------------------------------------- A/A noise test


def aa_pseudo_runs(runs: list[dict]) -> list[tuple[str, list[dict], list[dict]]]:
    """(name, reference side, pseudo-run) built from the repetitions of one run. Every pseudo-run holds outputs the
    reference holds too, only attached to another repetition number, so any difference is rerun noise."""
    reps = sorted({r["rep"] for r in runs})
    out = []
    if len(reps) < 2:
        return out

    def relabel(rs, mapping):
        return [{**r, "rep": mapping[r["rep"]]} for r in rs if r["rep"] in mapping]

    for k in range(1, len(reps)):  # shifted: r1->r2, r2->r3, r3->r1 for k = 1
        mapping = {reps[i]: reps[(i + k) % len(reps)] for i in range(len(reps))}
        arrow = ", ".join(f"r{a}->r{b}" for a, b in mapping.items())
        out.append((f"reps shifted by {k} ({arrow})", runs, relabel(runs, mapping)))
    for a in reps:  # one repetition of the reference against one other repetition, as a single-repetition rerun
        for b in reps:
            if a != b:
                out.append((f"single rep r{b} vs r{a}", [r for r in runs if r["rep"] == a],
                            relabel([r for r in runs if r["rep"] == b], {b: a})))
    return out


def aa_report(runs: list[dict], config: dict, run_id: str, condition: str = "skill") -> tuple[int, str]:
    """A/A test of run records (see aa_pseudo_runs): exit code and text. Pure function of its inputs."""
    cases = aa_pseudo_runs(runs)
    if not cases:
        return 2, f"run {run_id} has a single repetition; an A/A test needs at least two"
    lines = [f"A/A test on run {run_id}, condition {condition}: {len(runs)} runs, repetitions "
             f"{sorted({r['rep'] for r in runs})}. The pseudo-runs hold the run's own outputs, so the gate must pass on all.", ""]
    table, details, any_fail = [], [], False
    own_defects: dict[str, str] = {}
    for name, ref, pseudo in cases:
        result = evaluate(ref, pseudo, config)
        # the absolute rule has no noise to test: a leak in the run's own outputs is a defect of that run, listed below
        for r in result["rows"]:
            if r["rule"] == "absolute" and r["verdict"] == "FAIL" and r["scope"] == "ALL":
                own_defects.setdefault(r["metric"], r["detail"])
        fails = [r for r in result["rows"] if r["verdict"] == "FAIL" and r["rule"] != "absolute"]
        warns = [r for r in result["rows"] if r["verdict"] == "warn"]
        any_fail |= bool(fails)
        table.append([name, str(result["pairs"]["ALL"]), str(len(fails)), str(len(warns)), "FAIL" if fails else "PASS"])
        for r in fails:
            details.append(f"  {name}: {r['verdict']} {r['scope']}: {r['metric']} delta {_fmt(r['delta'])} "
                           f"CI {r['ci'] and [_fmt(r['ci'][0]), _fmt(r['ci'][1])]}; {r['detail']}")
    lines += stats._table(["pseudo-run", "paired runs", "FAIL rows", "warn rows", "gate"], table)
    if details:
        lines += ["", "FAIL rows (warn rows are not listed: a point estimate beyond tolerance whose CI reaches back inside it):"] + details
    if own_defects:
        lines += ["", "Absolute rules (not noise-testable, not counted above): the run itself carries a defect:"] + [
            f"  {m}: {d}" for m, d in own_defects.items()]
    lines += ["", "A/A FAILED: the gate fires on rerun noise" if any_fail else "A/A PASSED"]
    return (1 if any_fail else 0), "\n".join(lines)


def aa(run_dir: Path, config_path: Path, condition: str = "skill") -> tuple[int, str]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    info, records = stats.read_run(run_dir)
    runs = _gated_records(records, condition)
    if not runs:
        return 2, f"no '{condition}' runs in {run_dir}"
    return aa_report(runs, config, info.get("id", run_dir.name), condition)


# ---------------------------------------------------------------- command line


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze", help="write the reference from a run")
    f.add_argument("run_dir")
    f.add_argument("--out", default=str(REFERENCE))
    f.add_argument("--condition", default="skill")
    f.add_argument("--model", help="model name to record (run.json has none when the host default was used)")
    f.add_argument("--host", action="append")
    c = sub.add_parser("check", help="gate a run against the reference")
    c.add_argument("run_dir")
    c.add_argument("--against", default=str(REFERENCE))
    c.add_argument("--reference-condition", metavar="variant-NAME",
                   help="gate this run's skill runs against that variant of the same run instead of a frozen reference")
    c.add_argument("--config", default=str(CONFIG))
    c.add_argument("--weak-spots", help="weak spots file (default: weak_spots.json next to the reference)")
    c.add_argument("--all", action="store_true", help="show every per-skill row")
    c.add_argument("--condition", default="skill",
                   help="with --reference-condition: the side to gate (a second variant of the same ref = A/A)")
    a = sub.add_parser("aa", help="gate relabelled repetitions of a run against the run itself (must pass)")
    a.add_argument("run_dir")
    a.add_argument("--config", default=str(CONFIG))
    a.add_argument("--condition", default="skill")
    w = sub.add_parser("weak", help="record where the reference is worse than another run")
    w.add_argument("other_run_dir")
    w.add_argument("--against", default=str(REFERENCE))
    w.add_argument("--config", default=str(CONFIG))
    w.add_argument("--out", default=str(WEAK_SPOTS))
    args = parser.parse_args(argv)
    if args.cmd == "freeze":
        ref = freeze(Path(args.run_dir), args.condition, args.model, set(args.host or []))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(ref, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"froze {len(ref['runs'])} '{args.condition}' runs of {ref['run']['id']} -> {args.out} "
              f"(metrics v{ref['metrics_version']})")
        return 0
    if args.cmd == "aa":
        code, text = aa(Path(args.run_dir), Path(args.config), args.condition)
        print(text, file=sys.stderr if code == 2 else sys.stdout)
        return code
    if args.cmd == "weak":
        ref = _load_reference(Path(args.against))
        if isinstance(ref, str):
            print(ref, file=sys.stderr)
            return 2
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        info, records = stats.read_run(Path(args.other_run_dir), set(ref["run"]["hosts"]))
        other = _gated_records(records, ref["condition"])
        if not other:
            print(f"no '{ref['condition']}' runs in {args.other_run_dir}", file=sys.stderr)
            return 2
        report = weak_spots_report(ref, other, info.get("id", Path(args.other_run_dir).name), config)
        Path(args.out).write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{len(report['spots'])} weak spots of {report['reference_run']} vs {report['other_run']} -> {args.out}")
        return 0
    if args.reference_condition:
        code, text = check_in_run(Path(args.run_dir), args.reference_condition, Path(args.config), args.all,
                                  args.condition)
    else:
        code, text = check(Path(args.run_dir), Path(args.against), Path(args.config), args.all,
                           Path(args.weak_spots) if args.weak_spots else None)
    print(text, file=sys.stderr if code == 2 else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
