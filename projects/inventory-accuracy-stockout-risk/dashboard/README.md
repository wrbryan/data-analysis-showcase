# Dashboard specification

The CSV outputs are ready for a Power BI, Tableau, or spreadsheet dashboard.
Use `kpi_summary.csv` for the headline cards and the other reports as detail
tables.

1. **Executive overview** — inventory accuracy, adjustment value, stockout
   rate, inventory turnover, days of supply, and count completion.
2. **Variance analysis** — adjustment value and accuracy by SKU, category,
   supplier, zone, bin, and risk priority.
3. **Stockout and excess risk** — current on-hand, demand, days of supply,
   reorder point, safety stock, stockout days, excess units, and risk band.
4. **Cycle-count performance** — count completion, count accuracy, recounts,
   and variance by location and counter.
5. **Action tracker** — filter `sku_risk_priorities.csv` to `count_priority =
   Priority`; assign an owner, target date, status, and expected impact.
