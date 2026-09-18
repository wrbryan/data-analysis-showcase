-- Receivables aging by order using a fixed analysis date.
-- Only orders with a remaining positive balance are included in the final aging report.

CREATE OR REPLACE VIEW receivables_aging AS
WITH order_totals AS (
    SELECT
        order_id,
        order_date,
        payment_terms_days,
        ROUND(SUM(revenue), 2) AS original_order_value
    FROM sales_orders
    GROUP BY order_id, order_date, payment_terms_days
),
receipt_totals AS (
    SELECT
        order_id,
        ROUND(SUM(cash_received), 2) AS total_collected
    FROM cash_receipts
    GROUP BY order_id
),
open_orders AS (
    SELECT
        o.order_id,
        o.order_date,
        o.original_order_value,
        COALESCE(r.total_collected, 0) AS total_collected,
        ROUND(o.original_order_value - COALESCE(r.total_collected, 0), 2) AS remaining_balance,
        DATE '2024-12-31' AS as_of_date,
        DATEDIFF('day', o.order_date, DATE '2024-12-31') AS days_outstanding
    FROM order_totals o
    LEFT JOIN receipt_totals r
        ON o.order_id = r.order_id
)
SELECT
    order_id,
    order_date,
    original_order_value,
    total_collected,
    remaining_balance,
    as_of_date,
    days_outstanding,
    CASE
        WHEN remaining_balance <= 0 THEN 'Current'
        WHEN days_outstanding BETWEEN 1 AND 30 THEN '1-30 Days Past Due'
        WHEN days_outstanding BETWEEN 31 AND 60 THEN '31-60 Days Past Due'
        ELSE '61+ Days Past Due'
    END AS aging_bucket
FROM open_orders
WHERE remaining_balance > 0
ORDER BY days_outstanding DESC, order_date;
