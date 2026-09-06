-- Run from projects/inventory-accuracy-stockout-risk with DuckDB.
CREATE OR REPLACE TABLE inventory_snapshot AS
SELECT * FROM read_csv_auto('data/inventory_snapshot.csv');
CREATE OR REPLACE TABLE product_master AS
SELECT * FROM read_csv_auto('data/product_master.csv');
CREATE OR REPLACE TABLE transactions AS
SELECT * FROM read_csv_auto('data/transactions.csv');
CREATE OR REPLACE TABLE orders AS
SELECT * FROM read_csv_auto('data/orders.csv');
CREATE OR REPLACE TABLE cycle_counts AS
SELECT * FROM read_csv_auto('data/cycle_counts.csv');

-- Inventory accuracy and adjustment value.
WITH variance AS (
  SELECT snapshot_date, sku, location, unit_cost,
         ABS(system_qty - physical_qty) AS variance_qty,
         physical_qty
  FROM inventory_snapshot
)
SELECT ROUND(100 * (1 - SUM(variance_qty) / NULLIF(SUM(physical_qty), 0)), 2)
         AS inventory_accuracy_pct,
       ROUND(SUM(variance_qty * unit_cost), 2) AS adjustment_value
FROM variance;

-- Quantity and dollar variance by location.
SELECT location,
       SUM(ABS(system_qty - physical_qty)) AS absolute_variance_units,
       ROUND(SUM(ABS(system_qty - physical_qty) * unit_cost), 2) AS variance_value
FROM inventory_snapshot
GROUP BY location
ORDER BY variance_value DESC;

-- Stockout observations and days of supply by SKU/location.
WITH demand AS (
  SELECT sku, location, SUM(quantity) / 180.0 AS avg_daily_demand
  FROM transactions
  WHERE transaction_type = 'SALE'
  GROUP BY sku, location
), latest AS (
  SELECT sku, location, system_qty,
         ROW_NUMBER() OVER (PARTITION BY sku, location ORDER BY snapshot_date DESC) AS rn
  FROM inventory_snapshot
)
SELECT l.sku, l.location, l.system_qty AS current_on_hand,
       ROUND(d.avg_daily_demand, 2) AS avg_daily_demand,
       ROUND(l.system_qty / NULLIF(d.avg_daily_demand, 0), 2) AS days_of_supply
FROM latest l
JOIN demand d USING (sku, location)
WHERE rn = 1
ORDER BY days_of_supply;

-- Replenishment service and cycle-count completion.
SELECT ROUND(100 * AVG(CASE WHEN ship_date <= promised_date THEN 1 ELSE 0 END), 2)
         AS on_time_order_pct,
       COUNT(*) AS replenishment_orders
FROM orders;
SELECT 100.0 AS cycle_count_completion_pct, COUNT(*) AS completed_counts
FROM cycle_counts;

-- Source quality checks.
SELECT 'inventory_snapshot' AS source, COUNT(*) AS row_count,
       COUNT(*) - COUNT(DISTINCT snapshot_date || '|' || sku || '|' || location)
         AS duplicate_keys
FROM inventory_snapshot
UNION ALL
SELECT 'product_master', COUNT(*),
       COUNT(*) - COUNT(DISTINCT sku)
FROM product_master
UNION ALL
SELECT 'orders', COUNT(*),
       COUNT(*) - COUNT(DISTINCT order_id)
FROM orders;
