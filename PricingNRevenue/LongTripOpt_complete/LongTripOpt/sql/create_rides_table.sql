-- ============================================================
--  UrbanBlack Rides Dataset — PostgreSQL Schema
--  Drop & recreate for a clean state
-- ============================================================

-- Fare slab enum (mirrors fare_calculator.py rate bands)
-- Slab 1: < 15 km  → ₹25/km
-- Slab 2: 15–<18   → ₹23/km
-- Slab 3: 18–<20   → ₹22/km
-- Slab 4: ≥ 20 km  → ₹20/km

CREATE TABLE IF NOT EXISTS rides_dataset (

    -- ── Primary key ──────────────────────────────────────────
    trip_id                     UUID            PRIMARY KEY,

    -- ── Timestamps ───────────────────────────────────────────
    request_timestamp           TIMESTAMP       NOT NULL,
    started_at                  TIMESTAMP,          -- NULL for CANCELLED
    completed_at                TIMESTAMP,          -- NULL for CANCELLED

    -- ── Derived time features ─────────────────────────────────
    hour_of_day                 SMALLINT        NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week                 SMALLINT        NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    is_weekend                  BOOLEAN         NOT NULL DEFAULT FALSE,
    is_peak_hour                BOOLEAN         NOT NULL DEFAULT FALSE,

    -- ── Geo ───────────────────────────────────────────────────
    pickup_lat                  DOUBLE PRECISION NOT NULL,
    pickup_lng                  DOUBLE PRECISION NOT NULL,
    dropoff_lat                 DOUBLE PRECISION NOT NULL,
    dropoff_lng                 DOUBLE PRECISION NOT NULL,

    -- ── Distance & duration ───────────────────────────────────
    approach_km                 NUMERIC(8,2),
    actual_distance_km          NUMERIC(8,2)    NOT NULL,
    estimated_distance_km       NUMERIC(8,2),
    actual_duration_min         SMALLINT        NOT NULL,
    estimated_duration_min      SMALLINT,

    -- ── Ride classification ───────────────────────────────────
    vehicle_type                VARCHAR(20)     NOT NULL
                                    CHECK (vehicle_type IN ('economy','premium')),
    trip_type                   VARCHAR(30)     NOT NULL
                                    CHECK (trip_type IN (
                                        'standard','standard_long',
                                        'outskirts','airport','intercity'
                                    )),

    -- ── Fares ─────────────────────────────────────────────────
    -- fare_slab_stage_id: 1=<15km, 2=15-18km, 3=18-20km, 4=>=20km
    offered_fare                NUMERIC(10,2)   NOT NULL,
    final_fare                  NUMERIC(10,2),
    fare_slab_stage_id          SMALLINT        CHECK (fare_slab_stage_id BETWEEN 1 AND 4),

    -- ── Driver ────────────────────────────────────────────────
    driver_id                   UUID            NOT NULL,
    driver_rating               NUMERIC(3,2)    CHECK (driver_rating BETWEEN 1 AND 5),
    driver_total_trips          INT             DEFAULT 0,
    driver_shift_hours_elapsed  NUMERIC(6,2),
    driver_online_minutes       INT,
    driver_fuel_level_start     VARCHAR(20)
                                    CHECK (driver_fuel_level_start IN
                                    ('FULL','THREE_QUARTER','HALF','QUARTER','LOW')),
    driver_vehicle_condition    VARCHAR(20)
                                    CHECK (driver_vehicle_condition IN
                                    ('EXCELLENT','GOOD','FAIR','NEEDS_ATTENTION')),
    driver_daily_ride_km        NUMERIC(8,2),
    driver_daily_dead_km        NUMERIC(8,2),
    driver_quota_km             NUMERIC(8,2)    DEFAULT 135,
    driver_overuse_km           NUMERIC(8,2)    DEFAULT 0,
    driver_goal_km              SMALLINT        DEFAULT 135,
    driver_goal_km_reached      NUMERIC(8,2),
    depot_zone                  VARCHAR(50),

    -- ── Shift KPIs (added for training) ──────────────────────
    -- Minimum shift constraints: 25 rides, 12 h, 135 km
    driver_shift_rides          SMALLINT        DEFAULT 0,
    driver_shift_min_reached    BOOLEAN         DEFAULT FALSE,

    -- ── WTA / acceptance ─────────────────────────────────────
    rider_acceptance_flag       BOOLEAN,
    first_driver_accepted       BOOLEAN,
    drivers_offered_count       SMALLINT,

    -- ── Outcome ───────────────────────────────────────────────
    ride_status                 VARCHAR(20)     NOT NULL
                                    CHECK (ride_status IN ('RIDE_COMPLETED','CANCELLED')),
    revenue_per_km              NUMERIC(8,2)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_rides_driver_id        ON rides_dataset (driver_id);
CREATE INDEX IF NOT EXISTS idx_rides_request_ts       ON rides_dataset (request_timestamp);
CREATE INDEX IF NOT EXISTS idx_rides_status           ON rides_dataset (ride_status);
CREATE INDEX IF NOT EXISTS idx_rides_vehicle_type     ON rides_dataset (vehicle_type);
CREATE INDEX IF NOT EXISTS idx_rides_trip_type        ON rides_dataset (trip_type);
CREATE INDEX IF NOT EXISTS idx_rides_hour             ON rides_dataset (hour_of_day);
CREATE INDEX IF NOT EXISTS idx_rides_depot_zone       ON rides_dataset (depot_zone);
CREATE INDEX IF NOT EXISTS idx_rides_fare_slab        ON rides_dataset (fare_slab_stage_id);
CREATE INDEX IF NOT EXISTS idx_rides_first_accepted   ON rides_dataset (first_driver_accepted);
CREATE INDEX IF NOT EXISTS idx_rides_dist             ON rides_dataset (actual_distance_km);
