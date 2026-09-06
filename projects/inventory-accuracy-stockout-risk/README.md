# Inventory Accuracy & Stockout Risk

Deterministic, reproducible inventory-control case study for a 180-day
distribution-center operation. It identifies inventory record variance,
stockout exposure, excess/obsolete inventory, and risk-based count priorities.

## Run

From the repository root:

```bash
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
```

The generator uses seed `20260905` and creates 300 SKUs across 10 categories,
5 suppliers, 3 zones, and 12 zone/bin locations. It produces 180 daily
snapshots, more than 1,500 replenishment orders, more than 8,000 transactions,
and more than 450 scheduled cycle counts.

## Source data

See `data/README.md` and `docs/data_dictionary.md`. The five source tables are
inventory snapshots, product master, transactions, orders, and cycle counts.

## Outputs

The analyzer writes exactly these reports to `outputs/`:

- `kpi_summary.csv`
- `sku_risk_priorities.csv`
- `location_variance_summary.csv`
- `stockout_risk_report.csv`
- `data_quality_checks.csv`

## SQL

`sql/inventory_analysis.sql` contains DuckDB queries that register the five
source tables and reproduce the KPI, variance, stockout, and quality checks.

## Interpretation

Inventory accuracy is calculated as `1 - ABS(system_qty - physical_qty) /
physical_qty`. Adjustment value is absolute quantity variance multiplied by
unit cost. Stockout risk is a prioritization score using stockout observations,
on-hand gap to reorder point plus safety stock, demand, and supplier lead time.
High-risk SKUs should receive weekly counts and a replenishment/location review.
