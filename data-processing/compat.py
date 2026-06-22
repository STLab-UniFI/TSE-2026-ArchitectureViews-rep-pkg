"""
Compatibility shims so the replication package runs on pandas >= 3.0.

pandas 3.0 removed ``DataFrame.applymap`` and no longer allows positional
integer indexing on a label-indexed Series (``series[0]``). The ``plot_likert``
0.5.0 library relies on both, so we patch them here at import time. Import this
module **before** importing/using ``plot_likert``.
"""

import pandas as pd


def apply_patches():
    # 1) DataFrame.applymap was removed in pandas 3.0 (use .map instead).
    if not hasattr(pd.DataFrame, "applymap"):
        pd.DataFrame.applymap = pd.DataFrame.map

    # 2) plot_likert uses positional Series indexing (series[0]) which raises a
    #    KeyError under pandas 3.0. Replace the offending helper with a version
    #    that computes percentages without positional indexing.
    #
    #    NB: the plot_likert package rebinds the name ``plot_likert.plot_likert``
    #    to the *function* (it shadows the submodule), so we must reach the real
    #    submodule object through sys.modules to patch its globals.
    try:
        import sys
        import plot_likert  # noqa: F401  -- ensures the submodule is imported
        _pl = sys.modules["plot_likert.plot_likert"]

        def _compute_counts_percentage(counts):
            return counts.divide(counts.sum(axis="columns"), axis="rows") * 100

        _pl._compute_counts_percentage = _compute_counts_percentage
    except Exception:
        # plot_likert not installed yet / not needed for this run.
        pass


apply_patches()
