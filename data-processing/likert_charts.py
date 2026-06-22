"""
Diverging Likert plots for the survey's 5-point-scale questions.
All four plots (important elements, usage, utility, features) are produced in
one run. Some questions are stored as text labels and some as raw 1-5 integers
(``raw_values=True`` maps those to the scale labels first).
"""

import os
import compat  # noqa: F401  -- applies the pandas 3.0 patches on import
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import pandas as pd
import plot_likert

from config import CODING_CSV, FILTER_COLUMN, FILTER_VALUE, ensure_output_dir

IMPORTANCE_SCALE = ["Very unimportant", "Unimportant", "Neutral", "Important", "Very important"]
ACCORDANCE_SCALE = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]


def _convert_raw_input(df, scale):
    mapping = {i + 1: scale[i] for i in range(len(scale))}
    return df.replace(mapping)


def generate_likert_plot(file_path, scale_values, questions_dict, output_path,
                         filter_column=None, filter_value=None, title="",
                         raw_values=False):
    plt.rcParams.update({
        "font.family": "Georgia",
        "font.size": 14,
        "axes.titlesize": 18,
        "axes.labelsize": 16,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "legend.fontsize": 14,
    })

    df = pd.read_csv(file_path)
    if filter_column and filter_value:
        df = df[df[filter_column] == filter_value]

    df_filtered = df[list(questions_dict.keys())]
    df_filtered.columns = [questions_dict[c] for c in df_filtered.columns]

    if raw_values:
        df_filtered = _convert_raw_input(df_filtered, scale_values)

    ax = plot_likert.plot_likert(
        df_filtered,
        scale_values,
        plot_percentage=True,
        colors=plot_likert.colors.default_with_darker_neutral,
        figsize=(15, 8),
        title=title,
        xtick_interval=10,
    )

    for bars, text_color in zip(ax.containers[1:], ["white"] + ["black"] * 2 + ["white"] * 2):
        ax.bar_label(
            bars,
            label_type="center",
            fmt=lambda x: f"{round(x, 1):.0f}%" if round(x, 1).is_integer() else f"{round(x, 1):.1f}%",
            color=text_color,
            fontsize=9,
            fontweight="bold",
            path_effects=[PathEffects.withStroke(
                linewidth=1.5,
                foreground="white" if text_color == "black" else "black",
                alpha=1.0,
            )],
        )

    if ax.get_legend():
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18),
                  ncol=len(scale_values), frameon=True, title=None)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close()
    print(f"  saved {os.path.basename(output_path)}")


IMPORTANT_ELEMENTS = {
    "How important are the following elements in your architecture views? [Architectural components (for example code classes)]": "Architectural components",
    "How important are the following elements in your architecture views? [Connection/Interaction (for example HTTP calls)]": "Connection/Interaction",
    "How important are the following elements in your architecture views? [Layers (for example the front end)]": "Layers",
    "How important are the following elements in your architecture views? [Technologies (for example Kubernetes)]": "Technologies",
    "How important are the following elements in your architecture views? [Nested Components (for example elements of a layer)]": "Nested Components",
    "How important are the following elements in your architecture views? [Users (for example end users)]": "Users",
    "How important are the following elements in your architecture views? [Legends (for example meaning of the colors used)]": "Legends",
}

USAGE = {
    "Architecture views should use an informal notation (for example boxes and arrows, icons)": "Informal notation (Q7)",
    "Legends are not necessary in an architecture view": "Legends unnecessary (Q8)",
    "Architecture views should show the entire project and not just a portion of it": "Holistic overview (Q9)",
    "Architecture views should provide a high level overview of a project": "High-level overview (Q10)",
    "Design information and runtime information are equally important to be reported in architecture views": "Design and runtime balance (Q11)",
    "Technologies used in a project are important in architecture views": "Technologies importance (Q12)",
}

UTILITY = {
    "For which activity of the project lifecycle do you find architecture views most useful? (5-point usefulness grid) [Architecture design]": "Architecture design",
    "For which activity of the project lifecycle do you find architecture views most useful? (5-point usefulness grid) [Coding / implementation]": "Coding/implementation",
    "For which activity of the project lifecycle do you find architecture views most useful? (5-point usefulness grid) [Maintenance / operations]": "Maintenance/operations",
}

FEATURES = {
    "To which extent is it important to have versionable architecture views (version control with change tracking)?": "Versioning importance (Q24)",
    "To which extent is it important to have collaborative environment integration for architecture view editing?": "Collaboration importance (Q25)",
    "To which extent is it important to have ready to be-used architecture view templates?": "Ready-made templates (Q26)",
    "To which extent is it important to directly link architecture view elements to software artifact (for example code classes)?": "Element-artifact linkage (Q27)",
    "To which extend is it important to be able to automatically generate architecture views from the code?": "Code-driven views (Q28)",
}

# name, questions_dict, scale, raw_values
LIKERT_SPECS = [
    ("architecture-views-important-elements-likert", IMPORTANT_ELEMENTS, IMPORTANCE_SCALE, False),
    ("architecture-views-usage-likert", USAGE, ACCORDANCE_SCALE, True),
    ("architecture-views-utility-likert", UTILITY, IMPORTANCE_SCALE, False),
    ("architecture-views-features-likert", FEATURES, ACCORDANCE_SCALE, True),
]


def generate_all():
    out_dir = ensure_output_dir()
    print("Likert charts:")
    for name, questions, scale, raw in LIKERT_SPECS:
        generate_likert_plot(
            file_path=CODING_CSV,
            scale_values=scale,
            questions_dict=questions,
            output_path=os.path.join(out_dir, f"{name}.pdf"),
            filter_column=FILTER_COLUMN,
            filter_value=FILTER_VALUE,
            title="",
            raw_values=raw,
        )


if __name__ == "__main__":
    generate_all()
