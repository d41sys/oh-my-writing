Load when: building or filling the claims ledger for a text (workflow step 3).

# Claims ledger: <document name>

Checked on: <date> | Evidence folder or links: <where> | Checked by: <name or agent>

## How to fill it

- **Claim**: one checkable statement, in the author's words, shortened if needed. Split compound sentences so each row has one claim.
- **Type**: `fact`, `number`, `comparison`, `causal`, `prediction`, `method`, `quote`, `opinion`. Opinions need no evidence but must not be presented as facts.
- **Level**: the strength the text asserts now: `existence`, `narrow`, `systematic`, `guarantee` (see claim strength reference).
- **Evidence**: where the support lives, precise enough to open: file and line, table, page, URL with the passage. Write `none` or `memory` if that is the truth. Mark `secondary` when the location is a summary of the real source.
- **Status**: `supported` (evidence opened and it says this, at this level), `partial` (evidence supports a weaker or narrower claim), `unsupported` (no evidence, or evidence says otherwise), `needs-check` (evidence exists but was not opened, is unclear, or the domain is high-stakes).
- **Action**: `keep`, `narrow` (rewrite to the supported level), `cut`, `ask` (author must supply the source or number).
- **Revised wording**: only for `narrow`; the exact replacement sentence.

## Ledger

| id | line | claim | type | level | evidence | status | action | revised wording or note |
|----|------|-------|------|-------|----------|--------|--------|-------------------------|
| C1 |      |       |      |       |          |        |        |                         |
| C2 |      |       |      |       |          |        |        |                         |

## Cross-document checks

| check | result | where |
|-------|--------|-------|
| Same number appears identically everywhere (abstract, body, tables, captions) | | |
| Every comparison names baseline, metric, conditions, period | | |
| Every percentage change states its base | | |
| Every citation supports the sentence it is attached to | | |
| Quotes match the source word for word | | |
| Secondary citations marked | | |
| High-stakes statements marked for verification | | |

## Open items for the author

- [ASK AUTHOR: ...]
- [VERIFY: ...]
