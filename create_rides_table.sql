-- ============================================================
--  UrbanBlack Rides Dataset — PostgreSQL Schema (Full)
--  Drop & recreate to ensure clean state
-- ============================================================

CREATE TABLE IF NOT EXISTS rides_dataset (
    -- Primary key
    trip_id                     UUID            PRIMARY KEY,

    -- Timestamps
    request_timestamp           TIMESTAMP       NOT NULL,
    started_at                  TIMESTAMP,          -- NULL for CANCELLED rides
    completed_at                TIMESTAMP,          -- NULL for CANCELLED rides

    -- Derived time features
    hour_of_day                 SMALLINT        NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week                 SMALLINT        NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    is_weekend                  BOOLEAN         NOT NULL,
    is_peak_hour                BOOLEAN         NOT NULL,

    -- Geo
    pickup_lat                  DOUBLE PRECISION NOT NULL,
    pickup_lng                  DOUBLE PRECISION NOT NULL,
    dropoff_lat                 DOUBLE PRECISION NOT NULL,
    dropoff_lng                 DOUBLE PRECISION NOT NULL,

    -- Distance & duration
    approach_km                 NUMERIC(8,2)    NOT NULL,
    actual_distance_km          NUMERIC(8,2)    NOT NULL,
    estimated_distance_km       NUMERIC(8,2),
    actual_duration_min         SMALLINT        NOT NULL,
    estimated_duration_min      SMALLINT,

    -- Ride classification
    vehicle_type                VARCHAR(20)     NOT NULL CHECK (vehicle_type IN ('economy','premium')),
    trip_type                   VARCHAR(30)     NOT NULL,

    -- Fares
    offered_fare                NUMERIC(10,2)   NOT NULL,
    final_fare                  NUMERIC(10,2),
    fare_slab_stage_id          SMALLINT,

    -- Driver
    driver_id                   UUID            NOT NULL,
    driver_rating               NUMERIC(3,2),
    driver_total_trips          INT,
    driver_shift_hours_elapsed  NUMERIC(6,2),
    driver_online_minutes       INT,
    driver_fuel_level_start     VARCHAR(20)     CHECK (driver_fuel_level_start IN
                                    ('FULL','THREE_QUARTER','HALF','QUARTER','LOW')),
    driver_vehicle_condition    VARCHAR(20)     CHECK (driver_vehicle_condition IN
                                    ('EXCELLENT','GOOD','FAIR','NEEDS_ATTENTION')),
    driver_daily_ride_km        NUMERIC(8,2),
    driver_daily_dead_km        NUMERIC(8,2),
    driver_quota_km             NUMERIC(8,2),
    driver_overuse_km           NUMERIC(8,2)    DEFAULT 0,
    driver_goal_km              SMALLINT        DEFAULT 135,
    driver_goal_km_reached      NUMERIC(8,2),
    depot_zone                  VARCHAR(50),

    -- WTA / acceptance flags
    rider_acceptance_flag       BOOLEAN,
    first_driver_accepted       BOOLEAN,        -- ← WTA target variable
    drivers_offered_count       SMALLINT,

    -- Outcome
    ride_status                 VARCHAR(20)     NOT NULL CHECK (ride_status IN ('RIDE_COMPLETED','CANCELLED')),
    revenue_per_km              NUMERIC(8,2)
);

-- Indexes for typical ML / analytics query patterns
CREATE INDEX IF NOT EXISTS idx_rides_driver_id      ON rides_dataset (driver_id);
CREATE INDEX IF NOT EXISTS idx_rides_request_ts     ON rides_dataset (request_timestamp);
CREATE INDEX IF NOT EXISTS idx_rides_status         ON rides_dataset (ride_status);
CREATE INDEX IF NOT EXISTS idx_rides_vehicle_type   ON rides_dataset (vehicle_type);
CREATE INDEX IF NOT EXISTS idx_rides_trip_type      ON rides_dataset (trip_type);
CREATE INDEX IF NOT EXISTS idx_rides_hour           ON rides_dataset (hour_of_day);
CREATE INDEX IF NOT EXISTS idx_rides_depot_zone     ON rides_dataset (depot_zone);
CREATE INDEX IF NOT EXISTS idx_rides_first_accepted ON rides_dataset (first_driver_accepted);
