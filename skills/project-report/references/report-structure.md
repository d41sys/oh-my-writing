# Report structure and register

## Spine

The standard shape of a project report. Use the sections the documents support; cut the rest and say so in the reply.

| # | Section | What it holds | Source in the folder |
|---|---|---|---|
| 1 | Executive summary | The three to five things the reader must know, the overall status in one sentence, and any decision needed (what, who decides, by when) | everything, written last |
| 2 | Objectives and scope | What the project set out to do, what is in and out of scope, the baseline date | charter, plan, kickoff notes |
| 3 | Progress against plan | Planned vs actual for the period: milestones, deliverables, percent complete with how it is measured | plan, status emails, meeting notes |
| 4 | Results and metrics | Measured outcomes, budget and effort vs plan; each figure with unit, date and source | spreadsheets, reports |
| 5 | Timeline | Dates achieved, dates ahead, dates that moved and why (only if a document says why) | plan, meeting notes |
| 6 | Risks and issues | Each item with description, impact, owner, mitigation, status; open risks first | risk log, notes, emails |
| 7 | Decisions needed | Question, options in the documents, who decides, deadline | notes, emails |
| 8 | Next steps | Action, owner, date; each from a document or marked as missing | notes, plan |
| 9 | Appendix: sources | Every document used (path, as-of date), documents not read and why, conflicts not resolved | inventory, ledger |

Scale:

| Folder | Report |
|---|---|
| a few short documents | one page: summary, status, risks, next steps; sources as a list |
| a typical project folder (5-30 files) | the full spine, two to five diagrams |
| a large or final-report folder | the full spine, a results section by workstream, an appendix per major source set |

A status report looks forward (progress, risks, next steps). A final or closing report looks back (objectives met, results, lessons, outstanding items); swap the weight of sections 3, 4 and 8 accordingly and add a short "outstanding items and handover" section. For decision memos, post-mortems and research reports use `report-writing`.

## Executive summary

- First sentence: the overall state in plain words and the most important fact behind it ("Delivery is two weeks behind the 30 June plan; spend is within budget.").
- Then three to five findings, each carrying its number, date and source.
- Then the decision needed, if any: what, who, by when. If the documents name no decider or date, write the marker.
- No scene-setting, no restating the title, no "this report provides an overview".
- Draft it last, from the finished sections. Every number in it must appear in a later section.

## Professional register

Define the tone as properties you can check, not as a mood:

| Property | Means | Check |
|---|---|---|
| Plain | common words, short sentences, one idea each; define a term once | no sentence over about 30 words without a reason |
| Specific | names, dates, amounts, units, counts instead of "significant", "soon", "some" | each adjective of degree is replaced by a figure or deleted |
| Active | who does what, by when | the owner is the grammatical subject of an action item |
| No hype | no "exciting", "robust", "seamless", "world-class", no exclamation marks | scan finds none |
| Numbers | unit, period and source: "$48,200 spent by 30 June (budget.csv)", not "about 48k" | every number has a unit and an as-of date |
| Owners | each risk, issue, decision and action has a named person or role, or a marker | no unowned action |
| Calibrated | observed, reported, estimated and planned are kept apart | "reported by Dana" vs "measured"; "planned" never reads as done |
| Neutral on problems | state the problem, its impact and the owner; no blame, no softening | "Integration testing started 9 days late" not "faced some minor delays" |

Before and after, same facts:

> Before: "We are thrilled to report that the project is progressing really well and is on track to deliver exciting results soon, with some minor delays in testing."

> After: "Build is 70% complete against a plan of 80% at 30 June (plan.xlsx, status email 1 July). Integration testing started nine days late because the test environment was unavailable (meeting notes, 24 June). The 15 August launch date is unchanged. Risk to that date: [ASK AUTHOR: is the nine-day slip absorbed in the schedule?]"

What changed: the claim carries a figure, a date and a source; the cause is stated because a document states it; the unknown is a marker rather than reassurance.

## Tables

Use a table for any set of items with the same fields (milestones, risks, budget lines, actions). Header row, one fact per cell, units in the header, numbers right-aligned (the build script aligns numeric columns), no empty decorative columns. Put the source file in a column or below the table.

## Language other than English

Structure, ledger and checks carry over. Write the register by the target language's own norms of formal business writing; do not translate English idiom. Keep names, dates and figures exactly as in the documents.
