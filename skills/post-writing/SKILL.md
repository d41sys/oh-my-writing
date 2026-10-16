---
name: post-writing
description: Drafts, restructures and repurposes public posts such as blog posts, long-form articles, essays, newsletters, LinkedIn and X or Threads posts and threads, launch announcements, and adaptations of one piece across channels. Starts from the reader and one takeaway, opens on a concrete artifact, keeps proof ahead of adjectives, and never invents anecdotes, metrics or clients. Use when asked to write or improve a blog post, article, essay, newsletter issue, LinkedIn post, X thread, announcement, launch post, or to turn one piece into several channel versions.
metadata:
  version: "1.0"
  skill-author: d41sys
---

# Post Writing

Public posts are read by people who owe the author nothing: they can stop at the first line. This skill turns the author's real material into a post that earns the next paragraph. It starts from one reader and one takeaway, chooses a structure by the job the piece must do, and fits the result to the channel without changing what the piece claims.

The author's experience, numbers and opinions come only from the author. Where material is missing, the draft carries a marker or a question, never an invented stand-in.

## When to use

- Writing a blog post, long-form article, essay, personal or reflective piece, devlog or post-mortem.
- Writing a newsletter issue, or planning a recurring newsletter format.
- Writing a LinkedIn, X, Threads, Bluesky or similar post or thread; writing a carousel outline.
- Writing a product, feature, release or project announcement meant for the public.
- Repurposing one finished piece into other channels or lengths.
- Fixing a weak title, opening, structure or ending in an existing public post.

Not for:
- Removing machine-sounding patterns from a finished draft: use `anti-slop-editing`.
- Capturing or applying a specific author's voice: use `author-voice`.
- Turning raw notes into a brief and outline for a long piece, or co-writing interactively: use `structured-drafting`.
- Claim strength, citations and number checking in depth: use `evidence-grounded-writing`.
- Decision, research or market reports and executive summaries: use `report-writing`.
- Tutorials, how-to guides, READMEs, PR descriptions, changelogs: use `technical-docs`.
- Résumés, cover letters, profiles, outreach: use `career-documents`.
- Machine-learning paper sections: use `academic-writing`.

## Inputs

Read what the author supplied before asking anything: notes, a draft, a link, data, a voice sample, the target channel. Then fix these five items, silently where the material answers them:

1. **Reader.** Who opens this, what do they already know, what problem sent them here.
2. **One takeaway.** The single sentence the reader should be able to repeat afterwards.
3. **Action.** What the reader can do next, if anything: reply, try a command, read the repo, subscribe, nothing.
4. **Material.** The artifacts the author actually has: numbers, logs, screenshots, code, quotes, a real episode.
5. **Channel and size.** Where it will be published, and any length limit.

Ask at most 1 to 3 questions, and only when the answer would change the draft: usually the reader, the channel, or a missing fact the piece cannot work without. Otherwise proceed and state assumptions in one line at the top of the reply.

If the author supplied a writing sample, treat it as the voice target (see `author-voice` when available). If not, default to plain, direct prose that fits the genre. Do not impose a house persona.

## Workflow

Pick a mode first. **Draft** (material to post), **Repair** (existing draft to better draft), **Repurpose** (finished piece to other channels). Repurpose mode follows [repurposing](references/repurposing.md) after step 2 here.

