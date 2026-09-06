# Data dictionary

## Source tables

### `inventory_snapshot.csv`

`snapshot_date` is the daily observation date; `sku` and `location` form the
business key. `system_qty` is the recorded quantity, `physical_qty` is the
observed quantity, and `unit_cost` is the valuation cost per unit.

### `product_master.csv`

`sku` identifies the item. `description`, `category`, and `supplier` describe
it. `lead_time_days` is the replenishment lead time. `reorder_point` is the
replenishment trigger, `safety_stock` is the buffer, and `unit_cost` values it.

### `transactions.csv`

`transaction_date`, `sku`, and `location` identify a movement. `transaction_type`
is `SALE` or `RECEIPT`; `quantity` is positive units; `shift` is A, B, or C.

### `orders.csv`

`order_id` identifies the replenishment order. `order_date`, `promised_date`,
and `ship_date` are ISO dates. `ordered_qty` and `shipped_qty` are units.

### `cycle_counts.csv`

`count_id`, `count_date`, `sku`, and `location` identify a count. `counter` is
the counting team, `variance_qty` is physical minus system quantity, and
`recount_flag` identifies counts requiring a recount.

## Output tables

- `kpi_summary.csv`: KPI name, value, unit, period, and definition.
- `sku_risk_priorities.csv`: SKU-level variance, service risk, inventory value,
  count priority, and recommended action.
- `location_variance_summary.csv`: zone/bin variance and recount summary.
- `stockout_risk_report.csv`: SKU/location stockout, demand, supply, and
  excess-risk measures.
- `data_quality_checks.csv`: required-field, duplicate, referential-integrity,
  date-range, and minimum-volume checks.

Accuracy is `100 * (1 - ABS(system_qty - physical_qty) / physical_qty)`,
bounded at zero. Adjustment value is absolute variance times unit cost.
