#!/usr/bin/env python3
"""Deterministic grader for the Oh My Writing benchmark.

Usage:
  python3 evals/grade.py --validate            check every case file
  python3 evals/grade.py RUN_DIR               (re)grade a results directory written by run.py

Checks are mechanical (see evals/README.md). They catch invented numbers, lost negations,
missing markers, leftover stock phrases and leaked context; they do not measure prose quality.
"""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CASES_DIR = REPO / "evals" / "cases"
SKILLS_DIR = REPO / "skills"
SCRIPTS = SKILLS_DIR / "anti-slop-editing" / "scripts"
FACT_DIFF = SCRIPTS / "fact_diff.py"
SLOP_SCAN = SCRIPTS / "slop_scan.py"

FACT_CATEGORIES = {"numbers", "negations", "certainty", "scope", "names", "urls", "code", "code_blocks",
                   "quotes", "citations"}
# Categories where how often an item occurs matters (a dropped "not" among five); others compare as sets.
COUNTED = {"negations", "certainty", "scope"}
MARKER_KINDS = ["ASK AUTHOR", "VERIFY", "UNTESTED"]
CHECK_FIELDS = {
    "contains": {"values"}, "contains_any": {"values"}, "not_contains": {"values"},
    "regex": {"pattern"}, "not_regex": {"pattern"},
    "no_added_facts": set(), "preserves": {"source"},
    "slop_absent": {"patterns"}, "max_slop": {"max"},
    "markers": set(), "similarity": {"source"}, "word_count": set(),
}
TARGETS = {"output", "reply", "both"}


# ---------------------------------------------------------------- cases

