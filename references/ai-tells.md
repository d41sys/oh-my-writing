# AI-Writing Tells and Their Human Fix

A tell is a symptom: the real defect is missing specific thought. Fix by adding the specific fact or cutting; do not just swap synonyms (that only hides the symptom). LLM text regresses to the statistically average sentence; human expert text names this paper's object, number, and reason.

## Content tells (most damaging)
| Tell | Example | Human fix |
|---|---|---|
| Significance inflation | "marks a pivotal shift", "paves the way for", "has profound implications" | State the concrete consequence or cut |
| Trailing -ing commentary | "..., highlighting the importance of grounding" | Replace with the finding itself, with its number |
| Regression to the generic | a sentence that fits any paper in the field | Name this paper's object, number, condition |
| Vague attribution | "researchers have noted", "is widely regarded" | Cite who, or cut |
| Formula ending | "Despite these challenges, ...", "Future work could explore ..." | Concrete next step or nothing |
| Paragraph-final summary | last sentence restates the paragraph | Hand off to the next point or stop |
| Over-claiming coverage | "extensive experiments", "comprehensive analysis" | Say what was run |
| Two-sided closing summary | "These results demonstrate X while exposing Y" | State the measured result |
| Anthropomorphic suitcase words | model "reasons", "understands", "commits" | Observable behavior label |

## Sentence-shape tells (survive vocabulary scrubbing)
| Tell | Example | Fix |
|---|---|---|
| Negative parallelism | "not only X but also Y"; "not just X, it's Y" | Assert X and Y plainly, or the one that matters |
| Correction framing | "X is not A, but B"; "rather than A, B" when nobody claimed A | State B. Keep it only when A is a real, measured alternative (and when a reviewer required it) |
| Reflexive rule of three | "efficient, scalable, and robust"; "combining A, B, and C" | Keep only measured properties; say what each part does |
| Copula avoidance | "serves as", "stands as", "represents a" | "is" |
| Elegant variation | "agent ... model ... system ... planner" for one thing | One term |
| **Em dashes** | "the result — and this matters — is ..." | **Not used in our papers.** Comma, parentheses, colon, or two sentences |
| Bullet lists in prose sections | contributions aside | Paragraphs with topic sentences |
| Bold/italic emphasis in body text | "**critically**", "\emph{modeled}" | Put the point in stress position; italics only for definitions |

## Vocabulary, two tiers

**Tier 1, must fix.** Flowery words that rose sharply in post-2023 scientific text and rarely carry information in a paper:
delve, pivotal, intricate, intricacies, tapestry, realm, landscape (figurative), underscore, showcase, foster, harness, leverage (meaning "use"), seamless, meticulous(ly), nuanced, multifaceted, holistic, groundbreaking, paramount, commendable, ever-evolving, intriguingly, noteworthy, unveil, embark, a testament to, plays a key/crucial/vital/pivotal role, paves the way.

**Tier 2, count and fix clusters.** Normal academic words that LLMs also overuse (measured excess frequency in 2024 abstracts). One alone is fine; two or more in a paragraph, or the same one in many paragraphs, is the tell:
crucial, vital, comprehensive, notably, particularly, additionally, moreover, furthermore, enhance/enhancing, insights, potential, valuable, robust (unmeasured), significant (non-statistical), effectively, highlight (figurative), various, diverse, exhibited.

## Scan
Run from the paper root. Comment lines are skipped; `landscape` matches only outside `\begin{landscape}`.

Tier 1 + shape tells + project lessons (every hit must be fixed or justified):
```bash
grep -rnE --include=*.tex -i "delve|pivotal|intricac|intricate|tapestry|realm|underscor|showcas|foster|harness|leverag|seamless|meticulous|nuanced|multifacet|holistic|groundbreak|paramount|commendabl|ever-evolving|intriguing|noteworth|unveil|embark|testament to|plays? an? (key|crucial|vital|pivotal|important) role|paves? the way|not only|not just|rather than|serves as|stands as|it is worth noting|it should be noted|in summary|in conclusion|despite these challenges|extensive experiments|, (highlighting|underscoring|showcasing|demonstrating|emphasizing|reflecting|illustrating)|[^{]landscape|we do not claim|is not evidence|almost entirely|we will|in this paper|---|—" sections/ | grep -vE ':[0-9]+:\s*%'
```

Tier 2 density (paragraphs with 2+ hits need a rewrite):
```bash
for f in sections/*.tex; do grep -v '^\s*%' "$f" | tr 'A-Z' 'a-z' | awk -v f="$f" 'BEGIN{RS=""} {n=gsub(/crucial|vital|comprehensive|notably|particularly|additionally|moreover|furthermore|enhanc|insights|potential|valuable|robust|effectively|highlight|various|diverse|exhibited/,"&"); if(n>=2) print f": paragraph "NR": "n" tier-2 words"}'; done
```

## Not tells
Plain repetition of a defined term, short declarative sentences, first person "we", "is", and contrast sentences that carry a measured finding are human academic norms. Do not "fix" them.
