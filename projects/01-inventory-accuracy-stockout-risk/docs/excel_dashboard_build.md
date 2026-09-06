# Excel Executive Control Tower Build Guide

## Purpose

This guide explains how to build the Excel-based Executive Control Tower
from the validated output files in this project.

The dashboard presents two intentionally separate decisions:

1. SKU-level replenishment risk across all warehouse locations.
2. SKU/location-level cycle-count and inventory-control priority.

## Prerequisites

- Microsoft Excel with Power Query support.
- A local copy of this repository.
- Generated and analyzed Inventory Accuracy & Stockout Risk source/output files.

## Reproduce the analysis

From the repository root:

```bash
python projects/01-inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/01-inventory-accuracy-stockout-risk/python/analyze_inventory.py
```

## Import files

Import the five CSV output files from:

```text
projects/01-inventory-accuracy-stockout-risk/outputs/
```

| File | Grain | Use |
|---|---|---|
| `kpi_summary.csv` | One row per KPI | KPI cards |
| `sku_replenishment_priorities.csv` | One row per SKU | Replenishment-risk chart |
| `sku_location_count_priorities.csv` | One row per SKU/location | Cycle-count workload chart |
| `location_variance_summary.csv` | One row per location | Location-adjustment chart |
| `data_quality_checks.csv` | One row per validation check | Data-quality indicator |

## Workbook design

Create `inventory_accuracy_stockout_risk_dashboard.xlsx` with one presentation
worksheet named `Executive Control Tower`. Supporting query tables may remain in
hidden worksheets or Excel's data model.

## KPI cards

Create these nine cards from `kpi_summary.csv`:

| Card | Source `metric_name` | Expected value | Display format |
|---|---|---:|---|
| Critical + High Replenishment SKUs | `current_replenishment_queue_statement` | 8 | Whole number |
| Critical + High Replenishment Rate | `replenishment_critical_high_rate_pct` | 2.67% | Percentage, two decimals |
| Weekly Cycle-Count Assignments | `weekly_count_priority_statement` | 6 | Whole number |
| Biweekly Cycle-Count Assignments | `biweekly_count_priority_statement` | 472 | Whole number |
| Inventory Record Accuracy | `inventory_accuracy_pct` | 100.00% | Percentage, two decimals |
| Cumulative Adjustment Exposure | `adjustment_value` | $211,618.40 | Currency, two decimals |
| Cycle-Count Completion | `cycle_count_completion_pct` | 94.12% | Percentage, two decimals |
| Recount Rate | `recount_rate_pct` | 14.10% | Percentage, two decimals |
| On-Time Shipment Rate | `on_time_shipment_rate_pct` | 90.90% | Percentage, two decimals |

Percentage values in the CSV are stored as values such as `2.67` and should be
converted to decimal percentages before applying percentage formatting.

## Supporting charts

### Current SKU Replenishment Risk

- Source: `sku_replenishment_priorities.csv`
- Category: `replenishment_tier`
- Value: Count of SKU records
- Sort order: Critical, High, Watch, Routine
- Expected counts: 6 Critical, 2 High, 96 Watch, 196 Routine
- Grain: SKU across all warehouse locations

### Recommended Cycle-Count Workload

- Source: `sku_location_count_priorities.csv`
- Category: `recommended_count_frequency`
- Value: Count of SKU/location assignments
- Sort order: Weekly, Biweekly, Monthly, Quarterly
- Expected counts: 6 Weekly, 472 Biweekly, 122 Monthly, 3,000 Quarterly
- Value-axis label: `SKU/location assignments`
- Grain: SKU/location

### Locations With Highest Adjustment Exposure

- Source: `location_variance_summary.csv`
- Category: `location`
- Value: Sum of `total_adjustment_value`
- Filter: `total_adjustment_value > 0`
- Expected values: Z3-B03 `$106,636.60`; Z2-B02 `$104,981.80`
- Format: Currency with two decimal places
- Grain: Location-level adjustment exposure

## Action callout

**Action Now**

1. Review the 8 Critical + High SKUs for total supply position, inbound status, and replenishment-policy settings.

2. Execute the 6 weekly and 472 biweekly SKU/location cycle-count assignments.

3. Investigate the locations with recurring variance and adjustment exposure.

**Decision grains:**
Replenishment risk = SKU across all locations.
Count-control risk = SKU/location.

## Data-quality indicator

Show `Data Quality: 26 / 26 Checks Passed` by counting rows whose `status` is
`PASS` in `data_quality_checks.csv` and comparing that count with the total
validation checks.

## Refresh process

1. Regenerate source data and analysis outputs.
2. Open the Excel workbook.
3. Select Data -> Refresh All.
4. Confirm all quality checks pass.
5. Confirm KPI cards match the refreshed KPI output.
6. Export the Executive Control Tower to PDF.

## Limitations

- The dashboard is based on deterministic synthetic data.
- Excel is used as the presentation layer.
- Replenishment and count-control outputs are intentionally disconnected because they represent different analytical grains.
