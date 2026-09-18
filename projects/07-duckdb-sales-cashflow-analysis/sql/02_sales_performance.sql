-- Sales performance summaries by time, geography, channel, and product.
-- These outputs are designed for executive review and a quick look at where revenue and margin are concentrated.

CREATE OR REPLACE VIEW revenue_by_month AS
SELECT
    DATE_TRUNC('month', order_date)::DATE AS sales_month,
    ROUND(SUM(revenue), 2) AS revenue
FROM sales_orders
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE VIEW revenue_by_region AS
SELECT
    region,
    ROUND(SUM(revenue), 2) AS revenue
FROM sales_orders
GROUP BY region
ORDER BY revenue DESC;

CREATE OR REPLACE VIEW revenue_by_channel AS
SELECT
    channel,
    ROUND(SUM(revenue), 2) AS revenue
FROM sales_orders
GROUP BY channel
ORDER BY revenue DESC;

CREATE OR REPLACE VIEW product_performance AS
SELECT
    product,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(SUM(cogs), 2) AS cogs,
    ROUND(SUM(gross_profit), 2) AS gross_profit,
    ROUND(
        100.0 * SUM(gross_profit) / NULLIF(SUM(revenue), 0),
        2
    ) AS gross_margin_pct
FROM sales_orders
GROUP BY product
ORDER BY gross_profit DESC;

CREATE OR REPLACE VIEW revenue_mom AS
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS sales_month,
        SUM(revenue) AS revenue
    FROM sales_orders
    GROUP BY 1
)
SELECT
    sales_month,
    revenue,
    LAG(revenue) OVER (ORDER BY sales_month) AS prior_month_revenue,
    revenue - LAG(revenue) OVER (ORDER BY sales_month) AS revenue_change,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY sales_month)) / NULLIF(LAG(revenue) OVER (ORDER BY sales_month), 0),
        4
    ) AS revenue_change_pct
FROM monthly_revenue
ORDER BY sales_month;
