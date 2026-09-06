# PR validation report

Validation was run on branch `feature/inventory-project-data-analysis-qc`
after regenerating the deterministic source population with seed `20260905`.

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

## Final population and output counts

| item | count |
|---|---:|
| SKUs | 300 |
| inventory snapshots | 648,000 |
| transactions | 584,997 |
| orders | 13,500 |
| cycle counts | 46,800 |
| SKU replenishment rows | 300 |
| SKU/location count-priority rows | 3,600 |
| Critical+High SKU stockout rows | 8 |

## Separate tier distributions

| tier | SKU replenishment | SKU/location count control |
|---|---:|---:|
| Critical | 6 | 6 |
| High | 2 | 472 |
| Watch | 96 | 122 |
| Routine | 196 | 3,000 |

Routine is the clear majority at both grains. The queues are not
interchangeable: the replenishment queue uses total SKU position and SKU
demand, while the count queue uses local variance/control signals.

## KPI results

* SKU Critical+High rate: **2.67%** (8 of 300).
* Count-queue Critical+High rate: **13.28%** (478 of 3,600).
* Inventory accuracy: **100.00%** rounded; adjustment exposure:
  **$211,618.40**.
* Latest inventory value: **$124,676,423.10**.
* Cycle-count completion: **94.12%**.
* Recount rate: **14.10%** of completed counts, naturally generated and not
  hardcoded.
* Historical broad stockout-observation rate: **7.08%** of snapshots.
* On-time shipment rate: **90.90%**.

## Quality checks

All **26** rows in `outputs/data_quality_checks.csv` are `PASS` with
`records_affected=0`, including:

* source required fields, duplicate keys, references, dates, quantities, and
  movement/order behavior;
* replenishment tier reconciliation at SKU grain;
* one replenishment row per SKU;
* count-control tier reconciliation at SKU/location grain;
* retention of all 3,600 SKU/location records;
* Routine-majority checks at both grains;
* SKU-grain stockout report uniqueness and Critical+High-only filtering;
* explicit check that the count queue has no enterprise stockout inference.

Validation commands:

```text
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
python -m py_compile projects/inventory-accuracy-stockout-risk/python/*.py
duckdb < projects/inventory-accuracy-stockout-risk/sql/inventory_analysis.sql
```

Full generated inputs remain ignored; compact samples remain checked in.
