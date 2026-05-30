"""
Rebuild the final Stress C degradation figure from result CSV data.

The final report figure should include every degradation type stored in
results/stress_c_results.csv, including the "drop least important features"
condition that is useful as a near-control comparison.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RESULT_PATH = "results/stress_c_results.csv"
IMPROVED_PATH = "reports/figures_improved/stress_c_degradation_by_type.png"
FINAL_PATH = "reports/figures_final/10_stress_c_degradation_by_type.png"
CLEAN_F1 = 0.6774


PANEL_META = [
    ("noise", "Gaussian noise", "#D94E4E"),
    ("masking", "Random masking", "#F58518"),
    ("dropout_top", "Drop most important features", "#D94E4E"),
    ("dropout_bottom", "Drop least important features", "#4C78A8"),
]


def _severity_value(level):
    if "=" in level:
        return float(level.split("=", 1)[1])
    if level.startswith("p"):
        return float(level.split()[-1])
    if level.startswith("k"):
        return int(level.split()[-1])
    return level


def main():
    if not os.path.exists(RESULT_PATH):
        raise FileNotFoundError(f"{RESULT_PATH} not found")

    df = pd.read_csv(RESULT_PATH)
    present_types = set(df["type"].unique())
    expected_types = {item[0] for item in PANEL_META}
    missing = expected_types - present_types
    if missing:
        raise ValueError(f"Missing Stress C degradation type(s): {sorted(missing)}")

    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "figure.dpi": 160,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "font.size": 10,
    })

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2), sharey=True)
    fig.suptitle("Stress C: Performance Drops Differ by Degradation Type", fontsize=15)

    for ax, (deg_type, title, color) in zip(axes, PANEL_META):
        subset = df[df["type"] == deg_type].copy()
        subset["severity_value"] = subset["level"].map(_severity_value)
        subset = subset.sort_values("severity_value")

        ax.plot(subset["level"], subset["macro_f1"],
                marker="o", color=color, linewidth=2.4)
        for _, row in subset.iterrows():
            ax.text(row["level"], row["macro_f1"] + 0.03,
                    f"{row['macro_f1']:.2f}", ha="center", fontsize=8)

        ax.axhline(CLEAN_F1, color="#2F8F5B", linestyle="--",
                   linewidth=1.5, label="Clean RF")
        ax.set_title(title)
        ax.set_xlabel("Severity")
        ax.set_ylim(0, 0.84)
        ax.tick_params(axis="x", rotation=0)

    axes[0].set_ylabel("Macro-F1")
    axes[-1].legend(loc="upper right", frameon=False)
    plt.tight_layout(rect=[0, 0, 1, 0.92])

    for path in [IMPROVED_PATH, FINAL_PATH]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path)

    plt.close(fig)
    print(f"Saved: {IMPROVED_PATH}")
    print(f"Saved: {FINAL_PATH}")


if __name__ == "__main__":
    main()
