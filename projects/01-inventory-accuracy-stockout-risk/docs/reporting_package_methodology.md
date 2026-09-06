# KPI Logic and Reporting Methodology

## Purpose

This document describes the reporting layer for the two-page
Inventory Accuracy & Stockout Risk package. It documents how published output
CSV fields are selected and presented. It does not define new analytical logic
and does not claim a Power BI implementation.

## Source files

The reporting script reads only these existing outputs:

- `outputs/kpi_summary.csv`
- `outputs/sku_replenishment_priorities.csv`
- `outputs/sku_location_count_priorities.csv`
- `outputs/location_variance_summary.csv`
- `outputs/stockout_risk_report.csv`
- `outputs/data_quality_checks.csv`

## Analytical grains

- **Replenishment risk:** one row per SKU aggregated across all warehouse
  locations.
- **Count-control risk:** one row per SKU/location pair.
- **Location exposure:** one row per warehouse location.
- **KPI summary:** one row per published metric or statement.

The reporting package preserves these grains and does not join the source
outputs together.

## KPI logic and source fields

The nine Page 1 KPI cards are read from `kpi_summary.csv` by exact
`metric_name`:

| KPI | Source metric | Display |
|---|---|---:|
| Critical + High Replenishment SKUs | `current_replenishment_queue_statement` | 8 |
| Critical + High Replenishment Rate | `replenishment_critical_high_rate_pct` | 2.67% |
| Weekly Cycle-Count Assignments | `weekly_count_priority_statement` | 6 |
| Biweekly Cycle-Count Assignments | `biweekly_count_priority_statement` | 472 |
| Inventory Record Accuracy | `inventory_accuracy_pct` | 100.00% |
| Cumulative Adjustment Exposure | `adjustment_value` | $211,618.40 |
| Cycle-Count Completion | `cycle_count_completion_pct` | 94.12% |
| Recount Rate | `recount_rate_pct` | 14.10% |
| On-Time Shipment Rate | `on_time_shipment_rate_pct` | 90.90% |

The CSV stores percentage metrics as values such as `2.67`; the reporting
layer formats those values as percentages without changing the source output.

## Python reporting logic

The reporting script uses pandas to:

- Validate required columns and expected row counts.
- Require all 26 data-quality rows to have `status = PASS`.
- Sort replenishment tiers as Critical, High, Watch, Routine.
- Sort count frequencies as Weekly, Biweekly, Monthly, Quarterly.
- Rank the Page 2 replenishment table by `priority_rank` ascending.
- Rank the Page 2 count-priority table by `priority_score` descending with
  `priority_rank` ascending as the tie-breaker.
- Filter location exposure to `total_adjustment_value > 0` and sort descending.
- Format counts, percentages, quantities, and currency for presentation.

Matplotlib creates the two figures and writes them to one two-page PDF. No
additional KPI calculations or analytical transformations are introduced.

## SQL relationship

The reporting layer does not execute SQL. The existing SQL analysis remains the
source of the published output logic and is unchanged.

## Inclusion and exclusion rules

Included:

- All nine validated KPI cards.
- All four replenishment-tier categories on Page 1.
- All four count-frequency categories on Page 1.
- The two nonzero adjustment-exposure locations.
- All 8 rows from `stockout_risk_report.csv`.
- The top 15 count-priority rows by the approved ranking.
- All 26 quality checks as a validation gate.

Excluded:

- New source data.
- Generator or analyzer reruns inside the reporting script.
- New risk tiers or KPI definitions.
- Power BI, Excel, web, API, database, or dashboard-interaction layers.
- Unpublished analytical detail beyond the existing output schemas.

## Filter limitations

The report is a static presentation package. It has no interactive filters or
drill-through behavior. Page 2 intentionally shows the top 15 count-priority
records rather than all 3,600 records to preserve readable executive evidence;
the full queue remains available in the published CSV.

## Synthetic-data limitation

All findings are based on deterministic synthetic demonstration data generated
with seed `20260905`. They are not claims about a real employer, client,
customer, operation, or proprietary environment.
