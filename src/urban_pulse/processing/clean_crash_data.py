
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw/road_crashes")
OUTPUT_DIR = Path("data/processed")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Define the source column names for each year.
datasets = {
    2023: {
        "file": "crashes_2023.csv",
        "fatal": "2023 - Fatal Cases",
        "non_fatal": "2023 - Non-Fatal",
        "total": "2023 - Total Cases",
        "killed": "2023 - Killed People",
        "injured": "2023 - Injured People"
    },
    2024: {
        "file": "crashes_2024.csv",
        "fatal": "2024-Fatal crashes",
        "non_fatal": "2024-Non Fatal",
        "total": "2024-Total crashes"
    },
    2025: {
        "file": "crashes_2025.csv",
        "fatal": "2025-Fatal crashes",
        "non_fatal": "2025-Non Fatal",
        "total": "2025-Total crashes"
    }
}

cleaned_datasets = []

for year, config in datasets.items():

    print(f"\nProcessing {year}...")

    df = pd.read_csv(RAW_DIR / config["file"])

    # Remove summary rows, keeping individual police stations.
    is_summary = df["Station"].astype("string").str.contains(
        r"\btotal\b", case=False, na=False
    )

    df = df.loc[~is_summary].copy()

    # Create a consistent column structure.
    cleaned = pd.DataFrame({
        "zone": df["Zone"].str.strip(),
        "subdivision": df["Sub-division"].str.strip(),
        "station": df["Station"].str.strip(),
        "year": year,
        "fatal_crashes": df[config["fatal"]],
        "non_fatal_crashes": df[config["non_fatal"]],
        "total_crashes": df[config["total"]]
    })

    # Preserve people-level data where available.
    if year == 2023:
        cleaned["killed_people"] = df[config["killed"]]
        cleaned["injured_people"] = df[config["injured"]]
    else:
        cleaned["killed_people"] = pd.NA
        cleaned["injured_people"] = pd.NA

    cleaned_datasets.append(cleaned)

    print("Station records:", len(cleaned))

# Combine all three years.
final_df = pd.concat(cleaned_datasets, ignore_index=True)

# Save the combined dataset.
output_file = OUTPUT_DIR / "crash_records_2023_2025.csv"
final_df.to_csv(output_file, index=False)

print("\n" + "=" * 60)
print("DATA TRANSFORMATION COMPLETED")
print("=" * 60)

print("Total records:", len(final_df))
print("Years:", sorted(final_df["year"].unique()))
print("Output:", output_file)

print("\nFinal columns:")
print(final_df.columns.tolist())

print("\nSample records:")
print(final_df.head(10).to_string(index=False))
