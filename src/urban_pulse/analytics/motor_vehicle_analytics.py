from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import Window
from pyspark.sql import functions as F


# Find the project directory so this script can run from different folders.
project_dir = Path(__file__).resolve().parents[3]
input_file = (
    project_dir
    / "data"
    / "processed"
    / "violations"
    / "motor_vehicle_violations.parquet"
)
output_dir = project_dir / "data" / "processed" / "analytics" / "violations"

EXPECTED_CATEGORY_COUNT = 40
FIRST_YEAR = 2018
LAST_YEAR = 2025


def build_yearly_statistics(df):
    """Summarize reported and missing categories, preserving partial totals."""
    yearly = (
        df.groupBy("year")
        .agg(
            F.sum("cases").alias("available_cases"),
            F.count("cases").alias("reported_offence_categories"),
            F.sum(
                F.when(F.col("cases").isNull(), 1).otherwise(0)
            ).alias("missing_offence_categories"),
        )
        .withColumn(
            "total_expected_categories",
            F.lit(EXPECTED_CATEGORY_COUNT),
        )
        .withColumn(
            "annual_total_status",
            F.when(
                (F.col("reported_offence_categories") == EXPECTED_CATEGORY_COUNT)
                & (F.col("missing_offence_categories") == 0),
                F.lit("complete"),
            ).otherwise(F.lit("incomplete_partial_total")),
        )
        .orderBy("year")
    )
    return yearly


def build_yearly_top_10(df):
    """Rank each year's categories by recorded cases; null values are excluded."""
    year_window = Window.partitionBy("year").orderBy(
        F.desc("cases"),
        F.asc("offence_type"),
    )

    return (
        df.filter(F.col("cases").isNotNull())
        .withColumn("rank", F.row_number().over(year_window))
        .filter(F.col("rank") <= 10)
        .orderBy("year", "rank")
    )


def build_overall_top_10(df):
    """Rank categories by their sum of available case values across years."""
    return (
        df.groupBy("offence_type")
        .agg(
            F.sum("cases").alias("recorded_cases"),
            F.count("cases").alias("years_with_reported_values"),
        )
        .filter(F.col("recorded_cases").isNotNull())
        .orderBy(F.desc("recorded_cases"), F.asc("offence_type"))
        .limit(10)
    )


def build_category_trends(df):
    """Keep annual values and calculate changes only when both values exist."""
    year_window = Window.partitionBy("offence_type").orderBy("year")

    trends = (
        df.withColumn(
            "previous_year",
            F.lag("year").over(year_window),
        )
        .withColumn(
            "previous_year_cases",
            F.lag("cases").over(year_window),
        )
    )

    return (
        trends.withColumn(
            "change_from_previous_year",
            F.when(
                F.col("cases").isNotNull()
                & F.col("previous_year_cases").isNotNull(),
                F.col("cases") - F.col("previous_year_cases"),
            ),
        )
        .select(
            "offence_type",
            "year",
            "previous_year",
            "cases",
            "previous_year_cases",
            "change_from_previous_year",
        )
        .orderBy("offence_type", "year")
    )


def build_endpoint_changes(df):
    """Compare 2018 and 2025 only where both case counts are available."""
    endpoints = (
        df.groupBy("offence_type")
        .agg(
            F.max(
                F.when(F.col("year") == FIRST_YEAR, F.col("cases"))
            ).alias("cases_2018"),
            F.max(
                F.when(F.col("year") == LAST_YEAR, F.col("cases"))
            ).alias("cases_2025"),
        )
        .filter(
            F.col("cases_2018").isNotNull()
            & F.col("cases_2025").isNotNull()
        )
        .withColumn(
            "change_2018_to_2025",
            F.col("cases_2025") - F.col("cases_2018"),
        )
    )

    return endpoints.orderBy(
        F.desc("change_2018_to_2025"),
        F.asc("offence_type"),
    )


def save_as_parquet(dataset, output_file):
    """Use Pandas and PyArrow to write these small Spark aggregates."""
    dataset.toPandas().to_parquet(
        output_file,
        engine="pyarrow",
        index=False,
    )
    print("Saved:", output_file)


