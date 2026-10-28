"""
Cross-analysis of possible contributing factors.

It reports, over the respondents who passed the Q1 screening:
  (1) whether the agreement with Q7 ("Architecture views should use an
      informal notation") depends on the respondent profile: experience (Q2),
      number of OSS projects (Q3), OSS engagement (Q4), organizational role
      (Q5, multi-label) and role towards architecture views (Q6);
  (2) whether the use of UML (Q17) depends on experience (Q2);
  (3) how the respondents who use (semi-)automatic tools (Q29) rate automatic
      generation from code (Q28) and view-to-code linking (Q27), compared with
      the other respondents.

Tests: Kruskal-Wallis with epsilon squared (Q7 across the levels of Q2, Q3,
Q4, Q6), Mann-Whitney U with Cliff's delta (two-group comparisons of 5-point
items) and chi-square (UML x experience). The analysis is exploratory and
correlational. Results are printed and also written to
plot/factors-cross-analysis.txt.
"""

import os

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal, mannwhitneyu

from config import (
    CODING_CSV,
    FILTER_COLUMN,
    FILTER_VALUE,
    ensure_output_dir,
)

AGREE = (4, 5)
DISAGREE = (1, 2)

EXPERIENCE_ORDER = ["0-1 years", "2-3 years", "4-6 years", "7-10 years", "11-15 years", "16+ years"]
PROJECTS_ORDER = ["1-3 projects", "4-10 projects", "11-20 projects", "21+ projects"]
ENGAGEMENT_ORDER = ["Occasional contributor", "Regular contributor", "Core/maintainer team member"]

# Q5 roles compared one-vs-rest (multi-label question).
ROLES = [
    "Software Developer",
    "Technical Lead",
    "Software Architect",
    "DevOps Engineer",
    "Product Owner",
    "Management",
    "Academic/Researcher",
    "Data/ML Engineer",
]

UML_CODE = "UML"  # Q17 code

MIN_GROUP = 5  # groups smaller than this are listed but excluded from the tests


def _column(frame, needle):
    """Return the first column whose name contains `needle`."""
    matches = [c for c in frame.columns if needle.lower() in c.lower()]
    if not matches:
        raise KeyError(f"no column matching {needle!r}")
    return matches[0]


def _codes(value):
    """Split a multi-label coded answer into its individual codes."""
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [code.strip() for code in str(value).split(",") if code.strip()]


def _agree(series):
    return np.mean(np.isin(series, AGREE)) * 100


def _negative(series):
    return np.mean(np.isin(series, DISAGREE)) * 100


def _cliffs_delta(a, b):
    a, b = np.asarray(a), np.asarray(b)
    greater = sum((x > b).sum() for x in a)
    lower = sum((x < b).sum() for x in a)
    return (greater - lower) / (len(a) * len(b))


def _q7_by_levels(lines, title, groups, q7, order):
    lines.append(f"{title}")
    samples = []
    for level in order:
        values = q7[groups == level]
        if len(values) == 0:
            continue
        note = "" if len(values) >= MIN_GROUP else "  (excluded from test)"
        lines.append(f"  {level:<45} n={len(values):>3}  agree={_agree(values):5.1f}%{note}")
        if len(values) >= MIN_GROUP:
            samples.append(values)
    h, p = kruskal(*samples)
    n_tested = sum(len(s) for s in samples)
    epsilon_sq = h / (n_tested - 1)  # epsilon squared effect size for Kruskal-Wallis
    lines.append(f"  Kruskal-Wallis: H = {h:.2f}, p = {p:.3f}, epsilon^2 = {epsilon_sq:.4f}")
    lines.append("")
    return p


