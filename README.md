# TimeSense

Evaluate chronological fixed-origin baseline forecasts and flag holdout residuals using training-only calibration.

**Version0.2.0: local CPU research workbench.** Import a CSV, map the relevant columns, run the real calculation and inspect plots, tables and method assumptions. Export a JSON result report or exact replayable input. No API key, GPU, paid service or external model call is required.

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

At least10 finite numeric observations and five remaining training rows. Rows must be chronological and equally spaced; timestamp columns are not interpreted or sorted. Seasonal requires two complete training seasons. Holdout/horizon are bounded at10,000; horizon refers to future steps, not a calendar date.

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

Node is needed only for frontend development checks. Fresh rebuild evidence is in `evidence/rebuild/`. No Docker runtime, remote CI, publication or human review is implied merely by creating files. Required CI must pass before merging. Containers bind localhost and run nonroot; add authentication, HTTPS and deployment resource limits before external access. MIT license.
