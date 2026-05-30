"""
Create supplemental final-report figures.

Outputs:
  reports/figures_final/16_stress_b_feature_shift.png
  reports/figures_final/17_v3_data_quality_missing_inf.png
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from config import UNSW_PATH


FINAL_DIR = "reports/figures_final"
MANIFEST = os.path.join(FINAL_DIR, "figure_manifest.csv")


def _style():
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "figure.dpi": 160,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "font.size": 10,
    })


def plot_stress_b_feature_shift():
    """Plot top source-target shifted features from stress_b_feature_shift.csv."""
    path = "results/stress_b_feature_shift.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run experiments/analyze_stress_b_shift.py first."
        )

    df = pd.read_csv(path)
    top = df.sort_values("abs_standardized_mean_diff", ascending=False).head(12)
    top = top.iloc[::-1].copy()
    top["direction"] = np.where(top["standardized_mean_diff"] >= 0,
                                "Higher in CICIDS", "Higher in UNSW")

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = top["direction"].map({
        "Higher in CICIDS": "#4C78A8",
        "Higher in UNSW": "#F58518",
    })
    ax.barh(top["feature"], top["standardized_mean_diff"], color=colors, alpha=0.9)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Standardized Mean Difference (CICIDS - UNSW)")
    ax.set_ylabel("")
    ax.set_title("Stress B Feature Shift: UNSW Source vs CICIDS Target")
    xmin = min(top["standardized_mean_diff"].min() - 0.35, -0.5)
    xmax = max(top["standardized_mean_diff"].max() + 0.35, 0.5)
    ax.set_xlim(xmin, xmax)

    for y, val in enumerate(top["standardized_mean_diff"]):
        ha = "left" if val >= 0 else "right"
        offset = 0.03 if val >= 0 else -0.03
        ax.text(val + offset, y, f"{val:.2f}", va="center", ha=ha, fontsize=8)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#4C78A8", alpha=0.9),
        plt.Rectangle((0, 0), 1, 1, color="#F58518", alpha=0.9),
    ]
    ax.legend(handles, ["Higher in CICIDS", "Higher in UNSW"],
              loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    plt.tight_layout()

    out = os.path.join(FINAL_DIR, "16_stress_b_feature_shift.png")
    fig.savefig(out)
    plt.close(fig)
    return out


def compute_data_quality_counts():
    """Compute raw NaN, inf, and L7 non-integer counts from UNSW in chunks."""
    cols = ["SRC_TO_DST_SECOND_BYTES", "DST_TO_SRC_SECOND_BYTES", "L7_PROTO"]
    stats = {
        "SRC_TO_DST_SECOND_BYTES": {"raw_nan": 0, "inf": 0, "non_integer": 0},
        "DST_TO_SRC_SECOND_BYTES": {"raw_nan": 0, "inf": 0, "non_integer": 0},
        "L7_PROTO": {"raw_nan": 0, "inf": 0, "non_integer": 0},
    }

    for chunk in pd.read_csv(UNSW_PATH, usecols=cols, chunksize=500000,
                             low_memory=False):
        for col in cols:
            values = pd.to_numeric(chunk[col], errors="coerce")
            stats[col]["raw_nan"] += int(values.isna().sum())
            stats[col]["inf"] += int(np.isinf(values).sum())
            if col == "L7_PROTO":
                finite = values[np.isfinite(values)]
                stats[col]["non_integer"] += int(((finite % 1) != 0).sum())

    return pd.DataFrame([
        {"feature": feature, **counts}
        for feature, counts in stats.items()
    ])


def plot_data_quality():
    """Plot v3-specific data quality issues that preprocessing corrects."""
    df = compute_data_quality_counts()
    long = df.melt(id_vars="feature", var_name="issue", value_name="count")
    long = long[long["count"] > 0]

    issue_labels = {
        "raw_nan": "Raw NaN",
        "inf": "+/-inf",
        "non_integer": "Non-integer L7_PROTO",
    }
    long["issue_label"] = long["issue"].map(issue_labels)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    sns.barplot(data=long, x="feature", y="count", hue="issue_label",
                palette=["#4C78A8", "#F58518", "#54A24B"], ax=ax)
    ax.set_yscale("log")
    ax.set_xlabel("")
    ax.set_ylabel("Affected Values (log scale)")
    ax.set_title("NF-UQ-NIDS-v3 Data Quality Issues Handled Before Modeling")
    ax.tick_params(axis="x", rotation=20)

    for container in ax.containers:
        ax.bar_label(container, labels=[
            f"{int(v.get_height()):,}" if v.get_height() > 0 else ""
            for v in container
        ], fontsize=8, padding=2)

    ax.legend(title="")
    plt.tight_layout()

    out = os.path.join(FINAL_DIR, "17_v3_data_quality_missing_inf.png")
    fig.savefig(out)
    plt.close(fig)
    return out


def update_manifest(new_rows):
    """Append/update final figure manifest entries for supplemental figures."""
    if os.path.exists(MANIFEST):
        manifest = pd.read_csv(MANIFEST)
    else:
        manifest = pd.DataFrame(columns=["final_file", "source_file", "reason"])

    new_df = pd.DataFrame(new_rows)
    manifest = manifest[~manifest["final_file"].isin(new_df["final_file"])]
    manifest = pd.concat([manifest, new_df], ignore_index=True)
    manifest.to_csv(MANIFEST, index=False)


def main():
    os.makedirs(FINAL_DIR, exist_ok=True)
    _style()

    shift_fig = plot_stress_b_feature_shift()
    quality_fig = plot_data_quality()

    update_manifest([
        {
            "final_file": os.path.basename(shift_fig),
            "source_file": "results/stress_b_feature_shift.csv",
            "reason": "source-target feature shift required for Stress B distribution-shift analysis",
        },
        {
            "final_file": os.path.basename(quality_fig),
            "source_file": "data/NF-UNSW-NB15-v3.csv",
            "reason": "v3 data quality issues handled by preprocessing: NaN, inf, and non-integer L7_PROTO",
        },
    ])

    print(f"Saved: {shift_fig}")
    print(f"Saved: {quality_fig}")
    print(f"Updated: {MANIFEST}")


if __name__ == "__main__":
    main()
