"""
Cross-analysis of "when what is important".

It relates the perceived usefulness of architectural views across the three
lifecycle activities of Q16 (architecture design, coding/implementation,
maintenance/operations) to the preferences on view design (Q7-Q12), the
importance of view elements (Q18), and the importance of tool features
(Q24-Q28).

Results are printed and written to plot/lifecycle-cross-analysis.txt.

Added during first round of revision
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

try:  # inside data-processing/ of the replication package
    from config import CODING_CSV, FILTER_COLUMN, FILTER_VALUE, ensure_output_dir
except ImportError:  # standalone use
    CODING_CSV = None
    FILTER_COLUMN = "Which of the following sentences BEST describes an architecture view?"
    FILTER_VALUE = "A graphical representation showing the structure of system components"

    def ensure_output_dir():
        return os.getcwd()


LEVELS = {
    "Very unimportant": 1,
    "Unimportant": 2,
    "Neutral": 3,
    "Important": 4,
    "Very important": 5,
}

ACTIVITIES = {  # label: (column needle, threshold defining the "values" group)
    "Architecture design": ("[Architecture design]", 5),
    "Coding / implementation": ("[Coding / implementation]", 4),
    "Maintenance / operations": ("[Maintenance / operations]", 4),
}

ITEMS = {  # label: column needle
    "Q7  Informal notation": "should use an informal notation",
    "Q8  Legends not necessary": "Legends are not necessary",
    "Q9  Entire project": "should show the entire project",
    "Q10 High-level overview": "should provide a high level overview",
    "Q11 Design and runtime info": "Design information and runtime information",
    "Q12 Technologies": "Technologies used in a project are important",
    "Q18 Architectural components": "[Architectural components",
    "Q18 Connection/Interaction": "[Connection/Interaction",
    "Q18 Layers": "[Layers",
    "Q18 Technologies": "[Technologies (for example",
    "Q18 Nested components": "[Nested Components",
    "Q18 Users": "[Users",
    "Q18 Legends": "[Legends",
    "Q24 Versioning": "versionable architecture views",
    "Q25 Collaborative editing": "collaborative environment integration",
    "Q26 Templates": "ready to be-used architecture view templates",
    "Q27 Linking to code": "directly link architecture view elements",
    "Q28 Automatic generation": "automatically generate architecture views",
}

FAMILIES = {  # question families used to rank the items within each group
    "Design preferences (Q7-Q12)": [k for k in ITEMS if k.split()[0] in ("Q7", "Q8", "Q9", "Q10", "Q11", "Q12")],
    "View elements (Q18)": [k for k in ITEMS if k.startswith("Q18")],
    "Tool features (Q24-Q28)": [k for k in ITEMS if k.split()[0] in ("Q24", "Q25", "Q26", "Q27", "Q28")],
}


def _column(frame, needle):
    """Return the first column whose name contains `needle`."""
    matches = [c for c in frame.columns if needle.lower() in c.lower()]
    if not matches:
        raise KeyError(f"no column matching {needle!r}")
    return matches[0]


def _score(series):
    """Map a 5-point answer (label or number) to 1-5."""
    mapped = series.map(LEVELS)
    return mapped if mapped.notna().any() else pd.to_numeric(series, errors="coerce")


def _codes(value):
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [code.strip() for code in str(value).split(",") if code.strip()]


def _cliffs_delta(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    greater = (a[:, None] > b[None, :]).sum()
    less = (a[:, None] < b[None, :]).sum()
    return (greater - less) / (len(a) * len(b))


def _contrast(group, item):
    """Compare `item` between respondents in `group` (bool) and the others."""
    data = pd.DataFrame({"g": group, "x": item}).dropna()
    inside, outside = data.loc[data["g"], "x"], data.loc[~data["g"], "x"]
    test = stats.mannwhitneyu(inside, outside)
    return {
        "n_in": len(inside),
        "n_out": len(outside),
        "pct_in": (inside >= 4).mean() * 100,
        "pct_out": (outside >= 4).mean() * 100,
        "delta": _cliffs_delta(inside, outside),
        "p": test.pvalue,
    }


def _partial_spearman(frame, x, y, covariates):
    """Spearman correlation of x and y controlling for `covariates`."""
    ranks = frame[[x, y] + covariates].dropna().rank()
    design = np.column_stack([np.ones(len(ranks))] + [ranks[c] for c in covariates])
    res_x = ranks[x] - design @ np.linalg.lstsq(design, ranks[x], rcond=None)[0]
    res_y = ranks[y] - design @ np.linalg.lstsq(design, ranks[y], rcond=None)[0]
    r = np.corrcoef(res_x, res_y)[0, 1]
    dof = len(ranks) - 2 - len(covariates)
    t = r * np.sqrt(dof / (1 - r ** 2))
    return r, 2 * stats.t.sf(abs(t), dof)


def _benjamini_hochberg(pvalues):
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
    out = np.empty_like(adjusted)
    out[order] = adjusted
    return out


def generate_all(csv_path=None, report_path=None):
    csv_path = csv_path or CODING_CSV
    report_path = report_path or os.path.join(ensure_output_dir(), "lifecycle-cross-analysis.txt")

    responses = pd.read_csv(csv_path)
    responses = responses[responses[FILTER_COLUMN] == FILTER_VALUE].copy()

    scores = pd.DataFrame(index=responses.index)
    for label, (needle, _) in ACTIVITIES.items():
        scores[label] = _score(responses[_column(responses, needle)])
    for label, needle in ITEMS.items():
        scores[label] = _score(responses[_column(responses, needle)])

    lines = [
        "Cross-analysis of the lifecycle activities of Q16 with Q7-Q12, Q18, and Q24-Q28,",
        "over the respondents who passed the Q1 screening.",
        f"Valid respondents: {len(responses)}",
        "Percentages: share of 4-5 answers over the respondents who rated the item",
        "(Q8 is negatively worded: its share is the agreement that legends are NOT necessary).",
        "",
    ]

    for activity, (_, threshold) in ACTIVITIES.items():
        group = scores[activity] >= threshold
        label = "very important" if threshold == 5 else "important or very important"
        lines.append(f"== {activity}: respondents rating it {label} ({int(group.sum())}) vs. the others ({int((~group).sum())})")
        for item in ITEMS:
            c = _contrast(group, scores[item])
            lines.append(
                f"  {item:30s} {c['pct_in']:5.1f}% vs {c['pct_out']:5.1f}%   "
                f"Cliff's delta = {c['delta']:+.2f}   Mann-Whitney p = {c['p']:.4f}"
            )
        lines.append("")

    lines.append("== Ranking within each of the six groups (three activities x two groups): top 3 items per question family")
    for activity, (_, threshold) in ACTIVITIES.items():
        inside = scores[activity] >= threshold
        for name, mask in (("values views for it", inside), ("others", ~inside)):
            lines.append(f"  -- {activity}, {name} ({int(mask.sum())})")
            for family, members in FAMILIES.items():
                shares = sorted(
                    ((((scores.loc[mask, m].dropna()) >= 4).mean() * 100, m) for m in members),
                    reverse=True,
                )
                ranking = " > ".join(f"{' '.join(m.split())} {s:.1f}%" for s, m in shares[:3])
                lines.append(f"     {family:28s} {ranking}")
    lines.append("")

    rows = []
    activities = list(ACTIVITIES)
    for activity in activities:
        others = [a for a in activities if a != activity]
        for item in ITEMS:
            r, p = _partial_spearman(scores, activity, item, others)
            rows.append((activity, item, r, p))
    partial = pd.DataFrame(rows, columns=["activity", "item", "rho", "p"])
    partial["q"] = _benjamini_hochberg(partial["p"])
    lines.append("== Partial Spearman rho (activity vs. item, controlling for the other two activities)")
    lines.append(f"   Benjamini-Hochberg correction over {len(partial)} pairs; * = q < 0.05")
    header = "  " + " " * 30 + "".join(f"{a.split(' ')[0]:>22s}" for a in activities)
    lines.append(header)
    for item in ITEMS:
        cells = []
        for activity in activities:
            row = partial[(partial["activity"] == activity) & (partial["item"] == item)].iloc[0]
            cells.append(f"{row['rho']:+.3f}{'*' if row['q'] < 0.05 else ' '} (q={row['q']:.3f})")
        lines.append(f"  {item:30s}" + "".join(f"{c:>22s}" for c in cells))

    text = "\n".join(lines)
    print(text)
    with open(report_path, "w") as f:
        f.write(text + "\n")
    print(f"\n  saved {report_path}")


if __name__ == "__main__":
    generate_all(*sys.argv[1:3])
