"""Build one example chart of each type, for a quick smoke test."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chartforge import build_chart, chart_from_csv  # noqa: E402

OUT = tempfile.mkdtemp(prefix="chartforge-example-")

X = ["Jan", "Feb", "Mar", "Apr"]
SERIES = [
    {"label": "Store A", "values": [12, 19, 8, 15]},
    {"label": "Store B", "values": [9, 14, 11, 17]},
]

for kind in ("line", "bar", "barh", "scatter", "area"):
    print(build_chart({"type": kind, "title": f"{kind} example", "x": X, "series": SERIES},
                      os.path.join(OUT, f"{kind}.png"), theme="dark"))

print(build_chart({"type": "pie", "title": "Share", "labels": X, "values": [12, 19, 8, 15]},
                  os.path.join(OUT, "pie.svg")))
print(build_chart({"type": "histogram", "title": "Scores", "values": [1, 2, 2, 3, 3, 3, 4, 5]},
                  os.path.join(OUT, "histogram.png")))

csv_path = os.path.join(OUT, "sales.csv")
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("month,store_a,store_b\nJan,12,9\nFeb,19,14\nMar,8,11\nApr,15,17\n")
print(chart_from_csv(csv_path, "bar", "month", ["store_a", "store_b"],
                     os.path.join(OUT, "from_csv.png"), title="From CSV"))
print("charts in", OUT)
