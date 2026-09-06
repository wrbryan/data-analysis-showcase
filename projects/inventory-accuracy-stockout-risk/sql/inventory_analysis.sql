-- Inventory Accuracy & Stockout Risk
-- Run from the repository root with DuckDB.  Each numbered section is
-- independently useful; the CTE names mirror the Python calculations.

-- ============================================================================
-- 1. SOURCE REGISTRATION
-- ============================================================================
CREATE OR REPLACE TABLE inventory_snapshot AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/inventory_snapshot.csv'
);
CREATE OR REPLACE TABLE product_master AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/product_master.csv'
);
CREATE OR REPLACE TABLE transactions AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/transactions.csv'
);
CREATE OR REPLACE TABLE orders AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/orders.csv'
);
CREATE OR REPLACE TABLE cycle_counts AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/cycle_counts.csv'
);

-- ============================================================================
-- 2. INVENTORY ACCURACY AND ADJUSTMENT VALUE
-- ============================================================================
WITH inventory_variance AS (
  SELECT
    snapshot_date, sku, location, system_qty, physical_qty, unit_cost,
    system_qty - physical_qty AS quantity_variance,
    ABS(system_qty - physical_qty) AS absolute_variance,
    ABS(system_qty - physical_qty) * unit_cost AS adjustment_value,
    GREATEST(physical_qty, 1) AS accuracy_denominator
  FROM inventory_snapshot
),
accuracy AS (
  SELECT
    1 - SUM(absolute_variance) / NULLIF(SUM(accuracy_denominator), 0)
      AS weighted_inventory_record_accuracy,
    SUM(adjustment_value) AS adjustment_value
  FROM inventory_variance
)
SELECT
  ROUND(100 * weighted_inventory_record_accuracy, 2)
    AS inventory_accuracy_pct,
  ROUND(adjustment_value, 2) AS adjustment_value
FROM accuracy;

-- ============================================================================
-- 3. DEMAND, DAYS OF SUPPLY, AND STOCKOUT RISK
-- ============================================================================
WITH calendar AS (
  SELECT DATE_DIFF(
    'day', MIN(snapshot_date)::DATE, MAX(snapshot_date)::DATE
  ) + 1 AS calendar_days
  FROM inventory_snapshot
),
sku_demand AS (
  SELECT sku, SUM(ordered_qty) / MAX(calendar_days) AS average_daily_demand
  FROM orders CROSS JOIN calendar
  GROUP BY sku
),
location_count AS (
  SELECT sku, COUNT(DISTINCT location) AS locations
  FROM inventory_snapshot
  GROUP BY sku
),
latest AS (
  SELECT *
  FROM (
    SELECT
      i.*, ROW_NUMBER() OVER (
        PARTITION BY sku, location ORDER BY snapshot_date DESC
      ) AS row_number
    FROM inventory_snapshot i
  )
  WHERE row_number = 1
),
stockout_risk AS (
  SELECT
    latest.sku, latest.location, latest.physical_qty,
    sku_demand.average_daily_demand / location_count.locations
      AS average_daily_demand,
    latest.physical_qty /
      NULLIF(sku_demand.average_daily_demand / location_count.locations, 0)
      AS days_of_supply,
    product_master.reorder_point, product_master.lead_time_days,
    latest.physical_qty <= product_master.reorder_point
      OR latest.physical_qty /
         NULLIF(sku_demand.average_daily_demand / location_count.locations, 0)
         <= product_master.lead_time_days AS stockout_risk_flag
  FROM latest
  JOIN sku_demand USING (sku)
  JOIN location_count USING (sku)
  JOIN product_master USING (sku)
)
SELECT *
FROM stockout_risk
WHERE stockout_risk_flag
ORDER BY days_of_supply NULLS FIRST;

-- ============================================================================
-- 4. CYCLE COUNTS, SHIPMENT SERVICE, AND PRIORITY SCORE
-- ============================================================================
WITH count_kpis AS (
  SELECT
    SUM(scheduled_flag = 'Y') AS scheduled_counts,
    SUM(scheduled_flag = 'Y' AND completed_flag = 'Y') AS completed_counts,
    SUM(scheduled_flag = 'Y' AND completed_flag = 'Y' AND recount_flag = 'Y')
      AS recounts
  FROM cycle_counts
),
shipment_kpis AS (
  SELECT
    SUM(shipped_qty > 0) AS shipped_orders,
    SUM(shipped_qty > 0 AND ship_date <= promised_date) AS on_time_shipments
  FROM orders
)
SELECT
  100 * completed_counts / NULLIF(scheduled_counts, 0)
    AS cycle_count_completion_pct,
  100 * recounts / NULLIF(completed_counts, 0) AS recount_rate_pct,
  100 * on_time_shipments / NULLIF(shipped_orders, 0)
    AS on_time_shipment_rate_pct
