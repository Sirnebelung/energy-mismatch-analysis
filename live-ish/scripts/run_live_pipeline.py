from fetch_live_energy import main as fetch_energy
from fetch_live_weather import main as fetch_weather
from export_live_dashboard_data import export_live_data


def main():
    print("\n=== STEP 1: Fetching energy data ===")
    fetch_energy()

    print("\n=== STEP 2: Fetching weather data ===")
    fetch_weather()

    print("\n=== STEP 3: Exporting dashboard CSV ===")
    export_live_data()

    print("\nLive-ish pipeline completed.")


if __name__ == "__main__":
    main()