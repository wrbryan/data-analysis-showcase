# Source data

> **Synthetic-data disclaimer:** Every full source row is generated
> deterministically with seed `20260905`. These files do not represent a real
> company, customer, supplier, warehouse, or transaction history.

## Regeneration

Run from the repository root:

```bash
python projects/inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/inventory-accuracy-stockout-risk/python/analyze_inventory.py
```

The generator writes the full, ignored population to `data/generated/`.
`data/sample/` contains only compact checked-in examples for review and schema
inspection; the analyzer and SQL never read those samples. Regenerate after
changing the generator rather than editing generated files by hand.

The generated source period is `2026-01-01` through `2026-06-29` (180 calendar
days). It contains 300 SKUs, 10 categories, 5 suppliers, 12 bins across zones
Z1-Z3, 648,000 inventory snapshots, 555,773 movements, 162,000 orders, and
46,800 cycle counts.

| File | Grain | Required columns |
|---|---|---|
| `product_master.csv` | one row per SKU | `sku`, `product_name`, `category`, `supplier`, `unit_cost`, `lead_time_days`, `reorder_point`, `safety_stock`, `annual_demand_estimate`, `active_flag` |
| `inventory_snapshot.csv` | SKU/location/day | `snapshot_date`, `sku`, `location`, `zone`, `system_qty`, `physical_qty`, `unit_cost` |
| `transactions.csv` | inventory movement | `transaction_id`, `transaction_date`, `sku`, `location`, `zone`, `transaction_type`, `quantity`, `shift`, `reference_id` |
| `orders.csv` | customer order line | `order_id`, `order_date`, `sku`, `ordered_qty`, `shipped_qty`, `promised_date`, `ship_date`, `customer_segment` |
| `cycle_counts.csv` | scheduled count | `count_id`, `count_date`, `sku`, `location`, `zone`, `scheduled_flag`, `completed_flag`, `recount_flag`, `variance_qty`, `counter_team` |

`transactions.csv` includes `RECEIPT`, `PICK`, `ADJUSTMENT`, `TRANSFER_IN`,
`TRANSFER_OUT`, and `RETURN`. Orders deliberately include partial and delayed
shipments. The analyzer validates required fields, unique keys, references,
dates, non-negative inventory, movement coverage, order behavior, and minimum
volumes before publishing reports.
