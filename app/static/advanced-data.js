/* Validated research requests assembled from mapped CSV, without executable input. */
(function (global) {
  const data =
    typeof module !== "undefined" && module.exports
      ? require("./data.js")
      : global.LabData;
  function rollingInput(parsed, map, settings) {
    const request = {
      ...settings,
      values: data.numericColumn(parsed, map.values),
    };
    if (map.timestamps) {
      const column = parsed.headers.indexOf(map.timestamps);
      if (column < 0) throw Error("Choose an existing timestamp column.");
      request.timestamps = parsed.rows.map((row, i) => {
        if (!row[column].trim())
          throw Error(`Row ${i + 2}: timestamp is missing.`);
        return row[column].trim();
      });
    }
    return request;
  }
  const api = { rollingInput };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else global.LabAdvanced = api;
})(typeof window === "undefined" ? globalThis : window);
