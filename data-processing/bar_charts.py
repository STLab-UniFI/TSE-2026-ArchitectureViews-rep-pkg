"""
Frequency bar charts for the (multi-select, comma-separated) coded survey
questions. Every chart is declared in BAR_CHART_SPECS, so running this module
produces all of them at once.

Charts are horizontal and drawn at the printed column width (see figstyle.py),
so category labels stay horizontal and all text is printed at 8-9 pt.
"""

import os
import re
import matplotlib
matplotlib.use("Agg")  # headless: just write files, never open a window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figstyle
from config import CODING_CSV, FILTER_COLUMN, FILTER_VALUE, ensure_output_dir

# A comma separates two answers, except inside parentheses, as in "(code
# classes, technologies, etc)", or before "but", which continues a free-text answer.
ANSWER_SEPARATOR = re.compile(r",(?![^()]*\))(?!\s*but\b)")

# Display names for coded values (fixes typos/casing without touching the data).
# They are applied before counting, so different spellings of a value are merged.
DISPLAY_NAMES = {
    "Hard to mantain": "Hard to maintain",
    "NONE": "None",
    "Arcitectural Componets": "Architectural Components",
    "Do not knows": "Do not know",
    "VCS-integration": "VCS-Integration",
    "tool/repository suggestion": "repository/tool suggestions",
    "define_architecture": "define architecture",
    "dedicated_role": "dedicated role",
    "survey_suggestion": "survey suggestion",
    "textual_views": "textual views",
    "too_focused_on_code": "too focused on code",
}

MAX_LABEL_WIDTH_PT = 125   # wider category labels are wrapped on two lines
ROW_HEIGHT_IN = 0.18       # one-line row
EXTRA_LINE_IN = 0.12       # added for each extra label line
BAR_THICKNESS_IN = 0.11
AXIS_SPACE_IN = 0.42       # x tick labels + axis title


def _text_width_pt(fig, renderer, text):
    t = fig.text(0, 0, text, fontsize=figstyle.FONT_SIZE)
    width = t.get_window_extent(renderer).width * 72 / fig.dpi
    t.remove()
    return width


def _wrap_to_width(fig, renderer, text, max_pt):
    """Greedy word wrap using the real width of the text in the figure font."""
    if _text_width_pt(fig, renderer, text) <= max_pt:
        return text
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and _text_width_pt(fig, renderer, candidate) > max_pt:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return "\n".join(lines)


def generate_bar_chart(file_path, column_to_chart, output_path, filter_column=None,
                       filter_value=None, min_threshold=None, x_label="Respondents",
                       color=figstyle.BAR_COLOR):
    figstyle.apply()

    df = pd.read_csv(file_path)

    if column_to_chart not in df.columns:
        print(f"  [skip] column not found: {column_to_chart!r}")
        return None

    if filter_column and filter_value is not None:
        df = df[df[filter_column] == filter_value]
        if df.empty:
            print(f"  [skip] no rows match filter for {column_to_chart!r}")
            return None

    # Split comma-separated multi-select answers into individual values.
    values_split = (df[column_to_chart].str.split(ANSWER_SEPARATOR).explode().str.strip()
                    .replace(DISPLAY_NAMES))
    value_counts = values_split.value_counts().sort_values(ascending=False)

    if min_threshold is not None:
        value_counts = value_counts[value_counts >= min_threshold]
        if value_counts.empty:
            print(f"  [skip] nothing above threshold {min_threshold} for {column_to_chart!r}")
            return None

    # Category labels, wrapped to the label column width.
    probe = plt.figure()
    renderer = probe.canvas.get_renderer()
    labels = [_wrap_to_width(probe, renderer, str(v), MAX_LABEL_WIDTH_PT) for v in value_counts.index]
    plt.close(probe)

    # Row heights grow with the number of label lines; bars keep a fixed thickness.
    heights = [ROW_HEIGHT_IN + EXTRA_LINE_IN * label.count("\n") for label in labels]
    edges = np.concatenate([[0], np.cumsum(heights)])
    centers = (edges[:-1] + edges[1:]) / 2
    fig_height = edges[-1] + AXIS_SPACE_IN

    fig, ax = plt.subplots(figsize=(figstyle.COLUMN_WIDTH, fig_height), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02)

    ax.barh(centers, value_counts.values, height=BAR_THICKNESS_IN, color=color, zorder=2)
    ax.set_ylim(edges[-1], 0)  # first (largest) category on top
    ax.set_yticks(centers, labels, linespacing=1.1)
    ax.tick_params(axis="y", length=0, pad=3)

    for y, value in zip(centers, value_counts.values):
        ax.annotate(f"{value:.0f}", (value, y), xytext=(2, 0), textcoords="offset points",
                    ha="left", va="center_baseline", fontsize=figstyle.FONT_SIZE)
    ax.set_xlabel(x_label)
    ax.set_xlim(0, value_counts.max() * 1.15)  # room for the value labels
    ax.xaxis.grid(True, color=figstyle.GRID_COLOR, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    fig.savefig(output_path)
    plt.close(fig)
    print(f"  saved {os.path.basename(output_path)}")
    return value_counts


# Each spec: output filename (without extension), CSV column, and optional
# minimum-occurrence threshold (the paper shows tools mentioned at least 4 times
# and tool characteristics mentioned at least 20 times).
BAR_CHART_SPECS = [
    ("roles", "What is your current role(s) in your organization? [CODED]", None),
    ("view-purposes", "What is the most valuable purpose(s) of an architecture view? [CODED]", None),
    ("concerns", "What is the most important concern(s) an architecture view should cover? [CODED]", None),
    ("quality-attribute", "Which is the most important quality attribute an architecture view should cover?", None),
    ("standard-notations", "Are you using in some way any standard notation in your architecture views? If so, which ones? [CODED]", None),
    ("additional-important-elements", "If you believe important elements were missing above, please specify them with their importance (as example, code snippets - very important) [CODED]", None),
    ("tool-used", "Which tool do you use to create architecture views? (if any) [CODED]", 4),
    ("tool-features", "If you are using a tool, what made you pick it? [CODED]", 20),
    ("challenges", "What are the biggest challenges you face when creating architecture views? [CODED]", None),
    ("intended-user", "Who is the intended user of your architecture views? [CODED]", None),
    ("automatic-tool", "If yes, please specify which tool you use [CODED]", None),
    ("automatable-aspect", "Which of the following aspects could in your opinion be automated? [CODED]", None),
    ("view-changes", "In your opinion, how will the creation of architecture views change in the future? [CODED]", None),
    ("further-comments", "Any further comments o suggestions? [CODED]", None),
]


def generate_all():
    out_dir = ensure_output_dir()
    print("Bar charts:")
    for name, column, min_th in BAR_CHART_SPECS:
        generate_bar_chart(
            file_path=CODING_CSV,
            column_to_chart=column,
            output_path=os.path.join(out_dir, f"{name}.pdf"),
            filter_column=FILTER_COLUMN,
            filter_value=FILTER_VALUE,
            min_threshold=min_th,
        )


if __name__ == "__main__":
    generate_all()
