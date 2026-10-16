# TimeSense user guide — v0.2.0

## What this tool does

Evaluate chronological fixed-origin baseline forecasts and flag holdout residuals using training-only calibration.

Use case: An analyst has an equally spaced numeric sequence and needs an interpretable forecast baseline, an honest later holdout and an inspection list for unusual errors.

## Quickstart

Requires Docker Compose, or Python3.12+ for the installed pinned NumPy dependency. No API key, remote model, GPU or paid service is used.

```sh
docker compose up --build
```

Open http://127.0.0.1:8000. The interactive workbench loads a clearly labeled synthetic example. API docs: http://127.0.0.1:8000/docs. Change the host port in compose if running several tools together.

Without Docker:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Walkthrough

1. Load the synthetic48-observation series. Keep the8-row holdout and6 future steps.
2. Start with endpoint drift, then compare last-value and seasonal repetition. The synthetic example contains a deliberately unusual later value.
3. For seasonal repetition, season length4 requires at least8 training observations.
4. Inspect actual-versus-forecast plot, MAE/RMSE, row residuals and flags.
5. Export a report for each baseline. Future forecasts are not scored because their actual values are unavailable.

## Import and mapping

Import UTF-8 CSV with unique, nonempty header names. A BOM, CRLF, quoted commas, doubled quote escapes and quoted multiline fields are supported. Every data row must contain the same number of fields. Blank physical lines are ignored; empty fields within rows are not silently removed. The preview displays the first eight rows, while analysis uses all imported rows. Use mapping controls to select numeric columns; extra columns can remain unused. Import provenance is displayed as unverified, and imported values render as text.

Files and API requests are bounded at2MiB. CSV permits up to100 columns and100,000 rows; selected numeric matrices permit at most50 columns. Numbers must be finite with magnitude at most1e100. Imported files are read locally by the browser; selected data are sent to the local FastAPI service. The service holds requests in memory and does not persist them. No external network request is required by the workbench.

CSV format illustration (this fragment may be below the minimum sample size):

```csv
values
20
22.4
20.8
19.2
```

Input requirements: At least10 finite numeric observations and five remaining training rows. Rows must be chronological and equally spaced; timestamp columns are not interpreted or sorted. Seasonal requires two complete training seasons. Holdout/horizon are bounded at10,000; horizon refers to future steps, not a calendar date.

## Methods

The last holdout observations are separated from a chronological training prefix. Naive repeats the last value; drift extrapolates the endpoint slope; seasonal repeats the last training season. The entire holdout is predicted once from that prefix. Training-only rolling one-step residuals calibrate median centering and MAD scale with standard-deviation fallback. After evaluation, future projections use all supplied values.

## Read the output

MAE/RMSE are in value units. Holdout anomalies include zero-based original index, actual value and residual. The UI displays one-based row numbers. Flags mark a residual threshold, not a probability or verified anomaly. A zero training residual scale uses numeric tolerance for deterministic sequences. The result table separates future projections from evaluated holdout rows.

The workbench provides metric cards, a plot, interpretation and exact result table. For long time sequences, the table shows the first300 rows; the API report includes the complete arrays. Charts summarize calculations, not additional fitted models. The expandable API response exposes exact values. Change any mapping or parameter to clear old results, then rerun; an in-flight result is discarded if settings changed.

## Export and replay

**Export result report (JSON)** downloads application/version, timestamp, provenance label, mapping/settings and computed result. **Export replayable input (JSON)** includes selected numeric data and is exactly the `/analyze` request format. Exports are local downloads; review them for sensitive data before sharing. There is no result CSV export and therefore no spreadsheet-formula export interpretation. Synthetic example CSV uses only fixed headers/numeric values.

```sh
curl --fail -H 'Content-Type: application/json' --data-binary @examples/synthetic.json http://127.0.0.1:8000/analyze
curl --fail -H 'Content-Type: application/json' --data-binary @downloaded-analysis-input.json http://127.0.0.1:8000/analyze
```

See examples/synthetic.json for a complete forecast request; the short CSV fragment below is only a format illustration.

## Assumptions and limits

One-step residual calibration does not model full multi-step uncertainty, so later horizon errors can trigger extra flags. There are no prediction intervals, missing-value imputation, timestamp regularization, change-point models, automatic model selection or guaranteed anomaly precision. Changes in measurement or regime require domain inspection.

These are bounded local research tools. Synthetic fixtures do not establish external scientific validity. No domain expert or human audit is claimed. For network exposure, configure authentication, HTTPS, rate limits and deployment concurrency/memory bounds. Defaults bind to localhost and containers run without root privileges.

## Troubleshooting

Insufficient training observations: reduce holdout. Too few seasons: reduce season length or provide a longer history. Irregular timestamps: regularize observations before import using a documented policy. Excessive flags: inspect long-horizon uncertainty and data issues before adjusting thresholds; threshold changes do not validate an anomaly model.

CSV row/column error: fix the named row; do not convert a missing observation to zero automatically. HTTP422: inspect the specific schema/algorithm message and adjust mapping or input. HTTP413: reduce selected rows/columns below the2MiB request bound. File parse errors clear the usable dataset and results. For a browser error, inspect local service availability; restart only after reviewing the service log. If a download fails, check browser download permissions.

## Reproducibility and checks

```sh
pytest -q
node tools/test_ui.mjs
pip-audit --strict
bandit -r app -ll
```

Python tests exercise numerical results and actual HTTP endpoints. Node tests exercise CSV parsing, column mapping, numeric rejection and the synthetic analysis payload. Node22+ is used for development checks; it is not a runtime service dependency. Fresh rebuild evidence is under `evidence/rebuild/`; it records what was run and does not establish unexecuted Docker, GitHub CI or human validation. Configure required CI checks and never merge a failing release.

MIT license; see LICENSE.
