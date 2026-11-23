---
name: post-writing
description: Drafts, restructures and repurposes public posts such as blog posts, long-form articles, essays, newsletters, short email sequences, LinkedIn and X or Threads posts and threads, launch announcements, and adaptations of one piece across channels. Starts from the reader and one takeaway, opens on a concrete artifact, keeps proof ahead of adjectives, and never invents anecdotes, metrics, clients, links or calls to action. Use when asked to write or improve a blog post, article, essay, newsletter issue, LinkedIn post, X thread, announcement, launch post, welcome or onboarding email series, or to turn one piece into several channel versions.
license: MIT
metadata:
  version: "1.16"
  skill-author: d41sys
---

# Post Writing

Public posts are read by people who owe the author nothing: they can stop at the first line. This skill turns the author's real material into a post that earns the next paragraph. It starts from one reader and one takeaway, chooses a structure by the job the piece must do, and fits the result to the channel without changing what the piece claims.

The author's experience, numbers and opinions come only from the author. Where material is missing, the post states the claim only at the strength the facts support, or leaves it out; the question goes to the author in the reply. A post is read by the public, so it carries no marker, no bracket placeholder and no process note.

## When to use

- Writing a blog post, long-form article, essay, personal or reflective piece, devlog, or a public post that tells the story of an incident (a post-mortem post).
- Writing a newsletter issue (including an internal team newsletter), a short email sequence (welcome, onboarding, nurture, re-engagement), or planning a recurring newsletter format.
- Writing a LinkedIn, X, Threads, Bluesky or similar post or thread; writing a carousel outline.
- Writing a product, feature, release or project announcement meant for the public, or the set of channel posts around one launch.
- Repurposing one finished piece into other channels or lengths.
- Fixing a weak title, opening, structure or ending in an existing public post.

Not for:
- Removing machine-sounding patterns from a finished draft: use `anti-slop-editing`.
- Capturing or applying a specific author's voice: use `author-voice`.
- A fresh-reader or adversarial review of a finished post: use `independent-review`.
- Turning raw notes into a brief and outline for a long piece, or co-writing interactively: use `structured-drafting`.
- A post or article written from a transcript, an interview or a chat log: read `structured-drafting` first for how to treat the source (remarks not meant for print, a figure the speaker corrected, gaps), then come back here for the form.
- Claim strength, citations and number checking in depth: use `evidence-grounded-writing`.
- Decision, research or market reports and executive summaries, and the blameless incident post-mortem document written for a team: use `report-writing`. A public blog post that tells an incident's story stays here.
- Documentation pages for a product or tool (tutorials, how-to guides, READMEs, PR descriptions, release notes, changelogs): use `technical-docs`. A blog-style how-to post and a launch announcement post stay here.
- Résumés, cover letters, profiles and personal outreach emails for jobs or academia (cold, networking, referral, prospective supervisor): use `career-documents`. Email sequences and newsletters stay here.
- Paid ad copy, app-store listings, conversion landing pages and compliance-heavy SMS or WhatsApp programs are not covered in depth here. If asked, apply the grounding rules (no invented proof, no invented urgency), write to the strictest field limit first, and list every limit that needs checking in the reply.
- Machine-learning paper sections: use `structured-drafting` for structure plus `evidence-grounded-writing` for claims.

## Inputs

Read what the author supplied before asking anything: notes, a draft, a link, data, a voice sample, the target channel. Then fix these five items, silently where the material answers them:

1. **Reader.** Who opens this, what do they already know, what problem sent them here.
2. **One takeaway.** The single sentence the reader should be able to repeat afterwards.
3. **Action.** What the reader can do next, if anything: reply, try a command, read the repo, subscribe, nothing.
4. **Material.** The artifacts the author actually has: numbers, logs, screenshots, code, quotes, a real episode.
5. **Channel and size.** Where it will be published, and any length limit.

Ask at most three questions, fewer for short tasks, and only when the answer would change the draft: usually the reader, the channel, or a missing fact the piece cannot work without. In non-interactive runs proceed on stated assumptions. Otherwise proceed and state assumptions in one line at the top of the reply.

If the author supplied a writing sample, treat it as the voice target (see `author-voice` when available). If not, default to plain, direct prose that fits the genre. Do not impose a house persona.

Also take from the author, and never from memory or invention: the exact product and project names and any names or terms to avoid, the words readers use (quote or paraphrase only comments, reviews or messages the author supplied), and any fixed boilerplate. If a terminology list or house glossary exists, follow it over generic style advice.

## Workflow

