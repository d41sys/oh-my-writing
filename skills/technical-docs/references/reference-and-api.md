Load when: writing API, CLI, configuration, script or library reference; generating or updating docs from source files; reviewing code comments and docstrings; applying markdown, table, code-fence or diagram conventions.

# Reference, API and markdown conventions

## Contents

- Principles for reference pages
- Build from source of truth
- HTTP API entry
- CLI, script and config reference
- Markdown conventions
- Diagrams
- Pre-delivery checks for reference work
- Reviewing code comments and docstrings

## Principles for reference pages

- The reader scans mid-task. Put the fact first, in the same place in every entry.
- Short sentences, active voice, no ambiguity. When clarity, completeness and elegance conflict, choose in that order.
- Describe; do not teach, sell or defend. Link to a how-to or explanation instead.
- State constraints as rules: "Required. Cannot be combined with `--stdin`."
- Lists for enumerations ("Sub-commands: `init`, `build`, `serve`"); tables for fields.
- One default, plus a narrow escape hatch, instead of a menu of equal options.
- Give every numeric value a reason or a source (a default of 30 seconds says why, or links to where).
- Avoid wording tied to a date ("before March 2025 ..."). Describe the current method; put legacy behaviour in a collapsed "Older versions" block.
- Specific beats hedged. "Often" and "sometimes" belong in reference only when the real behaviour is conditional; then state the condition.
- Reference quality is several checks: accuracy, completeness, consistency, usefulness, precision. A page can be accurate and incomplete, or complete and wrong. Check each.

## Build from source of truth

1. Extract facts from code, not recall: package scripts for the command list, example env files for environment variables, route definitions or an OpenAPI file for endpoints, exports for the public API, container files for infrastructure.
2. Take versions from package or lock files.
3. Copy response shapes from types or schemas, or from a real response.
4. Generate what can be generated. Wrap generated sections in markers (for example `<!-- AUTO-GENERATED -->` and `<!-- /AUTO-GENERATED -->`), update only inside them, and preserve hand-written prose around them.
5. When updating an existing page: read it, compare it with the current code, show the user what differs, apply updates while keeping hand-written notes. Never silently overwrite custom content.
6. Validate: files and paths exist, links resolve, examples run, snippets compile. Add or change an example only when it can be validated; otherwise leave it out of the page and list it as `[UNTESTED]` in the reply.
7. Document what exists. Do not list planned endpoints or undocumented tables as if finished. A doubtful entry is left out of the page, or the page says what the source does not show; the `[VERIFY: ...]` line goes in the reply.
8. After a pass, report per page in the reply (an author-facing report, so markers may appear there): Updated (what changed), Flagged (why, how stale), or Skipped (why).

## HTTP API entry

Order the page: Base URLs (production, development), Authentication (method: bearer token, session cookie, API key or none; where the credential goes), then endpoints grouped by resource. For each endpoint use the same layout:

1. **Heading**: method and path, for example `POST /v1/documents/convert`.
2. **Summary**: one neutral sentence stating the operation.
3. **Auth**: required scope or "none".
4. **Request**: table of fields.

   | Field | Type | Required | Description |
   |---|---|---|---|
   | `format` | string | yes | Target format. One of `pdf`, `html`. |
   | `timeout` | integer | no | Seconds. Default 30. Range 1 to 120. |

5. **Example request**: a complete, runnable call with realistic values and the headers it needs.
6. **Response**: success status and an exact payload, plus a field table when fields are non-obvious.
7. **Errors**: a table of each status code the endpoint can return and its trigger.

   | Status | Meaning | Typical cause |
   |---|---|---|
   | 401 | Unauthorized | Missing or expired token |
   | 422 | Unprocessable | `format` not in the allowed set |

Request and response schemas must agree exactly with the implementation, and every listed error code needs a meaning. Never print examples that cannot run or that leave out required authentication.

If a task needs several endpoints in sequence, write a how-to and link to each entry.

## CLI, script and config reference

CLI or script entry:

1. Name and one-line description.
2. **Usage**: syntax line(s) in a `text` fence.
3. **Arguments and options**: table with name, type, default, description. Put options shared by every command in one table at the top instead of repeating them. List only what the parser defines: read the argument-parser code or run `--help`, and never add a flag that sounds natural. Mark which options are required, and give the short form beside the long form.
4. **Examples**: basic, with options, verbose; each with a short comment and a sample output block. Run them; an example that was not run is left out of the page and listed as `[UNTESTED]` in the reply.
5. **Streams and side effects**: what is read from files or standard input, what goes to standard output and what to standard error, which files are created, appended to or overwritten, and what is the default when an output option is omitted. When the code opens the output file before it reads the input, say that pointing the output at the input file destroys the input.
6. **Exit codes**: state each code the code returns together with what causes it ("exit code 0 on success; exit code 1 if the input file cannot be opened"), and say which failures are not turned into a code (a traceback instead). A reader scripting the tool needs the cause beside the number.
7. **Errors**: the message format, with an example, if it is machine-readable.

Configuration reference: group keys as the config file groups them; for each key give type, default, allowed values or range, effect, and the version it appeared in if relevant. Mark deprecated keys. Mark which keys are required. For tuning parameters and heuristics, say what the value controls, the bounds in which it is safe, and where the number came from when the source shows it. When the reason for a default is not in the source, leave the reason out of the page rather than inventing one, and ask `[ASK AUTHOR: why this default?]` in the reply.

