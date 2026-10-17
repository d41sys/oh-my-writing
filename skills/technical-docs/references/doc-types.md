Load when: choosing a documentation type, building a tutorial, how-to guide, reference page or explanation, untangling a page that mixes types, or planning how a docs set is organized and linked.

# Documentation types

Adapted from the Diátaxis framework (Daniele Procida and contributors, CC-BY-SA 4.0); see the attribution in SKILL.md.

## Classify with the compass

Two questions place any piece of content. Apply them loosely and at any scale: a whole site, a page, a paragraph, a sentence.

1. Does this help the reader **do** something or **know** something?
2. Is the reader **studying** (building a skill) or **working** (a real task in front of them)?

| | Studying | Working |
|---|---|---|
| **Doing** | Tutorial | How-to guide |
| **Knowing** | Explanation | Reference |

Reader signals to listen for:

| The request sounds like | Type |
|---|---|
| "I'm new, teach me", "get started", "first project" | Tutorial |
| "How do I rotate the key", "set up X with Y", "fix error Z" | How-to |
| "What does `--force` do", "list the config keys", "endpoint schema" | Reference |
| "Why does it work this way", "when should I choose A over B", "how does it fit together" | Explanation |

Two caveats:

- A tutorial is defined by the reader's relationship to the subject, not their seniority. A senior engineer learning a new tool still needs a tutorial; they just move through it fast.
- Exactly four types cover what a practitioner needs. If content seems to fit none, it usually belongs to a fifth artifact (README, changelog, PR body) or is two types fused together.

## Where mixing happens

Each pair of neighbours shares one axis, so each pair blurs:

| Pair | Shared axis | Typical leak |
|---|---|---|
| Tutorial and how-to | Both guide action | A how-to written as a friendly lesson; a tutorial full of real-world options |
| How-to and reference | Both serve work | Option tables pasted into steps; steps pasted into reference entries |
| Reference and explanation | Both hold knowledge | Design arguments inside a parameter description |
| Tutorial and explanation | Both serve study | A lesson that stops to lecture |

The worst collapse is tutorial into how-to. The fix for every leak is the same: keep the text in the page whose reader needs it, and replace the rest with a link.

Allowed inline: one sentence that prevents an error ("Run this with `--dry-run` first; a rollback locks the table"). Move out: a paragraph of history, a comparison of designs, a full parameter list.

Taking explanation out of a tutorial often exposes a spot where the learner was expected to work something out alone. That is a gap in the lesson, not a style issue; fill it with an action and an expected result.

## Tutorial

**Reader**: new to this, wants to gain skill, will follow where led. **Job**: a guided experience that ends with something working and the learner feeling capable.

Build it like this:

1. Name the outcome in one concrete sentence ("In this tutorial we will build a CLI that ..."; for a getting-started guide, "In this guide we will ..."). Say what will be built, not what the learner will "understand" or "learn"; write in the first person plural ("we") and point out in passing what the learner should notice. State the learning goal as a real outcome (what they can now do), not an abstraction.
2. Choose a bounded exercise that finishes in one sitting and yields something real. The exercise is meaningful (a visible achievement), completable, logical in sequence, and complete enough to touch every tool and concept the lesson promises.
3. Fix the environment: exact tool versions, a starting repo or files, and a way to reset if a step fails.
4. Write one path. Offer no "or use X instead", no database menus. Required platform branches are the only forks, and they are labeled.
5. Give every step an action and a result. Use ordered imperatives: "First, run ...", "Now open ...". After a step, show the output the learner should see; if the command is silent, say silence is success.
6. Show results early and often. Even the smallest step produces something the learner can interpret. Link cause to effect.
7. Warn before surprises ("this prints about a hundred lines of log") and name a known wrong-turn sign ("if the output lacks `listening on :8080`, the server did not start; recheck step 3").
8. Stay concrete: this file, this command, this output. Let general ideas emerge from specifics; park theory behind a link.
9. Spell out embodied basics a learner cannot guess: which terminal, where to type, how long to wait.
10. Close by describing what the learner has accomplished, then link to the next how-to, the reference and the explanation. If the learner gave a vague goal or none, ask before writing; a vague mission is worse than none.

Goal check: success means the learner gained skill, not that the artifact exists. If they stop halfway, they should still have gained something.

Reliability is the bar. Every promised result must appear for every reader, so test in a clean environment and, when possible, with someone who has not seen the draft. Budget regular maintenance: one product change can ripple through the whole lesson.

