
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 1. Start Spark
spark = (
    SparkSession.builder
    .appName("UrbanPulseCrashAnalysis")
    .master("local[*]")
    .getOrCreate()
)

print("\nSPARK VERSION:", spark.version)

# 2. Read the cleaned CSV dataset
df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/processed/crash_records_2023_2025.csv")
)

# 3. Display the dataset structure
print("\n1. DATASET SCHEMA")
df.printSchema()

# 4. Count records
print("\n2. TOTAL RECORDS")
print("Records:", df.count())

# 5. Display sample records
print("\n3. SAMPLE DATA")
df.show(10, truncate=False)

# 6. Calculate yearly crash statistics
print("\n4. YEAR-WISE CRASH STATISTICS")

yearly_summary = (
    df.groupBy("year")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes"),
        F.sum("non_fatal_crashes").alias("non_fatal_crashes"),
        F.sum("total_crashes").alias("total_crashes")
    )
    .orderBy("year")
)

yearly_summary.show()

# 7. Zone-wise crash analysis
print("\n5. ZONE-WISE CRASH STATISTICS")

zone_summary = (
    df.groupBy("year", "zone")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes"),
        F.sum("non_fatal_crashes").alias("non_fatal_crashes"),
        F.sum("total_crashes").alias("total_crashes")
    )
    .orderBy("year", F.desc("total_crashes"))
)

zone_summary.show(50, truncate=False)


# 8. Top 10 stations by total crashes
print("\n6. TOP 10 STATIONS BY TOTAL CRASHES")

station_summary = (
    df.groupBy("year", "station", "zone")
    .agg(
        F.sum("total_crashes").alias("total_crashes")
    )
)

top_stations = (
    station_summary
    .orderBy(F.desc("total_crashes"))
    .limit(10)
)

top_stations.show(truncate=False)


# 9. Fatal crash percentage by zone and year
print("\n7. FATAL CRASH PERCENTAGE BY ZONE")

zone_severity = (
    df.groupBy("year", "zone")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes"),
        F.sum("total_crashes").alias("total_crashes")
    )
    .withColumn(
        "fatal_crash_percentage",
        F.round(
            (F.col("fatal_crashes") / F.col("total_crashes")) * 100,
            2
        )
    )
    .orderBy("year", F.desc("fatal_crash_percentage"))
)

zone_severity.show(50, truncate=False)


# 10. Top 10 stations by fatal crashes
print("\n8. TOP 10 STATIONS BY FATAL CRASHES")

fatal_station_summary = (
    df.groupBy("year", "station", "zone")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes")
    )
    .orderBy(F.desc("fatal_crashes"))
    .limit(10)
)

fatal_station_summary.show(truncate=False)


# 11. Overall fatal crash percentage by year
print("\n9. YEAR-WISE FATAL CRASH PERCENTAGE")

year_severity = (
    df.groupBy("year")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes"),
        F.sum("total_crashes").alias("total_crashes")
    )
    .withColumn(
        "fatal_crash_percentage",
        F.round(
            (F.col("fatal_crashes") / F.col("total_crashes")) * 100,
            2
        )
    )
    .orderBy("year")
)

year_severity.show()

# 12. Station name consistency audit
print("\n10. STATION NAME CONSISTENCY AUDIT")

from pyspark.sql import functions as F

station_audit = (
    df.withColumn(
        "normalized_station",
        F.lower(
            F.regexp_replace(
                F.trim(F.col("station")),
                r"[^a-zA-Z0-9]",
                ""
            )
        )
    )
    .groupBy("normalized_station")
    .agg(
        F.countDistinct("station").alias("name_variants"),
        F.collect_set("station").alias("original_names"),
        F.countDistinct("year").alias("years_present")
    )
    .filter(F.col("name_variants") > 1)
    .orderBy(F.desc("name_variants"))
)

station_audit.show(100, truncate=False)


# 13. Station coverage by year
print("\n11. STATION COVERAGE BY YEAR")

df.groupBy("year").agg(
    F.countDistinct("station").alias("unique_stations"),
    F.count("*").alias("records")
).orderBy("year").show()


# 14. Display station names by year
print("\n12. ALL STATION NAMES BY YEAR")

station_names = (
    df.select("year", "station")
    .distinct()
    .orderBy("year", "station")
)

for year in [2023, 2024, 2025]:
    print(f"\nSTATIONS IN {year}")

    station_names.filter(
        F.col("year") == year
    ).select("station").show(100, truncate=False)


