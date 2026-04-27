import requests
import pandas as pd
from pathlib import Path

DATASET = "Elspotprices"
URL = f"https://api.energidataservice.dk/dataset/{DATASET}"

params = {
    "start": "2024-01-01",
    "end": "2024-01-03",
    "filter": '{"PriceArea":["DK1"]}'
}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()["records"]

df = pd.DataFrame(data)

Path("data").mkdir(exist_ok=True)
df.to_csv("data/elspotprices_test.csv", index=False)

print(df.head())
print(f"Saved {len(df)} rows to data/elspotprices_test.csv")