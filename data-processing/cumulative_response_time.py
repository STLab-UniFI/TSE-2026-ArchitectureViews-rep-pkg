"""Cumulative number of survey responses over time (drawn at the printed column width)."""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import figstyle
from config import CODING_CSV, ensure_output_dir

LINE_COLOR = "#4D4D4D"


def generate_all():
    out_dir = ensure_output_dir()
    output_path = os.path.join(out_dir, "response-time.pdf")

    figstyle.apply()

    df = pd.read_csv(CODING_CSV)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%m/%d/%Y %H:%M:%S")
    df = df.sort_values("Timestamp")
    df["Cumulative Count"] = range(1, len(df) + 1)

    fig, ax = plt.subplots(figsize=(figstyle.COLUMN_WIDTH, 2.0), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02)
    ax.plot(df["Timestamp"], df["Cumulative Count"], marker="o", markersize=2,
            linestyle="-", linewidth=0.9, color=LINE_COLOR)

    # Weekly ticks (same dates as before), shown as day and month.
    start_date, end_date = df["Timestamp"].min(), df["Timestamp"].max()
    ticks = pd.date_range(start=start_date, end=end_date, freq="W")
    if len(ticks) == 0 or ticks[0] != start_date:
        ticks = pd.Index([start_date]).append(ticks)
    ax.set_xticks(ticks, ticks.strftime("%d %b"), rotation=45, ha="right", rotation_mode="anchor")

    ax.set_xlabel("Date (December 2024 – February 2025)")
    ax.set_ylabel("Cumulative responses")
    ax.grid(True, color=figstyle.GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    fig.savefig(output_path, format="pdf")
    plt.close(fig)
    print("Cumulative response time:")
    print(f"  saved {os.path.basename(output_path)}")


if __name__ == "__main__":
    generate_all()
