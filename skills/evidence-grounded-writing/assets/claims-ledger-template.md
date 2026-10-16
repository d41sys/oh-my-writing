Load when: building or filling the claims ledger for a text (workflow step 3).

# Claims ledger: <document name>

Checked on: <date> | Evidence folder or links: <where> | Checked by: <name or agent>

## How to fill it

- **Claim**: one checkable statement, in the author's words, shortened if needed. Split compound sentences so each row has one claim.
- **Type**: `fact`, `number`, `estimate`, `calculation`, `comparison`, `causal`, `forecast`, `method`, `quote`, `opinion`, `recommendation`. Keep the class the author intended: an estimate is not a fact, a forecast is not a prediction of record, a recommendation is not an evidence claim. Opinions and recommendations need no evidence row but must not be presented as findings.
- **Level**: the strength the text asserts now: `existence`, `narrow`, `systematic`, `guarantee` (see claim strength reference).
- **Evidence**: where the support lives, precise enough to open: file and line, table, page, URL with the passage. Write `none` or `memory` if that is the truth. Mark `secondary` when the location is a summary of the real source.
- **Status**: `supported` (evidence opened and it says this, at this level), `partial` (evidence supports a weaker or narrower claim), `unsupported` (no evidence, or evidence says otherwise), `needs-check` (evidence exists but was not opened, is unclear, or the domain is high-stakes).
- **Action**: `keep`, `narrow` (rewrite to the supported level), `cut`, `ask` (author must supply the source or number).
- **Revised wording**: only for `narrow`; the exact replacement sentence. For results, add `confirmatory` or `exploratory` in the note when it matters.

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

## Citation checks

One row per use of a citation (the same source cited in two sentences is two rows).

| citation | line | sentence | exists | metadata | passage opened (locator) | supports this sentence? | action |
|----------|------|----------|--------|----------|--------------------------|--------------------------|--------|
|          |      |          |        |          |                          | supports / partly / does not support / cannot open | keep / fix / replace / remove |

## Cut or withdrawn claims

Claims removed from the text because no evidence supports them. List each so the change is visible and the author can restore it with a source.

| id | claim as written | why cut |
|----|------------------|---------|

## Open items for the author

- [ASK AUTHOR: ...]
- [VERIFY: ...]
- [UNTESTED] (commands or code in the text that were not run)
