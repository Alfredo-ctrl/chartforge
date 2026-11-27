"""Tests run against charts built on the fly, no fixtures needed."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chartforge import build_chart, chart_from_csv, describe, list_themes, list_types, spec_from_json  # noqa: E402

X = ["Jan", "Feb", "Mar", "Apr"]
SERIES = [
    {"label": "Store A", "values": [12, 19, 8, 15]},
    {"label": "Store B", "values": [9, 14, 11, 17]},
]
CSV = "month,store_a,store_b\nJan,12,9\nFeb,19,14\nMar,8,11\nApr,15,17\n"


class TestChartforge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.csv = os.path.join(cls.tmp, "sales.csv")
        with open(cls.csv, "w", encoding="utf-8") as f:
            f.write(CSV)

    def out(self, name):
        return os.path.join(self.tmp, name)

    def _check_file(self, path):
        self.assertTrue(os.path.isfile(path))
        self.assertGreater(os.path.getsize(path), 100)

    def test_themes(self):
        themes = list_themes()
        self.assertEqual(set(themes), {"light", "dark", "blue"})
        self.assertEqual(len(themes["dark"]["colors"]), 6)

    def test_types(self):
        types = list_types()
        self.assertEqual(set(types), {"line", "bar", "barh", "scatter", "pie", "donut", "histogram", "area"})

    def test_line_png(self):
        result = build_chart({"type": "line", "title": "Sales", "x": X, "series": SERIES}, self.out("line.png"))
        self.assertEqual(result["type"], "line")
        self.assertEqual(result["format"], "png")
        self.assertEqual((result["width"], result["height"]), (1000, 600))
        self._check_file(self.out("line.png"))

    def test_bar_svg(self):
        result = build_chart({"type": "bar", "x": X, "series": SERIES[:1]}, self.out("bar.svg"), theme="dark")
        self.assertEqual(result["format"], "svg")
        self.assertEqual(result["theme"], "dark")
        self._check_file(self.out("bar.svg"))

    def test_barh(self):
        build_chart({"type": "barh", "x": X, "series": SERIES}, self.out("barh.png"))
        self._check_file(self.out("barh.png"))

    def test_scatter(self):
        build_chart({"type": "scatter", "x": X, "series": SERIES}, self.out("scatter.png"))
        self._check_file(self.out("scatter.png"))

    def test_area(self):
        build_chart({"type": "area", "x": X, "series": SERIES}, self.out("area.png"), theme="blue")
        self._check_file(self.out("area.png"))

    def test_pie(self):
        result = build_chart({"type": "pie", "labels": X, "values": [12, 19, 8, 15]}, self.out("pie.png"))
        self.assertEqual(result["type"], "pie")
        self._check_file(self.out("pie.png"))

    def test_donut(self):
        result = build_chart({"type": "donut", "labels": X, "values": [12, 19, 8, 15]}, self.out("donut.png"))
        self.assertEqual(result["type"], "donut")
        self._check_file(self.out("donut.png"))

    def test_histogram(self):
        build_chart({"type": "histogram", "values": [1, 2, 2, 3, 3, 3, 4, 5], "bins": 5}, self.out("hist.png"))
        self._check_file(self.out("hist.png"))

    def test_labels_and_titles(self):
        build_chart({"type": "line", "title": "T", "xlabel": "Month", "ylabel": "Units",
                     "x": X, "series": SERIES}, self.out("labeled.png"))
        self._check_file(self.out("labeled.png"))

    def test_series_length_mismatch(self):
        with self.assertRaises(ValueError):
            build_chart({"type": "line", "x": X, "series": [{"label": "A", "values": [1, 2]}]}, self.out("bad.png"))

    def test_unknown_type(self):
        with self.assertRaises(ValueError):
            build_chart({"type": "radar", "x": X, "series": SERIES}, self.out("bad.png"))

    def test_unknown_theme(self):
        with self.assertRaises(ValueError):
            build_chart({"type": "line", "x": X, "series": SERIES}, self.out("bad.png"), theme="neon")

    def test_bad_output_format(self):
        with self.assertRaises(ValueError):
            build_chart({"type": "line", "x": X, "series": SERIES}, self.out("bad.jpg"))

    def test_pie_length_mismatch(self):
        with self.assertRaises(ValueError):
            build_chart({"type": "pie", "labels": ["a"], "values": [1, 2]}, self.out("bad.png"))

    def test_csv_bar(self):
        result = chart_from_csv(self.csv, "bar", "month", ["store_a", "store_b"], self.out("csv.png"), title="CSV")
        self.assertEqual(result["type"], "bar")
        self._check_file(self.out("csv.png"))

    def test_csv_pie(self):
        chart_from_csv(self.csv, "pie", "month", ["store_a"], self.out("csv_pie.svg"))
        self._check_file(self.out("csv_pie.svg"))

    def test_csv_donut(self):
        result = chart_from_csv(self.csv, "donut", "month", ["store_a"], self.out("csv_donut.png"))
        self.assertEqual(result["type"], "donut")
        self._check_file(self.out("csv_donut.png"))

    def test_csv_missing_column(self):
        with self.assertRaises(ValueError):
            chart_from_csv(self.csv, "line", "nope", ["store_a"], self.out("bad.png"))

    def test_csv_missing_file(self):
        with self.assertRaises(ValueError):
            chart_from_csv(self.out("nope.csv"), "line", "month", ["store_a"], self.out("bad.png"))

    def test_describe_png(self):
        build_chart({"type": "line", "x": X, "series": SERIES}, self.out("d.png"))
        info = describe(self.out("d.png"))
        self.assertEqual(info["format"], "png")
        self.assertEqual((info["width"], info["height"]), (1000, 600))
        self.assertGreater(info["size_bytes"], 100)

    def test_describe_svg(self):
        build_chart({"type": "bar", "x": X, "series": SERIES}, self.out("d.svg"))
        info = describe(self.out("d.svg"))
        self.assertEqual(info["format"], "svg")
        self.assertGreater(info["size_bytes"], 100)

    def test_spec_from_json(self):
        spec = spec_from_json('{"type": "line", "x": ["a"], "series": [{"values": [1]}]}')
        self.assertEqual(spec["type"], "line")
        with self.assertRaises(ValueError):
            spec_from_json("{not json")

    def test_cli_create_and_describe(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        spec = json.dumps({"type": "line", "x": X, "series": SERIES})
        out = self.out("cli.png")
        run = subprocess.run([sys.executable, "-m", "chartforge.cli", "create", "-o", out, "--structure", spec],
                             capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        payload = json.loads(run.stdout)
        self.assertEqual(payload["type"], "line")
        run = subprocess.run([sys.executable, "-m", "chartforge.cli", "describe", "-i", out],
                             capture_output=True, text=True, env=env)
        self.assertEqual(json.loads(run.stdout)["format"], "png")

    def test_cli_csv(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        out = self.out("cli_csv.png")
        run = subprocess.run([sys.executable, "-m", "chartforge.cli", "create", "-o", out,
                              "--csv", self.csv, "--type", "bar", "--x", "month", "--y", "store_a"],
                             capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self._check_file(out)

    def test_cli_bad_spec_fails(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        run = subprocess.run([sys.executable, "-m", "chartforge.cli", "create", "-o", self.out("x.png"),
                              "--structure", '{"type": "radar"}'],
                             capture_output=True, text=True, env=env)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("error", run.stderr)

    def test_mcp_tools_list_and_create(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        reqs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "create_chart",
                "arguments": {"spec": {"type": "bar", "x": X, "series": SERIES}, "output": self.out("mcp.png")}}},
        ]
        proc = subprocess.run([sys.executable, "-m", "chartforge.cli", "mcp"],
                              input="\n".join(json.dumps(r) for r in reqs),
                              capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = [json.loads(l) for l in proc.stdout.strip().splitlines()]
        tools = [t["name"] for t in lines[1]["result"]["tools"]]
        self.assertIn("create_chart", tools)
        self.assertIn("list_chart_types", tools)
        payload = json.loads(lines[2]["result"]["content"][0]["text"])
        self.assertEqual(payload["type"], "bar")
        self._check_file(self.out("mcp.png"))


if __name__ == "__main__":
    unittest.main()
