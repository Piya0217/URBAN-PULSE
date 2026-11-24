from pathlib import Path

import pandas as pd


# Resolve the project directory from this script's location.
project_dir = Path(__file__).resolve().parents[3]
input_file = (
    project_dir
    / "data"
    / "raw"
    / "traffic_cases_and_fines.csv"
)
output_dir = project_dir / "data" / "processed" / "violations"

# These are the case and fine columns for each enforcement category.
category_columns = [
    ("M.V. Act", "M.V.Act Cases", "M.V.Act Fine"),
    ("K.P. Act", "K.P.Act Cases", "K.P.Act Fine"),
    ("Towing", "Towing Cases", "Towing Charges"),
    ("K.T.C. Act", "K.T.C Act Cases", "K.T.C Act Fine"),
    ("Automation", "Automation cases", "Automation Fine"),
]

annual_total_columns = [
    "Total Cases Booked",
    "Total Fine Collected",
]

expected_years = list(range(2011, 2026))
expected_record_count = 15


def validate_source(df):
    """Check required columns, record count, and year coverage."""
    required_columns = (
        ["YEAR"]
        + annual_total_columns
        + [
            column
            for _, cases_column, fine_column in category_columns
            for column in (cases_column, fine_column)
        ]
    )
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Source CSV is missing required columns: {missing_columns}"
        )

    if len(df) != expected_record_count:
        raise ValueError(
            f"Expected {expected_record_count} source records, "
            f"but found {len(df)}."
        )

    numeric_years = pd.to_numeric(df["YEAR"], errors="coerce")

    if numeric_years.isna().any() or not numeric_years.mod(1).eq(0).all():
        raise ValueError("The YEAR column contains missing or invalid years.")

    found_years = numeric_years.astype(int).tolist()

    if len(set(found_years)) != len(found_years):
        raise ValueError("The source contains duplicate years.")

    if sorted(found_years) != expected_years:
        raise ValueError(
            f"Expected years 2011–2025, but found {sorted(found_years)}."
        )

    print(
        "Source validation passed: 15 records with one record for each "
        "year from 2011 through 2025."
    )

    return numeric_years.astype(int)


def convert_numeric_columns(df, columns):
    """Convert numeric fields while retaining genuine missing values."""
    for column in columns:
        converted = pd.to_numeric(df[column], errors="coerce")

        # Do not silently turn unexpected text into a missing value.
        invalid_values = df[column].notna() & converted.isna()
        if invalid_values.any():
            raise ValueError(
                f"Column '{column}' contains values that are not numeric."
            )

        # Case counts and collected fines cannot be negative.
        negative_values = converted.dropna() < 0
        if negative_values.any():
            raise ValueError(
                f"Column '{column}' contains negative values."
            )

        df[column] = converted


def build_category_dataset(df, years):
    """Create one long-format row per year and enforcement category."""
    category_frames = []

    for category, cases_column, fine_column in category_columns:
        category_frame = pd.DataFrame(
            {
                "year": years,
                "category": category,
                "cases": df[cases_column],
                "fine_collected": df[fine_column],
            }
        )
        category_frames.append(category_frame)

    long_df = pd.concat(category_frames, ignore_index=True)

    # Convert values to numbers. Missing K.T.C. Act values remain null.
    value_columns = ["cases", "fine_collected"]
    for column in value_columns:
        long_df[column] = pd.to_numeric(long_df[column], errors="coerce")

    return (
        long_df[
            ["year", "category", "cases", "fine_collected"]
        ]
        .sort_values(["year", "category"])
        .reset_index(drop=True)
    )


def build_annual_totals_dataset(df, years):
    """Keep the annual totals reported in the source CSV."""
    annual_totals = df[annual_total_columns].copy()
    annual_totals.insert(0, "year", years)

    annual_totals = annual_totals.rename(
        columns={
            "Total Cases Booked": "total_cases_booked",
            "Total Fine Collected": "total_fine_collected",
        }
    )

    # Convert the reported totals to numeric values without recalculating them.
    convert_numeric_columns(
        annual_totals,
        ["total_cases_booked", "total_fine_collected"],
    )

    return annual_totals[
        ["year", "total_cases_booked", "total_fine_collected"]
    ]


def main():
    print("\nCLEANING TRAFFIC CASES AND FINES DATA")
    print("Input:", input_file)

    # Read the source CSV without changing the original file.
    source_df = pd.read_csv(input_file)
    print("Source shape:", source_df.shape)

    years = validate_source(source_df)

    # Check and convert category values while preserving any nulls.
    category_value_columns = [
        column
        for _, cases_column, fine_column in category_columns
        for column in (cases_column, fine_column)
    ]
    convert_numeric_columns(source_df, category_value_columns)

    cleaned_df = build_category_dataset(source_df, years)

    # Confirm the source's expected missing K.T.C. Act values were retained.
    ktc_df = cleaned_df[cleaned_df["category"] == "K.T.C. Act"]
    if ktc_df["cases"].isna().sum() != 4:
        raise ValueError("Expected exactly 4 missing K.T.C. Act case values.")
    if ktc_df["fine_collected"].isna().sum() != 4:
        raise ValueError("Expected exactly 4 missing K.T.C. Act fine values.")

    annual_totals_df = build_annual_totals_dataset(source_df, years)

    if len(cleaned_df) != expected_record_count * len(category_columns):
        raise ValueError(
            "Unexpected number of rows in the long-format category dataset: "
            f"{len(cleaned_df)}."
        )

    # Create the output folder only after the source has passed validation.
    output_dir.mkdir(parents=True, exist_ok=True)

    category_output_file = output_dir / "traffic_cases_fines_long.parquet"
    annual_totals_output_file = (
        output_dir / "traffic_cases_fines_annual_totals.parquet"
    )

    # Use Pandas and PyArrow for Windows-compatible Parquet writing.
    cleaned_df.to_parquet(
        category_output_file,
        engine="pyarrow",
        index=False,
    )
    annual_totals_df.to_parquet(
        annual_totals_output_file,
        engine="pyarrow",
        index=False,
    )

    print("\nLONG-FORMAT CATEGORY DATA")
    print("Shape:", cleaned_df.shape)
    print("Columns:", list(cleaned_df.columns))
    print("Categories:", sorted(cleaned_df["category"].unique()))
    print("Missing values:")
    print(cleaned_df.isna().sum())
    print("Saved:", category_output_file)

    print("\nREPORTED ANNUAL TOTALS")
    print("Shape:", annual_totals_df.shape)
    print("Columns:", list(annual_totals_df.columns))
    print("Missing values:")
    print(annual_totals_df.isna().sum())
    print("Saved:", annual_totals_output_file)

    print("\nCLEANING COMPLETED")


if __name__ == "__main__":
    main()
