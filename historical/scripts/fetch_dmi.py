import requests
import pandas as pd
from pathlib import Path

URL = "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items"

START_DATE = "2024-01-01T00:00:00Z"
END_DATE = "2024-02-01T00:00:00Z"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data/raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

PARAMETERS = [
    "wind_speed_past1h",
    "temp_dry",
    "sun_last1h_glob"
]


def fetch_dmi_parameter(parameter_id):
    print(f"Henter DMI data: {parameter_id}")

    params = {
        "datetime": f"{START_DATE}/{END_DATE}",
        "parameterId": parameter_id,
        "bbox": "7,54,16,58",
        "limit": 300000
    }

    response = requests.get(URL, params=params)

    if response.status_code != 200:
        print("Fejl fra DMI API:")
        print("Status code:", response.status_code)
        print("URL:", response.url)
        print("Response:", response.text)
        response.raise_for_status()

    data = response.json()["features"]

    rows = []

    for item in data:
        props = item["properties"]

        rows.append({
            "HourUTC": props.get("observed"),
            "stationId": props.get("stationId"),
            "parameter": props.get("parameterId"),
            "value": props.get("value")
        })

    return pd.DataFrame(rows)


def main():
    all_data = []

    for parameter in PARAMETERS:
        df_param = fetch_dmi_parameter(parameter)
        print(f"{parameter}: {len(df_param)} rækker")
        all_data.append(df_param)

    df = pd.concat(all_data, ignore_index=True)

    print("\nSamlet rå DMI data:")
    print(df.head())
    print(df["parameter"].value_counts())

    df["HourUTC"] = pd.to_datetime(df["HourUTC"], utc=True)

    # Gennemsnit pr. time på tværs af stationer
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

    df_pivot.rename(columns={
        "wind_speed_past1h": "wind_speed",
        "temp_dry": "temperature",
        "sun_last1h_glob": "sunshine"
    }, inplace=True)

    output_file = RAW_DIR / "dmi_weather.csv"
    df_pivot.to_csv(output_file, index=False)

    print(f"\nGemt: {output_file}")
    print(df_pivot.head())


if __name__ == "__main__":
    main()