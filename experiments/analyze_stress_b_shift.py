"""
Stress B feature-distribution comparison.

Computes source-vs-target mean and variance for the shared v3 modeling
features using chunked reads. This makes the Stress B feature-shift discussion
reproducible instead of relying on hand-written notes.

Output:
  results/stress_b_feature_shift.csv
"""

import os
import sys
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from config import (
    UNSW_PATH, CICIDS_PATH, NUMERIC_FEATURES, PROTOCOL_FEATURES,
    CATEGORICAL_FEATURES,
)


FEATURE_COLUMNS = NUMERIC_FEATURES + PROTOCOL_FEATURES + CATEGORICAL_FEATURES


def _clean_feature_chunk(chunk):
    """Apply the same v3 feature cleaning needed for distribution statistics."""
    chunk = chunk.replace([np.inf, -np.inf], np.nan)
    if "L7_PROTO" in chunk.columns:
        chunk["L7_PROTO"] = chunk["L7_PROTO"].fillna(0).round()
    return chunk.apply(pd.to_numeric, errors="coerce").astype("float64")


def _init_stats():
    index = pd.Index(FEATURE_COLUMNS)
    return {
        "n_rows": 0,
        "count": pd.Series(0.0, index=index),
        "sum": pd.Series(0.0, index=index),
        "sumsq": pd.Series(0.0, index=index),
    }


def _update_stats(stats, chunk):
    chunk = _clean_feature_chunk(chunk)
    stats["n_rows"] += len(chunk)
    stats["count"] = stats["count"].add(chunk.count(), fill_value=0)
    stats["sum"] = stats["sum"].add(chunk.sum(skipna=True), fill_value=0)
    stats["sumsq"] = stats["sumsq"].add((chunk ** 2).sum(skipna=True), fill_value=0)


def compute_feature_stats(path, chunk_size, max_rows=None):
    """Compute per-feature count, missing, mean, and variance with chunked reads."""
    stats = _init_stats()
    rows_read = 0

    reader = pd.read_csv(
        path,
        usecols=FEATURE_COLUMNS,
        chunksize=chunk_size,
        low_memory=False,
    )
    for chunk_id, chunk in enumerate(reader, start=1):
        if max_rows is not None:
            remaining = max_rows - rows_read
            if remaining <= 0:
                break
            chunk = chunk.iloc[:remaining]

        _update_stats(stats, chunk)
        rows_read += len(chunk)

        if chunk_id == 1 or chunk_id % 10 == 0:
            print(f"  {os.path.basename(path)} chunk={chunk_id} rows={rows_read:,}", flush=True)

        if max_rows is not None and rows_read >= max_rows:
            break

    count = stats["count"]
    mean = stats["sum"] / count.replace(0, np.nan)
    variance = (stats["sumsq"] / count.replace(0, np.nan)) - (mean ** 2)
    variance = variance.clip(lower=0)
    missing = stats["n_rows"] - count

    return pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "rows": stats["n_rows"],
        "valid_count": count.reindex(FEATURE_COLUMNS).astype(int).values,
        "missing_after_inf_conversion": missing.reindex(FEATURE_COLUMNS).astype(int).values,
        "mean": mean.reindex(FEATURE_COLUMNS).values,
        "variance": variance.reindex(FEATURE_COLUMNS).values,
    })


def build_shift_table(source_stats, target_stats):
    """Merge source/target stats and rank features by standardized mean shift."""
    merged = source_stats.merge(
        target_stats,
        on="feature",
        suffixes=("_unsw", "_cicids"),
    )
    pooled_var = (merged["variance_unsw"] + merged["variance_cicids"]) / 2
    merged["mean_diff"] = merged["mean_cicids"] - merged["mean_unsw"]
    merged["abs_mean_diff"] = merged["mean_diff"].abs()
    merged["standardized_mean_diff"] = merged["mean_diff"] / np.sqrt(
        pooled_var.replace(0, np.nan)
    )
    merged["abs_standardized_mean_diff"] = merged["standardized_mean_diff"].abs()
    merged["variance_ratio_cicids_over_unsw"] = (
        merged["variance_cicids"] / merged["variance_unsw"].replace(0, np.nan)
    )

    cols = [
        "feature",
        "mean_unsw", "variance_unsw", "missing_after_inf_conversion_unsw",
        "mean_cicids", "variance_cicids", "missing_after_inf_conversion_cicids",
        "mean_diff", "abs_mean_diff", "standardized_mean_diff",
        "abs_standardized_mean_diff", "variance_ratio_cicids_over_unsw",
    ]
    return merged[cols].sort_values(
        ["abs_standardized_mean_diff", "abs_mean_diff"],
        ascending=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Compute Stress B source/target feature-shift statistics.")
    parser.add_argument("--chunk-size", type=int, default=500000)
    parser.add_argument("--max-source-rows", type=int, default=None,
                        help="Optional cap for quick diagnostics.")
    parser.add_argument("--max-target-rows", type=int, default=None,
                        help="Optional cap for quick diagnostics.")
    args = parser.parse_args()

    os.makedirs("results", exist_ok=True)

    print("Computing UNSW source feature statistics ...")
    source = compute_feature_stats(
        UNSW_PATH, chunk_size=args.chunk_size, max_rows=args.max_source_rows)

    print("\nComputing CICIDS target feature statistics ...")
    target = compute_feature_stats(
        CICIDS_PATH, chunk_size=args.chunk_size, max_rows=args.max_target_rows)

    shift = build_shift_table(source, target)
    out_path = "results/stress_b_feature_shift.csv"
    shift.to_csv(out_path, index=False)

    print(f"\nSaved: {out_path}")
    print("\nTop shifted features:")
    print(shift.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
