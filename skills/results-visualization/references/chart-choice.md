# Which chart answers which question

Start from the sentence the figure supports, then pick the chart. If no chart makes that sentence easier to see than a three-row table, use the table.

| Question the reader has | Chart | Helper | Traps |
|---|---|---|---|
| Which method is best as rounds, clients or a parameter change? | Line panels, one per setting | `method_lines` | Zoomed y-range exaggerates tiny gaps. Too many methods make the lines tangle; keep at most six and move the rest to a table. |
| What makes up the total cost or time, and how does it change with a setting? | Stacked bars | `stacked_bars` | Only the bottom part can be read against the axis. If one part is the point, put it at the bottom or plot it alone. Negative parts cannot stack. |
| Which single number is bigger, across a few settings? | Bars, or a table | `stacked_bars` with one part | A bar chart of three numbers adds little; a table may be clearer. |
| Which classes does the classifier confuse? | Confusion matrix per dataset | `confusion_grid` | Raw-count shading hides errors in small classes; shade by share of the true class and write counts in cells. Label order must match on both axes. |
| How is the data spread across clients, sites or groups? | Bubble matrix, or stacked bars per group | `bubble_matrix` | Area cannot be read as a number without a size key. Zero cells draw nothing; say so. |
| How do values vary across runs? | Mean line with a band, or box plots | `method_lines` plus `ax.fill_between` | Say what the band is (standard deviation, 95% interval, min–max) and how many runs. |
| How do two continuous measures relate? | Scatter | matplotlib `scatter` | Overplotting hides density; use transparency or a hexbin. |

## Before drawing

1. Write the finding as one sentence, with its numbers.
2. Name the comparison that sentence needs: across methods, across settings, or over time.
3. Put the compared items next to each other on a shared axis. Things far apart or on different scales are hard to compare.
4. Decide what the reader should see first. That is the highlighted series or the first panel.

## Signs a figure should be a table

- Fewer than about six numbers in total.
- The reader needs exact values more than the shape.
- Every series is flat and the differences sit in the third decimal place.