1. **Fix the brief.** Write reader, takeaway, action, channel and assumptions as five short lines. If the takeaway will not fit one sentence, the author has two posts; say so and pick one.
2. **Inventory the material.** List the concrete things available: numbers with their conditions, an incident with its sequence, code or output, a quote with its source, a screenshot. List what is missing and what the piece would need. Mark each gap `[ASK AUTHOR: ...]` or `[VERIFY: ...]`. Do not fill a gap with a plausible detail.
3. **Choose the post type.** Match the job to a type in [post types](references/post-types.md): how-to, argument or opinion, story or reflection, post-mortem or devlog, announcement, list with depth, explainer, comparison, newsletter issue. The type sets the spine; do not reuse one template for everything.
4. **Open on the concrete thing.** Draft the opening from the best artifact, example, number or scene. When the angle is still open, write two or three candidate openings that imply different pieces and let the author pick; see [openings and endings](references/openings-and-endings.md). Allow a line of context first when a cold reader cannot parse the artifact without it.
5. **Build the body by job.** Give each section one job, and say it in a heading or first sentence when the piece is long enough to need headings. Show the example before explaining the mechanism. Introduce a concept before a later paragraph leans on it. Keep the author's real sequence for incident and design stories: starting point, blocker, attempt, turn, result. Never invent why the author moved from one step to the next; ask.
6. **Package it.** Write the title or first line so it promises exactly what the piece delivers. Add headings, lists and tables in proportion to length and only where the content has that shape. For long web posts, state the answer to the likely query plainly near the top and use descriptive headings; do not repeat keywords for their own sake. Platform limits and conventions are in [platforms](references/platforms.md); treat every number there as something to verify before relying on it.
7. **End where the piece ends.** Close on the last concrete point, a real next action, or a real open question. Do not recap what the reader just read, and do not add a moral or an engagement prompt the material did not earn.
8. **Route the finishing passes.** For voice, apply the author's profile or sample (`author-voice` if available). For machine-sounding patterns, run `anti-slop-editing` as the final pass if it is available; otherwise apply the checks in [eval.md](eval.md).
9. **Self-check and return.** Run [eval.md](eval.md) on the draft, fix every failure, then return the deliverable in the shape under Output.

### Repair mode specifics

Diagnose before editing: is the problem the takeaway, the order, the opening, the proof, the length, or the sentences? Fix the highest layer that is broken. Keep the author's claims, qualifiers, numbers, names and voice unless one of them is the defect. Report changes in a short list with the reason for each.

### Draft mode with an open angle

When the author has raw notes but no settled angle, separate exploring from composing:

1. Collect fragments first: a sharp sentence with no home, a claim with a one-line reason, a scene, an analogy, a half-formed thought. Keep them unordered and in the author's words. Do not outline yet.
2. If one idea keeps recurring, name it. A good name later shapes the title and the transitions. Prefer an existing word over a coinage; if a new term is needed, define it where it first appears.
3. Read the whole pile, then write two or three candidate openings that imply different pieces. Let the author choose or combine.
4. Compose one move at a time. After each move, ask what the reader needs next, and offer two or three candidates that rely only on ideas already on the page. Surplus fragments stay unused; the piece ends when its line of thought is complete, not when the pile is empty.
5. When the next move needs a fact the pile lacks (an example, a number, a counter-case), name the gap and ask for it or cut the move.

This loop suits essays and argued posts where the author holds the judgment. For a templated post (announcement, release note, list) fix the shape first and fill it.

### Short posts (under about 300 words)

Skip the heavy steps. Write the brief in your head, pick one opening move, write the post, check the first line against the channel's display limit, run the final pass, and return it with the open items. A short post still needs a real artifact, claim or question in its first line, and still carries no invented detail.

### Missing material

| Situation | Do this |
|---|---|
| The author has a topic but no examples or numbers | Ask for the one best real example; if none exists, draft with `[ASK AUTHOR: ...]` markers and label any illustration as hypothetical |
| A needed fact is plausible but unverified | Keep it out of the text or mark it `[VERIFY: ...]`; never state it as fact |
| The author gives a statistic with no source | Keep it with `[VERIFY: source]` and do not strengthen the claim |
| The author asks for "a relatable story" | Ask for a real one; offer an outline where the story goes |
| Two pieces of evidence conflict | Show both and the condition that explains the difference, or ask |

## Rules

