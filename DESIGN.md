---
name: Oh My Writing
description: An editor's proof sheet for eleven writing skills; ink rules, newsprint, condensed type, one green mark.
colors:
  newsprint: "oklch(97% 0.007 86)"
  newsprint-shade: "oklch(94% 0.010 86)"
  newsprint-deep: "oklch(91% 0.012 84)"
  ink: "oklch(16% 0.012 280)"
  ink-soft: "oklch(29% 0.011 280)"
  margin-gray: "oklch(48% 0.010 75)"
  hairline: "oklch(85% 0.009 85)"
  hairline-strong: "oklch(64% 0.010 80)"
  proof-green: "oklch(49% 0.130 152)"
  proof-green-ink: "oklch(98% 0.005 88)"
  focus-green: "oklch(52% 0.135 152)"
typography:
  display:
    fontFamily: "Bricolage Grotesque, ui-sans-serif, sans-serif"
    fontSize: "clamp(3.5rem, 7.2vw, 6rem)"
    fontWeight: 800
    lineHeight: 0.98
    letterSpacing: "-0.012em"
    fontVariation: "'wdth' 75"
  headline:
    fontFamily: "Bricolage Grotesque, ui-sans-serif, sans-serif"
    fontSize: "clamp(2rem, 2.5vw + 1rem, 3.5rem)"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.012em"
    fontVariation: "'wdth' 75"
  title:
    fontFamily: "Bricolage Grotesque, ui-sans-serif, sans-serif"
    fontSize: "clamp(1.25rem, 0.75vw + 0.875rem, 1.625rem)"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.012em"
    fontVariation: "'wdth' 75"
  body:
    fontFamily: "Source Serif 4, ui-serif, Georgia, serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.55
  ui:
    fontFamily: "Bricolage Grotesque, ui-sans-serif, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.55
    fontVariation: "'opsz' 12"
  label:
    fontFamily: "Bricolage Grotesque, ui-sans-serif, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.55
    fontVariation: "'opsz' 12"
  code:
    fontFamily: "ui-monospace, Menlo, Consolas, monospace"
    fontSize: "0.875rem"
    lineHeight: 1.55
rounded:
  none: "0"
spacing:
  3xs: "2px"
  2xs: "4px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  2xl: "64px"
  3xl: "96px"
  4xl: "144px"
components:
  button-copy:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.newsprint}"
    typography: "{typography.ui}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
    height: "48px"
  button-copy-hover:
    backgroundColor: "{colors.proof-green}"
    textColor: "{colors.proof-green-ink}"
  button-copy-on-band:
    backgroundColor: "{colors.newsprint}"
    textColor: "{colors.ink}"
  button-copy-on-band-hover:
    backgroundColor: "{colors.newsprint-deep}"
    textColor: "{colors.ink}"
  proof-sheet:
    backgroundColor: "{colors.newsprint-shade}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "64px"
  output-panel:
    backgroundColor: "{colors.newsprint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "24px"
  disclosure-summary:
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    padding: "24px 8px"
  disclosure-summary-hover:
    textColor: "{colors.proof-green}"
  skill-block:
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "24px 0 64px"
  compare-table:
    backgroundColor: "{colors.newsprint-shade}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "12px 24px 12px 0"
  install-band:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.newsprint}"
---

# Design System: Oh My Writing

## Overview

**Creative North Star: "The Editor's Proof Sheet"**

A single-page site that behaves like a marked-up galley. Newsprint ground, ink rules, condensed lettering, and one green editorial mark. The reader judges a writing skill by reading the before and after sentences, so the page gives text room and refuses the feature-card grid. Each skill is its own ruled block with its assignments in disclosures; the reader picks the piece instead of waiting for a carousel. A comparison table then sets all eleven side by side.

Density is open and restrained. Everything is flat and square: no shadows, no radius, no imagery. Hierarchy comes from heavy condensed display type, a 4px ink rule under the masthead, hairlines between entries, and one tonal step of paper. Green is the proofreader's pen: it marks the deletion, the improved line label, hover, and focus.

