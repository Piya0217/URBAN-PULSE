
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw/road_crashes")

for file_path in sorted(DATA_DIR.glob("*.csv")):

    print("\n" + "=" * 75)
    print("DATASET:", file_path.name)
    print("=" * 75)

    df = pd.read_csv(file_path)

    print("\n1. DIMENSIONS")
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])

    print("\n2. COLUMN NAMES")
    print(df.columns.tolist())

    print("\n3. DATA TYPES")
    print(df.dtypes)

    print("\n4. COMPLETE DATA")
    print(df.to_string(index=False))

    print("\n5. MISSING VALUES")
    print(df.isnull().sum())

    print("\n6. DUPLICATE ROWS")
    print(df.duplicated().sum())
