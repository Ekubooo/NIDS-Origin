# Final Pre-Report Project Audit

Audit date: 2026-05-28

This is the final project-wide audit before writing the paper-style report. It
checks the repository against the proposal requirements, active code, result
tables, final figures, data consistency, and reproducibility scripts.

## Overall Conclusion

The project is ready to use as the technical basis for the final report.

All proposal-required experimental components are represented in active code,
results, and figures:

- Baseline multi-class classifier
- Stress Test A: held-out unknown classes
- Stress Test B: cross-dataset distribution shift
- Stress Test C: feature degradation
- Two improvement strategies
- Ablation study
- Failure analysis
- CLI prototype

No active result table or final figure was found to be missing. Old or confusing
legacy outputs have been moved to `reports/archive/legacy_outputs/`.

The remaining work is report writing, not experiment completion.

## Dataset And Metadata

The proposal describes NF-UQ-NIDS-v2, but this repository intentionally uses
NF-UQ-NIDS-v3. This is stated in `README.md`,
`reports/detailed_project_report.md`, and the data notes.

Confirmed active datasets:

| Dataset | Path | Rows | Label consistency |
|---|---|---:|---|
| NF-UNSW-NB15-v3 | `data/NF-UNSW-NB15-v3.csv` | 2,365,424 | 0 `Attack`/`Label` mismatches |
| NF-CSE-CIC-IDS2018-v3 | `data/NF-CSE-CIC-IDS2018-v3.csv` | 20,115,529 | 0 `Attack`/`Label` mismatches |

UNSW class distribution:

| Class | Count |
|---|---:|
| Benign | 2,237,731 |
| Exploits | 42,748 |
| Fuzzers | 33,816 |
| Generic | 19,651 |
| Reconnaissance | 17,074 |
| DoS | 5,980 |
| Backdoor | 4,659 |
| Shellcode | 2,381 |
| Analysis | 1,226 |
| Worms | 158 |

Feature metadata:

- `data/metadata/feature_columns.json` declares 49 modeling features.
- `data/metadata/common_features_unsw_cicids.json` also has 49 common features.
- The feature sets match exactly.
- Removed identifiers/timestamps are not present in the modeling features.
- Known dtype mismatches are limited to:
  - `DST_TO_SRC_SECOND_BYTES`
  - `L7_PROTO`
  - `SRC_TO_DST_SECOND_BYTES`
- These are handled by preprocessing and documented in final data-quality figures.

## Proposal Requirement Matrix

| Proposal requirement | Evidence in repository | Status |
|---|---|---|
| Dataset acquisition and EDA | `experiments/run_eda.py`, `reports/notes/data_and_eda_notes.md`, `reports/figures_final/01_*`, `02_*`, `17_*` | Complete |
| Missing/inf/data-quality report | `reports/notes/data_and_eda_notes.md`, `reports/figures_final/17_v3_data_quality_missing_inf.png` | Complete |
| Class distribution plot | `reports/figures_final/01_class_distribution.png` | Complete |
| Feature statistics | `reports/notes/data_and_eda_notes.md` | Complete |
| Preprocessing pipeline | `preprocessing/preprocess.py`, `artifacts/preprocessor.joblib`, `data/metadata/feature_columns.json` | Complete |
| Baseline classifiers | `experiments/run_baseline.py`, `results/baseline_results.csv` | Complete |
| Required Logistic Regression and Random Forest | `results/baseline_results.csv`, `results/per_class_report_LogisticRegression.csv`, `results/per_class_report_RandomForest.csv` | Complete |
| Per-class precision/recall/F1 | `results/per_class_report_*.csv` | Complete |
| Confusion matrices | `reports/figures/confusion_matrix_*.png` | Complete |
| Stress A held-out classes | `experiments/run_stress.py`, `results/stress_a_results.csv` | Complete |
| Stress A at least two held-out groups | `results/stress_a_results.csv` has 2 groups | Complete |
| Stress A confidence / unknown analysis | `results/stress_a_results.csv`, `results/stress_a_mapping_set*.csv`, final figures 05a/05b | Complete |
| Stress A confusion matrices | `results/stress_a_full_confusion_set*.csv`, final figures 06/07 | Complete |
| Stress B cross-dataset shift | `experiments/run_stress_b_full.py`, `results/stress_b_full_results.csv` | Complete |
| Stress B binary precision/recall/F1/FPR/FNR/delta | `results/stress_b_full_results.csv` | Complete |
| Stress B feature-shift explanation | `experiments/analyze_stress_b_shift.py`, `results/stress_b_feature_shift.csv`, final figure 16 | Complete |
| Stress C feature degradation | `experiments/run_stress.py`, `results/stress_c_results.csv` | Complete |
| Stress C degradation curve | `reports/figures_final/10_stress_c_degradation_by_type.png` | Complete |
| Improvement Strategy 1 | Confidence threshold rejection in `robustness/strategies.py` and `experiments/run_strategies.py` | Complete |
| Strategy 1 coverage/accuracy curve | `reports/figures_final/12_strategy1_coverage_accuracy_curve.png` | Complete |
| Improvement Strategy 2 | Ensemble disagreement in `robustness/strategies.py`, `robustness/streaming_ensemble.py`, `experiments/run_strategies.py` | Complete |
| Strategy 2 disagreement analysis | `results/strategy2_stress_a.csv`, final figure 13 | Complete |
| Strategy comparison vs baseline | `results/strategies_comparison.csv`, final figure 11 | Complete |
| Ablation study | `experiments/run_ablation.py`, `results/ablation_a_*`, `ablation_b_*`, `ablation_c_*`, final figures 14/15 | Complete |
| Failure analysis | `experiments/run_failure_analysis.py`, `reports/notes/strategy_failure_analysis.md` | Complete |
| CLI prototype | `predict.py`, `data/sample_test.csv`, README CLI commands | Complete |
| Final report figures | `reports/figures_final/`, `figure_manifest.csv` | Complete |

