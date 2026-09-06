# Dashboard specification

The generated outputs are designed for a one-page operations dashboard.

## KPI cards

* Overall inventory accuracy (`summary.json: overall_accuracy_pct`)
* High-risk SKU/location pairs
* Total stockout days
* Count events reviewed

## Visuals

1. **Risk matrix:** `risk_score` by `sku`, colored by `risk_band`, with
   `location_id` as a filter.
2. **Top 10 action queue:** table of `sku`, `location_id`, `stockout_days`,
   `days_of_cover`, and `risk_score`.
3. **Accuracy by region:** average `accuracy_pct` from the accuracy output.
4. **Variance Pareto:** `absolute_variance_units` by SKU/location, descending.

## Refresh

Run the generator and analyzer from the repository root, then point the BI
tool at the two CSVs in `outputs/`. Keep the seed and formulas documented so
the dashboard screenshot can be regenerated exactly.
