"""chartforge command line. JSON in, JSON out."""

import argparse
import json
import sys

from . import __version__, build_chart, chart_from_csv, describe, list_themes, list_types, spec_from_json


def _exit_error(msg):
    print(json.dumps({"error": msg}), file=sys.stderr)
    raise SystemExit(1)


def _print_result(payload):
    print(json.dumps(payload))


def cmd_create(args):
    try:
        if args.csv:
            result = chart_from_csv(
                args.csv, args.type, args.x, args.y, args.output,
                theme=args.theme, title=args.title, xlabel=args.xlabel, ylabel=args.ylabel,
            )
        else:
            spec = spec_from_json(args.structure)
            result = build_chart(spec, args.output, theme=args.theme)
    except (ValueError, FileNotFoundError, OSError) as e:
        _exit_error(str(e))
    _print_result(result)


def cmd_describe(args):
    try:
        result = describe(args.input)
    except ValueError as e:
        _exit_error(str(e))
    _print_result(result)


def cmd_themes(args):
    _print_result(list_themes())


def cmd_types(args):
    _print_result(list_types())


def cmd_mcp(args):
    from .mcp_server import run

    run()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="chartforge", description="Draw charts from a spec dict or a CSV file.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Build a chart from a JSON spec or a CSV file.")
    p_create.add_argument("-o", "--output", required=True, help="Output .png or .svg path")
    p_create.add_argument("--structure", help='JSON spec, e.g. \'{"type": "line", "x": ["Jan", "Feb"], "series": [{"label": "Sales", "values": [3, 5]}]}\'')
    p_create.add_argument("--csv", help="CSV file to chart from")
    p_create.add_argument("--type", help="Chart type when using --csv: line, bar, barh, scatter, pie, histogram, area")
    p_create.add_argument("--x", help="CSV column for the x axis (or pie labels)")
    p_create.add_argument("--y", nargs="+", help="CSV column(s) for the y values")
    p_create.add_argument("--theme", default=None, help="Theme: light, dark or blue (default light)")
    p_create.add_argument("--title", help="Chart title")
    p_create.add_argument("--xlabel", help="X axis label")
    p_create.add_argument("--ylabel", help="Y axis label")
    p_create.set_defaults(func=cmd_create)

    p_desc = sub.add_parser("describe", help="Print chart file info as JSON.")
    p_desc.add_argument("-i", "--input", required=True, help="Input .png or .svg path")
    p_desc.set_defaults(func=cmd_describe)

    p_themes = sub.add_parser("themes", help="List the built-in themes.")
    p_themes.set_defaults(func=cmd_themes)

    p_types = sub.add_parser("types", help="List the chart types and what each needs.")
    p_types.set_defaults(func=cmd_types)

    p_mcp = sub.add_parser("mcp", help="Start the MCP server on stdio.")
    p_mcp.set_defaults(func=cmd_mcp)

    args = parser.parse_args(argv)
    if args.command == "create":
        if args.csv:
            if not args.type or not args.x or not args.y:
                parser.error("create --csv needs --type, --x and --y")
        elif not args.structure:
            parser.error("create needs --structure or --csv")
    args.func(args)


if __name__ == "__main__":
    main()
