Load when: you must decide how strictly to apply the catalog to a given text, the genre is unclear, or the author's sample disagrees with a generic rule.

# Genre calibration

The same sentence can be a defect in one genre and the right choice in another. Calibrate before you judge a candidate. Order of authority, highest first:

1. The user's explicit instruction and scope.
2. The author's own samples (earlier writing they supplied, or the untouched parts of this text).
3. The genre and destination (where the text will be read and by whom).
4. The generic catalog.

A rule lower on the list never overrides one higher up. A habit the author shows in their own samples (dashes, short fragments, "honestly", rhetorical questions, bold) is voice, not slop.

## Choosing a profile

If the user names a destination, use it. If not, infer from the text only, state the profile in one line, and treat borderline matches as judgment calls rather than forcing edits.

| Signal in the text | Profile | Scanner flag |
|---|---|---|
| Chat message, DM, comment thread, quick note | casual | `--profile casual` |
| Article, newsletter, report, email to a client, résumé, cover letter, executive summary | professional | `--profile professional` |
| README, API docs, tutorial, changelog, design doc, commit or PR text, code-adjacent prose | technical | `--profile technical` |
| Paper section, abstract, thesis chapter, grant text | academic | `--profile academic` |
| Short story, scene, poem, personal essay | creative (no scanner profile; read, do not scan) | none |
| Quotation, citation, epigraph, dialogue someone said | protected (leave alone) | skipped automatically |
| Code, configuration, tables, frontmatter, link targets | protected (leave alone) | skipped automatically |

Profiles change how strictly a pattern applies. A family a profile does not report is not applicable there; another profile or a general voice request cannot switch it back on for that text.

## What each calibration changes

### Casual and social
- Care about: chat residue, placeholders, leaked markup. Those are never part of a casual message.
- Relax: nearly everything else. Fragments, "honestly", a dash, one emoji at the end of a line, a single "worth a look" in a DM are normal speech.
- Short posts: platform conventions rule. One or two meaningful hashtags are fine; a row of generic ones is stuffing. A reply-farming closing question is a candidate; a question the author really wants answered is not.
- Do not add casualness the author did not use. Forced slang is its own fingerprint.

### Professional (articles, reports, summaries, career documents)
- Full catalog applies, with judgment. Promotional wording and significance inflation matter most because they cost credibility with readers who decide something from the text.
- Investor, client and hiring readers punish unsupported superlatives hardest; a single unevidenced "world-class" deserves a look even when it is alone.
- Keep real lists (steps, comparisons, options). Flag bullet lists that are really prose in disguise; convert only if the scope allows restructuring.
- Salutations and sign-offs in letters and emails are conventions, not tells.

### Technical (docs, READMEs, changelogs, commit and PR text)
- Imperative fragments ("Add support for nested queries"), bare parameter lists and repeated domain terms are the register. Do not vary them for rhythm.
- Engineering vocabulary keeps its exact senses: robust, seamless, comprehensive, ecosystem, leverage as a noun, harness in "test harness", gate and gating. Flag only ornamental or unsupported uses.
- "May" and "could" are accurate hedges when behavior really is conditional; keep them.
- Keep numbered steps, parameter tables, and code samples exactly. Do not rewrite code, commands, paths, flags or config keys unless the user asked.
- Describe current state, not the history of edits ("now works", "changed from") in reference text; changelogs are the exception, because history is their job.

### Academic and scientific
- Preserve hedges, qualifiers, scope, statistics and citations exactly. A pattern fix must never raise or lower certainty or turn association into cause.
- Keep terms of art: "robust standard errors", "significant" in the statistical sense, passive voice where the actor is irrelevant, formal connectors that mark real logic.
- Candidates that matter most: boilerplate openers ("In recent years, X has attracted growing attention"), coverage claims without content ("extensive experiments"), anthropomorphic verbs for models ("understands", "reasons"), significance language, trailing commentary riders, vague attribution without a citation.
- Plain repetition of a defined term, first person "we", short declaratives and contrast sentences that carry a measured finding are norms, not defects.
- A style guide that the venue requires (including its dash and contraction rules) outranks the generic catalog for typography. Mechanics follow the guide; the habit may still be noted.
- For ML paper sections, use `academic-writing` if installed; otherwise `structured-drafting` for structure plus `evidence-grounded-writing` for claims.

### Fiction and creative writing
- Do not scan or normalize. Fragments, repetition, triads, rhetorical questions, odd rhythm and deliberate cliché can all be craft.
- Still remove chat residue and unfilled placeholders, and report fabricated-sounding generic description only as an observation: "this passage could belong to any story; the draft gives no detail specific to this one." Do not invent detail.
- Default mode is `detect` unless the user asks for edits; creative voice is easy to flatten.

### Quoted and attributed material
- Anything inside quotation marks, block quotes, citations, epigraphs, transcripts or example sentences that are explicitly shown as bad writing is not the author's prose. Do not flag it as a defect and do not edit it.
- If the quoted material contains a pattern, you may note it as an observation ("the quotation itself uses X; left as is"). Never "fix" a quotation.
- Illustrative samples inside a discussion of writing (such as "a model might write...") are exempt.

### Code, markup and structured data
- Fenced and inline code, command lines, paths, URLs, link targets, YAML or TOML frontmatter, HTML comments, table cells that hold data, LaTeX commands (`\cite`, `\ref`, math) are protected.
- Prose inside Markdown, HTML or LaTeX is editable; markup around it is not. Keep heading count and nesting unless restructuring was requested.
- Refuse in-place prose edits on a source file, config or data file; edit prose only in prose documents.
- Line breaks: keep the source layout unless the destination clearly renders single newlines visibly and the user wants unwrapping.

## Non-English and translated text

- The lexical lists are English only. For Vietnamese, Chinese and other languages, do not apply word lists; apply the structural, evidence and preservation checks, and say that lexical lists do not transfer.
- Structural patterns do carry over in spirit: stock openers that announce rather than state, denied-then-asserted contrasts, empty closers, vague attribution, fake vulnerability, claims without evidence. Judge them by reading.
- Translated or second-language drafts often show stacked passives, long nominalized phrases, and mechanical connectors copied from the source language. Treat these as clarity edits, not as signs of machine writing. In technical and academic text, necessary passives and formal connectors stay.
- If you cannot read the language well enough to judge, say so and limit the output to what you can verify (residue, placeholders, preservation).

## Reading the evidence honestly

- A pattern list is a writing-quality signal, not proof of who wrote the text. Rushed human writing, second-language writing and house-style prose trigger the same patterns. Do not state or imply that a text was or was not written by a model. If the user asks for a verdict on authorship, decline the verdict and offer the writing-quality findings.
- Do not treat a clean scan as proof of human writing or a hit count as proof of machine writing. Counts compare drafts of the same piece, not people.
- A pre-chat era date does not prove or disprove anything on its own either way; ignore date arguments.
- Several independent signs in the same passage justify an edit more than one weak sign. A single weak sign (curly quotes, one dash, one transition) is usually not worth touching.
- The goal is a text that is accurate, clear and recognizably the author's, never a text engineered to dodge a classifier. Do not add roughness, typos or invented asides to change how a text reads.
