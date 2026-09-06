# Dashboard wireframe

This five-page wireframe is designed for Power BI, Tableau, or a spreadsheet
model. Every page should show the synthetic-data disclaimer and refresh
timestamp. `data_quality_checks.csv` must be all `PASS`.

## 1. Executive control tower

* KPI cards: historical stockout-observation rate, current Critical+High
  count and percent, tier counts, inventory accuracy, adjustment value,
  cycle-count completion, recount rate, and on-time shipment rate from
  `kpi_summary.csv`.
* Show the distinction between historical observations and current latest
  action records; read both values from `kpi_summary.csv` rather than using
  targets or hardcoded percentages.
* Filters: `snapshot_date`, `zone`, `category`, and `supplier`.

## 2. Inventory variance and accuracy

* Pareto: `cumulative_adjustment_value`, `absolute_quantity_variance`,
  `inventory_value`, and `variance_event_count` by SKU from
  `sku_risk_priorities.csv`.
* Matrix: `average_inventory_accuracy`, `total_adjustment_value`, and
  `variance_event_count` by zone/location from
  `location_variance_summary.csv`.
* Drill-through fields: `system_qty`, `physical_qty`, `quantity_variance`,
  `unit_cost`, `inventory_value`, and cumulative adjustment value.

## 3. Current stockout action risk

* Action table uses `stockout_risk_report.csv`: `sku`, `location`,
  `physical_qty`, `average_daily_demand`, `days_of_supply`, `reorder_point`,
  `safety_stock`, `lead_time_days`, `materiality_flag`, `risk_tier`,
  `risk_reason`, `current_action_flag`, and `recommended_action`.
* Keep the exact tier order and definitions visible: Critical, High, Watch,
  Routine. The report itself contains only Critical and High. Critical uses
  zero physical quantity, days of supply at or below 0.25 lead time, or a
  material safety-stock exception with the current stockout-risk condition.
  High requires both reorder-point and lead-time triggers plus materiality.
  Watch also includes material recurring variance (at least two non-zero
  variance snapshots) when not Critical/High.
* A separate all-record table from `sku_risk_priorities.csv` lets users
  filter `risk_tier` to Watch/Routine without losing records.

## 4. Cycle-count performance

* Completion and recount cards from `kpi_summary.csv`.
* Label the **44.45% recount rate as an intentionally elevated synthetic
  control signal, not a benchmark**.
* Location heatmap: `zone`, `location`, `recount_count`,
  `variance_event_count`, and `average_inventory_accuracy`.
* Detail filters: `count_date`, `counter_team`, `scheduled_flag`,
  `completed_flag`, `recount_flag`, and `variance_qty` from generated
  `cycle_counts.csv`.

## 5. Action tracker and service

* Queue: `priority_rank`, `sku`, `location`, `priority_score`,
  `risk_tier`, `current_action_flag`, `materiality_flag`,
  `cumulative_adjustment_value`, and `recommended_count_frequency` from
  `sku_risk_priorities.csv`.
* Assignment fields (dashboard-only): owner, target date, status, and expected
  impact; do not write them back to synthetic source data.
* Service slice: `customer_segment`, `ordered_qty`, `shipped_qty`,
  `promised_date`, and `ship_date` from generated `orders.csv`.
