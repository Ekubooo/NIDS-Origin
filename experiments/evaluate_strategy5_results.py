"""
Evaluate Component 3 Strategy 5 artifacts and generate comparison figures.

This script does not train a model. It loads the Strategy 5 RF/preprocessor,
rebuilds the deterministic UNSW test split, runs Stress C for Strategy 5, and
then builds result-file-based comparison tables/figures.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("MPLCONFIGDIR", os.path.abspath(".matplotlib_cache"))

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import (
    ATTACK_COL,
    LABEL_COL,
    NUMERIC_FEATURES,
    SEED,
    UNSW_PATH,
)
from evaluation.plots import plot_degradation_curve
from preprocessing.preprocess import load_and_clean_data, clean_l7_proto, split_data
from robustness.stress_tests import run_stress_c


STRATEGY5_MODEL_PATH = "artifacts/strategy5_taichi_rf.joblib"
STRATEGY5_PREPROCESSOR_PATH = "artifacts/strategy5_preprocessor.joblib"
STRATEGY5_SUMMARY_PATH = "results/strategy5_summary.csv"
BASELINE_RESULTS_PATH = "results/baseline_results.csv"
BASELINE_STRESS_C_PATH = "results/stress_c_results.csv"


def _require(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file is missing: {path}")


def _ensure_dirs():
    os.makedirs("results", exist_ok=True)
    os.makedirs("reports/figures", exist_ok=True)


def load_raw_test_split():
    """Rebuild the deterministic raw UNSW test split used by existing scripts."""
    _require(UNSW_PATH)
    df = load_and_clean_data(UNSW_PATH)
    df = clean_l7_proto(df)

    y_full = df[ATTACK_COL]
    X_full = df.drop(columns=[ATTACK_COL, LABEL_COL])

    df_for_split = X_full.copy()
    df_for_split[ATTACK_COL] = y_full
    _, _, X_test, _, _, _ = split_data(df_for_split)

    y_test = X_test.pop(ATTACK_COL)
    class_names = sorted(y_full.unique())
    return X_test, y_test, class_names


def flatten_stress_c_results(results):
    rows = []
    for stress_type, payload in results.items():
        for level, macro_f1 in zip(payload["levels"], payload["macro_f1"]):
            rows.append({
                "method": "Strategy 5 (Taichi augmented RF)",
                "type": stress_type,
                "level": level,
                "macro_f1": round(float(macro_f1), 6),
            })
    return pd.DataFrame(rows)


def _stress_c_dict(df):
    label_map = {
        "noise": "Noise",
        "masking": "Masking",
        "dropout_top": "Dropout (top)",
        "dropout_bottom": "Dropout (bottom)",
    }
    out = {}
    for raw_type, label in label_map.items():
        sub = df[df["type"] == raw_type]
        out[label] = (sub["level"].tolist(), sub["macro_f1"].tolist())
    return out


def plot_stress_c_model_comparison(baseline_df, strategy5_df, save_path):
    types = ["noise", "masking", "dropout_top", "dropout_bottom"]
    titles = {
        "noise": "Gaussian Noise",
        "masking": "Random Masking",
        "dropout_top": "Dropout Top Features",
        "dropout_bottom": "Dropout Bottom Features",
    }

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.ravel()
    for ax, stress_type in zip(axes, types):
        base = baseline_df[baseline_df["type"] == stress_type]
        s5 = strategy5_df[strategy5_df["type"] == stress_type]
        ax.plot(base["level"], base["macro_f1"], marker="o", label="Baseline RF")
        ax.plot(s5["level"], s5["macro_f1"], marker="s", label="Strategy 5 RF")
        ax.set_title(titles[stress_type])
        ax.set_xlabel("Level")
        ax.set_ylabel("Macro-F1")
        ax.set_ylim(0, 0.75)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Stress C Comparison: Baseline RF vs Strategy 5")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_clean_comparison(baseline_results, strategy5_summary, save_path):
    rf = baseline_results[baseline_results["model"] == "RandomForest"].iloc[0]
    s5 = strategy5_summary.iloc[0]
    rows = pd.DataFrame([
        {
            "method": "Baseline RF",
            "macro_f1": float(rf["macro_f1"]),
            "weighted_f1": float(rf["weighted_f1"]),
        },
        {
            "method": "Strategy 5 RF",
            "macro_f1": float(s5["test_macro_f1"]),
            "weighted_f1": float(s5["test_weighted_f1"]),
        },
    ])

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(rows))
    width = 0.35
    ax.bar(x - width / 2, rows["macro_f1"], width, label="Macro-F1")
    ax.bar(x + width / 2, rows["weighted_f1"], width, label="Weighted-F1")
    ax.set_xticks(x)
    ax.set_xticklabels(rows["method"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Clean Test Comparison")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.4f", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def build_result_file_comparison():
    _require(BASELINE_RESULTS_PATH)
    _require(BASELINE_STRESS_C_PATH)
    _require(STRATEGY5_SUMMARY_PATH)
    _require("results/strategy5_stress_c.csv")

    baseline = pd.read_csv(BASELINE_RESULTS_PATH)
    baseline_stress_c = pd.read_csv(BASELINE_STRESS_C_PATH)
    strategy5 = pd.read_csv(STRATEGY5_SUMMARY_PATH)
    strategy5_stress_c = pd.read_csv("results/strategy5_stress_c.csv")

    rf = baseline[baseline["model"] == "RandomForest"].iloc[0]
    s5 = strategy5.iloc[0]

    clean_rows = pd.DataFrame([
        {
            "condition": "clean_test",
            "metric": "macro_f1",
            "baseline_rf": round(float(rf["macro_f1"]), 6),
            "strategy5_rf": round(float(s5["test_macro_f1"]), 6),
            "delta_strategy5_minus_baseline": round(float(s5["test_macro_f1"]) - float(rf["macro_f1"]), 6),
        },
        {
            "condition": "clean_test",
            "metric": "weighted_f1",
            "baseline_rf": round(float(rf["weighted_f1"]), 6),
            "strategy5_rf": round(float(s5["test_weighted_f1"]), 6),
            "delta_strategy5_minus_baseline": round(float(s5["test_weighted_f1"]) - float(rf["weighted_f1"]), 6),
        },
    ])

    stress_rows = baseline_stress_c.merge(
        strategy5_stress_c[["type", "level", "macro_f1"]],
        on=["type", "level"],
        how="inner",
        suffixes=("_baseline_rf", "_strategy5_rf"),
    )
    stress_rows = stress_rows.rename(columns={
        "macro_f1_baseline_rf": "baseline_rf",
        "macro_f1_strategy5_rf": "strategy5_rf",
    })
    stress_rows["condition"] = "stress_c_" + stress_rows["type"] + "_" + stress_rows["level"].astype(str)
    stress_rows["metric"] = "macro_f1"
    stress_rows["delta_strategy5_minus_baseline"] = (
        stress_rows["strategy5_rf"] - stress_rows["baseline_rf"]
    ).round(6)
    stress_rows = stress_rows[[
        "condition", "metric", "baseline_rf", "strategy5_rf",
        "delta_strategy5_minus_baseline",
    ]]

    comparison = pd.concat([clean_rows, stress_rows], ignore_index=True)
    comparison.to_csv("results/strategy5_comparison.csv", index=False)
    return baseline, baseline_stress_c, strategy5, strategy5_stress_c, comparison


def main():
    _ensure_dirs()
    _require(STRATEGY5_MODEL_PATH)
    _require(STRATEGY5_PREPROCESSOR_PATH)

    print("Loading Strategy 5 artifacts ...")
    model = joblib.load(STRATEGY5_MODEL_PATH)
    preprocessor = joblib.load(STRATEGY5_PREPROCESSOR_PATH)

    print("Rebuilding raw UNSW test split ...")
    X_test_raw, y_test, class_names = load_raw_test_split()

    n_numeric = len(NUMERIC_FEATURES)
    feature_importances = model.feature_importances_[:n_numeric]
    print("Running Strategy 5 Stress C ...")
    results = run_stress_c(
        X_test_raw=X_test_raw,
        y_test=y_test,
        preprocessor=preprocessor,
        model=model,
        class_names=class_names,
        feature_importances=feature_importances,
        numeric_feature_names=list(NUMERIC_FEATURES),
        seed=SEED,
    )

    strategy5_stress_c = flatten_stress_c_results(results)
    strategy5_stress_c.to_csv("results/strategy5_stress_c.csv", index=False)
    print("Saved: results/strategy5_stress_c.csv")

    plot_degradation_curve(
        _stress_c_dict(strategy5_stress_c),
        "reports/figures/strategy5_stress_c_degradation.png",
    )
    print("Saved: reports/figures/strategy5_stress_c_degradation.png")

    baseline, baseline_stress_c, strategy5, strategy5_stress_c, comparison = \
        build_result_file_comparison()
    print("Saved: results/strategy5_comparison.csv")

    plot_stress_c_model_comparison(
        baseline_stress_c,
        strategy5_stress_c,
        "reports/figures/strategy5_vs_baseline_stress_c.png",
    )
    print("Saved: reports/figures/strategy5_vs_baseline_stress_c.png")

    plot_clean_comparison(
        baseline,
        strategy5,
        "reports/figures/strategy5_clean_comparison.png",
    )
    print("Saved: reports/figures/strategy5_clean_comparison.png")

    print("\nResult-file comparison:")
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
