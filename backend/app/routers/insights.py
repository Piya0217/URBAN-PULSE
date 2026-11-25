from fastapi import APIRouter, HTTPException

from backend.app.services.data_service import read_analytics_file


router = APIRouter(
    prefix="/api/insights",
    tags=["Historical Crash Insights"],
)


def get_top_records(records, metric, limit=10):
    """Return the highest-ranked records, using station and zone to break ties."""
    records_with_metric = [
        record
        for record in records
        if record.get(metric) is not None
    ]

    return sorted(
        records_with_metric,
        key=lambda record: (
            -record[metric],
            record.get("station") or "",
            record.get("zone") or "",
        ),
    )[:limit]


@router.get("/accidents")
def get_historical_accident_insights():
    try:
        # Load the saved analytical outputs through the shared data service.
        historical_hotspots = read_analytics_file(
            "crashes/historical_hotspots.parquet"
        )
        station_trends = read_analytics_file(
            "crashes/station_crash_trends.parquet"
        )

        # Rank stations by their recorded three-year crash totals.
        top_historical_hotspots = get_top_records(
            historical_hotspots,
            "three_year_crashes",
        )

        # Include only stations with an actual positive endpoint increase.
        positive_increases = [
            record
            for record in station_trends
            if record.get("change_2023_to_2025") is not None
            and record["change_2023_to_2025"] > 0
        ]
        top_increasing_stations = get_top_records(
            positive_increases,
            "change_2023_to_2025",
        )

        # Rank stations by the fatal crash percentage already in the
        # historical hotspot output. Keep the supporting counts with it.
        top_fatality_severity = get_top_records(
            historical_hotspots,
            "fatal_crash_percentage",
        )
        fatality_severity = [
            {
                "station": record.get("station"),
                "zone": record.get("zone"),
                "fatal_crash_percentage": record.get(
                    "fatal_crash_percentage"
                ),
                "three_year_crashes": record.get("three_year_crashes"),
                "three_year_fatal_crashes": record.get(
                    "three_year_fatal_crashes"
                ),
            }
            for record in top_fatality_severity
        ]

        data = {
            "historical_hotspots": top_historical_hotspots,
            "increasing_stations": top_increasing_stations,
            "fatality_severity": fatality_severity,
        }

        return {
            "status": "success",
            "count": {
                section_name: len(section_records)
                for section_name, section_records in data.items()
            },
            "data": data,
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load analytics: {str(error)}",
        )