# 15. Historical crash hotspot analysis
print("\n13. HISTORICAL CRASH HOTSPOT ANALYSIS")

# Identify stations present in all three years
consistent_stations = (
    df.groupBy("station", "zone")
    .agg(
        F.countDistinct("year").alias("years_present")
    )
    .filter(F.col("years_present") == 3)
    .select("station", "zone")
)

# Keep records only for stations present in all years
consistent_df = df.join(
    consistent_stations,
    on=["station", "zone"],
    how="inner"
)

print("\nSTATIONS PRESENT IN ALL THREE YEARS:")
print(consistent_stations.count())


# Calculate historical crash statistics
historical_hotspots = (
    consistent_df.groupBy("station", "zone")
    .agg(
        F.sum("total_crashes").alias("three_year_crashes"),
        F.sum("fatal_crashes").alias("three_year_fatal_crashes"),
        F.avg("total_crashes").alias("average_annual_crashes")
    )
    .withColumn(
        "fatal_crash_percentage",
        F.round(
            F.col("three_year_fatal_crashes")
            / F.col("three_year_crashes") * 100,
            2
        )
    )
    .orderBy(F.desc("three_year_crashes"))
)

print("\nTOP 15 HISTORICAL CRASH HOTSPOTS:")

historical_hotspots.show(15, truncate=False)


# 16. Rank stations by fatal crashes
print("\n14. TOP 10 HISTORICAL FATAL CRASH HOTSPOTS:")

historical_hotspots.orderBy(
    F.desc("three_year_fatal_crashes")
).show(10, truncate=False)

# 17. STATION-WISE CRASH TREND ANALYSIS
print("\n15. STATION-WISE CRASH TREND ANALYSIS")

station_trends = (
    consistent_df
    .groupBy("station", "zone")
    .pivot("year", [2023, 2024, 2025])
    .agg(F.sum("total_crashes"))
    .withColumn(
        "change_2023_to_2025",
        F.col("2025") - F.col("2023")
    )
    .withColumn(
        "percentage_change",
        F.round(
            (F.col("2025") - F.col("2023"))
            / F.col("2023") * 100,
            2
        )
    )
)

print("\nTOP 10 STATIONS WITH INCREASING CRASH COUNTS:")

station_trends.orderBy(
    F.desc("change_2023_to_2025")
).show(10, truncate=False)


print("\nTOP 10 STATIONS WITH DECREASING CRASH COUNTS:")

station_trends.orderBy(
    F.asc("change_2023_to_2025")
).show(10, truncate=False)
# 18. SAVE ANALYTICAL DATASETS
print("\n16. SAVING ANALYTICAL DATASETS")

output_path = "data/processed/analytics/crashes"

# Year-wise statistics
yearly_crash_statistics = (
    df.groupBy("year")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes"),
        F.sum("non_fatal_crashes").alias("non_fatal_crashes"),
        F.sum("total_crashes").alias("total_crashes")
    )
    .orderBy("year")
)

# Zone-wise statistics
zone_crash_statistics = (
    df.groupBy("year", "zone")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes"),
        F.sum("non_fatal_crashes").alias("non_fatal_crashes"),
        F.sum("total_crashes").alias("total_crashes")
    )
)

# Station-wise annual statistics
station_year_statistics = (
    df.groupBy("year", "station", "zone")
    .agg(
        F.sum("fatal_crashes").alias("fatal_crashes"),
        F.sum("non_fatal_crashes").alias("non_fatal_crashes"),
        F.sum("total_crashes").alias("total_crashes")
    )
)

# Save all five datasets
datasets = {
    "yearly_crash_statistics": yearly_crash_statistics,
    "zone_crash_statistics": zone_crash_statistics,
    "station_year_statistics": station_year_statistics,
    "historical_hotspots": historical_hotspots,
    "station_crash_trends": station_trends
}

from pathlib import Path

# Create output directory
output_dir = Path("data/processed/analytics/crashes")
output_dir.mkdir(parents=True, exist_ok=True)

# Save Spark results using Pandas + PyArrow
for name, dataset in datasets.items():

    output_file = output_dir / f"{name}.parquet"

    dataset.toPandas().to_parquet(
        output_file,
        engine="pyarrow",
        index=False
    )

    print(f"Saved: {output_file}")

print("\nALL ANALYTICAL DATASETS SAVED SUCCESSFULLY")
# 7. Stop Spark
spark.stop()
