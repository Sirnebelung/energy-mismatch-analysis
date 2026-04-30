import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from config import HOURS_BACK

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data/database/energy_live.db"

DMI_URL = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"

PARAMETERS = [
    "wind_speed_past1h",
    "temp_dry",
    "sun_last1h_glob"
]


def get_time_window(hours_back=HOURS_BACK):
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=hours_back)

    return start.isoformat(), end.isoformat()


def fetch_dmi():
    start, end = get_time_window()

    all_rows = []

    for param in PARAMETERS:
        params = {
            "datetime": f"{start}/{end}",
            "parameterId": param,
            "bbox": "7,54,16,58",
            "limit": 300000
        }

        response = requests.get(DMI_URL, params=params)
        response.raise_for_status()

        data = response.json()["features"]

        for item in data:
            props = item["properties"]

            all_rows.append({
                "HourUTC": props.get("observed"),
                "parameter": props.get("parameterId"),
                "value": props.get("value")
            })

    df = pd.DataFrame(all_rows)

    df["HourUTC"] = pd.to_datetime(df["HourUTC"], utc=True)

    df_hourly = (
        df
        .set_index("HourUTC")
        .groupby("parameter")["value"]
        .resample("h")
        .mean()
        .reset_index()
    )

    df_pivot = (
        df_hourly
        .pivot_table(
            index="HourUTC",
            columns="parameter",
            values="value",
            aggfunc="mean"
        )
        .reset_index()
    )

    df_pivot = df_pivot.rename(columns={
        "wind_speed_past1h": "wind_speed",
        "temp_dry": "temperature",
        "sun_last1h_glob": "sunshine"
    })

    df_pivot["HourUTC"] = df_pivot["HourUTC"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return df_pivot


def update_sqlite(df):
    conn = sqlite3.connect(DB_PATH)

    for _, row in df.iterrows():
        conn.execute("""
            UPDATE live_energy
            SET wind_speed = ?, temperature = ?, sunshine = ?
            WHERE HourUTC = ?
        """, (
            row.get("wind_speed"),
            row.get("temperature"),
            row.get("sunshine"),
            row["HourUTC"]
        ))

    conn.commit()
    conn.close()

    print(f"Updated weather for {len(df)} timestamps")


def main():
    df = fetch_dmi()
    print(df.head())
    update_sqlite(df)


if __name__ == "__main__":
    main()