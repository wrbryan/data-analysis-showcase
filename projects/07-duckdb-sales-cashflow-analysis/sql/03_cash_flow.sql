-- Cash-flow view that compares booked sales to actual cash collections and monthly operating expense outflows.
-- This is an operational cash-view, not a GAAP financial statement.

CREATE OR REPLACE VIEW monthly_cash_flow AS
WITH revenue_by_month AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS sales_month,
        ROUND(SUM(revenue), 2) AS revenue_booked
    FROM sales_orders
    GROUP BY 1
),
receipts_by_month AS (
    SELECT
        DATE_TRUNC('month', receipt_date)::DATE AS cash_month,
        ROUND(SUM(cash_received), 2) AS cash_received
    FROM cash_receipts
    GROUP BY 1
),
expenses_by_month AS (
    SELECT
        DATE_TRUNC('month', expense_date)::DATE AS expense_month,
        ROUND(SUM(amount), 2) AS operating_expenses
    FROM operating_expenses
    GROUP BY 1
)
SELECT
    r.sales_month AS month,
    r.revenue_booked,
    COALESCE(c.cash_received, 0) AS cash_received,
    COALESCE(e.operating_expenses, 0) AS operating_expenses,
    COALESCE(c.cash_received, 0) - COALESCE(e.operating_expenses, 0) AS operating_cash_flow,
    r.revenue_booked - COALESCE(c.cash_received, 0) AS sales_booked_minus_cash_received,
    SUM(COALESCE(c.cash_received, 0) - COALESCE(e.operating_expenses, 0)) OVER (
        ORDER BY r.sales_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_operating_cash_flow
FROM revenue_by_month r
LEFT JOIN receipts_by_month c
    ON r.sales_month = c.cash_month
LEFT JOIN expenses_by_month e
    ON r.sales_month = e.expense_month
ORDER BY r.sales_month;
