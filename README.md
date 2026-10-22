# TimeSense

Evaluate chronological fixed-origin baseline forecasts and flag holdout residuals using training-only calibration.

**Version 0.4.0: local CPU research workbench.** Import a CSV, map the relevant columns, run the real calculation and inspect plots, tables and method assumptions. Export a JSON result report or exact replayable input. No API key, GPU, paid service or external model call is required.

## Why use it

An analyst has an equally spaced numeric sequence and needs an interpretable forecast baseline, an honest later holdout and an inspection list for unusual errors.

## Start

```sh
docker compose up --build
```

Open http://127.0.0.1:8000 and choose **Load synthetic example**. All bundled data are explicitly synthetic. Import your own UTF-8 CSV to use actual observations; their provenance remains unverified by the application.

Python3.12+ alternative:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API example:

```sh
curl --fail -H 'Content-Type: application/json' --data-binary @examples/synthetic.json http://127.0.0.1:8000/analyze
```

## Inputs, outputs and scientific scope

At least10 finite numeric observations and five remaining training rows. Rows must be chronological and equally spaced; timestamp validation is optional and never sorts input. Seasonal requires two complete training seasons. Holdout/horizon are bounded at10,000; horizon refers to future steps, not a calendar date.

MAE/RMSE are in value units. Holdout anomalies include zero-based original index, actual value and residual. The UI displays one-based row numbers. Flags mark a residual threshold, not a probability or verified anomaly. A zero training residual scale uses numeric tolerance for deterministic sequences. The result table separates future projections from evaluated holdout rows.

One-step residual calibration does not model full multi-step uncertainty, so later horizon errors can trigger extra flags. There are no prediction intervals, missing-value imputation, timestamp regularization, change-point models, automatic model selection or guaranteed anomaly precision. Changes in measurement or regime require domain inspection.

Read the [complete user guide](docs/USER_GUIDE.md) for the walkthrough, methods, export/replay, data limits and troubleshooting. A CSV sample is in `examples/synthetic.csv`; the JSON example calls the same API.

## Validate

```sh
pip install '.[dev]'
pytest -q
node tools/test_ui.mjs
pip-audit --strict
bandit -r app -ll
```

Node is needed only for frontend development checks. Fresh v0.4.0 developer evidence is in `evidence/improvements-0.4/`; previous v0.2 records remain historical. No Docker runtime, remote CI, publication or human review is implied merely by creating files. Required CI must pass before merging. Containers bind localhost and run nonroot; add authentication, HTTPS and deployment resource limits before external access. MIT license.

## v0.4.0: optional timestamp validation and dated forecasts

The CSV mapping panel now includes an optional timestamp column; the synthetic CSV contains a daily `timestamp` column. API `timestamps` is an optional string array exactly as long as `values`. Omitting it preserves the old API behavior: chronological regular row order is assumed and no calendar output is invented.

Accepted values are `YYYY-MM-DD` dates (interpreted at midnight UTC) or ISO datetimes with a T separator and explicit `Z` or ±HH:MM offset, such as `2026-01-01T12:00:00+03:00`. Numeric timezone offsets require hours00–23 and minutes00–59; malformed offsets are rejected rather than normalized. Fractional seconds are limited to six digits; leap seconds and naive datetimes are unsupported. All values normalize to UTC. Inputs must already be strictly increasing by UTC instant and have exactly equal intervals at datetime microsecond precision; they are never sorted, dropped, interpolated or resampled. Mixed offsets can be accepted when actual UTC intervals are equal; duplicate instants, naive datetimes, invalid dates, irregular spacing and calendar overflow return actionable422 errors.

The response adds `holdout_timestamps`, `future_timestamps`, `timestamp_interval_seconds` and `timestamp_basis` only when timestamps are supplied. Dates output as aware midnight-UTC timestamps; future timestamps extend the verified fixed UTC interval. These fields annotate the existing baseline calculations; future values remain unevaluated projections. Example: ten daily values datedJan1–Jan10 with horizon2 produce Jan11/Jan12 at00:00:00Z.

**DST and calendars:** equal local wall-clock spacing can be irregular in UTC across daylight-saving changes and will be rejected. There is no timezone database, business-day calendar or automatic resampling. Choose and document a suitable regular UTC grid or a calendar-aware forecasting method outside this tool. Prediction intervals and automatic missing-time repair remain out of scope.

## v0.4.0: expanding-window origin comparison

The new comparison panel uses the CSV value/timestamp mapping above. Choose initial training rows, forecast horizon, origins, step and season length, then compare naive/drift/seasonal baselines. `POST /rolling` accepts `values`, optional `timestamps`, `initial_train`, `horizon`, `folds`, `step`, `season_length` and optional unique `methods` list. Existing `/analyze` remains unchanged.

Origin j trains only on rows[0:initial_train+j*step], then forecasts the next horizon observations. The training prefix expands at later origins; no future observations enter a forecast. Each output includes training count, final training index, actual forecast indices, actuals, predictions and residuals. Overall MAE/RMSE pool actual out-of-sample errors; `per_horizon` aggregates each lead across all requested origins, with origin counts. Errors can be traced to every returned origin, not estimated from in-sample fit.

Bounds:10–2,000 values,1–8 origins, horizon1–24, initial training≥5, step1–240, season1–100; the final origin+horizon must fit inside the data. Seasonal needs two complete seasons in the first training prefix. Optional timestamps undergo the same strict increasing regular-UTC checks and annotate forecast rows; they do not change numerical forecasts. There is no automatic resampling or calendar/DST adjustment.

Overlapping windows reuse outcomes and are not independent trials. Comparing a small synthetic panel does not establish statistically significant model superiority. No confidence interval, tuning search, automatic winning-model recommendation or actual future observations are invented. Export the report to retain every origin's arrays. Request example: `examples/synthetic-rolling.json`.

## Server access and operating limits

See [Operations](docs/OPERATIONS.md) for optional shared-key API access, per-process request admission, platform notes and the additional work needed for public multi-user hosting.
