---
name: technical-docs
description: Use when writing technical text from code, a diff, commits, a config or a methods passage, including a plain-language account of a method for lay readers. Read it before drafting even a short changelog entry or pull request description that looks easy, because the usual failures there are invented results and the wrong reader. Covers a README, API or CLI reference, tutorial, how-to, quickstart, design rationale, code walkthrough, ADR, commit message, release notes and migration guide.
license: CC-BY-SA-4.0
metadata:
  version: "1.12.1"
  skill-author: d41sys
---

# Technical Docs

Technical readers arrive in one of four states: they want to learn by doing, to finish a task, to look something up, or to understand why. This skill classifies the request into one of those four page types before any text is written, then builds the page to the rules of that type. It also covers the artifacts that sit around code: READMEs, code walkthroughs, pull request bodies, changelogs and migration guides.

## When to use

- A page, README, guide, API/CLI/config reference or architecture write-up must be created, restructured or reviewed.
- A code change needs a PR description, a commit message, release notes or a migration guide.
- A hard-to-reverse technical choice needs a short decision record (ADR).
- A docs set feels messy: pages try to teach, instruct, specify and justify all at once.

Not for: ML paper sections (use `structured-drafting` for structure plus `evidence-grounded-writing` for claims); blog posts, essays or newsletters, including a blog-style how-to post and a launch announcement post (use `post-writing`; release notes and changelogs stay here); multi-option decision, research or market reports and blameless incident post-mortems (use `report-writing`; a single engineering decision stays here as an ADR); résumés and cover letters (use `career-documents`); tracing which claims need sources (use `evidence-grounded-writing`). For a final AI-pattern cleanup, use `anti-slop-editing` if available; otherwise apply the checks in [eval.md](eval.md). Clipped imperative fragments, bare parameter lists and repeated domain terms are normal in docs, changelogs and commit messages; do not "fix" them as style defects.

## Inputs

Read before writing: the code, config, schema, `--help` output or diff being documented; existing docs and their conventions (names, folders, template files); version numbers from package or lock files, not memory.

Ask at most three questions, fewer for short tasks, and only when the answer changes the page:

1. Who is the reader and what do they already know?
2. Which job is this page for: learning, finishing a task, looking up, or understanding?
3. Which version or environment does it target?

Otherwise (and always in non-interactive runs) proceed, and state assumptions at the top of your reply, not inside the page. Questions for the author go in the reply too (see rule 16), never into the page.

## Workflow

1. **Classify.** Apply the compass: is the reader doing or thinking, and are they studying or working? Pick one type from the table below. If the request spans types, plan one page per type and link them. See [doc types](references/doc-types.md).
2. **Inventory.** Check what docs already exist. Reuse and link them; do not create a page that duplicates a fact owned elsewhere. Create a new file only when something real must go in it, and follow the repo's folder and naming habits.
3. **Gather facts from source.** Read the code, run `--help`, read the diff and commit log. Never document planned or guessed behaviour. When a fact is missing, never invent it: state the gap in the reader's words ("The notes do not say which alternatives were weighed."), or leave the sentence out. Record the question for the author as a marker line in your reply, with one kind per line: `[VERIFY: ...]` (a source exists or must be found and checked: an external or checkable fact), `[ASK AUTHOR: ...]` (the author knows or decides it: intent, reasons, numbers they hold) or `[UNTESTED]` (a command or sample not run). No other marker kinds, no TBD or TODO stubs.
4. **Pick the skeleton.** Use the type's skeleton from [doc types](references/doc-types.md), the README or PR shape from [README and PR](references/readme-and-pr.md), or the entry layout from [reference and API](references/reference-and-api.md). Start from [assets/readme-template.md](assets/readme-template.md) or [assets/pr-description-template.md](assets/pr-description-template.md) where they fit.
5. **Draft to the type's contract.** Write the page for its single reader state. Move anything that belongs to another type into a link.
6. **Verify every command and sample.** Run it, or leave it out of the page, or say in plain words what was and was not run ("These steps were not run in this environment." only when that helps the reader), and list the item as `[UNTESTED]` in the reply with the environment it needs. State versions. Check that each path, flag, link and output you cite exists.
7. **Check navigation.** Add links to the neighbouring types, not copies of their content. Update the index or map page if the set of pages changed.
8. **Self-check and return.** Run [eval.md](eval.md), fix failures, then reply with the page plus a short list of what was verified, what is untested, and what is still open. When you wrote or split off more than one page, name each file and say in one line what went where and why. When files are written, also write `open-questions.md` beside them with the same marker lines.

### The four page types

| Reader state | Type | Contract in one line |
|---|---|---|
| Studying, doing | Tutorial | A guided path that always succeeds and builds skill through visible results. |
| Working, doing | How-to guide | Steps to reach one named goal, for someone who already has the basics. |
| Working, looking up | Reference | Neutral, complete, consistent facts shaped like the thing described. |
| Studying, thinking | Explanation | Context, reasons, alternatives and trade-offs, read away from the keyboard. |

