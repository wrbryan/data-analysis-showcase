# Data dictionary

## Source fields
- `sku`, `location_id`: business keys.
- `snapshot_date`, `transaction_date`, `count_date`, `order_date`: ISO dates.
- `closing_quantity`, `system_quantity`, `counted_quantity`: unit balances.
- `transaction_type`, `quantity`: movement classification and units.
- `reorder_point`, `lead_time_days`: replenishment policy inputs.

## Output fields
- `accuracy_pct`: pair-level cycle-count accuracy.
- `risk_score`, `risk_band`: stockout prioritization.
- `days_of_cover`: current stock divided by average daily sales.
- `duplicate_key_count`, `null_value_count`, `status`: quality controls.
