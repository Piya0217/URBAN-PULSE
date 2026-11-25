
from pathlib import Path
import pandas as pd

# Project data directory
DATA_DIR = Path("data/raw")

# Our three downloaded datasets
datasets = [
    "traffic_cases_and_fines.csv",
    "drink_and_drive_cases.csv",
    "motor_vehicle_act_cases.csv"
]

def inspect_dataset(filename):
    file_path = DATA_DIR / filename

    print("\n" + "=" * 65)
    print(f"DATASET: {filename}")
    print("=" * 65)

    # Check whether the file exists
    if not file_path.exists():
        print("File not found!")
        return

    # Read CSV into a Pandas DataFrame
    df = pd.read_csv(file_path)

    # Basic information
    print("\n1. DATASET DIMENSIONS")
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])
    print("File size:", file_path.stat().st_size, "bytes")

    # Column names
    print("\n2. COLUMN NAMES")
    print(df.columns.tolist())

    # Data types
    print("\n3. DATA TYPES")
    print(df.dtypes)

    # First five records
    print("\n4. FIRST FIVE ROWS")
    print(df.to_string(index=False))

    # Missing values
    print("\n5. MISSING VALUES")
    print(df.isnull().sum())

    # Duplicate records
    print("\n6. DUPLICATE ROWS")
    print(df.duplicated().sum())


# Inspect all three datasets
for dataset in datasets:
    inspect_dataset(dataset)
