# Executive summary

This case study demonstrates a repeatable inventory-control workflow. The
analysis combines daily inventory snapshots, product policy, movements,
replenishment orders, and cycle counts to answer where count and replenishment
resources should go first.

The primary management measures are inventory accuracy, adjustment value,
stockout rate, inventory turnover, days of supply, and cycle-count completion.
The risk report ranks every SKU/location pair using stockout observations and
the gap between current stock and reorder point plus safety stock.

## Recommended operating response

1. Perform weekly counts for priority SKUs and high-variance bins.
2. Review replenishment settings for high-risk items with low days of supply.
3. Require recount and supervisor approval for material adjustments.
4. Review supplier lead time and receiving process for repeated variance.
5. Track the KPI summary weekly and validate source quality before publishing.

The data is synthetic and deterministic. Production use would require actual
demand seasonality, open purchase orders, returns, supplier service levels,
adjustment approvals, and a documented dollar approval threshold.
