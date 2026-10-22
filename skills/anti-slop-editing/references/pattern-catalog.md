Load when: you need the detail behind a candidate (what the pattern is, what it costs, when it is fine, how to fix it) or you are auditing by reading without the scanner.

# Pattern catalog

Every entry is a signal to inspect, not a rule to enforce. A pattern becomes a finding only after you have read the sentence, checked the genre (see [genre calibration](genre-calibration.md)) and compared it with the author's own samples. The lexical entries are English only; for other languages use the structural, evidence and preservation checks and say that word lists do not transfer.

Fix principle for all entries: subtract, or restate the point from the author's material. If the sentence needs a fact the text does not contain, leave the span as written or cut it, and put the question to the author in the reply; in `edit` and `rewrite` mode no marker goes into the text itself. A `detect` report is author-facing, so there a fix may name the question as `[ASK AUTHOR: ...]` or `[VERIFY: ...]`. Do not swap one stock word for another; that hides the symptom and keeps the emptiness.

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

### Rhetorical questions and question runs (`rhetorical-question`, `question-run`)
- Looks like: "But what does this mean for developers?", "So why should you care?", "Do I know how it works? Where it breaks? Which corners it cut?"
- Cost: a question the reader did not ask, used as a transition or a drumbeat; the answer was ready anyway.
- Fine when: a genuine question to the reader that the text then works through or leaves for them ("Do you want the short version or the long one?"), an FAQ, an interview, a survey, or a Socratic passage the author chose. The author's samples that use questions are voice.
- Fix: delete the question and state the answer or finding. One immediately answered question per piece is a habit, not a defect; a run of three is a pattern.

### Performed insight and narrated candor (`performed-insight`, `narrated-candor`)
- Looks like: "Sit with that for a moment.", "That's not nothing.", "Here's where it gets interesting.", "That's the part nobody mentions.", "I want to be upfront:", "Rather than bury this, I'll say it plainly:".
- Cost: cues the reader to be impressed or to trust before giving them the content; the sentence about honesty is not the caveat.
- Fine when: it sits inside a quotation, or the sentence names what is surprising and why. A disclosure (a limit, a conflict of interest, an uncertainty) is content and stays; only the announcement around it goes.
- Fix: delete the cue and keep the fact or caveat it introduced: "I want to be upfront: the sample was small" becomes "The sample was small."

### Launch-copy introductions and slot-fill praise (`launch-intro`, `madlib-step`)
- Looks like: "Meet Flowdesk, your new favorite dashboard.", "Say hello to calm.", "Enter Flowdesk.", "a major step forward for AI infrastructure", "I recently had the pleasure of".
- Cost: any adjective or product name fits the slot, so the sentence says nothing about this product or result.
- Fine when: the piece is launch copy by design and the author's samples do this, or a measured result follows ("a first step toward the full API: it covers 4 of 11 endpoints").
- Fix: "Flowdesk is a treasury dashboard." State what it does or what was measured. Do not invent the capability.

### Affective adverbs (`affective-adverb`)
- Looks like: "Interestingly,", "Surprisingly,", "Remarkably,", "Undoubtedly," at the start of sentences.
- Cost: tells the reader how to react; two or more in a text read as filler.
- Fine when: once, and the text says what was expected and how the result differs.
- Fix: delete the adverb. Keep the fact; if the expectation matters, state it.

### Defended text and inline working (`caveat-stack`, `inline-arithmetic`)
- Looks like: a document where definitions, figures and diagrams each carry their own disclaimer ("Equation 2 explains the idea; it does not reproduce the experiment.", "This is an accounting view, not a physical model.", "These results do not establish that the setting is optimal."), or a sentence that shows its subtraction ("a saving of 120 (1,450 - 1,330)").
- Cost: the text reads as written to a reviewer who might object, not to a reader who needs the point; working in a sentence makes the reader redo the calculation.
- Fine when: the limit changes what the reader should conclude or do; that one stays, once, at the claim. A worked example in a tutorial shows its working on purpose.
- Fix: keep the limits the decision depends on, in one place; cut the rest. Give the result in the sentence and move the working to a table or appendix.

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

