# Inventory Accuracy & Stockout Risk

## Overview
Reproducible synthetic inventory operations analysis. The workflow measures
cycle-count accuracy and prioritizes SKU/location pairs at risk of stockout.
All data is generated with seed `20260905`.

## Run from repository root
```bash
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
```

## Required source data
`data/inventory_snapshot.csv`, `data/product_master.csv`, `data/transactions.csv`,
`data/orders.csv`, and `data/cycle_counts.csv`.

## Required outputs
The analyzer creates `outputs/inventory_accuracy_summary.csv`,
`outputs/stockout_risk_scores.csv`, `outputs/sku_location_action_queue.csv`,
`outputs/inventory_variance_summary.csv`, `outputs/monthly_inventory_kpis.csv`,
and `outputs/data_quality_checks.csv`.

## Analysis methodology
Accuracy is `100 * (1 - absolute cycle-count variance / system units)`.
Safety stock is `1.65 * demand standard deviation * sqrt(lead time)`.
Risk combines stockout observations (55%) and the current-stock gap to
reorder point plus safety stock (45%). High is >=55, Medium >=25, otherwise Low.

## SQL sections
`sql/analysis.sql` contains the documented DuckDB sections:
**1. Source registration**, **2. Inventory accuracy**, **3. Stockout risk**,
**4. Action queue**, and **5. Data quality checks**.

## Documentation
See `docs/analysis.md` for business interpretation and `docs/data_dictionary.md`
for field definitions.
