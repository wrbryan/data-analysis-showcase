# Source data

> **Synthetic-data disclaimer:** Every full source row is deterministic
> synthetic data generated with seed `20260905`; it does not represent a real
> company, customer, supplier, warehouse, or transaction history.

## Regeneration

From the repository root:

```bash
python projects/01-inventory-accuracy-stockout-risk/python/generate_synthetic_data.py
python projects/01-inventory-accuracy-stockout-risk/python/analyze_inventory.py
```

Full inputs are written to ignored `data/generated/`; compact checked-in
examples under `data/sample/` are preserved for schema inspection only.

The source period is `2026-01-01` through `2026-06-29` (180 days): 300 SKUs,
648,000 SKU/location/day snapshots, 12 bins, 13,500 SKU-level orders, about
585,000 movements, and 46,800 scheduled counts.

| File | Grain | Required columns |
|---|---|---|
| `product_master.csv` | one row per SKU | `sku`, `product_name`, `category`, `supplier`, `unit_cost`, `lead_time_days`, `reorder_point`, `safety_stock`, `annual_demand_estimate`, `active_flag` |
| `inventory_snapshot.csv` | SKU/location/day | `snapshot_date`, `sku`, `location`, `zone`, `system_qty`, `physical_qty`, `unit_cost` |
| `transactions.csv` | inventory movement | `transaction_id`, `transaction_date`, `sku`, `location`, `zone`, `transaction_type`, `quantity`, `shift`, `reference_id` |
| `orders.csv` | SKU customer order line | `order_id`, `order_date`, `sku`, `ordered_qty`, `shipped_qty`, `promised_date`, `ship_date`, `customer_segment` |
| `cycle_counts.csv` | scheduled SKU/location count | `count_id`, `count_date`, `sku`, `location`, `zone`, `scheduled_flag`, `completed_flag`, `recount_flag`, `variance_qty`, `counter_team` |

The generator includes all six movement types and partial/delayed shipments.
Most products and locations follow healthy replenishment behavior. A small
set of high-value, long-lead, fast-moving SKUs has constrained supply, while
only two bins carry recurring physical/system variance. Recounts are triggered
by the generated count variance pattern, rather than by a fixed output-rate
target.

Demand and replenishment policy are evaluated at SKU grain. Inventory control
is evaluated at SKU/location grain; low quantity in one bin is not an
enterprise stockout signal.
