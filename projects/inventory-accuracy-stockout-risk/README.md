# Inventory Accuracy & Stockout Risk

## Client-ready overview

This portfolio project turns daily warehouse snapshots, inventory movements,
customer orders, and cycle counts into a reproducible operational action
queue. It distinguishes a **historical stockout-observation KPI** from
**current latest-snapshot action risk**. All source data is synthetic,
deterministic, and not a substitute for production WMS/ERP data.

## Run from repository root

```bash
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
python -m py_compile projects/inventory-accuracy-stockout-risk/python/*.py
```

The fixed seed is `20260905`. Generation writes the full five-file source
population to `data/generated/` (ignored by Git). Only compact schema examples
are committed under `data/sample/`; sample files are not analysis inputs.
The analyzer reads `data/generated/` and overwrites the five CSVs in
`outputs/`. The DuckDB reference is `sql/inventory_analysis.sql`.

## Delivered scope

| Layer | Location |
|---|---|
| Synthetic data generator | `python/generate_synthetic_data.py` |
| Standard-library analyzer | `python/analyze_inventory.py` |
| DuckDB reference SQL | `sql/inventory_analysis.sql` |
| Source contract and regeneration steps | `data/README.md` |
| Field-level data dictionary | `docs/data_dictionary.md` |
| Evidence-based narrative | `docs/executive_summary.md` |
| Dashboard wireframe | `dashboard/README.md` |
| Validation evidence | `docs/pr_validation_report.md` |

The generated population covers 180 calendar days, 300 SKUs, 10 categories,
5 suppliers, and 12 bins across zones Z1-Z3: 648,000 snapshots, 555,773
movements, 162,000 orders, and 46,800 cycle counts.

## Risk definitions

Historical stockout observations are evaluated for **every snapshot**:
`physical_qty <= reorder_point OR days_of_supply <= lead_time_days`.
`historical_stockout_observation_rate_pct` is those observations divided by all
snapshots. It is a workload/history KPI, not the current action queue.

Current risk is evaluated once per SKU/location using its latest snapshot.
Tiers are mutually exclusive and applied in this order:

1. **Critical:** physical quantity `<= safety_stock` **OR** days of supply
   `<= 0.5 * lead_time_days`.
2. **High:** not Critical, physical quantity `<= reorder_point` **AND** days
   of supply `<= lead_time_days` **AND** `materiality_flag=Y`.
3. **Watch:** not Critical/High, physical quantity `<= reorder_point` **OR**
   days of supply `<= lead_time_days`.
4. **Routine:** otherwise.

`current_action_flag=Y` only for Critical and High; therefore
`stockout_risk_report.csv` contains only those tiers. `sku_risk_priorities.csv`
retains all 3,600 latest SKU/location records, including Watch and Routine.

Materiality is data-derived, never a fixed business cutoff. Across all latest
SKU/location records, calculate the exact linear-interpolated
`PERCENTILE_CONT(0.75)` independently for latest inventory value
(`physical_qty * unit_cost`), latest unit cost, and cumulative historical
adjustment value (`sum(abs(system_qty - physical_qty) * unit_cost)`). A record
is material when **any** of its three values is greater than or equal to its
corresponding 75th-percentile threshold. The exact thresholds are published
in `kpi_summary.csv`.

## Output contract

The analyzer writes exactly:

* `kpi_summary.csv`: `metric_name,metric_value,metric_unit,calculation_note`
* `sku_risk_priorities.csv`: one row per SKU/location; see the exact ordered
  schema in `docs/data_dictionary.md`
* `location_variance_summary.csv`: one row per location
* `stockout_risk_report.csv`: only current Critical + High action rows
* `data_quality_checks.csv`: `check_name,status,records_affected,details`

All quality checks must be `PASS` before using the reports. Output CSVs are
intentionally compact and reviewable; full source data is reproducibly
regenerated rather than committed.

## Assumptions and production handoff

Orders omit location, so SKU demand is allocated evenly across observed bins.
Synthetic lead times and costs are policy attributes, not supplier performance.
Production use should replace these assumptions with WMS/ERP keys, open-order
status, measured supplier lead time, approved adjustment reason codes, and
business-approved action governance.