def load_cases(patterns: list[str] | None = None) -> list[dict]:
    cases = []
    for path in sorted(CASES_DIR.glob("*/*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        case["_path"] = str(path.relative_to(REPO))
        if not patterns or any(fnmatch.fnmatch(case.get("id", ""), p) for p in patterns):
            cases.append(case)
    return cases


def validate_case(case: dict) -> list[str]:
    errs = []
    path = Path(case.get("_path", ""))
    expected_id = f"{path.parent.name}/{path.stem}" if path.name else None
    for key in ("id", "skill", "description", "prompt", "files", "output", "checks"):
        if key not in case:
            errs.append(f"missing key {key!r}")
    if errs:
        return errs
    if expected_id and case["id"] != expected_id:
        errs.append(f"id {case['id']!r} should be {expected_id!r}")
    if not (SKILLS_DIR / case["skill"] / "SKILL.md").is_file():
        errs.append(f"unknown skill {case['skill']!r}")
    if case["skill"] in case["prompt"]:
        errs.append("prompt must not name the skill")
    if case["output"] not in case["prompt"]:
        errs.append(f"prompt must say where to save the output ({case['output']})")
    if not isinstance(case["files"], dict) or not all(isinstance(v, str) for v in case["files"].values()):
        errs.append("files must map names to text")
    if not case["checks"]:
        errs.append("at least one check is required")
    for i, check in enumerate(case["checks"]):
        where = f"checks[{i}]"
        kind = check.get("type")
        if kind not in CHECK_FIELDS:
            errs.append(f"{where}: unknown type {kind!r}")
            continue
        missing = CHECK_FIELDS[kind] - set(check)
        if missing:
            errs.append(f"{where}: {kind} needs {sorted(missing)}")
        if check.get("target", "output") not in TARGETS:
            errs.append(f"{where}: target must be one of {sorted(TARGETS)}")
        for key in ("pattern",):
            if key in check:
                try:
                    re.compile(check[key], re.M)
                except re.error as exc:
                    errs.append(f"{where}: bad regex: {exc}")
        cats = check.get("categories", [])
        bad = set(cats) - FACT_CATEGORIES
        if bad:
            errs.append(f"{where}: unknown categories {sorted(bad)}")
        for key in ("source",):
            if key in check and check[key] not in case["files"]:
                errs.append(f"{where}: source {check[key]!r} is not an input file")
        for src in check.get("sources", []):
            if src not in case["files"]:
                errs.append(f"{where}: source {src!r} is not an input file")
    return errs


# ---------------------------------------------------------------- helper scripts

def _run_json(cmd: list[str], ok_codes=(0, 1)) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode not in ok_codes:
        raise RuntimeError(f"{Path(cmd[1]).name} failed ({proc.returncode}): {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _load_fact_diff():
    spec = importlib.util.spec_from_file_location("fact_diff", FACT_DIFF)
    module = importlib.util.module_from_spec(spec)
    keep, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ inside the shipped skill
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = keep
    return module


FACT = _load_fact_diff()


def fact_diff(before: str, after: str) -> dict:
    return FACT.build_report(before, after)


def slop_findings(text: str, profile: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "text.md"
        path.write_text(text, encoding="utf-8")
        return _run_json([sys.executable, str(SLOP_SCAN), "--json", "--profile", profile, str(path)],
                         ok_codes=(0,))["findings"]


# ---------------------------------------------------------------- checks

def _norm(s: str, case_sensitive: bool) -> str:
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return s if case_sensitive else s.casefold()


def _words(s: str) -> list[str]:
    return re.findall(r"\S+", s)


def _contains(check, text):
    cs = check.get("case_sensitive", False)
    hay = _norm(text, cs)
    hits = [v for v in check["values"] if _norm(v, cs) in hay]
    return hits


def check_contains(check, text, case):
    hits = _contains(check, text)
    missing = [v for v in check["values"] if v not in hits]
    return not missing, f"missing: {missing}" if missing else "all present"


def check_contains_any(check, text, case):
    hits = _contains(check, text)
    return bool(hits), f"found: {hits}" if hits else f"none of {check['values']}"


def check_not_contains(check, text, case):
    hits = _contains(check, text)
    return not hits, f"found: {hits}" if hits else "none present"


def check_regex(check, text, case):
    m = re.search(check["pattern"], text, re.M)
    return bool(m), f"matched {m.group(0)[:80]!r}" if m else "no match"


def check_not_regex(check, text, case):
    m = re.search(check["pattern"], text, re.M)
    return not m, f"matched {m.group(0)[:80]!r}" if m else "no match"


def _items(report: dict, cat: str, kind: str) -> list[dict]:
    return report["categories"].get(cat, {}).get(kind, [])


def _is_input_file_link(item: str, case: dict) -> bool:
    """A relative link to one of the case's own input files (a memo citing its source) is not a new URL."""
    return "://" not in item and item.split("#")[0].replace("\\", "/").rsplit("/", 1)[-1] in case["files"]


def check_no_added_facts(check, text, case):
    names = check.get("sources") or list(case["files"])
    sources = "\n\n".join([case["files"][n] for n in names] + [case["prompt"]])
    report = fact_diff(sources, text)
    allow = {a.casefold() for a in check.get("allow", [])}
    lexicon = FACT.word_set(sources)
    added = []
    for cat in check.get("categories", ["numbers", "citations", "urls"]):
        for it in _items(report, cat, "added"):
            if it["before"] != 0 or it["item"].casefold() in allow:
                continue
            if cat == "names" and not [w for w in FACT.new_name_words(it["item"], lexicon) if w not in allow]:
                continue
            if cat == "urls" and _is_input_file_link(it["item"], case):
                continue
            added.append(f"{cat}:{it['item']}")
    return not added, f"added: {added}" if added else "nothing added"


def check_preserves(check, text, case):
    report = fact_diff(case["files"][check["source"]], text)
    allow = {a.casefold() for a in check.get("allow_lost", [])}
    lost = []
    for cat in check.get("categories", ["numbers", "negations"]):
        for it in _items(report, cat, "lost"):
            gone = it["after"] < it["before"] if cat in COUNTED else it["after"] == 0
            if gone and it["item"].casefold() not in allow:
                lost.append(f"{cat}:{it['item']} ({it['before']}->{it['after']})")
    return not lost, f"lost: {lost}" if lost else "all kept"


def check_slop_absent(check, text, case):
    found = {f["pattern"] for f in slop_findings(text, check.get("profile", "professional"))}
    hits = sorted(found & set(check["patterns"]))
    return not hits, f"still present: {hits}" if hits else "none present"


def check_max_slop(check, text, case):
    n = len(slop_findings(text, check.get("profile", "professional")))
    return n <= check["max"], f"{n} findings (max {check['max']})"


def check_markers(check, text, case):
    kinds = check.get("kinds", MARKER_KINDS)
    n = len(re.findall(r"\[(?:" + "|".join(map(re.escape, kinds)) + r")\b", text))
    lo, hi = check.get("min", 1), check.get("max")
    ok = n >= lo and (hi is None or n <= hi)
    return ok, f"{n} markers (min {lo}, max {hi})"


def check_similarity(check, text, case):
    a = _words(case["files"][check["source"]])
    b = _words(text)
    ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    lo, hi = check.get("min", 0.0), check.get("max", 1.0)
    return lo <= ratio <= hi, f"similarity {ratio:.3f} (range {lo}-{hi})"


def check_word_count(check, text, case):
    n = len(_words(text))
    lo, hi = check.get("min", 0), check.get("max")
    return n >= lo and (hi is None or n <= hi), f"{n} words (min {lo}, max {hi})"


CHECKS = {name: globals()[f"check_{name}"] for name in CHECK_FIELDS}


def grade_case(case: dict, output: str | None, reply: str) -> dict:
    """Grade one run. output is the deliverable file text (None when the agent wrote no file)."""
    results = [{"type": "output_present", "passed": output is not None,
                "detail": "found" if output is not None else f"{case['output']} was not written"}]
    for check in case["checks"]:
        target = check.get("target", "both" if check["type"] == "markers" else "output")
        if target == "reply":
            text = reply
        elif target == "both":
            text = (output or "") + "\n\n" + reply
        else:
            text = output
        if text is None:
            results.append({"type": check["type"], "passed": False, "detail": "no output to check"})
            continue
        try:
            passed, detail = CHECKS[check["type"]](check, text, case)
        except Exception as exc:  # a broken helper must fail the check, not the whole run
            passed, detail = False, f"error: {exc}"
        results.append({"type": check["type"], "passed": passed, "detail": detail, "note": check.get("note")})
    return {"passed": all(r["passed"] for r in results), "score": sum(r["passed"] for r in results) / len(results),
            "checks": results}


# ---------------------------------------------------------------- run directories

def grade_run(run_dir: Path) -> dict:
    cases = {c["id"]: c for c in load_cases()}
    runs = []
    for meta_path in sorted((run_dir / "runs").glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        case = cases.get(meta["case"])
        if case is None:
            continue
        out_path = meta_path.parent / "workspace" / case["output"]
        output = out_path.read_text(encoding="utf-8", errors="replace") if out_path.is_file() else None
        reply_path = meta_path.parent / "reply.md"
        reply = reply_path.read_text(encoding="utf-8", errors="replace") if reply_path.is_file() else ""
        grade = grade_case(case, output, reply)
        runs.append({**{k: meta.get(k) for k in ("case", "skill", "host", "condition", "skill_loaded",
                                                  "exit_code", "duration_s", "error")}, **grade})
    judge_path = run_dir / "judge.json"
    judge = json.loads(judge_path.read_text(encoding="utf-8")) if judge_path.is_file() else []
    info_path = run_dir / "run.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.is_file() else {}
    results = {"run": info, "runs": runs, "judge": judge, "summary": summarize(runs, judge)}
    (run_dir / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "report.md").write_text(render_report(results), encoding="utf-8")
    return results


def _rate(rows: list[dict]) -> float | None:
    return sum(r["passed"] for r in rows) / len(rows) if rows else None


def host_failed(r: dict) -> bool:
    """The host crashed or timed out before writing the output: an infrastructure error, not a skill failure."""
    return bool(r.get("error")) and not r["checks"][0]["passed"]


def summarize(runs: list[dict], judge: list[dict]) -> dict:
    hosts = sorted({r["host"] for r in runs})
    skills = sorted({r["skill"] for r in runs})
    broken = {(r["case"], r["host"]) for r in runs if host_failed(r)}
    present: dict[tuple, set] = {}
    for r in runs:
        present.setdefault((r["case"], r["host"]), set()).add(r["condition"])
    conditions = {r["condition"] for r in runs}
    broken |= {pair for pair, conds in present.items() if conds != conditions}  # one side missing: unpaired
    by = {}
    for host in hosts:
        for skill in skills + ["ALL"]:
            rows = [r for r in runs if r["host"] == host and (skill == "ALL" or r["skill"] == skill)]
            # Compare like with like: a case counts only when both conditions produced a gradable run.
            valid = [r for r in rows if (r["case"], r["host"]) not in broken]
            s = [r for r in valid if r["condition"] == "skill"]
            b = [r for r in valid if r["condition"] == "baseline"]
            ps, pb = _rate(s), _rate(b)
            by[f"{host}/{skill}"] = {
                "skill_pass": ps, "baseline_pass": pb,
                "delta": None if ps is None or pb is None else ps - pb,
                "skill_n": len(s), "baseline_n": len(b),
                "skill_loaded": _rate([{"passed": bool(r["skill_loaded"])} for r in s]),
                "excluded": len({r["case"] for r in rows if (r["case"], r["host"]) in broken}),
            }
    failing = {}
    for r in runs:
        if host_failed(r):
            continue
        for c in r["checks"]:
            if not c["passed"]:
                key = f"{r['condition']}:{c['type']}"
                failing[key] = failing.get(key, 0) + 1
    verdicts = {"skill": 0, "baseline": 0, "tie": 0, "inconsistent": 0, "error": 0}
    for j in judge:
        verdicts[j["winner"]] = verdicts.get(j["winner"], 0) + 1
    return {"by": by, "failing_checks": dict(sorted(failing.items())), "judge": verdicts}


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


def render_report(results: dict) -> str:
    info, runs, summary = results["run"], results["runs"], results["summary"]
    lines = ["# Oh My Writing benchmark report", ""]
    if info:
        lines += [f"Run `{info.get('id')}` at {info.get('started')}; hosts {', '.join(info.get('hosts', []))}; "
                  f"{info.get('cases')} cases; models {info.get('models') or 'host default'}."]
        if info.get("contaminated"):
            lines += ["", "**Warning:** user-level skills with the same names were installed; the baseline may have "
                          "seen them."]
        lines += [""]
    lines += ["## Pass rate by skill", "",
              "A case counts only when both conditions produced a gradable run. Cases with a host error (crash, "
              "quota or timeout with no output) or with one condition missing are left out of both rates and "
              "counted as excluded.", "",
              "| host / skill | with skills | baseline | difference | skill loaded | n | excluded cases |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for key, v in summary["by"].items():
        diff = "n/a" if v["delta"] is None else f"{v['delta'] * 100:+.0f} pts"
        label = f"**{key}**" if key.endswith("/ALL") else key
        lines.append(f"| {label} | {_pct(v['skill_pass'])} | {_pct(v['baseline_pass'])} | {diff} | "
                     f"{_pct(v['skill_loaded'])} | {v['skill_n']}+{v['baseline_n']} | {v['excluded']} |")
    lines += ["", "## Cases", "", "| case | host | baseline | with skills | failed checks (with skills / baseline) |",
              "|---|---|:---:|:---:|---|"]
    index = {(r["case"], r["host"], r["condition"]): r for r in runs}
    for case, host in sorted({(r["case"], r["host"]) for r in runs}):
        s, b = index.get((case, host, "skill")), index.get((case, host, "baseline"))

        def mark(r):
            if r is None:
                return "-"
            return "ERROR" if host_failed(r) else ("PASS" if r["passed"] else "FAIL")

        def fails(r):
            if r is None:
                return "-"
            if host_failed(r):
                return f"host error: {r['error']}"[:200]
            bad = [f"{c['type']} ({c['detail']})" for c in r["checks"] if not c["passed"]]
            return "; ".join(bad) or "none"

        lines.append(f"| {case} | {host} | {mark(b)} | {mark(s)} | {fails(s)} / {fails(b)} |".replace("\n", " "))
    if summary["failing_checks"]:
        lines += ["", "## Failed checks by type", "", "| condition:check | failures |", "|---|---:|"]
        lines += [f"| {k} | {v} |" for k, v in summary["failing_checks"].items()]
    if results["judge"]:
        j = summary["judge"]
        lines += ["", "## Blind pairwise judge", "",
                  f"Preferred with-skills output: {j['skill']}; baseline: {j['baseline']}; tie: {j['tie']}; "
                  f"inconsistent across swapped order: {j['inconsistent']}; judge error (no verdict): "
                  f"{j.get('error', 0)}.", "",
                  "| case | host | judge | winner | reason |", "|---|---|---|---|---|"]
        for r in results["judge"]:
            reason = (r.get("reason") or "").replace("|", "/").replace("\n", " ")[:160]
            lines.append(f"| {r['case']} | {r['host']} | {r['judge']} | {r['winner']} | {reason} |")
    lines += ["", "## Limits", "",
              "Checks are mechanical: they detect invented numbers, names and citations, lost negations and qualifiers, "
              "missing gap markers, leftover stock patterns and leaked context. They do not measure prose quality, "
              "argument strength or voice. The judge is a single model's preference. Case counts are small; a difference "
              "of one or two cases is noise. Hosts run with their default model unless the run lists one.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run_dir", nargs="?", help="results directory written by run.py")
    parser.add_argument("--validate", action="store_true", help="validate every case file and exit")
    args = parser.parse_args(argv)
    if args.validate or not args.run_dir:
        bad = 0
        cases = load_cases()
        for case in cases:
            for err in validate_case(case):
                bad += 1
                print(f"[FAIL] {case.get('_path')}: {err}")
        print(f"[OK] {len(cases)} cases valid" if not bad else f"[FAIL] {bad} problems in {len(cases)} cases")
        return 1 if bad else 0
    results = grade_run(Path(args.run_dir))
    print((Path(args.run_dir) / "report.md").read_text(encoding="utf-8"))
    return 0 if results["runs"] else 1


if __name__ == "__main__":
    sys.exit(main())
