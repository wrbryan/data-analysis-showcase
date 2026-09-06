# Data dictionary

> **Synthetic-data disclaimer:** The five source CSVs are deterministic
> synthetic records generated with seed `20260905`; they contain no real
> business, customer, supplier, or warehouse data.

The table below is the field-level contract used by the generator, analyzer,
and SQL. `source_file` identifies the owning source CSV.

| field_name | source_file | data_type | definition | business_use |
|---|---|---|---|---|
| `sku` | `product_master.csv` | string | Unique stock-keeping unit key | Join product policy to every fact |
| `product_name` | `product_master.csv` | string | Display name for the SKU | Reporting and action queues |
| `category` | `product_master.csv` | string | Product category | Segment risk and variance |
| `supplier` | `product_master.csv` | string | Primary synthetic supplier | Supplier-level review |
| `unit_cost` | `product_master.csv` | decimal | Standard cost per unit | Inventory and adjustment valuation |
| `lead_time_days` | `product_master.csv` | integer | Planned supplier lead time | Stockout trigger and priority context |
| `reorder_point` | `product_master.csv` | integer | Quantity at which replenishment is triggered | Replenishment policy |
| `safety_stock` | `product_master.csv` | integer | Buffer above reorder point | Risk context |
| `annual_demand_estimate` | `product_master.csv` | integer | Synthetic annual demand planning attribute | Reference planning field |
| `active_flag` | `product_master.csv` | string | `Y` indicates an active SKU | Scope filter |
| `snapshot_date` | `inventory_snapshot.csv` | date | Daily inventory observation date | Calendar denominator |
| `location` | `inventory_snapshot.csv` | string | Zone/bin location such as Z1-B01 | Localize variance and risk |
| `zone` | `inventory_snapshot.csv` | string | Warehouse zone | Zone rollups |
| `system_qty` | `inventory_snapshot.csv` | integer | Quantity recorded in the system | Inventory record baseline |
| `physical_qty` | `inventory_snapshot.csv` | integer | Physically observed quantity | Accuracy and stockout denominator |
| `transaction_id` | `transactions.csv` | string | Unique movement identifier | Movement lineage |
| `transaction_date` | `transactions.csv` | date | Date of movement | Activity trend |
| `transaction_type` | `transactions.csv` | string | Receipt, pick, adjustment, transfer, or return | Movement mix and controls |
| `quantity` | `transactions.csv` | integer | Positive units moved | Volume and exception analysis |
| `shift` | `transactions.csv` | string | Synthetic Day, Evening, or Night shift | Operational segmentation |
| `reference_id` | `transactions.csv` | string | Source document reference | Traceability |
| `order_id` | `orders.csv` | string | Unique customer order identifier | Order-line grain and service denominator |
| `order_date` | `orders.csv` | date | Date order was placed | Demand calendar |
| `ordered_qty` | `orders.csv` | integer | Units requested | Average daily demand |
| `shipped_qty` | `orders.csv` | integer | Units shipped | Partial-shipment and service analysis |
| `promised_date` | `orders.csv` | date | Customer promise date | On-time shipment denominator |
| `ship_date` | `orders.csv` | date | Actual shipment date | On-time shipment numerator |
| `customer_segment` | `orders.csv` | string | Commercial, Maintenance, Retail, Government, or Internal | Service segmentation |
| `count_id` | `cycle_counts.csv` | string | Unique cycle-count event | Count lineage |
| `count_date` | `cycle_counts.csv` | date | Scheduled count date | Completion calendar |
| `scheduled_flag` | `cycle_counts.csv` | string | `Y` when count was scheduled | Completion denominator |
| `completed_flag` | `cycle_counts.csv` | string | `Y` when scheduled count was completed | Completion numerator |
| `recount_flag` | `cycle_counts.csv` | string | `Y` when completed count requires recount | Recount rate and control |
| `variance_qty` | `cycle_counts.csv` | integer | Physical minus system quantity at count | Count exception size |
| `counter_team` | `cycle_counts.csv` | string | Synthetic team performing count | Team-level operations review |

## Derived outputs

`kpi_summary.csv` contains named KPI values and calculation notes.
`sku_risk_priorities.csv` is one row per SKU/location pair and includes signed
and absolute variance, adjustment value, risk flag, score, and count frequency.
`location_variance_summary.csv` rolls those measures to bins.
`stockout_risk_report.csv` contains currently flagged pairs.
`data_quality_checks.csv` is the publication-control table with exact fields
`check_name`, `status`, `records_affected`, and `details`.
