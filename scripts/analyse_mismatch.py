import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# --------------------------------------------------------- OPSÆTNING -----------------------------------------------------------------
# --- FILER ---
elspot_file = Path("data/raw/elspotprices_combined_2024-01-01_2024-02-01.csv")
prod_file = Path("data/raw/production_consumption_2024-01-01_2024-02-01.csv")

# --- LOAD DATA ---
df_price = pd.read_csv(elspot_file)
df_prod = pd.read_csv(prod_file)

print("Elspot columns:", df_price.columns)
print("Prod columns:", df_prod.columns)

# --- CLEAN / FORBEREDELSE ---
df_price["HourUTC"] = pd.to_datetime(df_price["HourUTC"])
df_prod["HourUTC"] = pd.to_datetime(df_prod["HourUTC"])

# --- MERGE ---
df = pd.merge(
    df_prod,
    df_price,
    on=["HourUTC", "PriceArea"],
    how="inner"
)

# --- SAMLER PRODUCTION ---
df["total_production"] = (
    df["CentralPowerMWh"]
    + df["LocalPowerMWh"]
    + df["CommercialPowerMWh"]
    + df["OffshoreWindLt100MW_MWh"]
    + df["OffshoreWindGe100MW_MWh"]
    + df["OnshoreWindLt50kW_MWh"]
    + df["OnshoreWindGe50kW_MWh"]
    + df["SolarPowerLt10kW_MWh"]
    + df["SolarPowerGe10Lt40kW_MWh"]
    + df["SolarPowerGe40kW_MWh"]
)

# --- HÅNDTERER MISSING VALUES ---
df["consumption"] = df["GrossConsumptionMWh"]
df["total_production"] = df["total_production"].fillna(0)
df["consumption"] = df["consumption"].fillna(0)

# --- SAMLER GRØN ENERGI ---
cols = [
    "OffshoreWindLt100MW_MWh",
    "OffshoreWindGe100MW_MWh",
    "OnshoreWindLt50kW_MWh",
    "OnshoreWindGe50kW_MWh",
    "SolarPowerLt10kW_MWh",
    "SolarPowerGe10Lt40kW_MWh",
    "SolarPowerGe40kW_MWh"
]
df[cols] = df[cols].fillna(0)
df["renewable"] = df[cols].sum(axis=1)


df["renewable_share"] = df["renewable"] / df["total_production"]
df["renewable_share"] = df["renewable_share"].replace([float("inf"), -float("inf")], 0)
df["renewable_share"] = df["renewable_share"].fillna(0)

# --------------------------------------------------------- ANALYSE -----------------------------------------------------------------

# --- BEREGNING AF MISMATCH---
df["mismatch"] = df["total_production"] - df["consumption"]

# --- OUTPUT ---
print("\nFørste rækker:")
print(df[["HourUTC", "PriceArea", "total_production", "consumption", "mismatch"]].head())

# --- SIMPEL INSIGHT ---
print("\nStatistik:")
print(df["mismatch"].describe())

# --- STØRSTE OVERSKUD/UNDERSKUD ---
print("\nStørste overskud:")
print(df.nlargest(5, "mismatch")[["HourUTC", "PriceArea", "mismatch"]])

print("\nStørste underskud:")
print(df.nsmallest(5, "mismatch")[["HourUTC", "PriceArea", "mismatch"]])

# --- MØNSTER OVER DØGNET ---
df["hour"] = df["HourUTC"].dt.hour

print("\nGennemsnit mismatch pr. time:")
print(df.groupby("hour")["mismatch"].mean())

# --- DK1 vs DK2 ---
print("\nMismatch pr. område:")
print(df.groupby("PriceArea")["mismatch"].mean())

# --- KORRELATION MELLEM OVERSKUD/UNDERSKUD OG PRIS ---
print("\nPris vs mismatch correlation:")
print(df[["mismatch", "SpotPriceDKK"]].corr())

# --- KORRELATION MELLEM RENEWABLE SHARE OG PRIS ---
print("\nPris vs. Renewable share:")
print(df[["renewable_share", "SpotPriceDKK"]].corr())

# --------------------------------------------------------- VISUALISERING -----------------------------------------------------------------
# --- Plot: Mismatch over tid ---
plt.figure(figsize=(12, 5))
plt.plot(df["HourUTC"], df["mismatch"])
plt.title("Elbalance (produktion vs forbrug)")
plt.xlabel("Tid")
plt.ylabel("Mismatch (MWh)")
plt.xticks(rotation=45)
plt.axhline(0, linestyle='--')
plt.tight_layout()
plt.show()


# --- Plot: Pris vs Renewable ---
colors = df["PriceArea"].map({"DK1": "blue", "DK2": "red"})
plt.figure(figsize=(6, 6))
plt.scatter(df["renewable_share"], df["SpotPriceDKK"], c=colors, alpha=0.3)
plt.title("Elpris som funktion af andel vedvarende energi")
plt.xlabel("Andel vedvarende energi")
plt.ylabel("Elpris (DKK)")
plt.xlim(0, 1)

blue_patch = mpatches.Patch(color='blue', label='DK1')
red_patch = mpatches.Patch(color='red', label='DK2')
plt.legend(handles=[blue_patch, red_patch])

plt.tight_layout()
plt.show()

# --- Data til Dashboard ---
output_cols = [
    "HourUTC",
    "PriceArea",
    "mismatch",
    "renewable_share",
    "SpotPriceDKK"
]

df_dashboard = df[output_cols].copy()

Path("data/processed").mkdir(parents=True, exist_ok=True)
df_dashboard.to_csv("data/processed/dashboard_energy_data.csv", index=False)

print("Saved dashboard data to data/processed/dashboard_energy_data.csv")