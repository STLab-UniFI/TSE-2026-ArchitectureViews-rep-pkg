# Data processing — figure generation

Self-contained code that regenerates every figure of the study from the survey
data in `data/`. One command produces all the plots into `plot/`.

For environment setup (virtual environment + dependencies) and the basic run
command, see the [top-level README](../README.md#reproducing-the-plots-data-processing).
The notes below cover the outputs and the technical details specific to this
code.

> These are the **automatically generated** figures. The few plots that were
> later refined by hand for the paper are *not* reproduced here.

## Modules

| File | Produces |
|------|----------|
| `generate_all.py` | entrypoint — runs all of the below |
| `alluvial_charts.py` (+ `alluvial_plot.py`) | tool-classification alluvial plots |
| `bar_charts.py` | all frequency bar charts |
| `likert_charts.py` | all diverging Likert plots |
| `cumulative_response_time.py` | responses-over-time plot |
| `inter_rater.py` | Cohen's kappa / Krippendorff's alpha report |
| `notation_cross_analysis.py` | Q7 × Q17 × Q20 notation cross-analysis report |
| `config.py` | shared paths and the respondent filter |
| `compat.py` | pandas >= 3.0 compatibility shims |

Each family can also be run on its own, e.g. `python bar_charts.py`.

## Outputs (`plot/`)

- **Alluvial:** `tool_classification_alluvial.pdf`,
  `tool_classification_alluvial-unweighted.pdf`
- **Likert:** `architecture-views-{important-elements,usage,utility,features}-likert.pdf`
- **Bar charts:** `roles`, `view-purposes`, `concernes`, `quality-attribute`,
  `standard-notations`, `additional-important-elements`, `tool-used`,
  `tool-features`, `challenges`, `intended-user`, `automatic-tool`,
  `automatable-aspect`, `view-changes`, `further-comments` (`.pdf`)
- **Cumulative responses:** `response-time.pdf`
- **Inter-rater agreement:** `inter-rater-agreement.txt`
- **Notation cross-analysis:** `notation-cross-analysis.txt`
