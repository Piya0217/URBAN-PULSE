
import requests


BASE_URL = "http://127.0.0.1:8000"

EXPECTED_ENDPOINTS = {
    "/api/health": 1,

    # Accident Intelligence
    "/api/accidents/yearly": 3,
    "/api/accidents/zones": 12,
    "/api/accidents/stations": 151,
    "/api/accidents/hotspots": 46,
    "/api/accidents/trends": 46,

    # Motor Vehicle Act
    "/api/violations/motor-vehicle/yearly": 8,
    "/api/violations/motor-vehicle/top-10": 80,
    "/api/violations/motor-vehicle/overall-top-10": 10,
    "/api/violations/motor-vehicle/trends": 320,
    "/api/violations/motor-vehicle/changes": 26,

    # Drink and Drive
    "/api/violations/drink-drive/yearly": 3,
    "/api/violations/drink-drive/monthly": 36,
    "/api/violations/drink-drive/comparison": 3,

    # Traffic Cases and Fines
    "/api/violations/traffic-fines/yearly": 15,
    "/api/violations/traffic-fines/categories": 75,
    "/api/violations/traffic-fines/rankings/cases": 5,
    "/api/violations/traffic-fines/rankings/fines": 5,
    "/api/violations/traffic-fines/trends": 75,
    "/api/violations/traffic-fines/fine-per-case": 75,
}


def test_endpoints():
    passed = 0
    failed = 0

    print("\n========== URBAN PULSE API TESTING ==========\n")

    for endpoint, expected_count in EXPECTED_ENDPOINTS.items():

        try:
            response = requests.get(
                BASE_URL + endpoint,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if endpoint == "/api/health":
                valid = result.get("status") == "healthy"
            else:
                valid = (
                    result.get("status") == "success"
                    and result.get("count") == expected_count
                    and len(result.get("data", [])) == expected_count
                )

            if valid:
                passed += 1
                print(
                    f"PASS | {endpoint} | "
                    f"Records: {expected_count}"
                )
            else:
                failed += 1
                print(
                    f"FAIL | {endpoint} | "
                    f"Expected: {expected_count}, "
                    f"Received: {result.get('count')}"
                )

        except Exception as error:
            failed += 1
            print(f"FAIL | {endpoint} | {error}")

    print("\n========== TEST SUMMARY ==========")
    print(f"Total endpoints : {len(EXPECTED_ENDPOINTS)}")
    print(f"Passed          : {passed}")
    print(f"Failed          : {failed}")

    if failed == 0:
        print("\nALL API ENDPOINT TESTS PASSED!")
    else:
        print("\nSOME API TESTS NEED ATTENTION.")

def test_overview():
    response = requests.get(
        BASE_URL + "/api/overview",
        timeout=30
    )

    response.raise_for_status()
    result = response.json()

    assert result["status"] == "success"

    data = result["data"]

    assert data["accidents"]["latest_year"]["year"] == 2025
    assert data["motor_vehicle"]["latest_year"]["year"] == 2025
    assert data["drink_and_drive"]["latest_year"]["year"] == 2018
    assert data["traffic_cases_and_fines"]["latest_year"]["year"] == 2025

    assert len(data["top_historical_hotspots"]) == 5

    # Warnings are at the top level, outside "data".
    assert len(result["data_quality_warnings"]) >= 2

    print("PASS | /api/overview")


def test_insights():
    endpoint = "/api/insights/accidents"
    response = requests.get(BASE_URL + endpoint, timeout=30)

    response.raise_for_status()
    result = response.json()

    assert result["status"] == "success"

    data = result["data"]
    expected_sections = {
        "historical_hotspots",
        "increasing_stations",
        "fatality_severity",
    }
    assert expected_sections.issubset(data.keys())

    historical_hotspots = data["historical_hotspots"]
    increasing_stations = data["increasing_stations"]
    fatality_severity = data["fatality_severity"]

    assert len(historical_hotspots) == 10
    assert len(increasing_stations) == 10
    assert len(fatality_severity) == 10

    assert result["count"]["historical_hotspots"] == len(
        historical_hotspots
    )
    assert result["count"]["increasing_stations"] == len(
        increasing_stations
    )
    assert result["count"]["fatality_severity"] == len(fatality_severity)

    hotspot_counts = [
        station["three_year_crashes"]
        for station in historical_hotspots
    ]
    assert hotspot_counts == sorted(hotspot_counts, reverse=True)

    increases = [
        station["change_2023_to_2025"]
        for station in increasing_stations
    ]
    assert all(change > 0 for change in increases)
    assert increases == sorted(increases, reverse=True)

    fatality_percentages = [
        station["fatal_crash_percentage"]
        for station in fatality_severity
    ]
    assert fatality_percentages == sorted(
        fatality_percentages,
        reverse=True,
    )
    assert all(
        station.get("three_year_crashes") is not None
        and station.get("three_year_fatal_crashes") is not None
        for station in fatality_severity
    )

    print("PASS | /api/insights/accidents")


if __name__ == "__main__":
    test_endpoints()
    test_overview()
    test_insights()
