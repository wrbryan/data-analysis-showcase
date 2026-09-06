-- Inventory Accuracy & Stockout Risk (DuckDB reference)
-- Run from the repository root after running generate_synthetic_data.py.
-- Full inputs live in data/generated/ (ignored); data/sample/ is documentation
-- only.  The Python analyzer is the publication path for the CSV reports.

-- ============================================================================
-- 1. SOURCE REGISTRATION
-- ============================================================================
CREATE OR REPLACE TABLE inventory_snapshot AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/generated/inventory_snapshot.csv'
);
CREATE OR REPLACE TABLE product_master AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/generated/product_master.csv'
);
CREATE OR REPLACE TABLE transactions AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/generated/transactions.csv'
);
CREATE OR REPLACE TABLE orders AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/generated/orders.csv'
);
CREATE OR REPLACE TABLE cycle_counts AS
SELECT * FROM read_csv_auto(
  'projects/inventory-accuracy-stockout-risk/data/generated/cycle_counts.csv'
);

-- ============================================================================
-- 2. HISTORICAL ACCURACY, ADJUSTMENTS, AND STOCKOUT-OBSERVATION KPI
-- ============================================================================
WITH inventory_variance AS (
  SELECT
    snapshot_date, sku, location, system_qty, physical_qty, unit_cost,
    system_qty - physical_qty AS quantity_variance,
    ABS(system_qty - physical_qty) AS absolute_variance,
    ABS(system_qty - physical_qty) * unit_cost AS adjustment_value
  FROM inventory_snapshot
),
calendar AS (
  SELECT DATE_DIFF('day', MIN(snapshot_date)::DATE, MAX(snapshot_date)::DATE) + 1
    AS calendar_days
  FROM inventory_snapshot
),
sku_demand AS (
  SELECT sku, SUM(ordered_qty) / MAX(calendar_days) AS daily_demand
  FROM orders CROSS JOIN calendar
  GROUP BY sku
),
location_count AS (
  SELECT sku, COUNT(DISTINCT location) AS locations
  FROM inventory_snapshot GROUP BY sku
),
historical AS (
  SELECT
    i.*,
    p.reorder_point, p.lead_time_days,
    s.daily_demand / l.locations AS average_daily_demand,
    i.physical_qty / NULLIF(s.daily_demand / l.locations, 0)
      AS days_of_supply
  FROM inventory_variance i
  JOIN product_master p USING (sku)
  JOIN sku_demand s USING (sku)
  JOIN location_count l USING (sku)
)
SELECT
  ROUND(100 * (1 - SUM(absolute_variance) /
    NULLIF(SUM(GREATEST(physical_qty, 1)), 0)), 2) AS inventory_accuracy_pct,
  ROUND(SUM(adjustment_value), 2) AS cumulative_adjustment_value,
  ROUND(100 * SUM(
    physical_qty <= reorder_point OR days_of_supply <= lead_time_days
  ) / COUNT(*), 2) AS historical_stockout_observation_rate_pct
FROM historical;

