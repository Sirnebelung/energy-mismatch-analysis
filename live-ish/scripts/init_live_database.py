import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data/database/energy_live.db"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_energy (
            HourUTC TEXT NOT NULL,
            PriceArea TEXT NOT NULL,
            total_production REAL,
            consumption REAL,
            renewable REAL,
            central_power REAL,
            local_power REAL,
            commercial_power REAL,
            wind_production REAL,
            solar_production REAL,
            other_renewable REAL,
            renewable_share REAL,
            mismatch REAL,
            SpotPriceDKK REAL,
            wind_speed REAL,
            temperature REAL,
            sunshine REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (HourUTC, PriceArea)
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database initialized: {DB_PATH}")

if __name__ == "__main__":
    init_db()