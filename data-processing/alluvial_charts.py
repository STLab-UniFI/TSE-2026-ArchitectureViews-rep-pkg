"""
Alluvial (flow) plots of the tool classification, weighted by occurrence and as
plain unit counts. Uses the PublicationAlluvialPlot class in alluvial_plot.py.

The plots are drawn at the printed text width (see figstyle.py). Within each
dimension the categories use intensity levels of a single hue, from dark (the
first category below, which is also the most frequent one) to light.
"""

import os
from config import TOOL_CSV, ensure_output_dir
from alluvial_plot import PublicationAlluvialPlot
import figstyle

CATEGORY_ORDER = {
    "Notation Type": ["Free Form", "Fixed Notation"],
    "License Type": ["Free", "Freemium", "Commercial"],
    "Open Source": ["Yes", "No"],
    "Collaborative Model": ["Collaborative", "Single User"],
    "Environment": ["IDE-Integrated", "Standalone"],
    "Diagram-as-Code": ["Native", "No"],
}


def _make(use_weights, output_path, title):
    plotter = PublicationAlluvialPlot(
        TOOL_CSV, use_occurrence_weights=use_weights,
        figsize=(figstyle.TEXT_WIDTH, 3.5), dpi=300)
    plotter.customize_style(category_order=CATEGORY_ORDER)
    plotter.generate_plot(
        title=title, output_file=output_path, output_format="pdf", show_plot=False)
    print(f"  saved {os.path.basename(output_path)}")


def generate_all():
    out_dir = ensure_output_dir()
    print("Alluvial charts:")
    _make(True, os.path.join(out_dir, "tool_classification_alluvial.pdf"),
          "Tool Classification Analysis (Weighted by Occurrence)")
    _make(False, os.path.join(out_dir, "tool_classification_alluvial-unweighted.pdf"),
          "Tool Classification Analysis (Unit Count)")


if __name__ == "__main__":
    generate_all()
