#!/usr/bin/env python3
"""Second stage for reviewer-prompt cases: run each saved reviewer prompt in a fresh session, then grade the reviews.

run.py shows a judge the reviewer prompt a writer prepared, never the review that prompt produces. For every finished
run of a case with a `review_stage` block, this script:

1. starts a fresh session on the run's host, with no skills and read-only tools, in a workspace holding only the
   files `review_stage.files` names, and sends the saved prompt as its whole input. The reply is the review
   (runs/<run>/review/reply.md).
2. asks a grader which of the case's planted problems (`review_stage.defects`, written before any run) the review
   identifies, one yes or no per problem.
3. judges pairs of reviews blind, in both orders, the way run.py judges outputs.

Results go to review_stage.json and review-stage.md in the results directory.

  python3 evals/review_stage.py evals/results/RUN --judge omp --pairs skill:baseline --jobs 4
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade  # noqa: E402
import run  # noqa: E402

GRADER_PROMPT = """You are checking a review of a document against a list of problems the document is known to have.

Document:
<document>
{document}
</document>

Known problems:
{defects}

Review:
<review>
{review}
</review>

For each known problem, decide whether the review identifies it. It counts only if the review points to that problem itself (the place, the fact or the missing piece), not merely to a nearby topic, and does not call it fine.
Answer with exactly one line per problem, in the order given, and nothing after them:
{answer_lines}"""

REVIEW_JUDGE_PROMPT = """You are judging two reviews of the same document. Each was written in a fresh session from a prompt someone else prepared; you do not know how either prompt was made.

What the document's author wants to learn from a review:
<brief>
{brief}
</brief>

Document:
<document>
{document}
</document>

Review A:
<a>
{a}
</a>

Review B:
<b>
{b}
</b>

