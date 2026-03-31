-- ============================================================
--  UrbanBlack LongTripOpt — Fare Analysis Queries
--  Table: rides_dataset
-- ============================================================

-- ── 1. All completed rides ────────────────────────────────────
SELECT *
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
ORDER BY request_timestamp DESC
LIMIT 100;

-- ── 2. Average fare & count by trip type ─────────────────────
SELECT
    trip_type,
    COUNT(*)                            AS total_rides,
    ROUND(AVG(actual_distance_km), 2)   AS avg_km,
    ROUND(AVG(offered_fare), 2)         AS avg_offered_fare,
    ROUND(AVG(revenue_per_km), 2)       AS avg_rev_per_km
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY trip_type
ORDER BY avg_offered_fare DESC;

-- ── 3. Fare by hour of day (all-day pattern) ─────────────────
SELECT
    hour_of_day,
    COUNT(*)                            AS rides,
    ROUND(AVG(offered_fare), 2)         AS avg_fare,
    ROUND(MIN(offered_fare), 2)         AS min_fare,
    ROUND(MAX(offered_fare), 2)         AS max_fare
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- ── 4. Fare by fare slab (tiered long-trip rates) ────────────
-- Slab 1: < 15 km @ ₹25/km | Slab 2: 15–18 km @ ₹23/km
-- Slab 3: 18–20 km @ ₹22/km | Slab 4: ≥ 20 km @ ₹20/km
SELECT
    fare_slab_stage_id                  AS slab,
    CASE fare_slab_stage_id
        WHEN 1 THEN '< 15 km  (₹25/km)'
        WHEN 2 THEN '15-18 km (₹23/km)'
        WHEN 3 THEN '18-20 km (₹22/km)'
        WHEN 4 THEN '>= 20 km (₹20/km)'
    END                                 AS slab_label,
    COUNT(*)                            AS rides,
    ROUND(AVG(actual_distance_km), 2)   AS avg_km,
    ROUND(AVG(offered_fare), 2)         AS avg_fare,
    ROUND(AVG(revenue_per_km), 2)       AS avg_rev_per_km
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
  AND fare_slab_stage_id IS NOT NULL
GROUP BY fare_slab_stage_id
ORDER BY fare_slab_stage_id;

-- ── 5. Night vs day rides ─────────────────────────────────────
SELECT
    CASE WHEN hour_of_day >= 22 OR hour_of_day < 6
         THEN 'Night (22:00–05:59)' ELSE 'Day' END  AS time_window,
    COUNT(*)                                         AS rides,
    ROUND(AVG(offered_fare), 2)                      AS avg_fare,
    ROUND(AVG(actual_distance_km), 2)                AS avg_km
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY time_window;

-- ── 6. Peak vs off-peak (8-9, 17-20) ─────────────────────────
SELECT
    CASE WHEN is_peak_hour THEN 'Peak' ELSE 'Off-Peak' END AS period,
    COUNT(*)                            AS rides,
    ROUND(AVG(offered_fare), 2)         AS avg_fare
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY is_peak_hour;

-- ── 7. Economy vs Premium breakdown ──────────────────────────
SELECT
    vehicle_type,
    COUNT(*)                            AS rides,
    ROUND(AVG(offered_fare), 2)         AS avg_fare,
    ROUND(AVG(actual_distance_km), 2)   AS avg_km,
    ROUND(AVG(revenue_per_km), 2)       AS avg_rev_per_km
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY vehicle_type;

-- ── 8. Driver shift compliance (25 rides / 135 km rule) ──────
SELECT
    driver_id,
    COUNT(*)                                AS shift_rides,
    ROUND(SUM(actual_distance_km), 2)       AS shift_km,
    ROUND(SUM(actual_distance_km) / 135, 2) AS quota_pct,
    BOOL_OR(driver_shift_min_reached)       AS met_km_target,
    COUNT(*) >= 25                          AS met_ride_target
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY driver_id
ORDER BY shift_km DESC
LIMIT 20;

-- ── 9. Revenue leakage: rides where final < offered ──────────
SELECT
    trip_id,
    trip_type,
    actual_distance_km,
    offered_fare,
    final_fare,
    ROUND(offered_fare - final_fare, 2)     AS leakage
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
  AND final_fare < offered_fare
ORDER BY leakage DESC
LIMIT 20;

-- ── 10. Cancellation rate by depot zone ───────────────────────
SELECT
    depot_zone,
    COUNT(*)                                                AS total,
    SUM(CASE WHEN ride_status='CANCELLED' THEN 1 END)       AS cancelled,
    ROUND(
        100.0 * SUM(CASE WHEN ride_status='CANCELLED' THEN 1 END) / COUNT(*), 2
    )                                                       AS cancel_rate_pct
FROM rides_dataset
GROUP BY depot_zone
ORDER BY cancel_rate_pct DESC;

-- ── 11. Long-trip acceptance rate ────────────────────────────
-- (fare slab 2, 3, 4 = 15+ km rides)
SELECT
    CASE WHEN fare_slab_stage_id >= 2 THEN 'Long (≥15 km)' ELSE 'Short/Med (<15 km)' END AS trip_length,
    COUNT(*)                                                AS total_offered,
    SUM(rider_acceptance_flag::int)                         AS accepted,
    ROUND(
        100.0 * SUM(rider_acceptance_flag::int) / COUNT(*), 2
    )                                                       AS acceptance_rate_pct
FROM rides_dataset
WHERE fare_slab_stage_id IS NOT NULL
GROUP BY (fare_slab_stage_id >= 2)
ORDER BY trip_length;

-- ── 12. Fare verification: ML vs rule expected ────────────────
-- Run after loading predictions CSV
-- (assumes pred_fare_ml and pred_fare_rule columns exist)
/*
SELECT
    fare_slab_stage_id,
    ROUND(AVG(offered_fare), 2)         AS actual_fare,
    ROUND(AVG(pred_fare_rule), 2)       AS expected_rule_fare,
    ROUND(AVG(pred_fare_ml), 2)         AS ml_pred_fare,
    ROUND(AVG(ABS(offered_fare - pred_fare_rule)), 2) AS rule_mae
FROM rides_dataset
WHERE ride_status = 'RIDE_COMPLETED'
GROUP BY fare_slab_stage_id
ORDER BY fare_slab_stage_id;
*/
