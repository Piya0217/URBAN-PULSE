from pathlib import Path

import pandas as pd


# Resolve paths from this script's location.
project_dir = Path(__file__).resolve().parents[3]
data_dir = project_dir / "data" / "processed" / "violations"
category_file = data_dir / "traffic_cases_fines_long.parquet"
annual_totals_file = data_dir / "traffic_cases_fines_annual_totals.parquet"
raw_file = project_dir / "data" / "raw" / "traffic_cases_and_fines.csv"

EXPECTED_YEARS = set(range(2011, 2026))
EXPECTED_CATEGORIES = {
    "M.V. Act",
    "K.P. Act",
    "Towing",
    "K.T.C. Act",
    "Automation",
}

CATEGORY_COLUMNS = ["year", "category", "cases", "fine_collected"]
ANNUAL_TOTAL_COLUMNS = [
    "year",
    "total_cases_booked",
    "total_fine_collected",
]
RAW_TOTAL_COLUMNS = [
    "YEAR",
    "Total Cases Booked",
    "Total Fine Collected",
]

check_results = []


def report_check(description, passed, details=""):
    """Print and store the result of one validation check."""
    status = "PASS" if passed else "FAIL"
    message = f"{status}: {description}"

    if details:
        message += f" — {details}"

    print(message)
    check_results.append(bool(passed))


def load_parquet(file_path):
    """Check that a Parquet file exists and can be read with PyArrow."""
    if not file_path.is_file():
        report_check(f"{file_path.name} exists", False)
        report_check(
            f"{file_path.name} is readable",
            False,
            "file does not exist",
        )
        return None

    report_check(f"{file_path.name} exists", True)

    try:
        dataframe = pd.read_parquet(file_path, engine="pyarrow")
    except Exception as error:
        report_check(
            f"{file_path.name} is readable",
            False,
            str(error),
        )
        return None

    report_check(f"{file_path.name} is readable", True)
    print(f"\nDataset: {file_path.name}")
    print("Shape:", dataframe.shape)
    print("Columns:", list(dataframe.columns))
    print("Missing-value counts:")
    print(dataframe.isna().sum())

    return dataframe


def check_category_dataset(dataframe):
    """Validate the long-format category dataset."""
    if dataframe is None:
        report_check("Category dataset has the expected shape", False, "unavailable")
        report_check("Category dataset has the required columns", False, "unavailable")
        report_check("Category dataset covers 2011–2025", False, "unavailable")
        report_check("Category dataset has exactly five categories", False, "unavailable")
        report_check(
            "Category dataset has one record per year and category",
            False,
            "unavailable",
        )
        report_check(
            "Category dataset has exactly four missing case and fine values, all in K.T.C. Act",
            False,
            "unavailable",
        )
        report_check(
            "Category dataset has no missing year or category values",
            False,
            "unavailable",
        )
        report_check(
            "Category case and fine values are numeric or null",
            False,
            "unavailable",
        )
        report_check(
            "Category dataset has no negative case or fine values",
            False,
            "unavailable",
        )
        return

    report_check(
        "Category dataset has the expected shape of 75 rows by 4 columns",
        dataframe.shape == (75, 4),
        f"found {dataframe.shape[0]} rows by {dataframe.shape[1]} columns",
    )

    has_required_columns = set(CATEGORY_COLUMNS).issubset(dataframe.columns)
    report_check(
        "Category dataset has the required columns",
        has_required_columns,
        f"required: {CATEGORY_COLUMNS}",
    )

    if not has_required_columns:
        report_check("Category dataset covers 2011–2025", False, "year column unavailable")
        report_check("Category dataset has exactly five categories", False, "category column unavailable")
        report_check(
            "Category dataset has one record per year and category",
            False,
            "required columns unavailable",
        )
        report_check(
            "Category dataset has exactly four missing case and fine values, all in K.T.C. Act",
            False,
            "required columns unavailable",
        )
        report_check(
            "Category dataset has no missing year or category values",
            False,
            "required columns unavailable",
        )
        report_check(
            "Category case and fine values are numeric or null",
            False,
            "required columns unavailable",
        )
        report_check(
            "Category dataset has no negative case or fine values",
            False,
            "required columns unavailable",
        )
        return

    numeric_years = pd.to_numeric(dataframe["year"], errors="coerce")
    found_years = set(numeric_years.dropna())

    report_check(
        "Category dataset covers every year from 2011 through 2025",
        found_years == EXPECTED_YEARS,
        f"found years: {sorted(found_years)}",
    )

    found_categories = set(dataframe["category"].dropna())
    report_check(
        "Category dataset contains exactly the five expected categories",
        found_categories == EXPECTED_CATEGORIES,
        f"found categories: {sorted(found_categories)}",
    )

    expected_pairs = {
        (year, category)
        for year in EXPECTED_YEARS
        for category in EXPECTED_CATEGORIES
    }
    actual_pairs = {
        (year, category)
        for year, category in zip(numeric_years, dataframe["category"])
        if pd.notna(year) and pd.notna(category)
    }
    pair_counts = dataframe.groupby(["year", "category"], dropna=False).size()

    one_record_per_pair = (
        actual_pairs == expected_pairs
        and pair_counts.eq(1).all()
    )
    report_check(
        "Category dataset has exactly one record per year and category",
        one_record_per_pair,
    )

    cases_missing = dataframe["cases"].isna()
    fines_missing = dataframe["fine_collected"].isna()

    # Require the same four K.T.C. Act records to be missing both values.
    missing_values_are_expected = (
        cases_missing.equals(fines_missing)
        and int(cases_missing.sum()) == 4
        and int(fines_missing.sum()) == 4
        and dataframe.loc[cases_missing, "category"].eq("K.T.C. Act").all()
        and dataframe.loc[fines_missing, "category"].eq("K.T.C. Act").all()
    )
    report_check(
        "Category dataset has exactly four missing case and fine values on the same K.T.C. Act records",
        missing_values_are_expected,
        f"missing cases: {cases_missing.sum()}, "
        f"missing fines: {fines_missing.sum()}",
    )

    no_missing_identifiers = (
        dataframe["year"].notna().all()
        and dataframe["category"].notna().all()
    )
    report_check(
        "Category dataset has no missing year or category values",
        no_missing_identifiers,
    )

    numeric_cases = pd.to_numeric(dataframe["cases"], errors="coerce")
    numeric_fines = pd.to_numeric(
        dataframe["fine_collected"],
        errors="coerce",
    )
    invalid_cases = dataframe["cases"].notna() & numeric_cases.isna()
    invalid_fines = (
        dataframe["fine_collected"].notna()
        & numeric_fines.isna()
    )
    no_invalid_numeric_values = (
        not invalid_cases.any()
        and not invalid_fines.any()
    )
    report_check(
        "Category case and fine values are numeric or null",
        no_invalid_numeric_values,
        f"invalid case values: {invalid_cases.sum()}, "
        f"invalid fine values: {invalid_fines.sum()}",
    )

    no_negative_values = (
        not (numeric_cases < 0).any()
        and not (numeric_fines < 0).any()
    )
    report_check(
        "Category dataset has no negative case or fine values",
        no_negative_values,
    )


