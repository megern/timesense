import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_origin_drift_exact_and_naive_per_horizon_errors():
    data = {
        "values": list(range(20)),
        "initial_train": 8,
        "horizon": 3,
        "folds": 3,
        "step": 3,
        "season_length": 4,
    }
    response = TestClient(app).post("/rolling", json=data)
    assert response.status_code == 200, response.text
    results = {r["method"]: r for r in response.json()["results"]}
    assert results["drift"]["mae"] == 0 and results["drift"]["rmse"] == 0
    assert [row["mae"] for row in results["naive"]["per_horizon"]] == [1, 2, 3]
    assert results["naive"]["rmse"] == pytest.approx(np.sqrt(14 / 3))
    assert results["drift"]["origins"][0]["train_end_row_index"] == 7
    assert results["drift"]["origins"][0]["forecast_row_indices"] == [8, 9, 10]


def test_later_values_do_not_leak_into_first_origin():
    data = {
        "values": list(range(20)),
        "initial_train": 8,
        "horizon": 2,
        "folds": 2,
        "step": 4,
        "season_length": 4,
    }
    first = TestClient(app).post("/rolling", json=data).json()
    data["values"][8:] = [1000] * 12
    second = TestClient(app).post("/rolling", json=data).json()
    for a, b in zip(first["results"], second["results"]):
        assert a["origins"][0]["prediction"] == b["origins"][0]["prediction"]


def test_origin_feasibility_limits_and_timestamp_validation():
    data = {
        "values": list(range(20)),
        "initial_train": 16,
        "horizon": 4,
        "folds": 8,
        "step": 4,
    }
    assert TestClient(app).post("/rolling", json=data).status_code == 422
    data.update(folds=1, horizon=25)
    assert TestClient(app).post("/rolling", json=data).status_code == 422
    data.update(horizon=4, timestamps=["invalid"] * 20)
    assert TestClient(app).post("/rolling", json=data).status_code == 422


def test_documented_synthetic_feature_request_is_runnable():
    import json
    from pathlib import Path

    data = json.loads(
        (Path(__file__).parents[1] / "examples/synthetic-rolling.json").read_text()
    )
    response = TestClient(app).post("/rolling", json=data)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), dict)
