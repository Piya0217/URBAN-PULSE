from pathlib import Path

import pandas as pd


# Find the project directory from this script's location.
project_dir = Path(__file__).resolve().parents[3]
output_dir = project_dir / "data" / "processed" / "analytics" / "violations"
input_file = (
    project_dir
    / "data"
    / "processed"
    / "violations"
    / "motor_vehicle_violations.parquet"
)

EXPECTED_YEARS = set(range(2018, 2026))
EXPECTED_CATEGORY_COUNT = 40

# Map each expected output filename to the DataFrame loaded from that file.
output_files = [
    "yearly_offence_statistics.parquet",
    "yearly_top_10_offences.parquet",
    "overall_top_10_offences.parquet",
    "offence_category_trends.parquet",
    "offence_endpoint_changes.parquet",
]

datasets = {}
check_results = []


def report_check(description, passed, details=""):
    """Print and save the result of one validation check."""
    status = "PASS" if passed else "FAIL"
    message = f"{status}: {description}"

    if details:
        message += f" — {details}"

    print(message)
    check_results.append(passed)


def has_columns(dataframe, required_columns):
    """Return True when every requested column exists in a DataFrame."""
    return all(column in dataframe.columns for column in required_columns)


print("\nVALIDATING MOTOR VEHICLE ANALYTICS OUTPUTS")
print("Output directory:", output_dir)

# Check that every expected file exists, then read and summarize each one.
for filename in output_files:
    file_path = output_dir / filename
    exists = file_path.is_file()

    report_check(f"{filename} exists", exists)

    if not exists:
        print(f"\nDataset: {filename}")
        print("Rows: unavailable")
        print("Columns: unavailable")
        print("Missing-value counts: unavailable")
        datasets[filename] = None
        continue

    try:
        dataset = pd.read_parquet(file_path)
        datasets[filename] = dataset

        print(f"\nDataset: {filename}")
        print("Rows:", len(dataset))
        print("Columns:", list(dataset.columns))
        print("Missing-value counts:")
        print(dataset.isna().sum())
    except Exception as error:
        print(f"\nDataset: {filename}")
        print("Rows: unavailable")
        print("Columns: unavailable")
        print("Missing-value counts: unavailable")
        print("Read error:", error)
        datasets[filename] = None
        report_check(f"{filename} can be read as Parquet", False)

# Confirm that the loading loop successfully loaded every expected dataset.
loaded_count = sum(dataset is not None for dataset in datasets.values())
all_datasets_loaded = loaded_count == len(output_files)
report_check(
    "All five analytics datasets loaded successfully",
    all_datasets_loaded,
    f"loaded {loaded_count} of {len(output_files)} datasets",
)


# 1. Year-wise statistics checks.
yearly = datasets["yearly_offence_statistics.parquet"]

if yearly is not None and has_columns(
    yearly,
    [
        "year",
        "reported_offence_categories",
        "missing_offence_categories",
        "total_expected_categories",
        "annual_total_status",
    ],
):
    # Convert detected years to integers before comparing with expected years.
    found_years = set(
        pd.to_numeric(yearly["year"], errors="coerce")
        .dropna()
        .astype(int)
    )
    report_check(
        "Yearly statistics contain all years from 2018 through 2025",
        found_years == EXPECTED_YEARS,
        f"found years: {sorted(found_years)}",
    )

    reported = pd.to_numeric(
        yearly["reported_offence_categories"], errors="coerce"
    )
    missing = pd.to_numeric(
        yearly["missing_offence_categories"], errors="coerce"
    )
    expected = pd.to_numeric(
        yearly["total_expected_categories"], errors="coerce"
    )

    category_counts_are_valid = (
        expected.eq(EXPECTED_CATEGORY_COUNT)
        & (reported + missing).eq(EXPECTED_CATEGORY_COUNT)
    ).all()

    report_check(
        "Yearly statistics use 40 expected categories and account for all categories",
        category_counts_are_valid,
        "reported plus missing categories should equal 40 for every year",
    )

    complete_year = (
        reported.eq(EXPECTED_CATEGORY_COUNT)
        & missing.eq(0)
    )
    status_is_correct = (
        (
            complete_year
            & yearly["annual_total_status"].eq("complete")
        )
        | (
            ~complete_year
            & yearly["annual_total_status"].eq("incomplete_partial_total")
        )
    ).all()

    report_check(
        "Yearly completeness status matches reported and missing category counts",
        status_is_correct,
        "expected statuses: complete or incomplete_partial_total",
    )
else:
    report_check(
        "Yearly statistics have the columns required for validation",
        False,
        "the file is unavailable or required columns are missing",
    )


# 2. Yearly top-10 checks.
yearly_top = datasets["yearly_top_10_offences.parquet"]

