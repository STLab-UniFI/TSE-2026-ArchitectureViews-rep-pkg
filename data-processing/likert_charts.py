"""
Diverging Likert plots for the survey's 5-point-scale questions.
All four plots (important elements, usage, utility, features) are produced in
one run. Some questions are stored as text labels and some as raw 1-5 integers
(``raw_values=True`` maps those to the scale labels first).

As in the plot_likert library used for the first version of the paper, each bar
is centred on the middle of the neutral category (x = 0) and percentages are
computed over the non-missing answers of each question. The bars are drawn
directly with matplotlib so that colours and value labels can be controlled:
  * a diverging palette whose negative and positive levels have matching
    lightness (figstyle.LIKERT_COLORS);
  * every percentage printed in black or white, whichever contrasts more with
    the segment, without outlines;
  * labels that do not fit inside their segment are moved next to the bar end
    (outermost segments) or above the bar with a short leader line.
Figures are drawn at the printed text width, so all text is printed at 8-9 pt.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

import figstyle
from config import CODING_CSV, FILTER_COLUMN, FILTER_VALUE, ensure_output_dir

IMPORTANCE_SCALE = ["Very unimportant", "Unimportant", "Neutral", "Important", "Very important"]
ACCORDANCE_SCALE = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

ROW_HEIGHT_IN = 0.38       # height of one question row
BAR_HEIGHT = 0.58          # bar thickness, as a fraction of the row
AXIS_LEGEND_IN = 0.75      # x tick labels, axis title and legend
MAX_LABEL_WIDTH_PT = 140   # longer question labels are wrapped
INSIDE_PAD_PT = 3          # horizontal room a label needs inside its segment
OUTSIDE_GAP_PT = 2.5       # gap between the bar end and an outside label
LEADER_PT = 2.5            # length of the leader line for labels above the bar


def _convert_raw_input(series, scale):
    return series.map({i + 1: level for i, level in enumerate(scale)})


def likert_percentages(df, questions_dict, scale, raw_values=False):
    """Percentage of each scale level per question (rows follow the dict order)."""
    rows = {}
    for column, label in questions_dict.items():
        answers = df[column].dropna()
        if raw_values:
            answers = _convert_raw_input(answers, scale)
        counts = answers.value_counts().reindex(scale, fill_value=0)
        rows[label] = counts / counts.sum() * 100
    return pd.DataFrame(rows).T[scale]


def format_percentage(value):
    rounded = round(value, 1)
    return f"{rounded:.0f}%" if float(rounded).is_integer() else f"{rounded:.1f}%"


def _wrap_to_width(fig, renderer, text, max_pt):
    def width(s):
        t = fig.text(0, 0, s, fontsize=figstyle.FONT_SIZE)
        w = t.get_window_extent(renderer).width * 72 / fig.dpi
        t.remove()
        return w
    if width(text) <= max_pt:
        return text
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and width(candidate) > max_pt:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return "\n".join(lines)


def _place_value_labels(fig, ax, pct, starts):
    """Draw the percentage of every segment and return the drawn artists.

    A label goes inside its segment when it fits. Otherwise it goes next to the
    bar end if the segment is the outermost one on that side, or above the bar
    with a short leader line (overlapping labels are pushed apart).
    """
    renderer = fig.canvas.get_renderer()
    x_a = ax.transData.transform((0, 0))[0]
    x_b = ax.transData.transform((1, 0))[0]
    pt_per_unit = (x_b - x_a) * 72 / fig.dpi

    def width_pt(text):
        probe = ax.text(0, 0, text, fontsize=figstyle.FONT_SIZE)
        width = probe.get_window_extent(renderer).width * 72 / fig.dpi
        probe.remove()
        return width

    artists = []
    for row in range(len(pct)):
        values = pct.iloc[row].values
        nonzero = np.flatnonzero(values > 0)
        if nonzero.size == 0:
            continue
        outer_left, outer_right = nonzero[0], nonzero[-1]
        above = []
        for level in nonzero:
            value = values[level]
            text = format_percentage(value)
            x0 = starts[row, level]
            text_pt = width_pt(text)
            if text_pt + INSIDE_PAD_PT <= value * pt_per_unit:
                fill = figstyle.LIKERT_COLORS[level]
                artists.append(ax.text(x0 + value / 2, row, text, ha="center", va="center_baseline",
                                       color=figstyle.text_color_on(fill),
                                       fontsize=figstyle.FONT_SIZE, zorder=4))
            elif level == outer_left:
                artists.append(ax.annotate(text, (x0, row), xytext=(-OUTSIDE_GAP_PT, 0),
                                           textcoords="offset points", ha="right",
                                           va="center_baseline", fontsize=figstyle.FONT_SIZE,
                                           zorder=4))
            elif level == outer_right:
                artists.append(ax.annotate(text, (x0 + value, row), xytext=(OUTSIDE_GAP_PT, 0),
                                           textcoords="offset points", ha="left",
                                           va="center_baseline", fontsize=figstyle.FONT_SIZE,
                                           zorder=4))
            else:
                center = x0 + value / 2
                above.append({"center": center, "x": center, "text": text, "w": text_pt})

        # Labels above the bar keep the segment order; overlapping ones are pushed apart.
        for _ in range(20):
            moved = False
            for i in range(1, len(above)):
                a, b = above[i - 1], above[i]
                min_dist = ((a["w"] + b["w"]) / 2 + 3) / pt_per_unit
                if b["x"] - a["x"] < min_dist:
                    push = (min_dist - (b["x"] - a["x"])) / 2
                    a["x"] -= push
                    b["x"] += push
                    moved = True
            if not moved:
                break
        top = row - BAR_HEIGHT / 2   # y axis is inverted: the bar top is at the smaller y
        for lab in above:
            artists.append(ax.annotate(
                lab["text"], (lab["center"], top),
                xytext=((lab["x"] - lab["center"]) * pt_per_unit, LEADER_PT),
                textcoords="offset points", ha="center", va="bottom",
                fontsize=figstyle.FONT_SIZE, zorder=4,
                # white box so that the dashed zero line does not cross the label
                bbox=dict(boxstyle="square,pad=0.1", facecolor="white", edgecolor="none"),
                arrowprops=dict(arrowstyle="-", lw=0.5, color=figstyle.AXIS_COLOR,
                                shrinkA=0, shrinkB=0)))
    return artists


def generate_likert_plot(file_path, scale_values, questions_dict, output_path,
                         filter_column=None, filter_value=None, title="",
                         raw_values=False, width=figstyle.TEXT_WIDTH):
    figstyle.apply()

    df = pd.read_csv(file_path)
    if filter_column and filter_value:
        df = df[df[filter_column] == filter_value]
    pct = likert_percentages(df, questions_dict, scale_values, raw_values)
    n_rows = len(pct)

    fig, ax = plt.subplots(figsize=(width, n_rows * ROW_HEIGHT_IN + AXIS_LEGEND_IN),
                           layout="constrained")
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02)

    # Centre each bar on the middle of the neutral category.
    left = -(pct.iloc[:, 0] + pct.iloc[:, 1] + pct.iloc[:, 2] / 2).values
    starts = np.zeros((n_rows, len(scale_values)))
    y = np.arange(n_rows)
    current = left.copy()
    for level, label in enumerate(scale_values):
        widths = pct[label].values
        starts[:, level] = current
        ax.barh(y, widths, left=current, height=BAR_HEIGHT, color=figstyle.LIKERT_COLORS[level],
                edgecolor="white", linewidth=0.4, zorder=2)
        current = current + widths
    right = current

    ax.axvline(0, color="#8C8C8C", linewidth=0.6, linestyle=(0, (3, 2)), zorder=1)

    # Question labels on the left, wrapped if very long.
    renderer = fig.canvas.get_renderer()
    labels = [_wrap_to_width(fig, renderer, str(lbl), MAX_LABEL_WIDTH_PT) for lbl in pct.index]
    ax.set_yticks(y, labels, linespacing=1.1)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.set_ylim(n_rows - 0.5, -0.5)

    # x axis in absolute percentages, ticks every 10%.
    lo = np.floor(left.min() / 10) * 10
    hi = np.ceil(right.max() / 10) * 10
    ticks = np.arange(lo, hi + 1, 10)
    ax.set_xticks(ticks, [f"{abs(t):.0f}%" for t in ticks])
    ax.set_xlabel("Percentage of responses")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    # a thin left axis line separates question labels from labels placed next to the bars
    ax.spines["left"].set_color("#BFBFBF")

    handles = [Patch(facecolor=c, edgecolor="none") for c in figstyle.LIKERT_COLORS]
    fig.legend(handles, scale_values, loc="outside lower center", ncol=len(scale_values),
               handlelength=1.2, handleheight=0.9, columnspacing=1.6, borderaxespad=0.2)
    if title:
        ax.set_title(title)

    # Value labels; widen the x range until the labels outside the bars fit.
    ax.set_xlim(left.min() - 1.5, right.max() + 1.5)
    for _ in range(4):
        fig.canvas.draw()
        artists = _place_value_labels(fig, ax, pct, starts)
        fig.canvas.draw()
        inv = ax.transData.inverted()
        boxes = [inv.transform(a.get_window_extent(renderer)) for a in artists]
        need_lo = min([b[0][0] for b in boxes] + [ax.get_xlim()[0]])
        need_hi = max([b[1][0] for b in boxes] + [ax.get_xlim()[1]])
        need_top = min([min(b[0][1], b[1][1]) for b in boxes] + [-0.5])
        x0, x1 = ax.get_xlim()
        fits = need_lo >= x0 and need_hi <= x1 and need_top >= ax.get_ylim()[1]
        if fits:
            break
        for a in artists:
            a.remove()
        ax.set_xlim(min(x0, need_lo - 1.5), max(x1, need_hi + 1.0))
        ax.set_ylim(n_rows - 0.5, min(-0.5, need_top - 0.05))

    fig.savefig(output_path)
    plt.close(fig)
    print(f"  saved {os.path.basename(output_path)}")
    return pct


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
    "To which extent is it important to directly link architecture view elements to software artifact (for example code classes)?": "Element–artifact linkage (Q27)",
    "To which extend is it important to be able to automatically generate architecture views from the code?": "Code-driven views (Q28)",
}

# name, questions_dict, scale, raw_values
# Q24-Q28 were answered on a 1-5 importance scale ("Not important" ... "Very
# important"), so they use the importance labels, like Q16 and Q18.
LIKERT_SPECS = [
    ("architecture-views-important-elements-likert", IMPORTANT_ELEMENTS, IMPORTANCE_SCALE, False),
    ("architecture-views-usage-likert", USAGE, ACCORDANCE_SCALE, True),
    ("architecture-views-utility-likert", UTILITY, IMPORTANCE_SCALE, False),
    ("architecture-views-features-likert", FEATURES, IMPORTANCE_SCALE, True),
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
