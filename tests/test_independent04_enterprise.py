"""Independent arithmetic for overlapping origins and dated rolling boundaries."""

import math
from fractions import Fraction
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_overlapping_windows_pool_each_origin_lead_error_explicitly():
    values = [2**i for i in range(1, 11)]
    response = client.post(
        "/rolling",
        json={
            "values": values,
            "initial_train": 5,
            "horizon": 3,
            "folds": 2,
            "step": 1,
            "season_length": 2,
            "methods": ["naive", "drift", "seasonal"],
        },
    )
    assert response.status_code == 200, response.text
    results = {r["method"]: r for r in response.json()["results"]}
    for method in results:
        all_errors = []
        lead_errors = [[], [], []]
        for j, origin in enumerate([5, 6]):
            if method == "naive":
                prediction = [Fraction(values[origin - 1])] * 3
            elif method == "drift":
                prediction = [
                    Fraction(values[origin - 1])
                    + Fraction(values[origin - 1] - values[0], origin - 1) * (lead + 1)
                    for lead in range(3)
                ]
            else:
                prediction = [
                    Fraction(values[origin - 2 + lead % 2]) for lead in range(3)
                ]
            actual = values[origin : origin + 3]
            expected = [float(Fraction(a) - p) for a, p in zip(actual, prediction)]
            row = results[method]["origins"][j]
            assert row["forecast_row_indices"] == list(range(origin, origin + 3))
            assert row["prediction"] == pytest.approx([float(p) for p in prediction])
            assert row["residual"] == pytest.approx(expected)
            all_errors.extend(expected)
            for lead, value in enumerate(expected):
                lead_errors[lead].append(value)
        assert results[method]["mae"] == pytest.approx(
            sum(abs(e) for e in all_errors) / 6
        )
        assert results[method]["rmse"] == pytest.approx(
            math.sqrt(sum(e * e for e in all_errors) / 6)
        )
        assert [r["mae"] for r in results[method]["per_horizon"]] == pytest.approx(
            [sum(abs(e) for e in errors) / 2 for errors in lead_errors]
        )
    assert results["naive"]["mae"] == 176


@pytest.mark.parametrize("offset", ["+00:60", "+24:00", "-01:99"])
def test_new_rolling_route_preserves_strict_offset_validation(offset):
    payload = {
        "values": list(range(10)),
        "initial_train": 5,
        "horizon": 2,
        "folds": 2,
        "step": 1,
        "season_length": 2,
        "timestamps": [f"2026-01-01T00:00:{i:02d}{offset}" for i in range(10)],
    }
    assert client.post("/rolling", json=payload).status_code == 422
