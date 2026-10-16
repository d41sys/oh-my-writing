#!/usr/bin/env python3
"""Run Oh My Writing benchmark cases on agent hosts, with and without the skills, then grade.

Usage:
  python3 evals/run.py --host codex --host claude --jobs 4
  python3 evals/run.py --host codex --cases 'anti-slop-editing/*' --condition skill
  python3 evals/run.py --host codex --judge claude        # add blind pairwise preference

Each run gets a fresh git workspace outside this repository, so neither condition can read
skills/ or the library. In the `skill` condition every skill is linked into the host's
project skill folder; in `baseline` none is. The prompt never names a skill.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade  # noqa: E402

REPO = grade.REPO
SKILLS = sorted(p for p in grade.SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())
SKILL_FOLDER = {"codex": ".agents/skills", "claude": ".claude/skills"}
USER_SKILL_DIRS = [Path.home() / ".agents" / "skills", Path.home() / ".claude" / "skills"]
QUOTA_HIT: set[str] = set()  # hosts that refused a run for usage limits during this invocation
CLAUDE_TOOLS = ("Read,Write,Edit,Glob,Grep,Skill,Bash(python3:*),Bash(python:*),Bash(ls:*),"
                "Bash(cat:*),Bash(mkdir:*),Bash(wc:*)")


def contaminated() -> list[str]:
    return [str(d / s.name) for d in USER_SKILL_DIRS for s in SKILLS if (d / s.name).exists()]


def make_workspace(case: dict, host: str, condition: str) -> Path:
    ws = Path(tempfile.mkdtemp(prefix="omw-eval-"))
    for name, text in case["files"].items():
        path = ws / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (ws / Path(case["output"]).parent).mkdir(parents=True, exist_ok=True)
    if condition == "skill":
        folder = ws / SKILL_FOLDER[host]
        folder.mkdir(parents=True)
        for skill in SKILLS:
            (folder / skill.name).symlink_to(skill)
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    return ws


def host_command(host: str, prompt: str, ws: Path, reply_file: Path, args, read_only=False) -> list[str]:
    if host == "codex":
        cmd = ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "--json",
               "-s", "read-only" if read_only else "workspace-write", "-C", str(ws), "-o", str(reply_file)]
        if args.codex_model:
            cmd += ["-m", args.codex_model]
        if args.codex_effort:
            cmd += ["-c", f"model_reasoning_effort={args.codex_effort}"]
        return cmd + [prompt]
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--no-session-persistence",
           "--strict-mcp-config"]
    cmd += ["--allowedTools", "Read"] if read_only else ["--permission-mode", "acceptEdits", "--allowedTools", CLAUDE_TOOLS]
    if args.claude_model:
        cmd += ["--model", args.claude_model]
    return cmd


def parse_claude(log: str) -> str:
    reply = ""
    for line in log.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            reply = event.get("result") or reply
    return reply


def skill_was_loaded(host: str, skill: str, log: str) -> bool:
    if f"skills/{skill}/SKILL.md" in log:
        return True
    if host == "claude":
        return bool(re.search(r'"name":\s*"Skill".{0,200}?' + re.escape(skill), log))
    return False


def execute(host: str, prompt: str, ws: Path, out_dir: Path, args, read_only=False) -> dict:
    reply_file = (out_dir / "reply.md").resolve()  # hosts run with the workspace as cwd
    cmd = host_command(host, prompt, ws, reply_file, args, read_only)
    start = time.monotonic()
    error = None
    try:
        proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=args.timeout,
                              stdin=subprocess.DEVNULL)
        log, code = proc.stdout + "\n" + proc.stderr, proc.returncode
        if code != 0:
            reported = re.findall(r'"type":\s*"error",\s*"message":\s*"((?:[^"\\]|\\.)*)"', log)
            error = f"exit {code}: " + (reported[-1] if reported else proc.stderr.strip()[-300:])
            if re.search(r"usage limit|rate limit|quota", error, re.I):
                QUOTA_HIT.add(host)
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        log = partial.decode(errors="replace") if isinstance(partial, bytes) else partial
        code, error = None, f"timeout after {args.timeout}s"
    (out_dir / "log.txt").write_text(log, encoding="utf-8")
    if host == "claude":
        reply_file.write_text(parse_claude(log), encoding="utf-8")
    elif not reply_file.exists():
        reply_file.write_text("", encoding="utf-8")
    return {"log": log, "exit_code": code, "error": error, "duration_s": round(time.monotonic() - start, 1)}


def finished(out_dir: Path) -> bool:
    meta = out_dir / "meta.json"
    return meta.is_file() and not json.loads(meta.read_text(encoding="utf-8")).get("error")


def run_one(case: dict, host: str, condition: str, run_dir: Path, args) -> dict:
    slug = f"{case['id'].replace('/', '__')}__{host}__{condition}"
    out_dir = run_dir / "runs" / slug
    if args.resume and finished(out_dir):
        return json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    if host in QUOTA_HIT:  # do not burn timeouts once the host has refused for quota; --resume picks these up
        meta = {"case": case["id"], "skill": case["skill"], "host": host, "condition": condition,
                "skill_loaded": False, "exit_code": None, "error": "skipped: host usage limit reached",
                "duration_s": 0}
        (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return meta
    ws = make_workspace(case, host, condition)
    try:
        result = execute(host, case["prompt"], ws, out_dir, args)
        shutil.copytree(ws, out_dir / "workspace", symlinks=True,
                        ignore=shutil.ignore_patterns(".git", ".agents", ".claude"))
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    meta = {"case": case["id"], "skill": case["skill"], "host": host, "condition": condition,
            "skill_loaded": condition == "skill" and skill_was_loaded(host, case["skill"], result["log"]),
            "exit_code": result["exit_code"], "error": result["error"], "duration_s": result["duration_s"]}
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    status = "ERROR" if meta["error"] else "done"
    print(f"[{status}] {case['id']} {host} {condition} {meta['duration_s']}s"
          + (f" ({meta['error']})" if meta["error"] else ""), flush=True)
    return meta


JUDGE_PROMPT = """You are judging two responses to the same writing task. You do not know how either was produced.