Seed data teaches too: realistic names instead of "Test Client", one record per interesting state, records that show relationships.

## How-to guide

**Reader**: knows the basics, has a goal, owns their own system. **Job**: get one job done correctly, adaptably.

1. Title it "How to <goal>" and frame it around the user's goal, not around what a tool can do. One guide answers one question; two goals mean two guides.
2. Open with one or two sentences: the problem and what the guide delivers ("This guide shows you how to ...").
3. List prerequisites and required state. Do not reteach how to use the tools.
4. Write steps in dependency order; group related changes; reduce context switching; make each step verifiable. Steps may be thinking and decisions ("choose the replica count based on read load"), not only keystrokes.
5. Handle real variations with conditional imperatives: "If you run a replica, set `role=replica` and skip to step 5."
6. Add the realistic failure cases next to the step where they occur: symptom, likely cause, check, fix.
7. Point to reference for every full option list instead of repeating it; point to explanation when a choice needs background.
8. Start and end at meaningful points. A how-to need not run end to end; it must adapt to the reader's setup.
9. Prefer one default path with a narrow escape hatch to a menu of alternatives.

Skeleton: title, intro sentence, prerequisites table (requirement, version, how to check) with one command that verifies them all and what it should print, numbered steps (each headed or led by a verb; action, one-clause reason if non-obvious, command, expected output), verification, troubleshooting, related links. Show real trimmed output at checkpoints, not "you should see output". After an error-prone step, list the causes people actually hit, each as symptom, likely cause, check, fix; take them from issues, logs or your own run, not from guesses. Add "last verified on <version>" only when someone will keep it current; add time and difficulty only when they are measured.

Fragility sets freedom. When many approaches work, give guidance and reasons. When one preferred pattern exists, give a template with parameters. When an operation is fragile or order-bound, give the exact commands.

## Reference

**Reader**: mid-task, wants a precise fact fast, never reads front to back. **Job**: state the machinery completely and consistently.

See [reference and API](reference-and-api.md) for entry layouts. Core rules:

- Describe, do not instruct, teach, persuade or argue. Neutral voice, no marketing adjectives.
- Mirror the structure of the thing described (API routes, module tree, command tree, schema), so gaps are visible to maintainers and lookup is predictable. Mirror without forcing: do not bend the page into an awkward shape just to match.
- Use one layout for every entry. Readers must find types, defaults, constraints and errors in the same place every time.
- State rules as plain constraints: "Required. Cannot be combined with `--stdin`. Invalid when `mode=raw`."
- Include a short, copy-runnable example per entry to show syntax and shape, not an end-to-end journey.
- Generated reference (from OpenAPI, type stubs, docstrings) keeps facts accurate but is not a whole docs set; tutorials, how-tos and explanation are still needed.
- Keep it in sync on every release. Accuracy, completeness and consistency are separate checks; a page can pass one and fail the others.

## Explanation

**Reader**: away from the keyboard, wants to understand. **Job**: build a durable mental model.

1. Anchor on a real or imagined "why" question; it bounds the topic. Titles read naturally after an implicit "About ...".
2. Give context: history, constraints, the forces that shaped the design.
3. Compare alternatives and state trade-offs: "Optimistic concurrency gives higher write throughput under low contention but costs retries under heavy conflict."
4. Open up the internals ("a client request reaches the router, which ...") so behaviour stops looking arbitrary.
5. Ground each point with a specific example and its implication; avoid floating abstractions.
6. Weave connections to related ideas, analogies and neighbouring systems.
7. Allow reasoned opinion and multiple viewpoints, labeled as such.
8. Keep it bounded: no step-by-step procedures, no parameter tables; link to how-to and reference.

Do not scatter explanation in small parcels across other pages. Give it a home (a Concepts, Background or Discussion section) and link from the steps that need it.

