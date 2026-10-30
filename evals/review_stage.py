#!/usr/bin/env python3
"""Second stage for reviewer-prompt cases: run each saved reviewer prompt in a fresh session, then grade the reviews.

run.py shows a judge the reviewer prompt a writer prepared, never the review that prompt produces. For every finished
run of a case with a `review_stage` block, this script:

1. starts a fresh session on the run's host, with no skills and read-only tools, in a workspace holding only the
   files `review_stage.files` names, and sends the saved prompt as its whole input. The reply is the review
   (runs/<run>/review/reply.md).
2. asks a grader which of the case's planted problems (`review_stage.defects`, written before any run) the review
   identifies, one yes or no per problem, and, when the case lists them, which of the things the reader must be told
   (`review_stage.must_tell`, omissions written from the reader's job before any run) the review asks for, and, with
   --outside-facts, which statements in the review present a fact the document does not contain (a guard against a
   reviewer that fills gaps from its own knowledge).
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

For each known problem, decide whether the review identifies it anywhere in the review, including a fix or a finding about another problem. Count an explicit statement that the information is missing or unclear, or an instruction to the author to supply that information; the review need not repeat the diagnosis or give it a separate item. Match the specific problem (the place, the fact or the missing piece), not merely a nearby topic. Do not count a generic request for more detail, a different omission about the same topic, or a statement that calls the problem fine.
For a missing-information problem that lists multiple missing pieces, count an explicit identification of at least one listed omission. Do not require the review to list every omission or to repeat it in the proposed fix. This does not credit a different gap about the same topic.
Answer with exactly one line per problem, in the order given, and nothing after them:
{answer_lines}"""

MUST_TELL_PROMPT = """You are checking a review of a document against a list of things the document's reader must be told before acting, which the document does not say.

Document:
<document>
{document}
</document>

Things the reader must be told:
{items}

Review:
<review>
{review}
</review>

For each item, decide whether the review asks for it: it counts if the review says that information is missing or unclear, or tells the author to supply it, in any words and even inside a finding about something else. It does not count if the review only touches the topic without saying the information is missing, or if the review supplies the information itself as if the document already gave it.
Answer with exactly one line per item, in the order given, and nothing after them:
{answer_lines}"""

OUTSIDE_FACTS_PROMPT = """You are checking a review of a document for facts the review supplies that the document does not contain.

Document:
<document>
{document}
</document>

Review:
<review>
{review}
</review>

List every statement in the review that presents as true a specific fact about the world that the document does not state and that an author could copy into the document as it stands: a value, quantity, temperature, time, limit, rule, regulation, standard, product, or step of a procedure. Count each such statement once.

Do not list: anything quoted or paraphrased from the document; arithmetic on the document's own figures; a statement that information is missing, unclear or contradictory; an instruction to the author to supply, confirm or decide something ("state the safe opening temperature"); a question; a general consequence any reader would know ("someone could be hurt").

Write one line per statement, quoting the review's own words exactly:
FACT: "<words from the review>"
Then end with exactly one line: TOTAL: <number of FACT lines>
If there are none, write only: TOTAL: 0"""

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


def parse_found(reply: str, ids: list[str], keyword: str = "FOUND") -> dict[str, bool] | None:
    """{id: yes} from the grader's '<keyword> <id>: yes|no' lines (the last line per id wins); None unless every id
    has an answer."""
    found = {}
    for m in re.finditer(rf"(?im)^\s*{re.escape(keyword)}\s+([A-Za-z0-9_-]+)\s*:\s*(yes|no)\b", reply):
        if m.group(1) in ids:
            found[m.group(1)] = m.group(2).lower() == "yes"
    return found if set(found) == set(ids) else None


def _norm(text: str) -> str:
    text = text.translate(str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-",
                                         "\u2014": "-", "*": " ", "#": " ", "`": " ", "_": " "}))
    return re.sub(r"\s+", " ", text).strip().lower()


def misquotes(review: str, reference: str) -> list[str]:
    """Double-quoted spans of the review (straight or curly quotes, three words or more) that do not occur in the
    reference text (the document and the prompt), ignoring case, whitespace, markdown and quote or dash styles. An
    ellipsis splits a quote into pieces, each checked on its own."""
    ref = _norm(reference)
    out = []
    for m in re.finditer(r"\u201c([^\u201d\n]{1,400})\u201d|\"([^\"\n]{1,400})\"", review):
        span = m.group(1) or m.group(2)
        for piece in re.split(r"\u2026|\.\.\.|\[\u2026\]|\[\.\.\.\]", span):
            piece = _norm(piece).strip(" .,;:!?'\"()[]")
            if len(piece.split()) >= 3 and piece not in ref:
                out.append(span)
                break
    return out


