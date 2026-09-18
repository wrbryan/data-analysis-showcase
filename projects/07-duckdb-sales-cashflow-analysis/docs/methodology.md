# Methodology

## Data model

The data model is intentionally simple and uses a single shared key, order_id, to connect sales activity to collections and cash flow. The sales_orders table stores the booked revenue and cost for each order. The cash_receipts table captures actual cash received against those orders. The operating_expenses table records the operating costs used to measure monthly cash outflows.

This relationship is the core of the analysis:

- sales_orders: what was sold and when
- cash_receipts: what was collected and when
- operating_expenses: what the business spent during the same period

## Sales booked versus cash collected

Booked sales and cash collected are not the same thing. A customer may place an order in one month and pay weeks or months later depending on payment terms. This creates a timing gap between revenue recognition and cash realization. In operational analysis, that gap is useful because it highlights collection risk and working-capital pressure even when revenue looks strong.

## Why gross margin matters

Revenue alone can be misleading. A product with high sales volume may not generate the strongest operational return if its cost structure is weak. Gross margin helps separate products that produce strong dollars from products that are expensive to sell. It is especially useful when comparing products, channels, and regions.

## Receivables aging and collection risk

Receivables aging shows how long balances have remained unpaid. The analysis compares the order date to an as-of date and groups outstanding balances into age buckets. This helps identify which orders are current, which are becoming overdue, and which may need collection follow-up. It is a practical operational view of cash risk without moving into formal accounting treatment.

## DuckDB versus an Excel workflow

This project reflects a streamlined version of a common Excel analytics workflow:

- CSV input = source workbook/export
- SQL transformations = Power Query and calculated columns
- GROUP BY summaries = PivotTables
- exported report CSVs = recurring reporting output

DuckDB replaces several spreadsheet steps in-process, using local files and SQL queries rather than a separate database server. The database resides in the project folder as a portable, local file and can be recreated from CSV source files at any time.

## Local and portable design

The project uses a local DuckDB database file rather than a server-based database. This keeps the analysis portable, simple, and easy to run for a portfolio or classroom setting. No cloud infrastructure or database service is required for this workflow.