FROM count_kpis CROSS JOIN shipment_kpis;

-- Priority score components:
-- 35% adjustment value, 30% current stockout risk, 20% variance recurrence,
-- 15% context (inventory value, lead time, and location recurrence).
WITH pair_variance AS (
  SELECT
    i.sku, i.location, MAX(i.snapshot_date) AS latest_date,
    ANY_VALUE(i.system_qty ORDER BY i.snapshot_date DESC) AS system_qty,
    ANY_VALUE(i.physical_qty ORDER BY i.snapshot_date DESC) AS physical_qty,
    SUM(ABS(i.system_qty - i.physical_qty) * i.unit_cost) AS adjustment_value,
    SUM(ABS(i.system_qty - i.physical_qty) > 0) AS variance_event_count,
    COUNT(*) AS snapshot_count,
    SUM(GREATEST(i.physical_qty, 1)) AS accuracy_denominator,
    ANY_VALUE(i.physical_qty ORDER BY i.snapshot_date DESC)
      * ANY_VALUE(i.unit_cost ORDER BY i.snapshot_date DESC) AS inventory_value
  FROM inventory_snapshot i
  GROUP BY i.sku, i.location
),
sku_demand AS (
  SELECT sku, SUM(ordered_qty) / (
    DATE_DIFF('day', MIN(order_date)::DATE, MAX(order_date)::DATE) + 1
  ) AS average_daily_demand
  FROM orders
  GROUP BY sku
),
location_recurrence AS (
  SELECT location, SUM(ABS(system_qty - physical_qty) > 0)
    AS location_variance_events
  FROM inventory_snapshot
  GROUP BY location
),
pair_metrics AS (
  SELECT
    pair_variance.*, product_master.reorder_point,
    product_master.lead_time_days,
    sku_demand.average_daily_demand / COUNT(*) OVER (PARTITION BY pair_variance.sku)
      AS average_daily_demand,
    pair_variance.physical_qty <= product_master.reorder_point
      OR pair_variance.physical_qty /
         NULLIF(sku_demand.average_daily_demand /
           COUNT(*) OVER (PARTITION BY pair_variance.sku), 0)
         <= product_master.lead_time_days AS stockout_risk,
    location_recurrence.location_variance_events,
    MAX(pair_variance.adjustment_value) OVER () AS max_adjustment_value,
    MAX(pair_variance.inventory_value) OVER () AS max_inventory_value,
    MAX(product_master.lead_time_days) OVER () AS max_lead_time,
    MAX(location_recurrence.location_variance_events) OVER ()
      AS max_location_recurrence
  FROM pair_variance
  JOIN product_master USING (sku)
  JOIN sku_demand USING (sku)
  JOIN location_recurrence USING (location)
),
normalized AS (
  SELECT
    pair_metrics.*,
    100 * adjustment_value / MAX(adjustment_value) OVER ()
      AS adjustment_value_score,
    100 * variance_event_count / NULLIF(snapshot_count, 0)
      AS variance_recurrence_score,
    100 * location_variance_events / NULLIF(max_location_recurrence, 0)
      AS location_recurrence_score
  FROM pair_metrics
)
SELECT
  sku, location, ROUND(
    0.35 * adjustment_value_score
    + 0.30 * CASE WHEN stockout_risk THEN 100 ELSE 0 END
    + 0.20 * variance_recurrence_score
    + 0.15 * (
      40 * inventory_value / NULLIF(max_inventory_value, 0)
      + 30 * lead_time_days / NULLIF(max_lead_time, 0)
      + 30 * location_recurrence_score / 100
    ), 2) AS priority_score
FROM normalized
ORDER BY priority_score DESC;

-- ============================================================================
-- 5. DATA QUALITY CHECKS
-- ============================================================================
SELECT 'inventory_snapshot' AS source_file, COUNT(*) AS records,
  COUNT(*) - COUNT(DISTINCT snapshot_date || '|' || sku || '|' || location)
    AS duplicate_keys
FROM inventory_snapshot
UNION ALL
SELECT 'product_master', COUNT(*), COUNT(*) - COUNT(DISTINCT sku)
FROM product_master
UNION ALL
SELECT 'transactions', COUNT(*), COUNT(*) - COUNT(DISTINCT transaction_id)
FROM transactions
UNION ALL
SELECT 'orders', COUNT(*), COUNT(*) - COUNT(DISTINCT order_id)
FROM orders
UNION ALL
SELECT 'cycle_counts', COUNT(*), COUNT(*) - COUNT(DISTINCT count_id)
FROM cycle_counts;

SELECT transaction_type, COUNT(*) AS records
FROM transactions
GROUP BY transaction_type
ORDER BY transaction_type;
