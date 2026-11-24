from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark.sql.types import NumericType


# Resolve project paths from this script's location.
project_dir = Path(__file__).resolve().parents[3]
violations_dir = project_dir / "data" / "processed" / "violations"
analytics_dir = project_dir / "data" / "processed" / "analytics" / "violations"

EXPECTED_YEARS = set(range(2011, 2026))
EXPECTED_CATEGORIES = {
    "M.V. Act",
    "K.P. Act",
    "K.T.C. Act",
    "Towing",
    "Automation",
}
EXPECTED_CATEGORY_COUNT = 5
EXPECTED_YEAR_COUNT = 15
EXPECTED_CATEGORY_ROW_COUNT = EXPECTED_YEAR_COUNT * EXPECTED_CATEGORY_COUNT
FLOAT_TOLERANCE = 1e-9


# Output names, expected row counts, and required columns from the analytics script.
OUTPUT_SPECS = {
    "yearly_statistics": {
        "filename": "traffic_cases_fines_yearly_statistics.parquet",
        "rows": EXPECTED_YEAR_COUNT,
        "columns": [
            "year",
            "total_cases_booked",
            "total_fine_collected",
            "previous_year",
            "previous_total_cases_booked",
            "cases_change",
            "cases_change_percent",
            "previous_total_fine_collected",
            "fine_change",
            "fine_change_percent",
        ],
    },
    "category_yearly_statistics": {
        "filename": "traffic_cases_fines_category_yearly_statistics.parquet",
        "rows": EXPECTED_CATEGORY_ROW_COUNT,
        "columns": ["year", "category", "cases", "fine_collected"],
    },
    "category_cases_ranking": {
        "filename": "traffic_cases_fines_category_cases_ranking.parquet",
        "rows": EXPECTED_CATEGORY_COUNT,
        "columns": [
            "rank",
            "category",
            "available_cases_total",
            "reported_years",
            "expected_years",
        ],
    },
    "category_fines_ranking": {
        "filename": "traffic_cases_fines_category_fines_ranking.parquet",
        "rows": EXPECTED_CATEGORY_COUNT,
        "columns": [
            "rank",
            "category",
            "available_fine_total",
            "reported_years",
            "expected_years",
        ],
    },
    "category_trends": {
        "filename": "traffic_cases_fines_category_trends.parquet",
        "rows": EXPECTED_CATEGORY_ROW_COUNT,
        "columns": [
            "year",
            "category",
            "cases",
            "fine_collected",
            "previous_year",
            "previous_cases",
            "cases_change",
            "previous_fine_collected",
            "fine_change",
        ],
    },
    "fine_per_case": {
        "filename": "traffic_cases_fines_fine_per_case.parquet",
        "rows": EXPECTED_CATEGORY_ROW_COUNT,
        "columns": [
            "year",
            "category",
            "cases",
            "fine_collected",
            "fine_per_case",
        ],
    },
}

check_results = []


def report_check(description, passed, details=""):
    """Print and store the result of one validation check."""
    status = "PASS" if passed else "FAIL"
    message = f"{status}: {description}"

    if details:
        message += f" — {details}"

    print(message)
    check_results.append(bool(passed))


def read_parquet(spark, file_path, label, required_columns):
    """Check that a Parquet file exists, can be read, and has required columns."""
    if not file_path.is_file():
        report_check(f"{label} exists", False, str(file_path))
        report_check(f"{label} is readable", False, "file does not exist")
        report_check(f"{label} has required columns", False, "file unavailable")
        return None

    report_check(f"{label} exists", True)

    try:
        dataframe = spark.read.parquet(str(file_path))
    except Exception as error:
        report_check(f"{label} is readable", False, str(error))
        report_check(f"{label} has required columns", False, "file unreadable")
        return None

    report_check(f"{label} is readable", True)

    missing_columns = set(required_columns).difference(dataframe.columns)
    report_check(
        f"{label} has required columns",
        not missing_columns,
        f"missing columns: {sorted(missing_columns)}",
    )

    return dataframe


