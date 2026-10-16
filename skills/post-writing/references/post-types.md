Load when: choosing the spine of a public post, stress-testing an opinion, shaping a story from the author's notes, writing an announcement or newsletter issue, or deciding how to frame a claim for the reader.

# Post types

Each type below names the reader's job, a spine that serves it, the material it needs from the author, the usual way it goes wrong, and a quick check. Spines are starting shapes. Reorder or drop a beat when the material says so. If the piece fits two types, pick the one that matches the takeaway and borrow only the beats you need from the other.

## Choosing a type

| The reader wants to... | Type |
|---|---|
| do something and get a result | How-to post |
| decide whether a claim is right | Argument or opinion |
| understand what happened and why | Story, reflection, post-mortem or devlog |
| know what is new and whether it matters to them | Announcement |
| collect useful items | List with depth |
| understand a concept | Explainer |
| choose between options | Comparison |
| keep up with one source over time | Newsletter issue |

For documentation pages for a product or tool (tutorials, how-to guides, reference), use `technical-docs`; a how-to post is the blog-style, conversational, single-sitting version.

## How-to post

- **Spine:** the outcome the reader will have, prerequisites, ordered steps each with one action and the result to expect, the common failure and its fix, one next move.
- **Material needed:** commands, settings or actions the author actually ran, with the expected output. Versions and environment. A command or snippet the author did not run, or that you wrote, carries `[UNTESTED]`, and its output is never described as seen.
- **Failure mode:** a promise of "easy" or "five minutes" with steps that were never run; steps that skip a prerequisite; explaining theory before the first step.
- **Shortest path to a first result.** List every step, then separate what the reader must do from what can wait (extra settings, optional features) and move the optional part after the first working result. Never cut a security step, an authentication prerequisite or a consent or safety requirement to make the path shorter.
- **Check:** could a reader who knows nothing but the prerequisites reach the result? Is every command real and copyable, or marked `[UNTESTED]`? Is the version stated?

## Argument or opinion

- **Spine:** the claim in the first lines, the reader's likely objection, the author's reasons ordered by strength, the strongest objection stated fairly, what would change the author's mind, what the reader can do with the view.
- **Stress-test the claim before drafting.** Four moves help find a claim worth writing:
  - Invert it. If the opposite is defensible, the claim has something to argue against; if it is absurd, the claim may be too obvious.
  - Chase the premise. Ask what has to be true for the claim to hold; the premise is often the more interesting subject.
  - Chase the friction. Find where readers disagree, worry or get confused about the topic.
  - Flip the definition. Ask what a familiar term really means in practice.
- **Material needed:** the author's actual reasoning and the evidence it rests on. An opinion piece with no experience or evidence behind it is a slogan; ask for the basis.
- **Failure mode:** a straw opponent; a "not X, but Y" frame used for every point; confident tone over thin support; manufactured outrage.
- **Check:** is the strongest objection present and answered? Could a reader who disagrees tell exactly where they disagree?
- **Fairness.** When criticizing a practice, aim at the practice, not at people, and say what you are not attacking if that is easy to misread. If the author's own product or team does the same thing, say so.

## Story, reflection, or personal essay

- **Spine:** one specific moment, what was at stake, what happened in order, what turned, what the author makes of it, how it connects to something larger than the author.
- **One idea per essay.** If two lessons compete, there are two essays. Choose the one the material supports best.
- **Material needed:** real details from the author: time, place, people (with permission), what was said or tried, what went wrong. Only the author can supply these. Without them, ask or stop at an outline.
- **Failure mode:** inventing scenes to make the opening vivid; a lesson announced rather than shown; a tidy moral that the events do not support; vulnerability performed for effect.
- **Ending.** An earned insight or an honest open question. Do not close with a call to action unless the author wants one.
- **Check:** is every scene detail from the author's notes, with nothing added for atmosphere ("a rainy Tuesday")? Does each scene carry some uncertainty that makes the reader want the next paragraph, and is a scene without it cut? Is there exactly one idea? When the piece reconstructs a past event the notes only partly record, label what the notes state and what you infer, and never present the inference as remembered.

