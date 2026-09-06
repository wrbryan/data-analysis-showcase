-- Inventory Accuracy & Stockout Risk (DuckDB reference)
-- The Python analyzer is the publication path. This script documents the same
-- two complementary queues and can be run from the repository root.

CREATE OR REPLACE TABLE inventory_snapshot AS
SELECT * FROM read_csv_auto(
  'projects/01-inventory-accuracy-stockout-risk/data/generated/inventory_snapshot.csv'
);
CREATE OR REPLACE TABLE product_master AS
SELECT * FROM read_csv_auto(
  'projects/01-inventory-accuracy-stockout-risk/data/generated/product_master.csv'
);
CREATE OR REPLACE TABLE transactions AS
SELECT * FROM read_csv_auto(
  'projects/01-inventory-accuracy-stockout-risk/data/generated/transactions.csv'
);
CREATE OR REPLACE TABLE orders AS
SELECT * FROM read_csv_auto(
  'projects/01-inventory-accuracy-stockout-risk/data/generated/orders.csv'
);
CREATE OR REPLACE TABLE cycle_counts AS
SELECT * FROM read_csv_auto(
  'projects/01-inventory-accuracy-stockout-risk/data/generated/cycle_counts.csv'
);

-- ============================================================================
-- 1. SKU-LEVEL REPLENISHMENT QUEUE
-- ============================================================================
CREATE OR REPLACE TABLE sku_replenishment_queue AS
WITH latest AS (
  SELECT * EXCLUDE (rn)
  FROM (
    SELECT i.*, ROW_NUMBER() OVER (
      PARTITION BY sku, location ORDER BY snapshot_date DESC
    ) AS rn
    FROM inventory_snapshot i
  )
  WHERE rn = 1
),
period AS (
  SELECT DATE_DIFF('day', MIN(snapshot_date)::DATE, MAX(snapshot_date)::DATE) + 1 AS days
  FROM inventory_snapshot
),
demand AS (
  SELECT sku, SUM(ordered_qty) / MAX(days) AS average_daily_demand
  FROM orders CROSS JOIN period GROUP BY sku
),
exposure AS (
  SELECT sku, SUM(ABS(system_qty - physical_qty) * unit_cost) AS adjustment_exposure,
    SUM(ABS(system_qty - physical_qty)) AS total_absolute_quantity_variance
  FROM inventory_snapshot GROUP BY sku
),
position AS (
  SELECT sku, COUNT(*) AS location_count, SUM(system_qty) AS total_system_qty,
    SUM(physical_qty) AS total_physical_qty,
    SUM(system_qty - physical_qty) AS total_quantity_variance,
    SUM(physical_qty * unit_cost) AS inventory_value,
    MAX(unit_cost) AS unit_cost
  FROM latest GROUP BY sku
),
base AS (
  SELECT position.*, m.product_name, m.category, m.supplier, m.reorder_point,
    m.safety_stock, m.lead_time_days, d.average_daily_demand,
    e.adjustment_exposure, e.total_absolute_quantity_variance,
    position.total_system_qty, position.total_physical_qty,
    position.total_quantity_variance, position.inventory_value,
    position.location_count,
    position.total_physical_qty / NULLIF(d.average_daily_demand, 0) AS days_of_supply
  FROM position
  JOIN product_master m USING (sku)
  JOIN demand d USING (sku)
  JOIN exposure e USING (sku)
),
thresholds AS (
  SELECT QUANTILE_CONT(inventory_value, 0.75) AS inventory_value_p75,
    QUANTILE_CONT(adjustment_exposure, 0.75) AS adjustment_exposure_p75,
    QUANTILE_CONT(unit_cost, 0.75) AS unit_cost_p75
  FROM base
),
classified AS (
  SELECT b.*,
    (b.inventory_value >= t.inventory_value_p75
      OR b.adjustment_exposure >= t.adjustment_exposure_p75
      OR b.unit_cost >= t.unit_cost_p75) AS materiality,
    b.total_physical_qty <= b.reorder_point AS reorder_trigger,
    b.total_physical_qty <= b.safety_stock AS safety_trigger,
    b.days_of_supply <= b.lead_time_days AS lead_trigger
  FROM base b CROSS JOIN thresholds t
)
SELECT *,
  CASE
    WHEN total_physical_qty = 0 OR days_of_supply <= 0.25 * lead_time_days
      THEN 'Critical'
    WHEN safety_trigger AND lead_trigger AND materiality THEN 'Critical'
    WHEN reorder_trigger AND lead_trigger THEN 'High'
    WHEN reorder_trigger OR lead_trigger OR (materiality AND adjustment_exposure > 0)
      THEN 'Watch'
    ELSE 'Routine'
  END AS replenishment_tier
FROM classified;

SELECT replenishment_tier, COUNT(*) AS sku_count
FROM sku_replenishment_queue
GROUP BY replenishment_tier
ORDER BY CASE replenishment_tier
  WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Watch' THEN 3 ELSE 4 END;

-- Focused stockout report: SKU grain only, and only Critical + High.
SELECT sku, product_name, category, supplier, total_physical_qty,
  average_daily_demand, days_of_supply, reorder_point, safety_stock,
  lead_time_days, replenishment_tier