Library reference: mirror the public module layout; for each public symbol give signature, parameters, return value, errors raised, one short example.

## Markdown conventions

This section is the single owner of Markdown conventions for the writing skills; other skills point here and add only their own genre rules.

- **Headings**: exactly one H1; no skipped levels; sentence case unless a proper noun; descriptive ("Authentication flow", not "Details"). One idea per heading. Avoid H5 and deeper; restructure.
- **Emphasis**: bold for key terms and real emphasis, sparingly (about two or three terms per paragraph at most); never whole sentences; do not stack bold and italic on one span. Inline code for commands, file names, config values, environment variables. Strikethrough only marks deprecated content.
- **Lists**: numbered only for ordered steps; checkboxes only when tracking completion; parallel grammar within a list; at most two levels of nesting; items short (promote paragraph-length items to subsections). End items with a period only if they are full sentences. Lead into a step list with a short sentence.
- **Code fences**: always a language tag (`bash`, `json`, `python`, `text` for plain output). Keep each snippet focused on one point. Show the expected output in a separate `text` fence.
- **Tables**: a header row; about five columns at most; short cells; left-align text, right-align numbers. Use tables for reference data and comparisons, not narrative.
- **Links and citations**: meaningful text, never "click here". Relative paths inside the repo, full `https://` URLs outside. When a URL repeats, use reference-style links. Test every link before delivery. For an outside claim (a benchmark, a limit, a version's behaviour), link or footnote the source with its full URL; an absolute such as "supports every diagram type" needs a source that names the renderer and version, otherwise soften it or mark `[VERIFY: ...]`. Never invent a reference.
- **Callouts**: one to three lines in a blockquote with a bold label (`> **Warning:** ...`). Do not nest them.
- **Images**: next to the text they illustrate, with descriptive alt text and an italic caption (*Figure N: ...*); relative paths. Take screenshots from the running product, not mock-ups.
- **Collapsible detail**: `<details>` with a descriptive `<summary>` and a blank line after it so markdown inside renders. Use it for verbose logs, alternatives and optional deep dives, not to hide required steps.
- **Whitespace**: blank lines around headings, code fences, tables and blockquotes; tight list items; no trailing spaces; horizontal rules only after title metadata or before a references block.
- **Emoji**: none in technical docs by default. Exception: a changelog may use them as category markers if the project already does. Never in the H1, code, link text or table cells.
- **Accessibility**: alt text on every image, no colour-only meaning, contrast checked in light and dark themes when you set colours.
- **Freshness**: add a last-updated line only if someone will maintain it.
- **Polish pass**: spelling, parallel list grammar, no trailing spaces, no double blank runs; spot-check rendering in a light and a dark theme.

## Diagrams

Use a diagram when structure beats prose: flows, sequences, lifecycles, data models, architectures. Use a screenshot or photo for a real interface.

| Content | Diagram type |
|---|---|
| Process with decisions | flowchart |
| Who calls whom, in time order | sequence diagram |
| Lifecycle of one object | state diagram |
| Data model | entity-relationship |
| Schedule or roadmap | timeline or Gantt |
| Classes or modules | class diagram |
| System context and containers | architecture or C4 style |

Guidelines:

- Choose the most specific type; do not default to a flowchart.
- Keep it small: about ten nodes flat; group by subgraph up to about twenty; beyond about thirty, split into an overview plus detail diagrams.
- One main flow direction. Short active labels (three to six words). Semantic identifiers (`run_lint`, not `A`).
- Meaning must survive without colour: shape and label first.
- Add an accessible title and a one- or two-sentence description where the renderer supports it; otherwise add a visible text description under the figure.
- For a before/after pair, draw both with the same layout and direction.
- Check the renderer on the real destination (probe its version if the host allows). Some hosts and terminals show raw source; if so, keep a rendered image with a text description alongside the source, and keep both together.
- Use host theme defaults and reusable classes, not inline init directives; never loosen a renderer's security setting just to make a diagram draw.
- Name the same entity the same way in every diagram of a set, keep related diagrams in neighbouring sections, and write one bridging sentence that names nodes shared between them. Place each diagram next to the prose it illustrates.
- Sequence diagrams: about four or five participants; solid arrows for requests, dashed for responses; use the alternative, parallel and loop blocks for branches. Plain `sequenceDiagram` beats plugin-only syntax.
- Label example or protocol sketches as illustrative, not complete implementations.

## Pre-delivery checks for reference work

1. Every path, flag, field and status code appears in the source.
2. Every example was run, or is left out of the page and listed as `[UNTESTED]` in the reply. The page body holds no markers.
3. Versions are stated and come from files.
4. Layout is identical across entries of the same kind.
5. No instruction, selling or design argument inside a reference entry; links instead.
6. Generated sections are marked; hand-written text is intact.

## Reviewing code comments and docstrings

When asked to review comments or docstrings (not to write docs), check each against the code and report advisory groups:

- **Inaccurate**: the comment contradicts the code, or a parameter or return description is wrong.
- **Stale**: it refers to removed behaviour, renamed things or old versions.
- **Incomplete**: complex logic, side effects, edge cases or public API contracts are not explained.
- **Low-value**: it restates the code, will rot quickly, or is a TODO or FIXME with no owner. Suggest deleting it, not rewording it.

Fix only what the user asked to fix, and quote the line for each finding. A comment review is an author-facing findings list: markers and notes to the author may stay in it. A comment or docstring you write or rewrite is reader-facing: no markers, no TODO.
