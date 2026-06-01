"""
Component 3 Strategy 5: independent Taichi-augmented RandomForest training.

This script does not read or overwrite artifacts/best_model.joblib. It trains a
new RandomForest on a newly fitted preprocessor plus Taichi-augmented transformed
features, then saves Strategy 5-specific artifacts only.

Usage:
  python experiments/run_strategy5_taichi_aug.py --taichi-aug-type fusion
  python experiments/run_strategy5_taichi_aug.py --train-sample-frac 0.01 --taichi-aug-ratio 0.1
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedShuffleSplit

from config import (
    ATTACK_COL,
    LABEL_COL,
    NUMERIC_FEATURES,
    PROTOCOL_FEATURES,
    CATEGORICAL_FEATURES,
    SEED,
    UNSW_PATH,
)
from evaluation.metrics import macro_f1_score, weighted_f1_score
from preprocessing.preprocess import (
    build_preprocessor,
    clean_l7_proto,
    fit_preprocessor,
    load_and_clean_data,
    split_data,
)
from robustness.taichi_augmenter import TaichiGPUAugmenter


def _require_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required data file is missing: {path}. "
            "Strategy 5 needs the raw UNSW CSV but does not require pre-trained artifacts."
        )


def _stratified_sample(X, y, train_sample_frac=1.0, max_train_samples=None, seed=SEED):
    n = len(y)
    target_n = n

    if train_sample_frac is not None and train_sample_frac < 1.0:
        if train_sample_frac <= 0:
            raise ValueError("--train-sample-frac must be in (0, 1].")
        target_n = min(target_n, max(1, int(n * train_sample_frac)))

    if max_train_samples is not None:
        if max_train_samples <= 0:
            raise ValueError("--max-train-samples must be positive.")
        target_n = min(target_n, int(max_train_samples))

    if target_n >= n:
        return X, y

    n_classes = y.nunique() if hasattr(y, "nunique") else len(set(y))
    if target_n < n_classes:
        raise ValueError(
            f"Requested training sample cap ({target_n}) is smaller than the "
            f"number of classes ({n_classes}); stratified sampling would drop classes."
        )

    splitter = StratifiedShuffleSplit(n_splits=1, train_size=target_n, random_state=seed)
    idx, _ = next(splitter.split(X, y))
    if hasattr(X, "iloc"):
        X_sampled = X.iloc[idx].copy()
    else:
        X_sampled = X[idx]
    y_sampled = y.iloc[idx].copy() if hasattr(y, "iloc") else y[idx]
    return X_sampled, y_sampled


def prepare_strategy5_data(train_sample_frac=1.0, max_train_samples=None):
    """Load raw UNSW data, split, fit a fresh preprocessor, and transform splits."""
    _require_file(UNSW_PATH)

    print(f"Loading {UNSW_PATH} ...")
    df = load_and_clean_data(UNSW_PATH)
    df = clean_l7_proto(df)

    y_full = df[ATTACK_COL]
    X_full = df.drop(columns=[ATTACK_COL, LABEL_COL])

    df_for_split = X_full.copy()
    df_for_split[ATTACK_COL] = y_full
    X_train, X_val, X_test, _, _, _ = split_data(df_for_split)

    y_train = X_train.pop(ATTACK_COL)
    y_val = X_val.pop(ATTACK_COL)
    y_test = X_test.pop(ATTACK_COL)

    X_train, y_train = _stratified_sample(
        X_train,
        y_train,
        train_sample_frac=train_sample_frac,
        max_train_samples=max_train_samples,
        seed=SEED,
    )

    print(f"Strategy 5 train samples after optional sampling: {len(y_train):,}")
    print("Fitting Strategy 5 preprocessor on Strategy 5 training split ...")
    preprocessor = build_preprocessor()
    preprocessor = fit_preprocessor(preprocessor, X_train)

    print("Transforming train / val / test ...")
    X_train_t = preprocessor.transform(X_train)
    X_val_t = preprocessor.transform(X_val)
    X_test_t = preprocessor.transform(X_test)

    expected_features = (
        len(NUMERIC_FEATURES) + len(PROTOCOL_FEATURES) + len(CATEGORICAL_FEATURES)
    )
    if X_train_t.shape[1] != expected_features:
        raise RuntimeError(
            f"Unexpected transformed feature count: got {X_train_t.shape[1]}, "
            f"expected {expected_features}."
        )

    return {
        "X_train": X_train_t,
        "X_val": X_val_t,
        "X_test": X_test_t,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
        "preprocessor": preprocessor,
        "class_names": sorted(y_train.unique()),
    }


def train_strategy5_model(X_train_aug, y_train_aug, args):
    model = RandomForestClassifier(
        n_estimators=args.rf_n_estimators,
        max_depth=args.rf_max_depth,
        min_samples_leaf=args.rf_min_samples_leaf,
        min_samples_split=args.rf_min_samples_split,
        class_weight="balanced",
        random_state=SEED,
        n_jobs=args.rf_n_jobs,
    )
    model.fit(X_train_aug, y_train_aug)
    return model


def evaluate_model(model, X, y, split_name):
    t0 = time.time()
    y_pred = model.predict(X)
    infer_s = time.time() - t0
    return {
        f"{split_name}_accuracy": float(accuracy_score(y, y_pred)),
        f"{split_name}_macro_f1": float(macro_f1_score(y, y_pred)),
        f"{split_name}_weighted_f1": float(weighted_f1_score(y, y_pred)),
        f"{split_name}_inference_s": float(infer_s),
    }


def save_outputs(model, preprocessor, config, summary):
    os.makedirs("artifacts", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    joblib.dump(model, "artifacts/strategy5_taichi_rf.joblib")
    joblib.dump(preprocessor, "artifacts/strategy5_preprocessor.joblib")

    with open("artifacts/strategy5_config.json", "w") as f:
        json.dump(config, f, indent=2)

    pd.DataFrame([summary]).to_csv("results/strategy5_summary.csv", index=False)

    print("Saved: artifacts/strategy5_taichi_rf.joblib")
    print("Saved: artifacts/strategy5_preprocessor.joblib")
    print("Saved: artifacts/strategy5_config.json")
    print("Saved: results/strategy5_summary.csv")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--taichi-aug-type", choices=["fusion", "noise", "state", "mixup"],
                        default="fusion")
    parser.add_argument("--taichi-aug-ratio", type=float, default=1.0,
                        help="Augmented sample count as a fraction of Strategy 5 train rows.")
    parser.add_argument("--taichi-noise-std", type=float, default=0.05)
    parser.add_argument("--taichi-state-strength", type=float, default=0.35)
    parser.add_argument("--taichi-device-memory-gb", type=float, default=4.0)
    parser.add_argument("--taichi-cache-dir", default=".taichi_cache",
                        help="Project-local Taichi cache directory.")
    parser.add_argument("--train-sample-frac", type=float, default=1.0,
                        help="Optional stratified fraction of the train split for quick checks.")
    parser.add_argument("--max-train-samples", type=int, default=None,
                        help="Optional stratified cap on train rows before augmentation.")
    parser.add_argument("--rf-n-estimators", type=int, default=100)
    parser.add_argument("--rf-max-depth", type=int, default=None)
    parser.add_argument("--rf-min-samples-leaf", type=int, default=2)
    parser.add_argument("--rf-min-samples-split", type=int, default=5)
    parser.add_argument("--rf-n-jobs", type=int, default=-1)
    return parser.parse_args()


def main():
    args = parse_args()
    t0 = time.time()

    print("=" * 60)
    print("Component 3 Strategy 5: Taichi-Augmented RandomForest")
    print("=" * 60)
    print("This run is independent and will not read/overwrite best_model.joblib.")

    data = prepare_strategy5_data(
        train_sample_frac=args.train_sample_frac,
        max_train_samples=args.max_train_samples,
    )

    augmenter = TaichiGPUAugmenter(
        device_memory_gb=args.taichi_device_memory_gb,
        mutable_features=len(NUMERIC_FEATURES) + len(PROTOCOL_FEATURES),
        seed=SEED,
        cache_dir=args.taichi_cache_dir,
    )

    aug_t0 = time.time()
    try:
        X_train_aug, y_train_aug = augmenter.run(
            data["X_train"],
            data["y_train"],
            aug_type=args.taichi_aug_type,
            ratio=args.taichi_aug_ratio,
            noise_std=args.taichi_noise_std,
            state_strength=args.taichi_state_strength,
        )
    except RuntimeError as exc:
        raise SystemExit(f"Strategy 5 augmentation failed: {exc}") from None
    augmentation_s = time.time() - aug_t0

    print(
        "Augmented training matrix: "
        f"{data['X_train'].shape[0]:,} -> {X_train_aug.shape[0]:,} rows, "
        f"{X_train_aug.shape[1]} features"
    )

    train_t0 = time.time()
    model = train_strategy5_model(X_train_aug, y_train_aug, args)
    train_s = time.time() - train_t0

    val_metrics = evaluate_model(model, data["X_val"], data["y_val"], "val")
    test_metrics = evaluate_model(model, data["X_test"], data["y_test"], "test")

    total_s = time.time() - t0
    summary = {
        "method": "Strategy 5 (Taichi augmented RF)",
        "augmentation_type": args.taichi_aug_type,
        "augmentation_ratio": args.taichi_aug_ratio,
        "original_train_samples": int(data["X_train"].shape[0]),
        "augmented_train_samples": int(X_train_aug.shape[0]),
        "n_features": int(X_train_aug.shape[1]),
        "augmentation_time_s": round(augmentation_s, 3),
        "train_time_s": round(train_s, 3),
        "total_time_s": round(total_s, 3),
        **{k: round(v, 6) for k, v in val_metrics.items()},
        **{k: round(v, 6) for k, v in test_metrics.items()},
    }
    config = {
        "seed": SEED,
        "strategy": "taichi_augmented_random_forest",
        "data_path": UNSW_PATH,
        "taichi_aug_type": args.taichi_aug_type,
        "taichi_aug_ratio": args.taichi_aug_ratio,
        "taichi_noise_std": args.taichi_noise_std,
        "taichi_state_strength": args.taichi_state_strength,
        "taichi_device_memory_gb": args.taichi_device_memory_gb,
        "taichi_cache_dir": args.taichi_cache_dir,
        "train_sample_frac": args.train_sample_frac,
        "max_train_samples": args.max_train_samples,
        "rf_params": {
            "n_estimators": args.rf_n_estimators,
            "max_depth": args.rf_max_depth,
            "min_samples_leaf": args.rf_min_samples_leaf,
            "min_samples_split": args.rf_min_samples_split,
            "class_weight": "balanced",
            "random_state": SEED,
            "n_jobs": args.rf_n_jobs,
        },
        "outputs": {
            "model": "artifacts/strategy5_taichi_rf.joblib",
            "preprocessor": "artifacts/strategy5_preprocessor.joblib",
            "config": "artifacts/strategy5_config.json",
            "summary": "results/strategy5_summary.csv",
        },
    }

    save_outputs(model, data["preprocessor"], config, summary)

    print("\nStrategy 5 summary:")
    print(pd.DataFrame([summary]).to_string(index=False))
    print("=" * 60)
    print("Strategy 5 complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
