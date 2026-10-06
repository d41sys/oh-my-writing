---
name: academic-writing
description: Write ML/CV/NLP paper sections (abstract, introduction, related work, method, experiments, conclusion) from the project's results and notes, with checking built into every step so each drafted section comes out story-driven, faithful to the evidence, and free of AI-writing tells. Also revises existing sections with the same procedure. Use when asked to write, draft, or rewrite any part of a paper. ARIS skills (paper-write, paper-claim-audit, citation-audit) remain the pipeline and integrity gates.
---

# Paper Writer

Input: the project's results and notes, the existing draft (if any), and optionally an example paper to learn from. Output: LaTeX that has passed the built-in checks, plus a short list of items the author must approve. Checking is part of writing, not a separate pass.

## Scope: one part or the whole paper
- **One part** (default when the user names a section, e.g. "rewrite the abstract"): run Steps 0–5 for that part only, write the result to `paper/drafts/<section>.tex`, and stop. Do not touch other sections. The next part starts only when the user asks.
- **Whole paper**: run Steps 0–1 once, then Steps 2–5 per section in the order below.

In single-part mode, Step 1 reuses `paper/STORY.md` if it exists; otherwise it builds the card from the existing paper and results, and the author approves it together with the drafted part. Step 4 also checks consistency with the untouched sections (terms, numbers, claim strength) and reports conflicts instead of editing those sections.

## Procedure

### Step 0. Gather inputs
Read, do not guess: results files and tables, `NARRATIVE_REPORT.md`, `PAPER_PLAN.md`, figures, the existing section (if revising), the other sections (for consistency), the review history if any (e.g. ARIS `paper/PAPER_IMPROVEMENT_LOG.md`: wording earlier reviewers required), and `paper/WRITING_LESSONS.md` if present. Every fact you write later must come from these files.

