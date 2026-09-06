# Executive summary

> **Synthetic-data disclaimer:** Findings come from deterministic demonstration
> data generated with seed `20260905`; they are not claims about a real
> operation.

## What the analysis says

The 180-day population contains 300 SKUs, 648,000 SKU/location/day snapshots,
584,997 movements, 13,500 customer orders, and 46,800 scheduled counts. All
publication quality checks passed.

1. **The replenishment queue is deliberately SKU-level.** It aggregates the
   latest physical/system position, inventory value, and adjustment exposure
   across all 12 locations before calculating demand and DOS. It contains
   **196 Routine (65.33%), 96 Watch, 6 Critical, and 2 High** SKUs. The
   Critical+High stockout extract therefore has **8 rows (2.67%)**, each at
   SKU grain. The small Critical/High set is driven by high-value, long-lead,
   fast-moving constrained products rather than a low single bin.
2. **The count queue is a separate control workload.** All **3,600** SKU/bin
   records remain in `sku_location_count_priorities.csv`: **3,000 Routine
   (83.33%), 122 Watch, 472 High, and 6 Critical**. Its tiers use recurring
   variance, adjustment value, recount patterns, transaction volume, and
   location recurrence. They do not infer enterprise replenishment risk.
3. **Recount behavior is credible and emergent.** Completion is **94.12%** and
   recount rate is **14.10%** of completed counts, naturally produced by the
   limited recurring-variance bins rather than a hardcoded output target.
4. **Inventory exposure remains decision-relevant.** Weighted accuracy rounds
   to **100.00%** while cumulative adjustment exposure is **$211,618.40** and
   latest inventory value is **$124,676,423.10**. The aggregate accuracy
   percentage should not replace exception-level control.
5. **Historical and current views are distinct.** The broad historical
   stockout-observation rate is **7.08%** of snapshots. It is a workload
   history KPI, not the current SKU replenishment queue.
6. **Customer service has a delay signal.** On-time shipment rate is **90.90%**
   among shipped orders; partial and delayed orders are present for
   segmentation.

## Recommended operating response

1. Start with the eight Critical+High SKU rows; validate total supply,
   inbound status, and policy assumptions before expediting.
2. Use the SKU/location queue to schedule counts: weekly for Critical,
   biweekly for High, monthly for Watch, and quarterly for Routine.
3. Investigate recurring-variance bins and location patterns independently of
   SKU replenishment decisions.
4. Keep `data_quality_checks.csv` as a hard publication gate and reconcile
   tier totals at both grains on every refresh.

## Assumptions and next steps

Orders have no location, so demand is intentionally SKU-level. Costs, lead
times, and policy points are synthetic planning attributes. Production
deployment should add real WMS/ERP keys, open-order status, measured supplier
performance, approved adjustment reasons, and business-approved materiality
governance.
