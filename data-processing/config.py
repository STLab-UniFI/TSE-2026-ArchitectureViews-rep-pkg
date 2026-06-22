"""Shared paths and constants for the replication package."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
OUTPUT_DIR = os.path.join(HERE, "plot")

CODING_CSV = os.path.join(DATA_DIR, "coding.csv")
TOOL_CSV = os.path.join(DATA_DIR, "tool-classification-occurrence.csv")
CODING1_CSV = os.path.join(DATA_DIR, "coding1.csv")
CODING2_CSV = os.path.join(DATA_DIR, "coding2.csv")

# Respondents are filtered to those who correctly identified what an
# architecture view is (same screening filter used in the original notebooks).
FILTER_COLUMN = "Which of the following sentences BEST describes an architecture view?"
FILTER_VALUE = "A graphical representation showing the structure of system components"


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR
