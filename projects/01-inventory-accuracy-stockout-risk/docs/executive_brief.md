# Portfolio Executive Brief

This is the quick-review companion to the full [executive summary](executive_summary.md).
It exists to help a recruiter or hiring manager understand the business
decision and reporting evidence without reading the complete analysis.

## Decision in one minute

The project separates enterprise replenishment risk at SKU grain from
inventory-control work at SKU/location grain. The detailed findings,
assumptions, and operating context remain in the full executive summary.

### Decision signals

- **8 of 300 SKUs** are currently Critical or High for replenishment attention.
- **6 SKU/location records** require weekly cycle counts.
- **472 SKU/location records** require biweekly cycle counts.
- **Z3-B03 and Z2-B02** contain the nonzero location adjustment exposure:
  `$106,636.60` and `$104,981.80`, respectively.
- Inventory record accuracy is **100.00%**, while cycle-count completion is
  **94.12%** and recount rate is **14.10%**.
- On-time shipment rate is **90.90%**.

### Recommended response

1. Review the 8 Critical + High SKUs for total supply position, inbound status,
   and replenishment-policy settings.
2. Execute the 6 weekly and 472 biweekly SKU/location cycle-count assignments.
3. Investigate recurring variance and adjustment exposure at Z3-B03 and Z2-B02.
4. Validate all data-quality checks before each refresh.

### Reporting evidence

The companion reporting package contains a two-page PDF and matching PNGs:

- Page 1: Executive Control Tower.
- Page 2: Action Queues and Evidence.

The report uses only the published Inventory Accuracy & Stockout Risk outputs and does not introduce new
analysis or KPIs.

> **Synthetic-data limitation:** This is deterministic demonstration data
> generated with seed `20260905`. It contains no employer, client, customer,
> confidential, personal, or proprietary data.