- **Start from the reader, not from the topic.** A post about "our caching layer" has no reader; a post for "a developer whose p95 doubled after adding a cache" does. Exception: a personal essay may start from the author's question when the reader is a general audience that follows the author.
- **Open on something the reader can see.** An artifact, number, scene or sharp claim lets the reader judge the piece in one line. Warm-up sentences make the reader do that work for you. Exception: when the artifact is meaningless without a premise (a stack trace for a newcomer), give one line of context first.
- **Proof over adjectives.** Replace "powerful", "seamless", "game-changing" with the fact that would justify the word. If no fact exists, delete the adjective; do not manufacture the fact. Exception: a subjective judgment the author genuinely holds can stay as clearly their opinion.
- **Author experience comes only from the author.** Never write "last week a client told me", "in our production tests", or a number that the material does not contain, even as an illustration. Use a placeholder marker, or a labelled hypothetical ("suppose a team...") when an illustration is needed.
- **Structure by job, not by template.** A how-to wants ordered steps, an argument wants claim then reasons then the strongest objection, a story wants the real sequence. A fixed formula (hook, three bullets, question) makes unlike pieces look alike and drains the specific content. Exception: a recurring newsletter benefits from a stable skeleton, because the reader returns for it.
- **Formatting is proportional to length.** A 120-word post needs no headings; a 2,000-word guide needs them. Use a list for parallel items and a table for repeated fields; use prose for reasoning. Do not break every sentence onto its own line to fake emphasis. Exception: platforms where short lines are the norm (some feeds); even then keep the breaks for real pauses.
- **A title or hook is a promise.** Say what the piece delivers, with the specifics the reader would search or care about. A curiosity gap is fine only if the piece closes it. If the best title overstates the content, change the title or change the piece.
- **Endings stop on content.** A recap repeats what the reader just finished; an aphorism claims a significance the piece should have shown. Exception: a long guide can end with a short "where to go next" or a checklist that adds a usable artifact.
- **Platform guidance is current practice, not ranking science.** Length bands, fold points and posting habits drift. Present them as things to check, and do not claim that a format, link placement or hashtag count boosts distribution. Write for the reader; adjust only for display limits and conventions.
- **Honest framing.** Name a real limitation when it is relevant; do not stage fear, urgency or vulnerability the material does not support. Exception: none for fabricated stakes; a real deadline or a real risk is fair to state plainly.
- **Search and answer-engine visibility follows clarity.** Answer the query in plain words early, use descriptive headings, label units and versions, date what ages. One version serves people and machines; keyword repetition and machine-only variants help neither.
- **Other languages.** The lexical pattern lists in the sibling skills are English-only. For Vietnamese or any other language, apply the structural, evidence and preservation checks here and say plainly that word-level lists do not transfer. Keep technical terms, commands and code as the community writes them.

## Output

Return, in this order:

1. **Assumptions** (one line): reader, takeaway, channel, any assumed length.
2. **The post**, ready to paste, in the target format. For long pieces include the title and, if wanted, two alternative titles.
3. **Open items**: every `[ASK AUTHOR: ...]` and `[VERIFY: ...]` in the text, each with what is needed to resolve it. If none, say "No open items."
4. **Change note** (Repair and Repurpose only): short list of what changed and why, including anything deliberately left alone.

For Repurpose mode, give each channel as a labelled block with its own opening and ending, plus the carried-over core claim in one line and any publishing constraints still unresolved.

## Examples

Opening, before and after (illustrative; the numbers are placeholders the author must replace):

- Before: "In today's fast-moving world of software, performance matters more than ever, and caching is a key technique."
- After: "Our p95 went from `[ASK AUTHOR: before]` to `[ASK AUTHOR: after]` after we changed one cache setting. Here is the setting and what it broke."

Ending, before and after:

- Before: "In conclusion, caching is powerful when used wisely. What do you think?"
- After: "If you run the same workload, set the TTL to `[VERIFY: value]` and watch the miss rate for a day before you trust it. I would like to hear what your numbers look like."

The second ending is acceptable only if the author does want replies; otherwise stop one sentence earlier.

## Reference files

| File | Load when |
|---|---|
| [references/post-types.md](references/post-types.md) | Choosing the spine for a how-to, opinion, story, post-mortem, announcement, list, explainer, comparison or newsletter issue; stress-testing a thesis; framing honestly for the reader. |
| [references/platforms.md](references/platforms.md) | Fitting a piece to LinkedIn, X, Threads, Bluesky, Instagram, forums, Xiaohongshu, WeChat, email or a blog; checking limits and conventions. |
| [references/openings-and-endings.md](references/openings-and-endings.md) | Writing or repairing a title, opening, hook, headline or ending; deciding whether context before the artifact is justified. |
| [references/repurposing.md](references/repurposing.md) | Turning one piece into several channel versions, shortening under a limit, or checking that adapted versions still match the source. |
