# chartforge

Charts for AI agents. No GUI, no account, no vendor lock-in: a CLI, a Python API and an MCP server that any agent can drive — Muse, Antigravity, Codex, Claude Code, or a local model.

It draws charts with matplotlib and saves PNG or SVG, so install the package and you are set.

## Install

```sh
pip install chartforge
```

## Use it from the terminal

```sh
# what chart types exist?
chartforge types

# what themes exist?
chartforge themes

# describe a chart file
chartforge describe -i sales.png

# build a chart from a JSON spec
chartforge create -o sales.png --theme dark --structure '{
  "type": "line", "title": "Weekly sales",
  "x": ["Mon", "Tue", "Wed", "Thu"],
  "series": [{"label": "Store A", "values": [12, 19, 8, 15]}]
}'

# or build it from a CSV file
chartforge create -o sales.png --csv sales.csv --type bar --x month --y store_a store_b
```

## Spec format

```json
{
  "type": "line",
  "title": "Weekly sales",
  "xlabel": "Day",
  "ylabel": "Units",
  "theme": "dark",
  "x": ["Mon", "Tue", "Wed"],
  "series": [{"label": "Store A", "values": [12, 19, 8]}]
}
```

| type | needs |
| ---- | ----- |
| `line` | `x`, `series` (one or more, each with `label` and `values`) |
| `bar` | `x`, `series` |
| `barh` | `x`, `series` |
| `scatter` | `x`, `series` |
| `area` | `x`, `series` |
| `pie` | `labels`, `values` |
| `histogram` | `values`, optional `bins` (default 10) |

Themes: `light`, `dark`, `blue`.

## CSV format

First row is the header. One column is `x` (or the pie labels), the rest are the series. For a histogram, one y column holds the values.

```csv
month,store_a,store_b
Jan,12,9
Feb,19,14
Mar,8,11
```

## Use it from Python

```python
from chartforge import build_chart, chart_from_csv, describe

build_chart({"type": "bar", "title": "Sales",
             "x": ["Jan", "Feb"], "series": [{"label": "A", "values": [3, 5]}]},
            "sales.png", theme="dark")

chart_from_csv("sales.csv", "line", "month", ["store_a"], "sales.svg")
describe("sales.png")  # format, size, dimensions
```

## MCP server

```sh
chartforge mcp
```

Tools: `create_chart`, `create_chart_from_csv`, `describe_chart`, `list_themes`, `list_chart_types`.
