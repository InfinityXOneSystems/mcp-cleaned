# Prediction Graph Specs (Vega-Lite Compatible)

Reference visualization specs to render prediction outputs. Replace placeholders at runtime.

## 1) Forecast with Confidence Band
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "Forecast",
  "data": {"name": "table"},
  "datasets": {
    "table": []
  },
  "layer": [
    {
      "mark": {"type": "area", "color": "#8ecae6", "opacity": 0.25},
      "encoding": {
        "x": {"field": "ts", "type": "temporal"},
        "y": {"field": "lower", "type": "quantitative"},
        "y2": {"field": "upper"}
      }
    },
    {
      "mark": {"type": "line", "color": "#023047", "point": false},
      "encoding": {"x": {"field": "ts", "type": "temporal"}, "y": {"field": "predicted", "type": "quantitative"}}
    },
    {
      "mark": {"type": "line", "color": "#219ebc", "strokeDash": [2,2]},
      "encoding": {"x": {"field": "ts", "type": "temporal"}, "y": {"field": "observed", "type": "quantitative"}}
    }
  ]
}
```

## 2) Lead Score Distribution
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {"name": "table", "values": []},
  "mark": "bar",
  "encoding": {
    "x": {"bin": true, "field": "lead_score", "type": "quantitative"},
    "y": {"aggregate": "count", "type": "quantitative"}
  }
}
```

## 3) Driver Contributions (Top-K)
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {"name": "table", "values": []},
  "mark": "bar",
  "encoding": {
    "y": {"field": "driver", "type": "nominal", "sort": "-x"},
    "x": {"field": "contribution", "type": "quantitative"},
    "color": {"value": "#219ebc"}
  }
}
```