Task given to the writer:
<task>
{prompt}
</task>

Input files the writer had:
{files}

Response A (contents of {output}):
<a>
{a}
</a>

Response B (contents of {output}):
<b>
{b}
</b>

Judge which response better serves the task's reader: it does what was asked, keeps every fact from the inputs accurate and invents none (numbers, names, quotes, sources, experiences), marks missing information instead of filling it, and reads as clear, specific, natural prose without stock phrasing. Length is not a virtue.
Give three to six short reasons, then end with exactly one line: VERDICT: A, VERDICT: B, or VERDICT: TIE"""


def judge_once(case, a_text, b_text, judge_host, run_dir, tag, args) -> str:
    if judge_host in QUOTA_HIT:
        return "ERROR", ""
    files = "\n".join(f"<file name=\"{n}\">\n{t}\n</file>" for n, t in case["files"].items())
    prompt = JUDGE_PROMPT.format(prompt=case["prompt"], files=files, output=case["output"], a=a_text, b=b_text)
    out_dir = run_dir / "judge" / f"{case['id'].replace('/', '__')}__{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ws = Path(tempfile.mkdtemp(prefix="omw-judge-"))
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    try:
        execute(judge_host, prompt, ws, out_dir, args, read_only=True)
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    reply = (out_dir / "reply.md").read_text(encoding="utf-8", errors="replace")
    m = re.findall(r"VERDICT:\s*(A|B|TIE)", reply)
    return (m[-1] if m else "ERROR"), reply


def judge_pair(case, host, run_dir, args) -> dict | None:
    texts = {}
    for cond in ("skill", "baseline"):
        path = run_dir / "runs" / f"{case['id'].replace('/', '__')}__{host}__{cond}" / "workspace" / case["output"]
        if not path.is_file():
            return None
        texts[cond] = path.read_text(encoding="utf-8", errors="replace")
    first = random.Random(f"{args.seed}:{case['id']}:{host}").choice(["skill", "baseline"])
    second = "baseline" if first == "skill" else "skill"
    picks = []
    for tag, (a, b) in {"order1": (first, second), "order2": (second, first)}.items():
        verdict, reply = judge_once(case, texts[a], texts[b], args.judge, run_dir, f"{host}__{tag}", args)
        picks.append({"A": a, "B": b, "TIE": "tie"}.get(verdict, "error"))
        last_reply = reply
    if "error" in picks:
        winner = "error"
    else:
        winner = picks[0] if picks[0] == picks[1] else ("tie" if "tie" in picks else "inconsistent")
    reason = " ".join(l.strip() for l in last_reply.splitlines() if l.strip() and not l.startswith("VERDICT"))
    print(f"[judge] {case['id']} {host}: {winner}", flush=True)
    return {"case": case["id"], "host": host, "judge": args.judge, "winner": winner, "picks": picks,
            "reason": reason[:400]}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--host", action="append", choices=["codex", "claude"], required=True)
    p.add_argument("--cases", action="append", help="glob on case id, e.g. 'post-writing/*' (repeatable)")
    p.add_argument("--condition", choices=["skill", "baseline", "both"], default="both")
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--timeout", type=int, default=600, help="seconds per agent run")
    p.add_argument("--out", help="results directory (default evals/results/<timestamp>)")
    p.add_argument("--judge", choices=["codex", "claude"], help="blind pairwise judge host")
    p.add_argument("--codex-model")
    p.add_argument("--codex-effort", help="Codex model_reasoning_effort, e.g. medium")
    p.add_argument("--claude-model")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--allow-contaminated", action="store_true")
    p.add_argument("--resume", action="store_true",
                   help="reuse an --out directory: keep finished runs and judge verdicts, redo errored or missing ones")
    args = p.parse_args(argv)

    cases = grade.load_cases(args.cases)
    problems = [f"{c['_path']}: {e}" for c in cases for e in grade.validate_case(c)]
    if problems or not cases:
        print("\n".join(problems) or "no cases matched", file=sys.stderr)
        return 2
    dirty = contaminated()
    if dirty and not args.allow_contaminated:
        print("user-level skills would leak into the baseline:\n  " + "\n  ".join(dirty)
              + "\nremove them or pass --allow-contaminated", file=sys.stderr)
        return 2
    for host in args.host:
        if not shutil.which(host):
            print(f"{host} CLI not found", file=sys.stderr)
            return 2

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = (Path(args.out) if args.out else REPO / "evals" / "results" / stamp).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    conditions = ["skill", "baseline"] if args.condition == "both" else [args.condition]
    info = {"id": run_dir.name, "started": dt.datetime.now().isoformat(timespec="seconds"), "hosts": args.host,
            "conditions": conditions, "cases": len(cases), "contaminated": bool(dirty),
            "models": {k: v for k, v in {"codex": args.codex_model, "codex_effort": args.codex_effort,
                                          "claude": args.claude_model}.items() if v}}
    (run_dir / "run.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    jobs = [(c, h, cond) for c in cases for h in args.host for cond in conditions]
    print(f"{len(jobs)} runs -> {run_dir}", flush=True)
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(lambda j: run_one(*j, run_dir, args), jobs))

    if args.judge and len(conditions) == 2:
        judge_file = run_dir / "judge.json"
        kept = []
        if args.resume and judge_file.is_file():
            kept = [v for v in json.loads(judge_file.read_text(encoding="utf-8")) if v["winner"] != "error"]
        done = {(v["case"], v["host"]) for v in kept}
        pairs = [(c, h) for c in cases for h in args.host if (c["id"], h) not in done]
        with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            verdicts = kept + [v for v in pool.map(lambda ch: judge_pair(*ch, run_dir, args), pairs) if v]
        judge_file.write_text(json.dumps(verdicts, indent=2), encoding="utf-8")

    results = grade.grade_run(run_dir)
    for key, v in results["summary"]["by"].items():
        if key.endswith("/ALL"):
            print(f"{key}: with skills {grade._pct(v['skill_pass'])}, baseline {grade._pct(v['baseline_pass'])}, "
                  f"skill loaded {grade._pct(v['skill_loaded'])}")
    print(f"report: {run_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
