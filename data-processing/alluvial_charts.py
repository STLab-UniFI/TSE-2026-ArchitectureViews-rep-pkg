"""
Alluvial (flow) plots of the tool classification, weighted by occurrence and as
plain unit counts. Uses the PublicationAlluvialPlot class in alluvial_plot.py.
"""

import os
from config import TOOL_CSV, ensure_output_dir
from alluvial_plot import PublicationAlluvialPlot


def _make(use_weights, output_path, title, font_family):
    plotter = PublicationAlluvialPlot(
        TOOL_CSV, use_occurrence_weights=use_weights, figsize=(14, 8), dpi=300)
    plotter.customize_style(
        font_family=font_family, font_size_title=18,
        color_palette="tab20", flow_alpha=0.7)
    plotter.generate_plot(
        title=title, output_file=output_path, output_format="pdf", show_plot=False)
    print(f"  saved {os.path.basename(output_path)}")


def generate_all():
    out_dir = ensure_output_dir()
    print("Alluvial charts:")
    _make(True, os.path.join(out_dir, "tool_classification_alluvial.pdf"),
          "Tool Classification Analysis (Weighted by Occurrence)", "Georgia")
    _make(False, os.path.join(out_dir, "tool_classification_alluvial-unweighted.pdf"),
          "Tool Classification Analysis (Unit Count)", "Times New Roman")


if __name__ == "__main__":
    generate_all()
