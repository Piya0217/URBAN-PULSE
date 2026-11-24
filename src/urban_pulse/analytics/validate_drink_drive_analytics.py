from pathlib import Path

import pandas as pd


# Resolve the project directory from this script's location.
project_dir = Path(__file__).resolve().parents[3]
output_dir = project_dir / "data" / "processed" / "analytics" / "violations"

EXPECTED_YEARS = {2016, 2017, 2018}
EXPECTED_MONTHS = {
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
}
EXPECTED_TOTALS = {
    2016: 58928,
    2017: 73741,
    2018: 12277,
}
EXPECTED_REPORTED_MONTHS = {
    2016: 12,
    2017: 12,
    2018: 2,
}
EXPECTED_MISSING_MONTHS = {
    2016: 0,
    2017: 0,
    2018: 10,
}
EXPECTED_STATUSES = {
    2016: "COMPLETE",
    2017: "COMPLETE",
    2018: "INCOMPLETE",
}

# The filenames and required columns produced by the analytics script.
output_files = {
    "yearly_drink_drive_statistics.parquet": [
        "year",
        "available_cases",
        "reported_months",
        "missing_months",
        "total_expected_months",
        "annual_total_status",
    ],
    "monthly_drink_drive_statistics.parquet": [
        "month",
        "month_number",
        "year",
        "cases",
        "previous_year",
        "previous_year_cases",
        "change_from_previous_year",
    ],
    "drink_drive_yearly_comparison.parquet": [
        "year",
        "available_cases",
        "reported_months",
        "missing_months",
        "total_expected_months",
        "annual_total_status",
        "comparison_guidance",
    ],
}

datasets = {}
check_results = []


def report_check(description, passed, details=""):
    """Print and store the result of one validation check."""
    status = "PASS" if passed else "FAIL"
    message = f"{status}: {description}"

    if details:
        message += f" — {details}"

    print(message)
    check_results.append(bool(passed))


def has_columns(dataframe, required_columns):
    """Return True when every requested column exists in the DataFrame."""
    return all(column in dataframe.columns for column in required_columns)


def series_match_with_nulls(actual, expected):
    """Compare two Series, considering nulls equal when they occur together."""
    matches = actual.eq(expected) | (actual.isna() & expected.isna())
    return matches.fillna(False).all()


def values_match_by_year(dataframe, numeric_years, column, expected_values):
    """Check that a numeric column has the expected value for each year."""
    for year, expected_value in expected_values.items():
        matching_values = pd.to_numeric(
            dataframe.loc[numeric_years == year, column],
            errors="coerce",
        )

        # Require exactly one row for each expected year.
        if len(matching_values) != 1:
            return False

        actual_value = matching_values.iloc[0]
        if pd.isna(actual_value) or actual_value != expected_value:
            return False

    return True


print("\nVALIDATING DRINK AND DRIVE ANALYTICS OUTPUTS")
print("Output directory:", output_dir)

# Check that each output exists, can be read, and report its basic details.
for filename, required_columns in output_files.items():
    file_path = output_dir / filename
    file_exists = file_path.is_file()

    report_check(f"{filename} exists", file_exists)

    if not file_exists:
        print(f"\nDataset: {filename}")
        print("Rows: unavailable")
        print("Columns: unavailable")
        print("Missing-value counts: unavailable")
        datasets[filename] = None
        report_check(f"{filename} is readable", False, "file does not exist")
        continue

    try:
        dataset = pd.read_parquet(file_path)
        datasets[filename] = dataset

        print(f"\nDataset: {filename}")
        print("Rows:", len(dataset))
        print("Columns:", list(dataset.columns))
        print("Missing-value counts:")
        print(dataset.isna().sum())

        report_check(f"{filename} is readable", True)
        report_check(
            f"{filename} contains its required columns",
            has_columns(dataset, required_columns),
            f"required columns: {required_columns}",
        )
    except Exception as error:
        datasets[filename] = None
        print(f"\nDataset: {filename}")
        print("Rows: unavailable")
        print("Columns: unavailable")
        print("Missing-value counts: unavailable")
        print("Read error:", error)
        report_check(f"{filename} is readable", False, str(error))


# 1. Validate yearly statistics.
yearly = datasets["yearly_drink_drive_statistics.parquet"]
yearly_required = output_files["yearly_drink_drive_statistics.parquet"]

if yearly is not None and has_columns(yearly, yearly_required):
    numeric_years = pd.to_numeric(yearly["year"], errors="coerce")
    found_years = set(numeric_years.dropna().astype(int))

    report_check(
        "Yearly statistics contain 2016, 2017, and 2018",
        found_years == EXPECTED_YEARS,
        f"found years: {sorted(found_years)}",
    )

    expected_month_counts = (
        pd.to_numeric(yearly["total_expected_months"], errors="coerce")
        .eq(12)
        .all()
    )
    report_check(
        "Each year has 12 expected months",
        expected_month_counts,
    )

    reported_months_match = values_match_by_year(
        yearly,
        numeric_years,
        "reported_months",
        EXPECTED_REPORTED_MONTHS,
    )
    missing_months_match = values_match_by_year(
        yearly,
        numeric_years,
        "missing_months",
        EXPECTED_MISSING_MONTHS,
    )
    report_check(
        "Reported and missing month counts match expectations",
        reported_months_match and missing_months_match,
        "2016: 12 reported / 0 missing; "
        "2017: 12 reported / 0 missing; "
        "2018: 2 reported / 10 missing",
    )

    annual_totals_match = values_match_by_year(
        yearly,
        numeric_years,
        "available_cases",
        EXPECTED_TOTALS,
    )
    report_check(
        "Available annual totals match expectations",
        annual_totals_match,
        "2016: 58928; 2017: 73741; 2018: 12277",
    )

    statuses_match = all(
        len(yearly.loc[numeric_years == year, "annual_total_status"]) == 1
        and yearly.loc[
            numeric_years == year, "annual_total_status"
        ].iloc[0] == expected_status
        for year, expected_status in EXPECTED_STATUSES.items()
    )
    report_check(
        "Completeness statuses match expectations",
        statuses_match,
        "2016 and 2017: COMPLETE; 2018: INCOMPLETE",
    )

    # Yearly statistics should not contain nulls in required fields.
    yearly_fields_present = yearly[yearly_required].notna().all().all()
    report_check(
        "Yearly statistics have no missing values in required fields",
        yearly_fields_present,
    )
else:
    report_check(
        "Yearly statistics checks can run",
        False,
        "file unavailable or required columns missing",
    )


# 2. Validate monthly statistics.
monthly = datasets["monthly_drink_drive_statistics.parquet"]
monthly_required = output_files["monthly_drink_drive_statistics.parquet"]