## Post-mortem or devlog

A blameless incident post-mortem document (timeline, causes, action items, written for the team) is `report-writing`; this type is the public post that tells the story.

- **Spine:** the starting state, the failure or bottleneck as it appeared, the wrong hypotheses and why they seemed right, the root cause, the fix, the evidence that it worked, what changes now.
- **Material needed:** timestamps, logs, graphs, the actual rejected alternatives. Keep the cause chain exactly as the author gives it.
- **Failure mode:** a smoothed story that drops the dead ends; a blameless-sounding paragraph that hides who decided what; summary numbers with no measurement conditions; invented causes for a step the notes do not explain.
- **Compression rule.** When trimming, cut descriptive background first and keep causal links and the numbers that prove the fix. Move long logs and tables to an appendix or a repository link.
- **Inferred versus stated.** If the notes jump from one step to the next without a reason, ask for the reason. A reconstruction of motives, or a root cause the author only suspects, is written as the author's belief ("we think"), not as established fact.
- **Check:** can a reader see why each decision was taken and what the alternatives were?

## Announcement

Release notes and changelogs are `technical-docs`; this type is the announcement post that tells readers why the release matters to them.

- **Spine:** what is new in one plain sentence, who it is for and what problem it solves, how it works or what changed, proof (a number, a demo, a link), limits and status (beta, gated, unsupported cases), how to try it, where to learn more.
- **Material needed:** version, date, availability, real benchmark or usage figures with conditions, honest status.
- **Failure mode:** excitement in place of information; the change buried under thanks and context; features without the problem; claims of "revolutionary" with no number; leaving out known limits.
- **Check:** after the first paragraph, does the reader know what changed, whether it affects them, and where to go?
- **Link placement.** Put the link where the reader needs it: after the sentence that makes them want it. Check the channel's current conventions before moving links elsewhere (see [platforms](platforms.md)).
- **Product introduction versus design story.** An introduction serves a reader deciding whether to adopt: problem, how it works, evidence, a working first step. A design story serves a reader who wants to understand a decision: starting state, the failure, rejected options, the mechanism, verification. Pick one; mixing them gives a brochure that pretends to be a story.
- **Launch hygiene.** State one core claim up front and have every supporting point prove that claim. Say what is not shipping or not included when readers could assume otherwise (for example what stays local or private). If a likely misreading exists (a rename mistaken for a pivot, a preview mistaken for general availability), name and reject it in one sentence. Publish only what the author says is live; otherwise `[VERIFY: availability]`.
- **A set of posts around one launch.** The announcement, the short-text post and the professional-network post each carry the same claim and the same numbers. Each version stands alone and is not a shortened copy of another. The call to action, the link and the date come from the author.

## List with depth

- **Spine:** a title that states the count and the deliverable, a one-line selection criterion, items each with a claim, a reason and one concrete detail, an ordering the reader can understand (by importance, by sequence, by difficulty), a short close.
- **Rules:** do not pad to reach a round number. The count in the title must match the items. Items must not overlap; if two collapse into one idea, merge them.
- **Failure mode:** a list of platitudes with no detail; items that are really one point restated; ranking with no stated criterion.
- **Check:** could each item stand alone as a short post? Does each have something the reader can use?

## Explainer

- **Spine:** the question the reader has, the short answer, the mental model or one analogy, the mechanism shown through a concrete case, where the model breaks, where to go deeper.
- **Rules:** one analogy, stated with the point where it fails. Define the concept at first use. Order the passages so each depends only on what is already explained.
- **Failure mode:** several analogies that conflict; jargon introduced after it is used; the short answer withheld to create suspense in a piece the reader came to for an answer.
- **Check:** after reading, could the reader explain it to someone else?

