"""
Frequency bar charts for the (multi-select, comma-separated) coded survey
questions. Every chart is declared in BAR_CHART_SPECS, so running this module
produces all of them at once.
"""

import os
import matplotlib
matplotlib.use("Agg")  # headless: just write files, never open a window
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import textwrap

from config import CODING_CSV, FILTER_COLUMN, FILTER_VALUE, ensure_output_dir


def wrap_labels(text, width=20):
    return textwrap.fill(str(text), width=width)


def generate_bar_chart(file_path, column_to_chart, output_path, filter_column=None,
                       filter_value=None, min_threshold=None, x_label=None,
                       figsize=(12, 6), color="#808080"):
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 20,
        "axes.titlesize": 24,
        "axes.labelsize": 22,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "legend.fontsize": 18,
    })

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
    values_split = df[column_to_chart].str.split(",").explode().str.strip()
    value_counts = values_split.value_counts().sort_values(ascending=False)

    if min_threshold is not None:
        value_counts = value_counts[value_counts >= min_threshold]
        if value_counts.empty:
            print(f"  [skip] nothing above threshold {min_threshold} for {column_to_chart!r}")
            return None

    sns.set_style("whitegrid")
    plt.figure(figsize=figsize)
    ax = plt.gca()
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)

    bars = plt.bar(value_counts.index, value_counts.values, color=color, edgecolor=color)
    ax.set_xticks(range(len(value_counts)))
    ax.set_xticklabels([wrap_labels(str(label)) for label in value_counts.index])

    plt.xlabel(x_label or column_to_chart, labelpad=10)
    plt.ylabel("Frequency", labelpad=10)

    if len(value_counts) > 5:
        plt.xticks(rotation=45, ha="right")

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height + 0.1,
                 f"{height:.0f}", ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  saved {os.path.basename(output_path)}")
    return value_counts


# Each spec: output filename (without extension), CSV column, axis label, and
# optional minimum-occurrence threshold.
BAR_CHART_SPECS = [
    ("roles", "What is your current role(s) in your organization? [CODED]", "Role", None),
    ("view-purposes", "What is the most valuable purpose(s) of an architecture view? [CODED]", "Purpose", None),
    ("concernes", "What is the most important concern(s) an architecture view should cover? [CODED]", "Concern", None),
    ("quality-attribute", "Which is the most important quality attribute an architecture view should cover?", "Quality Attribute", None),
    ("standard-notations", "Are you using in some way any standard notation in your architecture views? If so, which ones? [CODED]", "Standard Notation", None),
    ("additional-important-elements", "If you believe important elements were missing above, please specify them with their importance (as example, code snippets - very important) [CODED]", "Additional Important Element", None),
    ("tool-used", "Which tool do you use to create architecture views? (if any) [CODED]", "Tool", None),
    ("tool-features", "If you are using a tool, what made you pick it? [CODED]", "Feature", None),
    ("challenges", "What are the biggest challenges you face when creating architecture views? [CODED]", "Challenge", None),
    ("intended-user", "Who is the intended user of your architecture views? [CODED]", "Intended User", None),
    ("automatic-tool", "If yes, please specify which tool you use [CODED]", "(Semi-)automatic Tool", None),
    ("automatable-aspect", "Which of the following aspects could in your opinion be automated? [CODED]", "Automatable Aspect", None),
    ("view-changes", "In your opinion, how will the creation of architecture views change in the future? [CODED]", "Future Change", None),
    ("further-comments", "Any further comments o suggestions? [CODED]", "Further Comment", None),
]


def generate_all():
    out_dir = ensure_output_dir()
    print("Bar charts:")
    for name, column, x_label, min_th in BAR_CHART_SPECS:
        generate_bar_chart(
            file_path=CODING_CSV,
            column_to_chart=column,
            output_path=os.path.join(out_dir, f"{name}.pdf"),
            filter_column=FILTER_COLUMN,
            filter_value=FILTER_VALUE,
            min_threshold=min_th,
            x_label=x_label,
        )


if __name__ == "__main__":
    generate_all()
