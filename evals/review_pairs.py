#!/usr/bin/env python3
"""Build a one-file blind A/B review page from a benchmark results directory.

Usage:
  python3 evals/review_pairs.py evals/results/<run-id>                  # writes review/<run-id>.html
  python3 evals/review_pairs.py evals/results/<run-id> --out review/x.html --seed 3

For every (case, host, repetition) with an output from both conditions the page shows the task, the source
documents, and the two reports side by side in random order (seeded). You rate each pair (A better, B better,
tie) with an optional note; ratings are kept in the browser (localStorage) and can be exported as JSON.
Reveal, which shows which side had the skills, unlocks only when every pair is rated.
The page is self-contained: reports are embedded (iframe srcdoc), no network, no scripts from the reports run.
Do not commit the output: review/ is a local folder.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade  # noqa: E402

SOURCE_PREVIEW_CHARS = 6000


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _local_file(ref: str, base: Path, root: Path) -> Path | None:
    if not ref or re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", ref, re.I):
        return None
    target = (base / ref.split("#")[0].split("?")[0]).resolve()
    return target if target.is_file() and grade._within(target, root) else None


def inline_local(markup: str, base: Path, root: Path) -> str:
    """Inline local images and stylesheets so a report renders inside srcdoc, where relative paths do not resolve."""
    def image(m):
        target = _local_file(m.group(3), base, root)
        return f"{m.group(1)}{m.group(2)}{_data_uri(target) if target else m.group(3)}{m.group(2)}"

    def link(m):
        tag = m.group(0)
        rel = re.search(r"""\brel=["']?([^"'\s>]+)""", tag, re.I)
        href = re.search(r"""\bhref=["']([^"']+)["']""", tag, re.I)
        target = _local_file(href.group(1), base, root) if href else None
        if target and rel and rel.group(1).lower() == "stylesheet":
            return "<style>" + target.read_text(encoding="utf-8", errors="replace") + "</style>"
        return tag

    markup = re.sub(r"""(<img\b[^>]*?\bsrc=)(["'])(.*?)\2""", image, markup, flags=re.I | re.S)
    return re.sub(r"<link\b[^>]*>", link, markup, flags=re.I)


def side_document(case: dict, ws: Path) -> tuple[str, str] | None:
    """(kind, full HTML document) shown for one side: the rendered HTML report if there is one, else the text."""
    candidates = [case.get("judge", {}).get("render")] + [
        d for d in case.get("deliverables", []) if d.lower().endswith((".html", ".htm"))]
    for rel in filter(None, candidates):
        path = ws / rel
        if path.is_file():
            return "html", inline_local(path.read_text(encoding="utf-8", errors="replace"), path.parent, ws)
    out = ws / case["output"]
    if out.is_file():
        body = html.escape(out.read_text(encoding="utf-8", errors="replace"))
        return "text", ("<!doctype html><meta charset=\"utf-8\"><pre style=\"white-space:pre-wrap;margin:1rem;"
                        "font:14px/1.55 ui-monospace,Menlo,Consolas,monospace\">" + body + "</pre>")
    return None


def collect_pairs(run_dir: Path, seed: int) -> tuple[list[dict], list[str]]:
    cases = {c["id"]: c for c in grade.load_cases()}
    sides: dict[tuple, dict] = {}
    for meta_path in sorted((run_dir / "runs").glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta["condition"] in ("skill", "baseline"):  # competitor and variant runs are not part of this page
            sides.setdefault((meta["case"], meta["host"], meta.get("rep") or 1), {})[meta["condition"]] = meta_path.parent
    pairs, skipped = [], []
    for (case_id, host, rep), conds in sorted(sides.items()):
        case = cases.get(case_id)
        label = f"{case_id} {host} r{rep}"
        if case is None:
            skipped.append(f"{label}: case file not found")
            continue
        docs = {c: side_document(case, d / "workspace") for c, d in conds.items()}
        if set(conds) != {"skill", "baseline"} or any(v is None for v in docs.values()):
            skipped.append(f"{label}: needs an output from both conditions")
            continue
        a_is = "skill" if random.Random(f"{seed}:{case_id}:{host}:{rep}").random() < 0.5 else "baseline"
        b_is = "baseline" if a_is == "skill" else "skill"
        texts = grade.source_texts(case)
        root = grade.fixture_root(case)
        sources = []
        for name, text in texts.items():
            size = (root / name).stat().st_size if root and (root / name).is_file() else len(text.encode("utf-8"))
            sources.append({"name": name, "size": size, "text": text[:SOURCE_PREVIEW_CHARS],
                            "cut": len(text) > SOURCE_PREVIEW_CHARS})
        pairs.append({"id": f"p{len(pairs)}", "case": case_id, "host": host, "rep": rep, "prompt": case["prompt"],
                      "a_is": a_is, "sources": sources, "a": docs[a_is], "b": docs[b_is]})
    return pairs, skipped


CSS = """
:root{--ink:#1b2430;--muted:#5b6676;--rule:#d5dae1;--soft:#f4f6f8;--accent:#1f4e79;--ok:#1b6e3c}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:#fff}
header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--rule);padding:.6rem 1.2rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap}
header h1{font-size:1rem;margin:0}header .grow{flex:1}
button{font:inherit;border:1px solid var(--rule);background:#fff;color:var(--ink);padding:.35rem .8rem;border-radius:6px;cursor:pointer}
button:hover:not(:disabled){border-color:var(--accent)}button:disabled{opacity:.45;cursor:not-allowed}
button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
main{padding:1rem 1.2rem 4rem;max-width:1800px;margin:0 auto}
section.pair{border:1px solid var(--rule);border-radius:8px;margin:0 0 2rem;padding:1rem}
section.pair h2{font-size:1rem;margin:0 0 .5rem}
.meta{color:var(--muted);font-size:.85rem}
details{margin:.4rem 0}summary{cursor:pointer;color:var(--accent)}
details pre{background:var(--soft);padding:.6rem;overflow:auto;max-height:18rem;white-space:pre-wrap;font-size:12.5px}
.task{background:var(--soft);padding:.6rem .8rem;border-radius:6px;white-space:pre-wrap}
.sides{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:.8rem}
.side h3{margin:0 0 .3rem;font-size:.95rem}
iframe{width:100%;height:78vh;border:1px solid var(--rule);border-radius:6px;background:#fff}
.rate{margin-top:.8rem;display:flex;gap:.5rem;align-items:flex-start;flex-wrap:wrap}
.rate textarea{flex:1;min-width:16rem;min-height:2.4rem;font:inherit;border:1px solid var(--rule);border-radius:6px;padding:.4rem}
.reveal{display:none;margin-top:.6rem;font-weight:600;color:var(--ok)}
body.revealed .reveal{display:block}
#summary{display:none;margin:1rem 0;padding:.8rem 1rem;border:1px solid var(--ok);border-radius:8px}
body.revealed #summary{display:block}
@media(max-width:900px){.sides{grid-template-columns:1fr}}
"""

SCRIPT = """
const DATA = JSON.parse(document.getElementById('data').textContent);
const KEY = 'omw-review:' + DATA.run + ':' + DATA.seed;
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { state = {}; }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
const rated = () => DATA.pairs.filter(p => state[p.id] && state[p.id].choice).length;
const label = {A: 'A better', B: 'B better', tie: 'Tie'};
function preferred(p, choice) { return choice === 'tie' ? 'tie' : (choice === 'A' ? p.a_is : (p.a_is === 'skill' ? 'baseline' : 'skill')); }
function refresh() {
  document.getElementById('progress').textContent = rated() + ' / ' + DATA.pairs.length + ' rated';
  document.getElementById('reveal').disabled = rated() < DATA.pairs.length;
  DATA.pairs.forEach(p => {
    const r = state[p.id] || {};
    document.querySelectorAll('#' + p.id + ' .rate button').forEach(b => b.classList.toggle('on', b.dataset.choice === r.choice));
    const out = document.querySelector('#' + p.id + ' .reveal');
    if (r.choice) out.textContent = 'A was ' + (p.a_is === 'skill' ? 'with skills' : 'baseline') + ', B was ' +
      (p.a_is === 'skill' ? 'baseline' : 'with skills') + '. You preferred: ' + ({skill: 'with skills', baseline: 'baseline', tie: 'neither'})[preferred(p, r.choice)] + '.';
  });
}
function summary() {
  const n = {skill: 0, baseline: 0, tie: 0};
  DATA.pairs.forEach(p => { const r = state[p.id]; if (r && r.choice) n[preferred(p, r.choice)]++; });
  document.getElementById('summary').textContent = 'You preferred the with-skills report in ' + n.skill + ' pairs, the baseline in ' + n.baseline + ', and neither in ' + n.tie + ' (of ' + DATA.pairs.length + ').';
}
document.querySelectorAll('section.pair').forEach(sec => {
  const p = DATA.pairs.find(x => x.id === sec.id);
  sec.querySelectorAll('.rate button').forEach(b => b.addEventListener('click', () => {
    state[p.id] = Object.assign({}, state[p.id], {choice: b.dataset.choice}); save(); refresh(); if (document.body.classList.contains('revealed')) summary();
  }));
  const note = sec.querySelector('textarea');
  note.value = (state[p.id] && state[p.id].note) || '';
  note.addEventListener('input', () => { state[p.id] = Object.assign({}, state[p.id], {note: note.value}); save(); });
});
document.getElementById('reveal').addEventListener('click', () => { document.body.classList.add('revealed'); summary(); refresh(); });
document.getElementById('export').addEventListener('click', () => {
  const rows = DATA.pairs.map(p => { const r = state[p.id] || {}; return {
    case: p.case, host: p.host, rep: p.rep, a_is: p.a_is, b_is: p.a_is === 'skill' ? 'baseline' : 'skill',
    choice: r.choice || null, preferred: r.choice ? preferred(p, r.choice) : null, note: r.note || ''}; });
  const blob = new Blob([JSON.stringify({run: DATA.run, seed: DATA.seed, exported: new Date().toISOString(), ratings: rows}, null, 2)], {type: 'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'ratings-' + DATA.run + '.json'; a.click();
});
document.getElementById('clear').addEventListener('click', () => {
  if (confirm('Delete all ratings and notes on this page?')) { state = {}; save(); location.reload(); }
});
refresh();
"""


def render_page(run_id: str, seed: int, pairs: list[dict]) -> str:
    esc = html.escape
    sections = []
    for i, p in enumerate(pairs, 1):
        sources = "".join(
            f"<details><summary>{esc(s['name'])} <span class=\"meta\">({s['size']} bytes)</span></summary>"
            f"<pre>{esc(s['text'])}{'&#10;[preview cut]' if s['cut'] else ''}</pre></details>" for s in p["sources"])
        frames = "".join(
            f"<div class=\"side\"><h3>Report {side}</h3><iframe sandbox=\"\" title=\"Report {side}, pair {i}\" "
            f"srcdoc=\"{esc(doc[1], quote=True)}\"></iframe></div>"
            for side, doc in (("A", p["a"]), ("B", p["b"])))
        sections.append(
            f"<section class=\"pair\" id=\"{p['id']}\"><h2>Pair {i} of {len(pairs)}: {esc(p['case'])} "
            f"<span class=\"meta\">{esc(p['host'])}, repetition {p['rep']}</span></h2>"
            f"<details open><summary>Task given to the agent</summary><div class=\"task\">{esc(p['prompt'])}</div></details>"
            f"<details><summary>Source documents ({len(p['sources'])})</summary>{sources}</details>"
            f"<div class=\"sides\">{frames}</div>"
            "<div class=\"rate\"><button data-choice=\"A\">A better</button><button data-choice=\"tie\">Tie</button>"
            "<button data-choice=\"B\">B better</button><textarea placeholder=\"Note (optional)\" "
            "aria-label=\"Note\"></textarea></div><div class=\"reveal\"></div></section>")
    data = {"run": run_id, "seed": seed,
            "pairs": [{k: p[k] for k in ("id", "case", "host", "rep", "a_is")} for p in pairs]}
    data_json = json.dumps(data).replace("</", "<\\/")
    return (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" "
            f"content=\"width=device-width,initial-scale=1\"><title>Blind review {esc(run_id)}</title>"
            f"<style>{CSS}</style></head><body><header><h1>Blind review: {esc(run_id)}</h1>"
            "<span id=\"progress\"></span><span class=\"grow\"></span>"
            "<button id=\"export\">Export JSON</button><button id=\"reveal\" disabled>Reveal</button>"
            "<button id=\"clear\">Clear</button></header><main>"
            "<p class=\"meta\">Rate which report you would rather hand to the reader. A and B are in random order. "
            "Reveal unlocks after every pair is rated. Ratings are saved in this browser.</p>"
            "<div id=\"summary\"></div>" + "".join(sections) + "</main>"
            f"<script id=\"data\" type=\"application/json\">{data_json}</script><script>{SCRIPT}</script></body></html>")


def build_page(run_dir: Path, seed: int = 7) -> tuple[str, int, list[str]]:
    pairs, skipped = collect_pairs(run_dir, seed)
    return render_page(run_dir.name, seed, pairs), len(pairs), skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_dir", type=Path, help="results directory written by run.py")
    ap.add_argument("--out", type=Path, help="output HTML (default: review/<run-id>.html in the repository)")
    ap.add_argument("--seed", type=int, default=7, help="seed for the A/B order")
    args = ap.parse_args(argv)
    run_dir = args.run_dir.resolve()
    if not (run_dir / "runs").is_dir():
        print(f"{run_dir} has no runs/ directory", file=sys.stderr)
        return 2
    page, n, skipped = build_page(run_dir, args.seed)
    for line in skipped:
        print(f"skipped {line}", file=sys.stderr)
    if n == 0:
        print("no pair has an output from both conditions", file=sys.stderr)
        return 1
    out = (args.out or grade.REPO / "review" / f"{run_dir.name}.html").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"{n} pairs -> {out}  (open {out})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
