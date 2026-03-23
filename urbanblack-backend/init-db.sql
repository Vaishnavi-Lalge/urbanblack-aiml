-- UrbanBlack – Database Initialization
-- Runs automatically ONCE on fresh postgres container (empty volume).

CREATE DATABASE urbanblack_auth;
CREATE DATABASE urbanblack_user;
CREATE DATABASE urbanblack_driver;
CREATE DATABASE urbanblack_ride;
CREATE DATABASE employee_details_db;
CREATE DATABASE traffic_operation_db;
CREATE DATABASE cab_registration_db;
CREATE DATABASE urbanblack_fleet;
CREATE DATABASE notification_db;
CREATE DATABASE quickkyc_db;
CREATE DATABASE urbanblack_wallet;
CREATE DATABASE urbanblack_payment;

-- Privileges are automatically granted to the creator (postgres user)

-- ============================================================
-- traffic_operation_db – Table Definitions
-- (Hibernate DDL auto=update will keep these in sync,
--  but this file serves as the canonical schema reference.)
-- ============================================================

CREATE TABLE IF NOT EXISTS assign_manager (
    assign_manager_to_depot_id BIGSERIAL    PRIMARY KEY,
    registration_date          DATE         NOT NULL DEFAULT CURRENT_DATE,
    manager_id                 BIGINT       NOT NULL,
    depot_id                   BIGINT       NOT NULL
);

CREATE TABLE IF NOT EXISTS allocate_vehicles (
    vehicle_to_depot_id BIGSERIAL    PRIMARY KEY,
    depot_id            BIGINT       NOT NULL,
    registration_date   DATE         NOT NULL DEFAULT CURRENT_DATE,
    vehicles_count      INT          NOT NULL DEFAULT 0,
    vehicle_ids         TEXT
);

CREATE TABLE IF NOT EXISTS assign_driver (
    assign_drivers_to_depot_id BIGSERIAL    PRIMARY KEY,
    depot_id                   BIGINT       NOT NULL,
    registration_date          DATE         NOT NULL DEFAULT CURRENT_DATE,
    drivers_count              INT          NOT NULL DEFAULT 0,
    employee_ids               TEXT
);
