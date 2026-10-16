# Diagram plan: [project name]

One brief per candidate, kept in `work/diagram-plan.md`. A brief is also the complete instruction passed to the drawing skill, so it must stand alone.

Default two to five diagrams. Drop any that a table or a sentence does better, and record the drop below.

## Diagram [n]: [slug]

- **Reader question:** [one question, for example "Which milestones are late and what do they block?"]
- **Why a diagram beats text or a table:** [one sentence: dependencies, overlap, flow, trend, or position that a table hides]
- **Report section and caption:** [section]; "[caption as it will appear]"
- **diagram-design visual type:** [Gantt / Timeline / Architecture / Data flow / Swimlane / Process / Bar / Line / Waterfall / Fishbone / Quadrant / Kanban / ...] (semantic pattern, if its guide routes to one: [name or none])
- **Size and drawn width:** [canvas near the printed text width, about 680 units (`fit`); or `doc-inline` 960 when the type needs the width (prints at about 70%); `doc-wide` only if the schedule cannot be split]
- **Audience:** [`executive` / `mixed` / `engineer`]
- **Variant and style:** minimal light; style [default / marker / profile name]; fonts [web / system]
- **Focal elements (at most two):** [the late milestone, the over-budget line]
- **Ledger facts it may show** (nothing else; labels and numbers copied exactly):

  | Label on the diagram | Value | Ledger ID | Source |
  |----------------------|-------|-----------|--------|
  | [text] | [number or date with unit] | [F07] | [file, location] |

- **Must not show:** [conflicting figures unresolved (F05/F09), unconfirmed items shown as confirmed, invented dependencies]
- **Status shown visually:** [planned vs done vs at risk, if the type has a way to show it]
- **File:** `diagrams/[slug].html`
- **Self-check run and result:** [pass / what was fixed]
- **Text and figure agree:** [yes: checked D01 against section 4 / no: what differs]

## Dropped candidates

| Candidate | Reason dropped |
|-----------|----------------|
| [for example budget bar chart] | [four lines; the table in section 4 reads faster] |

## Run notes

- Style gate: [asked and answered / default used because non-interactive / marker used]
- diagram-design found at: [skill list / path / not installed, so Mermaid blocks used]
- Assumptions to tell the author: [list]