**Key Characteristics:**
- Flat, square, shadowless; depth by paper tone and rules only.
- Condensed heavy sans for voice, serif for reading.
- Real deleted text (`<del>`) in the first viewport is the signature.
- Eleven ruled skill blocks and one comparison table carry the page; no cards.
- One accent, green, used for marks and state.
- Ink band inverts the page once, at install.

## Colors

Warm newsprint and near-black ink with a single deep proofreader green. Neutrals are tinted toward yellow (hue 75–86); ink toward violet (hue 280).

### Primary
- **Proof Green** (`colors.proof-green`): deletion strike-through, "after" label, summary markers, link and button hover, caret.
- **Proof Green Ink** (`colors.proof-green-ink`): text on a Proof Green fill.
- **Focus Green** (`colors.focus-green`): 2px focus outline, offset 2px.

### Neutral
- **Newsprint** (`colors.newsprint`): page ground and the output panel.
- **Newsprint Shade** (`colors.newsprint-shade`): the hero proof sheet, input panels, and the comparison section.
- **Newsprint Deep** (`colors.newsprint-deep`): image-slot gradient end and hover fill on the band button.
- **Ink** (`colors.ink`): text, heavy rules, copy button fill, install band.
- **Ink Soft** (`colors.ink-soft`): the struck "before" sentence in the hero proof.
- **Margin Gray** (`colors.margin-gray`): captions, notes, scrollbar.
- **Hairline** (`colors.hairline`): defined; not used by the shipped page.
- **Hairline Strong** (`colors.hairline-strong`): disclosure borders, the rule above "after", table row dividers.

### Named Rules
**The One Pen Rule.** Green marks an edit or a state, never a surface. No green backgrounds except the hover fill of the copy button.

**The Struck Text Rule.** Deletions are real `<del>` text with a green line (0.12em), never an image or a decorative stroke.

## Typography

**Display Font:** Bricolage Grotesque (ui-sans-serif, sans-serif), width axis 75, weight 800
**Body Font:** Source Serif 4 (ui-serif, Georgia, serif), regular and italic
**Code Font:** system monospace

**Character:** A narrow, heavy newspaper-masthead voice over a calm text serif. Display runs tight (letter-spacing -0.012em; brand mark -0.04em).

### Hierarchy
- **Display** (800, clamp 3.5rem to 6rem, 0.98): hero H1 only ("How your agent edits"), capped at 12ch.
- **Headline** (800, clamp 2rem to 3.5rem, 1.05): section H2s, max 30ch.
- **Title** (800, clamp 1.25rem to 1.625rem, 1.2): brand, skill names (H3), disclosure summaries.
- **Lead** (400, clamp 1.125rem to 1.375rem, 1.45): hero and section intros, 44ch in hero, 52ch elsewhere.
- **Body** (400, 1.125rem, 1.55): paragraphs capped at 65ch; ask text at 72ch.
- **After sentence** (400, clamp 1.5rem to 2.3rem, 1.2): the revised line at reading-display size.
- **UI** (500, 1rem, optical size 12): nav links, skill jump links and copy buttons.
- **Label** (500, 0.875rem, optical size 12): hero proof caption and notes. Case source links and trace links stay serif.
- **Table head** (800, 1rem, 1.3): comparison column heads. Row heads (skill names) use 1.25rem, width axis 75, no wrap.

### Named Rules
**The Voice Split Rule.** Condensed sans speaks (headings, summaries, skill names); text-size sans at weight 500 and optical size 12 carries interface labels (nav, buttons, captions, notes). Serif is the material being read. Never swap.

## Layout

A 1440px container with fluid gutters (64px, 24px under 60rem, 16px under 40rem). The hero is a two-column grid (1fr / 1.12fr) under a slim masthead, filling the viewport below it (`min-height: calc(100svh - 64px)`, none under 49rem): title and command left, proof sheet right, 4px ink rules above and below. Sections are single-column with a 120px base gap (80px, 56px on smaller screens). The cases section opens with a jump nav, a wrapping row of eleven in-page skill links (24px column gap), then eleven skill blocks. Each skill block starts under a 4px ink rule and is a two-column grid (`minmax(20rem, 1fr)` / `2.4fr`): name and one-line description left, disclosures right. It stacks under 60rem. The comparison table runs full width on Newsprint Shade and restacks under 49rem into labelled blocks. The install band is two columns above 49rem. Case pairs stack under 49rem. On a phone the command precedes the proof.

