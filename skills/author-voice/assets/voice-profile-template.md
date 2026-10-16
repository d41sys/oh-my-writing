# Voice profile: <author or project name>

<!-- Copy this file to a place you own, for example voice-profile.md. Delete the guidance comments
once the profile is filled in. Keep the finished profile short: one line per trait, each traceable
to a sample. A voice profile holds style only. Do not store biography, opinions or facts here.
This file is author-facing: open questions may stay in it as `[ASK AUTHOR: ...]` lines. Text drafted
from it for a reader never carries them. -->

## Header

| Field | Value |
|---|---|
| Author | <name or handle> |
| Profile id | <short label, for example "newsletter" or "work email"> |
| Built on | <YYYY-MM-DD> |
| Last updated | <YYYY-MM-DD> |
| Confirmed by author | <yes, YYYY-MM-DD / no> |
| Confidence | <low / medium / high, with the reason: sample count, words, spread> |
| Language and locale | <for example English (UK spelling), or Vietnamese> |
| Intended genres | <where this profile may be applied; do not apply it elsewhere without asking> |

## Sample set

<!-- One row per sample actually used. Public and private/casual voice go in separate tables
or are tagged in the Set column. Samples left out go in the second table with the reason. -->

| Sample | Date | Channel and audience | Set | Words | Notes |
|---|---|---|---|---|---|
| <file or title> | <YYYY-MM> | <blog post for peers> | <public> | <n> | <self-written, lightly edited> |

| Excluded | Reason |
|---|---|
| <file or title> | <ghost-written / heavily edited by others / AI-drafted / quoted text / too old / wrong channel> |

Measured with: <tool and command, for example `voice_stats.py` on the public set, or "read by hand">

## Measured traits

<!-- Numbers come from a script or a hand count. Say which sample set they describe.
They are observations, not targets. Strength: strong = holds in nearly every sample and in
every set; moderate = holds in about half the samples or in one set only; weak = seen in one or
two samples, or numbers that swing widely. Omit anything weaker than weak. -->

| Trait | Observation | Evidence | Strength | Holds in |
|---|---|---|---|---|
| Sentence length | <mean 14, median 12, stdev 8; short sentences between longer ones> | <voice_stats public set: mean 14.2, stdev 8.1> | <strong> | <all sets> |
| Paragraph shape | <2 to 4 sentences, point first> | <stat: 3.1 sentences on average; sample-02 para 3> | <moderate> | <public> |
| Person and address | <first person singular, speaks to "you"> | <I 22 and you 18 per 1000 words> | <strong> | <all sets> |
| Contractions | <uses them freely> | <contractions 31 per 1000 words> | <strong> | <all sets> |
| Punctuation | <rare semicolons, parentheses for asides> | <semicolon 0.4, parenthesis 6 per 1000 words> | <moderate> | <public> |
| Formatting | <prose with occasional short lists> | <bullet ratio 0.15> | <weak> | <public> |
| Fragments and rhythm | <runs of very short sentences, rarely a long one> | <stat: median 6, max 14; post-01 opening run> | <moderate> | <public> |
| Capitalization | <conventional> | <all sample titles and sentences> | <weak> | <public> |

## Observed moves

<!-- Habits that need reading, not counting: openings, closings, hedging, humor, jargon,
transitions, how evidence appears, recurring phrases. Quote the sample; keep quotes short and
name the file. -->

| Move | What the author does | Evidence (quote and sample) | Strength | Holds in |
|---|---|---|---|---|
| Opening | <starts on the concrete case, not the topic> | <"The build broke on Tuesday." (post-03)> | <moderate> | <public> |
| Closing | <ends on the last point, no summary> | <post-01, post-02, post-04 end mid-argument> | <strong> | <public> |
| Hedging | <hedges once, with the reason> | <"probably, since I only ran it twice" (post-02)> | <moderate> | <all sets> |
| Humor | <dry, one aside per piece> | <"(it did not)" (post-05)> | <weak> | <public> |
| Recurring phrase | <"in practice"> | <3 of 6 samples> | <moderate> | <public> |
| Compression | <compressed: terms defined in passing> | <post-02 "a cache, meaning the copy we keep nearby"> | <weak> | <public> |
| Claim style | <number first, then the claim> | <post-01, post-03, post-04> | <moderate> | <public> |
| Call to action | <none; pieces end on the last point> | <absent in 5 of 5 samples> | <moderate> | <public> |

## Splits and conflicts

<!-- Where samples disagree, record the split. Do not average it away. -->

| Trait | Split | Samples on each side | Handling |
|---|---|---|---|
| <Formality> | <contractions everywhere in chat, none in proposals> | <chat-01..04 / proposal-01..02> | <treat as two channels; see Channel notes> |

## Stated preferences, not observed

<!-- Things the author says they want but the samples do not show. Keep them out of the
tables above. Apply only when the author asks for them for a given piece. -->

| Preference | Said on | Samples show | Decision |
|---|---|---|---|
| <"I want to sound less formal"> | <YYYY-MM-DD> | <formal in 5 of 6 samples> | <pending: ask the author per piece> |

## Declared rules and terminology

<!-- Rules the author states outright, not traits read from samples: words they refuse, preferred
terms and casing, punctuation they never use. Keep each short, dated, and in the author's words.
Style only: no product facts, figures or biography. -->

| Rule | Said on | Applies to | Samples agree? |
|---|---|---|---|
| <"never use em dashes in client emails"> | <YYYY-MM-DD> | <client email> | <yes, 0 in 4 samples> |

## Channel notes

<!-- The identity (stance, vocabulary, moves) carries across channels. The register (length,
formality, layout) changes. Write only what a sample supports; mark the rest as extrapolated. -->

| Channel or audience | Register | What changes from the core voice | Supported by |
|---|---|---|---|
| <Blog for practitioners> | <conversational, 900 to 1500 words> | <none; this is the core> | <post-01..05> |
| <Email to clients> | <direct, short> | <no asides, fewer contractions> | <email-01..03> |
| <Channel with no samples> | <unknown> | <extrapolated; confirm before relying on it> | <none> |

## Never-do zones

<!-- Only things the author avoids that the samples show across several samples (absence needs
enough samples to mean something), or that the author explicitly asked for. Say which. -->

| Zone | Basis (observed in N samples / requested by author) | Notes |
|---|---|---|
| <No exclamation marks> | <observed in 6 of 6 samples> | <including celebratory posts> |

## Language and locale notes

- Spelling and date conventions seen: <for example "organise", "15 March 2026">
- Address forms and register markers (languages that have them): <for example Vietnamese: "mình" with peers, "em" to seniors>
- Measures that do not transfer to this language: <for example English contraction and pronoun counts>

## How to apply

- Follow strong traits; follow moderate traits unless the content or reader argues otherwise; ignore weak traits unless asked.
- Traits are tendencies, not quotas. Do not add a feature to hit a number.
- Facts, experiences, opinions and credentials come from the author's material, never from this profile.

## Changelog

<!-- Newest first. Record the date, the samples added or removed, and what changed. -->

- <YYYY-MM-DD>: built from <n> samples (<set names>); <confidence>. Open questions for the author are marked `[ASK AUTHOR: ...]`.