def parse_outside(reply: str) -> list[str] | None:
    """The quoted statements of the grader's 'FACT: "..."' lines; None when the reply has no 'TOTAL: <n>' line (the
    grader did not finish). The FACT lines are counted, not the stated total, which a model can miscount."""
    if not re.search(r"(?im)^\s*TOTAL:\s*\d+\s*$", reply):
        return None
    return [m.group(1).strip() for m in re.finditer(r"(?im)^\s*FACT:\s*[\"\u201c](.+)[\"\u201d]\s*$", reply)]


def summarise(reviews: list[dict], verdicts: list[dict], defect_ids: dict[str, list[str]],
              told_ids: dict[str, list[str]] | None = None, outside: bool = False) -> dict:
    """Per case and condition: reviews, errors, mean words, planted problems found (mean and per problem), must-tell
    items asked for (mean and per item, when the case lists any), quotes not in the document, and with `outside` the
    statements of fact the review supplies from outside the document (total and reviews with any); per case and pair:
    judge tallies. Errored or ungraded reviews count as errors, not as zero found."""
    out: dict = {}
    told_ids = told_ids or {}
    for r in reviews:
        c = out.setdefault(r["case"], {"conditions": {}, "pairs": {}})
        s = c["conditions"].setdefault(r["condition"], {"reviews": 0, "errors": 0, "words": 0, "graded": 0, "found": 0,
                                                         "told": 0, "misquotes": 0, "misquoted_reviews": 0,
                                                         "by_defect": {d: 0 for d in defect_ids[r["case"]]},
                                                         "by_item": {d: 0 for d in told_ids.get(r["case"], [])},
                                                         **({"outside": 0, "outside_reviews": 0} if outside else {})})
        needs_told = bool(told_ids.get(r["case"]))
        if (r.get("error") or r.get("found") is None or (needs_told and r.get("told") is None)
                or (outside and r.get("outside") is None)):
            s["errors"] += 1
            continue
        s["reviews"] += 1
        s["words"] += r["words"]
        bad = len(r.get("misquotes", []))
        s["misquotes"] += bad
        s["misquoted_reviews"] += bad > 0
        s["graded"] += 1
        s["found"] += sum(r["found"].values())
        for d, hit in r["found"].items():
            s["by_defect"][d] += hit
        for d, hit in (r.get("told") or {}).items():
            s["told"] += hit
            s["by_item"][d] += hit
        if outside:
            s["outside"] += len(r["outside"])
            s["outside_reviews"] += bool(r["outside"])
    for c in out.values():
        for s in c["conditions"].values():
            s["mean_words"] = round(s.pop("words") / s["reviews"]) if s["reviews"] else None
            s["mean_found"] = round(s["found"] / s["graded"], 2) if s["graded"] else None
            s["mean_told"] = round(s["told"] / s["graded"], 2) if s["graded"] and s["by_item"] else None
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


def _grade(case: dict, review: str, items: list[dict], template: str, keyword: str, out_dir: Path, args
           ) -> tuple[dict | None, str | None]:
    """One grader call over `items`; returns ({id: yes}, None) or (None, why)."""
    ids = [d["id"] for d in items]
    prompt = template.format(document=stage_document(case), review=review,
                             defects="\n".join(f"{d['id']}: {d['description']}" for d in items),
                             items="\n".join(f"{d['id']}: {d['description']}" for d in items),
                             answer_lines="\n".join(f"{keyword} {i}: yes|no" for i in ids))
    graded = _call(args.judge, prompt, out_dir, args,
                   omp_model=run.judge_omp_model(args) if args.judge == "omp" else None)
    reply = "" if graded["error"] else (out_dir / "reply.md").read_text(encoding="utf-8", errors="replace")
    answers = None if graded["error"] else parse_found(reply, ids, keyword)
    return answers, None if answers is not None else (graded["error"] or f"grader reply lacks a {keyword} line per item")


def _grade_outside(case: dict, review: str, out_dir: Path, args) -> tuple[list[str] | None, str | None]:
    """One grader call listing the statements of fact the review supplies from outside the document."""
    graded = _call(args.judge, OUTSIDE_FACTS_PROMPT.format(document=stage_document(case), review=review), out_dir, args,
                   omp_model=run.judge_omp_model(args) if args.judge == "omp" else None)
    reply = "" if graded["error"] else (out_dir / "reply.md").read_text(encoding="utf-8", errors="replace")
    facts = None if graded["error"] else parse_outside(reply)
    return facts, None if facts is not None else (graded["error"] or "outside-facts grader reply lacks a TOTAL line")


