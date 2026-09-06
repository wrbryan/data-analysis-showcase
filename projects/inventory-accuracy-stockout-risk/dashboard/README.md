# Dashboard wireframe

This five-page wireframe is designed for a client review in Power BI, Tableau,
or a spreadsheet model. Every page should show the synthetic-data disclaimer
and a refresh timestamp. The listed source fields are the fields to expose in
tooltips, filters, or table detail.

## 1. Executive control tower

* KPI cards: `inventory_accuracy_pct`, `adjustment_value`,
  `stockout_rate_pct`, `days_of_supply`, `cycle_count_completion_pct`,
  `recount_rate_pct`, and `on_time_shipment_rate_pct` from `kpi_summary.csv`.
* Trend/filter context: `snapshot_date`, `zone`, `category`, `supplier`.
* Publication gate: `data_quality_checks.csv` `status` must all be `PASS`.

## 2. Inventory variance and accuracy

* Pareto: `adjustment_value` and `absolute_quantity_variance` by `sku`,
  `product_name`, `category`, and `supplier` from `sku_risk_priorities.csv`.
* Matrix: `average_inventory_accuracy`, `total_adjustment_value`, and
  `variance_event_count` by `zone` and `location` from
  `location_variance_summary.csv`.
* Drill-through fields: `system_qty`, `physical_qty`, `quantity_variance`,
  `unit_cost`, and `variance_event_count`.

## 3. Stockout risk and replenishment

* Risk table: `sku`, `location`, `physical_qty`, `average_daily_demand`,
  `days_of_supply`, `reorder_point`, `safety_stock`, and `lead_time_days`
  from `stockout_risk_report.csv`.
* Filters: `category`, `supplier`, `zone`, `stockout_risk_flag`, and
  `recommended_count_frequency` from `sku_risk_priorities.csv`.
* Action tooltip: `stockout_risk_reason` and `recommended_action`.

## 4. Cycle-count performance

* Completion and recount cards from `kpi_summary.csv`.
* Location heatmap: `zone`, `location`, `recount_count`,
  `variance_event_count`, and `average_inventory_accuracy`.
* Detail filters: `count_date`, `counter_team`, `scheduled_flag`,
  `completed_flag`, `recount_flag`, and `variance_qty` from
  `cycle_counts.csv`.

## 5. Action tracker and service

* Queue: `priority_rank`, `sku`, `location`, `priority_score`,
  `stockout_risk_flag`, `adjustment_value`, and
  `recommended_count_frequency` from `sku_risk_priorities.csv`.
* Assignment fields (dashboard-only): owner, target date, status, and expected
  impact; do not write them back to synthetic source data.
* Service slice: `customer_segment`, `ordered_qty`, `shipped_qty`,
  `promised_date`, and `ship_date` from `orders.csv` to explain the
  on-time shipment KPI.
