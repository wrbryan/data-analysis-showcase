-- DuckDB-compatible exploration queries.
-- From repo root: duckdb :memory: < projects/inventory-accuracy-stockout-risk/sql/analysis.sql
CREATE OR REPLACE TABLE products AS
SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/raw/products.csv');
CREATE OR REPLACE TABLE inventory_daily AS
SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/raw/inventory_daily.csv');
CREATE OR REPLACE TABLE cycle_counts AS
SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/raw/cycle_counts.csv');
CREATE OR REPLACE TABLE sales_daily AS
SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/raw/sales_daily.csv');

-- Location/SKU accuracy, ranked from least accurate.
SELECT sku, location_id,
       ROUND(100 * (1 - SUM(ABS(system_quantity - counted_quantity))
                    / NULLIF(SUM(system_quantity), 0)), 2) AS accuracy_pct,
       COUNT(*) AS count_events
FROM cycle_counts
GROUP BY 1, 2
ORDER BY accuracy_pct
LIMIT 20;

-- Stockout days by SKU and location.
SELECT sku, location_id,
       SUM(CASE WHEN closing_quantity <= 0 THEN 1 ELSE 0 END) AS stockout_days,
       ROUND(AVG(units_sold), 2) AS avg_daily_demand
FROM inventory_daily
GROUP BY 1, 2
ORDER BY stockout_days DESC;
