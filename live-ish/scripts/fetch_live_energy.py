import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from config import HOURS_BACK

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data/database/energy_live.db"

ENERGY_DATASET = "ProductionConsumptionSettlement"
PRICE_DATASET = "DayAheadPrices"

ENERGY_URL = f"https://api.energidataservice.dk/dataset/{ENERGY_DATASET}"
PRICE_URL = f"https://api.energidataservice.dk/dataset/{PRICE_DATASET}"

PRICE_AREAS = ["DK1", "DK2"]


def get_time_window(hours_back=72):
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=hours_back)

    return start.strftime("%Y-%m-%dT%H:%M"), end.strftime("%Y-%m-%dT%H:%M")


def fetch_json(url, params):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("records", [])


def fetch_production_consumption(start, end):
    params = {
        "start": start,
        "end": end,
    }

    records = fetch_json(ENERGY_URL, params)
    return pd.DataFrame(records)


def fetch_prices(start, end):
    all_prices = []

    for area in PRICE_AREAS:
        params = {
            "start": start,
            "end": end,
            "filter": f'{{"PriceArea":["{area}"]}}',
        }

        records = fetch_json(PRICE_URL, params)
        df = pd.DataFrame(records)

        if not df.empty:
            df["PriceArea"] = area
            all_prices.append(df)

    if not all_prices:
        return pd.DataFrame()

    return pd.concat(all_prices, ignore_index=True)


def prepare_energy_data(df_prod, df_price):
    if df_prod.empty or df_price.empty:
        print("No production or price data returned.")
        return pd.DataFrame()

    df_price = df_price.rename(columns={
        "TimeUTC": "HourUTC",
        "DayAheadPriceDKK": "SpotPriceDKK"
    })

    df_prod["HourUTC"] = pd.to_datetime(df_prod["HourUTC"], utc=True)
    df_price["HourUTC"] = pd.to_datetime(df_price["HourUTC"], utc=True)

    df_price = (
        df_price
        .set_index("HourUTC")
        .groupby("PriceArea")["SpotPriceDKK"]
        .resample("h")
        .mean()
        .reset_index()
    )

    df = pd.merge(
        df_prod,
        df_price,
        on=["HourUTC", "PriceArea"],
        how="inner",
    )

    renewable_cols = [
        "OffshoreWindLt100MW_MWh",
        "OffshoreWindGe100MW_MWh",
        "OnshoreWindLt50kW_MWh",
        "OnshoreWindGe50kW_MWh",
        "SolarPowerLt10kW_MWh",
        "SolarPowerGe10Lt40kW_MWh",
        "SolarPowerGe40kW_MWh",
    ]

    production_cols = [
        "CentralPowerMWh",
        "LocalPowerMWh",
        "CommercialPowerMWh",
        *renewable_cols,
    ]

    for col in production_cols + ["GrossConsumptionMWh"]:
        if col not in df.columns:
            df[col] = 0

    df[production_cols] = df[production_cols].fillna(0)
    df[renewable_cols] = df[renewable_cols].fillna(0)

    df["total_production"] = df[production_cols].sum(axis=1)
    df["consumption"] = df["GrossConsumptionMWh"].fillna(0)
    df["renewable"] = df[renewable_cols].sum(axis=1)
    df["wind_production"] = df[
        [
        "OffshoreWindLt100MW_MWh",
        "OffshoreWindGe100MW_MWh",
        "OnshoreWindLt50kW_MWh",
        "OnshoreWindGe50kW_MWh",
        ]
    ].sum(axis=1)

    df["solar_production"] = df[
        [
        "SolarPowerLt10kW_MWh",
        "SolarPowerGe10Lt40kW_MWh",
        "SolarPowerGe40kW_MWh",
        ]
    ].sum(axis=1)
    df["central_power"] = df["CentralPowerMWh"]
    df["local_power"] = df["LocalPowerMWh"]
    df["commercial_power"] = df["CommercialPowerMWh"]
    df["other_renewable"] = df["renewable"] - df["wind_production"] - df["solar_production"]
    df["renewable_share"] = df["renewable"] / df["total_production"]
    df["renewable_share"] = df["renewable_share"].replace([float("inf"), -float("inf")], 0).fillna(0)
    df["mismatch"] = df["total_production"] - df["consumption"]

    output_cols = [
    "HourUTC",
    "PriceArea",
    "total_production",
    "consumption",
    "renewable",
    "central_power",
    "local_power",
    "commercial_power",
    "wind_production",
    "solar_production",
    "other_renewable",
    "renewable_share",
    "mismatch",
    "SpotPriceDKK",
    ]

    df = df[output_cols].copy()
    df["HourUTC"] = df["HourUTC"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return df


def insert_into_sqlite(df):
    if df.empty:
        print("Nothing to insert.")
        return

    conn = sqlite3.connect(DB_PATH)

    rows = df.to_records(index=False).tolist()

    conn.executemany(
        """
        INSERT OR REPLACE INTO live_energy (
    HourUTC,
    PriceArea,
    total_production,
    consumption,
    renewable,
    central_power,
    local_power,
    commercial_power,
    wind_production,
    solar_production,
    other_renewable,
    renewable_share,
    mismatch,
    SpotPriceDKK
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    conn.commit()
    conn.close()

    print(f"Inserted/updated {len(df)} rows in {DB_PATH}")

def cleanup_old_data(hours_back):
    conn = sqlite3.connect(DB_PATH)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    conn.execute("""
        DELETE FROM live_energy
        WHERE HourUTC < ?
    """, (cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),))

    conn.commit()
    conn.close()

    print(f"Deleted rows older than {cutoff.strftime('%Y-%m-%dT%H:%M:%SZ')}")

def main():
    start, end = get_time_window(hours_back=HOURS_BACK)

    print(f"Fetching Energinet data from {start} to {end}")

    df_prod = fetch_production_consumption(start, end)
    df_price = fetch_prices(start, end)

    print(f"Production rows: {len(df_prod)}")
    print(f"Price rows: {len(df_price)}")

    df = prepare_energy_data(df_prod, df_price)
    insert_into_sqlite(df)
    cleanup_old_data(HOURS_BACK)


if __name__ == "__main__":
    main()