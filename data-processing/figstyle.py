"""
Shared style for all the figures of the paper.

Every figure is drawn at the size at which it is printed (IEEEtran column or
text width), so the font sizes below are the sizes readers see in the paper.
Include the PDFs with ``width=\\columnwidth`` or ``width=\\textwidth`` and no
further scaling.
"""

import matplotlib as mpl

# IEEEtran journal layout (letter paper): \columnwidth = 251 pt, \textwidth = 514 pt
COLUMN_WIDTH = 3.487  # inches
TEXT_WIDTH = 7.14     # inches

FONT_SIZE = 8         # tick labels, value labels, node labels, legends
TITLE_SIZE = 9        # axis titles, column headers

TEXT_COLOR = "#1A1A1A"
AXIS_COLOR = "#4D4D4D"
GRID_COLOR = "#DDDDDD"
BAR_COLOR = "#7F7F7F"

# Diverging palette (ColorBrewer RdBu, 5 classes, light-grey neutral): the two
# negative and the two positive levels have matching lightness, and every level
# gives a WCAG contrast of at least 5:1 with the label colour drawn on it.
LIKERT_COLORS = ["#CA0020", "#F4A582", "#D9D9D9", "#92C5DE", "#0571B0"]

# Sequential blues for categories of the same dimension (dark -> light).
BLUES = ["#0571B0", "#92C5DE", "#D1E5F0"]

# Fonts: Arial when installed, otherwise its metric-compatible clone.
SANS_FONTS = ["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"]


def apply():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": SANS_FONTS,
        "font.size": FONT_SIZE,
        "axes.labelsize": TITLE_SIZE,
        "axes.titlesize": TITLE_SIZE,
        "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE,
        "legend.fontsize": FONT_SIZE,
        "text.color": TEXT_COLOR,
        "axes.labelcolor": TEXT_COLOR,
        "xtick.color": TEXT_COLOR,
        "ytick.color": TEXT_COLOR,
        "axes.edgecolor": AXIS_COLOR,
        "axes.linewidth": 0.6,
        "axes.labelpad": 3,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "xtick.major.pad": 2,
        "ytick.major.pad": 2,
        "legend.frameon": False,
        "pdf.fonttype": 42,   # embed TrueType fonts (no Type 3), as IEEE requires
        "ps.fonttype": 42,
        "savefig.dpi": 300,
        "savefig.bbox": "standard",  # keep the exact figure size (no 'tight' cropping)
    })


def relative_luminance(hex_color):
    rgb = [int(hex_color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(hex_a, hex_b):
    la, lb = sorted([relative_luminance(hex_a), relative_luminance(hex_b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def text_color_on(fill_hex):
    """Black or white, whichever contrasts more with the fill."""
    return "white" if contrast_ratio(fill_hex, "#FFFFFF") > contrast_ratio(fill_hex, "#000000") else "black"
