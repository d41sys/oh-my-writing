Load when: you need the detail behind a candidate (what the pattern is, what it costs, when it is fine, how to fix it) or you are auditing by reading without the scanner.

# Pattern catalog

Every entry is a signal to inspect, not a rule to enforce. A pattern becomes a finding only after you have read the sentence, checked the genre (see [genre calibration](genre-calibration.md)) and compared it with the author's own samples. The lexical entries are English only; for other languages use the structural, evidence and preservation checks and say that word lists do not transfer.

Fix principle for all entries: subtract, or restate the point from the author's material. If the sentence needs a fact the text does not contain, mark `[ASK AUTHOR: ...]` or ask. Do not swap one stock word for another; that hides the symptom and keeps the emptiness.

Scanner names appear in parentheses where `scripts/slop_scan.py` has a matching check.

## 1. Lexical inflation

Words that rose in machine-assisted prose and often stand in for a plainer or more exact word.

### Showy stock vocabulary (`delve`, `tapestry`, `pivotal`, `intricate`, `showcase`, `foster`, `unveil`, `embark`, `meticulous`, `nuanced`, `paramount`, and similar)
- Looks like: "delves into the intricate tapestry of", "fosters a pivotal shift", "meticulously crafted".
- Cost: the reader meets a flourish where a fact should be; trust drops with each one.
- Fine when: the literal sense applies (a tapestry on a wall, foster care, a real unveiling), the author's samples use the word, or it sits in a title or quotation.
- Fix: use the plain verb or noun ("examines", "encourages"), or cut the clause if it adds nothing.

### Inflated verbs for "use" (`leverage`, `harness`, `utilize`, `facilitate`, `streamline`, `empower`, `elevate`)
- Looks like: "leverages advanced techniques to harness data".
- Cost: longer, vaguer, and hides who does what.
- Fine when: the word is the field's exact term (financial leverage, a test harness, a harness for a climber, facilitation in a workshop sense).
- Fix: "uses", "applies", "runs on"; name the technique.

### Soft-compliment adjectives (`seamless`, `robust`, `comprehensive`, `holistic`, `groundbreaking`, `cutting-edge`, `world-class`)
- Looks like: "a seamless, robust, comprehensive solution".
- Cost: praise without evidence. A reader cannot check "robust" but can check "survives a node failure without data loss".
- Fine when: the term is technical and defined (robust standard errors, seamless session migration, comprehensive test suite with a stated scope).
- Fix: replace the adjective with the property it claims, or the measurement behind it.

### Cluster words (`crucial`, `vital`, `notably`, `particularly`, `enhance`, `insights`, `valuable`, `effectively`, `highlight`, `various`, `diverse`, `essential`)
- Looks like: one paragraph holding "crucial insights", "valuable", "effectively enhances", "various".
- Cost: each is fine alone; together they signal filler and flatten emphasis.
- Fine when: only one or two appear in a long section, or each carries a real distinction.
- Fix: keep the one that carries meaning; state the rest as facts. Treat the cluster as one finding, not four.

### Figurative landscape and journey words (`landscape`, `realm`, `journey`, `navigate the complexities`)
- Looks like: "navigating the evolving landscape of modern work".
- Cost: places a metaphor where the topic should be named.
- Fine when: literal (a landscape photo, a legal realm), or a deliberate image in creative writing.
- Fix: name the actual field, problem or process.

## 2. Empty framing and throat-clearing

Words that announce, introduce or comment on content instead of delivering it.

### Era openers (`era-opener`)
- Looks like: "In today's fast-paced digital world", "In an era where", "ever-evolving".
- Cost: delays the first useful sentence and fits any document on any topic.
- Fine when: a history piece names and dates the era.
- Fix: open on the concrete problem, fact or claim.

### Announcement phrases (`announce-note`, `stock-phrase`)
- Looks like: "It is worth noting that", "It is important to remember that", "The reality is that", "When it comes to", "In terms of", "At the end of the day".
- Cost: the reader is told something matters instead of being shown it.
- Fine when: the next clause is a caveat that changes what the reader should do, or the phrase is ordinary speech in a conversational voice.
- Fix: delete the phrase and keep the claim; recast "In terms of X" as the direct sentence.

