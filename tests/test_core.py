import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import Request, analyze, app


def test_drift_forecast():
    result = analyze(Request(values=list(range(20)), holdout=5, horizon=3))
    assert result["mae"] == 0
    assert result["future_forecast"] == [20, 21, 22]
    assert result["anomalies"] == []


def test_seasonal_and_anomaly():
    values = [1, 3, 2] * 8
    result = analyze(
        Request(values=values, holdout=6, method="seasonal", season_length=3)
    )
    assert result["rmse"] == 0
    values[-1] = 100
    result = analyze(
        Request(values=values, holdout=6, method="seasonal", season_length=3)
    )
    assert result["anomalies"][-1]["index"] == 23


def test_api_and_ui():
    import json
    from pathlib import Path

    client = TestClient(app)
    payload = json.loads(
        (Path(__file__).parents[1] / "examples/synthetic.json").read_text()
    )
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), dict)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200
    assert client.post("/analyze", json={}).status_code == 422


def test_nonfinite_rejected():
    import json
    from pathlib import Path

    payload = json.loads(
        (Path(__file__).parents[1] / "examples/synthetic.json").read_text()
    )
    key = next(iter(payload))
    if isinstance(payload[key][0], list):
        payload[key][0][0] = "nan"
    else:
        payload[key][0] = "nan"
    assert TestClient(app).post("/analyze", json=payload).status_code == 422


def test_holdout_not_used_to_fit_forecast():
    original = analyze(Request(values=list(range(20)), holdout=5))
    changed = analyze(Request(values=list(range(15)) + [1000] * 5, holdout=5))
    assert original["holdout_prediction"] == changed["holdout_prediction"]
    assert original["training_residual_scale"] == changed["training_residual_scale"]
    assert changed["mae"] > 900


def test_naive_exact_values():
    result = analyze(
        Request(values=list(range(10)) + [9] * 5, method="naive", holdout=5)
    )
    assert result["mae"] == 0
    assert result["future_forecast"] == [9] * 5


def test_insufficient_seasons_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Request(values=list(range(10)), method="seasonal", season_length=4, holdout=5)