Other artifacts map onto these: a README is a front door that links into all four; a PR body is a review aid; a commit message is a one-change record; a changelog is dated reference; a migration guide is a how-to with a before/after reference; a code walkthrough is explanation anchored to real files; an ADR is a short explanation of one decision.

## Rules

1. **One page, one type.** Mixed pages fail every reader: the learner meets choices, the worker wades through background, the person looking up a flag finds a story. Exception: a one-sentence safety reason or a pointer belongs inline in a step; a paragraph of rationale does not. A request that asks one page to do two jobs ("a getting-started guide that also lists every option") becomes two pages: the guide teaches one short path and links to a reference page that holds the full list; write the reference page beside it, complete, in the same delivery. The guide names the one setting its first run needs, and its pointer says what the reference holds (every key, its default and allowed values), so a reader holding only the guide knows where each option lives. Keep one file only when the author insists, as labeled sections. Reason: the full table buries the first run, and a request for "every option" is met by the linked page.
2. **Tutorials promise success and deliver it.** Pick one path, fix versions and starting files, show what the learner should see after each step, and say when silence means success. Teach by doing, not by telling. Start the learner from the files the project already ships (an example config, sample data, the script itself) when they give a quick visible result, instead of inventing stand-ins. The opening says in plain words what the learner will have at the end and what to do first, in whatever phrasing suits the page; the close says what the learner now has and where to go next. Exception: a genuinely required platform branch (for example an OS-specific install) is labeled, not removed.
3. **How-tos name a goal and trust the reader.** Title them "How to X". Skip steps any practitioner knows. Cover real variations ("if you run a replica, ...") and the likely failures. Reason: the reader's system is not your sandbox. Exception: fragile or order-dependent operations get exact commands.
4. **Reference is austere.** State what is, completely and in a fixed layout. No teaching, selling or arguing; link out. Reason: the reader is mid-task and scanning. Exception: a short example per entry is part of reference.
5. **Explanation earns its length by answering "why".** Give history, constraints, rejected alternatives and trade-offs, tied to concrete examples. Admit opinion where it is the author's real judgement. Do not slip in procedures or parameter tables.
6. **Describe the thing as it is now.** Do not narrate the edit that produced it ("this replaces the old approach"). Change history lives in the changelog, release notes, migration guide, commit message or decision record.
7. **Run it or say so.** A sample that was never run is a claim, not a sample. Either run it, drop it, or state in reader language that it was not run; the `[UNTESTED]` line goes in the reply. Reason: docs that do not match reality are worse than none. Exception: placeholder values in a sample are fine when the surrounding text says they are placeholders (for example `<your-token>` with "replace with your token").
8. **State versions and environment.** Every install, command and API page names the version and platform it targets, taken from the source (a docstring, a package or lock file, a CI config), not from recall. The interpreter version of your own test run is not a fact about the project: report it in the reply, and keep it out of the page unless the author asked for the tested environment to be recorded there.
9. **Never invent.** No endpoints, flags, config keys, defaults, install steps, package names, supported formats, benchmarks, user counts, customer quotes or "supports X" claims that the source does not show. A script's install step is what the source shows (the file, the interpreter version, "standard library only"), not a package-manager command. "Tested with 3.11" is not "requires 3.11": report the first as tested, and write a requirement or minimum only when the source states one. Commands run from where the source puts the script ("the directory containing the script"), not from a repository root you assume. Numbers in a changelog or PR come from the change itself; name the parts ("the cap plus jitter") instead of a sum or ratio you computed that appears in no source.
10. **Lead with what the reader does.** First screen: what this is and the first action. Plain verbs, short sentences, active voice. Cut filler openers ("Please note that", "In order to"). Clarity beats completeness beats elegance.
11. **Write for the new teammate.** If they would have to ask a question to follow it, the page is not done.
12. **Markdown discipline.** One H1, no skipped levels, descriptive sentence-case headings, fenced code blocks with a language tag (`text` for plain output), tables for reference data (about five columns at most, header row), relative links with meaningful text, numbered lists only for ordered steps. Details: [reference and API](references/reference-and-api.md#markdown-conventions).
13. **Audience and language.** Match the reader's level and the project's existing language. For readers outside the team (users, residents, a committee), explain internal names, codes and tool details in their terms or leave them out, and match an example page the author gives in length and register. For Vietnamese or other non-English docs, apply the structure, verification and navigation rules here; English wording rules (filler lists, tone words) do not transfer.
14. **Reasons belong to the author.** For an ADR, PR rationale or design note, record only the context, alternatives and reasons the author or the repo actually shows. A plausible rationale you made up is an invention. When the reasons are not shown, the page says what the record does not show ("The notes do not say which alternatives were weighed.") or leaves the section out, and the reply asks `[ASK AUTHOR: which alternatives were weighed?]`.
15. **A guarantee is as strong as the code.** Check order of operations, defaults and edge cases before writing "never", "always", "at most" or "backwards compatible". State a limit exactly: what it applies to (the delay, not the base) and whether an offset is added before or after a clamp. A changed default is a behaviour change even when the signature is unchanged; say so.
16. **The page reads as finished.** A README, guide, how-to, runbook, reference page, PR body, commit message, ADR, changelog or migration guide goes to a reader, so it holds no `[ASK AUTHOR]`, `[VERIFY]` or `[UNTESTED]` markers, no TODO or TBD placeholders, no empty template slots and no process narration ("as requested", "I checked the diff", "the notes say", per-paragraph source notes, `[source: ...]` tags). A gap is stated as a fact about the material ("No license is stated in the repository.") or the sentence is left out; a checkable claim you could not check is left out or stated as unconfirmed. Questions go to the reply, and `open-questions.md` when files are written. Reason: a reader sees placeholders and meta-notes as an unfinished page, and in non-interactive runs the author will not answer first. Exception: the author asked for a draft to edit, or the output is an author-facing artifact (a review of existing docs or code comments, a staleness report, a findings list); then markers stay there. HTML comments that tell the author to delete a section belong to templates, not to the finished page. Gap wording: [README and PR](references/readme-and-pr.md#gaps-in-a-reader-facing-page).
17. **A PR body says what could break.** In plain prose, name the change that carries the risk and what breaks if it is wrong: the consumers, data or jobs the diff and notes name (a named job counts), and how it is undone (for a changed default, the opt-out that restores the old behaviour). Look hardest where the author calls it safe. Say that a change is hard to reverse when it is (a destructive migration, a removed public API, a new on-disk format); a trivially reversible change needs no reversibility line. No fixed labels or risk template. Add rollout and rollback lines only for mechanisms the change or notes actually name; do not mention a canary, flag, staged deploy or dashboard that does not exist, not even to say it is absent. Carry the notes' status statements into the body with their exact scope (the test run and what was not run, CI, whether a design doc exists, which docs were left untouched) and do not widen them ("no other documentation" is wrong when the diff changes a docstring). Reason: reviewers decide how closely to read from the risk, and a mechanism the change lacks or a label the author would not write is noise to them.
18. **Write like the person, not the process.** Docs and PR text read as one colleague writing to another. Say each default, limit or caveat once, at the line it limits (an opt-out, or "jitter is added after the cap", appears in one place and not again in the summary, the changes and the risk lines). A short page (a PR body, commit message, changelog entry, or README under about 400 words) has only the headings its type needs: a small PR is a summary, the changes, what was run and what could break, and it drops reviewer-focus, related and rollout or monitoring sections that the notes do not fill. Use plain transitions with no signposting ("This section", "In summary") and prose for fewer than about four items. Keep the author's person ("we", "I") and the project's own register. Reason: reviewers and new teammates skim; repeated caveats and empty sections hide the one line that matters. Exception: a reference page or README whose type contract fixes the layout; faithfulness rules are unchanged, so every number, default, version and "not run" still appears once where it applies.
19. **Count the example, then write to that count.** When the author points to an example page, an accepted section or a sample to match, measure it before writing: its words, its paragraphs, whether it has headings, lists, code blocks or bold, how it opens and closes, and how much detail one point carries (figures, names and identifiers per paragraph). That is the budget. Stay within about a fifth of its length unless the request states a length, keep its paragraph count give or take one, use no heading, list or bold it lacks, and open and close the way it does. Material that does not fit stays in the notes, the facts this reader needs least going first. Count the draft again before handing over and trim when it is over. Reason: a section twice the length of its model does not match it, however close the register. Exception: a reference page, where completeness outranks the example's length.

## Output

Return the finished page(s) as Markdown in the repo's conventions, with a short note after it:

```
Page type: <tutorial | how-to | reference | explanation | README | PR | changelog | migration>
Written for: <reader and what they already know>
Verified: <commands and links actually run or opened>
Untested: <items left out or described as not run in the page, with why; marker lines>
Open: <[ASK AUTHOR: ...] and [VERIFY: ...] lines that need an answer>
Pages written: <each file with its type; for a split, which content went where and why>
```

Page files carry none of these lines. When files are written, put the same `Untested` and `Open` lines in `open-questions.md` beside them.

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

README gap, before and after (the repository states no license):

```text
Before: ## License
        [ASK AUTHOR: license]
After:  ## License
        No license is stated in this repository. Ask the owner before reusing the code.
Reply:  [ASK AUTHOR: which license applies?]
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

The four-type model (tutorial, how-to guide, reference, explanation) and its reader-need compass come from Diátaxis by Daniele Procida and contributors, licensed CC-BY-SA 4.0. This skill builds on that model in its own words and adds README, PR, changelog and code-walkthrough guidance. It is shared under the same license, CC-BY-SA 4.0.
