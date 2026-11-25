
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

ANALYTICS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analytics"
)


def read_analytics_file(filename: str) -> list:
    file_path = ANALYTICS_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Analytics file not found: {file_path}"
        )

    df = pd.read_parquet(file_path)

    # Convert values to JSON-compatible Python types.
    # Missing values become JSON null.
    return json.loads(df.to_json(orient="records"))
