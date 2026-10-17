# Diagram selection and hand-off to diagram-design

Diagrams in a report exist to answer a reader's question faster than prose. The drawing itself is done by the separate `diagram-design` skill (MIT, by its own author). This file covers only what this skill owns: whether to draw, which type to ask for, what to hand over, and what to do when it is not installed.

## Should this be a diagram?

Ask in order. Stop at the first "no".

1. Which reader question does it answer? Write it as a question ("Which milestones are late, and what do they block?"). No question, no diagram.
2. Would one sentence or a table answer it as well? Four budget lines, a list of owners, a before/after of attributes: table. A schedule with dependencies, a flow with handoffs, a spread of values over time: diagram.
3. Are the facts in the ledger, with sources? A diagram cannot contain anything the text could not cite.
4. Does it fit the budget of the type (about nine nodes, twelve connectors, two accent elements for most types)? If not, split into overview plus detail, or cut.

Default: two to five diagrams per report. One per major section at most. Decorative diagrams (logos, abstract flows with no data, a "methodology" picture) are out.

## Report question to diagram-design type

| Reader question | Type to ask for | Typical ledger facts |
|---|---|---|
| What is the schedule, what is late, what overlaps? | Gantt (tasks and phases on a timeline), or Timeline for a handful of dated events | task, start, end, status, owner |
| What happened when? | Timeline | dated events with status |
| How is the system built, and what connects to what? | Architecture (one snapshot) or Data flow (role-scoped steps) | components, connections, owners |
| What changed in the design between two states? | Architecture delta | before and after components |
| How does work move between teams? | Swimlane (handoffs) or Process (multi-actor with data) | steps, actors, handoffs |
| What are the decision rules? | Flowchart | conditions, outcomes |
| How did a measure move or compare? | Bar chart (categories), Line chart (time), Waterfall (a start total bridged to an end total, such as a budget bridge) | the series with units and dates |
| Where did the money or effort go? | Sankey (flow splits), Treemap (parts of a whole), Waterfall (variance) | amounts that sum, from the ledger |
| Why did something go wrong? | Fishbone (causes by category, only when documents list causes) | stated causes |
| Which risks matter most? | Quadrant (two axes, such as likelihood and impact) or Heatmap | each risk with the two ratings the documents give |
| What is in progress, blocked or waiting? | Kanban | items with state |
| Who owns what? | Org chart | roles and reporting lines |
| What depends on what? | Dependency graph | items and dependencies |
| How are layers or tiers arranged? | Layer stack | layers and contents |

Choose by the dominant reader question, not by decoration. If the table lists a type for a question only loosely, check the `diagram-design` type guide (its SKILL.md visual-type table and the `references/type-*.md` file) before committing.

Risk quadrants and heatmaps need a rating scale from the documents. If the documents give no likelihood or impact, do not invent one: use a table of risks with owners instead.

## The brief you hand over

One brief per diagram, from [the diagram brief template](../assets/diagram-brief-template.md). The brief is the full instruction; `diagram-design` does not see the report.

- Visual type (and the pattern, if its pattern table routes there).
- Size: draw at the width the page prints, so labels are not shrunk. The text column of a printed page is about 673 CSS px on A4 (695 on Letter), and the builder never enlarges a diagram past its drawn width. `doc-inline` (960x600) prints at about 70%, so its 12-unit node names print near 6 pt and its 8-unit arrow labels near 4 pt; `doc-wide` (1280x720) prints at about half. Prefer a canvas near 680 units wide (`fit`, content laid out to about 600 units) for flows and architectures of up to about eight nodes; keep `doc-inline` for a schedule or a chart that needs the width, with short labels and few nodes, and never `doc-wide` unless the schedule cannot be split. State the width in the brief. Do not use presentation or social presets. The build prints a note when a figure will print below 75% scale.
- Audience: `executive` for a steering report, `mixed` by default, `engineer` for an architecture appendix. It changes wording, not node count.
- Variant: minimal light (default), because the report page is light.
- Exact labels and values, copied from the ledger, with units and dates. Tell it not to add nodes, values or arrows.
- Which one or two elements are the focal point (the late milestone, the over-budget line), because the type spends its accent colour on those.
- Slug and output path: `diagrams/<slug>.html`. Lower-case words and hyphens.
- No motion. Static only.

## Style gate and non-interactive runs

`diagram-design` checks, before the first diagram in a project, whether its style guide is still the shipped default and asks how to style it. Follow it:

- Interactive: let it ask, once. Reuse the answer for every diagram in the report.
- Non-interactive, or the author said "just do it": use a project `.diagram-design` marker if one resolves; otherwise keep the default style. Say in the reply which was used, and that the author can restyle by naming a brand or a profile.
- Every diagram in one report uses the same style. Do not mix variants.
- It also asks you to state the plan (type, size, cuts) before drawing. When the author is reachable, show the whole diagram plan once for all diagrams, not one by one. When not, proceed and note the assumptions.

For offline or locked-down delivery ask for its system-font option. The report build can also drop the web font link with `--fonts system`.

## After drawing

1. Run its `scripts/self_check.py <file>` on each diagram (accessible SVG contract, single-file safety, content inside the viewBox). Fix what it reports in the diagram, not in the report.
2. Open each file once if a browser is available.
3. Compare every label and number to the ledger and the report text. `build_report.py --ledger work/ledger.md` lists numbers inside diagram labels that the ledger does not contain; it cannot judge dates written as words or names, so read those.
4. Keep the diagram's own `<title>` and `<desc>`: the report uses them as the accessible name, and the portable `report.md` prints the `<desc>` under the figure as its text description. Check that the `<desc>` says what the figure shows in a sentence or two, with the dates and figures drawn (the ledger's, no others), so a reader of the plain text gets the same answer the picture gives.

## Fallback when diagram-design is not installed

Check, in order: the list of available skills, `~/.agents/skills/diagram-design`, `~/.claude/skills/diagram-design`. If none:

1. Put one Mermaid block per planned diagram in the report source, at the place the figure belongs, with caption, source and slug in the fence line. See [assembly](assembly.md#mermaid-fallback). The portable `report.md` keeps the block fenced, so Markdown viewers that render Mermaid draw it and everyone else reads it as text.
2. Choose the Mermaid type that matches the plan: `gantt`, `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `pie`, `quadrantChart`, `timeline`, `xychart-beta` for bars and lines. Use only ledger facts and keep node text short.
3. Tell the author in one line: "Diagrams are Mermaid source; install the `diagram-design` skill and re-run for designed diagrams."
4. `build_report.py` shows each Mermaid block as labelled source in a numbered figure. It does not render it.

Never hand-draw a replacement SVG in this skill. A weak ad-hoc diagram is worse than a clear table.