## Key Results Confirmed

Baseline:

- Random Forest Macro-F1: 0.6774
- Random Forest Weighted-F1: 0.9863
- XGBoost Macro-F1: 0.6398
- Logistic Regression Macro-F1: 0.4211
- Majority Macro-F1: 0.0972

Stress A:

- Held-out group 1: `Worms, Analysis, Shellcode`
- Held-out group 2: `Backdoor, DoS, Fuzzers`
- Confidence unknown-detection AUROC: 0.9870 and 0.9832

Stress B:

- Full CICIDS rows: 20,115,529
- Binary F1: 0.2593
- FPR: 0.5607
- FNR: 0.2887
- Delta F1: 0.4181

Stress C:

- Four degradation types are present:
  - `noise`
  - `masking`
  - `dropout_top`
  - `dropout_bottom`
- Gaussian noise at `sigma=0.1` gives Macro-F1 0.2688.
- Drop least important features is near-control behavior, with Macro-F1 around
  0.674-0.677.

Strategies:

- Strategy 1 selected tau: 0.99 from validation.
- Strategy 1 accepted F1: 0.8667.
- Strategy 1 coverage: 0.9459.
- Strategy 2 clean full F1: 0.6674.
- Strategy 2 disagreement AUROC as wrong-prediction detector: 0.8529.
- Strategy 2 Stress A unknown-detection AUROC: 0.8446.
- Strategy 2 unknown vs known mean disagreement: 0.1850 vs 0.0045.

## Final Figures

`reports/figures_final/` contains 18 PNG figures and one manifest. The manifest
has 18 entries, no duplicates, no missing PNGs, and no extra PNGs.

The final figures cover:

- Data/EDA: 01, 02, 17
- Baselines: 03, 04
- Stress A: 05a, 05b, 06, 07
- Stress B: 08, 09, 16
- Stress C: 10
- Strategies: 11, 12, 13
- Ablations: 14, 15

## CLI Prototype

The following CLI paths were tested successfully on `data/sample_test.csv`:

```bash
python predict.py --input data/sample_test.csv --strategy none
python predict.py --input data/sample_test.csv --strategy confidence_threshold --tau 0.85
python predict.py --input data/sample_test.csv --strategy ensemble+threshold --tau 0.85
```

The ensemble path prints an XGBoost CPU/CUDA device warning, but predictions are
produced correctly. This should be described as a runtime warning, not a project
failure.

## Legacy Outputs

Old or potentially confusing outputs have been moved out of active result
folders:

```text
reports/archive/legacy_outputs/
```

The archive is ignored by `.gitignore`.

Active `results/` no longer contains the old
`strategy2_stress_a_lightweight_*.csv` files.

## Verification Commands

The following checks passed during final review:

```bash
python -m compileall config.py predict.py preprocessing models evaluation robustness experiments
python experiments/run_failure_analysis.py
python experiments/verify_8items.py
python experiments/verify_items.py
python experiments/check_consistency.py
```

Additional checks passed:

- Figure manifest count equals final PNG count.
- `strategy2_stress_a.csv` contains `unknown_detection_auroc`.
- `stress_b_feature_shift.csv` has 49 rows.
- `stress_c_results.csv` has all four degradation types.
- Active results directory has no old lightweight Strategy 2 files.

## Items To Mention As Limitations In The Report

These are not repository defects, but should be written honestly in the final
paper:

1. The proposal references NF-UQ-NIDS-v2; this project uses V3. State this
   clearly in the dataset section.
2. Strategy 1 becomes too conservative under some shifted/degraded settings,
   producing undefined accepted evaluation at 0% coverage.
3. Strategy 2 detects uncertainty but does not materially improve Stress B or
   Stress C F1.
4. Cross-dataset generalization is weak; Stress B is the largest failure mode.
5. The current repository contains a technical report base, not a fully formatted
   final academic paper.

## Final Status

No missing required experiment, result table, or final figure was found.

The project is complete enough to start writing the final report.
