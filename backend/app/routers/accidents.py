
from fastapi import APIRouter, HTTPException

from backend.app.services.data_service import read_analytics_file


router = APIRouter(
    prefix="/api/accidents",
    tags=["Accident Intelligence"],
)


def get_response(filename: str):
    try:
        records = read_analytics_file(filename)

        return {
            "status": "success",
            "count": len(records),
            "data": records,
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


@router.get("/yearly")
def get_yearly_accidents():
    return get_response(
        "crashes/yearly_crash_statistics.parquet"
    )


@router.get("/zones")
def get_zone_accidents():
    return get_response(
        "crashes/zone_crash_statistics.parquet"
    )


@router.get("/stations")
def get_station_accidents():
    return get_response(
        "crashes/station_year_statistics.parquet"
    )


@router.get("/hotspots")
def get_accident_hotspots():
    return get_response(
        "crashes/historical_hotspots.parquet"
    )


@router.get("/trends")
def get_station_crash_trends():
    return get_response(
        "crashes/station_crash_trends.parquet"
    )
