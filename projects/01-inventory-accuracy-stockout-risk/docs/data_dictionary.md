# Data dictionary

> **Synthetic-data disclaimer:** Sources are deterministic synthetic records
> generated with seed `20260905`; they contain no real business data.

## Source definitions

The five source schemas are defined in `data/README.md`. Key measures are:

* `quantity_variance = system_qty - physical_qty`.
* `adjustment_exposure = sum(abs(quantity_variance) * unit_cost)` over the
  source period.
* `average_daily_demand = sum(orders.ordered_qty) / calendar days` at SKU
  grain.
* `days_of_supply = latest total physical quantity / average daily demand`.
* `variance_event_count` counts non-zero snapshot variances for a
  SKU/location pair.

## Exact output schemas

* **`kpi_summary.csv`** —
  `metric_name,metric_value,metric_unit,calculation_note`
* **`sku_replenishment_priorities.csv`** —
  `priority_rank,sku,product_name,category,supplier,location_count,total_system_qty,total_physical_qty,total_quantity_variance,total_absolute_quantity_variance,unit_cost,inventory_value,adjustment_exposure,average_daily_demand,days_of_supply,reorder_point,safety_stock,lead_time_days,reorder_point_trigger,safety_stock_trigger,lead_time_trigger,materiality_flag,replenishment_tier,replenishment_reason,action_flag,priority_score`
* **`sku_location_count_priorities.csv`** —
  `priority_rank,sku,product_name,category,location,zone,latest_system_qty,latest_physical_qty,quantity_variance,absolute_quantity_variance,unit_cost,inventory_value,location_adjustment_exposure,variance_event_count,recurring_variance,count_records,recount_count,recount_rate,transaction_volume,location_recurrence_flag,control_tier,control_reason,count_action_flag,priority_score,recommended_count_frequency`
* **`location_variance_summary.csv`** —
  `zone,location,sku_location_records,total_adjustment_value,average_inventory_accuracy,recurring_variance_pairs,recount_count,transaction_volume,priority_rank`
* **`stockout_risk_report.csv`** —
  `priority_rank,sku,product_name,category,supplier,total_physical_qty,average_daily_demand,days_of_supply,reorder_point,safety_stock,lead_time_days,materiality_flag,replenishment_tier,replenishment_reason,action_flag,stockout_risk_reason,recommended_action`
* **`data_quality_checks.csv`** — `check_name,status,records_affected,details`

## Tier definitions

### SKU replenishment tier

Applied once per SKU after aggregating all locations:

| tier | exact rule |
|---|---|
| `Critical` | total physical quantity = 0, DOS <= 0.25 * lead time, or total quantity <= safety stock with materiality and DOS <= lead time |
| `High` | not Critical; total quantity <= reorder point and DOS <= lead time |
| `Watch` | not Critical/High; total quantity <= reorder point, DOS <= lead time, or material adjustment exposure |
| `Routine` | otherwise |

Materiality is data-derived at SKU grain: any of latest total inventory value,
SKU unit cost, or cumulative adjustment exposure is at or above its own
linear-interpolated `PERCENTILE_CONT(0.75)` threshold.

### SKU/location control tier

Applied independently to each of 3,600 pairs:

| tier | exact rule |
|---|---|
| `Critical` | recurring variance, latest absolute discrepancy >= 2, at least 3 recounts, and a recurring-variance location |
| `High` | recurring variance plus at least 2 recounts or adjustment exposure at/above the pair P75 |
| `Watch` | recurring variance, any recount, or a non-zero latest discrepancy |
| `Routine` | otherwise |

This queue uses no SKU replenishment or stockout field. `location_recurrence_flag`
means at least two recurring-variance SKU/location pairs share the location.
`recount_rate` is a percentage of completed counts for that pair.

`stockout_risk_report.csv` is a focused extract of the SKU queue and contains
only `Critical` and `High` rows, one row per SKU.