### Staged hooks and scenario openers (`staged-hook`, `scenario-opener`)
- Looks like: "Let's dive in", "Buckle up", "Imagine a world where", "Have you ever wondered".
- Cost: performs excitement before delivering content.
- Fine when: tutorials, spoken scripts and fiction where the author's samples work this way and the scenario is then used.
- Fix: start with the content or the concrete scenario itself.

### Audience sweeps (`audience-sweep`)
- Looks like: "Whether you're a beginner or an expert".
- Cost: claims everyone and addresses no one.
- Fine when: the two audiences really get different next steps.
- Fix: name the reader the piece is for, or cut the clause.

### Performed reaction, candor and attention (`stock-reaction`, `lingering-attention`, `hollow-intensifier`, `announced-feeling`)
- Looks like: "What surprised me most", "The line I keep coming back to", "To be honest", "I'm thrilled to announce".
- Cost: borrows the look of a personal response without content.
- Fine when: the author actually had the reaction and the sentence says why; mid-sentence "honestly" in casual voice.
- Fix: open with the reason the detail matters if the text gives it. Never invent a reaction, reason or experience to fill the gap.

### Restated importance (`importance-restated`)
- Looks like: "This matters because", "Here's why this matters".
- Cost: the claim of importance replaces the consequence.
- Fine when: a concrete consequence follows immediately.
- Fix: state the consequence; if the text has none, cut and flag the gap.

### Stock transitions (`transition-opener`)
- Looks like: sentence-initial "Moreover,", "Furthermore,", "Additionally," repeated.
- Cost: adds no logic; the reader senses a template.
- Fine when: the step really is additive and the connector is the lightest way to show it, especially in formal and academic writing.
- Fix: let the sentences connect by content, or use "and", "also", "but".

## 3. Contrast and reveal templates

Sentence shapes that stage a point by denying something nobody said.

### Denied-then-asserted contrast (`not-just`, `about-x-about-y`, `denied-then-asserted`, `split-denial`)
- Looks like: "It's not just a tool, it's a movement." "This isn't about speed; it's about trust." "Not because it was cheap. Because it worked."
- Cost: invents an opponent, then defeats them. It sounds deep and says less than the plain claim.
- Fine when: someone really asserted the denied half and the text says who or what measured it, or two measured options are being compared.
- Fix: state the second half directly, with its evidence. If the denied half was a real misreading, name it once.

### Negation chains and drumbeats (`negation-chain`)
- Looks like: "No setup, no waiting, no fuss." "It didn't ask. It didn't wait."
- Cost: describes by absence and borrows a staccato beat to sound decisive.
- Fine when: compact microcopy beside a button ("Free to start. No card required."), or a list of real exclusions.
- Fix: say what actually happens, in order, from the source.

### Staged reveals and self-answered questions (`staged-reveal`, `self-answered-question`)
- Looks like: "Here's the catch:", "The result? Faster builds.", "Why does this matter? Because...".
- Cost: manufactures suspense around ordinary information.
- Fine when: FAQs, interviews, labelled results ("Result: 42 ms"), or a question a reader really asks.
- Fix: state the point as a plain sentence.

### Crowd foil (`crowd-foil`)
- Looks like: "While everyone else debated, we shipped."
- Cost: makes an unsupported claim about unnamed others.
- Fine when: the rivals or the contrasting position are named and sourced.
- Fix: state what the author did, with the fact the source supports; drop the crowd.

### Mirror slogans (`less-more`)
- Looks like: "Less noise, more signal", "Think different, build better".
- Cost: symmetry stands in for content.
- Fine when: the slogan is the author's own and a brand line.
- Fix: replace with the specific change.

## 4. Puffery and vague attribution

Claims of importance or consensus with nothing behind them.

### Significance inflation (`significance`)
- Looks like: "marks a pivotal moment", "a testament to", "plays a crucial role", "paves the way", "profound implications".
- Cost: promotes a routine fact to history; credibility drops when applied to ordinary events.
- Fine when: the event really was a turning point and the text shows the evidence.
- Fix: name the concrete consequence, or cut.

### Promotional wording (`promo-wording`, `unlock-potential`)
- Looks like: "game-changing", "breathtaking", "revolutionary", "unlocks the full potential".
- Cost: reads as advertising in prose that is supposed to inform.
- Fine when: the piece is marketing copy by design and the author's samples sell this way, or the label is backed by a measurement (an exact "state-of-the-art" benchmark claim).
- Fix: state the capability or the number.