FROM sku_replenishment_queue
WHERE replenishment_tier IN ('Critical', 'High')
ORDER BY CASE replenishment_tier WHEN 'Critical' THEN 1 ELSE 2 END, days_of_supply;

-- ============================================================================
-- 2. SKU/LOCATION CYCLE-COUNT AND INVENTORY-CONTROL QUEUE
-- ============================================================================
CREATE OR REPLACE TABLE sku_location_count_queue AS
WITH latest AS (
  SELECT * EXCLUDE (rn)
  FROM (
    SELECT i.*, ROW_NUMBER() OVER (
      PARTITION BY sku, location ORDER BY snapshot_date DESC
    ) AS rn
    FROM inventory_snapshot i
  )
  WHERE rn = 1
),
variance_history AS (
  SELECT sku, location,
    SUM(ABS(system_qty - physical_qty) * unit_cost) AS location_adjustment_exposure,
    SUM(ABS(system_qty - physical_qty) > 0) AS variance_event_count
  FROM inventory_snapshot GROUP BY sku, location
),
counts AS (
  SELECT sku, location, COUNT(*) AS count_records,
    SUM(completed_flag = 'Y') AS completed_count,
    SUM(completed_flag = 'Y' AND recount_flag = 'Y') AS recount_count
  FROM cycle_counts GROUP BY sku, location
),
location_recurrence AS (
  SELECT location, SUM(variance_event_count >= 2) AS recurring_variance_pairs
  FROM variance_history GROUP BY location
),
transactions_by_pair AS (
  SELECT sku, location, COUNT(*) AS transaction_volume
  FROM transactions GROUP BY sku, location
)
SELECT l.sku, p.product_name, p.category, l.location, l.zone,
  l.system_qty AS latest_system_qty, l.physical_qty AS latest_physical_qty,
  l.system_qty - l.physical_qty AS quantity_variance,
  ABS(l.system_qty - l.physical_qty) AS absolute_quantity_variance,
  l.unit_cost, l.physical_qty * l.unit_cost AS inventory_value,
  v.location_adjustment_exposure, v.variance_event_count,
  v.variance_event_count >= 2 AS recurring_variance,
  c.count_records, c.recount_count,
  100 * c.recount_count / NULLIF(c.completed_count, 0) AS recount_rate,
  t.transaction_volume, r.recurring_variance_pairs >= 2 AS location_recurrence_flag,
  CASE
    WHEN v.variance_event_count >= 2
      AND ABS(l.system_qty - l.physical_qty) >= 2
      AND c.recount_count >= 3 AND r.recurring_variance_pairs >= 2
      THEN 'Critical'
    WHEN v.variance_event_count >= 2
      AND (c.recount_count >= 2 OR v.location_adjustment_exposure >=
        (SELECT QUANTILE_CONT(location_adjustment_exposure, 0.75)
         FROM variance_history))
      THEN 'High'
    WHEN v.variance_event_count >= 2 OR c.recount_count > 0
      OR ABS(l.system_qty - l.physical_qty) > 0
      THEN 'Watch'
    ELSE 'Routine'
  END AS control_tier
FROM latest l
JOIN product_master p USING (sku)
JOIN variance_history v USING (sku, location)
JOIN counts c USING (sku, location)
JOIN transactions_by_pair t USING (sku, location)
JOIN location_recurrence r USING (location);

SELECT control_tier, COUNT(*) AS sku_location_count
FROM sku_location_count_queue
GROUP BY control_tier
ORDER BY CASE control_tier
  WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Watch' THEN 3 ELSE 4 END;

-- ============================================================================
-- 3. KPI AND QUALITY RECONCILIATION
-- ============================================================================
SELECT
  100 * (1 - SUM(ABS(system_qty - physical_qty)) /
    NULLIF(SUM(GREATEST(physical_qty, 1)), 0)) AS inventory_accuracy_pct,
  SUM(ABS(system_qty - physical_qty) * unit_cost) AS adjustment_value
FROM inventory_snapshot;

SELECT
  100 * SUM(scheduled_flag = 'Y' AND completed_flag = 'Y')
    / NULLIF(SUM(scheduled_flag = 'Y'), 0) AS cycle_count_completion_pct,
  100 * SUM(scheduled_flag = 'Y' AND completed_flag = 'Y'
    AND recount_flag = 'Y')
    / NULLIF(SUM(scheduled_flag = 'Y' AND completed_flag = 'Y'), 0)
    AS recount_rate_pct
FROM cycle_counts;

SELECT 'sku_replenishment_queue_grain' AS check_name,
  CASE WHEN COUNT(*) = COUNT(DISTINCT sku) AND COUNT(*) = 300
    THEN 'PASS' ELSE 'FAIL' END AS status, COUNT(*) AS records
FROM sku_replenishment_queue
UNION ALL
SELECT 'sku_location_count_queue_grain',
  CASE WHEN COUNT(*) = 3600 AND COUNT(DISTINCT sku || '|' || location) = 3600
    THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM sku_location_count_queue
UNION ALL
SELECT 'stockout_report_tier_filter',
  CASE WHEN BOOL_AND(replenishment_tier IN ('Critical', 'High'))
    THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM sku_replenishment_queue
WHERE replenishment_tier IN ('Critical', 'High');

SELECT transaction_type, COUNT(*) AS records
FROM transactions
GROUP BY transaction_type
ORDER BY transaction_type;
