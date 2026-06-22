"""
Inter-rater agreement (Cohen's kappa and Krippendorff's alpha) between the two
independent codings, computed per code for every [CODED] column. Results are
printed and also written to plot/inter-rater-agreement.txt.
"""

import os
import pandas as pd
from sklearn.metrics import cohen_kappa_score
import krippendorff

from config import CODING1_CSV, CODING2_CSV, ensure_output_dir


def _extract_coding(value):
    if pd.isna(value) or str(value).strip() == "":
        return set()
    return set(code.strip() for code in str(value).split(","))


def generate_all():
    out_dir = ensure_output_dir()
    report_path = os.path.join(out_dir, "inter-rater-agreement.txt")

    coding1 = pd.read_csv(CODING1_CSV)
    coding2 = pd.read_csv(CODING2_CSV)
    coded_cols = [c for c in coding1.columns if "[CODED]" in c]

    lines = []
    for col in coded_cols:
        lines.append(f"=== Inter-rater agreement of col: {col} ===")
        parsed1 = [_extract_coding(x) for x in coding1[col].tolist()]
        parsed2 = [_extract_coding(x) for x in coding2[col].tolist()]

        unique_codes = set()
        for codes in parsed1 + parsed2:
            unique_codes.update(codes)

        for code in sorted(unique_codes):
            bin1 = [1 if code in row else 0 for row in parsed1]
            bin2 = [1 if code in row else 0 for row in parsed2]
            try:
                kappa = cohen_kappa_score(bin1, bin2)
            except Exception:
                kappa = float("nan")
            try:
                alpha = krippendorff.alpha(
                    reliability_data=[bin1, bin2], level_of_measurement="nominal")
            except Exception:
                alpha = float("nan")
            lines.append(f"  {code}: kappa={kappa:.3f}  alpha={alpha:.3f}")
        lines.append("")

    text = "\n".join(lines)
    print("Inter-rater agreement:")
    print(text)
    with open(report_path, "w") as f:
        f.write(text)
    print(f"  saved {os.path.basename(report_path)}")


if __name__ == "__main__":
    generate_all()