def check_annual_totals_dataset(dataframe):
    """Validate the annual totals dataset."""
    if dataframe is None:
        report_check("Annual totals have the expected shape", False, "unavailable")
        report_check("Annual totals have the required columns", False, "unavailable")
        report_check(
            "Annual totals cover 2011–2025 exactly once",
            False,
            "unavailable",
        )
        report_check(
            "Annual total fields are numeric",
            False,
            "unavailable",
        )
        report_check(
            "Annual totals have no missing or negative values",
            False,
            "unavailable",
        )
        return

    report_check(
        "Annual totals have the expected shape of 15 rows by 3 columns",
        dataframe.shape == (15, 3),
        f"found {dataframe.shape[0]} rows by {dataframe.shape[1]} columns",
    )

    has_required_columns = set(ANNUAL_TOTAL_COLUMNS).issubset(dataframe.columns)
    report_check(
        "Annual totals have the required columns",
        has_required_columns,
        f"required: {ANNUAL_TOTAL_COLUMNS}",
    )

    if not has_required_columns:
        report_check(
            "Annual totals cover 2011–2025 exactly once",
            False,
            "required columns unavailable",
        )
        report_check(
            "Annual total fields are numeric",
            False,
            "required columns unavailable",
        )
        report_check(
            "Annual totals have no missing or negative values",
            False,
            "required columns unavailable",
        )
        return

    numeric_years = pd.to_numeric(dataframe["year"], errors="coerce")
    found_years = set(numeric_years.dropna())
    one_record_per_year = (
        len(dataframe) == 15
        and found_years == EXPECTED_YEARS
        and numeric_years.value_counts().eq(1).all()
    )
    report_check(
        "Annual totals cover 2011–2025 exactly once",
        one_record_per_year,
        f"found years: {sorted(found_years)}",
    )

    numeric_cases = pd.to_numeric(
        dataframe["total_cases_booked"],
        errors="coerce",
    )
    numeric_fines = pd.to_numeric(
        dataframe["total_fine_collected"],
        errors="coerce",
    )
    invalid_cases = (
        dataframe["total_cases_booked"].notna()
        & numeric_cases.isna()
    )
    invalid_fines = (
        dataframe["total_fine_collected"].notna()
        & numeric_fines.isna()
    )
    no_invalid_numeric_values = (
        not invalid_cases.any()
        and not invalid_fines.any()
    )
    report_check(
        "Annual total fields are numeric",
        no_invalid_numeric_values,
        f"invalid case totals: {invalid_cases.sum()}, "
        f"invalid fine totals: {invalid_fines.sum()}",
    )

    no_missing_values = dataframe[ANNUAL_TOTAL_COLUMNS].notna().all().all()
    no_negative_values = (
        not (numeric_cases < 0).any()
        and not (numeric_fines < 0).any()
    )

    report_check(
        "Annual totals have no missing or negative values",
        no_missing_values and no_negative_values,
        f"missing values present: {not no_missing_values}; "
        f"negative values present: {not no_negative_values}",
    )


