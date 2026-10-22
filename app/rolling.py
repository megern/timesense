"""Expanding-window origin evaluation; all predictions use only each prefix."""

import math
import numpy as np
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class RollingRequest(BaseModel):
    values: list[float] = Field(min_length=10, max_length=2000)
    timestamps: list[str] | None = None
    initial_train: int = Field(default=16, ge=5, le=2000)
    horizon: int = Field(default=4, ge=1, le=24)
    folds: int = Field(default=4, ge=1, le=8)
    step: int = Field(default=4, ge=1, le=240)
    season_length: int = Field(default=4, ge=1, le=100)
    methods: list[Literal["naive", "drift", "seasonal"]] = Field(
        default_factory=lambda: ["naive", "drift", "seasonal"],
        min_length=1,
        max_length=3,
    )

    @model_validator(mode="after")
    def valid(self):
        if any(not math.isfinite(x) or abs(x) > 1e100 for x in self.values):
            raise ValueError("values must be finite with magnitude at most 1e100")
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("methods must be unique")
        if self.initial_train + (self.folds - 1) * self.step + self.horizon > len(
            self.values
        ):
            raise ValueError(
                "not enough observations for requested origins and horizons; reduce folds, step, horizon or initial training size"
            )
        if "seasonal" in self.methods and self.initial_train < 2 * self.season_length:
            raise ValueError("initial training prefix needs two complete seasons")
        if self.timestamps is not None and len(self.timestamps) != len(self.values):
            raise ValueError("timestamps and values must have equal lengths")
        return self


def compare_origins(req, forecast, parse_timestamps, utc_string):
    values = np.asarray(req.values)
    timeline = parse_timestamps(req.timestamps) if req.timestamps is not None else None
    output = []
    for method in req.methods:
        errors = []
        origins = []
        for fold in range(req.folds):
            origin = req.initial_train + fold * req.step
            predicted = forecast(
                values[:origin], req.horizon, method, req.season_length
            )
            actual = values[origin : origin + req.horizon]
            residual = actual - predicted
            errors.append(residual)
            row = {
                "training_rows": origin,
                "train_end_row_index": origin - 1,
                "forecast_row_indices": list(range(origin, origin + req.horizon)),
                "prediction": predicted.tolist(),
                "actual": actual.tolist(),
                "residual": residual.tolist(),
            }
            if timeline is not None:
                row["forecast_timestamps"] = [
                    utc_string(v) for v in timeline[origin : origin + req.horizon]
                ]
            origins.append(row)
        error = np.asarray(errors)
        output.append(
            {
                "method": method,
                "mae": float(np.abs(error).mean()),
                "rmse": float(np.sqrt(np.mean(error**2))),
                "per_horizon": [
                    {
                        "horizon": i + 1,
                        "mae": float(np.abs(error[:, i]).mean()),
                        "rmse": float(np.sqrt(np.mean(error[:, i] ** 2))),
                        "evaluated_origins": req.folds,
                    }
                    for i in range(req.horizon)
                ],
                "origins": origins,
            }
        )
    return {
        "results": output,
        "folds": req.folds,
        "horizon": req.horizon,
        "assumptions": "Each origin trains only on the expanding prefix ending immediately before its forecast rows. No future observations enter prediction. Metrics pool actual forecast errors, with equal weight per origin/horizon. Overlapping windows can reuse outcomes and are not independent trials. No confidence interval or automatic best-model claim. Optional timestamps are validated as regular UTC instants; without them regular chronological row order is assumed.",
    }