if monthly is not None and has_columns(monthly, monthly_required):
    report_check(
        "Monthly statistics contain exactly 36 records",
        len(monthly) == 36,
        f"found {len(monthly)} records",
    )

    found_months = set(monthly["month"].dropna())
    report_check(
        "Monthly statistics contain all 12 expected months",
        found_months == EXPECTED_MONTHS,
        f"found {len(found_months)} distinct month names",
    )

    # Check that each month name has its correct calendar month number.
    expected_month_numbers = monthly["month"].map(
        {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12,
        }
    )
    actual_month_numbers = pd.to_numeric(
        monthly["month_number"],
        errors="coerce",
    )
    month_numbers_match = (
        expected_month_numbers.eq(actual_month_numbers)
        .fillna(False)
        .all()
    )
    report_check(
        "Each month has its correct calendar month_number",
        month_numbers_match,
    )

    numeric_years = pd.to_numeric(monthly["year"], errors="coerce")
    monthly_pairs = {
        (month, int(year))
        for month, year in zip(monthly["month"], numeric_years)
        if pd.notna(month) and pd.notna(year)
    }
    expected_month_year_pairs = {
        (month, year)
        for month in EXPECTED_MONTHS
        for year in EXPECTED_YEARS
    }
    records_per_month_year = monthly.groupby(["month", "year"]).size()

    one_record_per_month_year = (
        monthly_pairs == expected_month_year_pairs
        and records_per_month_year.eq(1).all()
    )
    report_check(
        "Each month has exactly one record for each year",
        one_record_per_month_year,
    )

    # Month, month number, and year are essential identifiers and should not
    # be missing. The case and comparison columns are allowed to contain nulls.
    identifiers_present = monthly[
        ["month", "month_number", "year"]
    ].notna().all().all()
    report_check(
        "Monthly essential identifier fields have no missing values",
        identifiers_present,
    )

    # Check that the expected 2018 case values are missing or present correctly.
    missing_case_months = {
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    }
    expected_missing_case_rows = (
        numeric_years.eq(2018) & monthly["month"].isin(missing_case_months)
    )
    actual_missing_case_rows = monthly["cases"].isna()

    case_missing_pattern_matches = (
        expected_missing_case_rows == actual_missing_case_rows
    ).all()
    report_check(
        "2018 March through December cases remain null, with no unexpected null cases",
        case_missing_pattern_matches,
        "only 2018 March–December should have missing case values",
    )

    january_2018 = pd.to_numeric(
        monthly.loc[
            numeric_years.eq(2018) & monthly["month"].eq("January"),
            "cases",
        ],
        errors="coerce",
    )
    february_2018 = pd.to_numeric(
        monthly.loc[
            numeric_years.eq(2018) & monthly["month"].eq("February"),
            "cases",
        ],
        errors="coerce",
    )

    january_is_correct = (
        len(january_2018) == 1
        and pd.notna(january_2018.iloc[0])
        and january_2018.iloc[0] == 7022
    )
    february_is_correct = (
        len(february_2018) == 1
        and pd.notna(february_2018.iloc[0])
        and february_2018.iloc[0] == 5255
    )
    report_check(
        "2018 January and February cases match expectations",
        january_is_correct and february_is_correct,
        "January: 7022; February: 5255",
    )

    # Recalculate the prior row within each month. With one row per month-year,
    # this gives the preceding calendar year's value for that same month.
    ordered_monthly = monthly.copy()
    ordered_monthly["numeric_year"] = numeric_years
    ordered_monthly["numeric_cases"] = pd.to_numeric(
        ordered_monthly["cases"], errors="coerce"
    )
    ordered_monthly = ordered_monthly.sort_values(
        ["month", "numeric_year"]
    )

    expected_previous_year = ordered_monthly.groupby("month")[
        "numeric_year"
    ].shift(1)
    expected_previous_cases = ordered_monthly.groupby("month")[
        "numeric_cases"
    ].shift(1)

    actual_previous_year = pd.to_numeric(
        ordered_monthly["previous_year"], errors="coerce"
    )
    actual_previous_cases = pd.to_numeric(
        ordered_monthly["previous_year_cases"], errors="coerce"
    )

    previous_values_match = (
        series_match_with_nulls(actual_previous_year, expected_previous_year)
        and series_match_with_nulls(
            actual_previous_cases,
            expected_previous_cases,
        )
    )

    consecutive_years = (
        expected_previous_year
        == ordered_monthly["numeric_year"] - 1
    )
    valid_comparison = (
        ordered_monthly["numeric_cases"].notna()
        & expected_previous_cases.notna()
        & consecutive_years
    )
    expected_changes = (
        ordered_monthly["numeric_cases"] - expected_previous_cases
    ).where(valid_comparison)
    actual_changes = pd.to_numeric(
        ordered_monthly["change_from_previous_year"],
        errors="coerce",
    )

    changes_match = series_match_with_nulls(
        actual_changes,
        expected_changes,
    )
    report_check(
        "Year-over-year changes use valid values from consecutive years only",
        previous_values_match and changes_match,
    )

    first_year_rows = ordered_monthly["numeric_year"].eq(2016)
    first_year_previous_fields_are_null = ordered_monthly.loc[
        first_year_rows,
        ["previous_year", "previous_year_cases"],
    ].isna().all().all()
    report_check(
        "2016 previous_year and previous_year_cases are null",
        first_year_previous_fields_are_null,
    )
else:
    report_check(
        "Monthly statistics checks can run",
        False,
        "file unavailable or required columns missing",
    )


# 3. Validate yearly comparison labels and guidance.
comparison = datasets["drink_drive_yearly_comparison.parquet"]
comparison_required = output_files["drink_drive_yearly_comparison.parquet"]

if comparison is not None and has_columns(comparison, comparison_required):
    numeric_years = pd.to_numeric(comparison["year"], errors="coerce")

    comparison_statuses_match = all(
        len(comparison.loc[numeric_years == year, "annual_total_status"]) == 1
        and comparison.loc[
            numeric_years == year, "annual_total_status"
        ].iloc[0] == expected_status
        for year, expected_status in EXPECTED_STATUSES.items()
    )
    report_check(
        "Yearly comparison completeness statuses are correct",
        comparison_statuses_match,
    )

    guidance_2018 = comparison.loc[
        numeric_years == 2018,
        "comparison_guidance",
    ]

    partial_guidance_is_clear = (
        len(guidance_2018) == 1
        and isinstance(guidance_2018.iloc[0], str)
        and "not directly comparable" in guidance_2018.iloc[0].lower()
    )
    report_check(
        "2018 is labeled partial and not directly comparable to complete totals",
        partial_guidance_is_clear,
    )

    comparison_fields_present = comparison[comparison_required].notna().all().all()
    report_check(
        "Yearly comparison has no missing values in required fields",
        comparison_fields_present,
    )
else:
    report_check(
        "Yearly comparison checks can run",
        False,
        "file unavailable or required columns missing",
    )


# Print a summary of all checks.
passed_checks = sum(check_results)
total_checks = len(check_results)

print("\nVALIDATION SUMMARY")
print(f"Passed: {passed_checks}/{total_checks}")

if check_results and all(check_results):
    print("OVERALL RESULT: PASS")
else:
    print("OVERALL RESULT: FAIL")
