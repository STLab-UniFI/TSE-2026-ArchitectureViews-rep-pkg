"""
Replication package entrypoint: regenerate every plot into ./plot.

Run from anywhere with the project venv:
    python generate_all.py

Individual figure families can also be run on their own, e.g.:
    python bar_charts.py
"""

import compat  # noqa: F401  -- pandas 3.0 compatibility patches (import first)

import alluvial_charts
import bar_charts
import likert_charts
import cumulative_response_time
import inter_rater
from config import OUTPUT_DIR


def main():
    print(f"Output directory: {OUTPUT_DIR}\n")
    alluvial_charts.generate_all()
    bar_charts.generate_all()
    likert_charts.generate_all()
    cumulative_response_time.generate_all()
    inter_rater.generate_all()
    print("\nDone. All figures are in ./plot")


if __name__ == "__main__":
    main()
