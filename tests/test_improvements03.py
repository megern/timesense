import pytest
from fastapi.testclient import TestClient
from app.main import app, Request, analyze

from datetime import datetime, timedelta, timezone


def dated_payload():
    return {
        "values": list(range(10)),
        "timestamps": [f"2026-01-{i:02d}" for i in range(1, 11)],
        "holdout": 3,
        "horizon": 2,
    }


def test_date_inputs_normalized_utc_and_future_times_exact():
    response = TestClient(app).post("/analyze", json=dated_payload())
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["timestamp_interval_seconds"] == 86400
    assert result["holdout_timestamps"] == [
        f"2026-01-{i:02d}T00:00:00Z" for i in [8, 9, 10]
    ]
    assert result["future_timestamps"] == [
        "2026-01-11T00:00:00Z",
        "2026-01-12T00:00:00Z",
    ]
    assert result["future_forecast"] == [10, 11]


def test_mixed_offsets_compare_instants_not_wall_clock_strings():
    data = dated_payload()
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    data["timestamps"] = [
        (origin + timedelta(days=i))
        .astimezone(timezone(timedelta(hours=3 if i % 2 else 0)))
        .isoformat()
        for i in range(10)
    ]
    result = analyze(Request(**data))
    assert result["future_timestamps"][0] == "2026-01-11T00:00:00Z"


@pytest.mark.parametrize(
    "kind",
    [
        "invalid_date",
        "naive",
        "duplicate",
        "descending",
        "irregular",
        "length",
        "numeric",
    ],
)
def test_bad_timestamp_arrays_rejected_with_actionable_422(kind):
    data = dated_payload()
    if kind == "invalid_date":
        data["timestamps"][4] = "2026-02-30"
    if kind == "naive":
        data["timestamps"][4] = "2026-01-05T00:00:00"
    if kind == "duplicate":
        data["timestamps"][4] = data["timestamps"][3]
    if kind == "descending":
        data["timestamps"] = list(reversed(data["timestamps"]))
    if kind == "irregular":
        data["timestamps"][-1] = "2026-01-11"
    if kind == "length":
        data["timestamps"] = data["timestamps"][:-1]
    if kind == "numeric":
        data["timestamps"][4] = 42
    response = TestClient(app).post("/analyze", json=data)
    assert response.status_code == 422, response.text
    assert "timestamp" in response.text.lower()


def test_dst_wall_clock_spacing_is_not_regular_utc_spacing():
    data = dated_payload()
    data["timestamps"] = [
        f"2026-01-{i:02d}T12:00:00" + ("+03:00" if i < 6 else "+02:00")
        for i in range(1, 11)
    ]
    response = TestClient(app).post("/analyze", json=data)
    assert response.status_code == 422
    assert "regular in UTC" in response.text


def test_no_timestamps_preserves_forecast_and_does_not_invent_calendar():
    data = dated_payload()
    timed = analyze(Request(**data))
    del data["timestamps"]
    untimed = analyze(Request(**data))
    assert timed["holdout_prediction"] == untimed["holdout_prediction"]
    assert "future_timestamps" not in untimed


def test_calendar_overflow_controlled():
    data = dated_payload()
    data["timestamps"] = [f"9999-12-{i:02d}" for i in range(22, 32)]
    response = TestClient(app).post("/analyze", json=data)
    assert response.status_code == 422
    assert "calendar range" in response.text


@pytest.mark.parametrize(
    "value",
    [
        "2026-01-05T00:00:00.0000001Z",
        "2026-01-05 00:00:00Z",
        "2026-01-05T00:00:00+24:00",
    ],
)
def test_unsupported_timestamp_precision_or_format_rejected(value):
    data = dated_payload()
    data["timestamps"][4] = value
    response = TestClient(app).post("/analyze", json=data)
    assert response.status_code == 422
    assert "timestamp row 5" in response.text


def test_fractional_second_intervals_are_preserved():
    data = dated_payload()
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    data["timestamps"] = [
        (origin + timedelta(seconds=i * 0.5)).isoformat() for i in range(10)
    ]
    response = TestClient(app).post("/analyze", json=data)
    assert response.status_code == 200, response.text
    assert response.json()["timestamp_interval_seconds"] == 0.5
    assert response.json()["future_timestamps"] == [
        "2026-01-01T00:00:05Z",
        "2026-01-01T00:00:05.500000Z",
    ]


@pytest.mark.parametrize("offset", ["+24:00", "-24:00", "+99:00", "+23:60", "-23:99"])
def test_timezone_offset_bounds_are_strict(offset):
    data = dated_payload()
    data["timestamps"] = [f"2026-01-{day:02d}T00:00:00{offset}" for day in range(1, 11)]
    response = TestClient(app).post("/analyze", json=data)
    assert response.status_code == 422
    assert "hours 00..23, minutes 00..59" in response.text


def test_valid_offset_boundary_is_aware_and_regular():
    data = dated_payload()
    data["timestamps"] = [f"2026-01-{day:02d}T00:00:00+23:59" for day in range(1, 11)]
    response = TestClient(app).post("/analyze", json=data)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["timestamp_interval_seconds"] == 86400
    assert result["holdout_timestamps"][0] == "2026-01-07T00:01:00Z"
    assert result["future_timestamps"] == [
        "2026-01-10T00:01:00Z",
        "2026-01-11T00:01:00Z",
    ]