Judge which review would help the author more before sending the document: it finds the problems the document's readers would actually hit, points to the place accurately, suggests fixes that do not invent facts, does not report problems the document does not have, and answers what the author wants to learn. Length is not a virtue.
Give three to six short reasons, then end with exactly one line: VERDICT: A, VERDICT: B, or VERDICT: TIE"""


def stage_document(case: dict) -> str:
    """The files the reviewer gets, as one text (each file headed by its name when there is more than one)."""
    names = case["review_stage"]["files"]
    if len(names) == 1:
        return case["files"][names[0]]
    return "\n\n".join(f"=== {n} ===\n{case['files'][n]}" for n in names)


def parse_found(reply: str, ids: list[str]) -> dict[str, bool] | None:
    """{id: found} from the grader's 'FOUND <id>: yes|no' lines (the last line per id wins); None unless every id
    has an answer."""
    found = {}
    for m in re.finditer(r"(?im)^\s*FOUND\s+([A-Za-z0-9_-]+)\s*:\s*(yes|no)\b", reply):
        if m.group(1) in ids:
            found[m.group(1)] = m.group(2).lower() == "yes"
    return found if set(found) == set(ids) else None


def summarise(reviews: list[dict], verdicts: list[dict], defect_ids: dict[str, list[str]]) -> dict:
    """Per case and condition: reviews, errors, mean words, planted problems found (mean and per problem); per case
    and pair: judge tallies. Errored or ungraded reviews count as errors, not as zero found."""
    out: dict = {}
    for r in reviews:
        c = out.setdefault(r["case"], {"conditions": {}, "pairs": {}})
        s = c["conditions"].setdefault(r["condition"], {"reviews": 0, "errors": 0, "words": 0, "graded": 0,
                                                         "found": 0, "by_defect": {d: 0 for d in defect_ids[r["case"]]}})
        if r.get("error") or r.get("found") is None:
            s["errors"] += 1
            continue
        s["reviews"] += 1
        s["words"] += r["words"]
        s["graded"] += 1
        s["found"] += sum(r["found"].values())
        for d, hit in r["found"].items():
            s["by_defect"][d] += hit
    for c in out.values():
        for s in c["conditions"].values():
            s["mean_words"] = round(s.pop("words") / s["reviews"]) if s["reviews"] else None
            s["mean_found"] = round(s["found"] / s["graded"], 2) if s["graded"] else None
    for v in verdicts:
        c = out.setdefault(v["case"], {"conditions": {}, "pairs": {}})
        tally = c["pairs"].setdefault(v["pair"], {})
        tally[v["winner"]] = tally.get(v["winner"], 0) + 1
    return out


def _call(host: str, prompt: str, out_dir: Path, args, files: dict[str, str] | None = None,
          omp_model: str | None = None) -> dict:
    """One read-only session in a fresh workspace holding `files`; returns run.execute's result."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ws = Path(tempfile.mkdtemp(prefix="omw-review-"))
    try:
        for name, text in (files or {}).items():
            (ws / name).parent.mkdir(parents=True, exist_ok=True)
            (ws / name).write_text(text, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
        return run.execute(host, prompt, ws, out_dir, args, read_only=True,
                           **({"omp_model": omp_model} if omp_model else {}))
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def review_one(case: dict, meta: dict, run_out: Path, args) -> dict:
    """Run the saved reviewer prompt of one finished run, then grade the review against the planted problems."""
    stage = case["review_stage"]
    record = {"case": case["id"], "host": meta["host"], "condition": meta["condition"], "rep": meta["rep"]}
    review_dir = run_out / "review"
    kept = review_dir / "meta.json"
    if args.resume and kept.is_file():
        old = json.loads(kept.read_text(encoding="utf-8"))
        if not old.get("error") and old.get("found") is not None:
            return old
    shutil.rmtree(review_dir, ignore_errors=True)
    prompt_file = run_out / "workspace" / case["output"]
    if not prompt_file.is_file() or not prompt_file.read_text(encoding="utf-8").strip():
        record.update(error="no reviewer prompt", found=None, words=0)
    else:
        files = {n: case["files"][n] for n in stage["files"]}
        result = _call(meta["host"], prompt_file.read_text(encoding="utf-8"), review_dir, args, files)
        problems = run.isolation_problems(meta["host"], "baseline", None, result["log"])
        error = result["error"] or ("isolation: " + "; ".join(problems) if problems else None)
        review = (review_dir / "reply.md").read_text(encoding="utf-8", errors="replace") if not error else ""
        if not error and not review.strip():
            error = "empty review"
        record.update(error=error, duration_s=result["duration_s"], words=len(review.split()), found=None)
        if not error and stage["defects"]:
            ids = [d["id"] for d in stage["defects"]]
            prompt = GRADER_PROMPT.format(
                document=stage_document(case), review=review,
                defects="\n".join(f"{d['id']}: {d['description']}" for d in stage["defects"]),
                answer_lines="\n".join(f"FOUND {i}: yes|no" for i in ids))
            graded = _call(args.judge, prompt, review_dir / "grade", args,
                           omp_model=run.judge_omp_model(args) if args.judge == "omp" else None)
            reply = (review_dir / "grade" / "reply.md").read_text(encoding="utf-8", errors="replace")
            record["found"] = None if graded["error"] else parse_found(reply, ids)
            if record["found"] is None:
                record["grade_error"] = graded["error"] or "grader reply lacks an answer per problem"
        elif not error:
            record["found"] = {}
    review_dir.mkdir(parents=True, exist_ok=True)
    kept.write_text(json.dumps(record, indent=2), encoding="utf-8")
    hits = "-" if record.get("found") is None else sum(record["found"].values())
    print(f"[review] {case['id']} {meta['condition']} r{meta['rep']}: "
          + (f"ERROR {record['error'] or record.get('grade_error')}" if record.get("error") or record.get("found") is None
             else f"{record['words']} words, found {hits}"), flush=True)
    return record


def judge_reviews(case: dict, host: str, rep: int, pair: tuple[str, str], run_dir: Path, repeat: int, args
                  ) -> dict | None:
    """Blind verdict between the reviews two conditions' prompts produced, over both presentation orders."""
    x, y = pair
    texts = {}
    for cond in pair:
        review_dir = run_dir / "runs" / run.slug_of(case, host, cond, rep, repeat) / "review"
        meta = review_dir / "meta.json"
        if not meta.is_file() or json.loads(meta.read_text(encoding="utf-8")).get("error"):
            return None
        texts[cond] = (review_dir / "reply.md").read_text(encoding="utf-8", errors="replace")
    seed = f"{args.seed}:review:{case['id']}:{host}:{rep}:{x}:{y}"
    first = random.Random(seed).choice([x, y])
    second = y if first == x else x
    tail = f"{case['id'].replace('/', '__')}__{host}__r{rep}__{x}-vs-{y}"
    picks, last = [], ""
    for tag, (a, b) in {"order1": (first, second), "order2": (second, first)}.items():
        prompt = REVIEW_JUDGE_PROMPT.format(brief=case["review_stage"]["brief"], document=stage_document(case),
                                            a=texts[a], b=texts[b])
        out_dir = run_dir / "review-judge" / f"{tail}__{tag}"
        result = _call(args.judge, prompt, out_dir, args,
                       omp_model=run.judge_omp_model(args) if args.judge == "omp" else None)
        reply = "" if result["error"] else (out_dir / "reply.md").read_text(encoding="utf-8", errors="replace")
        m = re.findall(r"VERDICT:\s*(A|B|TIE)", reply)
        picks.append({"A": a, "B": b, "TIE": "tie"}.get(m[-1] if m else "", "error"))
        last = reply
    winner = run.combine_picks(picks)
    reason = " ".join(l.strip() for l in last.splitlines() if l.strip() and not l.startswith("VERDICT"))
    print(f"[review-judge] {case['id']} r{rep} {x} vs {y}: {winner}", flush=True)
    return {"case": case["id"], "host": host, "rep": rep, "pair": run.pair_key(pair), "judge": args.judge,
            "winner": winner, "picks": picks, "reason": reason[:400]}


def report(summary: dict) -> str:
    lines = ["# Review stage", "",
             "Each reviewer prompt from the first stage was run in a fresh session with no skills and read-only "
             "tools; the review is what came back. 'Found' counts the case's planted problems a grader says the "
             "review identifies. Judge verdicts compare the reviews, not the prompts.", ""]
    for case_id, c in sorted(summary.items()):
        lines += [f"## {case_id}", "", "| Condition | Reviews | Errors | Mean words | Mean found | Per problem |",
                  "|---|---|---|---|---|---|"]
        for cond, s in sorted(c["conditions"].items()):
            per = ", ".join(f"{d} {n}/{s['graded']}" for d, n in s["by_defect"].items()) or "-"
            lines.append(f"| {cond} | {s['reviews']} | {s['errors']} | {s['mean_words']} | {s['mean_found']} | {per} |")
        if c["pairs"]:
            lines += ["", "| Pair | Verdicts |", "|---|---|"]
            for pair, tally in sorted(c["pairs"].items()):
                lines.append(f"| {pair} | " + ", ".join(f"{k} {v}" for k, v in sorted(tally.items())) + " |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("run_dir", help="results directory written by run.py")
    p.add_argument("--judge", choices=["codex", "claude", "omp"], required=True,
                   help="host of the grader and the review judge")
    p.add_argument("--pairs", default="skill:baseline",
                   help="condition pairs whose reviews are judged, comma-separated (e.g. skill:baseline,skill:variant-r1)")
    p.add_argument("--cases", action="append", help="glob on case id (default: every case of the run with a review_stage)")
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--omp-model", default="gpt-6-sol", help="model of the omp reviewer sessions")
    p.add_argument("--omp-thinking")
    p.add_argument("--judge-omp-model", help="model of omp grader and judge calls (default: --omp-model)")
    p.add_argument("--codex-model")
    p.add_argument("--codex-effort")
    p.add_argument("--claude-model")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--resume", action="store_true", help="keep finished reviews and verdicts, redo the rest")
    args = p.parse_args(argv)

    run_dir = Path(args.run_dir).resolve()
    info = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    repeat = info.get("repeat", 1)
    cases = {c["id"]: c for c in grade.load_cases(args.cases) if c.get("review_stage")}
    metas = []
    for meta_file in sorted((run_dir / "runs").glob("*/meta.json")):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if meta["case"] in cases and not meta.get("error"):
            metas.append((meta, meta_file.parent))
    if not metas:
        print("no finished runs of a case with a review_stage", file=sys.stderr)
        return 2
    pairs = [tuple(x.split(":", 1)) for x in args.pairs.split(",") if x]
    conditions = {m["condition"] for m, _ in metas}
    missing = sorted({c for pair in pairs for c in pair} - conditions)
    if missing or any(len(pair) != 2 for pair in pairs):
        print(f"--pairs: conditions not in this run: {missing}" if missing else "--pairs wants A:B", file=sys.stderr)
        return 2

    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        reviews = list(pool.map(lambda m: review_one(cases[m[0]["case"]], m[0], m[1], args), metas))

    verdict_file = run_dir / "review_stage.json"
    kept = []
    if args.resume and verdict_file.is_file():
        kept = [v for v in json.loads(verdict_file.read_text(encoding="utf-8")).get("judge", [])
                if v["winner"] != "error"]
    done = {(v["case"], v["host"], v["rep"], v["pair"]) for v in kept}
    todo = sorted({(m["case"], m["host"], m["rep"], pair) for m, _ in metas for pair in pairs
                   if (m["case"], m["host"], m["rep"], run.pair_key(pair)) not in done})
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        verdicts = kept + [v for v in pool.map(
            lambda t: judge_reviews(cases[t[0]], t[1], t[2], t[3], run_dir, repeat, args), todo) if v]

    summary = summarise(reviews, verdicts,
                        {cid: [d["id"] for d in c["review_stage"]["defects"]] for cid, c in cases.items()})
    verdict_file.write_text(json.dumps({"reviews": reviews, "judge": verdicts, "summary": summary}, indent=2),
                            encoding="utf-8")
    (run_dir / "review-stage.md").write_text(report(summary), encoding="utf-8")
    print(f"report: {run_dir / 'review-stage.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
