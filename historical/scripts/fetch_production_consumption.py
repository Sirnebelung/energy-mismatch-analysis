import requests
import pandas as pd
from pathlib import Path

DATASET = "ProductionConsumptionSettlement"
BASE_URL = f"https://api.energidataservice.dk/dataset/{DATASET}"

START_DATE = "2024-01-01"
END_DATE = "2024-02-01"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data/raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_data():
    params = {
        "start": START_DATE,
        "end": END_DATE
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    records = response.json()["records"]
    df = pd.DataFrame(records)

    return df


def main():
    print("Henter produktion og forbrug...")

    df = fetch_data()

    output_file = RAW_DIR / f"production_consumption_{START_DATE}_{END_DATE}.csv"
    df.to_csv(output_file, index=False)

    print(f"Gemt: {output_file}")
    print(df.head())


if __name__ == "__main__":
    main()