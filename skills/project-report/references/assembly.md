# Assembly

`scripts/build_report.py` turns the report source (`work/report-source.md`) plus diagram files into one self-contained HTML file and, with `--md-out`, a portable Markdown copy that reads on its own. Standard library only; no pandoc, no JavaScript, no network needed to read the result.

```bash
python <skill-dir>/scripts/build_report.py work/report-source.md --diagrams diagrams --ledger work/ledger.md --out report.html --md-out report.md
```

Run it from the output folder. The deliverable folder holds `report.md` (the portable copy, generated), `report.html`, `diagrams/` and `open-questions.md`; the report source, inventory, extracted text, ledger and diagram plan live in `work/` beside them, so the folder a reader or author opens is not cluttered. Diagram files are looked up next to the source and in `--diagrams`, by file name; `work/` is never read except for the source and `--ledger`. Edit the source and rebuild; never edit `report.md` by hand, because the next build overwrites it.

| Option | Effect |
|---|---|
| `--diagrams DIR` | where to look for diagram files after the folder of the source |
| `--ledger FILE` | numbers in diagram labels are checked against this file (otherwise against the report text) |
| `--md-out FILE` | also write the portable Markdown copy to `FILE` (must not be the input file) and the standalone figure files beside it, in `diagrams/` |
| `--paper a4\|letter` | print page size (default A4) |
| `--fonts auto\|system` | `auto` keeps the font stylesheet link the diagrams use, so they look as drawn; `system` makes no network request and the diagrams use their fallback fonts |
| `--toc auto\|on\|off` | contents list: `auto` (default) only when the report has 6 or more top-level (`##`) sections, `on` forces it, `off` removes it |
| `--no-number` | no section numbers |
| `--allow-missing` | a missing diagram becomes a visible placeholder marker instead of an error |
| `--strict` | exit 1 when any warning remains (use it for the last build) |
| `--json` | machine-readable summary |

Exit codes: 0 built, 1 `--strict` with warnings, 2 bad input (missing file or diagram).

## Source format

A Markdown subset. Front matter is optional:

```markdown
---
title: Atlas project report, Q2 2026
type: Project status report
subtitle: Progress to 30 June 2026
project: Atlas
prepared_for: Steering committee
prepared_by: Project office
period: 1 April to 30 June 2026
date: 2026-07-01
status: Draft for review
lang: en
---
```

Without a `title`, the first `# ` heading becomes the title; a `# ` heading that repeats the title is dropped (the title block already shows it). Headings `##` and `###` are numbered (`1`, `1.1`); a heading starting with "Appendix" is not numbered, and everything from the first appendix heading to the end is set in a compact smaller type. Put appendices last. The contents list shows `##` and `###` headings, and only when the report has 6 or more `##` sections (see `--toc`). Also supported: paragraphs, nested bullet and numbered lists, pipe tables (a column whose cells are all numeric is right-aligned; `:--`, `:-:`, `--:` set alignment), block quotes, fenced code, horizontal rules, `**bold**`, `*italic*`, `` `code` ``, links and bare URLs. HTML comments are dropped. Raw HTML is escaped, not passed through. A block quote that starts with a bold **Key points**, **Decision needed**, **Bottom line** or **Recommendation** lead-in is styled as a callout; so is one that starts with **Overall assessment**, **Assessment** or **Outcome**. A paragraph that starts with `Source:` or `Sources:` is styled as a small source line: put one under each table.

Markers `[ASK AUTHOR: ...]`, `[VERIFY: ...]` and `[UNTESTED]` are highlighted so a gap cannot be missed in print. The build counts them and warns. A reader-facing report has none (gaps are written as plain statements and the questions go to `open-questions.md`); the highlighting is for drafts the author asked to edit, so the warning there is expected and the reply gives the count.

## Figures

On a line of its own:

```markdown
![Delivery plan, 12 weeks](diagrams/delivery-gantt.html "Source: plan.xlsx, sheet Schedule; status email, 1 July")
```

- Alt text is the caption. Quoted text after the target is the source line; without one the build warns, because a figure without a source cannot be checked.
- Targets: diagram-design HTML, a standalone `.svg`, or `.png`, `.jpg`, `.gif`, `.webp` (embedded as a data URI). Resolved next to the source, then in `--diagrams` (by file name).
- Figures are numbered in order of appearance. Refer to one in the text with `[[fig:delivery-gantt]]` (the file name without extension); it becomes a link reading "Figure N". Use that instead of typing the number. Writing `Figure [[fig:x]]`, `figure [[fig:x]]` or `Fig. [[fig:x]]` is fine too: the typed word is absorbed and the result reads "Figure N" once.
- Refer to every figure in the text before it appears and say what to look at.

### Mermaid fallback

````markdown
```mermaid caption="Delivery plan" source="plan.xlsx, sheet Schedule" id="delivery-plan"
gantt
  title Delivery plan
  ...
```
````

The block is shown as labelled source inside a numbered figure (it is not rendered, because rendering needs script). `id` is the slug for cross-references.

## Portable Markdown

The source holds front matter, `[[fig:slug]]` tokens and figure lines that point at diagram HTML. None of that reads in a Markdown viewer, in a diff, or when the reader opens `report.md` as text. `--md-out report.md` therefore writes a second copy that stands alone:

- the front matter becomes `# Title`, the subtitle in italics and one line of meta (type, prepared for, period, date);
- `[[fig:x]]` and the typed "Figure" before it become "Figure N";
- each drawn diagram becomes an image link to a standalone `.svg` in `diagrams/` (named after the slug) plus a caption line holding the caption, the diagram's own `<desc>` text and the source line. The `.svg` carries its scoped CSS inside the file and sits next to the `.html` the diagram skill produced, so any viewer can show it, and the `<desc>` sentence tells a reader of the plain text what the figure shows;
- a Mermaid block stays a fenced `mermaid` block with a caption line; a `.png` or similar image is copied into `diagrams/`;
- HTML comments are dropped; fenced code is untouched.

The caption line under the image reads, for example:

```markdown
*Figure 1.* Delivery plan, 12 weeks. Build runs 6 April to 10 July; testing follows from 13 July. Source: plan.xlsx, sheet Schedule; status email, 1 July
```

The portable copy is the deliverable the author named (`report.md`); the HTML is the one to print.

## How a diagram is embedded

The goal is that a diagram looks the same as it does in its own HTML file, and that several diagrams on one page do not interfere.

1. **Extract** the first top-level `<svg>` of the diagram page (comments, scripts and style content are ignored when locating it, and nested icon SVGs stay inside).
2. **Carry the page CSS.** Diagram pages style class-based shapes in the page `<style>`. The build copies those rules into the report, scoped to the figure's root (`#f2-root .zone { ... }`), re-scopes `:root` tokens onto the figure, carries the page `color`, `font-family` and `background`, and drops page chrome (`body`, headings, cards, header, footer, motion controls and similar). `@media` blocks are scoped the same way and dropped if nothing is left. `@keyframes` is dropped (motion is not carried); `@import` font lines become the report's font link.
3. **Prefix every id** with the figure number (`f2-`), and rewrite `url(#...)`, `href="#..."`, `aria-labelledby`, and `#id` selectors in CSS. Two diagrams that both define `dots` or `arrow` markers keep their own.
4. **Sanitise.** `<script>`, `<foreignObject>`, `<iframe>`, `<object>`, `<embed>`, `on*` handlers and `javascript:` links are removed. A warning appears if the diagram references an external URL.
5. **Size.** `width` and `height` attributes are removed so the figure scales with the page; the `viewBox` stays. The drawn width (`viewBox`) is kept as the figure's maximum width: a narrow diagram is shown at its drawn size, centred, not stretched to the page and then shrunk again in print. On screen a figure that is wider than 640 px never shrinks below 640 px (it scrolls sideways on a phone); in print it scales down to the text width, about 673 px on A4 and 695 px on Letter. A diagram drawn 960 units wide therefore prints at about 70%, and its 12-unit labels at about 6 pt. The build reports `print_scale` per figure in the JSON summary and prints a `note:` (not a warning) when it is below 75%. Draw diagrams near the printed text width ([diagram selection](diagram-selection.md#the-brief-you-hand-over)) or keep their labels few and large.
6. **Fonts.** Diagram pages load their fonts from a web stylesheet. With `--fonts auto` that link goes in the report head and the diagram looks as drawn when online; offline, or with `--fonts system`, each diagram falls back to the system font in its own font stack. This is the only possible external request, and the report body itself uses system fonts.
7. **Accessibility.** The diagram's `<title>` and `<desc>` stay as the accessible name (a root `role="img"` is added if absent), so the figure caption supplements them, not replaces them.

A different route exists inside `diagram-design`: its own export helper produces a standalone SVG with the same scoping and id prefixing. Such an `.svg` can be used as a target here; its ids are prefixed again, which is harmless.

## Print

The CSS sets `@page` to A4 or Letter with margins, a running footer (report title and page number), keeps figures, callouts and table rows whole, keeps a heading with the content after it, and lets tables of more than four rows break across pages with the header row repeated (tables of four rows or fewer stay on one page; keeping longer tables whole left half-empty pages in test builds). There is no cover page and no forced page break: the title block, the contents list (when there is one) and the first section share page 1, so a status report prints on about two to four pages. To get a PDF, open the HTML in a browser and print with background graphics enabled; or run a headless browser, for example `chrome --headless --print-to-pdf=report.pdf --no-pdf-header-footer report.html`. The footer is drawn by the page CSS, so turn the browser's own headers and footers off.

## Styling

House style lives in `assets/report.css` (colours as custom properties at the top). Edit it once for a client; the build reads it on every run. Keep the print rules at the bottom.

## Build warnings

| Warning | Fix |
|---|---|
| figure has no caption / source line | add alt text and the quoted source in the figure line |
| unresolved `[[fig:slug]]` | use the file name without extension, or the Mermaid `id` |
| number in a diagram label is not in the ledger or report | correct the diagram, or add the missing fact to the ledger with its source |
| gap markers remain | in a reader-facing report: rewrite the gap as a plain statement and move the question to `open-questions.md`. In a draft the author asked for: expected; state the count in the reply |
| `note:` figure prints at under 75% scale | redraw nearer the printed width, or cut nodes and labels; it is a note, not a warning, and does not fail `--strict` |
| diagram references an external URL | redraw without external assets |
| link with a disallowed scheme | only `http`, `https`, `mailto` and relative links are linked |
