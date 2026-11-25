# Contributing

chartforge grows by adding chart types or themes. A chart type is one branch in `_draw` in `chartforge/charts.py` plus one entry in `list_types` and one check in `_check_spec`.

Rules:

- One chart type does one thing. Keep it under 20 lines if you can.
- Never break the JSON contract: `chartforge describe` must keep working, and every chart type must run on any spec.
- Add a test in `tests/test_charts.py` that builds a chart with the new type.
- Run `python -m unittest` before opening a PR.

That's it.
