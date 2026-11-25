
from pathlib import Path
import pandas as pd

# File paths
input_file = Path("data/raw/motor_vehicle_act_cases.csv")
output_dir = Path("data/processed/violations")
output_dir.mkdir(parents=True, exist_ok=True)

# Read original dataset
df = pd.read_csv(input_file)

print("\nORIGINAL DATASET")
print("Shape:", df.shape)

# Remove the summary row, if present
df["Type of Offences"] = df["Type of Offences"].astype(str).str.strip()

df = df[
    df["Type of Offences"].str.lower() != "total"
].copy()

# Remove unnecessary serial number
df = df.drop(columns=["Sl.No."], errors="ignore")

# Convert year columns into long format
year_columns = [
    col for col in df.columns
    if col.isdigit()
]

cleaned_df = df.melt(
    id_vars=["Type of Offences"],
    value_vars=year_columns,
    var_name="year",
    value_name="cases"
)

# Standardise column names
cleaned_df = cleaned_df.rename(
    columns={"Type of Offences": "offence_type"}
)

cleaned_df["year"] = cleaned_df["year"].astype(int)

# Preserve missing values; do not replace them with zero
cleaned_df["cases"] = pd.to_numeric(
    cleaned_df["cases"],
    errors="coerce"
)

# Save cleaned dataset
output_file = output_dir / "motor_vehicle_violations.parquet"

cleaned_df.to_parquet(
    output_file,
    engine="pyarrow",
    index=False
)

print("\nCLEANED DATASET")
print("Shape:", cleaned_df.shape)
print("Columns:", list(cleaned_df.columns))
print("\nMissing values:")
print(cleaned_df.isnull().sum())

print("\nSample records:")
print(cleaned_df.head(10))

print("\nSaved:", output_file)
