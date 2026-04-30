import sqlite3
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data/database/energy_live.db"
EXPORT_PATH = BASE_DIR / "data/exports/live_dashboard_data.csv"

EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def export_live_data():
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            HourUTC,
            PriceArea,
            total_production,
            consumption,
            renewable,
            wind_production,
            solar_production,
            other_renewable,
            renewable_share,
            mismatch,
            SpotPriceDKK,
            wind_speed,
            temperature,
            sunshine,
            central_power,
            local_power,
            commercial_power
        FROM live_energy
        ORDER BY HourUTC, PriceArea
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df.to_csv(EXPORT_PATH, index=False)

    print(f"Exported {len(df)} rows to {EXPORT_PATH}")


if __name__ == "__main__":
    export_live_data()