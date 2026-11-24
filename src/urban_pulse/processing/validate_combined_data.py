
from pathlib import Path
import pandas as pd

file_path = Path("data/processed/crash_records_2023_2025.csv")

df = pd.read_csv(file_path)

print("=" * 55)
print("COMBINED CRASH DATA VALIDATION")
print("=" * 55)

# 1. Dataset dimensions
print("\n1. DATASET SIZE")
print("Rows:", len(df))
print("Columns:", len(df.columns))

# 2. Records per year
print("\n2. RECORDS PER YEAR")
print(df["year"].value_counts().sort_index())

# 3. Missing values
print("\n3. MISSING VALUES")
print(df.isnull().sum())

# 4. Duplicate station-year records
print("\n4. DUPLICATE STATION-YEAR RECORDS")
duplicates = df[df.duplicated(
    subset=["station", "year"], keep=False
)]

print("Duplicate records:", len(duplicates))

# 5. Crash arithmetic
print("\n5. CRASH TOTAL VALIDATION")

mismatch = df[
    df["fatal_crashes"] + df["non_fatal_crashes"]
    != df["total_crashes"]
]

if mismatch.empty:
    print("PASS: All crash totals are correct.")
else:
    print("WARNING: Mismatches found.")
    print(mismatch.to_string(index=False))

# 6. Final year-wise totals
print("\n6. YEAR-WISE CRASH TOTALS")

summary = df.groupby("year")[
    ["fatal_crashes", "non_fatal_crashes", "total_crashes"]
].sum()

print(summary)

# 7. Final status
print("\n7. FINAL CHECK")

if len(df) == 151 and duplicates.empty and mismatch.empty:
    print("PASS: Combined dataset passed basic validation.")
else:
    print("WARNING: Please investigate the validation results.")