def load_output_datasets(spark):
    """Load each analytics output and check its expected number of rows."""
    datasets = {}

    for key, specification in OUTPUT_SPECS.items():
        filename = specification["filename"]
        file_path = analytics_dir / filename
        dataframe = read_parquet(
            spark,
            file_path,
            filename,
            specification["columns"],
        )
        datasets[key] = dataframe

        if dataframe is None:
            report_check(
                f"{filename} has {specification['rows']} rows",
                False,
                "dataset unavailable",
            )
            continue

        actual_rows = dataframe.count()
        report_check(
            f"{filename} has {specification['rows']} rows",
            actual_rows == specification["rows"],
            f"found {actual_rows}",
        )

        print(f"\nDataset: {filename}")
        print("Rows:", actual_rows)
        print("Columns:", dataframe.columns)

    all_loaded = all(dataframe is not None for dataframe in datasets.values())
    report_check(
        "All six analytics outputs were loaded successfully",
        all_loaded,
    )

    return datasets


def check_year_values(dataset_name, dataframe):
    """Check that a dataset's year column is valid and covers 2011–2025."""
    if dataframe is None or "year" not in dataframe.columns:
        report_check(
            f"{dataset_name} has no null or invalid years",
            False,
            "dataset or year column unavailable",
        )
        report_check(
            f"{dataset_name} covers 2011–2025",
            False,
            "dataset or year column unavailable",
        )
        return

    invalid_year_count = dataframe.filter(
        F.col("year").isNull()
        | ~F.col("year").isin(sorted(EXPECTED_YEARS))
    ).count()
    report_check(
        f"{dataset_name} has no null or invalid years",
        invalid_year_count == 0,
        f"found {invalid_year_count} invalid year rows",
    )

    found_years = {
        row["year"]
        for row in dataframe.select("year").distinct().collect()
        if row["year"] is not None
    }
    report_check(
        f"{dataset_name} covers 2011–2025",
        found_years == EXPECTED_YEARS,
        f"found years: {sorted(found_years)}",
    )


def check_category_values(dataset_name, dataframe):
    """Check that a dataset contains exactly the five expected categories."""
    if dataframe is None or "category" not in dataframe.columns:
        report_check(
            f"{dataset_name} contains the five expected categories",
            False,
            "dataset or category column unavailable",
        )
        return

    actual_categories = {
        row["category"]
        for row in dataframe.select("category").distinct().collect()
        if row["category"] is not None
    }
    null_category_count = dataframe.filter(
        F.col("category").isNull()
    ).count()

    report_check(
        f"{dataset_name} contains the five expected categories",
        (
            actual_categories == EXPECTED_CATEGORIES
            and len(actual_categories) == EXPECTED_CATEGORY_COUNT
            and null_category_count == 0
        ),
        f"found categories: {sorted(actual_categories)}; "
        f"null category rows: {null_category_count}",
    )


