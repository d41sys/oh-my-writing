#!/usr/bin/env python3
"""Regression gate for skill revisions, on the deterministic statistics of evals/stats.py.

Usage:
  python3 evals/gate.py freeze RUN_DIR [--model NAME] [--out evals/gate/reference.json]
  python3 evals/gate.py check  RUN_DIR [--against evals/gate/reference.json] [--config evals/gate/config.json] [--all]

`freeze` records the with-skills outputs of a run (every metric, per case and repetition) together with the run id,
model, skill versions and metric version as the reference. `check` scores a new run the same way, pairs it with the
reference on (host, case, rep) and exits 1 when a skill revision is worse. Per skill and over all skills:

  hard rules (no statistics, tolerances in config.json "hard"):
    invented facts  the new total is above the reference total (plus the configured slack per run)
    leaked markers  any gap marker or placeholder in an output meant for a reader (stats.CASE_KIND = "reader")
    check pass rate the case-check pass rate is below the reference by more than the tolerance
  statistical rule, for every metric listed in config.json "metrics" with "gated": true:
    FAIL when the paired change (new - reference) is worse than the metric's tolerance AND the 95% bootstrap CI of
    the change excludes zero on the worse side. Worse than tolerance with a CI that includes zero is a warning only.

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
SCHEMA = 1


def _round(v):
    return None if v is None else round(v, 6)


# ---------------------------------------------------------------- freeze


def freeze(run_dir: Path, condition: str = "skill", model: str | None = None, hosts: set[str] | None = None) -> dict:
    info, records = stats.read_run(run_dir, hosts)
    runs = [{"case": r["case"], "skill": r["skill"], "kind": r["kind"], "host": r["host"], "rep": r["rep"],
             "metrics": {m: _round(v) for m, v in r["metrics"].items()}}
            for r in records if r["condition"] == condition and not r["host_error"]]
    if not runs:
        raise SystemExit(f"no '{condition}' runs in {run_dir}")
    return {
        "schema": SCHEMA, "metrics_version": stats.METRICS_VERSION, "tools": stats.tool_fingerprint(),
        "condition": condition,
        "run": {"id": info.get("id", run_dir.name), "started": info.get("started"),
                "hosts": sorted({r["host"] for r in runs}), "cases": len({r["case"] for r in runs}),
                "repeat": info.get("repeat"), "host_versions": {k: v for k, v in info.items() if k.endswith("_version")},
                "models": info.get("models") or {}, "model": model or "host default"},
        "skill_versions": stats.skill_versions(), "runs": runs,
    }


# ---------------------------------------------------------------- evaluate


def _index(runs: list[dict], metric: str, only: dict | None = None) -> dict[tuple, float]:
    out = {}
    for r in runs:
        if only and any(r.get(k) != v for k, v in only.items()):
            continue
        v = r["metrics"].get(metric)
        if v is not None:
            out[(r["host"], r["case"], r["rep"])] = v
    return out


def _row(scope, rule, metric, ref, new, delta, ci, verdict, detail="", n=None):
    return {"scope": scope, "rule": rule, "metric": metric, "reference": ref, "new": new, "delta": delta, "ci": ci,
            "verdict": verdict, "detail": detail, "n_cases": n}


def evaluate(reference: list[dict], new: list[dict], config: dict) -> dict:
    """reference and new: run records ({case, skill, kind, host, rep, metrics}). Returns {"rows": [...], "failed": bool,
    "pairs": {scope: n}}. Pure function of its inputs, so the result is the same on every call."""
    hard, soft = config["hard"], config["metrics"]
    min_cases = config.get("min_cases_for_ci", stats.MIN_CASES)
    rows: list[dict] = []
    pairs: dict[str, int] = {}
    skills = sorted({r["skill"] for r in new} | {r["skill"] for r in reference})
    for scope in skills + ["ALL"]:
        only = {} if scope == "ALL" else {"skill": scope}
        ref_runs = [r for r in reference if not only or r["skill"] == scope]
        new_runs = [r for r in new if not only or r["skill"] == scope]
        common = ({(r["host"], r["case"], r["rep"]) for r in ref_runs} & {(r["host"], r["case"], r["rep"]) for r in new_runs})
        pairs[scope] = len(common)
        if not common:
            rows.append(_row(scope, "pairing", "-", None, None, None, None, "n/a", "no (host, case, rep) in both runs"))
            continue

        def both(metric):
            a, b = _index(ref_runs, metric), _index(new_runs, metric)
            keys = common & set(a) & set(b)
            return {k: a[k] for k in keys}, {k: b[k] for k in keys}

        # hard: invented facts
        a, b = both("invented_facts")
        ref_sum, new_sum = sum(a.values()), sum(b.values())
        limit = ref_sum + hard.get("invented_facts_slack_per_run", 0.0) * len(a)
        rows.append(_row(scope, "hard", "invented_facts (total)", ref_sum, new_sum, new_sum - ref_sum, None,
                         "FAIL" if new_sum > limit else "ok", f"over {len(a)} paired runs; limit {limit:g}", len(a)))
        # hard: leaked markers in reader-facing output (absolute, not relative to the reference)
        leaks = [r for r in new_runs if r["kind"] == "reader" and (r["metrics"].get("gap_markers_leaked") or 0) > 0]
        ref_leaks = [r for r in ref_runs if r["kind"] == "reader" and (r["metrics"].get("gap_markers_leaked") or 0) > 0]
        n_new = sum(r["metrics"]["gap_markers_leaked"] for r in leaks)
        n_ref = sum(r["metrics"]["gap_markers_leaked"] for r in ref_leaks)
        names = sorted({f"{r['case']}#{r['rep']}" for r in leaks})
        rows.append(_row(scope, "hard", "leaked markers (reader-facing)", n_ref, n_new, n_new - n_ref, None,
                         "FAIL" if n_new > hard.get("leaked_markers_max", 0) else "ok",
                         ("in " + ", ".join(names[:4]) + (" ..." if len(names) > 4 else "")) if names else "none", None))
        # hard: case-check pass rate
        a, b = both("check_pass_rate")
        ref_rate, new_rate = sum(a.values()) / len(a), sum(b.values()) / len(b)
        tol = hard.get("check_pass_rate_tolerance", 0.0)
        rows.append(_row(scope, "hard", "check_pass_rate", ref_rate, new_rate, new_rate - ref_rate, None,
                         "FAIL" if new_rate < ref_rate - tol else "ok", f"tolerance {tol:g}; {len(a)} paired runs", len(a)))
        # statistical: paired regression beyond tolerance with a CI that excludes zero
        for metric, rule in soft.items():
            spec = stats.METRICS[metric]
            if not rule.get("gated", True) or spec["direction"] is None:
                continue
            a, b = both(metric)
            if not a:
                continue
            p = stats.paired(a, b, f"gate {scope}:{metric}")
            sign = 1 if spec["direction"] == "lower" else -1  # worse = delta * sign > 0
            worse_by = p["diff"] * sign
            ci = p["ci"]
            ci_worse = ci is not None and (ci[0] > 0 if sign == 1 else ci[1] < 0)
            ci_better = ci is not None and (ci[1] < 0 if sign == 1 else ci[0] > 0)
            tol = rule.get("tolerance", 0.0)
            if p["n_cases"] < min_cases:
                verdict = "few"
            elif worse_by > tol and ci_worse:
                verdict = "FAIL"
            elif worse_by > tol:
                verdict = "warn"
            elif ci_better:
                verdict = "better"
            else:
                verdict = "ok"
            rows.append(_row(scope, "stat", metric, p["a_mean"], p["b_mean"], p["diff"], ci, verdict,
                             f"tolerance {tol:g}, {spec['direction']} is better", p["n_cases"]))
    return {"rows": rows, "failed": any(r["verdict"] == "FAIL" for r in rows), "pairs": pairs}


# ---------------------------------------------------------------- output


def _fmt(v, digits=3):
    if v is None:
        return "-"
    s = f"{v:.{digits}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in {"", "-0"} else s


def render(result: dict, ref_meta: dict, new_info: dict, show_all: bool = False) -> str:
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
        lines += ["", "Warnings (worse than tolerance, CI includes zero):"] + [
            f"  {r['scope']}: {r['metric']}: delta {r['delta']:+.3g}" for r in warns]
    lines += ["", "GATE FAILED" if fails else "GATE PASSED"]
    return "\n".join(lines)


def check(run_dir: Path, reference_path: Path, config_path: Path, show_all: bool = False) -> tuple[int, str]:
    ref = json.loads(reference_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if ref.get("schema") != SCHEMA or ref.get("metrics_version") != stats.METRICS_VERSION:
        return 2, (f"reference was frozen with metrics v{ref.get('metrics_version')} (schema {ref.get('schema')}); this is "
                   f"v{stats.METRICS_VERSION}. Not comparable: freeze a new reference.")
    info, records = stats.read_run(run_dir, set(ref["run"]["hosts"]))
    new = [{**r, "metrics": {m: _round(v) for m, v in r["metrics"].items()}}  # same rounding as the stored reference
           for r in records if r["condition"] == ref["condition"] and not r["host_error"]]
    if not new:
        return 2, f"no '{ref['condition']}' runs on hosts {ref['run']['hosts']} in {run_dir}"
    result = evaluate(ref["runs"], new, config)
    text = render(result, ref, info, show_all)
    drift = {k: (ref["tools"].get(k), v) for k, v in stats.tool_fingerprint().items() if ref["tools"].get(k) != v}
    if drift:
        text = ("WARNING: scoring files changed since the reference was frozen (" + ", ".join(sorted(drift)) +
                "); values may not be comparable. Re-freeze if the change is intended.\n\n") + text
    return (1 if result["failed"] else 0), text


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
    c.add_argument("--config", default=str(CONFIG))
    c.add_argument("--all", action="store_true", help="show every per-skill row")
    args = parser.parse_args(argv)
    if args.cmd == "freeze":
        ref = freeze(Path(args.run_dir), args.condition, args.model, set(args.host or []))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(ref, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"froze {len(ref['runs'])} '{args.condition}' runs of {ref['run']['id']} -> {args.out} "
              f"(metrics v{ref['metrics_version']})")
        return 0
    code, text = check(Path(args.run_dir), Path(args.against), Path(args.config), args.all)
    print(text, file=sys.stderr if code == 2 else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