## Comparison

- **Spine:** who is choosing and what they need, the criteria, each option measured on the same criteria, a table when fields repeat, the verdict by use case, what the author did not test.
- **Material needed:** real measurements or direct use, with versions and test conditions. Disclose any relationship with an option compared.
- **Failure mode:** only the dimensions where the favoured option wins; vague "faster / slower" in table cells; a verdict that ignores the trade-offs shown.
- **Check:** are the conditions of each measurement stated? Would the author be comfortable if the alternatives' maintainers read it?

## Newsletter issue

- **One main idea per issue.** Everything else is supporting or labelled as secondary. Subscribers return for a reliable kind of value, so a stable skeleton is an asset.
- **Spine:** a subject line that works on its own, a first screen that already carries substance (the point, a conflict or an artifact), the main piece, optional short secondary items with clear labels, one primary action, a sign-off in the author's voice.
- **Cadence.** Pick a rhythm the author can sustain and keep it. A consistent sender name and a consistent format help recognition; missing a promised cadence costs more than a lighter issue.
- **Section labels.** Use them where they help a skimming reader find parts of a long issue; skip them in a short one.
- **Subject line.** Describe the content truthfully. The first sentence of the body should deliver on it. No fake "Re:" or "Fwd:", no invented urgency.
- **Links.** Descriptive anchor text, not "click here". One primary link or action; secondary links are fine if they are clearly secondary.
- **Format.** A single column, short paragraphs, essential images only. Text in images must also appear in text, and images need alt text.
- **Failure mode:** diary-style warm-up before the point; a link dump with no commentary; every issue structured differently; a roundup that only repeats headlines.
- **Check:** if the reader only sees the subject and the first screen, do they know what they will get? Does the issue have one main idea?
- **Internal or team newsletter, and series.** See [email sequences](email-sequences.md).
- **Compliance.** Marketing email has legal requirements (consent, an unsubscribe route, sender identity) that vary by region. Flag `[VERIFY: applicable email rules]` and leave them to the sender's platform and counsel; do not state legal specifics.

## Reader psychology, used honestly

These ideas shape how to present a point. They are not licences to manipulate.

- **Existing beliefs.** Readers discount what contradicts what they already believe. Start from what the audience holds, show where the new point connects, and give the evidence. Attacking the belief head-on rarely persuades.
- **The curse of knowledge.** Experts skip steps they no longer see. Test the draft on someone outside the field, or imagine reading it with only the prerequisites you listed.
- **Admit a real limit.** Naming one genuine weakness or trade-off makes the rest more believable. Do not invent a flaw as a rhetorical device.
- **Immediate benefit.** Say what the reader gets now before what they might get later. Describe outcomes, not feature names.
- **Concrete cases.** A specific case is easier to picture than a category. The case must be real, from the author's material. A hypothetical told as a story is an invented case; use it only when the author asked for one, and label it inside the post.
- **Framing.** The same fact can be framed as 90% success or 10% failure. Pick the frame that is accurate and useful for the reader's decision. If both are accurate, prefer the one that helps them judge.
- **Loss and risk.** People weigh potential loss heavily. Describe real risks plainly with their real likelihood; do not manufacture fear to move the reader.
- **Friction.** Say what switching or trying costs: time, migration, learning. A promise of "no effort" for complex work damages trust.
- **Diagnose what stops the reader before framing.** What should the reader do, what do they believe now, where are they in deciding, and what blocks them? When readers do not act, look first at the situation or the process (too many steps, an unclear next action) before blaming the reader.
- **One recommended path first.** When there are many options, give the recommended default, then the variations.

## Differentiation check

Replace the author's or product's name with a competitor's. If the sentence stays true and nothing changes, it is generic. Fix it with something specific to this author or product: a measured figure, a mechanism, a constraint. If the material has nothing specific, mark `[ASK AUTHOR: what is specific to this?]` rather than inventing a distinction.
