# Inventory Accuracy & Stockout Risk Reporting Package

This folder contains the two-page Python-generated reporting package built only
from the published Inventory Accuracy & Stockout Risk output CSVs.

## Files

- `inventory-accuracy-stockout-risk-report.pdf` - two-page report.
- `01-executive-control-tower.png` - Page 1: validated KPI cards, risk distributions, location exposure, and Action Now callout.
- `02-action-queues-and-evidence.png` - Page 2: replenishment queue, count-priority evidence, location exposure, and action owners.

## Reproduce

From the repository root:

```bash
python -m pip install -r projects/inventory-accuracy-stockout-risk/requirements-reporting.txt
python projects/inventory-accuracy-stockout-risk/python/generate_reporting_package.py
```

The script reads only the published files in
`projects/inventory-accuracy-stockout-risk/outputs/`. It validates required
columns, expected row counts, and all 26 `PASS` data-quality checks before
creating the outputs.

The report is deterministic: category ordering, queue ranking, numeric
formatting, page dimensions, and output filenames are explicit. The package is
presentation evidence for deterministic synthetic portfolio data, not a live
operational reporting system.
