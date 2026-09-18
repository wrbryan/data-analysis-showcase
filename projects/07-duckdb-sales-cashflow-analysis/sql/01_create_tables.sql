-- Create the foundational fact tables used throughout the analysis.
-- Each table is built directly from local CSV files so the project remains portable and easy to reproduce.

CREATE OR REPLACE TABLE sales_orders AS
SELECT
    order_id,
    CAST(order_date AS DATE) AS order_date,
    region,
    channel,
    product,
    CAST(units AS INTEGER) AS units,
    CAST(unit_price AS DOUBLE) AS unit_price,
    CAST(unit_cost AS DOUBLE) AS unit_cost,
    CAST(payment_terms_days AS INTEGER) AS payment_terms_days,
    CAST(units AS DOUBLE) * CAST(unit_price AS DOUBLE) AS revenue,
    CAST(units AS DOUBLE) * CAST(unit_cost AS DOUBLE) AS cogs,
    (CAST(units AS DOUBLE) * CAST(unit_price AS DOUBLE)) - (CAST(units AS DOUBLE) * CAST(unit_cost AS DOUBLE)) AS gross_profit
FROM read_csv_auto(
    'data/sales_orders.csv',
    header = true,
    all_varchar = false
);

CREATE OR REPLACE TABLE cash_receipts AS
SELECT
    receipt_id,
    order_id,
    CAST(receipt_date AS DATE) AS receipt_date,
    CAST(cash_received AS DOUBLE) AS cash_received
FROM read_csv_auto(
    'data/cash_receipts.csv',
    header = true,
    all_varchar = false
);

CREATE OR REPLACE TABLE operating_expenses AS
SELECT
    expense_id,
    CAST(expense_date AS DATE) AS expense_date,
    expense_category,
    region,
    CAST(amount AS DOUBLE) AS amount
FROM read_csv_auto(
    'data/operating_expenses.csv',
    header = true,
    all_varchar = false
);