### Staged reveals, colon reveals and self-answered questions (`staged-reveal`, `colon-reveal`, `self-answered-question`, `self-answered-fragment`)
- Looks like: "Here's the thing:", "The kicker:", "Plot twist:", "The best part?", "One word: speed.", "What if I told you the cache was the problem?" (also a scenario opener), "The result? Faster builds.", "Why does this matter? Because...", "What changed? Nothing."
- Cost: manufactures suspense around ordinary information. The setup adds words and delays the point; the reveal is rarely a surprise.
- Fine when: a genuine question to the reader ("Do you want the short version or the long one? I can do either."), a real label or list introducer ("Result: 42 ms", "Steps to reproduce:", "Pro tip:" in a tutorial), an FAQ or interview, or a question a reader would really ask whose answer is new information ("Who owns the rollout? Nobody yet.").
- Fix: delete the setup and state the point as a plain sentence ("It runs offline."). Keep a colon that introduces a checkable list or value. The setup is framing; the claim after it stays.

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
- Fix: cite the source if the author supplied one; otherwise soften to what the author can stand behind, or cut, and ask the author for the source in the reply (`[VERIFY: source for ...]`, not inside the text).

### Stock attribution beside a citation (found by reading)
- Looks like: "Studies show that caching cuts tail latency (Lee, 2021)."
- Cost: the lead-in repeats what the citation already says and sounds like the vague form.
- Fine when: the lead-in says what kind of evidence it is ("In a randomized trial").
- Fix: drop the lead-in and let the claim carry the citation, kept byte-identical; keep a certainty word ("suggests") if the sentence had one.

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

### Commitment and values claims (`commitment-claim`)
- Looks like: "underscored our commitment to developer productivity", "our dedication to quality", "our passion for excellence".
- Cost: asserts a value nobody can check, in the place where the fact should be. Often rides on a verb such as "underscored" or on a trailing rider.
- Fine when: a concrete obligation follows (a refund window, a deadline, a service level), or the line sits in a quotation or a contract.
- Fix: keep the fact the sentence rides on (what shipped, what changed) and cut the value claim, listing the removed claim in What changed. If nothing checkable is left, delete the sentence and say so. Do not invent the evidence of commitment.

### Hollow aphorisms, "real/actual" inflation and invented coinages (`aphorism-formula`)
- Looks like: "Trust is the currency of teams.", "At its core, what really matters is...", "real product-market fit", "genuine utility", "a failure mode nobody talks about", "she coined the phrase".
- Cost: profundity by template; "real" implies fake alternatives without saying which; "coined" and "nobody talks about" are priority claims the text may not support.
- Fine when: the contrast is explicit ("real revenue from paying customers, not grants"), the line is literal (the currency of a country), or the author's voice uses aphorisms deliberately.
- Fix: replace the template with the assertion the material supports; drop the adjective; define a term on first use instead of claiming to have coined it. An unsupported priority claim goes, with the question in the reply (`[VERIFY: ...]`).

### False concession and invented antonyms (`false-concession`)
- Looks like: "While X is impressive, Y remains a challenge.", "false precision rather than genuine accuracy".
- Cost: balance by template; the second half is a stock worry, or the pair has a made-up opposite that only exists for symmetry.
- Fine when: both halves carry named facts the text supports.
- Fix: state each half as its own fact; keep the uncertainty on both sides as the source has it. Do not resolve a tension the author left open.

### Vague association (`vague-association`)
- Looks like: "He is associated with the leadership of ExampleCorp.", "tied to economic modernization".
- Cost: implies a role or link while hiding what it was.
- Fine when: the source leaves the relationship unspecified, or a measured statistical association is the correct term (epidemiology, social science).
- Fix: name the relationship the text gives. If it does not give one, keep the vague wording and ask in the reply (`[ASK AUTHOR: what was the role?]`); never invent a title or mechanism.

### Parenthetical hedges (`parenthetical-hedge`)
- Looks like: "(and, increasingly, Z)", "(or, more precisely, Y)", "(and perhaps more importantly, W)".
- Cost: an afterthought tucked inside the sentence that either matters and deserves its own sentence, or does not.
- Fine when: the correction is exact and short ("or, more precisely, 4 of the 6 sites").
- Fix: make it a separate sentence, or delete it. Keep a hedge the claim needs at the source's level of certainty.

### Buried verbs, agentless passives and developer slogans (`nominalization`, `dev-slogan`)
- Looks like: "conducted an analysis of" (analyzed), "The results are preserved automatically.", "it just works", "batteries included", "zero config", "sane defaults".
- Cost: the action or the actor is hidden; slogans stand for behavior the text never states.
- Fine when: a Methods section names a formal procedure; a changelog, README or commit subject uses clipped imperative or passive lines as the register; the slogan is the product's own name for a feature or is quoted.
- Fix: put the action in the verb and name the actor only if the text gives one ("we" is not invented when agency is unclear); replace a slogan with the behavior ("installs with no config file").

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

