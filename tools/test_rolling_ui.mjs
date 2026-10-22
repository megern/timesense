import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import test from "node:test";
import { documentFromHTML, deferred } from "./ui-test-dom.mjs";
const root = new URL("../app/static/", import.meta.url);
const fixture = {
  assumptions:
    "Synthetic response fixture: every forecast uses its training prefix only.",
  results: [
    {
      method: "naive",
      mae: 2,
      rmse: 2.2361,
      per_horizon: [
        { horizon: 1, mae: 1, rmse: 1, evaluated_origins: 1 },
        { horizon: 2, mae: 3, rmse: 3, evaluated_origins: 1 },
      ],
      origins: [
        {
          training_rows: 16,
          forecast_row_indices: [16, 17],
          actual: [17, 19],
          prediction: [16, 16],
        },
      ],
    },
    {
      method: "drift",
      mae: 0.5,
      rmse: 0.7071,
      per_horizon: [
        { horizon: 1, mae: 0, rmse: 0, evaluated_origins: 1 },
        { horizon: 2, mae: 1, rmse: 1, evaluated_origins: 1 },
      ],
      origins: [
        {
          training_rows: 16,
          forecast_row_indices: [16, 17],
          actual: [17, 19],
          prediction: [17, 18],
        },
      ],
    },
    {
      method: "seasonal",
      mae: 5,
      rmse: 5.099,
      per_horizon: [
        { horizon: 1, mae: 4, rmse: 4, evaluated_origins: 1 },
        { horizon: 2, mae: 6, rmse: 6, evaluated_origins: 1 },
      ],
      origins: [
        {
          training_rows: 16,
          forecast_row_indices: [16, 17],
          actual: [17, 19],
          prediction: [13, 13],
        },
      ],
    },
  ],
};
function harness(
  response = Promise.resolve({ ok: true, json: async () => fixture }),
) {
  const document = documentFromHTML(
    fs.readFileSync(new URL("index.html", root), "utf8"),
  );
  const requests = [],
    blobs = [];
  const context = {
    document,
    console,
    TextEncoder,
    Blob,
    setTimeout: () => {},
    URL: {
      createObjectURL: (blob) => {
        blobs.push(blob);
        return "blob:synthetic";
      },
      revokeObjectURL: () => {},
    },
    fetch: async (path, options) => {
      requests.push({ path, input: JSON.parse(options.body) });
      return response;
    },
  };
  context.window = context;
  vm.createContext(context);
  for (const filename of [
    "config.js",
    "data.js",
    "advanced-data.js",
    "workbench.js",
    "advanced-ui.js",
  ])
    vm.runInContext(fs.readFileSync(new URL(filename, root), "utf8"), context, {
      filename,
    });
  return { document, requests, blobs };
}
const flush = () => new Promise((resolve) => setImmediate(resolve));
test("actual rolling comparison handler renders methods, per-horizon errors, origins and export", async () => {
  const h = harness(),
    get = (id) => h.document.getElementById(id);
  get("load-example").click();
  get("rolling-run").click();
  await flush();
  assert.equal(h.requests.length, 1, get("rolling-status").textContent);
  assert.equal(h.requests[0].path, "/rolling");
  assert.equal(h.requests[0].input.values.length, 48);
  assert.equal(
    get("rolling-results").hidden,
    false,
    get("rolling-status").textContent,
  );
  assert.match(get("rolling-status").textContent, /Calculation finished/);
  assert.match(get("rolling-summary").textContent, /naive22.236/);
  assert.match(get("rolling-summary").textContent, /drift0.50.707/);
  assert.match(get("rolling-summary").textContent, /seasonal55.099/);
  assert.match(get("rolling-horizons").textContent, /Evaluated|Origins/);
  assert.match(get("rolling-origins").textContent, /drift16171717/);
  assert.equal(get("rolling-assumptions").textContent, fixture.assumptions);
  get("rolling-export").click();
  const report = JSON.parse(await h.blobs[0].text());
  assert.equal(report.version, "0.4.0");
  assert.deepEqual(report.input, h.requests[0].input);
  assert.equal(report.result.results[1].mae, 0.5);
});
test("rolling controls invalidate an in-flight response", async () => {
  const pending = deferred(),
    h = harness(pending.promise),
    get = (id) => h.document.getElementById(id);
  get("rolling-run").click();
  get("rolling-panel").dispatch("input");
  pending.resolve({ ok: true, json: async () => fixture });
  await flush();
  assert.equal(get("rolling-results").hidden, true);
  assert.equal(get("rolling-export").disabled, true);
  assert.equal(get("rolling-summary").textContent, "");
});
