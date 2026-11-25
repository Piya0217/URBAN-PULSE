from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import Window
from pyspark.sql import functions as F


# Resolve paths from this file so it can be run from different directories.
project_dir = Path(__file__).resolve().parents[3]
input_file = (
    project_dir
    / "data"
    / "processed"
    / "violations"
    / "drink_drive_violations.parquet"
)
output_dir = project_dir / "data" / "processed" / "analytics" / "violations"

EXPECTED_YEARS = {2016, 2017, 2018}
EXPECTED_MONTH_COUNT = 12
EXPECTED_RECORD_COUNT = 36

# Map full month names to calendar month numbers.
MONTH_NUMBERS = {
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


def validate_input(df):
    """Check that the input has the expected fields and month-year records."""
    required_columns = {"month", "year", "cases"}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise ValueError(
            f"Input dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    record_count = df.count()
    if record_count != EXPECTED_RECORD_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_RECORD_COUNT} month-year records, "
            f"but found {record_count}."
        )

    found_years = {
        row["year"]
        for row in df.select("year").distinct().collect()
    }
    if found_years != EXPECTED_YEARS:
        raise ValueError(
            f"Expected years {sorted(EXPECTED_YEARS)}, "
            f"but found {sorted(found_years, key=str)}."
        )

    invalid_month_count = df.filter(
        F.col("month").isNull()
        | ~F.col("month").isin(list(MONTH_NUMBERS))
    ).count()

    if invalid_month_count > 0:
        raise ValueError(
            f"Found {invalid_month_count} rows with missing or invalid "
            "month names."
        )

    duplicate_month_year_count = (
        df.groupBy("month", "year")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    if duplicate_month_year_count > 0:
        raise ValueError(
            f"Found {duplicate_month_year_count} duplicate month-year groups."
        )

    print(
        "Input checks passed: 36 records, expected years, valid month names, "
        "and no duplicate month-year records."
    )


def build_yearly_statistics(df):
    """Summarize available cases and monthly completeness for each year."""
    yearly = (
        df.groupBy("year")
        .agg(
            # Spark sum ignores null values and returns the available total.
            F.sum("cases").alias("available_cases"),
            # count(cases) counts only months with reported case values.
            F.count("cases").alias("reported_months"),
            # Total rows minus reported values gives the number of missing months.
            (F.count("*") - F.count("cases")).alias("missing_months"),
        )
        .withColumn(
            "total_expected_months",
            F.lit(EXPECTED_MONTH_COUNT),
        )
        .withColumn(
            "annual_total_status",
            F.when(
                (F.col("reported_months") == EXPECTED_MONTH_COUNT)
                & (F.col("missing_months") == 0),
                F.lit("COMPLETE"),
            ).otherwise(F.lit("INCOMPLETE")),
        )
        .select(
            "year",
            "available_cases",
            "reported_months",
            "missing_months",
            "total_expected_months",
            "annual_total_status",
        )
        .orderBy("year")
    )

    return yearly


def build_monthly_statistics(df):
    """Add month numbers and compare each month with the prior calendar year."""
    month_lookup = F.create_map(
        *[
            value
            for month, number in MONTH_NUMBERS.items()
            for value in (F.lit(month), F.lit(number))
        ]
    )

    # Partition by month so January is compared with January, February with
    # February, and so on. The window orders each month's records by year.
    month_window = Window.partitionBy("month").orderBy("year")

    monthly = (
        df.withColumn("month_number", month_lookup[F.col("month")])
        .withColumn(
            "previous_year",
            F.lag("year").over(month_window),
        )
        .withColumn(
            "previous_year_cases",
            F.lag("cases").over(month_window),
        )
    )

    return (
        monthly.withColumn(
            "change_from_previous_year",
            F.when(
                (F.col("previous_year") == F.col("year") - 1)
                & F.col("cases").isNotNull()
                & F.col("previous_year_cases").isNotNull(),
                F.col("cases") - F.col("previous_year_cases"),
            ),
        )
        .select(
            "month",
            "month_number",
            "year",
            "cases",
            "previous_year",
            "previous_year_cases",
            "change_from_previous_year",
        )
        .orderBy("month_number", "year")
    )


def build_yearly_comparison(yearly_statistics):
    """Label complete and partial totals to guide valid comparisons."""
    return (
        yearly_statistics.withColumn(
            "comparison_guidance",
            F.when(
                F.col("annual_total_status") == "COMPLETE",
                F.lit("Complete annual total"),
            ).otherwise(
                F.lit(
                    "Partial annual total; not directly comparable "
                    "to complete annual totals"
                )
            ),
        )
        .select(
            "year",
            "available_cases",
            "reported_months",
            "missing_months",
            "total_expected_months",
            "annual_total_status",
            "comparison_guidance",
        )
        .orderBy("year")
    )


def save_as_parquet(dataset, output_file):
    """Write a small Spark result through Pandas and PyArrow."""
    dataset.toPandas().to_parquet(
        output_file,
        engine="pyarrow",
        index=False,
    )
    print("Saved:", output_file)


def print_interpretations(yearly_statistics):
    """Explain which annual values are complete and which are partial."""
    print("\nYEARLY TOTAL INTERPRETATION")

    for row in yearly_statistics.orderBy("year").collect():
        total = (
            "unavailable"
            if row["available_cases"] is None
            else f"{row['available_cases']:,}"
        )

        if row["annual_total_status"] == "COMPLETE":
            print(
                f"{row['year']}: {total} cases across all "
                f"{row['reported_months']} reported months; complete annual total."
            )
        else:
            print(
                f"{row['year']}: {total} cases across "
                f"{row['reported_months']} reported months; this is a partial "
                "annual total and is not directly comparable to complete "
                "annual totals."
            )

    print(
        "Monthly changes are calculated only for the same month in consecutive "
        "years when both case values are available. Missing values remain null."
    )


def main():
    output_dir.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("UrbanPulseDrinkDriveAnalytics")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        # Read the cleaned Parquet dataset without changing its values.
        df = spark.read.parquet(str(input_file))

        print("\nDRINK AND DRIVE ANALYTICS")
        print("Input:", input_file)
        print("Input columns:", df.columns)

        validate_input(df)

        yearly_statistics = build_yearly_statistics(df)
        monthly_statistics = build_monthly_statistics(df)
        yearly_comparison = build_yearly_comparison(yearly_statistics)

        print("\nYEARLY DRINK AND DRIVE STATISTICS")
        yearly_statistics.show(truncate=False)

        print("\nMONTHLY DRINK AND DRIVE STATISTICS")
        monthly_statistics.show(36, truncate=False)

        print("\nYEARLY COMPARISON")
        yearly_comparison.show(truncate=False)

        outputs = {
            "yearly_drink_drive_statistics": yearly_statistics,
            "monthly_drink_drive_statistics": monthly_statistics,
            "drink_drive_yearly_comparison": yearly_comparison,
        }

        print("\nSAVING ANALYTICAL OUTPUTS")
        for name, dataset in outputs.items():
            save_as_parquet(dataset, output_dir / f"{name}.parquet")

        print_interpretations(yearly_statistics)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
