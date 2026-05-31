"""
Taichi GPU feature augmentation for Component 3 Strategy 5.

This module is intentionally independent from existing baseline and strategy
pipelines. It augments already-transformed feature matrices and fails fast when
Taichi CUDA is unavailable.
"""

import logging
import math
import os
import sys

import numpy as np


_AUG_TYPES = {
    "noise": 0,
    "state": 1,
    "mixup": 2,
    "fusion": 3,
}


def _import_taichi():
    try:
        import taichi as ti
    except ImportError as exc:
        raise RuntimeError(
            "Taichi is required for Strategy 5. Install it with `pip install taichi` "
            "on the CUDA training machine."
        ) from exc
    return ti


def _ensure_cuda(ti, device_memory_gb, seed, cache_dir):
    cache_dir = os.path.abspath(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)
    try:
        ti.init(
            arch=ti.cuda,
            device_memory_GB=float(device_memory_gb),
            random_seed=int(seed),
            offline_cache=True,
            offline_cache_file_path=cache_dir,
        )
    except Exception as exc:
        raise RuntimeError(
            "Taichi CUDA backend could not be initialized. Strategy 5 forbids CPU "
            "fallback; verify Taichi, NVIDIA driver, and CUDA runtime on this host."
        ) from exc

    if ti.cfg.arch != ti.cuda:
        raise RuntimeError(
            f"Taichi initialized with arch={ti.cfg.arch}, expected ti.cuda. "
            "CPU fallback is forbidden for Strategy 5."
        )


def _build_class_index(y_codes):
    classes = np.unique(y_codes)
    starts = np.zeros(int(classes.max()) + 1, dtype=np.int32)
    counts = np.zeros(int(classes.max()) + 1, dtype=np.int32)
    sorted_parts = []

    for cls in classes:
        idx = np.flatnonzero(y_codes == cls).astype(np.int32)
        starts[int(cls)] = sum(len(part) for part in sorted_parts)
        counts[int(cls)] = len(idx)
        sorted_parts.append(idx)

    sorted_indices = np.concatenate(sorted_parts).astype(np.int32)
    return sorted_indices, starts, counts


def _make_kernel(ti):
    @ti.func
    def _randn():
        u1 = ti.max(ti.random(ti.f32), 1.0e-6)
        u2 = ti.random(ti.f32)
        return ti.sqrt(-2.0 * ti.log(u1)) * ti.cos(6.28318530718 * u2)

    @ti.func
    def _clip(v, lo, hi):
        out = v
        if out < lo:
            out = lo
        if out > hi:
            out = hi
        return out

    @ti.func
    def _copy_row(X_orig: ti.template(), X_aug: ti.template(),
                  src: ti.i32, dst: ti.i32, n_features: ti.i32):
        for j in range(n_features):
            X_aug[dst, j] = X_orig[src, j]

    @ti.func
    def _apply_noise(X_aug: ti.template(), feature_min: ti.template(),
                     feature_max: ti.template(), dst: ti.i32,
                     mutable_features: ti.i32, noise_std: ti.f32):
        for j in range(mutable_features):
            v = X_aug[dst, j] + _randn() * noise_std
            X_aug[dst, j] = _clip(v, feature_min[j], feature_max[j])

    @ti.func
    def _apply_state_machine(X_aug: ti.template(),
                             feature_min: ti.template(),
                             feature_max: ti.template(),
                             dst: ti.i32,
                             mutable_features: ti.i32,
                             state_strength: ti.f32):
        state = ti.cast(ti.floor(ti.random(ti.f32) * 4.0), ti.i32)
        scale = 0.25 + ti.random(ti.f32) * state_strength

        if state == 0:
            # Burst-like flow: bytes, packets, throughput, and packet buckets rise together.
            for j in range(mutable_features):
                if (2 <= j and j <= 5) or (24 <= j and j <= 30):
                    X_aug[dst, j] = _clip(X_aug[dst, j] + scale,
                                          feature_min[j], feature_max[j])
        elif state == 1:
            # Long-duration low-rate flow: duration and IAT rise, throughput decreases.
            for j in range(mutable_features):
                if (9 <= j and j <= 11) or (33 <= j and j <= 40):
                    X_aug[dst, j] = _clip(X_aug[dst, j] + scale,
                                          feature_min[j], feature_max[j])
                if j == 24 or j == 25:
                    X_aug[dst, j] = _clip(X_aug[dst, j] - scale,
                                          feature_min[j], feature_max[j])
        elif state == 2:
            # TCP flag / retransmission jitter.
            for j in range(mutable_features):
                if (6 <= j and j <= 8) or (20 <= j and j <= 23) or j == 31 or j == 32:
                    X_aug[dst, j] = _clip(X_aug[dst, j] + _randn() * scale,
                                          feature_min[j], feature_max[j])
        else:
            # Stealthy small-flow compression.
            for j in range(mutable_features):
                if (2 <= j and j <= 5) or (16 <= j and j <= 19) or (26 <= j and j <= 30):
                    X_aug[dst, j] = _clip(X_aug[dst, j] - scale,
                                          feature_min[j], feature_max[j])

    @ti.func
    def _apply_mixup(X_orig: ti.template(), y_orig: ti.template(),
                     sorted_indices: ti.template(), class_starts: ti.template(),
                     class_counts: ti.template(), X_aug: ti.template(),
                     src: ti.i32, dst: ti.i32, n_features: ti.i32):
        cls = y_orig[src]
        count = class_counts[cls]
        other = src
        if count > 0:
            offset = ti.cast(ti.floor(ti.random(ti.f32) * ti.cast(count, ti.f32)), ti.i32)
            other = sorted_indices[class_starts[cls] + offset]
        alpha = 0.25 + 0.5 * ti.random(ti.f32)
        for j in range(n_features):
            X_aug[dst, j] = alpha * X_orig[src, j] + (1.0 - alpha) * X_orig[other, j]

    @ti.kernel
    def fusion_augmentation_kernel(
        X_orig: ti.types.ndarray(dtype=ti.f32, ndim=2),
        y_orig: ti.types.ndarray(dtype=ti.i32, ndim=1),
        sorted_indices: ti.types.ndarray(dtype=ti.i32, ndim=1),
        class_starts: ti.types.ndarray(dtype=ti.i32, ndim=1),
        class_counts: ti.types.ndarray(dtype=ti.i32, ndim=1),
        feature_min: ti.types.ndarray(dtype=ti.f32, ndim=1),
        feature_max: ti.types.ndarray(dtype=ti.f32, ndim=1),
        X_aug: ti.types.ndarray(dtype=ti.f32, ndim=2),
        y_aug: ti.types.ndarray(dtype=ti.i32, ndim=1),
        aug_type: ti.i32,
        n_orig: ti.i32,
        n_features: ti.i32,
        mutable_features: ti.i32,
        noise_std: ti.f32,
        state_strength: ti.f32,
    ):
        for i in range(X_aug.shape[0]):
            src = ti.cast(ti.floor(ti.random(ti.f32) * ti.cast(n_orig, ti.f32)), ti.i32)
            if src >= n_orig:
                src = n_orig - 1

            selected = aug_type
            if aug_type == 3:
                r = ti.random(ti.f32)
                if r < 0.34:
                    selected = 0
                elif r < 0.67:
                    selected = 1
                else:
                    selected = 2

            _copy_row(X_orig, X_aug, src, i, n_features)
            y_aug[i] = y_orig[src]

            if selected == 0:
                _apply_noise(X_aug, feature_min, feature_max, i,
                             mutable_features, noise_std)
            elif selected == 1:
                _apply_state_machine(X_aug, feature_min, feature_max, i,
                                     mutable_features, state_strength)
            elif selected == 2:
                _apply_mixup(X_orig, y_orig, sorted_indices, class_starts,
                             class_counts, X_aug, src, i, n_features)

    return fusion_augmentation_kernel


