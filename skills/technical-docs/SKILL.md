---
name: technical-docs
description: Writes and revises technical documentation by first deciding what the reader needs (learn by doing, achieve a goal, look up a fact, or understand why), then producing the matching page type. Covers tutorials, how-to guides, reference and API/CLI pages, architecture explanations, READMEs, code walkthroughs, pull request descriptions, commit messages, changelogs, release notes, migration guides and decision records (ADRs). Use when asked to "write a README", "document this API", "write a tutorial", "write a how-to guide for this tool", "explain this architecture", "walk through this code", "write the PR description", "write a commit message", "write an ADR", "write release notes", "write a changelog", "write a migration guide", or "fix our docs structure". A blog-style how-to post or a launch announcement post goes to post-writing.
license: CC-BY-SA-4.0
metadata:
  version: "1.1"
  skill-author: d41sys
---

# Technical Docs

Technical readers arrive in one of four states: they want to learn by doing, to finish a task, to look something up, or to understand why. This skill classifies the request into one of those four page types before any text is written, then builds the page to the rules of that type. It also covers the artifacts that sit around code: READMEs, code walkthroughs, pull request bodies, changelogs and migration guides.

## When to use

- A page, README, guide, API/CLI/config reference or architecture write-up must be created, restructured or reviewed.
- A code change needs a PR description, a commit message, release notes or a migration guide.
- A hard-to-reverse technical choice needs a short decision record (ADR).
- A docs set feels messy: pages try to teach, instruct, specify and justify all at once.

Not for: ML paper sections (use `academic-writing` if installed; otherwise `structured-drafting` for structure plus `evidence-grounded-writing` for claims); blog posts, essays or newsletters, including a blog-style how-to post and a launch announcement post (use `post-writing`; release notes and changelogs stay here); multi-option decision, research or market reports and blameless incident post-mortems (use `report-writing`; a single engineering decision stays here as an ADR); résumés and cover letters (use `career-documents`); tracing which claims need sources (use `evidence-grounded-writing`). For a final AI-pattern cleanup, use `anti-slop-editing` if available; otherwise apply the checks in [eval.md](eval.md). Clipped imperative fragments, bare parameter lists and repeated domain terms are normal in docs, changelogs and commit messages; do not "fix" them as style defects.

## Inputs

Read before writing: the code, config, schema, `--help` output or diff being documented; existing docs and their conventions (names, folders, template files); version numbers from package or lock files, not memory.

Ask at most three questions, fewer for short tasks, and only when the answer changes the page:

1. Who is the reader and what do they already know?
2. Which job is this page for: learning, finishing a task, looking up, or understanding?
3. Which version or environment does it target?

Otherwise (and always in non-interactive runs) proceed, and state assumptions at the top of your reply, not inside the page.

## Workflow

1. **Classify.** Apply the compass: is the reader doing or thinking, and are they studying or working? Pick one type from the table below. If the request spans types, plan one page per type and link them. See [doc types](references/doc-types.md).
2. **Inventory.** Check what docs already exist. Reuse and link them; do not create a page that duplicates a fact owned elsewhere. Create a new file only when something real must go in it, and follow the repo's folder and naming habits.
3. **Gather facts from source.** Read the code, run `--help`, read the diff and commit log. Never document planned or guessed behaviour. A missing fact becomes one of three markers, never an invention: `[VERIFY: ...]` (a source exists or must be found and checked: an external or checkable fact), `[ASK AUTHOR: ...]` (the author knows or decides it: intent, reasons, numbers they hold) or `[UNTESTED]` (a command or sample not run). Do not use other markers such as TBD or TODO stubs.
4. **Pick the skeleton.** Use the type's skeleton from [doc types](references/doc-types.md), the README or PR shape from [README and PR](references/readme-and-pr.md), or the entry layout from [reference and API](references/reference-and-api.md). Start from [assets/readme-template.md](assets/readme-template.md) or [assets/pr-description-template.md](assets/pr-description-template.md) where they fit.
5. **Draft to the type's contract.** Write the page for its single reader state. Move anything that belongs to another type into a link.
6. **Verify every command and sample.** Run it, or mark it `[UNTESTED]` and say what environment it needs. State versions. Check that each path, flag, link and output you cite exists.
7. **Check navigation.** Add links to the neighbouring types, not copies of their content. Update the index or map page if the set of pages changed.
8. **Self-check and return.** Run [eval.md](eval.md), fix failures, then reply with the page plus a short list of what was verified, what is marked untested, and what is still open.

### The four page types

| Reader state | Type | Contract in one line |
|---|---|---|
| Studying, doing | Tutorial | A guided path that always succeeds and builds skill through visible results. |
| Working, doing | How-to guide | Steps to reach one named goal, for someone who already has the basics. |
| Working, looking up | Reference | Neutral, complete, consistent facts shaped like the thing described. |
| Studying, thinking | Explanation | Context, reasons, alternatives and trade-offs, read away from the keyboard. |

Other artifacts map onto these: a README is a front door that links into all four; a PR body is a review aid; a commit message is a one-change record; a changelog is dated reference; a migration guide is a how-to with a before/after reference; a code walkthrough is explanation anchored to real files; an ADR is a short explanation of one decision.

## Rules

