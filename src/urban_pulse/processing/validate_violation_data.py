from pathlib import Path

import pandas as pd


# Find the project directory from this script so the file can be run from
# either the project root or another working directory.
project_dir = Path(__file__).resolve().parents[3]
file_path = (
    project_dir
    / "data"
    / "processed"
    / "violations"
    / "motor_vehicle_violations.parquet"
)

# The cleaner creates one row for every offence category and year.
expected_columns = ["offence_type", "year", "cases"]
expected_years = list(range(2018, 2026))

df = pd.read_parquet(file_path)

print("\nVALIDATING MOTOR VEHICLE VIOLATION DATA")
print("File:", file_path)

# 1. Dimensions tell us how many records and fields are in the dataset.
print("\n1. DATASET DIMENSIONS")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

# 2. Compare the dataset schema with the columns produced by the cleaner.
print("\n2. COLUMN NAMES")
print("Found:", list(df.columns))
missing_columns = [column for column in expected_columns if column not in df.columns]
extra_columns = [column for column in df.columns if column not in expected_columns]
print("Missing expected columns:", missing_columns)
print("Unexpected columns:", extra_columns)

# The remaining checks rely on these three fields. Stop with a clear message
# if the input schema is incomplete, instead of raising a confusing KeyError.
required_columns = {"offence_type", "year", "cases"}
if not required_columns.issubset(df.columns):
    raise ValueError(
        "Cannot run all validation checks because one or more required "
        "columns are missing."
    )

# Convert years temporarily for validation. This does not alter the DataFrame
# or the Parquet file; it lets us identify text, fractional, and out-of-range years.
numeric_year = pd.to_numeric(df["year"], errors="coerce")
valid_year = (
    numeric_year.notna()
    & numeric_year.mod(1).eq(0)
    & numeric_year.isin(expected_years)
)
invalid_year_rows = df.loc[~valid_year, ["offence_type", "year"]]
found_years = sorted(numeric_year[valid_year].astype(int).unique().tolist())
missing_years = [year for year in expected_years if year not in found_years]
unexpected_years = sorted(
    numeric_year[numeric_year.notna() & ~numeric_year.isin(expected_years)]
    .unique()
    .tolist()
)

# 3. Year coverage checks which expected years appear and flags invalid values.
print("\n3. YEAR COVERAGE")
print("Expected years:", expected_years)
print("Years found:", found_years)
print("Missing expected years:", missing_years)
print("Unexpected numeric years:", unexpected_years)
print("Invalid year rows (null, non-numeric, fractional, or out of range):")
print(invalid_year_rows if not invalid_year_rows.empty else "None")

# 4. Count distinct non-missing offence categories.
print("\n4. OFFENCE CATEGORIES")
print("Unique offence categories:", df["offence_type"].nunique(dropna=True))

# 5. Missing values are reported as-is. In particular, missing case counts
# remain missing and are never filled with zero.
print("\n5. MISSING VALUES BY COLUMN")
print(df.isna().sum())

# 6. Exact duplicate rows may indicate repeated records in the cleaned data.
print("\n6. DUPLICATE RECORDS")
print("Duplicate rows:", df.duplicated().sum())

# 7. Show a row count for every expected year, including years with no rows.
records_per_year = df.loc[valid_year].groupby(numeric_year[valid_year].astype(int)).size()
records_per_year = records_per_year.reindex(expected_years, fill_value=0)
print("\n7. RECORDS PER YEAR")
print(records_per_year.rename_axis("year"))

# 8. Count missing case values per expected year. Reindexing keeps years with
# no records visible and reports zero missing values for those empty groups.
yearly_rows = df.loc[valid_year].copy()
yearly_rows["validated_year"] = numeric_year[valid_year].astype(int)
missing_cases_per_year = (
    yearly_rows.groupby("validated_year")["cases"]
    .apply(lambda cases: cases.isna().sum())
    .reindex(expected_years, fill_value=0)
)
print("\n8. MISSING CASE VALUES PER YEAR")
print(missing_cases_per_year.rename_axis("year"))

# 9. Negative case counts are not valid counts. Missing cases are not counted
# as negative and remain unchanged in the data.
numeric_cases = pd.to_numeric(df["cases"], errors="coerce")
negative_cases = df.loc[numeric_cases < 0, ["offence_type", "year", "cases"]]
print("\n9. NEGATIVE CASE COUNTS")
print("Negative case rows:", len(negative_cases))
print(negative_cases if not negative_cases.empty else "None")

print("\nVALIDATION COMPLETED")