def review_one(case: dict, meta: dict, run_out: Path, args) -> dict:
    """Run the saved reviewer prompt of one finished run, then grade the review against the planted problems, the
    things the reader must be told (when the case lists them) and, with --outside-facts, the facts it supplies itself."""
    stage = case["review_stage"]
    must_tell = stage.get("must_tell") or []
    record = {"case": case["id"], "host": meta["host"], "condition": meta["condition"], "rep": meta["rep"]}
    review_dir = run_out / "review"
    kept = review_dir / "meta.json"
    prompt_file = run_out / "workspace" / case["output"]
    if args.resume and kept.is_file():
        old = json.loads(kept.read_text(encoding="utf-8"))
        if not old.get("error") and old.get("found") is not None:
            review = (review_dir / "reply.md").read_text(encoding="utf-8", errors="replace")
            if "misquotes" not in old:
                old["misquotes"] = misquotes(review, stage_document(case) + "\n" + prompt_file.read_text(encoding="utf-8"))
            if must_tell and old.get("told") is None:
                old["told"], why = _grade(case, review, must_tell, MUST_TELL_PROMPT, "TOLD", review_dir / "told", args)
                if why:
                    old["grade_error"] = why
            if args.outside_facts and old.get("outside") is None:
                old["outside"], why = _grade_outside(case, review, review_dir / "outside", args)
                if why:
                    old["grade_error"] = why
            kept.write_text(json.dumps(old, indent=2), encoding="utf-8")
            return old
    shutil.rmtree(review_dir, ignore_errors=True)
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
        record.update(error=error, duration_s=result["duration_s"], words=len(review.split()), found=None,
                      misquotes=misquotes(review, stage_document(case) + "\n" + prompt_file.read_text(encoding="utf-8")))
        if not error:
            record["found"] = {}
            if stage["defects"]:
                record["found"], why = _grade(case, review, stage["defects"], GRADER_PROMPT, "FOUND",
                                              review_dir / "grade", args)
                if why:
                    record["grade_error"] = why
            if must_tell:
                record["told"], why = _grade(case, review, must_tell, MUST_TELL_PROMPT, "TOLD", review_dir / "told", args)
                if why:
                    record["grade_error"] = why
            if args.outside_facts:
                record["outside"], why = _grade_outside(case, review, review_dir / "outside", args)
                if why:
                    record["grade_error"] = why
    review_dir.mkdir(parents=True, exist_ok=True)
    kept.write_text(json.dumps(record, indent=2), encoding="utf-8")
    failed = (record.get("error") or record.get("found") is None or (must_tell and record.get("told") is None)
              or (args.outside_facts and record.get("outside") is None))
    told = f", told {sum(record['told'].values())}" if record.get("told") else ""
    facts = f", outside facts {len(record['outside'])}" if record.get("outside") is not None else ""
    print(f"[review] {case['id']} {meta['condition']} r{meta['rep']}: "
          + (f"ERROR {record.get('error') or record.get('grade_error')}" if failed
             else f"{record['words']} words, found {sum(record['found'].values())}{told}{facts}"), flush=True)
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
             "review identifies; 'Told', when the case lists things the reader must be told, counts those the review "
             "asks for. 'Misquotes' counts double-quoted spans of three words or more that are in neither the "
             "document nor the prompt (reviews with any / spans). 'Outside facts', with --outside-facts, counts "
             "statements a grader says present a fact the document does not contain (reviews with any / statements). "
             "Judge verdicts compare the reviews, not the prompts.", ""]
    for case_id, c in sorted(summary.items()):
        told = any(s["by_item"] for s in c["conditions"].values())
        outside = any("outside" in s for s in c["conditions"].values())
        lines += [f"## {case_id}", "",
                  "| Condition | Reviews | Errors | Mean words | Mean found | Misquotes | Per problem |"
                  + (" Mean told | Per item |" if told else "") + (" Outside facts |" if outside else ""),
                  "|---|---|---|---|---|---|---|" + ("---|---|" if told else "") + ("---|" if outside else "")]
        for cond, s in sorted(c["conditions"].items()):
            per = ", ".join(f"{d} {n}/{s['graded']}" for d, n in s["by_defect"].items()) or "-"
            items = ", ".join(f"{d} {n}/{s['graded']}" for d, n in s["by_item"].items()) or "-"
            lines.append(f"| {cond} | {s['reviews']} | {s['errors']} | {s['mean_words']} | {s['mean_found']} | "
                         f"{s['misquoted_reviews']} / {s['misquotes']} | {per} |"
                         + (f" {s['mean_told']} | {items} |" if told else "")
                         + (f" {s['outside_reviews']} / {s['outside']} |" if outside else ""))
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
    p.add_argument("--outside-facts", action="store_true",
                   help="also grade each review for statements of fact it supplies that the document does not contain")
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
                        {cid: [d["id"] for d in c["review_stage"]["defects"]] for cid, c in cases.items()},
                        {cid: [d["id"] for d in c["review_stage"].get("must_tell", [])] for cid, c in cases.items()},
                        outside=args.outside_facts)
    verdict_file.write_text(json.dumps({"reviews": reviews, "judge": verdicts, "summary": summary}, indent=2),
                            encoding="utf-8")
    (run_dir / "review-stage.md").write_text(report(summary), encoding="utf-8")
    print(f"report: {run_dir / 'review-stage.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
