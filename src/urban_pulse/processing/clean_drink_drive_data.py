from pathlib import Path

import pandas as pd


# Find the project folder so this script works from different directories.
project_dir = Path(__file__).resolve().parents[3]
input_file = project_dir / "data" / "raw" / "drink_and_drive_cases.csv"
output_dir = project_dir / "data" / "processed" / "violations"
output_file = output_dir / "drink_drive_violations.parquet"

# Read the original CSV. Pandas reads the source's "NA" entries as missing values.
df = pd.read_csv(input_file)

print("\nORIGINAL DRINK AND DRIVE DATA")
print("Shape:", df.shape)

# Remove the summary row so it is not treated as a month.
df["Month"] = df["Month"].astype(str).str.strip()
df = df[df["Month"].str.lower() != "total"].copy()

# The year is the first four characters of each year-specific column name.
year_columns = [column for column in df.columns if column[:4].isdigit()]

# Reshape from one row per month to one row per month and year.
cleaned_df = df.melt(
    id_vars=["Month"],
    value_vars=year_columns,
    var_name="year",
    value_name="cases",
)

# Keep only the year from the original column label and standardize the names.
cleaned_df = cleaned_df.rename(columns={"Month": "month"})
cleaned_df["year"] = cleaned_df["year"].str[:4].astype(int)

# Convert case counts to numbers while keeping missing values missing.
cleaned_df["cases"] = pd.to_numeric(cleaned_df["cases"], errors="coerce")

# Save the long-format dataset as Parquet.
output_dir.mkdir(parents=True, exist_ok=True)
cleaned_df.to_parquet(output_file, engine="pyarrow", index=False)

print("\nCLEANED DRINK AND DRIVE DATA")
print("Shape:", cleaned_df.shape)
print("Columns:", list(cleaned_df.columns))

print("\nMissing values:")
print(cleaned_df.isna().sum())

print("\nYears available:")
print(sorted(cleaned_df["year"].unique()))

print("\nSample records:")
print(cleaned_df.head(10))

print("\nSaved:", output_file)