class TaichiGPUAugmenter:
    """CUDA-only transformed feature augmenter for Strategy 5."""

    def __init__(
        self,
        device_memory_gb=4.0,
        mutable_features=47,
        seed=42,
        cache_dir=".taichi_cache",
        logger=None,
    ):
        self.device_memory_gb = device_memory_gb
        self.mutable_features = mutable_features
        self.seed = seed
        self.cache_dir = cache_dir
        self.logger = logger or logging.getLogger(__name__)
        self._ti = None
        self._kernel = None

    def _init_runtime(self):
        if self._ti is not None:
            return
        ti = _import_taichi()
        _ensure_cuda(ti, self.device_memory_gb, self.seed, self.cache_dir)
        self._ti = ti
        self._kernel = _make_kernel(ti)
        self.logger.info("Taichi CUDA initialized for Strategy 5 augmentation.")

    def run(
        self,
        X_train,
        y_train,
        aug_type="fusion",
        ratio=1.0,
        noise_std=0.05,
        state_strength=0.35,
    ):
        """Return `(X_augmented, y_augmented)` with original and augmented rows."""
        if aug_type not in _AUG_TYPES:
            raise ValueError(f"Unknown aug_type={aug_type!r}; expected one of {sorted(_AUG_TYPES)}")

        X_np = np.ascontiguousarray(X_train, dtype=np.float32)
        y_np = np.asarray(y_train)
        if X_np.ndim != 2:
            raise ValueError(f"X_train must be 2D, got shape={X_np.shape}")
        if len(y_np) != X_np.shape[0]:
            raise ValueError("X_train and y_train must have the same number of rows")
        if ratio <= 0:
            return X_np, y_np.copy()

        self._init_runtime()

        n_orig, n_features = X_np.shape
        n_aug = int(math.floor(n_orig * float(ratio)))
        if n_aug <= 0:
            return X_np, y_np.copy()

        mutable = min(int(self.mutable_features), n_features)
        labels, y_codes = np.unique(y_np, return_inverse=True)
        y_codes = np.ascontiguousarray(y_codes.astype(np.int32))
        sorted_indices, class_starts, class_counts = _build_class_index(y_codes)

        feature_min = np.ascontiguousarray(np.nanmin(X_np, axis=0).astype(np.float32))
        feature_max = np.ascontiguousarray(np.nanmax(X_np, axis=0).astype(np.float32))
        X_aug = np.empty((n_aug, n_features), dtype=np.float32)
        y_aug_codes = np.empty(n_aug, dtype=np.int32)

        self.logger.info(
            "Running Taichi augmentation: type=%s ratio=%.3f n_orig=%d n_aug=%d",
            aug_type, ratio, n_orig, n_aug,
        )
        self._kernel(
            X_np,
            y_codes,
            sorted_indices,
            class_starts,
            class_counts,
            feature_min,
            feature_max,
            X_aug,
            y_aug_codes,
            _AUG_TYPES[aug_type],
            n_orig,
            n_features,
            mutable,
            float(noise_std),
            float(state_strength),
        )
        self._ti.sync()

        y_aug = labels[y_aug_codes]
        X_out = np.vstack([X_np, X_aug]).astype(np.float32, copy=False)
        y_out = np.concatenate([y_np, y_aug])
        return X_out, y_out


def run_or_exit(*args, **kwargs):
    """Convenience wrapper for command-line scripts that want fail-fast behavior."""
    try:
        return TaichiGPUAugmenter().run(*args, **kwargs)
    except RuntimeError as exc:
        logging.error("%s", exc)
        sys.exit(1)