def compare_annual_totals_to_raw(annual_totals, raw_dataframe):
    """Confirm the cleaned annual totals match the values reported in the CSV."""
    if annual_totals is None or raw_dataframe is None:
        report_check(
            "Annual totals match the original raw CSV",
            False,
            "annual totals or raw CSV unavailable",
        )
        return

    missing_raw_columns = [
        column for column in RAW_TOTAL_COLUMNS
        if column not in raw_dataframe.columns
    ]
    if missing_raw_columns:
        report_check(
            "Annual totals match the original raw CSV",
            False,
            f"raw CSV missing columns: {missing_raw_columns}",
        )
        return

    raw_totals = raw_dataframe[RAW_TOTAL_COLUMNS].copy()
    raw_totals = raw_totals.rename(
        columns={
            "YEAR": "year",
            "Total Cases Booked": "raw_total_cases_booked",
            "Total Fine Collected": "raw_total_fine_collected",
        }
    )

    cleaned_totals = annual_totals[
        ["year", "total_cases_booked", "total_fine_collected"]
    ].copy()

    for dataframe in (raw_totals, cleaned_totals):
        dataframe["year"] = pd.to_numeric(dataframe["year"], errors="coerce")

    raw_totals["raw_total_cases_booked"] = pd.to_numeric(
        raw_totals["raw_total_cases_booked"],
        errors="coerce",
    )
    raw_totals["raw_total_fine_collected"] = pd.to_numeric(
        raw_totals["raw_total_fine_collected"],
        errors="coerce",
    )
    cleaned_totals["total_cases_booked"] = pd.to_numeric(
        cleaned_totals["total_cases_booked"],
        errors="coerce",
    )
    cleaned_totals["total_fine_collected"] = pd.to_numeric(
        cleaned_totals["total_fine_collected"],
        errors="coerce",
    )

    try:
        comparison = cleaned_totals.merge(
            raw_totals,
            on="year",
            how="outer",
            indicator=True,
            validate="one_to_one",
        )

        years_match = comparison["_merge"].eq("both").all()
        cases_match = comparison["total_cases_booked"].eq(
            comparison["raw_total_cases_booked"]
        ).all()
        fines_match = comparison["total_fine_collected"].eq(
            comparison["raw_total_fine_collected"]
        ).all()

        totals_unchanged = years_match and cases_match and fines_match
    except Exception as error:
        totals_unchanged = False
        details = f"comparison failed: {error}"
    else:
        details = (
            "compared total cases and total fines by year against the raw CSV"
        )

    report_check(
        "Reported annual totals are unchanged from the original raw CSV",
        totals_unchanged,
        details,
    )


print("\nVALIDATING TRAFFIC CASES AND FINES DATA")

# Read the Parquet outputs with Pandas and the PyArrow engine.
category_df = load_parquet(category_file)
annual_totals_df = load_parquet(annual_totals_file)

# Read the source CSV only for the reported-total comparison.
if not raw_file.is_file():
    raw_df = None
    report_check("Original raw CSV exists for comparison", False)
else:
    try:
        raw_df = pd.read_csv(raw_file)
        report_check("Original raw CSV is readable for comparison", True)
    except Exception as error:
        raw_df = None
        report_check(
            "Original raw CSV is readable for comparison",
            False,
            str(error),
        )

check_category_dataset(category_df)
check_annual_totals_dataset(annual_totals_df)
compare_annual_totals_to_raw(annual_totals_df, raw_df)

# Print the final count of passed and failed checks.
passed_checks = sum(check_results)
failed_checks = len(check_results) - passed_checks

print("\nVALIDATION SUMMARY")
print("Passed checks:", passed_checks)
print("Failed checks:", failed_checks)
print("Total checks:", len(check_results))

if failed_checks == 0:
    print("OVERALL RESULT: PASS")
else:
    print("OVERALL RESULT: FAIL")
