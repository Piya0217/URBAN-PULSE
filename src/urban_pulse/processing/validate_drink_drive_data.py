from pathlib import Path

import pandas as pd


# Find the project directory so the script works from different directories.
project_dir = Path(__file__).resolve().parents[3]
file_path = (
    project_dir
    / "data"
    / "processed"
    / "violations"
    / "drink_drive_violations.parquet"
)

expected_columns = ["month", "year", "cases"]
expected_years = [2016, 2017, 2018]
expected_months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Store each check's result so the script can print a clear summary at the end.
results = []


def report_check(description, passed, details=""):
    """Print and store the result of one validation check."""
    status = "PASS" if passed else "FAIL"
    message = f"{status}: {description}"
    if details:
        message += f" — {details}"

    print(message)
    results.append(passed)


print("\nVALIDATING DRINK AND DRIVE DATA")
print("File:", file_path)

# Read the saved Parquet file.
df = pd.read_parquet(file_path)

print("\nDimensions:", df.shape)
print("Columns:", list(df.columns))

# Check that the output has the expected size and columns.
report_check(
    "Dataset dimensions are 36 rows and 3 columns",
    df.shape == (36, 3),
    f"found {df.shape[0]} rows and {df.shape[1]} columns",
)
report_check(
    "Expected columns are present in the expected order",
    list(df.columns) == expected_columns,
)

# Only run field-specific checks if all required columns are available.
has_expected_columns = all(column in df.columns for column in expected_columns)

if has_expected_columns:
    # Convert years temporarily for comparison. This does not change the data.
    numeric_year = pd.to_numeric(df["year"], errors="coerce")
    years_found = sorted(numeric_year.dropna().unique().tolist())

    report_check(
        "Year coverage is 2016, 2017, and 2018",
        years_found == expected_years,
        f"found {years_found}",
    )

    # Count records for each expected year, including years with no records.
    records_per_year = numeric_year.value_counts().reindex(
        expected_years, fill_value=0
    )
    report_check(
        "Each year has exactly 12 records",
        records_per_year.eq(12).all(),
        f"counts: {records_per_year.to_dict()}",
    )

    # Normalize month spelling and surrounding spaces for the month checks.
    normalized_month = (
        df["month"]
        .astype("string")
        .str.strip()
        .str.capitalize()
    )
    valid_month = normalized_month.isin(expected_months).fillna(False)

    # Each year should contain every expected month exactly as a represented
    # month. Duplicate month-year combinations are checked separately below.
    month_coverage = {}
    for year in expected_years:
        months_for_year = set(
            normalized_month[
                (numeric_year == year) & valid_month
            ].dropna()
        )
        month_coverage[year] = len(months_for_year) == 12 and months_for_year == set(
            expected_months
        )

    report_check(
        "All 12 months are represented for each year",
        all(month_coverage.values()),
        f"complete years: "
        f"{[year for year, complete in month_coverage.items() if complete]}",
    )

    # Missing cases are counted without replacing or changing them.
    missing_cases_per_year = (
        df.assign(validated_year=numeric_year)
        .groupby("validated_year")["cases"]
        .apply(lambda cases: cases.isna().sum())
    )
    missing_2016 = int(missing_cases_per_year.get(2016, 0))
    missing_2017 = int(missing_cases_per_year.get(2017, 0))
    missing_2018 = int(missing_cases_per_year.get(2018, 0))

    report_check(
        "2016 and 2017 have no missing case counts",
        missing_2016 == 0 and missing_2017 == 0,
        f"2016: {missing_2016}, 2017: {missing_2017}",
    )
    report_check(
        "2018 has exactly 10 missing case counts",
        missing_2018 == 10,
        f"found {missing_2018}",
    )

    # A month-year pair should occur only once.
    month_year_duplicates = df.assign(
        validated_month=normalized_month,
        validated_year=numeric_year,
    ).duplicated(subset=["validated_month", "validated_year"]).sum()

    report_check(
        "There are no duplicate month-year records",
        month_year_duplicates == 0,
        f"found {month_year_duplicates}",
    )

    # Convert cases temporarily so negative numbers can be compared safely.
    numeric_cases = pd.to_numeric(df["cases"], errors="coerce")
    negative_case_count = int((numeric_cases < 0).sum())

    report_check(
        "There are no negative case counts",
        negative_case_count == 0,
        f"found {negative_case_count}",
    )

    # Missing or unrecognized month names are invalid.
    invalid_month_count = int((~valid_month).sum())

    report_check(
        "All month names are valid",
        invalid_month_count == 0,
        f"found {invalid_month_count} invalid month values",
    )
else:
    # Mark checks that need missing columns as failed instead of raising
    # confusing errors while trying to access a field that is not present.
    report_check(
        "Field checks can run",
        False,
        "one or more expected columns are missing",
    )

# Summarize all checks.
passed_checks = sum(results)
total_checks = len(results)

print("\nVALIDATION SUMMARY")
print(f"Passed: {passed_checks}/{total_checks}")

if all(results):
    print("OVERALL RESULT: PASS")
else:
    print("OVERALL RESULT: FAIL")
