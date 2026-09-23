"""
Cross-analysis of the notation-related answers (Q7, Q17, Q20).

For the respondents who declare the use of UML (Q17) it reports (i) how many of
them use at least one tool that enforces the syntax of a notation (Q20, i.e. a
tool classified as "Fixed Notation" in the tool classification) and (ii) how
they answered Q7 ("Architecture views should use an informal notation"),
comparing them with the remaining respondents. Results are printed and also
written to plot/notation-cross-analysis.txt.
"""

import os
import pandas as pd
from scipy.stats import mannwhitneyu

from config import (
    CODING_CSV,
    TOOL_CSV,
    FILTER_COLUMN,
    FILTER_VALUE,
    ensure_output_dir,
)

# Q17 code identifying the respondents who declare the use of UML.
UML_CODE = "UML"

# Tool labels that enforce the syntax of a notation but are absent from the
# tool classification (mentioned once, not traceable to a specific product).
# They are conservatively counted as notation-enforcing.
UNCLASSIFIED_ENFORCING = {"UML compiler"}

# 5-point Likert scale used in the survey.
AGREE = (4, 5)
DISAGREE = (1, 2)


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


def _pct(count, total):
    return f"{count} ({count / total * 100:.1f}%)"


def generate_all():
    out_dir = ensure_output_dir()
    report_path = os.path.join(out_dir, "notation-cross-analysis.txt")

    responses = pd.read_csv(CODING_CSV)
    responses = responses[responses[FILTER_COLUMN] == FILTER_VALUE].copy()

    q7 = _column(responses, "should use an informal notation")
    q17 = _column(responses, "any standard notation in your architecture views? If so, which ones? [CODED]")
    q20 = _column(responses, "Which tool do you use to create architecture views? (if any) [CODED]")

    tools = pd.read_csv(TOOL_CSV)
    classified = set(tools["TOOL"].str.strip())
    enforcing = set(
        tools.loc[tools["Notation Type"].str.strip() == "Fixed Notation", "TOOL"].str.strip()
    ) | UNCLASSIFIED_ENFORCING

    responses["uml"] = responses[q17].apply(lambda v: UML_CODE in _codes(v))
    responses["enforcing"] = responses[q20].apply(
        lambda v: any(tool in enforcing for tool in _codes(v))
    )
    responses["agrees"] = responses[q7].isin(AGREE)
    responses["disagrees"] = responses[q7].isin(DISAGREE)

    uml = responses[responses["uml"]]
    other = responses[~responses["uml"]]
    n_all, n_uml, n_other = len(responses), len(uml), len(other)

    test = mannwhitneyu(uml[q7], other[q7])

    unknown = sorted(
        {
            tool
            for value in responses[q20]
            for tool in _codes(value)
            if tool not in classified
        }
    )

    lines = [
        "Cross-analysis of Q7 (informal notation), Q17 (standard notations) and",
        "Q20 (tools used), over the respondents who passed the Q1 screening.",
        "",
        f"Valid respondents: {n_all}",
        f"Q7, agree or strongly agree (all respondents): {_pct(responses['agrees'].sum(), n_all)}",
        "",
        f"Respondents declaring the use of UML (Q17): {n_uml}",
        f"  no tool enforcing a notation (Q20):            {_pct((~uml['enforcing']).sum(), n_uml)}",
        f"  at least one notation-enforcing tool (Q20):    {_pct(uml['enforcing'].sum(), n_uml)}",
        f"  agree or strongly agree with Q7:               {_pct(uml['agrees'].sum(), n_uml)}",
        f"  disagree with Q7 and use an enforcing tool:    {_pct((uml['disagrees'] & uml['enforcing']).sum(), n_uml)}",
        "",
        f"Remaining respondents: {n_other}",
        f"  agree or strongly agree with Q7:               {_pct(other['agrees'].sum(), n_other)}",
        "",
        f"Mann-Whitney U on Q7 (UML vs. remaining respondents): "
        f"U = {test.statistic:.1f}, p = {test.pvalue:.3f}",
        "",
        "Tool labels mentioned in Q20 but absent from the tool classification "
        "(counted as non-enforcing unless listed in UNCLASSIFIED_ENFORCING):",
        "  " + (", ".join(unknown) if unknown else "none"),
    ]

    text = "\n".join(lines)
    print(text)
    with open(report_path, "w") as f:
        f.write(text + "\n")
    print(f"\n  saved {os.path.basename(report_path)}")


if __name__ == "__main__":
    generate_all()
