// prettier-ignore
window.APP_CONFIG = {
  "title": "TimeSense",
  "subtitle": "Evaluate chronological forecasts and inspect unusual holdout errors.",
  "question": "How well does a transparent baseline forecast unseen later values?",
  "action": "Evaluate forecast",
  "mapping": [
    [
      "values",
      "Time-ordered numeric value column"
    ]
  ],
  "params": [
    [
      "holdout",
      "Holdout observations",
      8,
      1,
      10000
    ],
    [
      "horizon",
      "Future forecast steps",
      6,
      1,
      10000
    ],
    [
      "season_length",
      "Season length",
      4,
      1,
      10000
    ],
    [
      "anomaly_threshold",
      "Residual threshold multiplier",
      3,
      1,
      20
    ]
  ],
  "method": true,
  "note": "Optional timestamps must be ISO dates or explicitly offset-aware datetimes, strictly increasing with equal intervals in UTC. No resampling or DST calendar adjustment. Without timestamps, chronological equal row spacing is assumed.",
  "sample": "timestamp,values\n2026-01-01,20.0\n2026-01-02,22.4\n2026-01-03,20.8\n2026-01-04,19.2\n2026-01-05,21.6\n2026-01-06,24.0\n2026-01-07,22.4\n2026-01-08,20.8\n2026-01-09,23.2\n2026-01-10,25.6\n2026-01-11,24.0\n2026-01-12,22.4\n2026-01-13,24.8\n2026-01-14,27.2\n2026-01-15,25.6\n2026-01-16,24.0\n2026-01-17,26.4\n2026-01-18,28.8\n2026-01-19,27.2\n2026-01-20,25.6\n2026-01-21,28.0\n2026-01-22,30.4\n2026-01-23,28.8\n2026-01-24,27.2\n2026-01-25,29.6\n2026-01-26,32.0\n2026-01-27,30.4\n2026-01-28,28.8\n2026-01-29,31.2\n2026-01-30,33.6\n2026-01-31,32.0\n2026-02-01,30.4\n2026-02-02,32.8\n2026-02-03,35.2\n2026-02-04,33.6\n2026-02-05,32.0\n2026-02-06,34.4\n2026-02-07,36.8\n2026-02-08,35.2\n2026-02-09,33.6\n2026-02-10,36.0\n2026-02-11,38.4\n2026-02-12,36.8\n2026-02-13,35.2\n2026-02-14,37.6\n2026-02-15,48.0\n2026-02-16,38.4\n2026-02-17,36.8\n",
  "slug": "timesense"
};
