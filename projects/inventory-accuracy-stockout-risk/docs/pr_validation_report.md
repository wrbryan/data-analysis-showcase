# PR validation report

Validation was run on branch `feature/inventory-project-data-analysis-qc` after
regenerating the deterministic source population with seed `20260905`.

## Final population and output counts

| item | count |
|---|---:|
| SKUs | 300 |
| inventory snapshots | 648,000 |
| transactions | 555,773 |
| orders | 162,000 |
| cycle counts | 46,800 |
| latest SKU/location records retained in `sku_risk_priorities.csv` | 3,600 |
| Critical+High rows in `stockout_risk_report.csv` | 2,027 |

## Risk and KPI results

* Historical stockout-observation rate: **70.29%** (all snapshots).
* Current Critical+High: **2,027 / 3,600 = 56.31%**.
* Current tier counts: **Critical 1,984; High 43; Watch 311;
  Routine 1,262**.
* Inventory accuracy: **99.98%**.
* Cumulative adjustment value: **$1,032,961.10**.
* Latest inventory value: **$37,957,832.60**.
* Aggregate latest days of supply: **14.83 days**.
* Cycle-count completion: **94.12%**.
* Recount rate: **44.45%**. This is an intentionally elevated synthetic
  control signal, **not a benchmark or target**.
* On-time shipment rate: **90.91%**.
* Materiality P75 thresholds: latest inventory value **$12,368.18**, unit cost
  **$92.92**, cumulative adjustment value **$438.50**.

## Quality checks

All 18 rows in `outputs/data_quality_checks.csv` are `PASS` with
`records_affected=0`:

1. required fields and duplicate keys for each of the five sources;
2. SKU reference integrity;
3. 180-day date range;
4. non-negative inventory;
5. snapshot cost matches product master;
6. shipped quantity does not exceed ordered quantity;
7. shipment date is not before order date;
8. all six transaction types are present;
9. partial shipments are present;
10. delayed shipments are present;
11. minimum order, transaction, and cycle-count volumes;
12. current tier partition equals all latest SKU/location records.

Additional validation completed:

```text
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
python -m py_compile projects/inventory-accuracy-stockout-risk/python/*.py
duckdb < projects/inventory-accuracy-stockout-risk/sql/inventory_analysis.sql
```

The DuckDB reference completed successfully and reproduced the source counts,
accuracy, cycle-count, shipment, and movement-type checks.

## Limitations

Data is synthetic and deterministic. Orders have no location, so demand is
allocated evenly across each SKU's observed bins. Lead times, costs, demand,
and recount behavior are synthetic planning/control signals. Materiality is
relative to the current latest-record population and is not a universal
financial threshold. The score and tiers require business governance before
production use; real deployments should add WMS/ERP keys, open-order status,
measured supplier performance, and approved adjustment reason codes.
