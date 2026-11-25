"""Minimal MCP server over stdio. No dependencies, plain JSON-RPC.

Tools: create_chart, create_chart_from_csv, describe_chart, list_themes, list_chart_types.
"""

import json
import sys

from . import __version__, build_chart, chart_from_csv, describe, list_themes, list_types

TOOLS = [
    {
        "name": "create_chart",
        "description": "Build a PNG or SVG chart from a spec dict: type (line, bar, barh, scatter, pie, histogram, area), optional title/xlabel/ylabel/theme, x labels plus series of values, or labels+values for pie, values+bins for histogram.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "object", "description": "Chart spec dict"},
                "output": {"type": "string", "description": "Output .png or .svg path"},
                "theme": {"type": "string", "description": "Theme: light, dark or blue (default light)"},
            },
            "required": ["spec", "output"],
        },
    },
    {
        "name": "create_chart_from_csv",
        "description": "Build a PNG or SVG chart from a CSV file: one column for x, one or more for y.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "CSV file path"},
                "type": {"type": "string", "description": "Chart type: line, bar, barh, scatter, pie, histogram, area"},
                "x_column": {"type": "string", "description": "CSV column for the x axis"},
                "y_columns": {"type": "array", "items": {"type": "string"}, "description": "CSV column(s) for the y values"},
                "output": {"type": "string", "description": "Output .png or .svg path"},
                "theme": {"type": "string", "description": "Theme: light, dark or blue (default light)"},
                "title": {"type": "string", "description": "Chart title"},
            },
            "required": ["path", "type", "x_column", "y_columns", "output"],
        },
    },
    {
        "name": "describe_chart",
        "description": "Get format, size and dimensions of a .png or .svg chart.",
        "inputSchema": {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Chart path"}},
            "required": ["input"],
        },
    },
    {
        "name": "list_themes",
        "description": "List the built-in chart themes with their colors.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_chart_types",
        "description": "List the chart types and what each one needs.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _text(payload):
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


def _call(name, args):
    if name == "list_themes":
        return _text(list_themes())
    if name == "list_chart_types":
        return _text(list_types())
    if name == "describe_chart":
        return _text(describe(args["input"]))
    if name == "create_chart":
        return _text(build_chart(args["spec"], args["output"], args.get("theme")))
    if name == "create_chart_from_csv":
        return _text(chart_from_csv(
            args["path"], args["type"], args["x_column"], args["y_columns"],
            args["output"], args.get("theme", "light"), args.get("title"),
        ))
    raise ValueError(f"unknown tool '{name}'")


def run():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method", "")
        req_id = req.get("id")
        if method in ("notifications/initialized", "notifications/cancelled"):
            continue
        if method == "initialize":
            result = {
                "protocolVersion": req.get("params", {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "chartforge", "version": __version__},
            }
            resp = {"result": result}
        elif method == "ping":
            resp = {"result": {}}
        elif method == "tools/list":
            resp = {"result": {"tools": TOOLS}}
        elif method == "tools/call":
            try:
                resp = {"result": _call(req["params"]["name"], req["params"].get("arguments", {}))}
            except Exception as e:
                resp = {"result": {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}], "isError": True}}
        else:
            resp = {"error": {"code": -32601, "message": f"method not found: {method}"}}
        if req_id is not None:
            print(json.dumps({"jsonrpc": "2.0", "id": req_id, **resp}), flush=True)
