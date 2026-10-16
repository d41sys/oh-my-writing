#!/usr/bin/env python3
"""List CANDIDATE AI-writing patterns in prose. Candidates are not verdicts.

The scanner is a locator, not a judge. Every hit is a place to look. Whether it is
a real defect depends on the sentence, the genre and the author's own habits, and
the report names the exception to consider next to each hit. A hit says nothing
about who wrote the text.

Usage:
    python scripts/slop_scan.py draft.md
    python scripts/slop_scan.py --profile technical --json draft.md
    cat draft.md | python scripts/slop_scan.py --profile academic -

Profiles (which families of patterns are reported):
    casual        chat residue and placeholders only
    professional  every family (default)
    technical     every family except rhythm; common engineering vocabulary
                  (robust, seamless, leverage, ...) is not reported
    academic      every family, plus a few paper-opener patterns

Never scanned for prose patterns: fenced code, inline code, URLs, quoted lines
(starting with ">"), text inside double quotes, closed YAML frontmatter and HTML
comments. The only URL check is for chatbot referral parameters.

The lexical lists are English only. For other languages the report says so;
an empty result then means nothing.

Output: human lines use [OK], [FLAG] and "->"; --json prints one JSON object.
Exit codes: 0 on success (even with candidates), 2 on an input error.
The scanner never rewrites the text.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from dataclasses import dataclass

FAMILIES = ("lexical", "framing", "contrast", "puffery", "rhythm", "ending", "format", "residue")
PROFILES = ("casual", "professional", "technical", "academic")
PROFILE_FAMILIES = {
    "casual": {"residue"},
    "professional": set(FAMILIES),
    "technical": set(FAMILIES) - {"rhythm"},
    "academic": set(FAMILIES),
}
# (minimum count, minimum per 1000 words) before em dashes are listed at all.
EM_DASH_LIMITS = {"professional": (3, 2.0), "technical": (4, 3.0), "academic": (2, 1.0)}

WORD_RE = re.compile(r"\w+(?:['\u2019-]\w+)*")
LIST_OR_HEAD_RE = re.compile(r"^\s*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|\||-{3,}\s*$|={3,}\s*$)")
CITE_NEAR_RE = re.compile(r"\[\d[^\]]*\]|\([A-Z][^()]*\d{4}[a-z]?\)|\bet al\b|https?://|\\cite|\[@")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"')\]]+")
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2705\u274C]")
BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
BOLD_LABEL_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*[^*\n]+\*\*\s*(?:[:\-\u2013\u2014.]|$)")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
HASHTAG_RE = re.compile(r"(?<![\w&])#[A-Za-z]\w+")
EM_DASH_RE = re.compile(r"\u2014|(?<=\s)--(?=\s)")
LIST_TERM_DASH_RE = re.compile(r"^\s*[-*+]\s+\*\*[^*\n]+\*\*\s*\u2014")
ABBREV = {"e.g", "i.e", "etc", "vs", "dr", "mr", "mrs", "ms", "fig", "al", "approx", "cf", "inc", "ltd", "prof"}
BOUNDARY_RE = re.compile(r"[.!?]+[\"'\u201d\u2019)\]]*\s+(?=[\"'\u201c\u2018(\[]?[A-Z0-9])")


@dataclass(frozen=True)
class Pattern:
    name: str
    family: str
    regex: re.Pattern
    consider: str
    strength: str = "strong"
    skip_in: frozenset = frozenset()
    only_in: frozenset = frozenset()
    group: str | None = None
    cluster: tuple | None = None  # ("paragraph" | "document", minimum hits in group)
    cited_ok: bool = False  # drop the hit when a citation or link sits in the same sentence


def _p(name, family, pattern, consider, *, flags=re.I, strength="strong", skip=(), only=(),
       group=None, cluster=None, cited_ok=False):
    return Pattern(name, family, re.compile(pattern, flags), consider, strength,
                   frozenset(skip), frozenset(only), group, cluster, cited_ok)


GENERIC_WORD = ("Fine in its literal or technical sense, inside a title or quotation, or when the "
                "author's own samples use it. Otherwise a plainer word usually does the same job.")
CLUSTER_WORD = ("One alone is ordinary vocabulary. Listed because 2+ of this kind sit in one paragraph; "
                "check whether each carries information.")
TECH = ("technical",)
# Zero-width start of a sentence (or of a line, optionally after a bullet marker).
SENT = r"(?:(?m:^)[ \t]*(?:[-*+][ \t]+)?|(?<=[.!?]\s))"

PATTERNS: list[Pattern] = [
    # ---- lexical inflation -------------------------------------------------
    _p("delve", "lexical", r"\bdelv(?:e|es|ed|ing)\b", GENERIC_WORD),
    _p("tapestry", "lexical", r"\btapestr(?:y|ies)\b", "Fine for a real textile or a deliberate literary image."),
    _p("pivotal", "lexical", r"\bpivotal\b", "Fine when the point really decided the outcome and the text shows how."),
    _p("intricate", "lexical", r"\bintricat(?:e|ely|cies|cy)\b", GENERIC_WORD),
    _p("realm-landscape", "lexical", r"\b(?:realm|landscape)s?\b",
       "Fine when literal (page orientation, a real terrain, a legal realm). Flag the figurative 'landscape of X'."),
    _p("underscore-verb", "lexical", r"\bunderscor(?:es|ed|ing)\b|\bunderscore\s+the\b",
       "Fine when 'underscore' names the character or the verb is exact.", skip=TECH),
    _p("underscore-verb", "lexical",
       r"\bunderscor(?:es|ed|ing)\s+(?:the|our|its|their|his|her|my|your|a|an|how|that|why|this|these|those)\b",
       "Fine in a quotation or when the verb is exact. Otherwise 'shows' or a cut: the claim after it is usually the point."),
    _p("showcase", "lexical", r"\bshowcas(?:e|es|ed|ing)\b", GENERIC_WORD),
    _p("foster", "lexical", r"\bfoster(?:s|ed|ing)?\b", "Fine for foster care or a surname; otherwise 'encourage' or a concrete verb."),
    _p("harness-verb", "lexical", r"(?<!test )(?<!wiring )(?<!safety )\bharness(?:es|ed|ing)?\b",
       "Fine for a test harness or a physical harness; flag the stock verb meaning 'use'.", skip=TECH),
    _p("leverage-verb", "lexical", r"\bleverag(?:e|es|ed|ing)\b",
       "Fine as a noun in finance or mechanics, or for real architectural leverage; flag the verb meaning 'use'.", skip=TECH),
    _p("seamless", "lexical", r"\bseamless(?:ly)?\b",
       "Fine for gapless migration or handover that the text describes; flag as a bare compliment.", skip=TECH),
    _p("meticulous", "lexical", r"\bmeticulous(?:ly)?\b", GENERIC_WORD),
    _p("nuanced", "lexical", r"\bnuanced\b", "Fine when the nuance is then spelled out."),
    _p("multifaceted", "lexical", r"\bmulti-?faceted\b", GENERIC_WORD),
    _p("holistic", "lexical", r"\bholistic(?:ally)?\b", "Fine in medicine or systems design when defined."),
    _p("groundbreaking", "lexical", r"\bgroundbreaking\b", "Fine only when the novelty is shown, not asserted."),
    _p("paramount", "lexical", r"\bparamount\b", GENERIC_WORD),
    _p("commendable", "lexical", r"\bcommendabl[ey]\b", GENERIC_WORD),
    _p("noteworthy", "lexical", r"\bnoteworthy\b", "Delete the label and let the fact show why it matters."),
    _p("unveil", "lexical", r"\bunveil(?:s|ed|ing)?\b", "Fine for a real unveiling event."),
    _p("embark", "lexical", r"\bembark(?:s|ed|ing)?\b", "Fine for boarding a ship or aircraft."),
    _p("beacon", "lexical", r"\bbeacon\b", "Fine for a real beacon, including signal beacons in networking."),
    _p("utilize", "lexical", r"\butiliz(?:e|es|ed|ing|ation)\b|\bcommenc(?:e|es|ed|ing)\b",
       "A wordiness fix ('use', 'start'), not evidence about authorship. Keep when it is the field's term."),
    _p("inflated-verb", "lexical", r"\b(?:facilitat(?:e|es|ed|ing)|underpin(?:s|ned|ning)?|streamlin(?:e|es|ed|ing)|elevat(?:e|es|ed|ing)|empower(?:s|ed|ing)?)\b",
       GENERIC_WORD, skip=TECH),
    _p("tier2-word", "lexical",
       r"\b(?:crucial|crucially|vital|notably|particularly|enhanc(?:e|es|ed|ing|ement|ements)|insights?|valuable|effectively|"
       r"highlight(?:s|ed|ing)?|various|diverse|exhibit(?:s|ed|ing)?|essential|importantly|remarkabl[ey]|substantial(?:ly)?)\b",
       CLUSTER_WORD, strength="weak", group="tier2", cluster=("paragraph", 2)),
    _p("tier2-word", "lexical", r"\b(?:robust|comprehensive|ecosystem)\b",
       CLUSTER_WORD + " In engineering text these are often exact terms.", strength="weak", skip=TECH,
       group="tier2", cluster=("paragraph", 2)),
    _p("tier2-word", "lexical", r"(?<!statistically )(?<!not )\bsignificant(?:ly)?\b",
       CLUSTER_WORD + " 'Significant' is exact when it means statistically significant.", strength="weak",
       group="tier2", cluster=("paragraph", 2)),
    # ---- empty framing and throat-clearing ---------------------------------
    _p("announce-note", "framing",
       r"\b(?:it(?:['\u2019]s| is)|it should be|it must be|it bears) (?:worth |important to |crucial to |essential to |vital to )?"
       r"(?:noting|note|noted|mentioning|emphasi[sz]ing|remember(?:ing)?)(?: that)?\b",
       "Keep only when the next clause is a caveat that changes what the reader should do."),
    _p("stock-phrase", "framing",
       r"\b(?:when it comes to|in terms of|at its core|the (?:fact|reality|truth) is(?: that)?|needless to say|it goes without saying)\b",
       "Ordinary wording in speech and some technical prose; flag only when deleting it loses nothing.", strength="weak"),
    _p("stock-phrase", "framing", r"\bat the end of the day\b",
       "Rarely carries information; fine in an author's spoken-style voice sample."),
    _p("staged-hook", "framing",
       r"\b(?:let['\u2019]s (?:dive in|dive into|delve|unpack|break (?:this|it) down|be (?:clear|honest|real))|real talk|buckle up|"
       r"without further ado|hot take)\b",
       "Fine in a tutorial voice or a spoken script when the author's samples do the same."),
    _p("era-opener", "framing",
       r"\bin today['\u2019]s (?:\w+(?:[ -]\w+){0,2} )?(?:world|landscape|era|age|environment|economy|marketplace|market|climate|society)\b|"
       r"\bin an? (?:era|age|world|time) (?:of|where|when|in which)\b|\bin the (?:rapidly |ever[- ])?(?:evolving|changing) (?:world|landscape|field)\b|"
       r"\b(?:rapidly|ever)[- ](?:evolving|changing)\b",
       "Fine in genuine history writing, where the era is named and dated."),
    _p("scenario-opener", "framing",
       r"\b(?:imagine a (?:world|future|scenario|time)|picture this|have you ever wondered|what if i told you)\b",
       "Fine in fiction, teaching, or a concrete scenario the piece then works through."),
    _p("audience-sweep", "framing", r"\bwhether you['\u2019]?(?:re| are)\b[^.;\n]{1,80}?\bor\b",
       "Name the reader you actually have; fine when the two groups really get different advice next."),
    _p("announced-feeling", "framing",
       r"\b(?:i(?:['\u2019]m| am)|we(?:['\u2019]re| are)|(?:our|the) team is) (?:so |really |truly )?(?:excited|thrilled|delighted|proud|pleased) to (?:share|announce|introduce)\b",
       "Fine for a launch post when the feeling is the author's and a concrete fact follows at once.", strength="weak"),
    _p("stock-reaction", "framing",
       r"\b(?:what surprised me most|i was (?:fascinated|surprised|amazed) to (?:discover|learn|find)|the (?:interesting|surprising|crazy) part (?:is|was)|"
       r"here['\u2019]s what (?:stood out|surprised me|I learned))\b",
       "Keep a reaction the author really had and explains; never add one."),
    _p("lingering-attention", "framing",
       r"\b(?:the (?:line|idea|question|part) (?:that )?i keep coming back to|i can['\u2019]t stop thinking about|i keep (?:coming back|thinking) (?:to|about))\b",
       "Keep when the sentence says why the idea keeps recurring."),
    _p("importance-restated", "framing", r"\b(?:here['\u2019]s why (?:this|that|it) matters|this matters because|why this matters)\b",
       "Keep when a concrete consequence follows in the same breath."),
    _p("performed-insight", "framing",
       r"\b(?:sit with (?:that|this)|let (?:that|this) sink in|that['\u2019]s not nothing|the punchline is|"
       r"the only (?:metric|thing|number) that (?:matters|counts)|here['\u2019]s what['\u2019]s (?:interesting|wild|funny|fascinating)|"
       r"here['\u2019]s where it gets (?:interesting|clever|good|weird)|this is the (?:interesting|clever|surprising|best) part|"
       r"that['\u2019]s the (?:whole|real) (?:point|story)|the part (?:that )?(?:nobody|no one) (?:talks about|mentions)|"
       r"(?:something|a thing) (?:nobody|no one) (?:talks about|tells you))\b",
       "Cues the reader to be impressed instead of showing why. Keep only inside a quotation or when the sentence "
       "names what is surprising and why."),
    _p("narrated-candor", "framing",
       r"\b(?:i want to be (?:upfront|honest|clear|transparent)|to be (?:fully |completely )?(?:transparent|upfront)|"
       r"rather than bury this|i['\u2019]d rather (?:flag|say) (?:it|this|that)|being (?:honest|upfront|transparent) about)\b",
       "Announces honesty instead of stating the caveat. Delete the wrapper and keep the disclosure itself "
       "(a limit, a conflict of interest, an uncertainty); that content stays.", strength="weak"),
    _p("launch-intro", "framing",
       r"\b[Ss]ay hello to\b|\b[Mm]eet [A-Z][\w-]+, (?:your|the|a)\b|\b[Tt]hink [A-Z]\w+ meets [A-Z]\w+\b|(?m:^)[ \t]*Enter [A-Z][\w-]+[.:!]",
       "Game-show introduction. Say what the product is and does. Fine in launch copy written to sell, when the author's samples do it.",
       flags=0),
    _p("madlib-step", "framing",
       r"\ba (?:major|crucial|significant|important|big|giant|huge|critical|meaningful|exciting|bold|key) (?:step|leap|move|stride|milestone) "
       r"(?:forward|towards?|for)\b|\bi recently had the (?:pleasure|privilege|opportunity) of\b",
       "Slot-fill praise: any adjective fits. Fine when a measured result follows in the same sentence."),
    _p("rhetorical-question", "framing",
       SENT + r"(?:so|but|and|now),? (?:why|what|how) (?:should|does|do|would|will|can|could|might) "
       r"(?:you|this|that|it|we|developers|teams|anyone)\b[^.!?\n]{0,70}\?",
       "A question the reader did not ask, answered at once. Fine in an FAQ, an interview, or a real question the reader must answer.",
       strength="weak"),
    _p("affective-adverb", "framing",
       r"\b(?:Interestingly|Surprisingly|Remarkably|Tellingly|Undoubtedly|Intriguingly|Fascinatingly|Unsurprisingly)\s*,",
       "Steers the reader's reaction. Fine once when the fact really is unexpected and the text says what was expected; "
       "listed because 2+ in one text read as filler.",
       flags=0, strength="weak", group="affective", cluster=("document", 2)),
    _p("transition-opener", "framing",
       r"\b(?:Moreover|Furthermore|Additionally|In addition|Importantly|Notably|Consequently)\s*,",
       "Fine when it marks a real logical step; listed because 3+ in one text read as filler.",
       flags=0, strength="weak", group="transitions", cluster=("document", 3)),
    # ---- contrast and reveal templates -------------------------------------
    _p("not-just", "contrast",
       r"(?:\bnot|\b(?:is|are|was|were|does|do|did|has|have|can|could|will|would)n['\u2019]t) (?:only|just|merely|simply)\b[^.!?\n]{1,100}?(?:\bbut\b|[,;\u2014]\s*(?:it['\u2019]s|it is|they['\u2019]re|this is|that['\u2019]s))",
       "Fine when the second half adds a second real, supported fact."),
    _p("about-x-about-y", "contrast",
       r"\b(?:isn['\u2019]t|is not|not) (?:really |just )?about\b[^.!?\n]{1,80}?[,;.\u2014]\s*(?:it['\u2019]s|it is|this is|that['\u2019]s)(?: really| actually)? about\b",
       "Fine when someone really claimed the first half and the text says who."),
    _p("denied-then-asserted", "contrast",
       r"\b(?:isn['\u2019]t|aren['\u2019]t|wasn['\u2019]t|weren['\u2019]t|doesn['\u2019]t|don['\u2019]t|is not|are not|was not|does not)\b[^.!?\n]{1,80}?"
       r"[,;\u2014]\s*(?:it['\u2019]s|it is|but|they['\u2019]re|they are|this is|that['\u2019]s|that is|rather|instead)\b",
       "A genuine correction of a stated or measured alternative is fine. Flag when nobody claimed the denied half.",
       strength="weak"),
    _p("split-denial", "contrast",
       r"\b(?:doesn['\u2019]t|does not|didn['\u2019]t) mean\b[^.!?\n]{1,100}\.\s+(?:It|This|That) means\b|"
       r"\bnot because\b[^.!?\n]{1,100}[.,;]\s*(?:but )?because\b",
       "Fine when the first half is a real misreading the text names."),
    _p("negation-chain", "contrast",
       r"(?i:\bno\s+[\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,3},\s+no\s+[\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,3},?\s+(?:and\s+)?no\s+[\w'\u2019-]+)|"
       r"\bNot [^.!?\n]{1,30}\.\s+Not [^.!?\n]{1,30}\.|"
       r"\b(?:It|They|We|You) (?:didn['\u2019]t|don['\u2019]t|won['\u2019]t) \w+\.\s+(?:It|They|We|You) (?:didn['\u2019]t|don['\u2019]t|won['\u2019]t) \w+\.",
       "Fine as compact microcopy next to a button ('Free to start. No card required.') or a list of real exclusions.",
       flags=0),
    _p("less-more", "contrast", r"\bless [a-z]+(?: [a-z]+)?,\s+more [a-z]+\b",
       "Fine as a slogan the author owns; weak on its own.", strength="weak"),
    _p("staged-reveal", "contrast",
       r"\bhere['\u2019]s the (?:thing|kicker|catch|twist|deal)\b|\bthe (?:catch|kicker|twist|truth)\s*[:?]|"
       + SENT + r"the (?:result|answer|problem|solution|reason|fix|upshot)\?[ \t]+(?=[A-Z])",
       "Fine as a result label in a report ('The result: 42 ms') or a question a reader really asks."),
    _p("colon-reveal", "contrast",
       SENT + r"(?:(?:the )?(?:best|worst|funniest|scariest|craziest|weirdest|coolest) (?:part|thing|bit)|plot twist|spoiler(?: alert)?|"
       r"one (?:word|thing)|(?:here['\u2019]s )?the (?:secret|trick|punchline|payoff|real (?:story|reason))|here['\u2019]s the (?:truth|best part))"
       r"[ \t]*(?::|\?[ \t]+(?=[A-Z0-9]))",
       "Suspense around ordinary information. Fine as a real label ('Result: 42 ms', 'Pro tip:' in a tutorial) "
       "or when the question is a real one the next sentence does not simply answer."),
    _p("self-answered-question", "contrast",
       r"[A-Za-z][^.!?\n]{4,70}\?\s+(?:Because|Simple|Simply|Short answer|The answer is|It turns out|Spoiler)\b",
       "FAQs, interviews and questions a reader really asks are fine."),
    _p("self-answered-fragment", "contrast",
       SENT + r"[A-Z][^.!?\n]{4,70}\?[ \t]+(?:Nothing|Everything|Nobody|No one|Everyone|Absolutely|Definitely|Exactly|Plenty|Not really|Hardly)\b"
       r"[^.!?\n]{0,30}[.!]",
       "A question asked only to be answered one word later. Fine in an FAQ or interview, or when the answer is the new information "
       "('Who owns the migration? Nobody yet.') and the question is one a reader would ask.", strength="weak"),
    _p("crowd-foil", "contrast",
       r"\b(?:while|as) (?:everyone else|others|the (?:industry|market|competition)|most (?:companies|teams|people|competitors))\b[^.\n]{0,40}"
       r"\b(?:debat\w+|stall\w*|wait\w*|argu\w+|scrambl\w+|catch\w* up|hesitat\w+|sleep\w*|struggl\w+)\b",
       "Fine when the text names the rivals or the position and supports the claim."),
    _p("false-concession", "contrast",
       r"\b(?:while|although) [^.!?\n,]{3,60}\b(?:impressive|promising|notable|commendable|laudable|encouraging)\b[^.!?\n]{0,40},"
       r"[^.!?\n]{3,80}\b(?:remains?|is still|are still)\b",
       "Balance by template: praise one side, then a 'remains a challenge'. Fine when both sides carry named facts.", strength="weak"),
    # ---- puffery and vague attribution -------------------------------------
    _p("significance", "puffery",
       r"\b(?:a|the)\s+(?:pivotal|watershed|defining|transformative)\s+(?:moment|chapter|milestone|shift|turning point)\b|\bturning point\b|"
       r"\ba testament to\b|\bstands? as a (?:testament|beacon|reminder)\b|\bpaves? the way\b|"
       r"\bplays? an? (?:key|crucial|vital|pivotal|significant|important|critical) role\b|\b(?:profound|far-reaching|lasting) (?:implications|impact)\b|"
       r"\bindelible mark\b|\bleaves? (?:a|an) (?:lasting|indelible) (?:mark|impression)\b",
       "Fine when the text then names the concrete consequence or the event really was a turning point."),
    _p("promo-wording", "puffery",
       r"\b(?:game[- ]chang(?:er|ing)|cutting[- ]edge|revolutionary|world[- ]class|best[- ]in[- ]class|next[- ]level|breathtaking|stunning|vibrant|"
       r"bustling|nestled|captivating|unparalleled|unmatched|second to none|state[- ]of[- ]the[- ]art|transformative|revolutioni[sz]e[sd]?|"
       r"rich (?:cultural )?(?:heritage|tapestry|history))\b",
       "Fine in marketing copy by design when the author's samples sell this way, or when a measurement backs the label "
       "(an exact 'state-of-the-art' benchmark claim)."),
    _p("copula-avoidance", "puffery",
       r"\b(?:serves?|stands?|acts?|functions?) as (?:a|an|the)\b|\bboasts?\b",
       "Fine when the role is literal (a proxy that acts as a gateway). Otherwise 'is' or 'has'.", strength="weak", skip=TECH),
    _p("unlock-potential", "puffery",
       r"\bunlock(?:s|ed|ing)?\s+(?:the\s+|your\s+|its\s+)?(?:full\s+)?(?:potential|power|value|secrets?|possibilit\w+)\b",
       "Fine in a quotation or an explicit slogan; otherwise state the actual capability."),
    _p("vague-attribution", "puffery",
       r"\b(?:experts|researchers|scientists|analysts|critics|observers|studies|research|reports|many people|some people|industry (?:experts|observers|leaders))\s+"
       r"(?:say|says|believe|believes|suggest|suggests|argue|argues|agree|note|have noted|has shown|have shown|show|shows|indicate|indicates|claim)\b|"
       r"\bit is (?:widely|commonly|generally) (?:believed|known|accepted|regarded|understood)\b|\bwidely regarded\b|"
       r"\baccording to (?:some|many) (?:experts|sources|reports)\b",
       "Fine when a name, citation or link in the same sentence says who. Otherwise name the source or cut.",
       cited_ok=True),
    _p("trailing-rider", "puffery",
       r",\s+(?:highlighting|underscoring|showcasing|emphasi[sz]ing|reflecting|symboli[sz]ing|demonstrating|illustrating|reinforcing|cementing|fostering|contributing to)\s+"
       r"(?:the|its|their|our|your|his|her|this|these|those|a|an|how|that)\b",
       "Fine when the participle phrase adds a new fact or a measured result."),
    _p("commitment-claim", "puffery",
       r"\b(?:our|its|their|my|his|her|the (?:team|company)['\u2019]s) (?:\w+ )?(?:commitment|dedication|passion) to\b",
       "Asserts a value nobody can check. Fine when a concrete obligation follows (a deadline, a figure, a deliverable) "
       "or in a quotation. Otherwise state what was done."),
    _p("aphorism-formula", "puffery",
       r"\b(?:is|are) the (?:language|currency|heartbeat|backbone|soul|dna|fabric|architecture) of\b",
       "Slogan template. Fine when literal ('the currency of Ecuador') or deliberate rhetoric in a voice that uses it.", strength="weak"),
    _p("vague-association", "puffery",
       r"\b(?:is|was|are|were|been|being) (?:closely |also |often )?(?:associated|connected|linked|tied) (?:with|to)\b|\bin (?:association|connection) with\b",
       "Name the actual role or link if the text gives it; if it does not, keep the wording rather than inventing one. "
       "A measured association is the correct term in science.", strength="weak", only=("professional",)),
    _p("parenthetical-hedge", "puffery",
       r"\((?:and,? (?:perhaps|arguably|increasingly|more importantly)|or,? more precisely)\b[^)]{0,50}\)",
       "Hedge tucked inside brackets. Make it its own sentence if it matters; cut it if it does not.", strength="weak"),
    _p("nominalization", "puffery",
       r"\b(?:conduct(?:ed|s|ing)?|perform(?:ed|s|ing)?|carr(?:y|ied|ies|ying) out|undertak(?:e|es|en|ing)|undertook) an? (?:\w+ )?"
       r"(?:analysis|evaluation|assessment|investigation|examination|comparison|optimi[sz]ation) of\b",
       "The verb is buried in a noun ('analyze', 'evaluate'). Fine in a Methods section that names a formal procedure.", strength="weak"),
    _p("dev-slogan", "puffery",
       r"\b(?:batteries[- ]included|it just works|zero[- ]config(?:uration)?|sane defaults|small enough to fit in your head)\b",
       "Marketing shorthand. State the behavior ('installs with no config file'). Fine as the product's own name for a feature or in a quotation.",
       strength="weak"),
    _p("hedge-stack", "puffery",
       r"\b(?:may|might|could)\b[^.!?\n]{0,30}\b(?:potentially|possibly|perhaps)\b|\b(?:potentially|possibly|perhaps)\b[^.!?\n]{0,30}\b(?:may|might|could)\b",
       "Keep one hedge that matches the source's real uncertainty. Stacking two says nothing extra.", skip=TECH),
    _p("false-range", "puffery",
       r"\bfrom\b[^.,;\n]{2,40}\bto\b[^.,;\n]{2,40},\s+from\b[^.,;\n]{2,40}\bto\b",
       "Fine when both ends are real points on one scale the text covers.", strength="weak"),
    # ---- formulaic endings -------------------------------------------------
    _p("closing-formula", "ending",
       r"\b(?:in (?:conclusion|summary|closing)|to (?:sum up|summari[sz]e|conclude|wrap up)|all in all)\s*[,:]",
       "Fine at the start of a real recap section of a long document the reader will skim."),
    _p("future-narrative", "ending",
       r"\bthe future (?:looks|is|remains) (?:bright|promising|exciting)\b|\bonly time will tell\b|\b(?:exciting|bright) (?:times|days) (?:lie|are) ahead\b|"
       r"\bthe possibilities are (?:endless|limitless)\b|\bthis is (?:just|only) the beginning\b|\bmay become one of the most important\b",
       "End on the last concrete fact or next step instead."),
    _p("resilience-formula", "ending",
       r"\bdespite (?:these|its|the|such|numerous|several|those) (?:\w+ ){0,2}(?:challenges|obstacles|setbacks|limitations|hurdles|difficulties)\b[^.]{0,120}"
       r"\b(?:continues? to|remains?|still|persist\w*)\b",
       "Fine when the challenges and the response are named in the text."),
    _p("endorsement-closer", "ending",
       r"\b(?:thank me later|you['\u2019]ll thank me|worth your time|worth (?:a|the) (?:read|look|watch)|worth checking out|go check it out)\b",
       "Fine in a DM between people who know each other, or when a reason follows."),
    _p("engagement-bait", "ending",
       r"\b(?:what do you think\?|let (?:me|us) know in the comments|drop (?:a|your) (?:comment|thoughts)|share your thoughts|thoughts\?)",
       "Fine when the author really wants replies and says about what."),
    _p("future-work-formula", "ending",
       r"\bfuture work (?:could|may|might|can) (?:explore|investigate|extend|examine)\b|\bwe hope (?:this|our) (?:work|paper|study)\b",
       "Fine when a specific next experiment or open question follows.", only=("academic",)),
    _p("academic-opener", "framing",
       r"\bin recent years\b|\bhas (?:attracted|received|garnered) (?:significant|considerable|increasing|growing|widespread) (?:attention|interest)\b|"
       r"\bhas achieved remarkable (?:success|progress)\b|\bextensive experiments\b",
       "Fine when the period is named and the claim is cited; otherwise open on the concrete problem.", only=("academic",)),
    # ---- chat residue ------------------------------------------------------
    _p("chat-opener", "residue",
       r"^\s*(?:(?:certainly|sure|absolutely|of course)[!,]|(?:great|good|excellent|fantastic) (?:question|point)[!.,]|i['\u2019]d be (?:happy|glad) to help)",
       "In a real conversational reply to a real person this is normal. Pasted into an article, report or post it is residue.",
       flags=re.I | re.M),
    _p("chat-closer", "residue",
       r"\b(?:i hope this helps|hope this helps|let me know if (?:you['\u2019]d like|you would like|you need|there['\u2019]s anything)|would you like me to|"
       r"is there anything else|happy to (?:help|assist) further)\b",
       "Normal in a real email or support reply to a real reader; residue anywhere else."),
    _p("assistant-self-reference", "residue",
       r"\bas an? (?:ai|large language model|language model|ai language model)\b|\bi (?:do not|don['\u2019]t|cannot|can['\u2019]t) (?:have (?:access|personal)|browse|access real-time)\b|"
       r"\bas of my (?:last|latest|most recent) (?:knowledge |training )?(?:update|cutoff)\b|\bmy (?:knowledge|training) (?:cutoff|data)\b|\bknowledge cutoff\b",
       "Fine only in text about language models. Otherwise delete the wrapper and check the claim it excused."),
    _p("rewrite-wrapper", "residue",
       r"^\s*here(?:['\u2019]s| is) (?:a |an |the )?(?:revised|rewritten|improved|polished|updated|edited|final|new)\b[^\n]{0,40}",
       "Delete the wrapper line; keep the content it introduced.", flags=re.I | re.M),
    _p("reasoning-leak", "residue",
       r"^\s*(?:okay|ok|alright),? (?:so )?(?:the user|let me|i need to|i['\u2019]ll)\b|\blet me think (?:about this|step by step)\b",
       "Leaked working notes. Delete them and check that nothing the reader needs went with them.", flags=re.I | re.M),
    _p("placeholder", "residue",
       r"\[(?:insert|your|company|recipient|client|name|date|city|link|url|title)[^\]\n]{0,40}\]|\bLorem ipsum\b",
       "An unfilled template slot. Fill it from the author's material or mark it [ASK AUTHOR: ...]; never invent the value."),
    _p("template-braces", "residue", r"\{\{[^}\n]{1,40}\}\}",
       "Template syntax in docs or code may be intentional.", skip=TECH),
    _p("citation-leak", "residue",
       r"oaicite|contentReference|\bturn\d+(?:search|view|news|image)\d+\b|\u3010[^\u3011\n]{0,40}\u2020[^\u3011\n]{0,40}\u3011",
       "Markup copied out of a chat interface. Remove it and re-check the cited claim at its source."),
    _p("hidden-character", "residue", r"[\u200b-\u200d\u2060\ufeff]",
       "Zero-width characters are sometimes pasted by accident from web pages. Remove them; they say nothing about authorship.",
       flags=0),
]

REFERRAL_RE = re.compile(r"utm_source=(?:chatgpt\.com|openai|copilot|perplexity)", re.I)


def _blank(chars: list[str], start: int, end: int) -> None:
    for i in range(start, end):
        if chars[i] != "\n":
            chars[i] = " "


def mask_protected(text: str) -> str:
    """Return text of equal length with protected regions replaced by spaces."""
    chars = list(text)
    lines = text.split("\n")
    offset = 0
    offsets = []
    for line in lines:
        offsets.append(offset)
        offset += len(line) + 1

    first_prose = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 100)):
            if lines[i].strip() in ("---", "..."):
                _blank(chars, 0, offsets[i] + len(lines[i]))
                first_prose = i + 1
                break

    fence = None
    for i in range(first_prose, len(lines)):
        line = lines[i]
        stripped = line.lstrip()
        start, end = offsets[i], offsets[i] + len(line)
        if fence is None:
            m = re.match(r"(`{3,}|~{3,})", stripped)
            if m:
                fence = m.group(1)[0]
                _blank(chars, start, end)
            elif stripped.startswith(">"):
                _blank(chars, start, end)
        else:
            _blank(chars, start, end)
            if stripped.startswith(fence * 3):
                fence = None

    work = "".join(chars)
    for rx in (re.compile(r"<!--.*?-->", re.S), re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)"), URL_RE):
        for m in rx.finditer(work):
            _blank(chars, m.start(), m.end())
        work = "".join(chars)

    def blank_quotes(rx):
        nonlocal work
        for m in rx.finditer(work):
            if "\n\n" not in m.group(0):
                _blank(chars, m.start(), m.end())
        work = "".join(chars)

    blank_quotes(re.compile(r'(?<![\w])"(?=\S)[^"]{1,600}?(?<=\S)"(?!\w)'))
    blank_quotes(re.compile("\u201c[^\u201d]{1,600}\u201d"))
    return work


def paragraph_spans(masked: str):
    return [(m.start(), m.end()) for m in re.finditer(r"(?:^[ \t]*\S[^\n]*(?:\n|\Z))+", masked, re.M)]


def prose_blocks(masked: str):
    """Runs of consecutive prose lines, excluding headings, list items and tables."""
    blocks, start, pos = [], None, 0
    for line in masked.split("\n"):
        is_prose = bool(line.strip()) and not LIST_OR_HEAD_RE.match(line)
        if is_prose and start is None:
            start = pos
        if not is_prose and start is not None:
            blocks.append((start, pos - 1))
            start = None
        pos += len(line) + 1
    if start is not None:
        blocks.append((start, len(masked)))
    return blocks


def snippet(text: str, limit: int = 160) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


def looks_non_english(masked: str) -> bool:
    letters = [c for c in masked if c.isalpha()]
    if len(letters) < 40:
        return False
    return sum(1 for c in letters if ord(c) > 0x7F) / len(letters) > 0.08


def scan(text: str, profile: str) -> dict:
    masked = mask_protected(text)
    line_starts = [0]
    for m in re.finditer("\n", text):
        line_starts.append(m.end())

    def locate(pos: int):
        line = bisect.bisect_right(line_starts, pos)
        return line, pos - line_starts[line - 1] + 1

    allowed = PROFILE_FAMILIES[profile]
    paras = paragraph_spans(masked)
    para_starts = [s for s, _ in paras]

    def para_index(pos: int) -> int:
        return bisect.bisect_right(para_starts, pos) - 1

    hits = []  # (start, end, pattern)
    for pat in PATTERNS:
        if pat.family not in allowed or profile in pat.skip_in or (pat.only_in and profile not in pat.only_in):
            continue
        for m in pat.regex.finditer(masked):
            if m.end() == m.start():
                continue
            if pat.cited_ok:
                left = max(text.rfind(c, 0, m.start()) for c in ".!?\n")
                right_candidates = [i for i in (text.find(c, m.end()) for c in ".!?\n") if i != -1]
                right = min(right_candidates) if right_candidates else len(text)
                if CITE_NEAR_RE.search(text[left + 1:right + 1]):
                    continue
            hits.append((m.start(), m.end(), pat))

    # Cluster rules: some patterns count only when several of their group appear together.
    group_counts: dict = {}
    for s, _e, pat in hits:
        if pat.cluster:
            scope = para_index(s) if pat.cluster[0] == "paragraph" else 0
            group_counts[(pat.group, scope)] = group_counts.get((pat.group, scope), 0) + 1
    kept = []
    for s, e, pat in hits:
        if pat.cluster:
            scope = para_index(s) if pat.cluster[0] == "paragraph" else 0
            if group_counts[(pat.group, scope)] < pat.cluster[1]:
                continue
        kept.append((s, e, pat))

    # Drop a hit that sits entirely inside a longer hit.
    kept.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    final, covered_end = [], -1
    for s, e, pat in kept:
        if e <= covered_end:
            continue
        final.append((s, e, pat))
        covered_end = max(covered_end, e)

    findings = []
    for s, e, pat in final:
        line, col = locate(s)
        findings.append({"line": line, "col": col, "family": pat.family, "pattern": pat.name,
                         "text": snippet(text[s:e]), "consider": pat.consider, "strength": pat.strength})

    for m in URL_RE.finditer(text):
        if "residue" in allowed and REFERRAL_RE.search(m.group(0)):
            line, col = locate(m.start())
            findings.append({"line": line, "col": col, "family": "residue", "pattern": "ai-referral-parameter",
                             "text": snippet(REFERRAL_RE.search(m.group(0)).group(0)),
                             "consider": "A chatbot added this tracking parameter. Strip it from the link; the link itself stays.",
                             "strength": "strong"})

    words = len(WORD_RE.findall(masked))

    if "rhythm" in allowed:
        findings.extend(_rhythm(masked, text, locate))
    if "format" in allowed:
        findings.extend(_format(masked, text, locate, profile, words))

    findings.sort(key=lambda f: (f["line"], f["col"], f["family"]))

    by_family = {}
    for fam in FAMILIES:
        n = sum(1 for f in findings if f["family"] == fam)
        if n:
            by_family[fam] = {"count": n, "per_1000_words": round(n * 1000 / words, 1) if words else 0.0}
    notes = []
    if looks_non_english(masked):
        notes.append("Text looks non-English. The lexical, framing, contrast and ending lists are English only, "
                     "so an empty or short result says nothing. Check structure, evidence and preservation instead.")
    return {
        "profile": profile,
        "words": words,
        "findings": findings,
        "summary": {"total": len(findings),
                    "per_1000_words": round(len(findings) * 1000 / words, 1) if words else 0.0,
                    "by_family": by_family},
        "notes": notes,
    }


def _sentences(block_text: str, base: int):
    spans, start = [], 0
    for m in BOUNDARY_RE.finditer(block_text):
        before = block_text[start:m.start()]
        tok = re.findall(r"[A-Za-z.]+$", before)
        if m.group(0).startswith(".") and tok and tok[0].lower().rstrip(".") in ABBREV:
            continue
        spans.append((start, m.start() + len(m.group(0).rstrip())))
        start = m.end()
    spans.append((start, len(block_text)))
    out = []
    for a, b in spans:
        seg = block_text[a:b]
        if seg.strip():
            lead = len(seg) - len(seg.lstrip())
            out.append((base + a + lead, base + b))
    return out


def _rhythm(masked: str, text: str, locate) -> list:
    out = []
    for b_start, b_end in prose_blocks(masked):
        sents = _sentences(masked[b_start:b_end], b_start)
        info = []
        for s, e in sents:
            ws = WORD_RE.findall(masked[s:e].lower())
            key = ""
            if ws:
                key = " ".join(ws[:2]) if ws[0] in {"the", "a", "an"} and len(ws) > 1 else ws[0]
            info.append((s, e, key, len(ws)))

        def emit(run, pattern, consider, strength):
            s = run[0][0]
            line, col = locate(s)
            out.append({"line": line, "col": col, "family": "rhythm", "pattern": pattern,
                        "text": snippet(text[s:run[0][1]], 80), "consider": consider, "strength": strength})

        i = 0
        while i < len(info):
            j = i
            while j + 1 < len(info) and info[j + 1][2] == info[i][2] and info[i][2]:
                j += 1
            if j - i + 1 >= 3:
                emit(info[i:j + 1], "same-opener-run",
                     f"{j - i + 1} consecutive sentences open with '{info[i][2]}'. Fine for deliberate parallelism, "
                     "instructions or a list written as prose.", "weak")
            i = j + 1
        i = 0
        while i < len(info):
            j = i
            while j < len(info) and 0 < info[j][3] <= 4:
                j += 1
            if j - i >= 3:
                emit(info[i:j], "fragment-run",
                     f"{j - i} consecutive sentences of 4 words or fewer. Fine for dialogue, a slogan block or a deliberate beat.",
                     "weak")
                i = j
            else:
                i += 1
        i = 0
        while i < len(info):
            best = i
            j = i
            lens = []
            while j < len(info) and 10 <= info[j][3] <= 40:
                lens.append(info[j][3])
                mean = sum(lens) / len(lens)
                if min(lens) >= 0.8 * mean and max(lens) <= 1.2 * mean:
                    best = j
                    j += 1
                else:
                    break
            if best - i + 1 >= 4:
                emit(info[i:best + 1], "uniform-length-run",
                     f"{best - i + 1} consecutive sentences within 20% of the same length. Often fine; "
                     "read it aloud before changing anything.", "weak")
                i = best + 1
            else:
                i += 1
        i = 0
        while i < len(info):
            j = i
            while j < len(info) and masked[info[j][0]:info[j][1]].rstrip().endswith("?"):
                j += 1
            if j - i >= 3:
                emit(info[i:j], "question-run",
                     f"{j - i} consecutive questions. Fine in an FAQ, a survey or a deliberate Socratic passage; "
                     "otherwise state the answers.", "weak")
                i = j
            else:
                i += 1
    return out


def _format(masked: str, text: str, locate, profile: str, words: int) -> list:
    out = []

    def add(pos, pattern, snip, consider, strength="strong"):
        line, col = locate(pos)
        out.append({"line": line, "col": col, "family": "format", "pattern": pattern,
                    "text": snippet(snip, 80), "consider": consider, "strength": strength})

    if profile in EM_DASH_LIMITS:
        min_count, min_density = EM_DASH_LIMITS[profile]
        dashes = []
        for m in EM_DASH_RE.finditer(masked):
            line_start = masked.rfind("\n", 0, m.start()) + 1
            line_end = masked.find("\n", m.start())
            line_text = masked[line_start: line_end if line_end != -1 else len(masked)]
            if LIST_TERM_DASH_RE.match(line_text):
                continue
            dashes.append(m)
        density = len(dashes) * 1000 / words if words else 0.0
        if len(dashes) >= min_count and density >= min_density:
            for m in dashes:
                add(m.start(), "em-dash-density", text[max(0, m.start() - 25): m.end() + 25],
                    f"{len(dashes)} dashes, {density:.1f} per 1000 words. A prompt to look, not a limit: "
                    "fine when the author's own samples use them or the house style does.", "weak")

    lines = masked.split("\n")
    pos = 0
    offsets = []
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    for i, line in enumerate(lines):
        if re.match(r"\s*#{1,6}\s", line) and EMOJI_RE.search(line):
            add(offsets[i], "heading-emoji", line.strip(),
                "Decorative emoji in a heading. Fine for a social post or when the brand voice uses them.")
        tags = HASHTAG_RE.findall(line)
        if len(tags) >= 5:
            add(offsets[i], "hashtag-block", line.strip(),
                "A block of generic tags. Keep one or two that carry meaning on platforms that use tags.")

    echo_rx = re.compile(r"\b(?:matters?|(?:is|are) (?:critical|key|essential|crucial|important|vital|everything))\b", re.I)
    for i, line in enumerate(lines):
        if not re.match(r"\s*#{1,6}\s", line):
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines) or LIST_OR_HEAD_RE.match(lines[j]):
            continue
        short = lines[j].strip()
        if not (len(WORD_RE.findall(short)) <= 6 and short.endswith(".") and echo_rx.search(short)):
            continue
        k = j + 1
        if k < len(lines) and lines[k].strip():
            continue  # not a one-line paragraph
        while k < len(lines) and not lines[k].strip():
            k += 1
        if k < len(lines) and lines[k].strip() and not LIST_OR_HEAD_RE.match(lines[k]):
            add(offsets[j], "heading-echo", short,
                "A one-line paragraph under a heading that only says the topic matters. Start with the substantive sentence "
                "unless the line is a real scope statement.", "weak")

    if profile != "technical":
        for b_start, b_end in prose_blocks(masked):
            n = len(BOLD_RE.findall(masked[b_start:b_end]))
            if n >= 3:
                add(b_start, "decorative-bold", text[b_start:b_end],
                    f"{n} bold spans in one paragraph. Fine for UI labels, warnings or a glossary; "
                    "otherwise put the point in the sentence's stress position.", "weak")

        run = []
        for i, line in enumerate(lines + [""]):
            if BOLD_LABEL_BULLET_RE.match(line):
                run.append(i)
                continue
            if len(run) >= 3:
                add(offsets[run[0]], "label-bullet-list", lines[run[0]].strip(),
                    f"{len(run)} bullets that each open with a bold label. Fine for real definitions or reference entries.", "weak")
            run = []

        run = []
        for i, line in enumerate(lines + [""]):
            m = BULLET_RE.match(line)
            if m and len(WORD_RE.findall(m.group(1))) <= 4 and not m.group(1).endswith("."):
                run.append(i)
                continue
            if len(run) >= 5:
                add(offsets[run[0]], "short-fragment-bullets", lines[run[0]].strip(),
                    f"{len(run)} consecutive bullets of 4 words or fewer. Keep when the content really is a parameter, option or feature list.",
                    "weak")
            run = []
    return out


def read_input(path: str) -> str:
    if path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8-sig", errors="replace")


def render_human(result: dict, label: str) -> str:
    out = [f"slop_scan: {label} profile={result['profile']} words={result['words']}"]
    for note in result["notes"]:
        out.append(f"-> note: {note}")
    if not result["findings"]:
        out.append("[OK] no candidates found in the families this profile reports.")
    for f in result["findings"]:
        out.append(f"[FLAG] L{f['line']}:C{f['col']} {f['family']}/{f['pattern']} ({f['strength']}) \"{snippet(f['text'], 70)}\"")
        out.append(f"  -> consider: {f['consider']}")
    s = result["summary"]
    out.append(f"summary: {s['total']} candidates, {s['per_1000_words']} per 1000 words (candidates, not verdicts)")
    for fam, d in s["by_family"].items():
        out.append(f"  {fam}: {d['count']} ({d['per_1000_words']} per 1000 words)")
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="List candidate AI-writing patterns with line numbers and the exception to consider. "
                    "Candidates are not verdicts and say nothing about authorship. Never rewrites the text.")
    parser.add_argument("path", nargs="?", default="-", help="file to scan; '-' or omitted reads stdin")
    parser.add_argument("--profile", choices=PROFILES, default="professional",
                        help="which families to report (default: professional)")
    parser.add_argument("--json", action="store_true", help="print one JSON object instead of text")
    args = parser.parse_args(argv)
    try:
        text = read_input(args.path)
    except OSError as exc:
        print(f"slop_scan: error: cannot read {args.path}: {exc.strerror or exc}", file=sys.stderr)
        return 2
    result = scan(text, args.profile)
    label = "<stdin>" if args.path == "-" else args.path
    result["file"] = label
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_human(result, label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