Pick a mode first. **Draft** (material to post), **Repair** (existing draft to better draft), **Repurpose** (finished piece to other channels). Repurpose mode follows [repurposing](references/repurposing.md) after step 2 here.

1. **Fix the brief.** Write reader, takeaway, action, channel and assumptions as five short lines. If the takeaway will not fit one sentence, the author has two posts; say so and pick one.
2. **Inventory the material.** List the concrete things available: numbers with their conditions, an incident with its sequence, code or output, a quote with its source, a screenshot, the link to the canonical piece. List what is missing and what the piece would need. This list is a working note for the author, not post text. Record each gap as a question for the reply: `[ASK AUTHOR: ...]` (the author knows or decides it), `[VERIFY: ...]` (a source exists or must be found and checked) or `[UNTESTED]` (a command or snippet nobody ran). In the post, a gap is handled as in [gaps in a published post](#gaps-in-a-published-post). Do not fill a gap with a plausible detail.
3. **Choose the post type.** Match the job to a type in [post types](references/post-types.md): how-to, argument or opinion, story or reflection, post-mortem or devlog, announcement, list with depth, explainer, comparison, newsletter issue. The type sets the spine; do not reuse one template for everything.
4. **Open on the concrete thing.** Draft the opening from the best artifact, example, number or scene. When the angle is still open, offer two or three candidate openings that imply different pieces, in the reply, for the author to pick; the post itself carries one. See [openings and endings](references/openings-and-endings.md). Allow a line of context first when a cold reader cannot parse the artifact without it.
5. **Build the body by job.** Give each section one job, and say it in a heading or first sentence when the piece is long enough to need headings. Show the example before explaining the mechanism. Introduce a concept before a later paragraph leans on it. Keep the author's real sequence for incident and design stories: starting point, blocker, attempt, turn, result. Never invent why the author moved from one step to the next; ask.
6. **Package it.** Write the title or first line so it promises exactly what the piece delivers. Add headings, lists and tables in proportion to length and only where the content has that shape. For long web posts, state the answer to the likely query plainly near the top and use descriptive headings; do not repeat keywords for their own sake. Platform limits and conventions are in [platforms](references/platforms.md); treat every number there as something to verify before relying on it.
7. **End where the piece ends.** Close on the last concrete point, a real next action, or a real open question. Do not recap what the reader just read, and do not add a moral or an engagement prompt the material did not earn.
8. **Route the finishing passes.** For voice, apply the author's profile or sample (`author-voice` if available). For machine-sounding patterns, run `anti-slop-editing` as the final pass if it is available; otherwise apply the checks in [eval.md](eval.md).
9. **Self-check and return.** Run [eval.md](eval.md) on the draft, fix every failure, then return the deliverable in the shape under Output.

### Repair mode specifics

Diagnose before editing: is the problem the takeaway, the order, the opening, the proof, the length, or the sentences? Fix the highest layer that is broken. Keep the author's claims, qualifiers, numbers, names and voice unless one of them is the defect. Report changes in a short list with the reason for each.

### Draft mode with an open angle

When the author has raw notes but no settled angle, use Explore mode and the move-by-move loop in `structured-drafting` (its co-authoring protocol). Without that skill: collect unordered fragments in the author's words, name any recurring idea, write two or three candidate openings that imply different pieces for the author to pick, then compose one move at a time from ideas already on the page, asking for any fact the pile lacks. This suits essays and argued posts; for a templated post (announcement, list) fix the shape first and fill it.

### Short posts (under about 300 words)

Skip the heavy steps. Write the brief in your head, pick one opening move, write the post, check the first line against the channel's display limit, run the final pass, and return it with the open questions in the reply. A short post still needs a real artifact, claim or question in its first line, and still carries no invented detail. Before returning, check that separate findings were not merged into a run of same-length sentences (see "Write like the person").

### Gaps in a published post

A gap is something the material does not give. The post either makes the claim at the strength the facts support or leaves the sentence out; when the reader would otherwise assume something false, it says plainly what the material does not cover. The author's question goes to the reply.

| Situation | In the post | In the reply (and `open-questions.md` when the post is saved to a file) |
|---|---|---|
| The author has a topic but no examples or numbers | Argue from what is stated, with no figure, no scene and no "recently"; or write the claim at the strength the facts give and stop | `[ASK AUTHOR: the one best real example or number, with its conditions]`; ask it first when the session is interactive |
| A needed fact is plausible but unverified | Leave it out, or state it as the author's own claim ("by our count", "the vendor says") when that is what the material gives | `[VERIFY: ...]` naming the fact and where to check it |
| The author gives a statistic with no source | Keep the figure at the author's strength and attribute it to them; add no "studies show" | `[VERIFY: source for the statistic]` |
| The author asks for "a relatable story" and supplied none | Deliver the post anyway. Build relatability from what is real: the author's numbers in their real order, or the reader's situation as a plain condition from the material ("if your containers start cold on every job"). Write no scene, character or "Imagine ..." passage: a hypothetical told as narrative is an invented anecdote. Write a labelled hypothetical only when the author asked for one, and label it inside the post | `[ASK AUTHOR: a real moment when ... (what kind of moment, where it would go)]`; say that the post has no story slot filled |
| The author supplied a command or code sample they did not say they ran, or you wrote one | Show it only if the post needs it, give no output as observed, and say plainly that it was not run here ("This command was not run for this post.") when a reader could assume it was | `[UNTESTED]` naming the snippet |
| The post needs a link, handle, screenshot or testimonial that was not supplied | Leave it out and write the sentence so it still works; never write a URL, handle, quote or "customer said" from memory | `[ASK AUTHOR: link]` (or image, quote), saying where it would go |
| The post needs a call to action, deadline or sign-off that was not supplied | End on the last concrete point | `[ASK AUTHOR: ...]` stating what was not given |
| The notes hold one main idea plus unrelated tangents | Build the post on the one takeaway | "Left out" in the reply, one line per tangent; a short labelled secondary item only if the author wants one |
| Two pieces of evidence conflict | Show both figures, each attributed to who gave it, with the condition that explains the difference when the material gives one; otherwise say plainly that the material does not settle which holds. Compute nothing from either. Omitting both is not showing them: a post that drops the contested figures hides the disagreement | `[ASK AUTHOR: which figure is current?]` |
| Status, availability or a date is unclear | State what the notes say, at that strength ("in beta", "planned") | `[VERIFY: availability]` |

Exception: the author asks for a draft to edit, or for slots to fill. Then markers may stay in the post, and the reply says so. Author-facing artifacts shown with the post (candidate openings, a brief, a change note, a left-out list) are working material and live in the reply, never inside the post text.

## Rules

- **Start from the reader, not from the topic.** A post about "our caching layer" has no reader; a post for "a developer whose p95 doubled after adding a cache" does. Exception: a personal essay may start from the author's question when the reader is a general audience that follows the author.
- **Open on something the reader can see.** An artifact, number, scene or sharp claim lets the reader judge the piece in one line. Warm-up sentences make the reader do that work for you. Exception: when the artifact is meaningless without a premise (a stack trace for a newcomer), give one line of context first.
- **Proof over adjectives.** Replace "powerful", "seamless", "game-changing" with the fact that would justify the word. If no fact exists, delete the adjective; do not manufacture the fact. Exception: a subjective judgment the author genuinely holds can stay as clearly their opinion.
- **Author experience comes only from the author.** Never write "last week a client told me", "in our production tests", or a number that the material does not contain, even as an illustration; an invented scale value, rating or count ("a 2 versus a 9") and a figure computed from supplied ones (a difference, ratio or percentage the notes do not state) both count. A difference or ratio the material itself states ("a gap of three sites") is a supplied figure: keep it with its caveat. Give the supplied pair and let the reader compare. Likewise add no opinion, doubt or warning in the author's voice that the notes do not hold ("I would be careful about calling this a win"); the notes' own caveats are the only ones. A hypothetical scenario told as a story ("Imagine a team that...", "Picture a container that...", "Say a developer...") is an invented anecdote with a disclaimer, and it is also a scenario opener; do not use it to open or carry a post. Where a real moment belongs, write the post without it and ask for it in the reply. Write an illustration only when the author asked for one or an explanation cannot work without it; then label it as hypothetical in the post itself, keep it to the mechanism with no named people or invented figures, and never present it as something that happened. Exception: stating the reader's situation as a plain condition taken from the material ("if you run flags in short-lived containers") is not an anecdote.
- **The post reads as finished.** Unless the author asked for a draft to edit, the post holds no `[ASK AUTHOR]`, `[VERIFY]` or `[UNTESTED]` marker, no bracket placeholder ("[add a number here]", "[link]", "[Name]"), no `[source: ...]` tag and no process narration ("as requested", "I kept this short", "I ran a scan", "per your notes"). Missing proof is handled as in [gaps in a published post](#gaps-in-a-published-post). Questions, assumptions, alternatives and left-out items go to the reply. Reason: a published post with a blank in it is unfinished, and a note to the author in a feed is read as the author's own words. Exception: the author asked for a draft to edit, or for a template with slots; then markers may stay and the reply says so.
- **Select for the story; match the example.** Keep the facts that move the piece and the reader cares about; leave lab detail (file names, flags, internal codes, every intermediate count) in the notes unless the reader would use it. Selecting is not inventing, and a kept figure keeps its value. When the author points to an earlier post or a sample, match its length, voice and level of detail.
- **Count the example, then write to that count.** When the author points to an earlier post or a sample to match, measure it before writing: its words, its paragraphs, whether it has headings, lists or bold, how it opens and closes, and how much detail one point carries (dates, figures and names per paragraph). That is the budget. Stay within about a fifth of its length unless the request states a length, keep its paragraph count give or take one, use no heading, list or bold it lacks, and open and close the way it does. Material that does not fit stays in the notes, the facts this reader needs least going first. Count the draft again before handing over and trim when it is over. Reason: a post half as long again as the last one does not match it, however close the voice.
- **Structure by job, not by template.** A how-to wants ordered steps, an argument wants claim then reasons then the strongest objection, a story wants the real sequence. A fixed formula (hook, three bullets, question) makes unlike pieces look alike and drains the specific content. Exception: a recurring newsletter benefits from a stable skeleton, because the reader returns for it.
- **Formatting is proportional to length.** A post, email or note under about 400 words needs no headings; a 2,000-word guide needs them. A first-person narrative or reflective piece of up to about 1,200 words usually reads better as continuous prose, because section headings turn a voice into a report; add one only where a reader would jump to a part (a results section, a how-to step). Use a list for parallel items and a table for repeated fields; use prose for reasoning and for fewer than about four items. Do not break every sentence onto its own line to fake emphasis. Exception: platforms where short lines are the norm (some feeds); even then keep the breaks for real pauses.
- **Write like the person, not the process.** The post sounds like the author telling a reader, not like an analysis of a topic. Each condition, limit or caveat appears once, beside the claim it limits (the benchmark setup sits next to the number); no later sentence, closing line or thread post repeats it or restates the figure to attach it. The same holds for the lesson: a one-line takeaway the author would say appears once, and no paragraph before it only restates it. Use plain transitions with no signposting ("In this post", "Here's the thing", "The key takeaway", "In summary"), no commentary on the post's own argument ("that difference is worth keeping in view", "what this shows is") and no labels such as "Takeaway:" the author would not write. Keep the author's person and register ("I" stays "I", "we" stays "we"; a plain sentence is not promoted to platform copy such as "available to every team to submit and track"). Let sentence length follow content: a finding that stands on its own gets its own sentence, and a figure stays in one sentence with its condition even when that runs long. Once commentary is cut, the risk is the opposite: separate facts merged into a run of same-length sentences, so split at real clause boundaries where one sentence carries two findings. Never chop sentences or add fragments for effect; an author's own sample sets the rhythm. Reason: readers leave posts that sound assembled, and a limit repeated three times reads as defensive. Exception: a stable newsletter skeleton or a platform convention; faithfulness rules are unchanged, so every condition, status and qualifier still appears once where it applies.
- **A title or hook is a promise.** Say what the piece delivers, with the specifics the reader would search or care about. A curiosity gap is fine only if the piece closes it. If the best title overstates the content, change the title or change the piece.
- **Endings stop on content.** A recap repeats what the reader just finished; an aphorism claims a significance the piece should have shown. Exception: a long guide can end with a short "where to go next" or a checklist that adds a usable artifact.
- **Platform guidance is current practice, not ranking science.** Length bands, fold points and posting habits drift. Present them as things to check, and do not claim that a format, link placement or hashtag count boosts distribution. Write for the reader; adjust only for display limits and conventions.
- **Honest framing.** Name a real limitation when it is relevant; do not stage fear, urgency or vulnerability the material does not support. Exception: none for fabricated stakes; a real deadline or a real risk is fair to state plainly.
- **Nothing added at the edges.** The call to action, link, hashtag set, sign-off line, discount, deadline or "reply to this email" prompt must come from the author's material or request. If the post needs one and none was given, end on the last concrete point and ask in the reply. This holds hardest for launches, newsletters and email sequences, where stock CTAs, fake urgency and invented testimonials are the usual fabrications.
- **One post, one job.** Material that does not serve the takeaway is cut or moved to its own post, and the reply says what was left out. A post that touches four topics proves none of them.
- **Length follows the request, filled from the material.** A stated length is a target: land within about 15% of it. Notes or an outline are compressed; each point expands into what it meant in practice, how it was done, what the author saw and why it matters to this reader, all drawn from the material, until the piece reaches the target. Fill only with the author's material and reasoning, each point stated once, beside the claim; never with a restated lesson, a scene, an invented example or a question the author did not raise. When the material truly cannot reach the target without that, write what it carries and say in the reply how much shorter it is and what material would fill the rest. Reason: a piece at two-thirds of the asked length is a different piece, and padding is where repetition and invention enter.
- **State what the material states.** Availability, status and dates of a launch are as the author gave them: do not present a beta as general availability or a plan as shipped. If status is unclear, state it at the weaker strength and put the question in the reply.
- **Search and answer-engine visibility follows clarity.** Answer the query in plain words early, use descriptive headings, label units and versions, date what ages. One version serves people and machines; keyword repetition and machine-only variants help neither.
- **Other languages.** The lexical pattern lists in the sibling skills are English-only. For Vietnamese or any other language, apply the structural, evidence and preservation checks here and say plainly that word-level lists do not transfer. Keep technical terms, commands and code as the community writes them. When adapting from an English source, rewrite in the target language's own rhythm instead of translating sentence by sentence; carry over numbers, units and qualifiers unchanged, and avoid calquing English openers and closers.

## Output

Return, in this order:

1. **Assumptions** (one line, in the reply): reader, takeaway, channel, any assumed length.
2. **The post**, ready to paste, in the target format and free of markers and notes. For long pieces include the title and, if wanted, two alternative titles. When the post is saved to a file, the file holds the post only; when there are open questions, also write `open-questions.md` beside it, numbered, each as a marker line with what it blocks and what the post says meanwhile.
3. **Open questions** (in the reply): every `[ASK AUTHOR: ...]`, `[VERIFY: ...]` and `[UNTESTED]` item, each with what is needed to resolve it and how the post handles the gap now. If none, say "No open questions."
4. **Left out** (when material was cut or did not fit): one line per item and the reason.
5. **Change note** (Repair and Repurpose only): short list of what changed and why, including anything deliberately left alone.

Deliver a draft in the sense that publishing and timing are the author's: do not say a post was published, scheduled or sent. "Draft" does not mean markers in the text.

For Repurpose mode, give each channel as a labelled block with its own opening and ending, plus the carried-over core claim in one line and any publishing constraints still unresolved. The core-claim line and the constraints are reply notes, not part of any channel's post text; when the versions are saved to one file, keep them in the reply or in a clearly separated author-facing section that is not copied into a post.

## Examples

Opening, before and after (the figures are illustrative; real ones come from the author's notes):

- Before: "In today's fast-moving world of software, performance matters more than ever, and caching is a key technique."
- After, with the numbers in the notes: "Our p95 went from 420 ms to 95 ms after we changed one cache setting. Here is the setting and what it broke."
- After, when the notes give no numbers: "We changed one cache setting and p95 dropped. Here is the setting and what it broke." The reply asks: `[ASK AUTHOR: p95 before and after, and how it was measured]`.

Ending, before and after:

- Before: "In conclusion, caching is powerful when used wisely. What do you think?"
- After, when the notes give the TTL: "If you run the same workload, set the TTL to 60 seconds and watch the miss rate for a day before you trust it. I would like to hear what your numbers look like."
- After, when the notes give no TTL: "Watch the miss rate for a day after you change the setting before you trust it." The reply asks: `[VERIFY: recommended TTL value]`.

The reply-seeking sentence in the first ending is acceptable only if the author does want replies; otherwise stop one sentence earlier.

## Reference files

| File | Load when |
|---|---|
| [references/post-types.md](references/post-types.md) | Choosing the spine for a how-to, opinion, story, post-mortem, announcement, list, explainer, comparison or newsletter issue; stress-testing a thesis; framing honestly for the reader. |
| [references/platforms.md](references/platforms.md) | Fitting a piece to LinkedIn, X, Threads, Bluesky, Instagram, forums, Xiaohongshu, WeChat, email or a blog; checking limits and conventions. |
| [references/openings-and-endings.md](references/openings-and-endings.md) | Writing or repairing a title, opening, hook, headline or ending; deciding whether context before the artifact is justified. |
| [references/repurposing.md](references/repurposing.md) | Turning one piece into several channel versions, shortening under a limit, or checking that adapted versions still match the source. |
| [references/email-sequences.md](references/email-sequences.md) | Writing a welcome, onboarding, nurture, re-engagement or launch email series, an internal team newsletter, or a single SMS or WhatsApp text the author asked for. |