-- ============================================================================
-- 3. CURRENT LATEST-SNAPSHOT ACTION RISK
-- ============================================================================
-- Policy trigger used consistently below and by the historical KPI:
-- physical_qty <= reorder_point OR days_of_supply <= lead_time_days.
-- Recurring variance means at least two non-zero quantity-variance snapshots
-- for the SKU/location pair.
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
sku_demand AS (
  SELECT sku, SUM(ordered_qty) / MAX(calendar_days) AS daily_demand
  FROM orders
  CROSS JOIN (
    SELECT DATE_DIFF('day', MIN(snapshot_date)::DATE, MAX(snapshot_date)::DATE) + 1
      AS calendar_days
    FROM inventory_snapshot
  ) calendar
  GROUP BY sku
),
location_count AS (
  SELECT sku, COUNT(DISTINCT location) AS locations
  FROM inventory_snapshot GROUP BY sku
),
pair_history AS (
  SELECT
    sku, location,
    SUM(ABS(system_qty - physical_qty) * unit_cost) AS cumulative_adjustment_value,
    SUM(ABS(system_qty - physical_qty) > 0) AS variance_event_count
  FROM inventory_snapshot
  GROUP BY sku, location
),
base AS (
  SELECT
    l.sku, p.product_name, p.category, p.supplier, l.location, l.zone,
    l.physical_qty, l.unit_cost,
    l.physical_qty * l.unit_cost AS inventory_value,
    h.cumulative_adjustment_value,
    h.variance_event_count,
    s.daily_demand / c.locations AS average_daily_demand,
    l.physical_qty / NULLIF(s.daily_demand / c.locations, 0)
      AS days_of_supply,
    p.reorder_point, p.safety_stock, p.lead_time_days
  FROM latest l
  JOIN product_master p USING (sku)
  JOIN sku_demand s USING (sku)
  JOIN location_count c USING (sku)
  JOIN pair_history h USING (sku, location)
),
thresholds AS (
  SELECT
    QUANTILE_CONT(inventory_value, 0.75) AS inventory_value_p75,
    QUANTILE_CONT(unit_cost, 0.75) AS unit_cost_p75,
    QUANTILE_CONT(cumulative_adjustment_value, 0.75)
      AS cumulative_adjustment_value_p75
  FROM base
),
classified AS (
  SELECT
    b.*,
    CASE WHEN b.inventory_value >= t.inventory_value_p75
      OR b.unit_cost >= t.unit_cost_p75
      OR b.cumulative_adjustment_value >= t.cumulative_adjustment_value_p75
      THEN 'Y' ELSE 'N' END AS materiality_flag,
    (
      b.physical_qty <= b.reorder_point
      OR b.days_of_supply <= b.lead_time_days
    ) AS current_stockout_risk_condition,
    b.variance_event_count >= 2 AS recurring_variance,
    CASE WHEN
      b.physical_qty = 0
      OR b.days_of_supply <= 0.25 * b.lead_time_days
      OR (
        b.physical_qty <= b.safety_stock
        AND (
          b.inventory_value >= t.inventory_value_p75
          OR b.unit_cost >= t.unit_cost_p75
          OR b.cumulative_adjustment_value >= t.cumulative_adjustment_value_p75
        )
        AND (
          b.physical_qty <= b.reorder_point
          OR b.days_of_supply <= b.lead_time_days
        )
      )
      THEN 'Critical'
      WHEN b.physical_qty <= b.reorder_point
        AND b.days_of_supply <= b.lead_time_days
        AND (
          b.inventory_value >= t.inventory_value_p75
          OR b.unit_cost >= t.unit_cost_p75
          OR b.cumulative_adjustment_value >= t.cumulative_adjustment_value_p75
        )
        THEN 'High'
      WHEN b.physical_qty <= b.reorder_point
        OR b.days_of_supply <= b.lead_time_days
        OR (
          (
            b.inventory_value >= t.inventory_value_p75
            OR b.unit_cost >= t.unit_cost_p75
            OR b.cumulative_adjustment_value >= t.cumulative_adjustment_value_p75
          )
          AND b.variance_event_count >= 2
        )
        THEN 'Watch'
      ELSE 'Routine'
    END AS risk_tier
  FROM base b CROSS JOIN thresholds t
),
tiered AS (
  SELECT
    c.*,
    CASE
      WHEN c.risk_tier = 'Critical' THEN
        'Critical: physical quantity = 0, days of supply <= 0.25 lead time, or physical quantity <= safety stock with materiality and current stockout-risk condition'
      WHEN c.risk_tier = 'High' THEN
        'High: physical quantity <= reorder point and days of supply <= lead time; materiality flag=Y'
      WHEN c.risk_tier = 'Watch' THEN
        'Watch: physical quantity <= reorder point, days of supply <= lead time, or materiality flag=Y with recurring variance (at least two non-zero variance snapshots)'
      ELSE 'Routine: neither current quantity trigger is met'
    END AS risk_reason
  FROM classified c
)
SELECT
  *, CASE WHEN risk_tier IN ('Critical', 'High') THEN 'Y' ELSE 'N' END
    AS current_action_flag
FROM tiered
ORDER BY CASE risk_tier
  WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Watch' THEN 3 ELSE 4 END,
  days_of_supply NULLS FIRST;

-- The materiality threshold is data-derived, not a fixed business number:
-- QUANTILE_CONT(0.75) (the exact linear-interpolated 75th percentile) is
-- computed independently across latest inventory value, unit cost, and
-- cumulative adjustment value.  A row is material when any metric is >= its
-- corresponding threshold.

-- ============================================================================
-- 4. OPERATING KPIs
-- ============================================================================
SELECT
  100 * SUM(scheduled_flag = 'Y' AND completed_flag = 'Y')
    / NULLIF(SUM(scheduled_flag = 'Y'), 0) AS cycle_count_completion_pct,
  100 * SUM(scheduled_flag = 'Y' AND completed_flag = 'Y'
    AND recount_flag = 'Y')
    / NULLIF(SUM(scheduled_flag = 'Y' AND completed_flag = 'Y'), 0)
    AS recount_rate_pct
FROM cycle_counts;

SELECT
  100 * SUM(shipped_qty > 0 AND ship_date <= promised_date)
    / NULLIF(SUM(shipped_qty > 0), 0) AS on_time_shipment_rate_pct
FROM orders;

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
