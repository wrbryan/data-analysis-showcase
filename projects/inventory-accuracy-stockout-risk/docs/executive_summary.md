# Executive summary

> **Synthetic-data disclaimer:** Findings below are calculated from the
> deterministic demonstration data generated with seed `20260905`. They are
> examples of the decision workflow, not claims about a real operation.

## What the analysis says

The 180-day population contains 300 SKUs, 648,000 SKU/location/day snapshots,
555,773 movements, 162,000 customer orders, and 46,800 scheduled cycle counts.
The analyzer produced five report CSVs and all 17 data-quality checks passed.

1. **Inventory records are highly accurate in aggregate, but the dollar
   exposure is material.** Weighted inventory record accuracy is **99.98%**
   using the required physical-quantity denominator, while cumulative
   adjustment value is **$1,032,961.10**. This is a reason to focus controls
   on high-cost and recurring exceptions rather than relying on the aggregate
   percentage alone.
2. **Stockout exposure is broad under the policy trigger.** The flagged
   stockout-observation rate is **70.29%** of snapshots, where the rule is
   physical quantity at or below reorder point or days of supply at or below
   lead time. The stockout report contains **2,338** currently flagged
   SKU/location pairs for immediate count and replenishment review.
3. **Cycle-count execution is incomplete and recount demand is substantial.**
   Completion is **94.12%** (44,048 of 46,800 scheduled counts), and the
   recount rate is **44.45%** of completed counts. Supervisors should reserve
   capacity for missed counts and repeat counts in high-variance bins.
4. **Shipment service has a measurable delay signal.** On-time shipment rate
   is **90.91%** among shipped orders. The source deliberately includes
   partial shipments and delayed shipments, allowing service performance to
   be segmented by customer segment and SKU in the dashboard.
5. **Prioritization should combine accuracy, value, and service risk.** The
   priority queue ranks 3,600 SKU/location pairs using the documented
   adjustment-value, stockout, recurrence, and context score. Recommended
   frequencies are **Weekly** for stockout/high-score pairs, **Biweekly** for
   intermediate risk, and **Monthly** for routine pairs.

## Recommended operating response

1. Start with the weekly queue and validate physical quantity before posting
   material adjustments.
2. Review reorder points and lead-time assumptions for flagged fast movers;
   demand is derived from `orders.ordered_qty`, not movement volume.
3. Recover the 2,752 missed scheduled counts and use recounts as a coaching
   and root-cause signal.
4. Segment the 9.09% not-on-time shipment share by customer segment, supplier,
   and SKU before changing promise policy.
5. Keep `data_quality_checks.csv` as a hard publication gate on every refresh.

## Assumptions and next steps

Orders do not contain a location, so SKU demand is allocated evenly across
observed bins. Costs and lead times are synthetic planning attributes.
Production deployment should add real warehouse/order keys, open-order status,
measured supplier performance, adjustment approvals, and a business-approved
materiality threshold.
