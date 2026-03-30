import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "driver.db")


def get_conn() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def create_tables() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS driver_segments (
                segment_id TEXT PRIMARY KEY,
                driver_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                prediction INTEGER NOT NULL,
                confidence REAL NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS driver_summary (
                driver_id TEXT PRIMARY KEY,
                operational_seconds INTEGER DEFAULT 0,
                non_operational_seconds INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def segment_exists(segment_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM driver_segments WHERE segment_id = ?",
            (segment_id,),
        ).fetchone()
    return row is not None


def insert_segment(segment: dict) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO driver_segments (
                segment_id,
                driver_id,
                start_time,
                end_time,
                duration_seconds,
                prediction,
                confidence,
                source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                segment["segment_id"],
                segment["driver_id"],
                segment["start_time"],
                segment["end_time"],
                int(segment["duration_seconds"]),
                int(segment["prediction"]),
                float(segment["confidence"]),
                segment["source"],
            ),
        )
        conn.commit()
        return cur.rowcount == 1


def update_summary(driver_id: str, duration_seconds: int, prediction: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO driver_summary (driver_id, operational_seconds, non_operational_seconds)
            VALUES (?, 0, 0)
            ON CONFLICT(driver_id) DO NOTHING
            """,
            (driver_id,),
        )

        if int(prediction) == 1:
            conn.execute(
                """
                UPDATE driver_summary
                SET operational_seconds = operational_seconds + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE driver_id = ?
                """,
                (int(duration_seconds), driver_id),
            )
        else:
            conn.execute(
                """
                UPDATE driver_summary
                SET non_operational_seconds = non_operational_seconds + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE driver_id = ?
                """,
                (int(duration_seconds), driver_id),
            )
        conn.commit()


def get_driver_summary(driver_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT operational_seconds, non_operational_seconds
            FROM driver_summary
            WHERE driver_id = ?
            """,
            (driver_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "operational_seconds": int(row["operational_seconds"]),
        "non_operational_seconds": int(row["non_operational_seconds"]),
    }