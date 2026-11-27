"""Charts from a spec dict: validate, draw with matplotlib, save PNG or SVG."""

import csv
import io
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

THEMES = {
    "light": {"bg": "white", "fg": "#1f2937", "grid": "#d1d5db", "palette": ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"]},
    "dark": {"bg": "#111827", "fg": "#f9fafb", "grid": "#374151", "palette": ["#60a5fa", "#f87171", "#4ade80", "#fbbf24", "#a78bfa", "#22d3ee"]},
    "blue": {"bg": "#eff6ff", "fg": "#1e3a8a", "grid": "#bfdbfe", "palette": ["#1d4ed8", "#0ea5e9", "#6366f1", "#2563eb", "#3b82f6", "#06b6d4"]},
}

TYPES = ["line", "bar", "barh", "scatter", "pie", "donut", "histogram", "area"]

FORMATS = ["png", "svg"]


def list_themes():
    return {name: {"background": t["bg"], "text": t["fg"], "colors": t["palette"]} for name, t in THEMES.items()}


def list_types():
    return {
        "line": "Lines over x. Needs x plus one or more series.",
        "bar": "Vertical bars. Needs x plus one or more series.",
        "barh": "Horizontal bars. Needs x plus one or more series.",
        "scatter": "Dots. Needs x plus one or more series.",
        "pie": "Slices. Needs labels plus one values list.",
        "donut": "Pie with a hole in the middle. Needs labels plus one values list.",
        "histogram": "Distribution of one values list. Optional bins.",
        "area": "Filled lines over x. Needs x plus one or more series.",
    }


def _numbers(name, values):
    if not isinstance(values, list) or not values:
        raise ValueError(f"'{name}' has to be a non-empty list of numbers")
    try:
        return [float(v) for v in values]
    except (TypeError, ValueError):
        raise ValueError(f"'{name}' has to hold numbers only, got {values!r}")


def _labels(name, values):
    if not isinstance(values, list) or not values:
        raise ValueError(f"'{name}' has to be a non-empty list")
    return [str(v) for v in values]


def _check_spec(spec):
    if not isinstance(spec, dict):
        raise ValueError("spec has to be a dict, e.g. {\"type\": \"line\", \"x\": [...], \"series\": [...]}")
    kind = spec.get("type")
    if kind not in TYPES:
        raise ValueError(f"unknown chart type '{kind}'. Run 'chartforge types' to see them all.")
    theme = spec.get("theme", "light")
    if theme not in THEMES:
        raise ValueError(f"unknown theme '{theme}'. Run 'chartforge themes' to see them all.")
    title = spec.get("title")
    if title is not None and not isinstance(title, str):
        raise ValueError("'title' has to be text")
    if kind in ("pie", "donut"):
        labels = _labels("labels", spec.get("labels"))
        values = _numbers("values", spec.get("values"))
        if len(labels) != len(values):
            raise ValueError("'labels' and 'values' need the same length")
        return kind, theme, {"labels": labels, "values": values}
    if kind == "histogram":
        values = _numbers("values", spec.get("values"))
        bins = spec.get("bins", 10)
        if not isinstance(bins, int) or isinstance(bins, bool) or bins < 1 or bins > 100:
            raise ValueError("'bins' has to be a whole number from 1 to 100")
        return kind, theme, {"values": values, "bins": bins}
    x = _labels("x", spec.get("x"))
    series = spec.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError("'series' has to be a non-empty list, e.g. [{\"label\": \"A\", \"values\": [1, 2]}]")
    clean = []
    for s in series:
        if not isinstance(s, dict) or "values" not in s:
            raise ValueError("every series needs 'values', e.g. {\"label\": \"A\", \"values\": [1, 2]}")
        vals = _numbers("values", s["values"])
        if len(vals) != len(x):
            raise ValueError(f"series '{s.get('label', '?')}' has {len(vals)} values but x has {len(x)}")
        clean.append({"label": str(s.get("label", "")), "values": vals})
    return kind, theme, {"x": x, "series": clean}


def _style_ax(ax, theme, spec):
    t = THEMES[theme]
    ax.set_facecolor(t["bg"])
    ax.tick_params(colors=t["fg"])
    for spine in ax.spines.values():
        spine.set_color(t["grid"])
    if spec.get("title"):
        ax.set_title(spec["title"], color=t["fg"], fontsize=14, fontweight="bold")
    if spec.get("xlabel"):
        ax.set_xlabel(spec["xlabel"], color=t["fg"])
    if spec.get("ylabel"):
        ax.set_ylabel(spec["ylabel"], color=t["fg"])
    ax.grid(True, color=t["grid"], alpha=0.6, linestyle="--", linewidth=0.5)
    ax.set_axisbelow(True)


def _draw(ax, kind, theme, data):
    colors = THEMES[theme]["palette"]
    if kind == "donut":
        wedges, _, autotexts = ax.pie(
            data["values"], labels=data["labels"], autopct="%1.1f%%",
            colors=colors, textprops={"color": THEMES[theme]["fg"]},
            wedgeprops={"width": 0.4},
        )
        for txt in autotexts:
            txt.set_color(THEMES[theme]["fg"])
        ax.set_aspect("equal")
        return
    if kind == "pie":
        wedges, _, autotexts = ax.pie(
            data["values"], labels=data["labels"], autopct="%1.1f%%",
            colors=colors, textprops={"color": THEMES[theme]["fg"]},
        )
        for txt in autotexts:
            txt.set_color(THEMES[theme]["fg"])
        ax.set_aspect("equal")
        return
    if kind == "histogram":
        ax.hist(data["values"], bins=data["bins"], color=colors[0], edgecolor=THEMES[theme]["bg"])
        return
    x = data["x"]
    xs = range(len(x))
    if kind == "bar":
        width = 0.8 / len(data["series"])
        for i, s in enumerate(data["series"]):
            pos = [v + (i - (len(data["series"]) - 1) / 2) * width for v in xs]
            ax.bar(pos, s["values"], width=width, color=colors[i % len(colors)], label=s["label"] or None)
    elif kind == "barh":
        height = 0.8 / len(data["series"])
        for i, s in enumerate(data["series"]):
            pos = [v + (i - (len(data["series"]) - 1) / 2) * height for v in xs]
            ax.barh(pos, s["values"], height=height, color=colors[i % len(colors)], label=s["label"] or None)
        ax.set_yticks(list(xs))
        ax.set_yticklabels(x)
    elif kind == "scatter":
        for i, s in enumerate(data["series"]):
            ax.scatter(list(xs), s["values"], color=colors[i % len(colors)], label=s["label"] or None)
    elif kind == "area":
        for i, s in enumerate(data["series"]):
            ax.fill_between(list(xs), s["values"], color=colors[i % len(colors)], alpha=0.35, label=s["label"] or None)
            ax.plot(list(xs), s["values"], color=colors[i % len(colors)])
    else:  # line
        for i, s in enumerate(data["series"]):
            ax.plot(list(xs), s["values"], color=colors[i % len(colors)], marker="o", label=s["label"] or None)
    if kind not in ("barh",):
        ax.set_xticks(list(xs))
        ax.set_xticklabels(x)
    if len(data["series"]) > 1 or any(s["label"] for s in data["series"]):
        ax.legend()


def build_chart(spec, output, theme=None):
    """Draw a chart from a spec dict and save it. Returns info about the file."""
    kind, spec_theme, data = _check_spec(spec)
    theme = theme or spec_theme
    if theme not in THEMES:
        raise ValueError(f"unknown theme '{theme}'. Run 'chartforge themes' to see them all.")
    fmt = os.path.splitext(output)[1].lower().lstrip(".")
    if fmt not in FORMATS:
        raise ValueError(f"output has to end in .png or .svg, got '{output}'")
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(THEMES[theme]["bg"])
    _draw(ax, kind, theme, data)
    _style_ax(ax, theme, spec)
    fig.tight_layout()
    fig.savefig(output, format=fmt, facecolor=fig.get_facecolor())
    plt.close(fig)
    info = {"output": output, "type": kind, "format": fmt, "theme": theme}
    info.update(describe(output))
    return info


def chart_from_csv(path, kind, x_column, y_columns, output, theme="light", title=None, xlabel=None, ylabel=None):
    """Build a chart from a CSV file: one column for x, one or more for y."""
    theme = theme or "light"
    if kind not in TYPES:
        raise ValueError(f"unknown chart type '{kind}'. Run 'chartforge types' to see them all.")
    if not os.path.isfile(path):
        raise ValueError(f"can't find '{path}'")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"'{path}' has no data rows")
    if x_column not in rows[0]:
        raise ValueError(f"column '{x_column}' is not in '{path}'")
    if isinstance(y_columns, str):
        y_columns = [y_columns]
    if not y_columns:
        raise ValueError("give at least one y column")
    for col in y_columns:
        if col not in rows[0]:
            raise ValueError(f"column '{col}' is not in '{path}'")
    spec = {"type": kind, "title": title, "xlabel": xlabel or x_column, "ylabel": ylabel, "theme": theme}
    if kind == "pie":
        spec["labels"] = [r[x_column] for r in rows]
        spec["values"] = _numbers(y_columns[0], [r[y_columns[0]] for r in rows])
    elif kind == "histogram":
        spec["values"] = _numbers(y_columns[0], [r[y_columns[0]] for r in rows])
    else:
        spec["x"] = [r[x_column] for r in rows]
        spec["series"] = [
            {"label": col, "values": _numbers(col, [r[col] for r in rows])} for col in y_columns
        ]
    return build_chart(spec, output)


def describe(path):
    """File info: format, size, dimensions when it's a PNG."""
    if not os.path.isfile(path):
        raise ValueError(f"can't find '{path}'")
    info = {"path": path, "size_bytes": os.path.getsize(path)}
    ext = os.path.splitext(path)[1].lower()
    if ext == ".png":
        from PIL import Image

        with Image.open(path) as img:
            info.update({"format": "png", "width": img.width, "height": img.height})
    elif ext == ".svg":
        with open(path, encoding="utf-8") as f:
            head = f.read(4096)
        info["format"] = "svg"
        import re

        m = re.search(r'width="([\d.]+)(pt|px)?"\s+height="([\d.]+)', head)
        if m:
            info["width"] = float(m.group(1))
            info["height"] = float(m.group(3))
    else:
        raise ValueError(f"describe only works on .png or .svg, got '{path}'")
    return info


def spec_from_json(text):
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"bad JSON: {e}")
    if not isinstance(spec, dict):
        raise ValueError("spec JSON has to be an object")
    return spec
