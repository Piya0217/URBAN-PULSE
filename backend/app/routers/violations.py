
from fastapi import APIRouter, HTTPException

from backend.app.services.data_service import read_analytics_file


router = APIRouter(
    prefix="/api/violations",
    tags=["Violation Analytics"],
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
            detail=f"Unable to load violation analytics: {str(error)}",
        )


# --------------------------------------------------
# MOTOR VEHICLE ACT ANALYTICS
# --------------------------------------------------

@router.get("/motor-vehicle/yearly")
def get_motor_vehicle_yearly():
    return get_response(
        "violations/yearly_offence_statistics.parquet"
    )


@router.get("/motor-vehicle/top-10")
def get_motor_vehicle_top_10():
    return get_response(
        "violations/yearly_top_10_offences.parquet"
    )


@router.get("/motor-vehicle/overall-top-10")
def get_motor_vehicle_overall_top_10():
    return get_response(
        "violations/overall_top_10_offences.parquet"
    )


@router.get("/motor-vehicle/trends")
def get_motor_vehicle_trends():
    return get_response(
        "violations/offence_category_trends.parquet"
    )


@router.get("/motor-vehicle/changes")
def get_motor_vehicle_changes():
    return get_response(
        "violations/offence_endpoint_changes.parquet"
    )


# --------------------------------------------------
# DRINK AND DRIVE ANALYTICS
# --------------------------------------------------

@router.get("/drink-drive/yearly")
def get_drink_drive_yearly():
    return get_response(
        "violations/yearly_drink_drive_statistics.parquet"
    )


@router.get("/drink-drive/monthly")
def get_drink_drive_monthly():
    return get_response(
        "violations/monthly_drink_drive_statistics.parquet"
    )


@router.get("/drink-drive/comparison")
def get_drink_drive_comparison():
    return get_response(
        "violations/drink_drive_yearly_comparison.parquet"
    )


# --------------------------------------------------
# TRAFFIC CASES AND FINES ANALYTICS
# --------------------------------------------------

@router.get("/traffic-fines/yearly")
def get_traffic_fines_yearly():
    return get_response(
        "violations/traffic_cases_fines_yearly_statistics.parquet"
    )


@router.get("/traffic-fines/categories")
def get_traffic_fines_categories():
    return get_response(
        "violations/traffic_cases_fines_category_yearly_statistics.parquet"
    )


@router.get("/traffic-fines/rankings/cases")
def get_traffic_fines_cases_ranking():
    return get_response(
        "violations/traffic_cases_fines_category_cases_ranking.parquet"
    )


@router.get("/traffic-fines/rankings/fines")
def get_traffic_fines_fines_ranking():
    return get_response(
        "violations/traffic_cases_fines_category_fines_ranking.parquet"
    )


@router.get("/traffic-fines/trends")
def get_traffic_fines_trends():
    return get_response(
        "violations/traffic_cases_fines_category_trends.parquet"
    )


@router.get("/traffic-fines/fine-per-case")
def get_traffic_fines_per_case():
    return get_response(
        "violations/traffic_cases_fines_fine_per_case.parquet"
    )