### Copula avoidance (`copula-avoidance`)
- Looks like: "serves as", "stands as", "boasts", "features".
- Cost: dresses "is" and "has" in heavier clothes.
- Fine when: the role is literal ("a proxy that acts as a gateway").
- Fix: "is", "has".

### Vague attribution (`vague-attribution`)
- Looks like: "Experts believe", "Studies show", "It is widely known", "critics argue".
- Cost: the reader cannot check the source; an editor who silently turns it into the author's own assertion adds a claim.
- Fine when: a name, citation or link in the same sentence says who.
- Fix: cite the source if the author supplied one; otherwise `[VERIFY: source for ...]`, or soften to what the author can stand behind, or cut.

### Trailing commentary riders (`trailing-rider`)
- Looks like: "..., highlighting the importance of collaboration", "..., underscoring its value".
- Cost: a participial phrase that comments instead of informing.
- Fine when: the phrase adds a new fact or a measured result.
- Fix: end the sentence at the fact, or turn the commentary into a sentence with evidence.

### Stacked hedges (`hedge-stack`)
- Looks like: "could potentially possibly help".
- Cost: several hedges say no more than one.
- Fine when: the source itself is that uncertain; a single accurate hedge ("may", "in our sample") is not a defect.
- Fix: keep one hedge at the source's level of certainty. Never drop a hedge the claim needs.

### Overbroad ranges and analogy stacks (`false-range`)
- Looks like: "from startups to nations, from ideas to infrastructure", three historical comparisons in a row.
- Cost: sounds expansive and covers nothing in particular.
- Fine when: both ends are real points on a scale the text covers; one analogy that explains a mechanism.
- Fix: list the real topics, or keep the one analogy that does analytical work and say what it explains.

### Unexplained relabeling and false agency
- Looks like: "the concern turns into panic", "the data tells us", "the market decided".
- Cost: hides the mechanism or the person who acted.
- Fine when: the change is explained next, or the figure of speech is plainly metaphor.
- Fix: ask what changed and who acted; use only what the text says.

## 5. Rhythm and shape uniformity

Found by reading shape, not words. Scanner hits here are always weak.

### Reflexive triads
- Looks like: "fast, reliable, and scalable"; three parallel items where the content has two or four.
- Cost: the rhythm decides the list, not the facts.
- Fine when: there really are three things, or the triad is a deliberate rhetorical choice.
- Fix: keep the items the source supports; state what each does.

### Same-opener and fragment runs (`same-opener-run`, `fragment-run`)
- Looks like: four sentences starting "We..."; "Fast. Cheap. Reliable. Done."
- Cost: a drumbeat that replaces argument.
- Fine when: instructions, dialogue, poetry, parallel structure the author chose.
- Fix: combine related sentences, or reorder so each starts from what it adds.

### Uniform sentence length (`uniform-length-run`)
- Looks like: four or more consecutive sentences within a fifth of the same length.
- Cost: monotone cadence tires the ear.
- Fine when: reference text, legal text, or any register where evenness is the norm.
- Fix: read aloud; vary only where repetition is accidental. Keep deliberate repetition and rough edges.

### Synonym cycling
- Looks like: "the model... the system... the framework... the engine" for one thing.
- Cost: the reader wonders whether four things exist.
- Fine when: genuinely different referents.
- Fix: pick the clearest term and repeat it. Repeating a technical term is correct.

### Interchangeable paragraphs and symmetrical sections
- Looks like: swapping two body paragraphs changes nothing; every section has the same length and shape.
- Cost: no cumulative argument; the structure is a template.
- Fine when: reference entries, FAQs, option catalogs where order is arbitrary by design.
- Fix: report it; restructure only if the user asked for structural work.

## 6. Formulaic endings

### Closing formulas and future-narrative closers (`closing-formula`, `future-narrative`)
- Looks like: "In conclusion", "The future looks bright", "This is just the beginning", "Only time will tell".
- Cost: restates or gestures instead of finishing.
- Fine when: a long document ends with a real recap the reader will skim, or a concrete next step follows.
- Fix: end on the last concrete fact or the next action.

### Resilience formula (`resilience-formula`)
- Looks like: "Despite these challenges, the city continues to thrive."
- Cost: no challenge and no response is named.
- Fine when: the challenges and the response are specific.
- Fix: name them or cut.