### Manufactured punchlines and stranded auxiliaries (found by reading)
- Looks like: "We planned for every failure mode. Except the one that happened.", "The tool died; the data didn't.", "Not always. Not perfectly."
- Cost: a twist or a beat stands where the specific event should be; one is style, a repeated habit is a template.
- Fine when: one earned short sentence carries real weight, or the passage is comic or theatrical by design.
- Fix: keep one if earned; turn the rest into a sentence with the actual subject and cause. If the source does not say what the missed failure mode was, keep the original beat or cut it, and ask in the reply (`[ASK AUTHOR: which failure mode?]`) instead of guessing.

### Colon into a forced triple (found by reading)
- Looks like: "The architecture provides: separate ports, processes, and local state."
- Cost: the colon list is shaped as three even when the content has two or four parts.
- Fine when: there really are three, or a spec table or option list is the register.
- Fix: list what the source supports and state the real count.

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

### Lead-in that states the next sentence's conclusion (found by reading)
- Looks like: "Searches are faster." followed by "The index now answers in 40 ms, down from 90."; "The platform is built for every team." before the facts about who uses it.
- Cost: the reader meets the claim twice, once as a bare adjective and once with the evidence.
- Fine when: the genre needs a headline or summary line, or the first sentence adds a fact the second does not.
- Fix: delete the lead-in and keep the facts it summed up, including any scope fact (who, for what, what it does not do) stated as a plain sentence.

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

### Heading echoes and heading case (`heading-echo`)
- Looks like: "## Performance" followed by "Speed matters." before the real content; Title Case Subheadings in a document otherwise written in sentence case.
- Cost: a one-line restatement of the heading delays the content; mixed case reads as pasted from elsewhere.
- Fine when: the line is a real scope statement for a formal section, or the house style requires title case throughout.
- Fix: delete the echo line and start with the substantive sentence; match the document's own heading case. Only change heading case when the scope allows structure edits.

### Unnecessary hyphenation and modifier stacks (found by reading)
- Looks like: "in real-time" (adverbial), "works out-of-the-box", "a high-quality, well-architected, future-proof solution".
- Cost: noise at the margins; stacked modifiers repeat praise without properties.
- Fine when: the hyphen precedes a noun ("real-time analytics") or is the style guide's rule.
- Fix: "in real time", "out of the box"; name the property the stacked adjectives stand for. Low priority (P2).

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
- Fix: delete the wrapper; check the claim, and if it may be stale keep it as written and ask in the reply (`[VERIFY: current status of ...]`).

### Leaked scaffolding, placeholders and markup (`reasoning-leak`, `placeholder`, `template-braces`, `citation-leak`, `ai-referral-parameter`, `hidden-character`)
- Looks like: "Okay, so the user wants...", "[Insert name]", "oaicite", a link ending `?utm_source=chatgpt.com`, zero-width characters.
- Cost: visible debris, or broken cited claims.
- Fine when: template braces in docs, or zero-width characters pasted by accident from a web page (neither indicates authorship).
- Fix: delete the debris; fill placeholders from the author's material; where the material has no value, cut the sentence that needed it or leave the slot out, and ask in the reply (`[ASK AUTHOR: ...]`); re-check any claim whose citation markup leaked.

### Acknowledgment loops and wrong-reader re-explanations
- Looks like: "You're asking about X. To answer your question..." before the answer; re-explaining what the reader already knows.
- Cost: delays the answer.
- Fine when: the restatement orients a reader among several questions ("To answer your question from Tuesday:"), or the reader is new to the topic.
- Fix: read to decide; delete only restatements that add nothing before the answer.

## 9. Signals this skill does not use

- Vocabulary-diversity ratios, punctuation-distribution or burstiness scores, function-word statistics and normalization or confusable-character checks come from detector work. They do not measure what a reader loses and they invite chasing a score; this skill reports reader cost only.
- Not tells on their own: repeating a defined term, short declarative sentences, first-person "we", plain "is" and "has", typographic curly quotes, and contrast sentences that carry a measured finding. Do not fix these.
- Moral adjectives on data or objects ("an honest shape") and "assumptions that stop being true" are sometimes plain imprecision, sometimes metaphor. Check the meaning before changing; replace only with a property the text supports (calibrated, no longer holds).