def print_interpretations(yearly, overall_top_10, endpoint_changes):
    """Describe the output using only values computed from the dataset."""
    print("\nINTERPRETATIONS")

    for row in yearly.orderBy("year").collect():
        total = (
            "unavailable"
            if row["available_cases"] is None
            else f"{row['available_cases']:,}"
        )
        status = (
            "complete annual total"
            if row["annual_total_status"] == "complete"
            else "partial total; some category values are missing"
        )
        print(
            f"{row['year']}: {total} available recorded cases across "
            f"{row['reported_offence_categories']} reported categories; "
            f"{row['missing_offence_categories']} categories are missing. "
            f"Status: {status}."
        )

    top_category = overall_top_10.first()
    if top_category is not None:
        print(
            f"Across available values, {top_category['offence_type']} has the "
            f"largest recorded total ({top_category['recorded_cases']:,}) "
            f"among the categories shown in the overall ranking."
        )

    largest_increase = endpoint_changes.orderBy(
        F.desc("change_2018_to_2025"),
        F.asc("offence_type"),
    ).first()
    largest_decrease = endpoint_changes.orderBy(
        F.asc("change_2018_to_2025"),
        F.asc("offence_type"),
    ).first()

    if largest_increase is not None:
        print(
            f"Among categories with values in both endpoint years, "
            f"{largest_increase['offence_type']} has the largest recorded "
            f"increase: {largest_increase['change_2018_to_2025']:,} "
            f"from 2018 to 2025."
        )

    if largest_decrease is not None:
        print(
            f"Among categories with values in both endpoint years, "
            f"{largest_decrease['offence_type']} has the largest recorded "
            f"decrease: {largest_decrease['change_2018_to_2025']:,} "
            f"from 2018 to 2025."
        )

    print(
        "These are recorded counts. A missing value is not treated as zero "
        "or as evidence of fewer violations."
    )


def main():
    output_dir.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("UrbanPulseMotorVehicleAnalytics")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        # Read the cleaned dataset without changing its source values.
        df = spark.read.parquet(str(input_file))

        # Confirm the actual number of distinct, non-null offence categories.
        actual_category_count = (
            df.filter(F.col("offence_type").isNotNull())
            .select("offence_type")
            .distinct()
            .count()
        )

        if actual_category_count != EXPECTED_CATEGORY_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_CATEGORY_COUNT} offence categories, "
                f"but found {actual_category_count}."
            )

        print(
            f"Category count confirmed: "
            f"{actual_category_count} distinct offence categories."
        )

        print("\nMOTOR VEHICLE VIOLATION ANALYTICS")
        print("Input:", input_file)
        print("Input records:", df.count())
        print("Input columns:", df.columns)

        yearly_statistics = build_yearly_statistics(df)
        yearly_top_10 = build_yearly_top_10(df)
        overall_top_10 = build_overall_top_10(df)
        category_trends = build_category_trends(df)
        endpoint_changes = build_endpoint_changes(df)

        print("\nYEAR-WISE OFFENCE STATISTICS")
        yearly_statistics.show(truncate=False)

        print("\nTOP 10 OFFENCE CATEGORIES BY YEAR")
        yearly_top_10.show(100, truncate=False)

        print("\nOVERALL TOP 10 OFFENCE CATEGORIES")
        overall_top_10.show(truncate=False)

        print("\nOFFENCE CATEGORY TRENDS")
        category_trends.show(100, truncate=False)

        print("\nLARGEST RECORDED INCREASES, 2018 TO 2025")
        endpoint_changes.orderBy(
            F.desc("change_2018_to_2025"),
            F.asc("offence_type"),
        ).show(10, truncate=False)

        print("\nLARGEST RECORDED DECREASES, 2018 TO 2025")
        endpoint_changes.orderBy(
            F.asc("change_2018_to_2025"),
            F.asc("offence_type"),
        ).show(10, truncate=False)

        # Each output is a small aggregate, so write via Pandas + PyArrow.
        outputs = {
            "yearly_offence_statistics": yearly_statistics,
            "yearly_top_10_offences": yearly_top_10,
            "overall_top_10_offences": overall_top_10,
            "offence_category_trends": category_trends,
            "offence_endpoint_changes": endpoint_changes,
        }

        print("\nSAVING ANALYTICAL OUTPUTS")
        for name, dataset in outputs.items():
            save_as_parquet(dataset, output_dir / f"{name}.parquet")

        print_interpretations(
            yearly_statistics,
            overall_top_10,
            endpoint_changes,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
