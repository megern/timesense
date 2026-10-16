window.APP_CONFIG = {
  "title": "TimeSense",
  "subtitle":
    "Evaluate chronological forecasts and inspect unusual holdout errors.",
  "question":
    "How well does a transparent baseline forecast unseen later values?",
  "action": "Evaluate forecast",
  "mapping": [["values", "Time-ordered numeric value column"]],
  "params": [
    ["holdout", "Holdout observations", 8, 1, 10000],
    ["horizon", "Future forecast steps", 6, 1, 10000],
    ["season_length", "Season length", 4, 1, 10000],
    ["anomaly_threshold", "Residual threshold multiplier", 3, 1, 20]
  ],
  "method": true,
  "note":
    "Keep equally spaced observations in chronological order. Forecast holdout once from the training prefix; anomaly flags use training-only residual calibration.",
  "sample":
    "values\n20.0\n22.4\n20.8\n19.2\n21.6\n24.0\n22.4\n20.8\n23.2\n25.6\n24.0\n22.4\n24.8\n27.2\n25.6\n24.0\n26.4\n28.8\n27.2\n25.6\n28.0\n30.4\n28.8\n27.2\n29.6\n32.0\n30.4\n28.8\n31.2\n33.6\n32.0\n30.4\n32.8\n35.2\n33.6\n32.0\n34.4\n36.8\n35.2\n33.6\n36.0\n38.4\n36.8\n35.2\n37.6\n48.0\n38.4\n36.8\n",
  "slug": "timesense"
};