### Endorsement and engagement closers (`endorsement-closer`, `engagement-bait`)
- Looks like: "Worth your time", "Thank me later", "What do you think? Let me know below."
- Cost: a vote of confidence with no reason, or a reply farm.
- Fine when: a DM between acquaintances, or the author really wants replies about something specific.
- Fix: give the reason the item is worth the reader's time, if the text has it; otherwise end earlier.

### Paragraph-final echoes
- Looks like: the last sentence of a paragraph restates the paragraph.
- Cost: the reader reads everything twice.
- Fine when: a summary sentence helps a skimming reader of a long, dense section.
- Fix: end on the strongest concrete sentence, or hand off to the next point.

### Paper-style endings (`future-work-formula`)
- Looks like: "Future work could explore more settings."
- Cost: no specific next step.
- Fine when: a particular experiment or open question follows.
- Fix: name the next experiment, or omit.

## 7. Formatting decoration

### Dash density (`em-dash-density`)
- Looks like: several dashes in a short passage, each doing a comma's or a colon's job.
- Cost: constant interruption.
- Fine when: the author's samples use them, a house style requires them, or a list term uses a dash.
- Fix: comma, colon, parentheses or two sentences, only where the join is weak. A dash count is a prompt to look, never a limit.

### Decorative bold and label lists (`decorative-bold`, `label-bullet-list`)
- Looks like: three bold phrases in one paragraph; every bullet starting with a bold label then restating it.
- Cost: nothing stands out when everything does.
- Fine when: UI labels, warnings, glossaries, reference entries.
- Fix: put the key point in the sentence's stress position; fold label-and-restatement bullets into prose only if the scope allows restructuring.

### Fragment bullets (`short-fragment-bullets`)
- Looks like: five or more bullets of two or three words with no verbs.
- Cost: lists the topics without saying anything about them.
- Fine when: real parameter, option, feature or step lists.
- Fix: report it; convert to prose only when scope allows.

### Heading decoration (`heading-emoji`)
- Looks like: an emoji in each heading; a heading that repeats the title; a rule between every section; dramatic headings.
- Cost: noise before content.
- Fine when: social posts or a brand style that uses them.
- Fix: headings that name what the section holds.

### Hashtag blocks (`hashtag-block`)
- Looks like: a row of six generic tags.
- Cost: reads as stuffing.
- Fine when: one or two meaningful tags on a platform that uses tags.
- Fix: keep the meaningful ones.

### Typographic residue
- Looks like: curly quotes plus perfectly even punctuation in a casual chat message or commit note.
- Cost: weak signal only; most editors auto-curl.
- Fine when: almost always.
- Fix: leave it unless the destination uses straight quotes.

## 8. Chat residue

Highest priority because it is never part of the message. Remove only the wrapper; keep the content it surrounded.

### Conversational wrappers (`chat-opener`, `chat-closer`, `rewrite-wrapper`)
- Looks like: "Certainly! Here is a revised version:", "I hope this helps", "Would you like me to expand?"
- Cost: shows the text was pasted from a chat and was not read.
- Fine when: a real reply to a real person (an email, a support answer).
- Fix: delete the wrapper line.

### Self-reference and cutoff disclaimers (`assistant-self-reference`)
- Looks like: "As an AI language model", "As of my last update".
- Cost: undermines the claim it excuses.
- Fine when: the text is about language models.
- Fix: delete the wrapper; check the claim, and mark `[VERIFY: current status of ...]` if it may be stale.

### Leaked scaffolding, placeholders and markup (`reasoning-leak`, `placeholder`, `template-braces`, `citation-leak`, `ai-referral-parameter`, `hidden-character`)
- Looks like: "Okay, so the user wants...", "[Insert name]", "oaicite", a link ending `?utm_source=chatgpt.com`, zero-width characters.
- Cost: visible debris, or broken cited claims.
- Fine when: template braces in docs, or zero-width characters pasted by accident from a web page (neither indicates authorship).
- Fix: delete the debris; fill placeholders from the author's material or mark `[ASK AUTHOR: ...]`; re-check any claim whose citation markup leaked.

### Acknowledgment loops and wrong-reader re-explanations
- Looks like: "You're asking about X. To answer your question..." before the answer; re-explaining what the reader already knows.
- Cost: delays the answer.
- Fine when: the restatement orients a reader among several questions ("To answer your question from Tuesday:"), or the reader is new to the topic.
- Fix: read to decide; delete only restatements that add nothing before the answer.