**Example paper (optional).** If the user gives an example paper (arXiv id, PDF, or URL), read the whole paper (not just the abstract) and write `paper/EXEMPLAR_NOTES.md` following `references/exemplar.md`. The notes are about the research, not the sentences: what question they asked and why prior evidence could not answer it, the design lever that makes the question answerable, the chain of experiments and which skeptic question each one closes, how the benchmark was built and kept clean, and which claims each result licenses. Writing moves come last and briefly. The notes end with a transfer table that maps each of their design roles to our paper (we have it / we have it but don't say it / we lack it). Learn structure, argument order, paragraph roles, Figure-1 type, and how they state the "why"; never borrow their claim strength or hedging level, which must come from our evidence. For a numeric style profile, ARIS `paper-write — style-ref: <source>` already produces one; reuse it instead of re-extracting.

### Step 1. Story card (once per paper; the author approves it before any prose)
Write `paper/STORY.md` with one line per field, each filled from the inputs (rules: §1 below):
- Contribution type: insight / performance / capability
- Central claim: "We show X, because Y, evidenced by Z", at the right claim level
- Challenge: what prior work cannot do, **and why** (the technical reason)
- Insight: one sentence the reader can repeat
- Evidence map: claim → table/figure/file → supported / needs evidence / cut
- Novelty: what is new, what is borrowed
- Strongest skeptic objection and the result that answers it
- Opening → Challenge → Action → Resolution, one line each

If the inputs do not give a field (often the *why* of the challenge), write `[ASK AUTHOR: ...]`. Never supply a reason, mechanism, or threat yourself. Stop and show the card to the author; prose starts only after approval.

### Step 2. Section outline
For the section being written, follow its recipe in `references/sections.md`. Write one LaTeX comment per planned paragraph: `% TL;DR: <the paragraph's one message> [source: <file/table>]`. Read the TL;DR lines in order: they alone must tell the section's part of the story. Fix the outline before drafting.

### Step 3. Draft
Under each TL;DR comment, write the paragraph: first sentence states the message; evidence with numbers; last sentence hands off. Apply the sentence rules (§4, `references/style.md`) while writing, not afterwards.

### Step 4. Check (every section, before moving on)
**4a. Self-check by the writer** (mechanical; fix every failure before 4b):
1. **Fact trace**: every number, claim, scope, and qualifier maps to an input file with the same strength. Anything added (a sharper consequence, a mechanism, a broader scope, an aggregated number) is deleted or marked `[VERIFY]`. Anything a reviewer required (improvement log) is present, including pre-specified contrasts.
2. **Story trace**: the TL;DR lines still read as the story; each paragraph does one job; no zig-zag; no paragraph without a duty.
3. **Voice scan**: run the Tier-1 and Tier-2 scans in `references/ai-tells.md` on the new section; rewrite every hit that carries no information.
4. **Consistency**: terms, numbers, and claim strength match the untouched sections; no "don't borrow" move from the example paper appears. Report conflicts; do not edit other sections.
5. **Section rules**: the mechanical rules of the section's recipe in `references/sections.md` (word limit, acronyms spelled out, sentence length, closing-sentence constraint), so the external reviewer's round is not spent on them.

**4b. External review by a different model** (the writer never grades its own prose). Send the draft to a reviewer from another model family, using the prompt in `references/review.md` ("External reviewer prompt"):
- Default: Codex CLI, one fresh session per round, read-only, run from the repo root so the reviewer reads the draft, `paper/STORY.md`, the sources, and the improvement log itself. Save the prompt to a file, then:
  `codex exec -m <model> -c model_reasoning_effort=xhigh -s read-only --skip-git-repo-check -o paper/drafts/reviews/<section>_round<N>.md - < prompt.txt`
  Model: ARIS `REVIEWER_MODEL` if the installed CLI supports it, else the model of the last successful review round recorded in the project's review history. The `mcp__codex__codex` tool also works but times out at 30 s on xhigh reviews; prefer the CLI.
- Never resume a session and never tell the reviewer what was fixed or why; it sees only the current files.
- If Codex is unavailable, use a subagent pinned to a different model than the writer. If no other model is available, say "external review not run" in the hand-off; never substitute a self-review.
- Apply CRITICAL and MAJOR findings that the evidence supports; a finding that would add an unsupported claim is rejected with a one-line reason. Re-run 4a, then one more fresh 4b round. At most two 4b rounds per section; report what remains.

### Step 5. Hand-off
Return the drafted part and a short list: `[ASK AUTHOR]` / `[VERIFY]` items, anything cut, rounded, or moved, which example-paper roles were used, conflicts with untouched sections, the external reviewer's verdict and any finding not applied (with reason), and any check that still fails. In single-part mode, stop here.

**Order of sections (whole paper)**: story card → abstract draft (forces focus) → introduction → method/protocol → experiments → related work → conclusion → abstract rewritten last. Figures and tables are planned with the outline of the section that uses them (`references/figures-latex.md`).

**Revising an existing section**: same steps, but edit, do not rewrite. An existing paper that was already checked and submitted is the default text; every sentence you keep needs no re-verification, every sentence you rewrite does. Step 0 input is the existing text. Before drafting, mark each sentence keep / fix / cut, and change only sentences with a concrete defect (wrong fact, missing required element, reviewer request, rule violation). Reuse the old wording for everything else, including whole parts that already work (e.g. a challenge or motivation passage). Never paraphrase a correct sentence. Step 4's fact trace then covers only the changed sentences, compared against the old text and the results; the hand-off lists each change with its reason.

## Principles behind every step

A reader has limited attention and no access to your head (you have months of context, the reader has none). Every rule here either (a) tells the reader what to expect before they read it, (b) puts the important thing where they look, or (c) removes something that costs attention without paying information. AI-sounding prose fails (c): it is statistically average text, so it says what any paper could say. Expert prose is specific: it names this paper's object, number, and reason.

The goal is that the reader **understands**, **remembers**, and **believes** one to three claims. Inform, do not persuade.

**Specific never means invented.** Specificity comes from the paper's own facts. Never add a consequence, threat, mechanism, reason, or scope the sources do not state.

**Clarity beats rule compliance.** Plain words over internal labels ("main bottleneck" over a lab-internal label like "dominant gate" when the meaning is equal). One organizing sentence before a block of evidence ("We assign each failure to the step where it occurs") is signposting, not filler. If following a rule makes a passage harder to read, the rule is being misapplied.

Title, abstract, introduction, and Figure 1 set a judgement the rest of the paper rarely changes; give them as much effort as everything else combined. If an hour of your time saves a reviewer one minute, spend it.

## §1 Story rules (used in Step 1)

1. **Contribution type, pick one**: *insight* (explain something that exists), *performance* (do it better), *capability* (do something new). Analysis/benchmark papers are insight papers: the story is a finding, not a method.
2. **One central claim**, falsifiable: "improves" or "enhances" are not claims; "reduces error from a to b on C" is. After the abstract alone, a reviewer must be able to write "X is good for Y in the context of Z".
3. **Challenge = observable limitation + technical reason**: "Prior methods fail at A because B." The reason comes from the sources or the author, never from you.
4. **Insight**: why our approach removes B, in one sentence.
5. **Evidence map**: unsupported claims are narrowed or cut, never softened with a synonym.
6. **Claim level**: *existence* ("we find cases where X"), *systematic* ("X holds across N settings"), *narrow* ("X holds for A under condition B"), *guarantee* ("X always holds"). Pick the strongest level the evidence supports and write exactly that; hedge words never replace picking the level.
7. **The contest you win**: frame around the strongest real result. Informing outranks winning: never omit, bury, or spin an unfavorable number.
8. **Novelty statement**: what is new and what is borrowed. The same paper reads as arrogant or as modest depending on this sentence.
9. **Red-team**: assume a mistake exists and find it; name the skeptic's alternative explanations and which result rules each out; say which analyses were post hoc.

Never frame the work as "naive baseline, then our fix": it reads as an incremental patch. Never hide a simple method behind invented terms.

## §2 Structure rules (used in Step 2)

- Context → content → conclusion at every scale. Abstract = the story in miniature; introduction = the abstract expanded; body = the introduction expanded.
- Results are a chain of statements, each building on the last, in the order the argument needs, not the order experiments were run.
- Every experiment has a duty: shows it works, shows the mechanism causes the gain, shows value in the target setting, or rules out an alternative. No duty → appendix.
- One running example through the paper when possible; the concrete example before the general definition.
- Non-original background in a short Preliminaries, so the reader sees where the contribution starts.
- Every section must answer "what does removing this cost the story?" No answer → appendix.

## §3 Paragraph rules (used in Steps 2–3)

- One message per paragraph; the first sentence states it; the last sentence concludes or hands off.
- No zig-zag: introduce A then B, discuss A then B; parallel ideas get parallel sentence shape.
- Each sentence relates to the previous one by cause, contrast, consequence, refinement, or example. Connectives match the real logic: no "To this end" without a stated goal; no "First/Second" for unordered items.
- Explain a term where it first appears; define every acronym at first use.
- Vary paragraph shape; identical molds numb the reader.

## §4 Sentence rules (used in Step 3; full list in `references/style.md`)

- Old, linking information at the start of a sentence; the new point at the end.
- Subject and verb adjacent; actions in verbs, not nouns.
- Active voice by default; passive allowed in method/setup when the agent does not matter.
- Past tense for what we ran and observed; present tense for what holds and for the paper itself; never "we will show".
- One concept, one name, everywhere including captions.
- Hedge words are deleted unless the uncertainty is real. Claim-defining and reviewer-required qualifiers stay. Generic caveats live only in Limitations; no self-defence ("we do not claim").
- No anthropomorphic words ("understands", "commits") for claims about internal processes seen only from outputs; name the source of each gain.
- No "for various reasons", no "etc." unless obvious, no non-referential "this", no em dashes; italics only for definitions.
- Every "X is critical" gets a citation or number; every "the gain comes from Y" gets the ablation.

## Reference files
| File | Used in |
|---|---|
| `references/sections.md` | Step 2 recipes and Step 4 section checklists |
| `references/style.md` | Step 3 sentence rules |
| `references/ai-tells.md` | Step 4 voice scan |
| `references/figures-latex.md` | figures, tables, math, citations, final checks |
| `references/review.md` | Step 4b external reviewer prompt, reviewer questions, this project's lessons |
| `references/exemplar.md` | Step 0 analysis of an example paper (research design first, writing last) |

## With ARIS
`/paper-plan` → this skill's Step 1 story card feeds the claims-evidence matrix. `/paper-write` → use Steps 2–5 per section. After all sections: ARIS `paper-claim-audit`, `citation-audit`, `auto-paper-improvement-loop`.
