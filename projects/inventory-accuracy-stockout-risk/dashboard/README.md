# Dashboard wireframe

This wireframe is designed for Power BI, Tableau, or a spreadsheet model.
Every page should show the synthetic-data disclaimer and refresh timestamp.
`data_quality_checks.csv` must be all `PASS`.

## 1. Executive control tower

* KPI cards: replenishment SKU tier distribution, count-queue tier
  distribution, Critical+High SKU stockout count, inventory accuracy,
  adjustment exposure, cycle-count completion/recount rate, and shipment
  service from `kpi_summary.csv`.
* Keep the two distributions in separate visuals and label their grains:
  **SKU replenishment** versus **SKU/location inventory control**.

## 2. SKU replenishment and stockout risk

* Action table uses `stockout_risk_report.csv`, which is intentionally only
  Critical+High **SKU rows**: total physical quantity, average daily demand,
  DOS, reorder point, safety stock, lead time, tier, reason, and action.
* Supporting table uses `sku_replenishment_priorities.csv` for all 300 SKUs.
  Show total on-hand/value and adjustment exposure across locations.
* Keep the tier order visible: Critical, High, Watch, Routine. Do not
  calculate enterprise stockout risk from a single bin.

## 3. Inventory control and cycle-count priority

* Queue uses `sku_location_count_priorities.csv` and retains all 3,600
  SKU/location records.
* Show `control_tier`, `control_reason`, variance events, recurring variance,
  recount count/rate, transaction volume, location recurrence, and recommended
  frequency. This page must not show a replenishment/stockout tier.
* Heatmap summarizes `location_variance_summary.csv` by zone/location.

## 4. Accuracy, service, and drill-through

* Pareto: adjustment exposure and absolute variance by SKU/location.
* Detail filters: count date, counter team, completion/recount flags, and
  variance quantity from generated `cycle_counts.csv`.
* Service slice: customer segment, ordered/shipped quantity, promised date,
  and ship date from generated `orders.csv`.

Assignment fields (owner, target date, status, expected impact) are
dashboard-only and should not be written back to synthetic source data.
