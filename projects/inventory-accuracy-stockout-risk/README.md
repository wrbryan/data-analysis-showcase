# Inventory Accuracy & Stockout Risk

## Client-ready overview

This portfolio project turns daily warehouse snapshots, inventory movements,
customer orders, and cycle counts into an operational action queue. It answers
three client questions: **Can we trust the inventory record? Which
SKU/location pairs are most exposed to a stockout? Where should count and
replenishment capacity go first?**

All source data is synthetic, deterministic, and clearly labeled as such. It
is suitable for demonstrating reproducible data generation, Python analytics,
SQL design, data-quality controls, and dashboard thinking; it is not a
substitute for production WMS/ERP data.

## Run from repository root

```bash
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
python -m py_compile projects/inventory-accuracy-stockout-risk/python/*.py
```

The fixed seed is `20260905`. The generator overwrites the five source CSVs
and the analyzer overwrites the five output CSVs.

## Delivered scope

| Layer | Location |
|---|---|
| Synthetic data generator | `python/generate_synthetic_data.py` |
| Standard-library analyzer | `python/analyze_inventory.py` |
| DuckDB reference SQL | `sql/inventory_analysis.sql` |
| Source data and disclaimer | `data/README.md` |
| Field-level data dictionary | `docs/data_dictionary.md` |
| Evidence-based narrative | `docs/executive_summary.md` |
| Five-page dashboard wireframe | `dashboard/README.md` |

The data covers 180 calendar days, 300 SKUs, 10 categories, 5 suppliers, and
12 bins across zones Z1-Z3. It includes 648,000 inventory snapshots, more than
8,000 movements and orders by a wide margin, and 46,800 scheduled counts.
Movement types are `RECEIPT`, `PICK`, `ADJUSTMENT`, `TRANSFER_IN`,
`TRANSFER_OUT`, and `RETURN`. Orders include customer segments, partial
shipments, and delayed shipments.

## Methodology

* **Quantity variance:** `system_qty - physical_qty`; absolute variance is its
  absolute value and adjustment value is absolute variance × unit cost.
* **Weighted inventory record accuracy:** `1 - sum(abs variance) /
  sum(max(physical_qty, 1))`, reported as a percentage.
* **Average daily demand:** total `orders.ordered_qty` divided by the observed
  calendar days. Because orders are SKU-level, demand is allocated evenly
  across that SKU's locations for location-level days-of-supply.
* **Days of supply:** latest physical quantity divided by average daily demand.
* **Stockout risk:** `physical_qty <= reorder_point OR days_of_supply <=
  lead_time_days`.
* **Cycle performance:** completed scheduled counts ÷ scheduled counts;
  recounts ÷ completed counts.
* **Shipment service:** shipped orders with `ship_date <= promised_date`
  divided by shipped orders.
* **Priority score:** 35% normalized adjustment value, 30% current stockout
  risk, 20% variance recurrence, and 15% context (inventory value, lead time,
  and location recurrence). Weekly, biweekly, and monthly frequencies follow
  score and stockout rules documented in the analyzer and SQL.

## Output contract

The analyzer writes exactly:

* `outputs/kpi_summary.csv`
* `outputs/sku_risk_priorities.csv`
* `outputs/location_variance_summary.csv`
* `outputs/stockout_risk_report.csv`
* `outputs/data_quality_checks.csv`

The last file is a publication gate with exact fields
`check_name,status,records_affected,details`; every generated check must be
`PASS` before reports are used.

## Assumptions and production handoff

Orders intentionally omit location, so demand is distributed across the
SKU's observed bins. The synthetic lead times and costs are policy attributes,
not supplier performance. A production implementation should replace those
assumptions with WMS/ERP keys, open-order status, measured supplier lead time,
approved adjustment reason codes, and a business-approved materiality threshold.
