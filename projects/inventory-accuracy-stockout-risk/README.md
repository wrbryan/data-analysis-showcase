# Inventory Accuracy & Stockout Risk

## Client-ready overview

This reproducible synthetic project separates two operational decisions that
should not be conflated:

1. **SKU replenishment / stockout queue:** one row per SKU, aggregating the
   latest system and physical quantity, inventory value, and adjustment
   exposure across all locations. Demand is SKU-level from customer orders.
2. **SKU/location cycle-count / inventory-control queue:** one row per bin,
   prioritizing variance, adjustment exposure, recurrence, recount patterns,
   transaction volume, and location recurrence. A low quantity in one bin is
   never treated as an enterprise SKU stockout.

## Run from repository root

```bash
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
python -m py_compile projects/inventory-accuracy-stockout-risk/python/*.py
```

The fixed seed is `20260905`. Full five-file inputs are regenerated in
`data/generated/` (ignored by Git); compact schema examples remain in
`data/sample/`. The DuckDB reference is
`sql/inventory_analysis.sql`.

The generated population covers 180 calendar days, 300 SKUs, 10 categories,
5 suppliers, and 12 bins across zones Z1-Z3: 648,000 snapshots, about 585,000
movements, 13,500 SKU-level orders, and 46,800 cycle counts.

**Replenishment decision grain: SKU across all warehouse locations.**

**Cycle-count decision grain: SKU/location.**

**Current Critical + High replenishment queue: 8 of 300 SKUs.**

**Cycle-count priority queue:**

- **Weekly: 6 SKU/location records**
- **Biweekly: 472 SKU/location records**
- **Monthly: 122 SKU/location records**
- **Quarterly: 3,000 SKU/location records**

**Historical stockout-policy exposure: 7.08% of observations.**  
This is a historical monitoring metric, not the current action queue.

**All data is deterministic synthetic data.**  
**No employer, client, customer, confidential, personal, or proprietary data is included.**

## Presentation artifacts

This project has two presentation artifacts with different purposes. They use
the same validated output CSVs and do not represent separate analyses.

- **`dashboard/` — workbook dashboard:** the Excel Executive Control Tower
  source artifact and its build guide. Use it when reviewing how the dashboard
  can be assembled, refreshed, and maintained in a spreadsheet workflow.
- **`reporting/` — static reporting package:** the reproducible Python-generated
  two-page PDF and matching PNGs. Use it for quick executive or portfolio
  review without opening Excel.

The dashboard is the workbook-oriented presentation surface; the reporting
package is the portable, rendered evidence of the same results. Neither folder
contains additional analytical logic, source data, or new KPIs.

## Delivered scope

| Layer | Location |
|---|---|
| Synthetic data generator | `python/generate_synthetic_data.py` |
| Standard-library analyzer | `python/analyze_inventory.py` |
| DuckDB reference SQL | `sql/inventory_analysis.sql` |
| Source contract and regeneration steps | `data/README.md` |
| Field-level output and source dictionary | `docs/data_dictionary.md` |
| Evidence-based narrative | `docs/executive_summary.md` |
| Excel dashboard build guide | [`dashboard/README.md`](dashboard/README.md) |
| Excel dashboard workbook | [`dashboard/inventory_accuracy_stockout_risk_dashboard.xlsx`](dashboard/inventory_accuracy_stockout_risk_dashboard.xlsx) |
| Executive Control Tower PDF | [`dashboard/executive-control-tower.pdf`](dashboard/executive-control-tower.pdf) |
| Executive Control Tower PNG | [`dashboard/executive-control-tower.png`](dashboard/executive-control-tower.png) |
| Excel dashboard documentation | [`docs/excel_dashboard_build.md`](docs/excel_dashboard_build.md) |
| Executive decision brief | [`docs/executive-brief.pdf`](docs/executive-brief.pdf) |
| Validation evidence | `docs/pr_validation_report.md` |

## Queue definitions

### SKU replenishment

`average_daily_demand = sum(orders.ordered_qty) / calendar days` at SKU
grain. `days_of_supply = total latest physical quantity / average daily
demand`. Tiers compare **total** on-hand to the SKU policy reorder point and
safety stock and compare DOS to the SKU lead time:

* **Critical:** total physical quantity is zero, DOS is at or below 25% of
  lead time, or a material safety-stock/lead-time exception exists.
* **High:** total quantity is at or below reorder point and DOS is at or below
  lead time.
* **Watch:** a broad SKU policy trigger or material adjustment exposure exists.
* **Routine:** neither current SKU-level trigger is met.

`stockout_risk_report.csv` contains only Critical and High **SKU rows**.

### SKU/location inventory control

`sku_location_count_priorities.csv` retains all 3,600 latest SKU/location
records. It uses recurring non-zero variance, adjustment exposure, recount
count/rate, transaction volume, and location recurrence to recommend weekly,
biweekly, monthly, or quarterly count frequency. It deliberately contains no
enterprise stockout/replenishment tier.

## Output contract

The analyzer writes:

* `kpi_summary.csv`: KPI values plus separate replenishment and count-queue
  tier distributions.
* `sku_replenishment_priorities.csv`: exactly 300 SKU rows.
* `sku_location_count_priorities.csv`: exactly 3,600 SKU/location rows.
* `stockout_risk_report.csv`: only Critical + High SKU replenishment rows.
* `location_variance_summary.csv`: supporting zone/location control rollup.
* `data_quality_checks.csv`: publication gate; every row must be `PASS`.

The generator naturally produces a small set of high-value, long-lead,
fast-moving SKU supply risks and a limited set of recurring-variance bins.
Recount rate is an emergent result of observed count variance and is expected
to land naturally around 10–15%; it is not hardcoded as an output target.