def generate_all():
    out_dir = ensure_output_dir()
    report_path = os.path.join(out_dir, "factors-cross-analysis.txt")

    responses = pd.read_csv(CODING_CSV)
    responses = responses[responses[FILTER_COLUMN] == FILTER_VALUE].copy()
    n_all = len(responses)

    q2 = responses[_column(responses, "How many years have you been developing software?")]
    q3 = responses[_column(responses, "Number of OSS projects contributed to")]
    q4 = responses[_column(responses, "How would you describe your OSS contribution?")]
    q5 = responses[_column(responses, "current role(s) in your organization? [CODED]")].apply(_codes)
    q6 = responses[_column(responses, "primary role in relation to architecture views")]
    q7 = responses[_column(responses, "should use an informal notation")].astype(int)
    q17 = responses[_column(responses, "any standard notation in your architecture views? If so, which ones? [CODED]")].apply(_codes)
    q27 = responses[_column(responses, "directly link architecture view elements")].astype(int)
    q28 = responses[_column(responses, "automatically generate architecture views from the code")].astype(int)
    q29 = responses[_column(responses, "Do you use any (semi-)automatic tool")].eq("Yes")

    lines = [
        "Cross-analysis of possible contributing factors (exploratory, correlational),",
        "over the respondents who passed the Q1 screening.",
        "",
        f"Valid respondents: {n_all}",
        f"Q7, agree or strongly agree (all respondents): {_agree(q7):.1f}%",
        "",
        "(1) Agreement with Q7 by respondent profile",
        "",
    ]

    profile_p = []
    profile_p.append(_q7_by_levels(lines, "Experience (Q2)", q2, q7, EXPERIENCE_ORDER))
    profile_p.append(_q7_by_levels(lines, "OSS projects (Q3)", q3, q7, PROJECTS_ORDER))
    profile_p.append(_q7_by_levels(lines, "OSS engagement (Q4)", q4, q7, ENGAGEMENT_ORDER))
    profile_p.append(_q7_by_levels(lines, "Role towards architecture views (Q6)", q6, q7, sorted(q6.unique())))

    lines.append("Organizational role (Q5, one-vs-rest, Mann-Whitney U)")
    for role in ROLES:
        mask = q5.apply(lambda codes, role=role: role in codes)
        a, b = q7[mask], q7[~mask]
        p = mannwhitneyu(a, b).pvalue
        profile_p.append(p)
        lines.append(
            f"  {role:<22} n={len(a):>3}  agree={_agree(a):5.1f}% vs {_agree(b):5.1f}%  "
            f"delta={_cliffs_delta(a, b):+.2f}  p={p:.3f}"
        )
    lines += ["", f"Smallest p-value across all profile comparisons: {min(profile_p):.3f}", ""]

    lines.append("(2) Use of UML (Q17) by experience (Q2)")
    uml = q17.apply(lambda codes: UML_CODE in codes)
    for level in EXPERIENCE_ORDER:
        mask = q2 == level
        if mask.sum():
            lines.append(f"  {level:<12} n={mask.sum():>3}  UML={uml[mask].mean() * 100:5.1f}%")
    table = pd.crosstab(q2, uml)
    table = table[table.sum(axis=1) >= MIN_GROUP]
    chi2, p, _, _ = chi2_contingency(table)
    lines.append(f"  Chi-square (levels with n >= {MIN_GROUP}): chi2 = {chi2:.2f}, p = {p:.3f}")
    junior = q2.isin(EXPERIENCE_ORDER[:3])   # up to 6 years
    senior = q2.isin(EXPERIENCE_ORDER[4:])   # more than 10 years
    for label, mask in (("up to 6 years", junior), ("more than 10 years", senior)):
        lines.append(
            f"  {label:<18} n={mask.sum():>3}  UML={uml[mask].mean() * 100:5.1f}%  "
            f"Q7 agree={_agree(q7[mask]):5.1f}%"
        )
    lines.append("")

    lines.append("(3) Automation users (Q29 = Yes) vs. other respondents")
    for label, item in (("Q28 automatic generation from code", q28), ("Q27 linking view elements to code", q27)):
        a, b = item[q29], item[~q29]
        p = mannwhitneyu(a, b).pvalue
        lines.append(
            f"  {label}: important {_agree(a):.1f}% vs {_agree(b):.1f}%, "
            f"unimportant {_negative(a):.1f}% vs {_negative(b):.1f}% "
            f"(n = {len(a)} vs {len(b)}; Mann-Whitney U p = {p:.5f}, delta = {_cliffs_delta(a, b):+.2f})"
        )

    text = "\n".join(lines)
    print(text)
    with open(report_path, "w") as f:
        f.write(text + "\n")
    print(f"\n  saved {os.path.basename(report_path)}")


if __name__ == "__main__":
    generate_all()
