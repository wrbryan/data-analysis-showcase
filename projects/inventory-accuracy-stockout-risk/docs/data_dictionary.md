# Data dictionary

All dates are ISO `YYYY-MM-DD`; quantities are non-negative units.

* `sku`: stable product identifier.
* `location_id`: distribution-center identifier.
* `opening_quantity`, `closing_quantity`: daily system balances.
* `units_sold`, `units_received`: daily inventory movements.
* `system_quantity`, `counted_quantity`: quantities at a physical cycle count.
* `accuracy_pct`: pair-level record accuracy after absolute variance.
* `days_of_cover`: current stock divided by average daily demand.
* `risk_score` / `risk_band`: stockout prioritization output from 0–100 / Low,
  Medium, High.