1. **One page, one type.** Mixed pages fail every reader: the learner meets choices, the worker wades through background, the person looking up a flag finds a story. Exception: a one-sentence safety reason or a pointer belongs inline in a step; a paragraph of rationale does not.
2. **Tutorials promise success and deliver it.** Pick one path, fix versions and starting files, show what the learner should see after each step, and say when silence means success. Teach by doing, not by telling. Exception: a genuinely required platform branch (for example an OS-specific install) is labeled, not removed.
3. **How-tos name a goal and trust the reader.** Title them "How to X". Skip steps any practitioner knows. Cover real variations ("if you run a replica, ...") and the likely failures. Reason: the reader's system is not your sandbox. Exception: fragile or order-dependent operations get exact commands.
4. **Reference is austere.** State what is, completely and in a fixed layout. No teaching, selling or arguing; link out. Reason: the reader is mid-task and scanning. Exception: a short example per entry is part of reference.
5. **Explanation earns its length by answering "why".** Give history, constraints, rejected alternatives and trade-offs, tied to concrete examples. Admit opinion where it is the author's real judgement. Do not slip in procedures or parameter tables.
6. **Describe the thing as it is now.** Do not narrate the edit that produced it ("this replaces the old approach"). Change history lives in the changelog, release notes, migration guide, commit message or decision record.
7. **Run it or mark it.** A sample that was never run is a claim, not a sample. Mark it `[UNTESTED]` rather than let it pass as working. Reason: docs that do not match reality are worse than none. Exception: placeholder values in a sample are fine when they are visibly marked as placeholders.
8. **State versions and environment.** Every install, command and API page names the version and platform it was checked against. Take them from files, not recall.
9. **Never invent.** No endpoints, flags, defaults, benchmarks, user counts, customer quotes or "supports X" claims that the source does not show. Numbers in a changelog or PR come from the change itself.
10. **Lead with what the reader does.** First screen: what this is and the first action. Plain verbs, short sentences, active voice. Cut filler openers ("Please note that", "In order to"). Clarity beats completeness beats elegance.
11. **Write for the new teammate.** If they would have to ask a question to follow it, the page is not done.
12. **Markdown discipline.** One H1, no skipped levels, descriptive sentence-case headings, fenced code blocks with a language tag (`text` for plain output), tables for reference data (about five columns at most, header row), relative links with meaningful text, numbered lists only for ordered steps. Details: [reference and API](references/reference-and-api.md#markdown-conventions).
13. **Audience and language.** Match the reader's level and the project's existing language. For Vietnamese or other non-English docs, apply the structure, verification and navigation rules here; English wording rules (filler lists, tone words) do not transfer.
14. **Reasons belong to the author.** For an ADR, PR rationale or design note, record only the context, alternatives and reasons the author or the repo actually shows. A plausible rationale you made up is an invention; ask with `[ASK AUTHOR: which alternatives were weighed?]`.
15. **A guarantee is as strong as the code.** Check order of operations, defaults and edge cases before writing "never", "always", "at most" or "backwards compatible". State a limit exactly (for example, whether an offset is added before or after a clamp). A changed default is a behaviour change even when the signature is unchanged; say so.

## Output

Return the finished page(s) as Markdown in the repo's conventions, with a short note after it:

```
Page type: <tutorial | how-to | reference | explanation | README | PR | changelog | migration>
Written for: <reader and what they already know>
Verified: <commands and links actually run or opened>
Untested: <items marked [UNTESTED], with why>
Open: <[ASK AUTHOR: ...] and [VERIFY: ...] markers that need an answer>
Linked pages: <neighbouring docs this page points to or needs created>
```

When editing an existing page, change the smallest amount that fixes the defect, keep the author's wording and structure elsewhere, and report what changed and why in a few lines. Do not silently overwrite hand-written content or generated sections.

## Examples

Reference entry, before and after (reader is looking up a flag):

```text
Before: --retries is a really useful option that lets you make your
        requests more resilient. We recommend setting it to 3.
After:  --retries <n>   Retry failed requests n times. Integer, 0 to 10.
        Default: 0. Cannot be combined with --no-network.
```

Changelog line, before and after:

```text
Before: Refactored cache eviction module.
After:  Fixed: repeated searches no longer slow down after an hour of use (#238).
```

Commit message, before and after (diff makes the exporter skip blank rows):

```text
Before: fixed stuff in exporter
After:  fix(export): skip blank rows when writing CSV

        Blank rows in the source table produced lines of bare commas,
        which the importer rejected. Skip rows whose fields are all
        empty. Closes #87.
```

## Reference files

| File | Load when |
|---|---|
| [doc types](references/doc-types.md) | Choosing or building a tutorial, how-to, reference page or explanation; untangling a mixed page or a request that mixes types; planning docs architecture and navigation |
| [README and PR](references/readme-and-pr.md) | Writing a README, code walkthrough, PR description, commit message, ADR, changelog, release notes or migration guide |
| [reference and API](references/reference-and-api.md) | Writing API, CLI, config or script reference; generating docs from source; reviewing code comments; markdown and diagram conventions |
| [README template](assets/readme-template.md) | Starting a README from a skeleton |
| [PR description template](assets/pr-description-template.md) | Starting a PR body from a skeleton |
| [eval.md](eval.md) | Final self-check before returning |

## Attribution

The four-type model (tutorial, how-to guide, reference, explanation) and its reader-need compass come from Diátaxis by Daniele Procida and contributors, licensed CC-BY-SA 4.0. This skill is an adapted, reorganized summary in different words, extended with README, PR, changelog and code-walkthrough guidance; it is shared under the same license, CC-BY-SA 4.0.
