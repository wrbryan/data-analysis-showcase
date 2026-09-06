# Data dictionary

> **Synthetic-data disclaimer:** Sources are deterministic synthetic records
> generated with seed `20260905`; they contain no real business data.

## Source fields

The five source schemas are defined in `data/README.md` and are identical
between `data/sample/` and generated `data/generated/`: product master,
inventory snapshot, transactions, orders, and cycle counts. Key derived
definitions are:

* `quantity_variance = system_qty - physical_qty`.
* `absolute_quantity_variance = abs(quantity_variance)`.
* `adjustment_value = absolute_quantity_variance * unit_cost`.
* `average_daily_demand = sum(orders.ordered_qty) / calendar days`, allocated
  evenly across each SKU's observed locations.
* `days_of_supply = latest physical_qty / average_daily_demand`.

## Risk fields

Historical stockout observations use every snapshot and the broad trigger
`physical_qty <= reorder_point OR days_of_supply <= lead_time_days`.
Current risk uses one latest snapshot per SKU/location and these exclusive,
ordered tiers:

| tier | exact rule |
|---|---|
| `Critical` | physical quantity `<= safety_stock` OR days of supply `<= 0.5 * lead_time_days` |
| `High` | not Critical AND physical quantity `<= reorder_point` AND days of supply `<= lead_time_days` AND materiality flag is `Y` |
| `Watch` | not Critical/High AND physical quantity `<= reorder_point` OR days of supply `<= lead_time_days` |
| `Routine` | otherwise |

Materiality is calculated across all latest SKU/location records. Each of
latest inventory value (`physical_qty * unit_cost`), latest `unit_cost`, and
cumulative adjustment value is compared with its own exact
linear-interpolated `PERCENTILE_CONT(0.75)` threshold. `materiality_flag=Y`
when any comparison is greater than or equal to its threshold. Thresholds are
published as KPI rows.

## Exact output schemas

The following ordered headers are the analyzer's output contract.

* **`kpi_summary.csv`** — `metric_name,metric_value,metric_unit,calculation_note`
* **`sku_risk_priorities.csv`** —
  `priority_rank,sku,product_name,category,supplier,location,zone,system_qty,physical_qty,quantity_variance,absolute_quantity_variance,unit_cost,inventory_value,cumulative_adjustment_value,average_daily_demand,days_of_supply,reorder_point,safety_stock,lead_time_days,stockout_risk_flag,historical_stockout_observation_count,variance_event_count,materiality_flag,risk_tier,risk_reason,current_action_flag,priority_score,recommended_count_frequency`
* **`location_variance_summary.csv`** —
  `zone,location,sku_location_records,total_adjustment_value,average_inventory_accuracy,stockout_risk_records,recount_count,priority_rank`
* **`stockout_risk_report.csv`** —
  `sku,product_name,category,supplier,location,zone,physical_qty,average_daily_demand,days_of_supply,reorder_point,safety_stock,lead_time_days,materiality_flag,risk_tier,risk_reason,current_action_flag,stockout_risk_reason,recommended_action`
* **`data_quality_checks.csv`** — `check_name,status,records_affected,details`

`sku_risk_priorities.csv` retains every latest SKU/location record.
`stockout_risk_report.csv` contains only rows with
`risk_tier` Critical or High and `current_action_flag=Y`.

### Derived output field definitions

| field | definition |
|---|---|
| `stockout_risk_flag` | `Y` when the broad current trigger (physical <= reorder OR days <= lead) is true |
| `historical_stockout_observation_count` | Number of historical snapshots for that SKU/location meeting the broad trigger |
| `materiality_flag` | `Y` when any of the three latest-record measures meets its own P75 threshold |
| `risk_tier` | Current latest-snapshot tier from the table above |
| `risk_reason` | Human-readable reason generated from the exact tier rule |
| `current_action_flag` | `Y` only for Critical or High; these are the action-report rows |
| `priority_score` | Bounded triage score: 35% cumulative adjustment, 30% current broad trigger, 20% variance recurrence, 15% context |
