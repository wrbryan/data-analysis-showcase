# Inventory Accuracy & Stockout Risk

An end-to-end, reproducible operations analytics project for identifying where
inventory records are unreliable and which SKU/location pairs are most likely
to stock out. It is intentionally built with the Python standard library so it
runs in a clean environment, while the included SQL is ready for DuckDB.

## Quick start (from repository root)

```bash
python projects/inventory-accuracy-stockout-risk/generate_data.py
python projects/inventory-accuracy-stockout-risk/analyze.py
```

The generator overwrites `data/raw/` with the same data every time
(seed `20260905`). The analyzer writes `outputs/stockout_risk_by_sku_location.csv`,
`outputs/inventory_accuracy_by_sku_location.csv`, and `outputs/summary.json`.
Generated inputs and outputs are checked in so the project is immediately
reviewable, but can always be recreated with the two commands above.

## Data model

| File | Grain | Purpose |
| --- | --- | --- |
| `products.csv` | SKU | Product cost, reorder point, supplier |
| `locations.csv` | location | DC and region lookup |
| `suppliers.csv` | supplier | Promised lead-time reference |
| `inventory_daily.csv` | SKU/location/day | Opening, movement, and closing stock |
| `sales_daily.csv` | SKU/location/day | Demand used for risk modeling |
| `receipts.csv` | receipt | Inbound replenishment events |
| `cycle_counts.csv` | count event | Physical quantity versus system quantity |

## Method

* **Inventory accuracy:** `100 × (1 − sum(abs(system − counted)) /
  sum(system))`, calculated for each SKU/location pair.
* **Safety stock:** `1.65 × demand standard deviation × sqrt(lead time)`.
* **Stockout risk score:** a 0–100 score combining the share of days at zero
  stock (55%) and the gap between current stock and reorder-plus-safety stock
  (45%). Bands are Low (<25), Medium (25–55), and High (≥55).
* Lead times are deterministic supplier-range proxies in the synthetic data;
  replace them with measured supplier performance in production.

## Validation and review

```bash
python -m py_compile projects/inventory-accuracy-stockout-risk/*.py
python projects/inventory-accuracy-stockout-risk/analyze.py
```

See `docs/analysis.md` for interpretation guidance and
`dashboard/README.md` for a suggested dashboard layout. `sql/analysis.sql`
contains standalone DuckDB queries for ad-hoc validation.
