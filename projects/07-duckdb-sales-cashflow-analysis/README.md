# DuckDB Sales Cashflow Analysis

This project builds a simple, reproducible sales-and-cash-flow analysis using Python, DuckDB, SQL, and fictional CSV data. It is designed for a public portfolio and focuses on the relationship between booked sales, gross margin, operating expenses, collections timing, and month-to-month cash pressure.

## Business problem

A small multi-region industrial-products distributor is growing sales but wants a clearer view of profitability, cash collections, operating expenses, and periods of cash pressure. The analysis focuses on whether booked revenue is translating into actual cash flow and where management attention may be needed.

## Questions answered

1. Which regions, products, and sales channels generate the highest revenue?
2. Which products and channels have the highest gross profit and gross-margin percentage?
3. How do sales booked compare with cash actually collected each month?
4. Which expense categories contribute most to operating cash outflows?
5. Which months have the greatest potential cash-flow pressure?
6. Which sales orders remain uncollected, and how many days have elapsed since the invoice/order date?
7. What management actions could be considered based on the results?

## Tools used

- Python 3
- DuckDB
- pandas
- SQL
- CSV data files
- Jupyter notebook for optional walkthrough
- matplotlib for a simple chart if needed

## Project structure

```text
projects/07-duckdb-sales-cashflow-analysis/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── sales_orders.csv
│   ├── cash_receipts.csv
│   ├── operating_expenses.csv
│   └── README.md
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_sales_performance.sql
│   ├── 03_cash_flow.sql
│   ├── 04_receivables_aging.sql
│   └── 05_management_summary.sql
├── scripts/
│   ├── setup_database.py
│   ├── run_analysis.py
│   └── export_reports.py
├── notebooks/
│   └── sales_cashflow_walkthrough.ipynb
├── outputs/
│   └── .gitkeep
└── docs/
    └── methodology.md
```

## Data note

All source data in this project is fully fictional and synthetic. It does not use employer, customer, production, or personally sensitive data. The project is intended for portfolio demonstration and analyst practice.

The input CSV files are committed so the project can be reproduced locally, while the generated DuckDB database is created as a local analysis artifact and excluded from Git.

## Workflow

1. CSV files in data/ supply source records.
2. DuckDB tables are created locally in sales_cashflow.duckdb.
3. SQL scripts in sql/ perform the core transformations and summary logic.
4. Python scripts automate table creation, analysis, and report export.
5. CSV exports are written to outputs/ for review and portfolio presentation.

## Setup and run

From the repository root or inside the project folder, run:

```bash
cd projects/07-duckdb-sales-cashflow-analysis
python -m venv .venv
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install dependencies:

```bash
pip install -r requirements.txt
python scripts/setup_database.py
python scripts/run_analysis.py
python scripts/export_reports.py
```

## Key metrics explained

- Revenue: total sales value booked from orders before considering costs or collections.
- COGS: cost of goods sold, representing the direct cost to fulfill the orders.
- Gross profit: revenue minus COGS; it shows the business value created before operating expenses.
- Gross-margin percentage: gross profit divided by revenue, shown as a percentage; it helps compare product profitability.
- Cash received: actual cash collected from customers during the month.
- Operating expenses: recurring and variable operating costs such as payroll, freight, marketing, software, and facilities.
- Operating cash flow: cash received minus operating expenses; this indicates near-term cash generation or pressure.
- Accounts receivable / sales not yet collected: order revenue that has been booked but not yet received in cash.

## Analyst findings

Placeholder text only — no fabricated results yet.

- Revenue concentration by region, channel, and product will be reviewed after running the scripts.
- Gross-margin analysis will identify the most profitable products and channels.
- Cash-collection gaps will be compared to booked sales by month.
- Receivables aging will highlight orders with the highest collection risk.
- Management actions will be based on the actual outputs generated from the dataset.

## Validation and limitations

- Verify source totals from the raw CSV files before interpreting outputs.
- Reconcile order revenue to cash receipts to check collection coverage and timing.
- This is fictional data and simplifies real accounting practices.
- Cash-flow reporting here is an operational-management view, not a formal GAAP financial statement.
- The project is designed for learning, portfolio work, and business-analysis communication, not audited financial reporting.

## Suggested next steps

- Add budget-versus-actual data.
- Add customer-level aging analysis.
- Add dashboard visuals.
- Convert CSV files to Parquet.
- Add scenario analysis for slower collections or higher expense growth.

## Quick local validation checklist

This project is designed to be reproducible from the documented local workflow: the DuckDB database is created from the tracked CSV source files, the SQL and Python analysis run locally, and the generated report CSVs are produced as output artifacts.

From the project root folder:

1. Open `README.md` and confirm the setup and run commands are clear.

2. Create and activate a Python virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. Install the project dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Build the local DuckDB database from the fictional CSV files:

   ```bash
   python scripts/setup_database.py
   ```

5. Confirm the local database file was created:

   ```bash
   ls -lh sales_cashflow.duckdb
   ```

6. Run the analysis and confirm that the management summary and receivables-aging preview print without errors:

   ```bash
   python scripts/run_analysis.py
   ```

7. Export the analysis results:

   ```bash
   python scripts/export_reports.py
   ```

8. Confirm the generated report files exist and contain data:

   ```bash
   ls -lh outputs/
   ```

   Expected report files:

   - `outputs/monthly_financial_summary.csv`
   - `outputs/product_performance.csv`
   - `outputs/cash_flow_summary.csv`
   - `outputs/receivables_aging.csv`

9. Confirm the generated database is not tracked by Git:

   ```bash
   git check-ignore sales_cashflow.duckdb
   git status
   ```

   Expected result: `sales_cashflow.duckdb` is ignored and does not appear as a file to commit.

## Project files to validate locally

- [README.md](README.md)
- [data/README.md](data/README.md)
- [docs/methodology.md](docs/methodology.md)
- [sql/01_create_tables.sql](sql/01_create_tables.sql)
- [scripts/setup_database.py](scripts/setup_database.py)
- [scripts/run_analysis.py](scripts/run_analysis.py)
- [scripts/export_reports.py](scripts/export_reports.py)

## Exact commands to run

```bash
cd projects/07-duckdb-sales-cashflow-analysis
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup_database.py
python scripts/run_analysis.py
python scripts/export_reports.py
```
