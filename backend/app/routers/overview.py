
from fastapi import APIRouter, HTTPException

from backend.app.services.data_service import read_analytics_file


router = APIRouter(
    prefix="/api/overview",
    tags=["Dashboard Overview"],
)


def load_file(filename):
    return read_analytics_file(filename)


@router.get("")
def get_overview():

    try:
        # Accident analytics
        crash_yearly = load_file(
            "crashes/yearly_crash_statistics.parquet"
        )

        latest_crash = max(
            crash_yearly,
            key=lambda row: row["year"]
        )

        # Motor Vehicle Act
        motor_yearly = load_file(
            "violations/yearly_offence_statistics.parquet"
        )

        latest_motor = max(
            motor_yearly,
            key=lambda row: row["year"]
        )

        # Drink and Drive
        drink_yearly = load_file(
            "violations/yearly_drink_drive_statistics.parquet"
        )

        latest_drink = max(
            drink_yearly,
            key=lambda row: row["year"]
        )

        # Traffic cases and fines
        fines_yearly = load_file(
            "violations/traffic_cases_fines_yearly_statistics.parquet"
        )

        latest_fines = max(
            fines_yearly,
            key=lambda row: row["year"]
        )

        # Historical hotspots
        hotspots = load_file(
            "crashes/historical_hotspots.parquet"
        )

        top_hotspots = sorted(
            hotspots,
            key=lambda row: row["three_year_crashes"],
            reverse=True
        )[:5]

        return {
            "status": "success",

            "data": {
                "accidents": {
                    "latest_year": latest_crash,
                    "yearly_trend": crash_yearly,
                },

                "motor_vehicle": {
                    "latest_year": latest_motor,
                },

                "drink_and_drive": {
                    "latest_year": latest_drink,
                },

                "traffic_cases_and_fines": {
                    "latest_year": latest_fines,
                },

                "top_historical_hotspots": top_hotspots,
            },

            "data_quality_warnings": [
                {
                    "dataset": "Drink and Drive",
                    "year": 2018,
                    "warning": (
                        "Only 2 of 12 months are reported. "
                        "Annual total is incomplete."
                    ),
                },
                {
                    "dataset": "Traffic Cases and Fines",
                    "year": 2022,
                    "warning": (
                        "Category case sum differs from the "
                        "reported annual total by 22 cases."
                    ),
                },
            ],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate overview: {str(error)}",
        )
