from pathlib import Path
import pandas as pd

output_dir = Path("data/processed/analytics/crashes")

files = [
    "yearly_crash_statistics.parquet",
    "zone_crash_statistics.parquet",
    "station_year_statistics.parquet",
    "historical_hotspots.parquet",
    "station_crash_trends.parquet"
]

print("\nVERIFYING SAVED ANALYTICS DATASETS")

for file in files:
    file_path = output_dir / file

    df = pd.read_parquet(file_path)

    print(f"\nDataset: {file}")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Status: SUCCESS")

print("\nALL DATASETS VERIFIED SUCCESSFULLY!")