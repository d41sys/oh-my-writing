#!/usr/bin/env python3
"""Deterministic grader for the Oh My Writing benchmark.

Usage:
  python3 evals/grade.py --validate            check every case file (including its controls)
  python3 evals/grade.py --controls [GLOB]     grade the controls of matching cases; exit 1 on any mismatch
  python3 evals/grade.py RUN_DIR               (re)grade a results directory written by run.py

Checks are mechanical (see evals/README.md). They catch invented numbers, lost negations,
missing markers, leftover stock phrases and leaked context; they do not measure prose quality.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import difflib
import fnmatch
import functools
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import shutil
import sys
import tempfile
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CASES_DIR = REPO / "evals" / "cases"
SKILLS_DIR = REPO / "skills"
SCRIPTS = SKILLS_DIR / "anti-slop-editing" / "scripts"
FACT_DIFF = SCRIPTS / "fact_diff.py"
SLOP_SCAN = SCRIPTS / "slop_scan.py"
INVENTORY = SKILLS_DIR / "project-report" / "scripts" / "inventory.py"
FIXTURES_PREFIX = "evals/fixtures/"
# The installed diagram-design skill's checker (user level; both benchmark conditions see that skill).
DIAGRAM_SKILL = Path.home() / ".agents" / "skills" / "diagram-design"
DIAGRAM_SELF_CHECK = DIAGRAM_SKILL / "scripts" / "self_check.py"
FONT_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}
RASTER_EXT = {".png", ".jpg", ".jpeg", ".webp"}
SLOP_PROFILES = {"casual", "professional", "technical", "academic"}
JUDGE_MODES = {"visual", "style", "reader"}

FACT_CATEGORIES = {"numbers", "negations", "certainty", "scope", "names", "urls", "code", "code_blocks",
                   "quotes", "citations"}
# Categories where how often an item occurs matters (a dropped "not" among five); others compare as sets.
COUNTED = {"negations", "certainty", "scope"}
MARKER_KINDS = ["ASK AUTHOR", "VERIFY", "UNTESTED"]
CHECK_FIELDS = {
    "contains": {"values"}, "contains_any": {"values"}, "not_contains": {"values"},
    "regex": {"pattern"}, "not_regex": {"pattern"},
    "no_added_facts": set(), "preserves": {"source"},
    "slop_absent": {"patterns"}, "max_slop": {"max"}, "slop_density": {"max"}, "rhythm": set(),
    "markers": set(), "similarity": {"source"}, "word_count": set(),
    "facts_recalled": {"facts"}, "diagrams": set(), "html_deliverable": {"path"},
}
# Checks that read files in the run's workspace, not only the output text.
WORKSPACE_CHECKS = {"diagrams", "html_deliverable"}
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


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _rel_path_ok(p) -> bool:
    return isinstance(p, str) and bool(p) and not p.startswith("/") and ".." not in Path(p).parts


def _regex_errors(patterns, where: str) -> list[str]:
    errs = []
    for pat in patterns:
        try:
            re.compile(pat, re.I | re.M)
        except (re.error, TypeError) as exc:
            errs.append(f"{where}: bad regex {pat!r}: {exc}")
    return errs


def _regex_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) for v in value)


def _validate_new_check(kind: str, check: dict, where: str) -> list[str]:
    errs = []
    if kind == "facts_recalled":
        facts = check["facts"]
        if not isinstance(facts, list) or not facts:
            return [f"{where}: facts must be a non-empty list"]
        ids = []
        for j, fact in enumerate(facts):
            here = f"{where}.facts[{j}]"
            if not isinstance(fact, dict) or not isinstance(fact.get("id"), str) or not fact["id"]:
                errs.append(f"{here}: needs a string id")
                continue
            ids.append(fact["id"])
            if not _regex_list(fact.get("any")):
                errs.append(f"{here}: 'any' must be a non-empty list of regex strings")
            else:
                errs += _regex_errors(fact["any"], here)
        if len(ids) != len(set(ids)):
            errs.append(f"{where}: fact ids must be unique")
        if "min" in check and not (_is_num(check["min"]) and 0 <= check["min"] <= 1):
            errs.append(f"{where}: min must be a number from 0 to 1")
    elif kind == "diagrams":
        for key in ("min", "max"):
            if key in check and not (isinstance(check[key], int) and not isinstance(check[key], bool)
                                     and check[key] >= 0):
                errs.append(f"{where}: {key} must be a non-negative integer")
        if not errs and "min" in check and "max" in check and check["min"] > check["max"]:
            errs.append(f"{where}: min is greater than max")
        for key in ("numbers_from_sources", "self_check"):
            if key in check and not isinstance(check[key], bool):
                errs.append(f"{where}: {key} must be true or false")
        if "allow" in check and not (isinstance(check["allow"], list) and all(isinstance(a, str) for a in check["allow"])):
            errs.append(f"{where}: allow must be a list of strings")
        labels = check.get("labels_any", [])
        if not isinstance(labels, list):
            errs.append(f"{where}: labels_any must be a list")
        else:
            for j, label in enumerate(labels):
                here = f"{where}.labels_any[{j}]"
                if not isinstance(label, dict) or not isinstance(label.get("id"), str) or not _regex_list(label.get("any")):
                    errs.append(f"{here}: needs a string id and a non-empty 'any' list of regexes")
                else:
                    errs += _regex_errors(label["any"], here)
        if "labels_none" in check:
            if not _regex_list(check["labels_none"]):
                errs.append(f"{where}: labels_none must be a non-empty list of regex strings")
            else:
                errs += _regex_errors(check["labels_none"], f"{where}.labels_none")
    elif kind == "slop_density":
        if not (_is_num(check["max"]) and check["max"] >= 0):
            errs.append(f"{where}: max must be a non-negative number (findings per 1000 words)")
        if "profile" in check and check["profile"] not in SLOP_PROFILES:
            errs.append(f"{where}: profile must be one of {sorted(SLOP_PROFILES)}")
    elif kind == "rhythm":
        if "min_cv" in check and not (_is_num(check["min_cv"]) and 0 <= check["min_cv"] <= 2):
            errs.append(f"{where}: min_cv must be a number from 0 to 2")
        if "min_sentences" in check and not (isinstance(check["min_sentences"], int)
                                             and not isinstance(check["min_sentences"], bool)
                                             and check["min_sentences"] >= 2):
            errs.append(f"{where}: min_sentences must be an integer of at least 2")
    elif kind == "html_deliverable":
        if not _rel_path_ok(check["path"]):
            errs.append(f"{where}: path must be a relative path inside the workspace")
        for key in ("no_script", "self_contained"):
            if key in check and not isinstance(check[key], bool):
                errs.append(f"{where}: {key} must be true or false")
        if "min_figures" in check and not (isinstance(check["min_figures"], int)
                                           and not isinstance(check["min_figures"], bool) and check["min_figures"] >= 0):
            errs.append(f"{where}: min_figures must be a non-negative integer")
    return errs


def _validate_extras(case: dict) -> list[str]:
    """Validate the optional fields: fixtures, timeout, deliverables, judge, review_stage."""
    errs = []
    fixtures = case.get("fixtures")
    if "fixtures" in case:
        if not (isinstance(fixtures, str) and fixtures.startswith(FIXTURES_PREFIX) and _rel_path_ok(fixtures)
                and len(fixtures) > len(FIXTURES_PREFIX)):
            errs.append(f"fixtures must be a path under {FIXTURES_PREFIX}")
        elif not (REPO / fixtures).is_dir():
            errs.append(f"fixtures directory {fixtures!r} does not exist")
        elif not fixture_files(REPO / fixtures):
            errs.append(f"fixtures directory {fixtures!r} has no files")
    if "timeout" in case and not (isinstance(case["timeout"], int) and not isinstance(case["timeout"], bool)
                                  and case["timeout"] > 0):
        errs.append("timeout must be a positive integer (seconds)")
    deliverables = case.get("deliverables")
    if "deliverables" in case:
        if not (isinstance(deliverables, list) and deliverables and all(_rel_path_ok(d) for d in deliverables)):
            errs.append("deliverables must be a non-empty list of relative paths")
        elif len(set(deliverables)) != len(deliverables):
            errs.append("deliverables must not repeat a path")
    if "style_ref" in case and not (isinstance(case["style_ref"], str) and case["style_ref"] in case.get("files", {})):
        errs.append("style_ref must be the name of one of the case's files")
    if "judge" in case:
        judge = case["judge"]
        if not isinstance(judge, dict) or judge.get("mode") not in JUDGE_MODES:
            errs.append("judge must be an object with mode 'visual', 'style' or 'reader'")
        elif judge["mode"] in ("style", "reader"):
            if "render" in judge:
                errs.append("judge.render belongs to mode 'visual' only")
        elif not _rel_path_ok(judge.get("render")):
            errs.append("judge.render must be a relative path to the HTML to screenshot")
        elif not (isinstance(deliverables, list) and judge["render"] in deliverables):
            errs.append("judge.render must be listed in deliverables")
    if "review_stage" in case:
        errs += _validate_review_stage(case["review_stage"], case.get("files", {}))
    return errs


def _validate_review_stage(stage, files: dict) -> list[str]:
    """review_stage (used by review_stage.py): the case files the reviewer gets, the author's brief for the judge and
    the planted problems, each with a unique id and a description."""
    if not isinstance(stage, dict):
        return ["review_stage must be an object"]
    errs = []
    extra = set(stage) - {"files", "brief", "defects"}
    if extra:
        errs.append(f"review_stage: unknown fields {sorted(extra)}")
    names = stage.get("files")
    if not (isinstance(names, list) and names and all(isinstance(n, str) and n in files for n in names)):
        errs.append("review_stage.files must be a non-empty list of the case's file names")
    if not (isinstance(stage.get("brief"), str) and stage["brief"].strip()):
        errs.append("review_stage.brief must be a non-empty string")
    defects = stage.get("defects")
    if not isinstance(defects, list):
        errs.append("review_stage.defects must be a list (empty when none were planted)")
        return errs
    ids = []
    for i, d in enumerate(defects):
        ok = (isinstance(d, dict) and set(d) == {"id", "description"} and isinstance(d["id"], str)
              and re.fullmatch(r"[A-Za-z0-9_-]+", d["id"]) and isinstance(d["description"], str) and d["description"].strip())
        if not ok:
            errs.append(f"review_stage.defects[{i}] must be {{id: letters, digits, '_' or '-', description: text}}")
        else:
            ids.append(d["id"])
    if len(ids) != len(set(ids)):
        errs.append("review_stage.defects ids must be unique")
    return errs


def _validate_controls(case: dict, check_types: set | None = None) -> list[str]:
    """Validate the shape of the `controls` field: unique names, expect pass/fail, fail controls naming the check
    types they must trip, output and reply text, extra workspace files."""
    controls = case["controls"]
    if not isinstance(controls, list) or not controls:
        return ["controls must be a non-empty list"]
    if check_types is None:
        check_types = {c.get("type") for c in case.get("checks", []) if isinstance(c, dict)}
    known = check_types | {"output_present"}
    errs, names = [], set()
    for i, control in enumerate(controls):
        where = f"controls[{i}]"
        if not isinstance(control, dict):
            errs.append(f"{where}: must be an object")
            continue
        name = control.get("name")
        if not (isinstance(name, str) and name.strip()):
            errs.append(f"{where}: name must be a non-empty string")
        elif name in names:
            errs.append(f"{where}: name {name!r} repeats")
        else:
            names.add(name)
        extra = set(control) - {"name", "expect", "fails", "output", "reply", "files"}
        if extra:
            errs.append(f"{where}: unknown fields {sorted(extra)}")
        expect = control.get("expect")
        if expect not in ("pass", "fail"):
            errs.append(f"{where}: expect must be 'pass' or 'fail'")
        fails = control.get("fails")
        if expect == "fail":
            if not (isinstance(fails, list) and fails and all(isinstance(t, str) for t in fails)):
                errs.append(f"{where}: a fail control needs `fails`, a non-empty list of check types")
            else:
                unknown = [t for t in fails if t not in known]
                if unknown:
                    errs.append(f"{where}: fails names check types the case does not have: {unknown}")
        elif expect == "pass" and "fails" in control:
            errs.append(f"{where}: a pass control must not set `fails`")
        if "output" not in control or not (control["output"] is None or isinstance(control["output"], str)):
            errs.append(f"{where}: output must be a string (the deliverable text) or null (file not written)")
        if not isinstance(control.get("reply"), str):
            errs.append(f"{where}: reply must be a string")
        files = control.get("files", {})
        if not isinstance(files, dict) or not all(_rel_path_ok(k) and isinstance(v, str) for k, v in files.items()):
            errs.append(f"{where}: files must map relative paths (no '..', not absolute) to text")
        elif case.get("output") in files:
            errs.append(f"{where}: files must not write the case output {case['output']!r}; use `output`")
    return errs


def _control_rule_errors(case: dict) -> list[str]:
    """The shipped-case rule: controls exist and include at least one pass and one fail control."""
    controls = case.get("controls")
    if not isinstance(controls, list) or not controls:
        return ["controls are required: at least one pass and one fail control"]
    expects = {c.get("expect") for c in controls if isinstance(c, dict)}
    return [f"controls need at least one {want!r} control" for want in ("pass", "fail") if want not in expects]


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
        return errs
    errs += _validate_extras(case)
    if not case["checks"]:
        errs.append("at least one check is required")
    names = source_names(case)
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
            if key in check and check[key] not in names:
                errs.append(f"{where}: source {check[key]!r} is not an input file")
        for src in check.get("sources", []):
            if src not in names:
                errs.append(f"{where}: source {src!r} is not an input file")
        if not missing and kind in {"facts_recalled", "diagrams", "html_deliverable", "slop_density", "rhythm"}:
            errs += _validate_new_check(kind, check, where)
    if "controls" in case:
        errs += _validate_controls(case, {c.get("type") for c in case["checks"] if isinstance(c, dict)})
    return errs


def validate_real_case(case: dict) -> list[str]:
    """validate_case plus the rule for the shipped cases: every case has at least one pass and one fail control."""
    return validate_case(case) + _control_rule_errors(case)


# ---------------------------------------------------------------- helper scripts

def _run_json(cmd: list[str], ok_codes=(0, 1)) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode not in ok_codes:
        raise RuntimeError(f"{Path(cmd[1]).name} failed ({proc.returncode}): {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    keep, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ inside the shipped skill
    sys.modules[name] = module  # dataclasses look the defining module up here
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = keep
    return module


FACT = _load_script("fact_diff", FACT_DIFF)


@functools.lru_cache(maxsize=1)
def _inventory():
    return _load_script("project_inventory", INVENTORY)


def fact_diff(before: str, after: str) -> dict:
    return FACT.build_report(before, after)


# ---------------------------------------------------------------- source text (input files and fixtures)

def fixture_root(case: dict) -> Path | None:
    fx = case.get("fixtures")
    return (REPO / fx) if fx else None  # an absolute path passes through unchanged


def fixture_files(root: Path) -> list[Path]:
    """Fixture files as the agent sees them, in a stable order (same filter as the extractor's own walk)."""
    skip = _inventory().SKIP_DIRS
    return sorted(p for p in root.rglob("*")
                  if (p.is_file() or p.is_symlink()) and p.name != ".DS_Store"
                  and not any(part in skip for part in p.relative_to(root).parts[:-1]))


@functools.lru_cache(maxsize=64)
def _extract_fixtures(root: str, signature: tuple) -> tuple:
    inv, base = _inventory(), Path(root)
    out = []
    for rel, size, _ in signature:
        _, text, _, _ = inv.extract(base / rel, size, 50 * 2**20)
        out.append((rel, text))
    return tuple(out)


def fixture_texts(case: dict) -> dict[str, str]:
    """Extracted text of every fixture file, keyed by path relative to the fixture root.
    Office files, PDF and e-mail go through the project-report extractor; unreadable files give empty text."""
    root = fixture_root(case)
    if root is None or not root.is_dir():
        return {}
    signature = tuple((p.relative_to(root).as_posix(), p.lstat().st_size, p.lstat().st_mtime_ns)
                      for p in fixture_files(root))
    return dict(_extract_fixtures(str(root), signature))


def source_names(case: dict) -> set[str]:
    names = set(case["files"])
    root = fixture_root(case)
    if root is not None and root.is_dir():
        names |= {p.relative_to(root).as_posix() for p in fixture_files(root)}
    return names


def source_texts(case: dict) -> dict[str, str]:
    """Every input the agent was given, as text: inline files plus extracted fixtures."""
    return {**case["files"], **fixture_texts(case)}


@functools.lru_cache(maxsize=1)
def _slop_scan():
    return _load_script("slop_scan", SLOP_SCAN)


def slop_scan_result(text: str, profile: str) -> dict:
    """slop_scan's own result for text (imported with bytecode off, no subprocess)."""
    return _slop_scan().scan(text, profile)


def slop_findings(text: str, profile: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "text.md"
        path.write_text(text, encoding="utf-8")
        return _run_json([sys.executable, str(SLOP_SCAN), "--json", "--profile", profile, str(path)],
                         ok_codes=(0,))["findings"]


# ---------------------------------------------------------------- gap markers

_MARKER_TOKEN = re.compile(r"(?:\*{1,2}|_{1,2})?\[(?:" + "|".join(map(re.escape, MARKER_KINDS)) + r")\b[^\]\n]*\](?:\*{1,2}|_{1,2})?")
_EMPTY_LINE = re.compile(r"^[\s>*+\-\u2022]*(?:\d+[.)])?[\s>*]*$")
_HEADING = re.compile(r"^\s*#{1,6}\s")


def strip_markers(text: str) -> str:
    """Remove gap markers ([ASK AUTHOR: ...], [VERIFY: ...], [UNTESTED ...]) so a judge sees prose only.
    A marker inside a sentence is cut out with its surrounding space; a line left empty by the removal (a marker
    line, a bullet holding only a marker) is dropped, and so is a heading whose whole section was markers."""
    lines = text.split("\n")
    out: list[str | None] = []
    for line in lines:
        if not _MARKER_TOKEN.search(line):
            out.append(line)
            continue
        indent = line[:len(line) - len(line.lstrip(" \t"))]
        cut = _MARKER_TOKEN.sub(" ", line)
        cut = re.sub(r"(?<=\S)[ \t]{2,}", " ", cut)
        cut = re.sub(r" +([.,;:!?)])", r"\1", cut).rstrip()
        out.append(None if _EMPTY_LINE.match(cut) else indent + cut.lstrip(" \t"))
    for i, line in enumerate(lines):
        if out[i] is not None and _HEADING.match(line):
            j, saw_removed = i + 1, False
            while j < len(lines) and not _HEADING.match(lines[j]) and (out[j] is None or not out[j].strip()):
                saw_removed |= out[j] is None
                j += 1
            if saw_removed:
                out[i] = None
    joined = re.sub(r"\n{3,}", "\n\n", "\n".join(l for l in out if l is not None)).strip("\n")
    return joined + "\n" if joined and text.endswith("\n") else joined


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


def _fact_text(name: str, text: str) -> str:
    """Text as compared by fact_diff. CSV/TSV cells are separated so that '2026-06-29,14,171,6.8' is not read as
    one fused number; quoted cells such as "1,240" stay intact."""
    if not name.lower().endswith((".csv", ".tsv")):
        return text
    try:
        rows = csv.reader(io.StringIO(text), delimiter="\t" if name.lower().endswith(".tsv") else ",")
        return "\n".join(" ; ".join(row) for row in rows)
    except csv.Error:
        return text


RUN_DATES: list[str] = []  # ISO dates the run being graded took place on; set per run by use_run_dates()


def use_run_dates(run_dir: Path, meta: dict) -> None:
    """The date a run happened is a fact the agent has from its environment (a report dated today invents
    nothing). meta.json records it; older runs fall back to the run's start day and the next day."""
    global RUN_DATES
    if meta.get("date"):
        RUN_DATES = [meta["date"]]
        return
    try:
        info = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        start = dt.date.fromisoformat(info["started"][:10])
        RUN_DATES = [start.isoformat(), (start + dt.timedelta(days=1)).isoformat()]
    except (OSError, KeyError, ValueError):
        RUN_DATES = []


def _run_date_text() -> str:
    lines = []
    for iso in RUN_DATES:
        d = dt.date.fromisoformat(iso)
        lines.append(f"Today: {iso}, {d.day} {d:%B %Y}, {d:%B} {d.day}, {d:%Y}, {d.day} {d:%b %Y}")
    return "\n".join(lines)


def sources_blob(case: dict, names: list[str] | None = None) -> str:
    """Source text plus the input file names (reports cite file names, and 'v2' or '06' in one is not an
    invented number) plus the prompt, plus the date of the run (see use_run_dates)."""
    texts = source_texts(case)
    names = names or list(texts)
    return "\n\n".join([_fact_text(n, texts[n]) for n in names] + ["\n".join(names), case["prompt"],
                                                                  _run_date_text()])


TITLED_LINK = re.compile(r"""\]\(\s*([^)\s]+)\s+(?:"[^"]*"|'[^']*')\s*\)""")


def _is_input_file_link(item: str, case: dict) -> bool:
    """A relative link to one of the case's own input files (a memo citing its source) or into the agent's own
    output (a figure such as diagrams/schedule.svg) is not a new URL."""
    if "://" in item or item.startswith("www."):
        return False
    path = item.split("#")[0].replace("\\", "/")
    while path.startswith(("../", "./")):
        path = path.split("/", 1)[1]
    if path.rsplit("/", 1)[-1] in {n.rsplit("/", 1)[-1] for n in source_names(case)}:
        return True
    parts = Path(case["output"]).parts
    return (len(parts) > 1 and path.split("/", 1)[0] == parts[0]) or Path(path).suffix.lower() in {
        ".svg", ".html", ".htm", ".png", ".jpg", ".jpeg", ".webp"}


def check_no_added_facts(check, text, case):
    names = check.get("sources") or None
    sources = sources_blob(case, names)
    report = fact_diff(sources, TITLED_LINK.sub(r"](\1)", text))  # ](target "title") -> ](target)
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
    report = fact_diff(source_texts(case)[check["source"]], text)
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


def check_slop_density(check, text, case):
    result = slop_scan_result(text, check.get("profile", "professional"))
    words, n = result["words"], result["summary"]["total"]
    if not words:
        return False, "no prose words to scan"
    density = n * 1000 / words
    return density <= check["max"], f"{n} findings in {words} words = {density:.1f} per 1000 (max {check['max']})"


def sentence_lengths(text: str) -> list[int]:
    """Words per sentence in running prose (headings, list items, code, quotes and URLs are not counted)."""
    scan = _slop_scan()
    masked = scan.mask_protected(text)
    lengths = []
    for start, end in scan.prose_blocks(masked):
        for s, e in scan._sentences(masked[start:end], start):
            n = len(scan.WORD_RE.findall(masked[s:e]))
            if n:
                lengths.append(n)
    return lengths


def check_rhythm(check, text, case):
    """Sentence-length variation: coefficient of variation (std / mean) of words per sentence is at least min_cv.
    Uniform sentence lengths are a tell; the check is skipped (passes) when there are too few sentences to judge."""
    lengths = sentence_lengths(text)
    lo_n, lo = check.get("min_sentences", 5), check.get("min_cv", 0.4)
    if len(lengths) < lo_n:
        return True, f"{len(lengths)} sentences, fewer than {lo_n}: not judged"
    mean = sum(lengths) / len(lengths)
    cv = (sum((x - mean) ** 2 for x in lengths) / len(lengths)) ** 0.5 / mean
    return cv >= lo, f"sentence length cv {cv:.2f} over {len(lengths)} sentences, mean {mean:.1f} (min {lo})"


def check_markers(check, text, case):
    kinds = check.get("kinds", MARKER_KINDS)
    # the same question asked in the reply and again in open-questions.md is one question
    found = re.findall(r"\[(?:" + "|".join(map(re.escape, kinds)) + r")\b[^\]]*\]?", text)
    n = len({" ".join(m.casefold().split()) for m in found})
    lo, hi = check.get("min", 1), check.get("max")
    ok = n >= lo and (hi is None or n <= hi)
    return ok, f"{n} markers (min {lo}, max {hi})"


def check_similarity(check, text, case):
    a = _words(source_texts(case)[check["source"]])
    b = _words(text)
    ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    lo, hi = check.get("min", 0.0), check.get("max", 1.0)
    return lo <= ratio <= hi, f"similarity {ratio:.3f} (range {lo}-{hi})"


def check_word_count(check, text, case):
    n = len(_words(text))
    lo, hi = check.get("min", 0), check.get("max")
    return n >= lo and (hi is None or n <= hi), f"{n} words (min {lo}, max {hi})"


# ---------------------------------------------------------------- fact recall, diagrams, HTML deliverable

def check_facts_recalled(check, text, case):
    hay = _norm(text, True)
    facts = check["facts"]
    missed = [f["id"] for f in facts if not any(re.search(p, hay, re.I | re.M) for p in f["any"])]
    frac = (len(facts) - len(missed)) / len(facts)
    lo = check.get("min", 0.8)
    detail = f"recalled {len(facts) - len(missed)}/{len(facts)} ({frac:.2f}, min {lo})"
    return frac >= lo, detail + (f"; missed: {missed}" if missed else "")


def _squash(s: str) -> str:
    return " ".join(s.split())


class _SvgScan(HTMLParser):
    """Outermost <svg> elements of a document, with their visible <text> labels and an aria-hidden flag."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.svgs: list[dict] = []
        self._depth = 0
        self._cur: dict | None = None
        self._label: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "svg":
            if self._depth == 0:
                hidden = (dict(attrs).get("aria-hidden") or "").strip().lower() == "true"
                self._cur = {"hidden": hidden, "labels": [], "sig": []}
            self._depth += 1
        if not self._depth:
            return
        self._cur["sig"].append((tag, tuple(sorted((k, v or "") for k, v in attrs))))
        if tag == "text":
            self._label = []

    def handle_endtag(self, tag):
        if not self._depth:
            return
        if tag == "text" and self._label is not None:
            label = _squash(" ".join(self._label))
            if label:
                self._cur["labels"].append(label)
            self._label = None
        if tag == "svg":
            self._depth -= 1
            if self._depth == 0:
                cur, self._cur = self._cur, None
                cur["text"] = "\n".join(cur.pop("labels"))
                cur["sig"] = hashlib.sha1(repr(cur["sig"]).encode()).hexdigest()
                self.svgs.append(cur)

    def handle_data(self, data):
        if self._label is not None:
            self._label.append(data)


def visible_svgs(markup: str) -> list[dict]:
    scan = _SvgScan()
    scan.feed(markup)
    scan.close()
    return [s for s in scan.svgs if not s["hidden"]]


MERMAID_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*mermaid[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.M | re.S)
MERMAID_DATA_TYPES = {"gantt", "timeline", "journey", "pie", "quadrantchart", "xychart-beta", "xychart",
                      "sankey-beta", "gitgraph"}
MERMAID_ARROW = re.compile(r"-->|--[>x)]|->>|-->>|==>|-\.->|\.->|->")


def mermaid_text(block: str) -> str:
    """Visible labels of one mermaid block: node and edge labels, titles, messages; never node ids."""
    lines = [l.strip() for l in block.splitlines() if l.strip() and not l.strip().startswith("%%")]
    kind = lines[0].split()[0].lower() if lines else ""
    labels = []
    for line in lines[1:] if lines else []:
        if kind in MERMAID_DATA_TYPES:
            labels.append(line)
            continue
        if ":" in line and MERMAID_ARROW.search(line.split(":", 1)[0]):
            labels.append(line.split(":", 1)[1])
            line = line.split(":", 1)[0]
        elif re.match(r"(?i)note\b[^:]*:", line):
            labels.append(line.split(":", 1)[1])
            continue
        m = re.match(r"(?i)(?:title|section|participant|actor)\s+(.*)", line)
        if m:
            labels.append(m.group(1))
            continue
        labels += [q for q in re.findall(r'"([^"]*)"', line)]
        rest = re.sub(r'"[^"]*"', " ", line)
        for pattern in (r"\[([^\[\]]*)\]", r"\(([^()]*)\)", r"\{([^{}]*)\}", r"\|([^|]*)\|"):
            labels += re.findall(pattern, rest)
    return "\n".join(_squash(l) for l in labels if l.strip())


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def _html_candidates(case: dict) -> list[str]:
    """Paths of the report HTML (never counted as a standalone diagram file)."""
    paths = [d for d in case.get("deliverables", []) if d.lower().endswith((".html", ".htm"))]
    paths += [c["path"] for c in case["checks"] if c["type"] == "html_deliverable"]
    paths.append(str(Path(case["output"]).with_suffix(".html")))
    return list(dict.fromkeys(paths))


def collect_diagrams(case: dict, ws: Path | None, output_text: str | None) -> tuple[list[dict], list[Path]]:
    """Diagrams a run produced (see README): svg files and diagram .html files under the output folder,
    non-decorative inline svgs in the report HTML, mermaid blocks in the report text, raster images the report
    references. The same diagram reached twice is counted once (same visible text, or same markup when it has none).
    Returns (diagrams, diagram html files); each diagram has kind, origin, text and verifiable."""
    found: list[dict] = []
    seen: set = set()
    html_files: list[Path] = []

    def add(kind, origin, text, key, verifiable=True):
        if key in seen:
            return
        seen.add(key)
        found.append({"kind": kind, "origin": origin, "text": text, "verifiable": verifiable})

    def add_svgs(kind, origin, markup):
        for svg in visible_svgs(markup):
            add(kind, origin, svg["text"], ("t", _squash(svg["text"]).casefold()) if svg["text"] else ("m", svg["sig"]))

    if ws is not None:
        parts = Path(case["output"]).parts
        out_dir = ws / parts[0] if len(parts) > 1 else ws
        reports = {(ws / p).resolve() for p in _html_candidates(case)}
        read = lambda p: p.read_text(encoding="utf-8", errors="replace")
        if out_dir.is_dir():
            for p in sorted(out_dir.rglob("*.svg")):
                add_svgs("svg-file", p.relative_to(ws).as_posix(), read(p))
            for p in sorted([*out_dir.rglob("*.html"), *out_dir.rglob("*.htm")]):
                if p.resolve() in reports or not p.is_file():
                    continue
                markup = read(p)
                if visible_svgs(markup):
                    html_files.append(p)
                add_svgs("html-file", p.relative_to(ws).as_posix(), markup)
        report_markup = []
        for p in sorted(reports):
            if p.is_file() and _within(p, ws):
                markup = read(p)
                report_markup.append((p, markup))
                add_svgs("inline-svg", p.relative_to(ws.resolve()).as_posix(), markup)
    for i, m in enumerate(MERMAID_RE.finditer(output_text or ""), 1):
        text = mermaid_text(m.group(2))
        add("mermaid", f"mermaid block {i}", text, ("t", _squash(text).casefold()) if text else ("m", m.group(2)))
    if ws is not None:
        md_dir = (ws / case["output"]).parent
        refs = [(md_dir, r) for r in re.findall(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)", output_text or "")]
        for p, markup in report_markup:
            scan = _HtmlScan()
            scan.feed(markup)
            refs += [(p.parent, r) for r in scan.imgs]
        for base, ref in refs:
            target = base / urllib.parse.unquote(urllib.parse.urlsplit(ref).path)
            if target.suffix.lower() in RASTER_EXT and target.is_file() and _within(target, ws):
                add("raster", target.resolve().relative_to(ws.resolve()).as_posix(), "", ("r", str(target.resolve())),
                    verifiable=False)
    return found, html_files


_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"


def _norm_number(raw: str) -> str:
    """'48,500' -> '48500', '06' -> '6', '6.80' -> '6.8'."""
    raw = raw.replace(",", "")
    whole, dot, frac = raw.partition(".")
    whole = whole.lstrip("0") or "0"
    frac = frac.rstrip("0")
    return whole + ("." + frac if frac else "")


def _source_numbers(sources: str, allow: set[str]) -> set[str]:
    """Every number in the sources, leniently: thousands-grouped and split forms, identifier digits (v2) too."""
    found = set()
    for text in [sources, *allow]:
        for m in re.finditer(_NUM, text):
            found.add(_norm_number(m.group(0)))
            found.update(_norm_number(p) for p in m.group(0).split(",") if p)
    return found


def _added_numbers(text: str, sources: str, allow: set[str]) -> list[str]:
    """Numbers visible in a diagram that appear nowhere in the sources. Units and currency are ignored ('48500' in
    a label matches '48500 USD'); digits glued to letters ('Q3', 'A1') are identifiers, not figures."""
    known = _source_numbers(sources, allow)
    return [m.group(0) for m in re.finditer(r"(?<![A-Za-z0-9_.])(?:" + _NUM + r")", text)
            if _norm_number(m.group(0)) not in known]


def _run_self_check(files: list[Path], ws: Path) -> tuple[bool | None, str]:
    if not DIAGRAM_SELF_CHECK.is_file():
        return None, "self_check skipped (diagram-design not installed)"
    if not files:
        return True, "self_check: no diagram .html files"
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run([sys.executable, str(DIAGRAM_SELF_CHECK), *map(str, files)], capture_output=True,
                          text=True, timeout=120, env=env)
    if proc.returncode == 0:
        return True, f"self_check ok on {len(files)} file(s)"
    bad = [l.strip().replace(str(ws) + "/", "") for l in proc.stdout.splitlines()
           if l.startswith("FAIL") or l.startswith("  - ")]
    return False, "self_check failed: " + "; ".join(bad)[:400]


def check_diagrams(check, text, case, ws):
    diagrams, html_files = collect_diagrams(case, ws, text)
    n = len(diagrams)
    lo, hi = check.get("min", 0), check.get("max")
    kinds: dict[str, int] = {}
    for d in diagrams:
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    problems, notes = [], []
    if n < lo:
        problems.append(f"only {n} diagrams (min {lo})")
    if hi is not None and n > hi:
        problems.append(f"{n} diagrams (max {hi})")
    raster = [d for d in diagrams if not d["verifiable"]]
    if raster:
        notes.append(f"{len(raster)} raster diagram(s) unverifiable: numbers not checked")
    if check.get("numbers_from_sources"):
        sources = sources_blob(case)
        allow = {a.casefold() for a in check.get("allow", [])}
        for d in diagrams:
            invented = _added_numbers(d["text"], sources, allow) if d["verifiable"] and d["text"] else []
            if invented:
                problems.append(f"numbers not in the sources in {d['origin']}: {invented}")
        if raster and len(raster) > n / 2:
            problems.append("more than half of the diagrams are unverifiable raster images")
    for label in check.get("labels_any", []):
        if not any(re.search(p, d["text"], re.I | re.M) for d in diagrams for p in label["any"]):
            problems.append(f"label {label['id']!r} appears in no diagram")
    if check.get("labels_none"):
        for d in diagrams:
            for p in check["labels_none"]:
                m = re.search(p, d["text"], re.I | re.M)
                if m:
                    problems.append(f"forbidden label {m.group(0)[:40]!r} in {d['origin']}")
    if check.get("self_check"):
        ok, detail = _run_self_check(html_files, ws) if ws is not None else (None, "self_check skipped (no workspace)")
        notes.append(detail)
        if ok is False:
            problems.append(detail)
    summary = f"{n} diagram(s) " + (str(kinds) if kinds else "")
    return not problems, "; ".join([summary.strip()] + problems + [x for x in notes if x not in problems])


class _HtmlScan(HTMLParser):
    """What a report page loads or runs: scripts, handlers, resource references, figures."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = 0
        self.handlers: list[str] = []
        self.refs: list[tuple[str, str, str, str]] = []  # tag, attribute, value, rel
        self.imgs: list[str] = []
        self.objects = 0
        self.svg_figures = 0
        self.css: list[str] = []
        self._svg_depth = 0
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "script":
            self.scripts += 1
        self.handlers += [f"<{tag} {k}>" for k in a if k.startswith("on")]
        for attr in ("src", "href", "poster", "data", "xlink:href", "action", "formaction"):
            if attr in a:
                self.refs.append((tag, attr, a[attr], a.get("rel", "").lower()))
        for part in a.get("srcset", "").split(","):
            if part.strip():
                self.refs.append((tag, "srcset", part.split()[0], ""))
        if "style" in a:
            self.css.append(a["style"])
        if tag == "style":
            self._in_style = True
        if tag == "img":
            self.imgs.append(a.get("src", ""))
        if tag == "object":
            self.objects += 1
        if tag == "svg":
            if self._svg_depth == 0 and a.get("aria-hidden", "").strip().lower() != "true":
                self.svg_figures += 1
            self._svg_depth += 1

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        if tag == "svg" and self._svg_depth:
            self._svg_depth -= 1

    def handle_data(self, data):
        if self._in_style:
            self.css.append(data)


def _ref_problem(tag: str, attr: str, value: str, rel: str, base: Path, root: Path) -> str | None:
    v = value.strip()
    if not v or v.startswith("#"):
        return None
    parsed = urllib.parse.urlsplit(v)
    scheme = parsed.scheme.lower()
    if scheme in {"data", "mailto", "tel"}:
        return None
    if scheme == "javascript":
        return None  # reported by the no_script check
    if scheme in {"http", "https"} or v.startswith("//"):
        host = (parsed.hostname if scheme else urllib.parse.urlsplit("http:" + v).hostname) or ""
        if tag in {"a", "area"} or host in FONT_HOSTS:  # a hyperlink is not a loaded resource
            return None
        return f"remote resource {v[:70]}"
    if scheme:
        return f"unsupported scheme in {v[:70]}"
    path = urllib.parse.unquote(parsed.path)
    if not path:
        return None
    if path.startswith("/"):
        return f"absolute path {v[:70]}"
    target = (base / path).resolve()
    if not _within(target, root):
        return f"points outside the workspace: {v[:70]}"
    if not target.exists():
        return f"missing local file {v[:70]}"
    return None


def check_html_deliverable(check, text, case, ws):
    if ws is None:
        return False, "no workspace to inspect"
    path = ws / check["path"]
    if not path.is_file():
        return False, f"{check['path']} was not written"
    scan = _HtmlScan()
    scan.feed(path.read_text(encoding="utf-8", errors="replace"))
    scan.close()
    problems = []
    if check.get("no_script"):
        js = [v for t, a, v, _ in scan.refs if v.strip().lower().startswith("javascript:")]
        if scan.scripts:
            problems.append(f"{scan.scripts} <script> element(s)")
        if scan.handlers:
            problems.append(f"event handler attribute(s): {sorted(set(scan.handlers))[:5]}")
        if js:
            problems.append("javascript: URL")
    if check.get("self_contained"):
        bad = [p for p in (_ref_problem(t, a, v, r, path.parent, ws) for t, a, v, r in scan.refs) if p]
        for css in scan.css:
            for ref in re.findall(r"url\(\s*['\"]?([^)'\"]+)|@import\s+['\"]([^'\"]+)", css):
                bad += [p for p in (_ref_problem("css", "url", ref[0] or ref[1], "", path.parent, ws),) if p]
        if bad:
            problems.append(f"not self-contained: {sorted(set(bad))[:5]}")
    figures = scan.svg_figures + len(scan.imgs) + scan.objects
    need = check.get("min_figures", 0)
    if figures < need:
        problems.append(f"{figures} figure(s) (min {need})")
    return not problems, "; ".join(problems) or f"ok ({figures} figure(s))"


CHECKS = {name: globals()[f"check_{name}"] for name in CHECK_FIELDS}


def grade_case(case: dict, output: str | None, reply: str, workspace: Path | None = None) -> dict:
    """Grade one run. output is the deliverable file text (None when the agent wrote no file); workspace is the
    run's workspace directory, needed by the checks that inspect other files (diagrams, html_deliverable)."""
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
        needs_ws = check["type"] in WORKSPACE_CHECKS
        if text is None and not needs_ws:
            results.append({"type": check["type"], "passed": False, "detail": "no output to check"})
            continue
        try:
            if needs_ws:
                passed, detail = CHECKS[check["type"]](check, text, case, workspace)
            else:
                passed, detail = CHECKS[check["type"]](check, text, case)
        except Exception as exc:  # a broken helper must fail the check, not the whole run
            passed, detail = False, f"error: {exc}"
        results.append({"type": check["type"], "passed": passed, "detail": detail, "note": check.get("note")})
    return {"passed": all(r["passed"] for r in results), "score": sum(r["passed"] for r in results) / len(results),
            "checks": results}


# ---------------------------------------------------------------- run directories

STYLE_AXES = {"human": "reads as a skilled human professional (fewer AI tells)",
              "faithful": "more faithful to the inputs"}
READER_AXES = {"fit": "reads like the required document (style reference or genre)",
               "flow": "coherent, concise, one clear story in plain sentences",
               "faithful": "more faithful to the inputs"}
AXES_BY_MODE = {"style": STYLE_AXES, "reader": READER_AXES}
JUDGE_CRITERIA = {"accuracy": "factual accuracy vs sources", "needs": "covers what the reader needs",
                  "tone": "professional tone", "diagrams": "diagram usefulness and design",
                  "layout": "layout and readability"}


def with_open_questions(reply: str, workspace: Path) -> str:
    """Questions left for the author in an open-questions file are addressed to the author, like the reply."""
    for notes in sorted(workspace.glob("**/open-questions.md")) if workspace.is_dir() else []:
        reply += "\n\n" + notes.read_text(encoding="utf-8", errors="replace")
    return reply


def grade_run(run_dir: Path) -> dict:
    cases = {c["id"]: c for c in load_cases()}
    runs = []
    for meta_path in sorted((run_dir / "runs").glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        case = cases.get(meta["case"])
        if case is None:
            continue
        workspace = meta_path.parent / "workspace"
        out_path = workspace / case["output"]
        output = out_path.read_text(encoding="utf-8", errors="replace") if out_path.is_file() else None
        reply_path = meta_path.parent / "reply.md"
        reply = reply_path.read_text(encoding="utf-8", errors="replace") if reply_path.is_file() else ""
        reply = with_open_questions(reply, workspace)
        use_run_dates(run_dir, meta)
        grade = grade_case(case, output, reply, workspace)
        deliverables = {d: (workspace / d).is_file() for d in case.get("deliverables", [])}
        runs.append({**{k: meta.get(k) for k in ("case", "skill", "host", "condition", "skill_loaded",
                                                  "exit_code", "duration_s", "error")},
                     "rep": meta.get("rep") or 1, "deliverables": deliverables, **grade})
    judge_path = run_dir / "judge.json"
    judge = json.loads(judge_path.read_text(encoding="utf-8")) if judge_path.is_file() else []
    info_path = run_dir / "run.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.is_file() else {}
    results = {"run": info, "runs": runs, "judge": judge, "summary": summarize(runs, judge)}
    (run_dir / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "report.md").write_text(prereg_header(run_dir) + render_report(results), encoding="utf-8")
    return results


PREREG_FILE = "prereg.md"
PREREG_MARK = "<!-- pre-registered text"


def prereg_header(run_dir: Path) -> str:
    """The pre-registered text (run.py --prereg copied it to prereg.md before any run) for the top of report.md,
    behind a marker comment with its hash and registration time; empty when the run was not pre-registered. Built on
    every grading, so re-running grade.py keeps it."""
    kept = run_dir / PREREG_FILE
    if not kept.is_file():
        return ""
    info_path = run_dir / "run.json"
    info = (json.loads(info_path.read_text(encoding="utf-8")).get("prereg") or {}) if info_path.is_file() else {}
    digest = hashlib.sha256(kept.read_bytes()).hexdigest()
    mark = f"{PREREG_MARK}: prereg.md, sha256 {digest}, registered {info.get('registered', 'unknown')} -->"
    return f"{mark}\n{kept.read_text(encoding='utf-8').rstrip()}\n\n---\n\n"



def _rate(rows: list[dict]) -> float | None:
    return sum(r["passed"] for r in rows) / len(rows) if rows else None


def _scores(rows: list[dict]) -> dict:
    """Mean, lowest and highest per-run score (fraction of checks passed)."""
    values = [r["score"] for r in rows]
    if not values:
        return {"mean": None, "min": None, "max": None}
    return {"mean": sum(values) / len(values), "min": min(values), "max": max(values)}


def host_failed(r: dict) -> bool:
    """The host crashed or timed out before writing the output: an infrastructure error, not a skill failure."""
    return bool(r.get("error")) and not r["checks"][0]["passed"]


DEFAULT_JUDGE_PAIR = "skill:baseline"


def _pair_of(entry: dict) -> str:
    return entry.get("pair") or DEFAULT_JUDGE_PAIR


def _judge_scores(judge: list[dict], conds: tuple[str, str] = ("skill", "baseline")) -> dict:
    """Mean visual-judge score per condition and criterion, over pairs the judge scored."""
    out = {}
    for cond in conds:
        rows = [j["scores"][cond] for j in judge if (j.get("scores") or {}).get(cond)]
        if rows:
            out[cond] = {"n": len(rows), **{
                c: (sum(r[c] for r in rows if c in r) / n) if (n := sum(1 for r in rows if c in r)) else None
                for c in JUDGE_CRITERIA}}
    return out


def _axis_counts(judge: list[dict], a: str, b: str, mode: str) -> dict:
    """Verdict tally per question over the entries of one multi-question judge mode ('style' or 'reader'); empty
    when no entry has that mode. An errored entry counts as an error on every question."""
    axes = AXES_BY_MODE[mode]
    entries = [j for j in judge if j.get("mode") == mode]
    counts = {axis: {a: 0, b: 0, "tie": 0, "inconsistent": 0, "error": 0} for axis in axes}
    for j in entries:
        for axis in axes:
            verdict = "error" if j["winner"] == "error" else j[axis]
            counts[axis][verdict] = counts[axis].get(verdict, 0) + 1
    return counts if entries else {}


def _judge_counts(judge: list[dict], a: str, b: str) -> tuple[dict, dict]:
    """Verdict tally over a pairwise judge's entries for the pair (a, b), and the same per style question (empty
    unless some entry is a style verdict). Style and reader entries are never added to the overall tally."""
    verdicts = {a: 0, b: 0, "tie": 0, "inconsistent": 0, "error": 0}
    for j in judge:
        if j.get("mode") not in AXES_BY_MODE:
            verdicts[j["winner"]] = verdicts.get(j["winner"], 0) + 1
    return verdicts, _axis_counts(judge, a, b, "style")


def _triple(r: dict) -> tuple:
    return (r["case"], r["host"], r.get("rep", 1))


def _paired_rows(rows: list[dict], conds: list[str]) -> tuple[dict[str, list[dict]], set]:
    """Rows per condition, kept only on the (case, host, rep) triples where every condition in `conds` has a run and
    none of those runs failed on the host. Also returns those triples."""
    by: dict[tuple, dict[str, dict]] = {}
    for r in rows:
        by.setdefault(_triple(r), {})[r["condition"]] = r
    ok = {k for k, c in by.items() if all(n in c and not host_failed(c[n]) for n in conds)}
    return {n: [c[n] for k, c in by.items() if k in ok] for n in conds}, ok


def _delta(a, b):
    return None if a is None or b is None else a - b


def _competitor_stats(rows: list[dict], name: str, has_skill: bool, has_baseline: bool) -> dict | None:
    """A competitor against the baseline and against our skills, each on the triples where both have a gradable
    run (a competitor that did not run a case, or that crashed on it, drops only its own comparisons)."""
    if not any(r["condition"] == name for r in rows):
        return None
    out = {}
    for label, other, present in (("vs_baseline", "baseline", has_baseline), ("vs_skill", "skill", has_skill)):
        paired, _ = _paired_rows(rows, [other, name] if present else [name])
        c, o = paired[name], paired.get(other, [])
        sc, so = _scores(c), _scores(o)
        out[label] = {"n": len(c), "competitor_pass": _rate(c), f"{other}_pass": _rate(o),
                      "delta": _delta(_rate(o), _rate(c)) if label == "vs_skill" else _delta(_rate(c), _rate(o)),
                      "competitor_score": sc["mean"], f"{other}_score": so["mean"],
                      "score_delta": (_delta(so["mean"], sc["mean"]) if label == "vs_skill"
                                      else _delta(sc["mean"], so["mean"]))}
    loaded_rows = _paired_rows(rows, [name])[0][name]
    out["loaded"] = _rate([{"passed": bool(r["skill_loaded"])} for r in loaded_rows])
    return out


VARIANT_PREFIX = "variant-"


def _variant_stats(rows: list[dict], name: str, has_skill: bool) -> dict | None:
    """Our skills at the run's commit against our skills at another ref (condition variant-NAME), on the (case, host,
    rep) triples where both have a gradable run: the same pairing as a competitor against our skills."""
    if not has_skill or not any(r["condition"] == name for r in rows):
        return None
    paired, _ = _paired_rows(rows, ["skill", name])
    s, v = paired["skill"], paired[name]
    ss, sv = _scores(s), _scores(v)
    loaded = lambda rs: _rate([{"passed": bool(r["skill_loaded"])} for r in rs])
    return {"n": len(s), "skill_pass": _rate(s), "variant_pass": _rate(v), "delta": _delta(_rate(s), _rate(v)),
            "skill_score": ss["mean"], "variant_score": sv["mean"], "score_delta": _delta(ss["mean"], sv["mean"]),
            "skill_loaded": loaded(s), "variant_loaded": loaded(v)}


def summarize(runs: list[dict], judge: list[dict]) -> dict:
    """Pass rates and scores per host and skill. Skill against baseline is paired exactly as before (a triple counts
    only when both gradable runs exist); every competitor condition is paired with the baseline and with our skills
    separately, so a competitor that ran only some cases never removes pairs from the main comparison. `delta` is
    skill minus baseline, competitor minus baseline in `competitors[name].vs_baseline`, and skill minus competitor
    in `competitors[name].vs_skill`. Every `variant-NAME` condition (our skills at another git ref) is paired with
    `skill` alone in `variants[name]`, delta = skill minus variant."""
    hosts = sorted({r["host"] for r in runs})
    skills = sorted({r["skill"] for r in runs})
    conditions = {r["condition"] for r in runs}
    competitors = sorted(c for c in conditions if c.startswith("competitor-"))
    variants = sorted(c for c in conditions if c.startswith(VARIANT_PREFIX))
    needed = [c for c in ("skill", "baseline") if c in conditions]  # a one-sided run is not "unpaired"
    by = {}
    for host in hosts:
        for skill in skills + ["ALL"]:
            rows = [r for r in runs if r["host"] == host and (skill == "ALL" or r["skill"] == skill)]
            paired, ok = _paired_rows([r for r in rows if r["condition"] in needed], needed)
            s, b = paired.get("skill", []), paired.get("baseline", [])
            ps, pb = _rate(s), _rate(b)
            ss, sb = _scores(s), _scores(b)
            by[f"{host}/{skill}"] = {
                "skill_pass": ps, "baseline_pass": pb,
                "delta": None if ps is None or pb is None else ps - pb,
                "skill_score": ss["mean"], "skill_score_min": ss["min"], "skill_score_max": ss["max"],
                "baseline_score": sb["mean"], "baseline_score_min": sb["min"], "baseline_score_max": sb["max"],
                "score_delta": None if ss["mean"] is None or sb["mean"] is None else ss["mean"] - sb["mean"],
                "skill_n": len(s), "baseline_n": len(b),
                "skill_loaded": _rate([{"passed": bool(r["skill_loaded"])} for r in s]),
                "excluded": len({(r["case"], r.get("rep", 1)) for r in rows
                                 if r["condition"] in needed and _triple(r) not in ok}),
            }
            stats = {c[len("competitor-"):]: _competitor_stats(rows, c, "skill" in conditions, "baseline" in conditions)
                     for c in competitors}
            stats = {name: st for name, st in stats.items() if st}
            if stats:
                by[f"{host}/{skill}"]["competitors"] = stats
            ab = {c[len(VARIANT_PREFIX):]: _variant_stats(rows, c, "skill" in conditions) for c in variants}
            ab = {name: st for name, st in ab.items() if st}
            if ab:
                by[f"{host}/{skill}"]["variants"] = ab
    failing = {}
    for r in runs:
        if host_failed(r):
            continue
        for c in r["checks"]:
            if not c["passed"]:
                key = f"{r['condition']}:{c['type']}"
                failing[key] = failing.get(key, 0) + 1
    default = [j for j in judge if _pair_of(j) == DEFAULT_JUDGE_PAIR]
    verdicts, style = _judge_counts(default, "skill", "baseline")
    reader = _axis_counts(default, "skill", "baseline", "reader")
    judge_pairs = {}
    for pair in sorted({_pair_of(j) for j in judge} - {DEFAULT_JUDGE_PAIR}):
        a, b = pair.split(":", 1)  # condition names never contain ':'
        entries = [j for j in judge if _pair_of(j) == pair]
        pair_verdicts, pair_style = _judge_counts(entries, a, b)
        judge_pairs[pair] = {"a": a, "b": b, "verdicts": pair_verdicts, "style": pair_style,
                             "reader": _axis_counts(entries, a, b, "reader"), "scores": _judge_scores(entries, (a, b))}
    return {"by": by, "failing_checks": dict(sorted(failing.items())), "judge": verdicts,
            "judge_scores": _judge_scores(default), "judge_style": style, "judge_reader": reader,
            "judge_pairs": judge_pairs}


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


def _score_cell(v: dict, side: str) -> str:
    mean = v[f"{side}_score"]
    if mean is None:
        return "n/a"
    return f"{mean:.2f} ({v[f'{side}_score_min']:.2f}-{v[f'{side}_score_max']:.2f})"


def _pct_score(rate, score) -> str:
    return "n/a" if rate is None else f"{rate * 100:.0f}% ({score:.2f})"


def _pts(delta) -> str:
    return "n/a" if delta is None else f"{delta * 100:+.0f} pts"


def _competitor_lines(summary: dict) -> list[str]:
    rows = [(key, name, c) for key, v in summary["by"].items() for name, c in v.get("competitors", {}).items()]
    if not rows:
        return []
    lines = ["", "## Competitors", "",
             "Third-party skills installed instead of ours (evals/competitors.json), each run only on the cases it is "
             "mapped to. Cells give pass rate and, in brackets, mean score. Each comparison uses only the cases and "
             "repetitions where both sides produced a gradable run: competitor against baseline in the first group, "
             "our skills against the competitor in the second, so the baseline and our-skills columns differ between "
             "the groups when the sets of cases differ.", "",
             "| host / skill | competitor | competitor | baseline | competitor minus baseline | n | our skills | "
             "competitor | ours minus competitor | n | competitor loaded |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for key, name, c in rows:
        b, s = c["vs_baseline"], c["vs_skill"]
        label = f"**{key}**" if key.endswith("/ALL") else key
        lines.append(f"| {label} | {name} | {_pct_score(b['competitor_pass'], b['competitor_score'])} | "
                     f"{_pct_score(b['baseline_pass'], b['baseline_score'])} | {_pts(b['delta'])} | {b['n']} | "
                     f"{_pct_score(s['skill_pass'], s['skill_score'])} | "
                     f"{_pct_score(s['competitor_pass'], s['competitor_score'])} | {_pts(s['delta'])} | {s['n']} | "
                     f"{_pct(c['loaded'])} |")
    return lines


def _variant_lines(summary: dict) -> list[str]:
    names = sorted({name for v in summary["by"].values() for name in v.get("variants", {})})
    lines = []
    for name in names:
        lines += ["", f"## A/B: skill vs variant-{name}", "",
                  f"Our skills at this run's commit (`skill`) against our skills as of the ref given for variant {name} "
                  "(`variant-" + name + "`), both on every case. Cells give pass rate and, in brackets, mean score; "
                  "only the cases and repetitions where both sides produced a gradable run are counted.", "",
                  f"| host / skill | skill | variant-{name} | skill minus variant | n | skill loaded | variant loaded |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for key, v in summary["by"].items():
            a = v.get("variants", {}).get(name)
            if a is None:
                continue
            label = f"**{key}**" if key.endswith("/ALL") else key
            lines.append(f"| {label} | {_pct_score(a['skill_pass'], a['skill_score'])} | "
                         f"{_pct_score(a['variant_pass'], a['variant_score'])} | {_pts(a['delta'])} | {a['n']} | "
                         f"{_pct(a['skill_loaded'])} | {_pct(a['variant_loaded'])} |")
    return lines


def _judge_pair_lines(pair: str, info: dict, entries: list[dict]) -> list[str]:
    """Report section for a judged pair other than skill:baseline."""
    a, b = info["a"], info["b"]
    v = info["verdicts"]
    lines = ["", f"## Blind judge: {a} vs {b}", "",
             f"Preferred {a}: {v[a]}; {b}: {v[b]}; tie: {v['tie']}; inconsistent across swapped order: "
             f"{v['inconsistent']}; judge error (no verdict): {v.get('error', 0)}."]
    for axes, counts in ((STYLE_AXES, info["style"]), (READER_AXES, info["reader"])):
        if counts:
            lines += ["", f"| question | {a} | {b} | tie | inconsistent | error |", "|---|---:|---:|---:|---:|---:|"]
            for axis, label in axes.items():
                c = counts[axis]
                lines.append(f"| {label} | {c[a]} | {c[b]} | {c['tie']} | {c['inconsistent']} | {c.get('error', 0)} |")
    plain = [r for r in entries if r.get("mode") != "reader"]
    if plain:
        lines += ["", "| case | host | rep | judge | winner / reads human | faithful | reason |",
                  "|---|---|---:|---|---|---|---|"]
    for r in plain:
        reason = (r.get("reason") or "").replace("|", "/").replace("\n", " ")[:160]
        lines.append(f"| {r['case']} | {r['host']} | {r.get('rep', 1)} | {r['judge']} | "
                     f"{r.get('human', r['winner'])} | {r.get('faithful', '-')} | {reason} |")
    if len(plain) < len(entries):
        lines += ["", "| case | host | rep | judge | fit | flow | faithful | reason |", "|---|---|---:|---|---|---|---|---|"]
        for r in entries:
            if r.get("mode") == "reader":
                reason = (r.get("reason") or "").replace("|", "/").replace("\n", " ")[:160]
                lines.append(f"| {r['case']} | {r['host']} | {r.get('rep', 1)} | {r['judge']} | "
                             f"{r.get('fit', 'error')} | {r.get('flow', 'error')} | {r.get('faithful', 'error')} | "
                             f"{reason} |")
    return lines


def render_report(results: dict) -> str:
    info, runs, summary = results["run"], results["runs"], results["summary"]
    lines = ["# Oh My Writing benchmark report", ""]
    if info:
        extra = [f"{k.replace('_', ' ')} {v}" for k, v in info.items()
                 if k in ("repeat", "codex_version", "claude_version", "diagram_design_version") and v]
        lines += [f"Run `{info.get('id')}` at {info.get('started')}; hosts {', '.join(info.get('hosts', []))}; "
                  f"{info.get('cases')} cases; models {info.get('models') or 'host default'}"
                  + (f"; {', '.join(extra)}" if extra else "") + "."]
        if info.get("contaminated"):
            lines += ["", "**Warning:** user-level skills with the same names were installed; the baseline may have "
                          "seen them."]
        if info.get("competitors"):
            lines += ["", "Competitors (local cache, unmodified): " + "; ".join(
                f"{n} = {c['repo']} @ {(c.get('commit') or 'unpinned')[:10]}, {c['license']}"
                for n, c in info["competitors"].items()) + "."]
        if info.get("variants"):
            lines += ["", "Variants (our skills at another git ref): " + "; ".join(
                f"variant-{n} = {v['ref']} @ {v['sha'][:10]}" for n, v in info["variants"].items()) + "."]
        lines += [""]
    lines += ["## Pass rate and mean score by skill", "",
              "Pass rate: share of runs in which every check passed. Mean score: average over runs of the share of "
              "checks passed, with the lowest-highest run in brackets. A case (and repetition) counts only when both "
              "conditions produced a gradable run. Pairs with a host error (crash, quota or timeout with no output) "
              "or with one condition missing are left out of both sides and counted as excluded.", "",
              "| host / skill | with skills | baseline | difference | score with skills | score baseline | "
              "skill loaded | n | excluded pairs |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for key, v in summary["by"].items():
        diff = "n/a" if v["delta"] is None else f"{v['delta'] * 100:+.0f} pts"
        label = f"**{key}**" if key.endswith("/ALL") else key
        lines.append(f"| {label} | {_pct(v['skill_pass'])} | {_pct(v['baseline_pass'])} | {diff} | "
                     f"{_score_cell(v, 'skill')} | {_score_cell(v, 'baseline')} | "
                     f"{_pct(v['skill_loaded'])} | {v['skill_n']}+{v['baseline_n']} | {v['excluded']} |")
    lines += _competitor_lines(summary)
    lines += _variant_lines(summary)
    comps = sorted({r["condition"] for r in runs if r["condition"].startswith(("competitor-", VARIANT_PREFIX))})
    lines += ["", "## Cases", "",
              "| case | host | rep | baseline | with skills | score baseline / skills | "
              "failed checks (with skills / baseline) |" + "".join(f" {c} |" for c in comps),
              "|---|---|---:|:---:|:---:|---|---|" + "---|" * len(comps)]
    index = {(r["case"], r["host"], r.get("rep", 1), r["condition"]): r for r in runs}
    for case, host, rep in sorted({(r["case"], r["host"], r.get("rep", 1)) for r in runs}):
        s, b = index.get((case, host, rep, "skill")), index.get((case, host, rep, "baseline"))

        def mark(r):
            if r is None:
                return "-"
            return "ERROR" if host_failed(r) else ("PASS" if r["passed"] else "FAIL")

        def score(r):
            return "-" if r is None or host_failed(r) else f"{r['score']:.2f}"

        def fails(r):
            if r is None:
                return "-"
            if host_failed(r):
                return f"host error: {r['error']}"[:200]
            bad = [f"{c['type']} ({c['detail']})" for c in r["checks"] if not c["passed"]]
            return "; ".join(bad) or "none"

        cells = "".join(f" {'-' if (r := index.get((case, host, rep, c))) is None else mark(r) + ' ' + score(r)} |"
                        for c in comps)
        lines.append(f"| {case} | {host} | {rep} | {mark(b)} | {mark(s)} | {score(b)} / {score(s)} | "
                     f"{fails(s)} / {fails(b)} |".replace("\n", " ") + cells)
    if summary["failing_checks"]:
        lines += ["", "## Failed checks by type", "", "| condition:check | failures |", "|---|---:|"]
        lines += [f"| {k} | {v} |" for k, v in summary["failing_checks"].items()]
    default_judge = [r for r in results["judge"] if _pair_of(r) == DEFAULT_JUDGE_PAIR]
    pairwise = [r for r in default_judge if r.get("mode") not in AXES_BY_MODE]
    styled = [r for r in default_judge if r.get("mode") == "style"]
    readers = [r for r in default_judge if r.get("mode") == "reader"]
    if pairwise:
        j = summary["judge"]
        lines += ["", "## Blind pairwise judge", "",
                  f"Preferred with-skills output: {j['skill']}; baseline: {j['baseline']}; tie: {j['tie']}; "
                  f"inconsistent across swapped order: {j['inconsistent']}; judge error (no verdict): "
                  f"{j.get('error', 0)}."]
        js = summary.get("judge_scores") or {}
        if js:
            lines += ["", "Visual judge scores (1-5, mean over the pairs it scored and both presentation orders):", "",
                      "| criterion | with skills | baseline |", "|---|---:|---:|"]
            for key, label in JUDGE_CRITERIA.items():
                cell = lambda side: "n/a" if js.get(side, {}).get(key) is None else f"{js[side][key]:.2f}"
                lines.append(f"| {label} | {cell('skill')} | {cell('baseline')} |")
            lines.append(f"| pairs scored | {js.get('skill', {}).get('n', 0)} | {js.get('baseline', {}).get('n', 0)} |")
        lines += ["", "| case | host | rep | judge | winner | reason |", "|---|---|---:|---|---|---|"]
        for r in pairwise:
            reason = (r.get("reason") or "").replace("|", "/").replace("\n", " ")[:160]
            lines.append(f"| {r['case']} | {r['host']} | {r.get('rep', 1)} | {r['judge']} | {r['winner']} | "
                         f"{reason} |")
    if styled:
        lines += ["", "## Blind style judge", "",
                  "Two separate questions, each decided over both presentation orders, with gap markers removed from "
                  "both texts first. Human: which reads as written by a skilled human professional, with fewer AI "
                  "tells (stock phrases, hedging fog, symmetric lists, empty openers and closers). Faithful: which "
                  "is more faithful to the inputs. A response can win one and lose the other.", "",
                  "| question | with skills | baseline | tie | inconsistent | error |", "|---|---:|---:|---:|---:|---:|"]
        for axis, label in STYLE_AXES.items():
            c = summary["judge_style"][axis]
            lines.append(f"| {label} | {c['skill']} | {c['baseline']} | {c['tie']} | {c['inconsistent']} | "
                         f"{c.get('error', 0)} |")
        lines += ["", "| case | host | rep | judge | reads human | faithful | reason |", "|---|---|---:|---|---|---|---|"]
        for r in styled:
            reason = (r.get("reason") or "").replace("|", "/").replace("\n", " ")[:160]
            lines.append(f"| {r['case']} | {r['host']} | {r.get('rep', 1)} | {r['judge']} | "
                         f"{r.get('human', 'error')} | {r.get('faithful', 'error')} | {reason} |")
    if readers:
        lines += ["", "## Blind reader judge", "",
                  "Three separate questions, each decided over both presentation orders, with gap markers removed "
                  "from both texts first. Fit: which reads like the document that was asked for, in the style of the "
                  "case's style reference or the genre and reader it names. Flow: which is coherent, concise and "
                  "tells one clear story in plain sentences, without stacked caveats, untranslated shorthand or "
                  "formulaic sentences. Faithful: which invents nothing and drops nothing the reader needs. A "
                  "response can win one and lose the others.", "",
                  "| question | with skills | baseline | tie | inconsistent | error |", "|---|---:|---:|---:|---:|---:|"]
        for axis, label in READER_AXES.items():
            c = summary["judge_reader"][axis]
            lines.append(f"| {label} | {c['skill']} | {c['baseline']} | {c['tie']} | {c['inconsistent']} | "
                         f"{c.get('error', 0)} |")
        lines += ["", "| case | host | rep | judge | fit | flow | faithful | reason |", "|---|---|---:|---|---|---|---|---|"]
        for r in readers:
            reason = (r.get("reason") or "").replace("|", "/").replace("\n", " ")[:160]
            lines.append(f"| {r['case']} | {r['host']} | {r.get('rep', 1)} | {r['judge']} | {r.get('fit', 'error')} | "
                         f"{r.get('flow', 'error')} | {r.get('faithful', 'error')} | {reason} |")
    for pair, info in (summary.get("judge_pairs") or {}).items():
        lines += _judge_pair_lines(pair, info, [r for r in results["judge"] if _pair_of(r) == pair])
    lines += ["", "## Limits", "",
              "Checks are mechanical: they detect invented numbers, names and citations, lost negations and qualifiers, "
              "missing gap markers, leftover stock patterns and leaked context, and for report cases missed facts, "
              "diagram counts and labels, and HTML hygiene. They do not measure prose quality, argument strength or "
              "voice. The judge is a single model's preference. Case counts are small; a difference of one or two "
              "cases is noise, and repetitions of the same case are not independent cases. Hosts run with their "
              "default model unless the run lists one.", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- controls

def _control_workspace(case: dict, control: dict) -> Path:
    """A workspace built as the runner builds one (case files, fixtures verbatim, output folder), plus the control's
    own files and, when the control wrote one, its deliverable at the case's output path."""
    import run  # lazy: run.py imports this module
    ws = run.make_workspace(case, "claude", "baseline")
    for name, text in control.get("files", {}).items():
        path = ws / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if control["output"] is not None:
        out = ws / case["output"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(control["output"], encoding="utf-8")
    return ws


def grade_control(case: dict, control: dict) -> dict:
    """Grade one control as a real run is graded (grade_case with the workspace, open-questions files added to the
    reply, no run date). `ok` says whether the grade is what the control expects; `problem` says why not."""
    global RUN_DATES
    ws = _control_workspace(case, control)
    saved, RUN_DATES = RUN_DATES, []
    try:
        result = grade_case(case, control["output"], with_open_questions(control["reply"], ws), ws)
    finally:
        RUN_DATES = saved
        shutil.rmtree(ws, ignore_errors=True)
    failing = [r["type"] for r in result["checks"] if not r["passed"]]
    detail = "; ".join(f"{r['type']}: {r['detail']}" for r in result["checks"] if not r["passed"])
    problem = None
    if control["expect"] == "pass":
        if not result["passed"]:
            problem = f"expected pass, failed {detail}"
    elif result["passed"]:
        problem = "expected fail, every check passed"
    else:
        unmet = [t for t in control["fails"] if t not in failing]
        if unmet:
            problem = f"expected {unmet} to fail, failing: {sorted(set(failing))}"
    return {"passed": result["passed"], "failing": failing, "ok": problem is None, "problem": problem}


def run_controls(patterns: list[str] | None = None) -> int:
    """Grade the controls of the matching cases, print one line per control and a summary; 1 on any mismatch."""
    cases = load_cases(patterns)
    if not cases:
        print("[FAIL] no cases matched")
        return 1
    total = bad = 0
    for case in cases:
        errs = (_validate_controls(case) if "controls" in case else []) + _control_rule_errors(case)
        for err in errs:
            bad += 1
            print(f"[FAIL] {case['id']}: {err}")
        if errs:
            continue
        for control in case["controls"]:
            total += 1
            got = grade_control(case, control)
            bad += not got["ok"]
            types = ",".join(sorted(set(got["failing"]))) or "-"
            line = (f"{'[OK]  ' if got['ok'] else '[FAIL]'} {case['id']} {control['name']} "
                    f"expected={control['expect']} got={'pass' if got['passed'] else 'fail'} failing={types}")
            print(line if got["ok"] else f"{line}\n       {got['problem']}")
    print(f"[FAIL] {bad} control problem(s) in {len(cases)} cases, {total} controls graded" if bad
          else f"[OK] {total} controls behave as expected in {len(cases)} cases")
    return 1 if bad else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run_dir", nargs="?", help="results directory written by run.py")
    parser.add_argument("--validate", action="store_true", help="validate every case file and exit")
    parser.add_argument("--controls", nargs="?", const="*", metavar="GLOB",
                        help="grade the controls of the cases whose id matches GLOB (default all); exit 1 on a mismatch")
    args = parser.parse_args(argv)
    if args.controls is not None:
        return run_controls([args.controls])
    if args.validate or not args.run_dir:
        bad = 0
        cases = load_cases()
        for case in cases:
            for err in validate_real_case(case):
                bad += 1
                print(f"[FAIL] {case.get('_path')}: {err}")
        print(f"[OK] {len(cases)} cases valid" if not bad else f"[FAIL] {bad} problems in {len(cases)} cases")
        return 1 if bad else 0
    results = grade_run(Path(args.run_dir))
    print((Path(args.run_dir) / "report.md").read_text(encoding="utf-8"))
    return 0 if results["runs"] else 1


if __name__ == "__main__":
    sys.exit(main())
