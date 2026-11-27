# Contributing

chartforge grows by adding chart types. A chart type is one branch in `_draw` in `chartforge/charts.py` plus one entry in `list_types()`.

Rules:

- One chart type does one thing. Share the drawing code with the other types instead of copying it.
- Never break the JSON contract: `chartforge describe` must keep working on any .png or .svg.
- A new feature touches code, test, README, MCP description and example in the same commit.
- Add a test in `tests/test_charts.py` for anything new.
- Run `python -m unittest discover -s tests` before opening a PR.
- One commit per change, with a message that says why, not just what.
