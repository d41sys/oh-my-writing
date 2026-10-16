Load when: a text contains percentages, rates, averages, changes over time, rounded values, ranges, intervals or significance statements, or when the same number appears in several places.

# Numbers and statistics

A number is only as useful as its context. Check the arithmetic, then check what the number is a number of.

## 1. The context a number needs

For each important figure, make sure the reader can answer:

| Question | Example of a missing answer | Fix |
| --- | --- | --- |
| What is it measured in? | "latency improved by 120" | "120 ms" |
| Out of what? (denominator) | "40% failed" | "40% (48 of 120 requests) failed" |
| Over what period or population? | "sales grew 15%" | "sales grew 15% from Q1 to Q2 2024" |
| Compared to what? | "30% faster" | "30% faster than version 2.1 on the same machine" |
| How was it computed? | "average score 7.2" | "mean of 5 ratings per item, scale 1-10" |
| How sure are we? | "effect of 2.3 points" | "2.3 points (95% interval 0.4 to 4.2, 80 participants)" |

Not every number needs every item. Version labels, dates, port numbers and plain counts of things listed in the text do not need denominators or intervals. Measured or inferred results do.

If the author has not supplied a unit, denominator or period, do not guess it: `[ASK AUTHOR: denominator for the 40%]`.

## 2. Arithmetic checks

Do them yourself, in the open, before keeping a number.

- **Percent change** = (new - old) / old x 100. A drop from 210 ms to 168 ms is (168-210)/210 = -20%, a 20% reduction. "Reduced by 96%" would mean the new value is 4% of the old.
- **Percent versus percentage points.** Going from 10% to 12% is +2 percentage points, and +20% relative. Say which. Writing "up 2%" for a rate that rose from 10% to 12% is wrong.
- **Relative versus absolute.** "Cut the error rate by 50%" may mean 0.02% to 0.01%, an absolute change of 0.01 percentage points. Give both when the base is small or the gain looks big. If the reader needs to judge impact, the absolute figure matters more.
- **Reverse changes are not symmetric.** A 50% fall needs a 100% rise to recover.
- **Reading "times".** "3x faster" is ambiguous (three times the speed, or three times quicker to run?). State the pair of values.
- **Sum checks.** Parts add to the whole (allow rounding). Percentages in an exclusive set add to about 100%; if not, say why (multiple answers, missing category).
- **Rates and per-unit values.** Per what? Per 1,000 users, per year, per request. Compare rates only over the same unit and period.
- **Averages.** Name the average (mean, median). A mean of skewed values (income, latency, price) can mislead; give the median or spread. An average of averages is not the overall average unless the groups are equal in size.
- **Sample size.** State how many units the number rests on and what counts as a unit (people, sessions, seeds). Many measurements on a few units are not many independent results.
- **Total counts versus evaluable counts.** Say how many were excluded, lost or unmeasurable before quoting percentages of the rest.

## 3. Base rates and conditional probabilities

A positive result from a test is not the same as the condition being present. Always use the base rate.

Worked check: a screening test finds 90% of true cases (sensitivity) and wrongly flags 9% of healthy people. If 1% of people have the condition, in 1,000 people: 10 have it, 9 are found; 990 do not, 89 are wrongly flagged (990 x 0.09 = 89.1). Of about 98 flagged people, 9 have the condition, roughly 9%. Writing "the test is 90% accurate, so a positive means a 90% chance" would be wrong by a factor of ten.

Related traps:

- "Most X are Y" is not "most Y are X".
- A group-level association does not tell any one person's outcome.
- Rare events: a large relative risk on a tiny base is still a tiny absolute risk.
- Survivorship: results drawn only from the successes say nothing about failure rates.

## 4. Rounding and precision

- Round only at the end. Keep full precision in the working.
- Report no more digits than the measurement supports. 12.3456 ms from a timer with 1 ms resolution is false precision.
- Round so that the meaning survives: 99.6% is not "100%" if the point is that failures exist; 0.4% should not become "0%".
- Round the uncertainty first (usually to one or two significant digits), then round the estimate to the same decimal place: 12.346 +/- 0.023 mm.
- Say what the plus-minus is: standard deviation, standard error, or a 95% interval.
- Zero is not "missing", "not measured", "below detection" or "not applicable". Write which one.
- If an interval is wider than the estimate, say so; do not hide it by dropping the interval.
- Negative values of a quantity that cannot be negative are reported as measured and discussed, not cut to zero.
- Use the same number of decimals in a column, and use units consistently (do not switch between ms and s mid-paragraph).
- Constants and conversion factors come from an authoritative table, not from memory.
- Check the order of magnitude: compare to a known scale. A result can be arithmetically correct and still impossible (a tenfold speedup on a step that is 3% of runtime).

## 5. Consistency across the document

1. List every number that appears more than once (summary, body, tables, figure captions, conclusions).
2. Confirm each occurrence agrees in value, unit, denominator, population and label.
3. A legitimate difference (different subset, different time) is named in the text, not left for the reader to discover.
4. Check table and figure values against the prose, and totals against rows.
5. After any edit that touches a number, re-run this list for that number.
6. Terms stay stable: do not call the same measure "accuracy", "success rate" and "hit rate" in different places.

## 6. Significance and uncertainty

- Report the effect size with an interval, not only a p-value. A tiny effect can be significant in a huge sample; a large effect can be non-significant in a small one.
- "Not significant" means the data did not rule out zero. It does not show there is no effect; ask whether the study could have detected a meaningful one.
- A p-value does not give the probability that the hypothesis is true.
- Many comparisons make chance findings likely. If many were run, say how many and how they were handled; label unplanned patterns as exploratory.
- One run is an anecdote for a noisy quantity. Report runs or seeds and the spread.
- Say what population an interval speaks for (this sample, or a wider group).
- Separate confirmed claims (planned test) from exploratory ones (noticed later).
- Practical size: say whether the difference matters in terms the reader cares about (minutes saved, money, risk), with the numbers.

## 7. Turning a number into a sentence

- Put the number with its meaning: not "p95 latency is 120 ms" alone, but "95% of requests finish within 120 ms; the slowest 5% take longer".
- Concrete anchors beat adjectives: "cut build time from 14 minutes to 6" instead of "much faster builds". Use only anchors present in the evidence.
- One strong, verified number is better than five loosely sourced ones.
- Replace metricless words ("high throughput", "low overhead", "scalable") with the measured dimension, or cut them.
- Label examples as illustrative if they are not real results, and never present an illustrative figure as data.
- Cut-offs and thresholds are heuristics unless proven; say so, and state the rule openly so readers can disagree.

## 8. When the data cannot support an estimate

Say so. "The data do not allow an estimate of X" is a valid result. Do not fill the gap with a typical value, a plausible range from memory, or a number from a similar case. Offer the next step: what measurement would settle it. Mark `[ASK AUTHOR: ...]` or `[VERIFY: ...]` in the text.

## 9. Category swaps to catch

- Counts of items presented as counts of people or cases.
- A trend in a descriptive series presented as a cause or a rate of spread.
- Predicted values presented as measured values.
- An association in a group presented as a prognosis for an individual.
- A subset result (one site, one month) presented as the whole.
