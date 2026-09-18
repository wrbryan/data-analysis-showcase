-- Management summary combining monthly booked sales, cost, margin, cash collection, and operating cash-flow measures.
-- This view is designed to be the main reporting output for a quick business review.

CREATE OR REPLACE VIEW management_summary AS
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS sales_month,
        ROUND(SUM(revenue), 2) AS revenue,
        ROUND(SUM(cogs), 2) AS cogs,
        ROUND(SUM(gross_profit), 2) AS gross_profit
    FROM sales_orders
    GROUP BY 1
),
monthly_cash_flow AS (
    SELECT
        month,
        cash_received,
        operating_expenses,
        operating_cash_flow,
        cumulative_operating_cash_flow
    FROM monthly_cash_flow
),
open_ar AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS sales_month,
        ROUND(SUM(revenue - COALESCE((
            SELECT SUM(cash_received)
            FROM cash_receipts cr
            WHERE cr.order_id = s.order_id
        ), 0)), 2) AS sales_not_collected
    FROM sales_orders s
    GROUP BY 1
)
SELECT
    ms.sales_month AS month,
    ms.revenue,
    ms.cogs,
    ms.gross_profit,
    ROUND(100.0 * ms.gross_profit / NULLIF(ms.revenue, 0), 2) AS gross_margin_pct,
    COALESCE(mcf.cash_received, 0) AS cash_received,
    COALESCE(mcf.operating_expenses, 0) AS operating_expenses,
    COALESCE(mcf.operating_cash_flow, 0) AS operating_cash_flow,
    COALESCE(ar.sales_not_collected, 0) AS sales_not_collected,
    COALESCE(mcf.cumulative_operating_cash_flow, 0) AS cumulative_operating_cash_flow
FROM monthly_sales ms
LEFT JOIN monthly_cash_flow mcf
    ON ms.sales_month = mcf.month
LEFT JOIN open_ar ar
    ON ms.sales_month = ar.sales_month
ORDER BY ms.sales_month;
