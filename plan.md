# NIDS Project: Taichi GPU Augmentation Implementation Plan

## Objective
Implement Component 3 (Improvement Strategies) - Strategy 5 (Feature Robustness via Augmentation) using a high-performance Taichi GPU Kernel. The implementation must strictly follow a "Transparent Middleware" pattern, ensuring no destructive modifications to existing baselines or preprocessing pipelines.

## Prerequisite Checks (CUDA Fail-Fast)
**Agent Task:** Before generating code, ensure `taichi` is installed in the environment (`pip install taichi`). 
**Human/Agent Verification:** Ensure NVIDIA drivers are correctly loaded. The implemented Python code MUST contain strict assertions to abort execution if the CUDA backend cannot be initialized (fallback to CPU is explicitly forbidden to ensure HPC requirements).

## Step 1: Create the Taichi Augmenter Module
**File to Create:** `robustness/taichi_augmenter.py`

1. **Imports:** `taichi as ti`, `numpy as np`, `logging`, `sys`.
2. **CUDA Initialization Block:**
   - Call `ti.init(arch=ti.cuda, device_memory_GB=4.0)`.
   - Add assertion: `if ti.cfg.arch != ti.cuda: raise RuntimeError(...)` -> `sys.exit(1)`.
3. **Taichi Kernel Design (`@ti.kernel`):**
   - **Name:** `fusion_augmentation_kernel`
   - **Inputs:** `X_orig` (ti.types.ndarray), `y_orig` (ti.types.ndarray), `X_aug` (ti.types.ndarray), `y_aug` (ti.types.ndarray), `aug_type` (ti.i32), `noise_std` (ti.f32), `mask_prob` (ti.f32).
   - **Logic:** - Loop over the augmented block size in parallel.
     - `aug_type == 0`: Apply Gaussian noise (`ti.random()` based Box-Muller transform or native `ti.randn()`) to continuous feature columns.
     - `aug_type == 1`: Apply random zero-masking based on `mask_prob`.
     - `aug_type == 2`: Intra-class Mixup. Randomly pick another index from the same class label (passed via a pre-computed offset/bounds array), generate a scalar `alpha = ti.random()`, and interpolate features.
4. **Python Wrapper Class (`TaichiGPUAugmenter`):**
   - **Method `run(X_train, y_train, aug_type='noise', ratio=1.0)`**:
     - Allocate NumPy arrays for augmented data `[int(N * ratio), num_features]`.
     - Pass data to Taichi Kernel via `ti.ndarray`.
     - Fetch result, perform `np.vstack([X_train, X_aug])` and `np.concatenate([y_train, y_aug])`.
     - Explicitly delete Taichi ndarrays to free VRAM.
     - Return the concatenated (fused) matrices.

## Step 2: Non-Intrusive Integration
**File to Modify:** `experiments/run_strategies.py`

1. **CLI Argument Parsing:**
   - Add argument `--strategy` (choices: `confidence_threshold`, `ensemble`, `taichi_aug`).
   - Add argument `--taichi_aug_type` (choices: `noise`, `mask`, `mixup`, default: `noise`).
2. **Execution Flow Injection:**
   - Locate the section where data is loaded and preprocessed (but before `model.fit()`).
   - Add conditional logic:
     ```
     python
     if args.strategy == 'taichi_aug':
         from robustness.taichi_augmenter import TaichiGPUAugmenter
         import logging
         logging.info(f"🚀 Injecting Taichi GPU Augmenter (Type: {args.taichi_aug_type})...")
         X_train_resampled, y_train_resampled = TaichiGPUAugmenter.run(
             X_train_resampled, y_train_resampled, 
             aug_type=args.taichi_aug_type, 
             ratio=1.0
         )
     ```
   - Ensure the downstream model (RandomForest) receives this mutated `X_train_resampled`.

## Step 3: Validation & Metric Generation
**Files to Modify/Create:** N/A (Leverage existing scripts)

1. The agent should verify that `experiments/run_stress.py` (specifically Stress Test C) can correctly evaluate the newly trained RandomForest model.
2. The expected output is a flattened degradation curve for Stress C compared to the original baseline.