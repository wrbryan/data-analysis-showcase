-- Run from repository root with DuckDB.
-- 1. Source registration
CREATE OR REPLACE TABLE inventory_snapshot AS SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/inventory_snapshot.csv');
CREATE OR REPLACE TABLE product_master AS SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/product_master.csv');
CREATE OR REPLACE TABLE transactions AS SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/transactions.csv');
CREATE OR REPLACE TABLE orders AS SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/orders.csv');
CREATE OR REPLACE TABLE cycle_counts AS SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/data/cycle_counts.csv');
-- 2. Inventory accuracy
SELECT sku, location_id, ROUND(100 * (1 - SUM(ABS(system_quantity-counted_quantity))/NULLIF(SUM(system_quantity),0)),2) accuracy_pct FROM cycle_counts GROUP BY 1,2 ORDER BY accuracy_pct;
-- 3. Stockout risk
SELECT sku, location_id, SUM(closing_quantity<=0) stockout_days, MAX(snapshot_date) latest_date FROM inventory_snapshot GROUP BY 1,2 ORDER BY stockout_days DESC;
-- 4. Action queue
SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/outputs/sku_location_action_queue.csv') ORDER BY risk_score DESC;
-- 5. Data quality checks
SELECT * FROM read_csv_auto('projects/inventory-accuracy-stockout-risk/outputs/data_quality_checks.csv');
