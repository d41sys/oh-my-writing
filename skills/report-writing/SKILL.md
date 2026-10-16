---
name: report-writing
description: "Writes and revises reports that support a decision or record findings, including decision memos (which vendor, option or plan to pick, from pilot notes), research and analysis reports, market and competitive reports, executive summaries, status or progress reports, investor update materials, audit reports, lessons-learned entries, and blameless post-mortems of an outage or incident from raw notes. Leads with the answer and how sure the author is, keeps observation, inference and recommendation apart, and makes comparisons fair and numbers traceable. Use when asked to write a decision memo or a memo on which vendor or option to choose, an executive summary, market or competitive analysis, research report, status report, investor update, one-pager, audit report, or a post-mortem or incident write-up for the team, or to turn findings into a recommendation. Not for ML paper sections, blog posts (including a public post telling an incident's story), outreach emails, or technical documentation."
license: MIT
metadata:
  version: "1.3"
  skill-author: d41sys
---

# Report writing

A report exists so a specific reader can decide something or trust a record. This skill puts the answer first, shows the evidence the decision needs, and keeps the line between what was observed, what is inferred, and what is recommended. It works from the author's material and never supplies facts the author did not.

## When to use

- A decision memo, option comparison, or recommendation for a named decision-maker.
- A research, analysis, market, or competitive report, or a landscape review.
- An executive summary, either for a report being written or for one that already exists.
- A status or progress report written from notes or figures in the conversation, an investor update, a one-pager, or a deck's supporting memo. (A project, status or final report built from a folder of documents, or one that needs designed diagrams and a print-ready HTML file, is `project-report`.)
- A blameless post-mortem or incident review document written for the team, or a lessons-learned entry. (A public blog post that tells an incident's story is `post-writing`.)
- An audit or diagnostic report that checks something against a standard and lists what fails.
- Revising any of the above: restructure, tighten, repair the comparison, fix inconsistent numbers.

Not for: ML paper sections (use `academic-writing` if installed; otherwise `structured-drafting` for structure plus `evidence-grounded-writing` for claims); blog posts, essays, newsletters and public incident-story posts (use `post-writing`); tutorials, READMEs, PR descriptions, release notes, changelogs (use `technical-docs`); résumés, application letters and job or academic outreach (use `career-documents`); only checking claims or citations (use `evidence-grounded-writing`); only reviewing a finished draft (use `independent-review`). For a generic material-to-outline job with no report genre, use `structured-drafting`. Investor, customer or partner outreach messages (cold emails, pitches, sales follow-ups) are out of scope for all of the writing skills here: this skill writes the investor update report, not the outreach email.

## Inputs

Read what the author supplied before asking anything: data, notes, prior reports, the question, the audience. Ask at most three questions, fewer for short tasks, and only when the answer changes the output:

1. Who decides, what are they deciding, and by when? (A report with no decision is a record; say so and pick the record shape.)
2. What does the reader already believe or want? (This sets how much proof the lead needs.)
3. Is there a length, template, or companion material (deck, model, earlier memo) the numbers must match?

If the author does not answer (and always in non-interactive runs), proceed, state the assumption in one line at the top of your reply, and log each gap as a question for the author. Log it as `[ASK AUTHOR: ...]` (the author knows or decides it) or `[VERIFY: ...]` (a source exists or must be found and checked); a command, query, or code line quoted in a report that was not run is logged as `[UNTESTED]`. These marker lines live in the reply and in `open-questions.md`, not in the reader's report (see "The report reads as finished"). Never fill a gap with a plausible number.

## Workflow

Pick the mode first: **draft** (material to report), **revise** (existing report; smallest effective edit, keep the author's findings and qualifiers unless they are the defect), or **summarize** (executive summary of an existing report; only restate what the report supports).

1. **Name the type and the reader's job.** Match the request to one shape in [report types](references/report-types.md): decision memo, research report, market or competitive report, executive summary, status report, investor materials, post-mortem, lessons-learned entry, audit report. Write one line: "The reader is X; after reading they will decide or believe Y."
2. **Inventory the material.** List each fact, number, and source the author gave. Tag every material statement as observation, inference, forecast, opinion, or recommendation. Flag any number lacking a unit, period, baseline, or source. Log the gaps now (as questions for the reply), and decide for each whether the report states it plainly or omits the sentence.
3. **Find the core finding.** State it in one sentence a skeptical reader could dispute. Try the opposite: if nobody could hold it, it is a platitude and needs a sharper claim. Then attack it with the strongest counter-evidence in the material. Result: holds, morphs (say what changed), or breaks (report what replaces it rather than defending it). If the material supports no finding, say that plainly and write the record shape instead.
4. **Choose the spine for the type.** Load [report types](references/report-types.md) for the section order, density, and traps of that type. Start from the template in [decision memo template](assets/decision-memo-template.md) or [research report template](assets/research-report-template.md) when the author has none. Drop sections the reader will not use; keep the evidence trail.
5. **Build any comparison before writing about it.** If options, vendors, competitors, or periods are compared, follow [comparisons and recommendations](references/comparisons-and-recommendations.md): fix the measurement contract, state criteria and weights as choices before scoring, tag evidence as proven or asserted, mark unknown as unknown, and test whether the ranking survives a change of weights.
6. **Draft the body, decision-first.** Lead with the recommendation or finding, how confident it is and why, and what would change it. If the author's material states no recommendation, follow the recommendation-ownership rule below instead of supplying one. Then give the evidence the decision needs, in the order the reader will challenge it. Put method, raw data, and source records in the appendix.
7. **Choose tables and figures by the relationship shown.** Use [tables and figures](references/tables-and-figures.md). Each visual answers one question and has a caption that states the finding. If prose is clearer, use prose.
8. **Write the executive summary last.** It must be readable alone: finding, key numbers with their baselines, recommendation, confidence, and the decision or action requested. No method section, no new claims.
9. **Run the consistency sweep.** Recompute totals and percentages from their parts. Check every number against its source and against every companion material (deck equals memo equals model). Check as-of dates, units, currency, and period labels. If two versions of a number exist, stop and resolve it with the author before continuing.
10. **Hand off, then self-check.** If `evidence-grounded-writing` is available, route claim, citation, and number checks to it; otherwise apply the checks in [eval.md](eval.md). If `independent-review` is available, offer a fresh-reader pass on anything going to a decision-maker. If `anti-slop-editing` is available, run it as the final pass; otherwise apply the pattern checks in [eval.md](eval.md). If the author has a house voice, apply `author-voice`. Fix every failure, then return.

## Rules

- **Answer first.** The reader's time is the scarce resource, and a decision-maker who must dig for the point may decide on the wrong one. Lead with the recommendation or finding. Exception: when the reader will reject the conclusion without one piece of context, give that piece in a single sentence before the answer, not three paragraphs. Fixed-order records (status logs, ledgers) keep their template order but still flag what changed or needs action in the first lines.
- **State confidence with its reason.** "High, because the figure is audited and matches scope" is checkable; "we are fairly confident" is not. Use high, medium, low, and say what each rests on. Do not give numeric probabilities unless a stated model produces them. Exception: a purely descriptive record that makes no forecast or judgment needs no confidence label.
- **Keep observation, inference, and recommendation apart.** Readers act on a recommendation differently than on a measurement, and mixing them hides which part they may challenge. Label or position them so each is identifiable. An interview theme is not prevalence; a scenario is not a prediction; a correlation is not a cause.
- **Every number carries its context.** Give unit, period, geography or population, baseline, source, and as-of date, because a bare "grew 40%" cannot be judged. Name the source ("a 2023 survey of 400 users"), never "studies show" or "experts agree". A derived figure is labeled a calculation with its inputs visible; do not present it as if a source printed it. Exception: a number repeated within one paragraph after its first full statement can be short.
- **Compare like with like.** Same metric definition, same window, same baseline, same scope for every candidate. Where they cannot match, say so beside the figure. If the windows or definitions cannot be aligned, do not rank, sum, or average on that criterion: show the figures side by side with each window named, say what measurement would make them comparable, and decide on the criteria that were measured alike. Unknown is not "no" and "not checked" is not "failed"; show them as such.
- **Weights and criteria are choices; show them.** Declare them before looking at composites, and show the ranking under at least one alternative weighting. A composite may summarize but never replaces the per-criterion scores or a failed hard requirement. Exception: a simple ranking with two or three obvious criteria needs no weighting scheme.
- **Estimates are labeled estimates.** Do not turn a forecast, a vendor claim, or a model output into a fact by phrasing. Show the assumptions that drive it. Hedge where the uncertainty is real, once, at that claim; do not coat the whole report in "may" and "could".
- **Options include doing nothing, and a trigger.** A recommendation is credible when the reader can see the alternatives it beat, what it costs, and what evidence would reverse it. Exception: a status report that requests no choice needs none.
- **Recommend concretely.** Action, expected impact, effort or cost, owner and date where the author knows them. When impact has no number, state it qualitatively; never invent a percentage. "Consider exploring" is not a recommendation.
- **The recommendation is the author's.** It is a judgment and a commitment, so write it only when the notes state it or the author confirms it. When the notes give none and the request asks for "our recommendation", lead the summary with the findings and say plainly that the notes make no recommendation: present the options the evidence supports and what each rests on, without choosing, and say what the evidence points toward as analysis (not as the author's position). The question ("notes support X or Y; which do you recommend?") goes to the reply as an `[ASK AUTHOR: ...]` line. Exception: when the author said "you decide" or asked for your own recommendation, give it, label it yours, and show the reasoning.
- **The report reads as finished.** Unless the author asked for a draft to edit, text a reader receives holds no `[ASK AUTHOR]`, `[VERIFY]` or `[UNTESTED]` marker, no draft banner and no note addressed to the author. A gap is stated in reader language as a fact about the material ("The notes do not give a launch date."; "Owner: not assigned in the notes."; "The source analysis makes no recommendation; the options are set out below.") or the sentence is omitted. The author's question goes to the reply and, when the report is saved as a file, also to `open-questions.md` beside it. Reason: a placeholder in a document sent to a reader looks unfinished, and in a run with no author to answer it stays in the reader's hands. Never invent to close a gap: no estimated figure, owner, date or recommendation. Keep process narration out of reader text ("I ran a scanner", "as requested", per-paragraph source notes, `[source: ...]` tags); it goes in the reply. Sources a reader would check (a survey, a contract, a log) are content and stay. Exception: the author asked for a draft to edit; then markers stay at the gap in the file, with a draft banner, and in `open-questions.md`. Author-facing artifacts keep markers: the reply, `open-questions.md`, the revise-mode change list, and any worksheet shown to the author. Memos, summaries, research and status reports, investor materials, audit reports, post-mortems and lessons-learned entries are reader-facing. Wording for common gaps and the file format: [report types](references/report-types.md), "Gaps in a reader-facing report".
- **One source of truth for shared numbers.** When a deck, memo, model, and email repeat figures, they must come from one list and agree exactly, including rounding. Exception: deliberate rounding for a slide is fine if the precise figure is one click away and the rounding rule is consistent.
- **Match density and voice to the type.** Decision and research reports run cool, plain, active, and dense; status reports are terse; investor and post-mortem pieces are plain and specific with a little more warmth. Never use hype or inflated adjectives to carry weight the evidence should carry. A cool register still needs a reason for the reader to care: state the consequence, not mood.
- **Post-mortems are blameless and causal.** The goal is changing the system, so describe conditions and decisions as made with the information then available, and trace causes to mechanisms. "Human error" and "should have been more careful" are stopping points, not root causes. Every causal claim needs evidence; mark probable causes as probable. Times, durations, and counts come from the author's record: compute a duration only from timestamps given, show the arithmetic, and state an unknown time as not known. When the notes assign fault to a named person, keep the observable event and its conditions, write the role instead of the name, and drop the verdict. The post-mortem is a reader-facing document: an action item with no owner or date in the notes reads "owner: to be assigned" and "date: not set", and the question goes to the reply.
- **Every stated value survives the write-up.** Every measured value, threshold, limit, config setting (including the value it replaced or should have had), duration and count in the author's notes stays in the report unless the author cut it, because a reader acting on the report needs the figure that makes the cause or comparison concrete ("set to null instead of 30 seconds", not "set to null"). Dropping blame, a name or a tangent never justifies dropping a number. If you leave one out on purpose, list it (value and reason) in the reply, or the change list in revise mode, never inside the report; a silent omission is a defect. Before returning, scan the notes for each number and unit and find it in the report.
- **Preserve when editing.** In revise mode keep the author's claims, qualifiers, negations, figures, names, and structure unless they are the defect. Report each change and the reason in one line.
- **Other languages.** For Vietnamese or any non-English report apply the structural checks (decision first, evidence, context for numbers, consistency, preservation); the English word-level pattern lists do not transfer. Keep technical terms the way that community uses them.
- **Not advice.** Investor and regulatory material is writing support; do not give legal, financial, or compliance conclusions, and do not call anything compliant, certified, or audit-ready without the author's evidence.

## Output

Return, in this order:

1. The report in the author's format (Markdown by default), with one H1, sentence-case headings, no skipped levels. It is finished reader text: no markers, no draft banner, no notes to the author. Gaps are stated plainly or omitted. If the request asks for a draft to edit, markers and a draft banner stay.
2. When the report is saved as a file: `open-questions.md` beside it, one numbered `[ASK AUTHOR: ...]` or `[VERIFY: ...]` line per gap, each with what it blocks and what the report says instead (format in [report types](references/report-types.md)). Skip the file when no question is open.
3. A short note in the reply (3 to 8 lines): the type and reader assumed, the core finding in one sentence with its stress-test result, assumptions made, each open question in full as the same marker line (the author can answer from the reply), values left out on purpose, and which hand-offs ran.
4. In revise mode, a change list in the reply: what changed and why, one line each, and anything deliberately left alone.

Do not append praise, a recap of the report, or offers of further help.

## Examples

Lead before and after (invented figures for illustration only):

> Before: "This memo reviews three vendors across several dimensions and discusses trade-offs relevant to the Q3 platform decision."
>
> After: "Recommend Vendor B for the Q3 platform move: it is the only option that meets the 99.9% uptime requirement, at a 12% higher run cost than A. Confidence: medium. Uptime comes from a signed contract term, not a measured record; a two-week pilot would raise it to high. Decision needed by 14 March to hold the migration window."

Bare number repaired:

> Before: "Churn improved by 30%."
>
> After: "Monthly churn fell from 4.0% to 2.8% (Jan to Jun, paid accounts, billing data). That is the first period below the 3.5% plan; two of the six months followed the pricing change, so the effect of the change alone is not isolated."

Mismatched windows (invented figures for illustration only):

> Before: "Vendor A scored 94 and Vendor B scored 88, so A is the better choice."
>
> After: "A and B were measured over different windows, so the 94 and 88 are not comparable and this memo does not rank them on performance. Retest both over the same two weeks; until then, decide on price and support terms, which were measured alike."

## Reference files

| File | Load when |
|------|-----------|
| [report types](references/report-types.md) | Choosing the spine, density, voice, and traps for a specific report type |
| [comparisons and recommendations](references/comparisons-and-recommendations.md) | Any comparison, scoring, market numbers, options, or recommendation |
| [tables and figures](references/tables-and-figures.md) | Choosing, building, captioning, or auditing tables and charts |
| [decision memo template](assets/decision-memo-template.md) | Drafting a decision memo or decision record from scratch |
| [research report template](assets/research-report-template.md) | Drafting a research, market, or competitive report from scratch |
| [eval.md](eval.md) | Self-check before returning any output |