if yearly_top is not None and has_columns(yearly_top, ["year", "cases"]):
    records_per_year = yearly_top.groupby("year").size()

    report_check(
        "Yearly top-10 output has no more than 10 records per year",
        records_per_year.le(10).all(),
        f"counts: {records_per_year.to_dict()}",
    )
    report_check(
        "Yearly top-10 output has no missing case counts",
        yearly_top["cases"].notna().all(),
    )
else:
    report_check(
        "Yearly top-10 output has the columns required for validation",
        False,
        "the file is unavailable or required columns are missing",
    )


# 3. Overall top-10 checks.
overall_top = datasets["overall_top_10_offences.parquet"]

if overall_top is not None:
    report_check(
        "Overall top-10 output has no more than 10 records",
        len(overall_top) <= 10,
        f"found {len(overall_top)} records",
    )
    report_check(
        "Overall top-10 output includes years_with_reported_values",
        "years_with_reported_values" in overall_top.columns,
    )
else:
    report_check(
        "Overall top-10 output is available",
        False,
        "the file is missing or could not be read",
    )


# 4. Trend output checks.
trends = datasets["offence_category_trends.parquet"]

if trends is not None:
    required_trend_columns = {
        "previous_year",
        "previous_year_cases",
    }
    missing_trend_columns = required_trend_columns.difference(trends.columns)

    report_check(
        "Trend output includes previous_year and previous_year_cases",
        not missing_trend_columns,
        f"missing columns: {sorted(missing_trend_columns)}",
    )

    if has_columns(trends, ["offence_type", "year"]):
        # Check that each category has at least one trend row for every year.
        trend_years = pd.to_numeric(trends["year"], errors="coerce")
        trend_records = pd.DataFrame(
            {
                "offence_type": trends["offence_type"],
                "year": trend_years,
            }
        ).dropna(subset=["offence_type", "year"])
        trend_records["year"] = trend_records["year"].astype(int)

        years_by_category = trend_records.groupby("offence_type")["year"].agg(
            lambda years: set(years)
        )
        all_categories = set(trends["offence_type"].dropna())

        categories_with_all_years = {
            category
            for category in all_categories
            if years_by_category.get(category, set()) == EXPECTED_YEARS
        }
        missing_years_by_category = {
            category: sorted(
                EXPECTED_YEARS - years_by_category.get(category, set())
            )
            for category in all_categories
            if years_by_category.get(category, set()) != EXPECTED_YEARS
        }

        report_check(
            "Every offence category has trend records for 2018 through 2025",
            bool(all_categories)
            and len(categories_with_all_years) == len(all_categories),
            f"categories missing years: {missing_years_by_category}",
        )
    else:
        report_check(
            "Trend output has offence_type and year columns for coverage validation",
            False,
            "one or more required columns are missing",
        )
else:
    report_check(
        "Trend output is available",
        False,
        "the file is missing or could not be read",
    )


# 5. Endpoint comparison checks.
endpoint_changes = datasets["offence_endpoint_changes.parquet"]

if endpoint_changes is not None and has_columns(
    endpoint_changes,
    ["offence_type", "cases_2018", "cases_2025"],
):
    endpoint_values_present = endpoint_changes[
        ["cases_2018", "cases_2025"]
    ].notna().all().all()

    # Compare saved endpoint categories with the cleaned source dataset to
    # confirm each one had values in both 2018 and 2025.
    if input_file.is_file():
        try:
            source = pd.read_parquet(input_file)
            source_pivot = source.pivot(
                index="offence_type",
                columns="year",
                values="cases",
            ).reindex(columns=[2018, 2025])

            eligible_categories = set(
                source_pivot.index[
                    source_pivot[2018].notna()
                    & source_pivot[2025].notna()
                ]
            )
            output_categories = set(endpoint_changes["offence_type"])
            categories_are_eligible = output_categories.issubset(
                eligible_categories
            )

            report_check(
                "Endpoint output contains only categories with both endpoint values",
                endpoint_values_present and categories_are_eligible,
                f"{len(output_categories)} output categories; "
                f"{len(eligible_categories)} eligible in the source",
            )
        except Exception as error:
            report_check(
                "Endpoint output can be checked against the cleaned source",
                False,
                f"could not validate source endpoint values: {error}",
            )
    else:
        report_check(
            "Cleaned source file is available for endpoint validation",
            False,
            f"not found: {input_file}",
        )
else:
    report_check(
        "Endpoint output has the columns required for validation",
        False,
        "the file is unavailable or required columns are missing",
    )


# Print a compact summary of all checks.
passed_checks = sum(check_results)
total_checks = len(check_results)

print("\nVALIDATION SUMMARY")
print(f"Passed: {passed_checks}/{total_checks}")

if all(check_results):
    print("OVERALL RESULT: PASS")
else:
    print("OVERALL RESULT: FAIL")
