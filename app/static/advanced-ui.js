"use strict";
function renderRolling(value) {
  const get = (id) => document.getElementById(id);
  table(
    get("rolling-summary"),
    ["Method", "Out-of-sample MAE", "RMSE"],
    value.results.map((row) => [row.method, format(row.mae), format(row.rmse)]),
  );
  table(
    get("rolling-horizons"),
    ["Method", "Horizon", "MAE", "RMSE", "Origins"],
    value.results.flatMap((row) =>
      row.per_horizon.map((h) => [
        row.method,
        h.horizon,
        format(h.mae),
        format(h.rmse),
        h.evaluated_origins,
      ]),
    ),
  );
  table(
    get("rolling-origins"),
    [
      "Method",
      "Training rows",
      "Forecast row (1-based)",
      "Actual",
      "Prediction",
    ],
    value.results.flatMap((row) =>
      row.origins.flatMap((origin) =>
        origin.prediction.map((prediction, i) => [
          row.method,
          origin.training_rows,
          origin.forecast_row_indices[i] + 1,
          format(origin.actual[i]),
          format(prediction),
        ]),
      ),
    ),
  );
  get("rolling-assumptions").textContent = value.assumptions;
}

(function () {
  const get = (id) => document.getElementById(id);
  let generation = 0,
    report = null;
  function invalidate() {
    generation++;
    report = null;
    get("rolling" + "-results").hidden = true;
    get("rolling" + "-export").disabled = true;
  }
  function save() {
    if (report) download("rolling" + "-report.json", report);
  }
  get("rolling" + "-export").onclick = save;
  async function execute(request) {
    invalidate();
    const token = generation;
    get("rolling" + "-run").disabled = true;
    get("rolling" + "-status").textContent =
      "Running bounded local calculation…";
    try {
      const response = await fetch("/rolling", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      const value = await response.json();
      if (token !== generation) return;
      if (!response.ok)
        throw Error(
          Array.isArray(value.detail)
            ? value.detail.map((row) => row.msg).join("; ")
            : value.detail,
        );
      report = {
        version: "0.4.0",
        input: request,
        result: value,
        source: get("source-label").textContent,
      };
      renderRolling(value);
      get("rolling" + "-results").hidden = false;
      get("rolling" + "-export").disabled = false;
      get("rolling" + "-status").textContent =
        "Calculation finished. Review assumptions before interpreting.";
    } catch (error) {
      if (token === generation)
        get("rolling" + "-status").textContent = error.message;
    } finally {
      get("rolling" + "-run").disabled = false;
    }
  }
  get("rolling-panel").addEventListener("input", invalidate);
  document
    .querySelectorAll("#mapping,.fields")
    .forEach((node) => node.addEventListener("input", invalidate));
  get("csv-file").addEventListener("change", invalidate);
  get("load-example").addEventListener("click", invalidate);
  get("rolling-run").onclick = () => {
    try {
      if (!data) throw Error("Load the main CSV first.");
      execute(
        LabAdvanced.rollingInput(data, mapping(), {
          initial_train: Number(get("rolling-train").value),
          horizon: Number(get("rolling-horizon").value),
          folds: Number(get("rolling-folds").value),
          step: Number(get("rolling-step").value),
          season_length: Number(get("rolling-season").value),
        }),
      );
    } catch (error) {
      invalidate();
      get("rolling-status").textContent = error.message;
    }
  };
})();