Architecture docs are explanation plus a map. Skeleton: one-paragraph overview, stack table (layer, technology, version), annotated directory tree two levels deep, key flows traced step by step (request, middleware, handler, store, response), configuration, deployment. Pick the diagram type by what it shows; see [reference and API](reference-and-api.md#diagrams).

Decision records are a short explanation: context, options considered, decision, consequences. Write one only when the choice is hard to reverse, surprising without context, and the result of a real trade-off. Skeleton and rules: [README and PR](readme-and-pr.md#decision-records-adrs).

## Docs architecture and navigation

- **Readers jump.** Experienced users enter at reference, drop into a how-to for an edge case, and read explanation when evaluating a trade-off. Every page must stand alone and link to its neighbours.
- **Every page links outward by type**: a how-to links to the reference for its options and the explanation for its concepts; a tutorial links onward to how-tos; reference links to the how-tos that use it.
- **Do not plan a four-folder skeleton and fill it later.** Empty category pages and "TODO" stubs are broken promises. Improve what exists, and let structure form when accumulated edits demand a heading.
- **Complete, not finished.** Whatever is published must be accurate, useful and coherent now, even though the set will keep growing.
- **Fix docs by small loops.** Pick any one page; ask what need it serves and whether its form matches; choose one change (add, delete, move, rephrase); make and commit it; repeat. Do not throw away a messy docs set to start over.
- **Inventory before creating.** List the existing surfaces (README, architecture docs, decision records, runbooks, changelog, generated docs), map each to a role, and reuse them. When a role is missing, propose the smallest new section and ask before adding a new top-level file.
- **One owner per fact.** The fact lives in one place; other pages link to it. Typical project roles: rules and conventions; a map of what exists and who owns it; current status and blockers; durable history and decisions. Do not let the map turn into a status dashboard or the history repeat every commit.
- **Keep agent and contributor instruction files short**: signposts to the map and status, not copies of them.
- **Update the role affected by a change**: structure change updates the map; a removed feature gets its page archived and marked, not silently deleted; a hard-to-reverse decision gets a record; routine fixes rely on version control.
- **Staleness pass.** Periodically list pages untouched for a long time (for example 90 days), compare against recent source changes, and end with Updated / Flagged / Skipped per page.
- **Completeness is not a page count.** Do not call docs ready because a number of files exist; check that the content matches the implemented behaviour.
- **Progressive disclosure.** A main page gives the overview; deep detail sits one link away, one level deep, not in chains that cause partial reads.
- **Sync on behaviour change.** A new, renamed or changed feature updates or creates its page in the same change. Always update docs for new major features, route changes, dependency changes, architecture changes and setup changes; for cosmetic fixes and internal refactors it is optional.
- **Role names matter less than roles.** A docs set needs a place for rules and conventions, a map (what exists, where, who owns it), current status (blockers, what is being removed), and durable history (decisions, removals, incidents). Keep each role in one file and link between them; do not let rules hold live status, the map become a dashboard, or history repeat every commit.
- **History is append-only.** Correct a stale claim with an explicit dated correction, not a silent rewrite. For removed paths, keep a short table (path, why removed, replacement) while recreating them is still a risk.
- **Do not claim docs are read automatically** unless a real mechanism loads them. Otherwise say which page to read first.
- **FAQ and troubleshooting come from real confusion**, such as issues, support threads and the moments you got stuck while writing, not from hypothetical questions.
- **Short tool or feature pages** can use four parts: what it does, when to reach for it, common questions, how you know it is working.
- **Quick-reference sheets and cheat sheets** may drop the surrounding prose entirely; scannability wins. The four-type model does not apply to contract-first or regulatory specifications that must be reviewed and published as one baseline.

## Mixed-page repair, quickly

1. Highlight each paragraph with its reader state (do, finish, look up, understand).
2. Keep the dominant state; the rest moves or becomes a link.
3. Create a destination page only when the moved content is substantial and real; otherwise delete it.
4. Add links both ways.
5. Recheck the moved-out page's first line still states its own type's job.

## A request that mixes types

When a user asks for one document that spans types ("a tutorial that also documents every endpoint"), decide before writing:

1. Name the primary reader state (here: a newcomer learning by doing) and write that page to its contract. It uses only the endpoints the lesson needs.
2. Put the remaining material in its own page of the right type (here: a reference page listing every endpoint in one layout) and link to it from the spot in the tutorial where the reader would ask "what else can I call?". Link back from the reference.
3. Tell the user what you split and why, in the reply, naming each file ("the guide is `getting-started.md`; the separate reference page `configuration.md` lists every key"), so the change is visible and reversible. The page text itself does not narrate the split.
4. If the user explicitly wants a single file, keep one document but separate the parts under their own H2 sections, label each with its type, and make the reference part self-contained. Say it is a compromise.
5. Create the second page only when it has real content from the source; never a stub.
