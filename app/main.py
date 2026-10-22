from .access import AccessControl
import math
from .rolling import RollingRequest, compare_origins
from .guard import InputGuard
import re
from datetime import date, datetime, timezone
from typing import Literal
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field, PrivateAttr, model_validator


def finite(values):
    if not all(abs(v) <= 1e100 and math.isfinite(v) for v in values):
        raise ValueError("numeric values must be finite with magnitude at most 1e100")


def matrix(rows):
    if (
        not rows
        or not rows[0]
        or len(rows[0]) > 50
        or any(len(row) != len(rows[0]) for row in rows)
    ):
        raise ValueError("numeric matrix must be rectangular with 1 to 50 columns")
    finite([v for row in rows for v in row])


def parse_timestamps(values):
    """Accept ISO dates or timezone-aware datetimes and compare instants in UTC."""
    normalized = []
    for index, value in enumerate(values):
        try:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                parsed = datetime.combine(
                    date.fromisoformat(value), datetime.min.time(), timezone.utc
                )
            elif re.fullmatch(
                r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])",
                value,
            ):
                parsed = datetime.fromisoformat(
                    value.replace("Z", "+00:00").replace("t", "T")
                )
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError("datetime needs an explicit UTC offset or Z")
                parsed = parsed.astimezone(timezone.utc)
            else:
                raise ValueError(
                    "use YYYY-MM-DD or an ISO datetime with T and Z/±HH:MM offset (hours 00..23, minutes 00..59; at most six fractional-second digits)"
                )
            normalized.append(parsed)
        except (ValueError, OverflowError) as exc:
            raise ValueError(f"timestamp row {index + 1}: {exc}") from exc
    step = normalized[1] - normalized[0]
    if step.total_seconds() <= 0:
        raise ValueError("timestamps must be strictly increasing in UTC")
    for index in range(1, len(normalized)):
        current_step = normalized[index] - normalized[index - 1]
        if current_step.total_seconds() <= 0:
            raise ValueError(
                f"timestamp row {index + 1}: timestamps must be strictly increasing in UTC"
            )
        if current_step != step:
            raise ValueError(
                f"timestamp row {index + 1}: intervals must be regular in UTC; resample explicitly before analysis"
            )
    return normalized


def utc_string(value):
    return value.isoformat().replace("+00:00", "Z")


class Request(BaseModel):
    values: list[float] = Field(min_length=10, max_length=100000)
    holdout: int = Field(default=5, ge=1, le=10000)
    horizon: int = Field(default=5, ge=1, le=10000)
    method: Literal["naive", "drift", "seasonal"] = "drift"
    season_length: int = Field(default=1, ge=1, le=10000)
    anomaly_threshold: float = Field(default=3, ge=1, le=20)

    timestamps: list[str] | None = Field(default=None, min_length=10, max_length=100000)
    _timeline: list[datetime] | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def valid(self):
        finite(self.values)
        if len(self.values) - self.holdout < 5:
            raise ValueError("at least five training observations required")
        if (
            self.method == "seasonal"
            and len(self.values) - self.holdout < 2 * self.season_length
        ):
            raise ValueError("seasonal forecasts require two training seasons")
        if self.timestamps is not None:
            if len(self.timestamps) != len(self.values):
                raise ValueError("timestamps and values must have equal lengths")
            self._timeline = parse_timestamps(self.timestamps)
            try:
                (
                    self._timeline[-1]
                    + (self._timeline[1] - self._timeline[0]) * self.horizon
                )
            except OverflowError as exc:
                raise ValueError(
                    "future timestamps exceed the supported calendar range; reduce horizon"
                ) from exc
        return self


def forecast(values, steps, method, season):
    if method == "naive":
        return np.repeat(values[-1], steps)
    if method == "drift":
        return values[-1] + np.arange(1, steps + 1) * (values[-1] - values[0]) / (
            len(values) - 1
        )
    return np.resize(values[-season:], steps)


def analyze(req: Request):
    values = np.asarray(req.values)
    train, actual = values[: -req.holdout], values[-req.holdout :]
    prediction = forecast(train, req.holdout, req.method, req.season_length)
    residual = actual - prediction
    calibration = []
    first = max(2, req.season_length if req.method == "seasonal" else 2)
    for index in range(first, len(train)):
        calibration.append(
            float(
                train[index]
                - forecast(train[:index], 1, req.method, req.season_length)[0]
            )
        )
    center = float(np.median(calibration))
    scale = float(1.4826 * np.median(np.abs(np.asarray(calibration) - center)))
    if scale < 1e-12:
        scale = float(np.std(calibration))
    tolerance = max(1e-10, float(np.max(np.abs(train))) * 1e-12)
    flags = np.abs(residual - center) > (
        req.anomaly_threshold * scale if scale > tolerance else tolerance
    )
    timestamp_output = {}
    if req._timeline is not None:
        step = req._timeline[1] - req._timeline[0]
        timestamp_output = {
            "holdout_timestamps": [
                utc_string(value) for value in req._timeline[-req.holdout :]
            ],
            "future_timestamps": [
                utc_string(req._timeline[-1] + step * i)
                for i in range(1, req.horizon + 1)
            ],
            "timestamp_interval_seconds": step.total_seconds(),
            "timestamp_basis": "UTC instants; date-only values are midnight UTC. Regular intervals checked exactly at Python datetime microsecond precision. No automatic resampling or DST calendar adjustment.",
        }
    return {
        **timestamp_output,
        "holdout_prediction": prediction.tolist(),
        "holdout_actual": actual.tolist(),
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "anomalies": [
            {
                "index": int(i + len(train)),
                "value": float(actual[i]),
                "residual": float(residual[i]),
            }
            for i in np.flatnonzero(flags)
        ],
        "training_residual_scale": scale,
        "future_forecast": forecast(
            values, req.horizon, req.method, req.season_length
        ).tolist(),
        "limitations": "Holdout is forecast once from the chronological training prefix. Anomalies use training-only one-step residual calibration, so longer-horizon uncertainty can inflate flags. Equally spaced observations required; supplied timestamps are validated as regular UTC instants. Without timestamps, chronological regular row order is assumed. Prediction intervals are not modeled.",
    }


app = FastAPI(title="TimeSense", version="0.4.0")


STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/guide")
def user_guide():
    return FileResponse(
        Path(__file__).parent / "USER_GUIDE.md", media_type="text/plain"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def run_analysis(req: Request):
    try:
        result = analyze(req)

        def check(value):
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("numeric overflow; rescale input values")
            if isinstance(value, dict):
                for item in value.values():
                    check(item)
            elif isinstance(value, list):
                for item in value:
                    check(item)

        check(result)
        return result
    except (ValueError, np.linalg.LinAlgError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


app.add_middleware(InputGuard)


@app.post("/rolling")
def rolling(request: RollingRequest):
    try:
        result = compare_origins(request, forecast, parse_timestamps, utc_string)
        if any(
            not math.isfinite(r["mae"]) or not math.isfinite(r["rmse"])
            for r in result["results"]
        ):
            raise ValueError("forecast error overflow; rescale observations")
        return result
    except (ValueError, OverflowError, FloatingPointError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


app.add_middleware(AccessControl)