def check_duplicate_year_category_records(dataset_name, dataframe):
    """Check for duplicate records with the same year and category."""
    required_columns = {"year", "category"}

    if dataframe is None or not required_columns.issubset(dataframe.columns):
        report_check(
            f"{dataset_name} has no duplicate year-category records",
            False,
            "dataset or required columns unavailable",
        )
        return

    duplicate_count = (
        dataframe.groupBy("year", "category")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    report_check(
        f"{dataset_name} has no duplicate year-category records",
        duplicate_count == 0,
        f"found {duplicate_count} duplicate groups",
    )


def check_source_numeric_values(dataset_name, dataframe, columns, allow_nulls):
    """Check source metric types and values, allowing nulls only when requested."""
    if dataframe is None:
        report_check(
            f"{dataset_name} numeric values are valid",
            False,
            "dataset unavailable",
        )
        return

    missing_columns = set(columns).difference(dataframe.columns)
    if missing_columns:
        report_check(
            f"{dataset_name} numeric values are valid",
            False,
            f"missing columns: {sorted(missing_columns)}",
        )
        return

    invalid_details = []
    for column in columns:
        data_type = dataframe.schema[column].dataType
        if not isinstance(data_type, NumericType):
            invalid_details.append(
                f"{column} has non-numeric type {data_type.simpleString()}"
            )
            continue

        null_count = dataframe.filter(F.col(column).isNull()).count()
        negative_count = dataframe.filter(F.col(column) < 0).count()

        if not allow_nulls and null_count > 0:
            invalid_details.append(f"{column} has {null_count} null values")
        if negative_count > 0:
            invalid_details.append(
                f"{column} has {negative_count} negative values"
            )

    report_check(
        f"{dataset_name} numeric values are valid",
        not invalid_details,
        "; ".join(invalid_details) if invalid_details else "",
    )


def check_non_negative_values(dataset_name, dataframe, columns):
    """Check that count, fine, and rate values are not negative."""
    if dataframe is None:
        report_check(
            f"{dataset_name} has no negative measure values",
            False,
            "dataset unavailable",
        )
        return

    missing_columns = set(columns).difference(dataframe.columns)
    if missing_columns:
        report_check(
            f"{dataset_name} has no negative measure values",
            False,
            f"missing columns: {sorted(missing_columns)}",
        )
        return

    negative_counts = {
        column: dataframe.filter(F.col(column) < 0).count()
        for column in columns
    }
    total_negative_values = sum(negative_counts.values())

    report_check(
        f"{dataset_name} has no negative measure values",
        total_negative_values == 0,
        f"negative values by column: {negative_counts}",
    )


def check_source_category_dataset(dataframe):
    """Independently validate the cleaned category source dataset."""
    if dataframe is None:
        report_check(
            "Category source has exactly 75 rows",
            False,
            "dataset unavailable",
        )
        return

    row_count = dataframe.count()
    report_check(
        "Category source has exactly 75 rows",
        row_count == EXPECTED_CATEGORY_ROW_COUNT,
        f"found {row_count}",
    )
    check_year_values("Category source", dataframe)
    check_category_values("Category source", dataframe)
    check_duplicate_year_category_records("Category source", dataframe)
    check_source_numeric_values(
        "Category source",
        dataframe,
        ["cases", "fine_collected"],
        allow_nulls=True,
    )


def check_source_annual_totals_dataset(dataframe):
    """Independently validate the cleaned reported annual totals source."""
    if dataframe is None:
        report_check(
            "Annual totals source has exactly 15 rows",
            False,
            "dataset unavailable",
        )
        report_check(
            "Annual totals source has one record per year",
            False,
            "dataset unavailable",
        )
        return

    row_count = dataframe.count()
    report_check(
        "Annual totals source has exactly 15 rows",
        row_count == EXPECTED_YEAR_COUNT,
        f"found {row_count}",
    )
    check_year_values("Annual totals source", dataframe)

    if "year" not in dataframe.columns:
        report_check(
            "Annual totals source has one record per year",
            False,
            "year column unavailable",
        )
    else:
        duplicate_year_count = (
            dataframe.groupBy("year")
            .count()
            .filter(F.col("count") > 1)
            .count()
        )
        report_check(
            "Annual totals source has one record per year",
            duplicate_year_count == 0 and row_count == EXPECTED_YEAR_COUNT,
            f"found {duplicate_year_count} duplicate year groups",
        )

    check_source_numeric_values(
        "Annual totals source",
        dataframe,
        ["total_cases_booked", "total_fine_collected"],
        allow_nulls=False,
    )


def record_keys_with_null(dataframe, column):
    """Return year-category keys where a metric is null."""
    return {
        (row["year"], row["category"])
        for row in dataframe
        .filter(F.col(column).isNull())
        .select("year", "category")
        .collect()
    }


def check_ktc_missing_values(source_categories, datasets):
    """Check that known K.T.C. nulls are preserved in applicable outputs."""
    if source_categories is None or not {
        "year",
        "category",
        "cases",
        "fine_collected",
    }.issubset(source_categories.columns):
        report_check(
            "Source has the expected four matching K.T.C. Act null records",
            False,
            "category input or required columns unavailable",
        )
        expected_case_null_keys = set()
        expected_fine_null_keys = set()
    else:
        expected_case_null_keys = record_keys_with_null(
            source_categories,
            "cases",
        )
        expected_fine_null_keys = record_keys_with_null(
            source_categories,
            "fine_collected",
        )

        expected_source_pattern = (
            len(expected_case_null_keys) == 4
            and len(expected_fine_null_keys) == 4
            and expected_case_null_keys == expected_fine_null_keys
            and all(
                category == "K.T.C. Act"
                for _, category in expected_case_null_keys
            )
        )
        report_check(
            "Source has the expected four matching K.T.C. Act null records",
            expected_source_pattern,
            f"null case records: {len(expected_case_null_keys)}; "
            f"null fine records: {len(expected_fine_null_keys)}",
        )

    # These outputs retain row-level category metrics, so their null keys
    # should match the source input exactly.
    row_level_outputs = [
        "category_yearly_statistics",
        "category_trends",
        "fine_per_case",
    ]

    for output_name in row_level_outputs:
        dataframe = datasets.get(output_name)
        required_columns = {
            "year",
            "category",
            "cases",
            "fine_collected",
        }
        if dataframe is None or not required_columns.issubset(dataframe.columns):
            report_check(
                f"{output_name} preserves the K.T.C. Act null records",
                False,
                "dataset or required columns unavailable",
            )
            continue

        output_case_null_keys = record_keys_with_null(dataframe, "cases")
        output_fine_null_keys = record_keys_with_null(
            dataframe,
            "fine_collected",
        )

        nulls_preserved = (
            output_case_null_keys == expected_case_null_keys
            and output_fine_null_keys == expected_fine_null_keys
            and output_case_null_keys == output_fine_null_keys
        )
        report_check(
            f"{output_name} preserves the K.T.C. Act null records",
            nulls_preserved,
            f"null case records: {len(output_case_null_keys)}; "
            f"null fine records: {len(output_fine_null_keys)}",
        )

    # Rankings aggregate values, so verify their reported-year counts instead.
    for output_name in ["category_cases_ranking", "category_fines_ranking"]:
        dataframe = datasets.get(output_name)
        required_columns = {"category", "reported_years", "expected_years"}

        if dataframe is None or not required_columns.issubset(dataframe.columns):
            report_check(
                f"{output_name} reports K.T.C. Act coverage correctly",
                False,
                "dataset or required columns unavailable",
            )
            continue

        ktc_row = dataframe.filter(F.col("category") == "K.T.C. Act")
        ktc_coverage_is_correct = (
            ktc_row.count() == 1
            and ktc_row.filter(
                (F.col("reported_years") == EXPECTED_YEAR_COUNT - 4)
                & (F.col("expected_years") == EXPECTED_YEAR_COUNT)
            ).count() == 1
        )
        report_check(
            f"{output_name} reports K.T.C. Act coverage correctly",
            ktc_coverage_is_correct,
            "expected 11 reported years out of 15",
        )

    # The rate should remain null where the K.T.C. source values are missing.
    fine_per_case = datasets.get("fine_per_case")
    if fine_per_case is None or "fine_per_case" not in fine_per_case.columns:
        report_check(
            "Fine-per-case values remain null for missing K.T.C. Act records",
            False,
            "dataset or fine_per_case column unavailable",
        )
    else:
        rate_null_keys = record_keys_with_null(
            fine_per_case,
            "fine_per_case",
        )
        report_check(
            "Fine-per-case values remain null for missing K.T.C. Act records",
            expected_case_null_keys.issubset(rate_null_keys),
        )


def check_ranking(dataset_name, dataframe, total_column):
    """Check ranks are exactly 1–5 and categories match the expected set."""
    required_columns = {
        "rank",
        "category",
        total_column,
        "reported_years",
        "expected_years",
    }

    if dataframe is None or not required_columns.issubset(dataframe.columns):
        report_check(
            f"{dataset_name} has unique ranks from 1 to 5",
            False,
            "dataset or required columns unavailable",
        )
        report_check(
            f"{dataset_name} contains all five categories",
            False,
            "dataset or required columns unavailable",
        )
        return

    ranks = {
        row["rank"]
        for row in dataframe.select("rank").distinct().collect()
        if row["rank"] is not None
    }
    rank_values_are_correct = (
        ranks == {1, 2, 3, 4, 5}
        and dataframe.filter(F.col("rank").isNull()).count() == 0
        and dataframe.count() == EXPECTED_CATEGORY_COUNT
    )
    report_check(
        f"{dataset_name} has unique ranks from 1 to 5",
        rank_values_are_correct,
        f"found ranks: {sorted(ranks)}",
    )

    check_category_values(dataset_name, dataframe)

    expected_year_values_are_correct = (
        dataframe.filter(
            F.col("expected_years") != EXPECTED_YEAR_COUNT
        ).count() == 0
    )
    report_check(
        f"{dataset_name} reports 15 expected years per category",
        expected_year_values_are_correct,
    )

    ktc_reported_years_are_correct = (
        dataframe.filter(F.col("category") == "K.T.C. Act")
        .filter(F.col("reported_years") == EXPECTED_YEAR_COUNT - 4)
        .count() == 1
    )
    report_check(
        f"{dataset_name} reports 11 available years for K.T.C. Act",
        ktc_reported_years_are_correct,
    )


def check_trend_changes(trends, source_categories):
    """Check predecessor fields and changes against the cleaned category source."""
    required_columns = {
        "year",
        "category",
        "cases",
        "fine_collected",
        "previous_year",
        "previous_cases",
        "cases_change",
        "previous_fine_collected",
        "fine_change",
    }

    if (
        trends is None
        or source_categories is None
        or not required_columns.issubset(trends.columns)
        or not {
            "year",
            "category",
            "cases",
            "fine_collected",
        }.issubset(source_categories.columns)
    ):
        report_check(
            "Trend predecessor fields match the preceding source year",
            False,
            "trend output, source input, or required columns unavailable",
        )
        report_check(
            "Category trend changes follow the missing-value rules",
            False,
            "trend output or required columns unavailable",
        )
        report_check(
            "First-year trend changes and previous-year values are null",
            False,
            "trend output or required columns unavailable",
        )
        return

    # Calculate predecessor values independently from the cleaned source.
    source_window = Window.partitionBy("category").orderBy("year")
    expected_previous = (
        source_categories
        .withColumn(
            "expected_previous_year",
            F.lag("year").over(source_window),
        )
        .withColumn(
            "expected_previous_cases",
            F.lag("cases").over(source_window),
        )
        .withColumn(
            "expected_previous_fine",
            F.lag("fine_collected").over(source_window),
        )
        .select(
            "year",
            "category",
            "expected_previous_year",
            "expected_previous_cases",
            "expected_previous_fine",
        )
    )

    actual_previous = trends.select(
        "year",
        "category",
        F.col("previous_year").alias("actual_previous_year"),
        F.col("previous_cases").alias("actual_previous_cases"),
        F.col("previous_fine_collected").alias("actual_previous_fine"),
    )

    predecessor_comparison = expected_previous.join(
        actual_previous,
        on=["year", "category"],
        how="full_outer",
    )

    predecessor_mismatches = predecessor_comparison.filter(
        ~F.col("expected_previous_year").eqNullSafe(
            F.col("actual_previous_year")
        )
        | ~F.col("expected_previous_cases").eqNullSafe(
            F.col("actual_previous_cases")
        )
        | ~F.col("expected_previous_fine").eqNullSafe(
            F.col("actual_previous_fine")
        )
    ).count()

    report_check(
        "Trend predecessor fields match the preceding source year for the same category",
        predecessor_mismatches == 0,
        f"found {predecessor_mismatches} mismatched rows",
    )

    consecutive_years = F.col("previous_year") == F.col("year") - 1

    valid_case_pair = F.coalesce(
        consecutive_years
        & F.col("cases").isNotNull()
        & F.col("previous_cases").isNotNull(),
        F.lit(False),
    )
    invalid_case_change = (
        (valid_case_pair & F.col("cases_change").isNull())
        | (~valid_case_pair & F.col("cases_change").isNotNull())
        | (
            valid_case_pair
            & (
                F.abs(
                    F.col("cases_change")
                    - (F.col("cases") - F.col("previous_cases"))
                )
                > FLOAT_TOLERANCE
            )
        )
    )

    valid_fine_pair = F.coalesce(
        consecutive_years
        & F.col("fine_collected").isNotNull()
        & F.col("previous_fine_collected").isNotNull(),
        F.lit(False),
    )
    invalid_fine_change = (
        (valid_fine_pair & F.col("fine_change").isNull())
        | (~valid_fine_pair & F.col("fine_change").isNotNull())
        | (
            valid_fine_pair
            & (
                F.abs(
                    F.col("fine_change")
                    - (
                        F.col("fine_collected")
                        - F.col("previous_fine_collected")
                    )
                )
                > FLOAT_TOLERANCE
            )
        )
    )

    invalid_change_count = trends.filter(
        invalid_case_change | invalid_fine_change
    ).count()
    report_check(
        "Category trend changes are null unless consecutive-year values exist, and otherwise equal the difference",
        invalid_change_count == 0,
        f"found {invalid_change_count} invalid trend rows",
    )

    first_year_rows = trends.filter(F.col("year") == 2011)
    first_year_invalid_count = first_year_rows.filter(
        F.col("previous_year").isNotNull()
        | F.col("previous_cases").isNotNull()
        | F.col("previous_fine_collected").isNotNull()
        | F.col("cases_change").isNotNull()
        | F.col("fine_change").isNotNull()
    ).count()
    first_year_is_correct = (
        first_year_rows.count() == EXPECTED_CATEGORY_COUNT
        and first_year_invalid_count == 0
    )
    report_check(
        "First-year trend changes and previous-year values are null",
        first_year_is_correct,
        f"first-year rows: {first_year_rows.count()}",
    )


def check_fine_per_case(dataframe):
    """Check null rules and ratios using a floating-point tolerance."""
    required_columns = {
        "cases",
        "fine_collected",
        "fine_per_case",
    }
    if dataframe is None or not required_columns.issubset(dataframe.columns):
        report_check(
            "Fine-per-case values follow null and ratio rules",
            False,
            "dataset or required columns unavailable",
        )
        return

    should_be_null = (
        F.col("cases").isNull()
        | F.col("fine_collected").isNull()
        | (F.col("cases") == 0)
    )
    should_have_ratio = F.coalesce(
        F.col("cases").isNotNull()
        & F.col("fine_collected").isNotNull()
        & (F.col("cases") > 0),
        F.lit(False),
    )

    expected_ratio = (
        F.col("fine_collected").cast("double")
        / F.col("cases").cast("double")
    )

    invalid_rate = (
        (should_be_null & F.col("fine_per_case").isNotNull())
        | (should_have_ratio & F.col("fine_per_case").isNull())
        | (
            should_have_ratio
            & (
                F.abs(
                    F.col("fine_per_case").cast("double") - expected_ratio
                )
                > FLOAT_TOLERANCE
            )
        )
    )

    invalid_rate_count = dataframe.filter(invalid_rate).count()
    report_check(
        "Fine-per-case is null when inputs are missing or cases are zero, and otherwise matches fine_collected / cases",
        invalid_rate_count == 0,
        f"found {invalid_rate_count} invalid rates",
    )


def check_yearly_totals(yearly, source_annual_totals):
    """Compare yearly output totals to the reported annual totals input."""
    required_columns = {
        "year",
        "total_cases_booked",
        "total_fine_collected",
    }

    if (
        yearly is None
        or source_annual_totals is None
        or not required_columns.issubset(yearly.columns)
        or not required_columns.issubset(source_annual_totals.columns)
    ):
        report_check(
            "Yearly statistics match the original reported annual totals",
            False,
            "yearly output, source input, or required columns unavailable",
        )
        report_check(
            "First-year yearly changes are null",
            False,
            "yearly output or required columns unavailable",
        )
        return

    output_totals = yearly.select(
        "year",
        F.col("total_cases_booked").alias("output_cases"),
        F.col("total_fine_collected").alias("output_fines"),
    )
    source_totals = source_annual_totals.select(
        "year",
        F.col("total_cases_booked").alias("source_cases"),
        F.col("total_fine_collected").alias("source_fines"),
    )

    totals_comparison = output_totals.join(
        source_totals,
        on="year",
        how="full_outer",
    )
    mismatch_count = totals_comparison.filter(
        F.col("output_cases").isNull()
        | F.col("source_cases").isNull()
        | F.col("output_fines").isNull()
        | F.col("source_fines").isNull()
        | ~F.col("output_cases").eqNullSafe(F.col("source_cases"))
        | ~F.col("output_fines").eqNullSafe(F.col("source_fines"))
    ).count()

    report_check(
        "Yearly statistics match the original reported annual totals",
        mismatch_count == 0,
        f"found {mismatch_count} mismatched years",
    )

    first_year = yearly.filter(F.col("year") == 2011)
    first_year_changes_are_null = (
        first_year.count() == 1
        and first_year.filter(
            F.col("previous_year").isNotNull()
            | F.col("previous_total_cases_booked").isNotNull()
            | F.col("previous_total_fine_collected").isNotNull()
            | F.col("cases_change").isNotNull()
            | F.col("cases_change_percent").isNotNull()
            | F.col("fine_change").isNotNull()
            | F.col("fine_change_percent").isNotNull()
        ).count() == 0
    )
    report_check(
        "First-year yearly changes and previous-year values are null",
        first_year_changes_are_null,
    )


def build_and_check_reconciliation(category_source, annual_source):
    """Compare available category sums with reported totals without filling nulls."""
    required_category_columns = {
        "year",
        "cases",
        "fine_collected",
    }
    required_annual_columns = {
        "year",
        "total_cases_booked",
        "total_fine_collected",
    }

    if (
        category_source is None
        or annual_source is None
        or not required_category_columns.issubset(category_source.columns)
        or not required_annual_columns.issubset(annual_source.columns)
    ):
        report_check(
            "Category-to-annual reconciliation distinguishes missing values from mismatches",
            False,
            "source inputs or required columns unavailable",
        )
        return

    # Spark sum ignores nulls and returns only the sum of reported values.
    # Count nulls separately; no missing values are replaced with zero.
    category_sums = (
        category_source.groupBy("year")
        .agg(
            F.sum("cases").alias("available_category_cases"),
            F.sum("fine_collected").alias("available_category_fines"),
            F.count(
                F.when(F.col("cases").isNull(), F.lit(1))
            ).alias("missing_case_categories"),
            F.count(
                F.when(F.col("fine_collected").isNull(), F.lit(1))
            ).alias("missing_fine_categories"),
        )
    )

    reconciliation = (
        category_sums.join(annual_source, on="year", how="inner")
        .withColumn(
            "case_reconciliation_status",
            F.when(
                F.col("missing_case_categories") > 0,
                F.lit("INCOMPLETE"),
            )
            .when(
                F.col("available_category_cases").eqNullSafe(
                    F.col("total_cases_booked")
                ),
                F.lit("PASS"),
            )
            .otherwise(F.lit("WARN")),
        )
        .withColumn(
            "fine_reconciliation_status",
            F.when(
                F.col("missing_fine_categories") > 0,
                F.lit("INCOMPLETE"),
            )
            .when(
                F.col("available_category_fines").eqNullSafe(
                    F.col("total_fine_collected")
                ),
                F.lit("PASS"),
            )
            .otherwise(F.lit("WARN")),
        )
        .select(
            "year",
            "available_category_cases",
            "total_cases_booked",
            "missing_case_categories",
            "case_reconciliation_status",
            "available_category_fines",
            "total_fine_collected",
            "missing_fine_categories",
            "fine_reconciliation_status",
        )
        .orderBy("year")
    )

    print("\nCATEGORY SUMS VS REPORTED ANNUAL TOTALS")
    reconciliation.show(EXPECTED_YEAR_COUNT, truncate=False)

    expected_case_status = (
        F.when(
            F.col("missing_case_categories") > 0,
            F.lit("INCOMPLETE"),
        )
        .when(
            F.col("available_category_cases").eqNullSafe(
                F.col("total_cases_booked")
            ),
            F.lit("PASS"),
        )
        .otherwise(F.lit("WARN"))
    )
    expected_fine_status = (
        F.when(
            F.col("missing_fine_categories") > 0,
            F.lit("INCOMPLETE"),
        )
        .when(
            F.col("available_category_fines").eqNullSafe(
                F.col("total_fine_collected")
            ),
            F.lit("PASS"),
        )
        .otherwise(F.lit("WARN"))
    )
    status_mismatch_count = reconciliation.filter(
        ~F.col("case_reconciliation_status").eqNullSafe(expected_case_status)
        | ~F.col("fine_reconciliation_status").eqNullSafe(expected_fine_status)
    ).count()

    for row in reconciliation.orderBy("year").collect():
        print(
            f"{row['year']}: cases {row['case_reconciliation_status']}; "
            f"fines {row['fine_reconciliation_status']} "
            f"(missing case categories: {row['missing_case_categories']}, "
            f"missing fine categories: {row['missing_fine_categories']})."
        )

    case_pass_count = reconciliation.filter(
        F.col("case_reconciliation_status") == "PASS"
    ).count()
    case_warning_count = reconciliation.filter(
        F.col("case_reconciliation_status") == "WARN"
    ).count()
    case_incomplete_count = reconciliation.filter(
        F.col("case_reconciliation_status") == "INCOMPLETE"
    ).count()
    fine_pass_count = reconciliation.filter(
        F.col("fine_reconciliation_status") == "PASS"
    ).count()
    fine_warning_count = reconciliation.filter(
        F.col("fine_reconciliation_status") == "WARN"
    ).count()
    fine_incomplete_count = reconciliation.filter(
        F.col("fine_reconciliation_status") == "INCOMPLETE"
    ).count()

    report_check(
        "Reconciliation statuses distinguish matches, mismatches, and missing values",
        reconciliation.count() == EXPECTED_YEAR_COUNT
        and status_mismatch_count == 0,
        f"cases: {case_pass_count} PASS, {case_warning_count} WARN, "
        f"{case_incomplete_count} INCOMPLETE; "
        f"fines: {fine_pass_count} PASS, {fine_warning_count} WARN, "
        f"{fine_incomplete_count} INCOMPLETE",
    )


def main():
    spark = (
        SparkSession.builder
        .appName("ValidateTrafficCasesFinesAnalytics")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        print("\nVALIDATING TRAFFIC CASES AND FINES ANALYTICS")

        outputs = load_output_datasets(spark)

        # Load cleaned source Parquet files as independent validation references.
        source_categories = read_parquet(
            spark,
            violations_dir / "traffic_cases_fines_long.parquet",
            "traffic_cases_fines_long.parquet source",
            ["year", "category", "cases", "fine_collected"],
        )
        source_annual_totals = read_parquet(
            spark,
            violations_dir / "traffic_cases_fines_annual_totals.parquet",
            "traffic_cases_fines_annual_totals.parquet source",
            ["year", "total_cases_booked", "total_fine_collected"],
        )

        # Independently validate both cleaned source datasets.
        check_source_category_dataset(source_categories)
        check_source_annual_totals_dataset(source_annual_totals)

        # Validate years and categories in the analytics outputs.
        for dataset_name in [
            "yearly_statistics",
            "category_yearly_statistics",
            "category_trends",
            "fine_per_case",
        ]:
            check_year_values(dataset_name, outputs.get(dataset_name))

        for dataset_name in [
            "category_yearly_statistics",
            "category_cases_ranking",
            "category_fines_ranking",
            "category_trends",
            "fine_per_case",
        ]:
            check_category_values(dataset_name, outputs.get(dataset_name))

        # Check unique year-category rows wherever those keys apply.
        for dataset_name in [
            "category_yearly_statistics",
            "category_trends",
            "fine_per_case",
        ]:
            check_duplicate_year_category_records(
                dataset_name,
                outputs.get(dataset_name),
            )

        check_ktc_missing_values(source_categories, outputs)

        check_ranking(
            "Category cases ranking",
            outputs.get("category_cases_ranking"),
            "available_cases_total",
        )
        check_ranking(
            "Category fines ranking",
            outputs.get("category_fines_ranking"),
            "available_fine_total",
        )

        check_trend_changes(
            outputs.get("category_trends"),
            source_categories,
        )
        check_fine_per_case(outputs.get("fine_per_case"))
        check_yearly_totals(
            outputs.get("yearly_statistics"),
            source_annual_totals,
        )

        # Changes may be negative, so check only measures that should be
        # non-negative, not the year-over-year change columns.
        non_negative_checks = [
            (
                "Yearly statistics",
                outputs.get("yearly_statistics"),
                [
                    "total_cases_booked",
                    "total_fine_collected",
                    "previous_total_cases_booked",
                    "previous_total_fine_collected",
                ],
            ),
            (
                "Category yearly statistics",
                outputs.get("category_yearly_statistics"),
                ["cases", "fine_collected"],
            ),
            (
                "Category cases ranking",
                outputs.get("category_cases_ranking"),
                ["available_cases_total"],
            ),
            (
                "Category fines ranking",
                outputs.get("category_fines_ranking"),
                ["available_fine_total"],
            ),
            (
                "Category trends",
                outputs.get("category_trends"),
                [
                    "cases",
                    "fine_collected",
                    "previous_cases",
                    "previous_fine_collected",
                ],
            ),
            (
                "Fine per case",
                outputs.get("fine_per_case"),
                ["cases", "fine_collected", "fine_per_case"],
            ),
        ]
        for dataset_name, dataframe, columns in non_negative_checks:
            check_non_negative_values(dataset_name, dataframe, columns)

        build_and_check_reconciliation(
            source_categories,
            source_annual_totals,
        )

    finally:
        spark.stop()

    passed_checks = sum(check_results)
    failed_checks = len(check_results) - passed_checks

    print("\nVALIDATION SUMMARY")
    print("Passed checks:", passed_checks)
    print("Failed checks:", failed_checks)
    print("Total checks:", len(check_results))

    if failed_checks > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
