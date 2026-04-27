import requests
import pandas as pd
from pathlib import Path

DATASET = "Elspotprices"
BASE_URL = f"https://api.energidataservice.dk/dataset/{DATASET}"

START_DATE = "2024-01-01"
END_DATE = "2024-02-01"
PRICE_AREAS = ["DK1", "DK2"]

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_elspotprices(price_area: str) -> pd.DataFrame:
    params = {
        "start": START_DATE,
        "end": END_DATE,
        "filter": f'{{"PriceArea":["{price_area}"]}}'
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    records = response.json()["records"]
    df = pd.DataFrame(records)

    df["PriceArea"] = price_area

    return df


def main():
    all_data = []

    for area in PRICE_AREAS:
        print(f"Henter elpriser for {area}...")
        df = fetch_elspotprices(area)
        all_data.append(df)

        output_file = RAW_DIR / f"elspotprices_{area}_{START_DATE}_{END_DATE}.csv"
        df.to_csv(output_file, index=False)
        print(f"Gemt: {output_file} ({len(df)} rækker)")

    combined_df = pd.concat(all_data, ignore_index=True)

    combined_file = RAW_DIR / f"elspotprices_combined_{START_DATE}_{END_DATE}.csv"
    combined_df.to_csv(combined_file, index=False)

    print(f"\nSamlet fil gemt: {combined_file}")
    print(combined_df.head())


if __name__ == "__main__":
    main()