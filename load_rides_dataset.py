"""
load_rides_dataset.py
---------------------
Load the cleaned rides CSV into PostgreSQL.

Usage:
    python load_rides_dataset.py \
        --csv rides_dataset_clean.csv \
        --host localhost --port 5432 \
        --dbname urbanblack_ride \
        --user postgres --password root \
        --create-table

Options:
    --csv           Path to the cleaned CSV file (required)
    --host          PostgreSQL host            (default: localhost)
    --port          PostgreSQL port            (default: 5432)
    --dbname        Database name              (default: urbanblack_ride)
    --user          Username                   (default: postgres)
    --password      Password                   (default: root)
    --table         Target table name          (default: rides_dataset)
    --create-table  Create / reset the table before loading
    --use-copy      Use fast COPY path instead of batch INSERT
"""

import argparse
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS {table} (
    trip_id                     UUID            PRIMARY KEY,
    request_timestamp           TIMESTAMP       NOT NULL,
    started_at                  TIMESTAMP,
    completed_at                TIMESTAMP,
    hour_of_day                 SMALLINT        NOT NULL,
    day_of_week                 SMALLINT        NOT NULL,
    is_weekend                  BOOLEAN         NOT NULL,
    is_peak_hour                BOOLEAN         NOT NULL,
    pickup_lat                  DOUBLE PRECISION NOT NULL,
    pickup_lng                  DOUBLE PRECISION NOT NULL,
    dropoff_lat                 DOUBLE PRECISION NOT NULL,
    dropoff_lng                 DOUBLE PRECISION NOT NULL,
    approach_km                 NUMERIC(8,2),
    actual_distance_km          NUMERIC(8,2)    NOT NULL,
    estimated_distance_km       NUMERIC(8,2),
    actual_duration_min         SMALLINT        NOT NULL,
    estimated_duration_min      SMALLINT,
    vehicle_type                VARCHAR(20)     NOT NULL,
    trip_type                   VARCHAR(30)     NOT NULL,
    offered_fare                NUMERIC(10,2)   NOT NULL,
    final_fare                  NUMERIC(10,2),
    fare_slab_stage_id          SMALLINT,
    driver_id                   UUID            NOT NULL,
    driver_rating               NUMERIC(3,2),
    driver_total_trips          INT,
    driver_shift_hours_elapsed  NUMERIC(6,2),
    driver_online_minutes       INT,
    driver_fuel_level_start     VARCHAR(20),
    driver_vehicle_condition    VARCHAR(20),
    driver_daily_ride_km        NUMERIC(8,2),
    driver_daily_dead_km        NUMERIC(8,2),
    driver_quota_km             NUMERIC(8,2),
    driver_overuse_km           NUMERIC(8,2),
    driver_goal_km              SMALLINT,
    driver_goal_km_reached      NUMERIC(8,2),
    depot_zone                  VARCHAR(50),
    rider_acceptance_flag       BOOLEAN,
    first_driver_accepted       BOOLEAN,
    drivers_offered_count       SMALLINT,
    ride_status                 VARCHAR(20)     NOT NULL,
    revenue_per_km              NUMERIC(8,2)
);
"""

COLUMNS = [
    'trip_id', 'request_timestamp', 'started_at', 'completed_at',
    'hour_of_day', 'day_of_week', 'is_weekend', 'is_peak_hour',
    'pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng',
    'approach_km', 'actual_distance_km', 'estimated_distance_km',
    'actual_duration_min', 'estimated_duration_min',
    'vehicle_type', 'trip_type', 'offered_fare', 'final_fare',
    'fare_slab_stage_id', 'driver_id', 'driver_rating', 'driver_total_trips',
    'driver_shift_hours_elapsed', 'driver_online_minutes',
    'driver_fuel_level_start', 'driver_vehicle_condition',
    'driver_daily_ride_km', 'driver_daily_dead_km',
    'driver_quota_km', 'driver_overuse_km',
    'driver_goal_km', 'driver_goal_km_reached',
    'depot_zone', 'rider_acceptance_flag', 'first_driver_accepted',
    'drivers_offered_count', 'ride_status', 'revenue_per_km',
]

BOOL_COLS = {'is_weekend', 'is_peak_hour', 'rider_acceptance_flag', 'first_driver_accepted'}
NULL_COLS  = {'started_at', 'completed_at'}  # nullable timestamps


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--csv',          required=True)
    p.add_argument('--host',         default='localhost')
    p.add_argument('--port',         type=int, default=5432)
    p.add_argument('--dbname',       default='urbanblack_ride')
    p.add_argument('--user',         default='postgres')
    p.add_argument('--password',     default='root')
    p.add_argument('--table',        default='rides_dataset')
    p.add_argument('--create-table', action='store_true')
    p.add_argument('--use-copy',     action='store_true')
    return p.parse_args()


def load_df(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str)  # read all as str first

    # Validate required columns
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}")

    # Coerce booleans (CSV stores True/False)
    for col in BOOL_COLS:
        df[col] = df[col].map({'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

    # Replace empty strings with None for nullable columns
    for col in df.columns:
        df[col] = df[col].where(df[col].notna() & (df[col] != '') & (df[col] != 'None'), other=None)

    return df


def ensure_table(conn, table_name: str, create: bool):
    with conn.cursor() as cur:
        if create:
            cur.execute(CREATE_TABLE_SQL.format(table=table_name))
            conn.commit()
            print(f"  Table '{table_name}' created / verified.")
        else:
            cur.execute("SELECT to_regclass(%s)", [table_name])
            if not cur.fetchone()[0]:
                raise RuntimeError(
                    f"Table '{table_name}' not found. Re-run with --create-table."
                )


def row_tuple(row):
    return tuple(
        None if pd.isna(v) else v
        for v in [row[c] for c in COLUMNS]
    )


def load_batch(conn, table_name: str, df: pd.DataFrame):
    placeholders = ', '.join(['%s'] * len(COLUMNS))
    col_list     = ', '.join(COLUMNS)
    query = sql.SQL(
        f"INSERT INTO {{table}} ({col_list}) VALUES ({placeholders}) ON CONFLICT (trip_id) DO NOTHING"
    ).format(table=sql.Identifier(table_name))

    values = [row_tuple(row) for _, row in df.iterrows()]
    with conn.cursor() as cur:
        execute_batch(cur, query, values, page_size=500)
    conn.commit()


def load_copy(conn, table_name: str, csv_path: Path):
    col_list = ', '.join(COLUMNS)
    copy_sql = sql.SQL(
        f"COPY {{table}} ({col_list}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"
    ).format(table=sql.Identifier(table_name))
    with conn.cursor() as cur:
        with open(csv_path, 'r', encoding='utf-8') as f:
            cur.copy_expert(copy_sql, f)
    conn.commit()


def main():
    args   = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    print(f"Connecting to {args.host}:{args.port}/{args.dbname} …")
    conn = psycopg2.connect(
        host=args.host, port=args.port, dbname=args.dbname,
        user=args.user, password=args.password
    )

    try:
        ensure_table(conn, args.table, args.create_table)

        if args.use_copy:
            print("Loading via COPY …")
            load_copy(conn, args.table, csv_path)
        else:
            print("Loading via batch INSERT …")
            df = load_df(csv_path)
            load_batch(conn, args.table, df)

        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {t}").format(t=sql.Identifier(args.table))
            )
            n = cur.fetchone()[0]
        print(f"Done. Total rows in '{args.table}': {n}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
