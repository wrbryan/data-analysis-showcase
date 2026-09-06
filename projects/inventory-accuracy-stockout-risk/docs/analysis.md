# Analysis brief

## Business question

Which distribution-center/SKU combinations should an inventory manager act on
first: records that cannot be trusted, or stock that is likely to run out?

## Recommended decisions

1. Filter the risk output to **High** risk and sort by `stockout_days`; expedite
   replenishment or transfer inventory.
2. Review low `accuracy_pct` pairs before changing reorder points. A bad system
   balance makes a mathematically correct forecast operationally unsafe.
3. Use `days_of_cover` and `lead_time_days` together: coverage below lead time
   is an immediate service-level concern.
4. Investigate repeated variance events at the same location for receiving,
   put-away, picking, or counting process causes.

## Caveats

This is synthetic data, so the results demonstrate the workflow rather than
forecast actual demand. The risk score is a prioritization heuristic, not a
probability. In production, add promotions, seasonality, open purchase orders,
supplier on-time performance, returns, and item shelf life.
