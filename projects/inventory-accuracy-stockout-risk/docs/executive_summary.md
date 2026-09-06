# Executive summary

> **Synthetic-data disclaimer:** Findings below come from deterministic
> demonstration data generated with seed `20260905`. They are examples of a
> decision workflow, not claims about a real operation.

## What the analysis says

The 180-day population contains 300 SKUs, 648,000 SKU/location/day snapshots,
555,773 movements, 162,000 customer orders, and 46,800 scheduled cycle counts.
All 18 publication checks passed.

1. **Historical stockout observations are broad.** The historical
   stockout-observation rate is **70.29%** of snapshots under the broad
   `physical <= reorder OR days of supply <= lead` trigger. This KPI describes
   observed historical workload and is intentionally separate from current
   action risk.
2. **Current action risk is latest-snapshot based.** Of 3,600 latest
   SKU/location records, **1,984 Critical**, **43 High**, **311 Watch**, and
   **1,262 Routine**. Therefore **2,027 (56.31%)** are current Critical+High
   action records in `stockout_risk_report.csv`; all 3,600 remain in
   `sku_risk_priorities.csv`.
3. **Materiality is relative to this synthetic population.** The exact
   linear-interpolated P75 thresholds are **$12,368.18** latest inventory
   value, **$92.92** unit cost, and **$438.50** cumulative adjustment value.
   A latest record is material when any measure meets its threshold.
4. **Inventory records are highly accurate in aggregate, but exposure remains
   material.** Weighted inventory record accuracy is **99.98%** and cumulative
   adjustment value is **$1,032,961.10**. Focus controls on high-value and
   recurring exceptions rather than the aggregate percentage alone.
5. **Cycle-count execution has a deliberate synthetic control signal.**
   Completion is **94.12%** (44,048 of 46,800 scheduled counts), and the
   **44.45% recount rate is intentionally elevated synthetic control signal,
   not a benchmark or target**. It exists to make recount triage and
   exception-management workflow visible in a portfolio demonstration.
6. **Shipment service has a measurable delay signal.** On-time shipment rate
   is **90.91%** among shipped orders; partial and delayed shipments are
   intentionally present for segmentation.
7. **Inventory value and supply context support prioritization.** Latest
   inventory value is **$37,957,832.60** and aggregate latest days of supply
   is **14.83 days**. The priority score combines cumulative adjustment,
   current broad trigger, variance recurrence, and context; it is not a
   replacement for the tier rules.

## Recommended operating response

1. Start with the Critical+High queue and validate physical quantity before
   posting material adjustments.
2. Review reorder points and lead-time assumptions for flagged fast movers;
   demand comes from `orders.ordered_qty`, not movement volume.
3. Use Watch rows for monitoring and replenish-planning review, not the
   immediate action extract.
4. Recover the **2,752** missed scheduled counts and treat the deliberately
   elevated recount rate as a synthetic process-control exercise.
5. Segment the 9.09% not-on-time shipment share by customer segment, supplier,
   and SKU before changing promise policy.
6. Keep `data_quality_checks.csv` as a hard publication gate on every refresh.

## Assumptions and next steps

Orders do not contain a location, so SKU demand is allocated evenly across
observed bins. Costs and lead times are synthetic planning attributes.
Production deployment should add real warehouse/order keys, open-order status,
measured supplier performance, adjustment approvals, and business-approved
materiality governance.
