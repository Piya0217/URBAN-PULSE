from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark.sql.types import NumericType


# Resolve project paths from this script's location.
project_dir = Path(__file__).resolve().parents[3]
violations_dir = project_dir / "data" / "processed" / "violations"
analytics_dir = project_dir / "data" / "processed" / "analytics" / "violations"

category_input_file = violations_dir / "traffic_cases_fines_long.parquet"
annual_totals_input_file = (
    violations_dir / "traffic_cases_fines_annual_totals.parquet"
)

EXPECTED_CATEGORY_COUNT = 5
EXPECTED_CATEGORIES = {
    "M.V. Act",
    "K.P. Act",
    "K.T.C. Act",
    "Towing",
    "Automation",
}
EXPECTED_YEARS = set(range(2011, 2026))
EXPECTED_YEAR_COUNT = 15


def validate_inputs(category_df, annual_totals_df):
    """Check input schemas, categories, years, and metric values."""
    required_category_columns = {
        "year",
        "category",
        "cases",
        "fine_collected",
    }
    required_annual_columns = {
        "year",
        "total_cases_booked",
        "total_fine_collected",
    }

    missing_category_columns = required_category_columns.difference(
        category_df.columns
    )
    if missing_category_columns:
        raise ValueError(
            "Category dataset is missing required columns: "
            f"{sorted(missing_category_columns)}"
        )

    missing_annual_columns = required_annual_columns.difference(
        annual_totals_df.columns
    )
    if missing_annual_columns:
        raise ValueError(
            "Annual totals dataset is missing required columns: "
            f"{sorted(missing_annual_columns)}"
        )

    # Neither input may have a missing year value.
    for dataset_name, dataframe in [
        ("Category dataset", category_df),
        ("Annual totals dataset", annual_totals_df),
    ]:
        null_year_count = dataframe.filter(F.col("year").isNull()).count()
        if null_year_count > 0:
            raise ValueError(
                f"{dataset_name} contains {null_year_count} null year values."
            )

    # Reject missing category labels before comparing the category set.
    null_category_count = category_df.filter(
        F.col("category").isNull()
    ).count()
    if null_category_count > 0:
        raise ValueError(
            f"Category dataset contains {null_category_count} null category values."
        )

    actual_categories = {
        row["category"]
        for row in category_df.select("category").distinct().collect()
    }
    if actual_categories != EXPECTED_CATEGORIES:
        missing_categories = EXPECTED_CATEGORIES - actual_categories
        unexpected_categories = actual_categories - EXPECTED_CATEGORIES
        raise ValueError(
            "Category dataset does not match the expected category set. "
            f"Missing: {sorted(missing_categories)}; "
            f"unexpected: {sorted(unexpected_categories)}."
        )

    if len(actual_categories) != EXPECTED_CATEGORY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CATEGORY_COUNT} categories, "
            f"but found {len(actual_categories)}."
        )

    print(
        "Category set confirmed:",
        ", ".join(sorted(actual_categories)),
    )

    category_years = {
        row["year"]
        for row in category_df.select("year").distinct().collect()
    }
    if category_years != EXPECTED_YEARS:
        raise ValueError(
            "Category dataset must cover years 2011–2025. "
            f"Found: {sorted(category_years)}."
        )

    if category_df.count() != EXPECTED_YEAR_COUNT * EXPECTED_CATEGORY_COUNT:
        raise ValueError(
            "Expected 75 category-year records, but found "
            f"{category_df.count()}."
        )

    duplicate_category_years = (
        category_df.groupBy("year", "category")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    if duplicate_category_years:
        raise ValueError(
            "Found duplicate year-category records: "
            f"{duplicate_category_years}."
        )

    # Confirm that both metrics are missing on the same four K.T.C. Act rows.
    missing_cases_records = {
        (row["year"], row["category"])
        for row in category_df
        .filter(F.col("cases").isNull())
        .select("year", "category")
        .collect()
    }
    missing_fines_records = {
        (row["year"], row["category"])
        for row in category_df
        .filter(F.col("fine_collected").isNull())
        .select("year", "category")
        .collect()
    }

    expected_ktc_missing_pattern = (
        len(missing_cases_records) == 4
        and len(missing_fines_records) == 4
        and missing_cases_records == missing_fines_records
        and all(
            category == "K.T.C. Act"
            for _, category in missing_cases_records
        )
    )
    if not expected_ktc_missing_pattern:
        raise ValueError(
            "Expected exactly four matching null cases and fine_collected "
            "records, all belonging to K.T.C. Act. "
            f"Found {len(missing_cases_records)} null cases records and "
            f"{len(missing_fines_records)} null fine records."
        )

    print(
        "K.T.C. Act missing-value pattern confirmed: four matching records "
        "have null cases and fine_collected values."
    )

    # Category metrics must have numeric Spark types. Null metric values are
    # allowed and remain null; negative values are not allowed.
    category_metric_columns = ["cases", "fine_collected"]
    for column in category_metric_columns:
        data_type = category_df.schema[column].dataType
        if not isinstance(data_type, NumericType):
            raise ValueError(
                f"Category metric '{column}' must be numeric; "
                f"found {data_type.simpleString()}."
            )

        negative_count = category_df.filter(F.col(column) < 0).count()
        if negative_count > 0:
            raise ValueError(
                f"Category metric '{column}' contains "
                f"{negative_count} negative values."
            )

    annual_years = {
        row["year"]
        for row in annual_totals_df.select("year").distinct().collect()
    }
    if annual_years != EXPECTED_YEARS:
        raise ValueError(
            "Annual totals dataset must cover years 2011–2025. "
            f"Found: {sorted(annual_years)}."
        )

    if annual_totals_df.count() != EXPECTED_YEAR_COUNT:
        raise ValueError(
            "Expected 15 reported annual totals, but found "
            f"{annual_totals_df.count()}."
        )

    duplicate_annual_years = (
        annual_totals_df.groupBy("year")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    if duplicate_annual_years:
        raise ValueError(
            f"Found {duplicate_annual_years} duplicate annual-total years."
        )

    # Annual totals must be numeric, non-null, and non-negative.
    annual_metric_columns = [
        "total_cases_booked",
        "total_fine_collected",
    ]
    for column in annual_metric_columns:
        data_type = annual_totals_df.schema[column].dataType
        if not isinstance(data_type, NumericType):
            raise ValueError(
                f"Annual total '{column}' must be numeric; "
                f"found {data_type.simpleString()}."
            )

        null_count = annual_totals_df.filter(F.col(column).isNull()).count()
        if null_count > 0:
            raise ValueError(
                f"Annual total '{column}' contains {null_count} null values."
            )

        negative_count = annual_totals_df.filter(F.col(column) < 0).count()
        if negative_count > 0:
            raise ValueError(
                f"Annual total '{column}' contains "
                f"{negative_count} negative values."
            )

    print(
        "Input validation passed: required columns, exact category set, "
        "non-null years, valid metric types and values, 2011–2025 coverage, "
        "and unique year/category records."
    )


def build_yearly_statistics(annual_totals_df):
    """Calculate changes from the source-reported annual totals."""
    year_window = Window.orderBy("year")

    yearly = (
        annual_totals_df
        .withColumn(
            "previous_year",
            F.lag("year").over(year_window),
        )
        .withColumn(
            "previous_total_cases_booked",
            F.lag("total_cases_booked").over(year_window),
        )
        .withColumn(
            "previous_total_fine_collected",
            F.lag("total_fine_collected").over(year_window),
        )
        .withColumn(
            "cases_change",
            F.when(
                (F.col("previous_year") == F.col("year") - 1)
                & F.col("total_cases_booked").isNotNull()
                & F.col("previous_total_cases_booked").isNotNull(),
                F.col("total_cases_booked")
                - F.col("previous_total_cases_booked"),
            ),
        )
        .withColumn(
            "cases_change_percent",
            F.when(
                (F.col("previous_year") == F.col("year") - 1)
                & F.col("total_cases_booked").isNotNull()
                & F.col("previous_total_cases_booked").isNotNull()
                & (F.col("previous_total_cases_booked") > 0),
                (
                    (
                        F.col("total_cases_booked")
                        - F.col("previous_total_cases_booked")
                    )
                    / F.col("previous_total_cases_booked")
                )
                * 100,
            ),
        )
        .withColumn(
            "fine_change",
            F.when(
                (F.col("previous_year") == F.col("year") - 1)
                & F.col("total_fine_collected").isNotNull()
                & F.col("previous_total_fine_collected").isNotNull(),
                F.col("total_fine_collected")
                - F.col("previous_total_fine_collected"),
            ),
        )
        .withColumn(
            "fine_change_percent",
            F.when(
                (F.col("previous_year") == F.col("year") - 1)
                & F.col("total_fine_collected").isNotNull()
                & F.col("previous_total_fine_collected").isNotNull()
                & (F.col("previous_total_fine_collected") > 0),
                (
                    (
                        F.col("total_fine_collected")
                        - F.col("previous_total_fine_collected")
                    )
                    / F.col("previous_total_fine_collected")
                )
                * 100,
            ),
        )
        .select(
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
        )
        .orderBy("year")
    )

    return yearly


def build_category_yearly_statistics(category_df):
    """Keep the original yearly category values, including null values."""
    return (
        category_df
        .select(
            "year",
            "category",
            "cases",
            "fine_collected",
        )
        .orderBy("category", "year")
    )


def build_overall_category_rankings(category_df):
    """Rank categories by available reported cases and fines."""
    category_totals = (
        category_df.groupBy("category")
        .agg(
            F.sum("cases").alias("available_cases_total"),
            F.count("cases").alias("reported_case_years"),
            F.sum("fine_collected").alias("available_fine_total"),
            F.count("fine_collected").alias("reported_fine_years"),
        )
    )

    cases_window = Window.orderBy(
        F.desc("available_cases_total"),
        F.asc("category"),
    )
    cases_ranking = (
        category_totals
        .withColumn("rank", F.row_number().over(cases_window))
        .select(
            "rank",
            "category",
            "available_cases_total",
            F.col("reported_case_years").alias("reported_years"),
            F.lit(EXPECTED_YEAR_COUNT).alias("expected_years"),
        )
        .orderBy("rank")
    )

    fines_window = Window.orderBy(
        F.desc("available_fine_total"),
        F.asc("category"),
    )
    fines_ranking = (
        category_totals
        .withColumn("rank", F.row_number().over(fines_window))
        .select(
            "rank",
            "category",
            "available_fine_total",
            F.col("reported_fine_years").alias("reported_years"),
            F.lit(EXPECTED_YEAR_COUNT).alias("expected_years"),
        )
        .orderBy("rank")
    )

    return cases_ranking, fines_ranking


def build_category_trends(category_df):
    """Calculate changes only for valid values in consecutive years."""
    year_window = Window.partitionBy("category").orderBy("year")

    trends = (
        category_df
        .withColumn(
            "previous_year",
            F.lag("year").over(year_window),
        )
        .withColumn(
            "previous_cases",
            F.lag("cases").over(year_window),
        )
        .withColumn(
            "previous_fine_collected",
            F.lag("fine_collected").over(year_window),
        )
    )

    consecutive_years = F.col("previous_year") == F.col("year") - 1

    return (
        trends
        .withColumn(
            "cases_change",
            F.when(
                consecutive_years
                & F.col("cases").isNotNull()
                & F.col("previous_cases").isNotNull(),
                F.col("cases") - F.col("previous_cases"),
            ),
        )
        .withColumn(
            "fine_change",
            F.when(
                consecutive_years
                & F.col("fine_collected").isNotNull()
                & F.col("previous_fine_collected").isNotNull(),
                F.col("fine_collected") - F.col("previous_fine_collected"),
            ),
        )
        .select(
            "year",
            "category",
            "cases",
            "fine_collected",
            "previous_year",
            "previous_cases",
            "cases_change",
            "previous_fine_collected",
            "fine_change",
        )
        .orderBy("category", "year")
    )


def build_fine_per_case_statistics(category_df):
    """Calculate a rate only when cases and fine values support it."""
    return (
        category_df
        .withColumn(
            "fine_per_case",
            F.when(
                F.col("cases").isNotNull()
                & F.col("fine_collected").isNotNull()
                & (F.col("cases") > 0),
                F.col("fine_collected") / F.col("cases"),
            ),
        )
        .select(
            "year",
            "category",
            "cases",
            "fine_collected",
            "fine_per_case",
        )
        .orderBy("category", "year")
    )


def save_as_parquet(dataset, output_file):
    """Write a small Spark result through Pandas and PyArrow."""
    dataset.toPandas().to_parquet(
        output_file,
        engine="pyarrow",
        index=False,
    )
    print("Saved:", output_file)


def print_interpretations(yearly, cases_ranking, fines_ranking):
    """Print concise summaries based on the computed outputs."""
    print("\nYEARLY REPORTED TOTALS AND CHANGES")
    for row in yearly.orderBy("year").collect():
        cases_change = (
            "not available"
            if row["cases_change"] is None
            else f"{row['cases_change']:,}"
        )
        fine_change = (
            "not available"
            if row["fine_change"] is None
            else f"{row['fine_change']:,}"
        )
        print(
            f"{row['year']}: source-reported cases "
            f"{row['total_cases_booked']:,}, cases change {cases_change}; "
            f"source-reported fine {row['total_fine_collected']:,}, "
            f"fine change {fine_change}."
        )

    top_cases = cases_ranking.first()
    if top_cases is not None:
        print(
            f"Highest available category total for cases: "
            f"{top_cases['category']} with "
            f"{top_cases['available_cases_total']:,} cases across "
            f"{top_cases['reported_years']} reported years."
        )

    top_fines = fines_ranking.first()
    if top_fines is not None:
        print(
            f"Highest available category total for fines: "
            f"{top_fines['category']} with "
            f"{top_fines['available_fine_total']:,} collected across "
            f"{top_fines['reported_years']} reported years."
        )

    print(
        "Category rankings use available reported values. Missing K.T.C. Act "
        "values remain null and are not counted as zero."
    )
    print(
        "Yearly totals come from the reported annual totals dataset; "
        "they are not recalculated from category values."
    )


def main():
    analytics_dir.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("UrbanPulseTrafficCasesFinesAnalytics")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        # Read the cleaned category and reported annual totals datasets.
        category_df = spark.read.parquet(str(category_input_file))
        annual_totals_df = spark.read.parquet(str(annual_totals_input_file))

        print("\nTRAFFIC CASES AND FINES ANALYTICS")
        print("Category input:", category_input_file)
        print("Annual totals input:", annual_totals_input_file)
        print("Category columns:", category_df.columns)
        print("Annual totals columns:", annual_totals_df.columns)

        validate_inputs(category_df, annual_totals_df)

        yearly_statistics = build_yearly_statistics(annual_totals_df)
        category_yearly_statistics = build_category_yearly_statistics(
            category_df
        )
        cases_ranking, fines_ranking = build_overall_category_rankings(
            category_df
        )
        category_trends = build_category_trends(category_df)
        fine_per_case = build_fine_per_case_statistics(category_df)

        print("\nYEARLY TRAFFIC CASES AND FINES STATISTICS")
        yearly_statistics.show(20, truncate=False)

        print("\nCATEGORY-WISE YEARLY STATISTICS")
        category_yearly_statistics.show(100, truncate=False)

        print("\nOVERALL CATEGORY RANKING BY AVAILABLE CASES")
        cases_ranking.show(truncate=False)

        print("\nOVERALL CATEGORY RANKING BY AVAILABLE FINES")
        fines_ranking.show(truncate=False)

        print("\nCATEGORY YEAR-OVER-YEAR TRENDS")
        category_trends.show(100, truncate=False)

        print("\nFINE PER RECORDED CASE")
        fine_per_case.show(100, truncate=False)

        outputs = {
            "traffic_cases_fines_yearly_statistics": yearly_statistics,
            "traffic_cases_fines_category_yearly_statistics":
                category_yearly_statistics,
            "traffic_cases_fines_category_cases_ranking": cases_ranking,
            "traffic_cases_fines_category_fines_ranking": fines_ranking,
            "traffic_cases_fines_category_trends": category_trends,
            "traffic_cases_fines_fine_per_case": fine_per_case,
        }

        print("\nSAVING ANALYTICAL OUTPUTS")
        for name, dataset in outputs.items():
            save_as_parquet(dataset, analytics_dir / f"{name}.parquet")

        print_interpretations(
            yearly_statistics,
            cases_ranking,
            fines_ranking,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
