
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw/road_crashes")

# Each file has slightly different column names.
datasets = {
    "crashes_2023.csv": {
        "fatal": "2023 - Fatal Cases",
        "non_fatal": "2023 - Non-Fatal",
        "total": "2023 - Total Cases"
    },
    "crashes_2024.csv": {
        "fatal": "2024-Fatal crashes",
        "non_fatal": "2024-Non Fatal",
        "total": "2024-Total crashes"
    },
    "crashes_2025.csv": {
        "fatal": "2025-Fatal crashes",
        "non_fatal": "2025-Non Fatal",
        "total": "2025-Total crashes"
    }
}

for filename, columns in datasets.items():

    print("\n" + "=" * 65)
    print("VALIDATING:", filename)
    print("=" * 65)

    df = pd.read_csv(DATA_DIR / filename)

    # Identify summary rows such as East Total and Grand Total.
    is_summary = (
        df["Station"]
        .astype("string")
        .str.contains(r"\btotal\b", case=False, na=False)
    )

    stations = df.loc[~is_summary].copy()
    summaries = df.loc[is_summary].copy()

    print("\n1. ROW COUNTS")
    print("Total rows:", len(df))
    print("Station rows:", len(stations))
    print("Summary rows:", len(summaries))

    # Check whether required numeric columns contain missing values.
    numeric_columns = [
        columns["fatal"],
        columns["non_fatal"],
        columns["total"]
    ]

    print("\n2. MISSING VALUES")
    print(stations[numeric_columns].isnull().sum())

    # Check whether fatal + non-fatal = total crashes.
    calculated_total = (
        stations[columns["fatal"]]
        + stations[columns["non_fatal"]]
    )

    mismatch = stations[
        calculated_total != stations[columns["total"]]
    ]

    print("\n3. CRASH TOTAL VALIDATION")
    if mismatch.empty:
        print("PASS: All station totals match.")
    else:
        print("WARNING: Found mismatched station totals.")
        print(
            mismatch[
                ["Station"] + numeric_columns
            ].to_string(index=False)
        )

    # Check repeated station names.
    duplicate_stations = stations[
        stations["Station"].duplicated(keep=False)
    ]

    print("\n4. DUPLICATE STATION NAMES")
    if duplicate_stations.empty:
        print("PASS: No repeated station names.")
    else:
        print(duplicate_stations["Station"].to_list())

    # Check station sums against the published grand total.
    grand_total = summaries[
        summaries["Station"].str.contains(
            "Grand Total", case=False, na=False
        )
    ]

    print("\n5. STATION SUM VS GRAND TOTAL")

    if len(grand_total) == 1:
        for metric in numeric_columns:
            station_sum = stations[metric].sum()
            published_total = grand_total.iloc[0][metric]

            print(f"\n{metric}")
            print("Station sum:", station_sum)
            print("Published total:", published_total)

            if station_sum == published_total:
                print("PASS")
            else:
                print("WARNING: Totals do not match.")

    else:
        print("WARNING: Expected exactly one Grand Total row.")

    # Display the published summary rows separately.
    print("\n5. SUMMARY ROWS")
    if summaries.empty:
        print("No summary rows found.")
    else:
        print(summaries.to_string(index=False))
