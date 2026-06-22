"""Cumulative number of survey responses over time."""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import CODING_CSV, ensure_output_dir


def generate_all():
    out_dir = ensure_output_dir()
    output_path = os.path.join(out_dir, "response-time.pdf")

    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 20,
        "axes.titlesize": 24,
        "axes.labelsize": 22,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "legend.fontsize": 18,
    })

    df = pd.read_csv(CODING_CSV)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%m/%d/%Y %H:%M:%S")
    df = df.sort_values("Timestamp")
    df["Cumulative Count"] = range(1, len(df) + 1)

    plt.figure(figsize=(12, 6))
    plt.plot(df["Timestamp"], df["Cumulative Count"], marker="o", linestyle="-",
             color="#808080", markerfacecolor="#808080", markeredgecolor="#808080",
             label="Cumulative Data Points")

    start_date, end_date = df["Timestamp"].min(), df["Timestamp"].max()
    ticks = pd.date_range(start=start_date, end=end_date, freq="W")
    if len(ticks) == 0 or ticks[0] != start_date:
        ticks = pd.Index([start_date]).append(ticks)

    plt.xticks(ticks, ticks.strftime("%d/%m/%Y"), rotation=45)
    plt.xlabel("Time (Weeks)")
    plt.ylabel("Cumulative Survey Responses")
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close()
    print("Cumulative response time:")
    print(f"  saved {os.path.basename(output_path)}")


if __name__ == "__main__":
    generate_all()