Spacing scale: 2, 4, 8, 12, 16, 24, 40, 64, 96, 144px. Tap targets in nav, jump, skill-name and footer links are at least 48px high.

## Elevation & Depth

None. The system is flat and shadowless (`--shadow-card: none`). Depth is tonal: Newsprint, Newsprint Shade for sheets and sections, Ink for the band. The case output panel is separated by a 4px ink top rule.

### Named Rules
**The Flat Paper Rule.** No shadows, gradients on UI, or blurs. Separation comes from a rule or one paper step.

## Shapes

Square everywhere: `--radius-card` and `--radius-pill` are `0`. Borders are 1px hairlines (`--rule-hair`) or a 4px ink rule (`--rule-heavy`). No icons, no imagery, no clipping.

## Components

### Copy Button
- **Shape:** square, 48px minimum height, 12px 16px padding.
- **Default:** ink fill, newsprint text, UI type (Bricolage 500).
- **Hover:** green fill, green-ink text. Active: nudges down 1px (120ms, ease-out).
- **On the band:** inverted to newsprint fill with ink text; hover goes to Newsprint Deep.
- **Behavior:** hidden unless the Clipboard API exists; the command is always selectable (`user-select: all`). The confirmation line below (label size, 1.5em high) is space-reserved once the button shows, so copying causes no layout shift.

### Proof Sheet
Newsprint Shade panel, padding clamp 24px to 64px. Struck "before" sentence in Ink Soft at Title size (clamp 1.25rem to 1.625rem), then a hairline-strong rule, then the "after" sentence in display-sized serif with a green label and a Margin Gray caption.

### Case Disclosure
Native `<details name="cases">` (exclusive group); only the first case on the page is open on load. Hairline-strong top border (none on the first in a skill block), closing border on the last. Summary in Title type with a green marker, hover to green. Open content: ask paragraph, then an input/output pair. The output panel is newsprint with a 4px ink top rule; the input panel is Newsprint Shade. Cases drawn only from the usage guide have no pair: a single "You get" line (`p.gets`, 65ch) follows the request.

### Skill Jump Nav
Wrapping row of eleven in-page links in UI type (Bricolage 500, 1rem, optical size 12), 24px column gap, 48px tap height, hover to green. Sits above the skill blocks.

### Skill Block
One per skill. A 4px ink rule on top, 24px above and 64px below the content. Left: H3 skill name as a link to the skill's folder (Title type, no underline until hover, no wrap) and a one-line description in Ink Soft (max 32ch). Right: that skill's disclosures. Stacks to one column under 60rem.

### Comparison Table
Full-bleed Newsprint Shade section holding a four-column table (Skill, You ask for, You give, You get). The head row has a 4px ink rule above it; body rows are separated by Hairline Strong 1px rules. Column heads and the "label: " prefix are in the display face. Row heads are condensed display type linking to the skill block. Under 49rem the head row is hidden and each row becomes a block with labelled lines.

### Install Band
Full-bleed Ink section with newsprint text; headline and command left, host list right with Margin Gray hairline dividers.

### Navigation
Slim running masthead: brand left in Title type, text links right in UI type (Bricolage 500, 1rem), 48px tap height, hover to green. A skip link slides in on focus.

## Do's and Don'ts

### Do:
- **Do** keep every surface square and flat; use a 1px hairline or one paper step to separate.
- **Do** mark edits in Proof Green and nothing else.
- **Do** keep sentences at reading size (1.125rem and up) with measure at or under 72ch.
- **Do** let case dates, places, and requests come from the real fixture text.
- **Do** keep a 48px minimum tap target and the 2px Focus Green outline.
- **Do** respect `prefers-reduced-motion`; transitions are 120 to 420ms, ease-out.

### Don't:
- **Don't** build feature cards, icon grids, or a carousel.
- **Don't** add shadows, rounded corners, gradients on UI, or decorative imagery.
- **Don't** fake a deletion with an image or a drawn line; use `<del>`.
- **Don't** lead with benchmark scores; the two sentences are the evidence.
- **Don't** use a second accent colour or set body copy in the display face.
