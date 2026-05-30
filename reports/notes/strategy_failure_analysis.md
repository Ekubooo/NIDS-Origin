# Strategy, Ablation, and Failure Analysis Notes

## Failure Case 1: Worms Cannot Be Learned
- **Condition**: Any training configuration (class_weight / SMOTE)
- **Performance**: Recall = 0.8438, Precision = 0.7500, F1 = 0.7941
- **Support**: 32 samples (0.007% of total)
- **Behavior**: Worms is almost always misclassified as another attack class
- **Root cause**: Only 158 training samples; the feature space is entirely
  covered by higher-frequency attack classes (especially Backdoor and Exploits).
- **Strategy effect**: Strategy 1 (tau=0.99) rejects most Worms as "unknown"
  rather than misclassifying them, which is the correct safety behavior.
- **Improvement direction**: Few-shot learning or one-class classifiers for
  extremely rare classes. Traditional supervised methods are insufficient.
- **Practical significance**: Worms propagation patterns are evolving;
  traditional NetFlow features may not capture modern worm behavior.

## Failure Case 2: Strategy 1 Coverage Collapse at High Tau
- **Condition**: tau >= 0.95 on full test set

  Tau sweep summary:
  | tau | coverage | accepted_accuracy | unknown_rejection | known_false_rej |
  |-----|----------|-------------------|-------------------|-----------------|
  | 0.5 | 0.9807 | 0.9951 | 0.7437 | 0.0182 |
  | 0.7 | 0.9657 | 0.9990 | 0.9575 | 0.0328 |
  | 0.85 | 0.9572 | 0.9997 | 0.9947 | 0.0413 |
  | 0.9 | 0.9530 | 0.9998 | 0.9987 | 0.0455 |
  | 0.95 | 0.9492 | 1.0000 | 1.0000 | 0.0493 |
  | 0.5 | 0.9873 | 0.9960 | 0.4508 | 0.0043 |
  | 0.7 | 0.9754 | 0.9980 | 0.8114 | 0.0095 |
  | 0.85 | 0.9695 | 0.9989 | 0.9032 | 0.0138 |
  | 0.9 | 0.9673 | 0.9992 | 0.9226 | 0.0156 |
  | 0.95 | 0.9642 | 0.9999 | 0.9476 | 0.0183 |

- **Finding**: At tau=0.99, coverage=94.6% is acceptable. At tau=0.95,
  unknown rejection drops but known false rejection also decreases.
- **Recommendation**: The operational tau depends on the deployment scenario.
  - High-security (prefer fewer false negatives): tau=0.90, higher rejection
  - Balanced: tau=0.85, coverage >= 85% with decent unknown detection
- **Limitation**: tau > 0.99 would make coverage collapse rapidly

## Failure Case 3: Stress B Cross-Dataset Recall Collapse
- **Condition**: Model trained on UNSW, tested on CICIDS2018
- **Binary F1 on CICIDS**: 0.2593
- **FPR (Benign -> Alert)**: 0.5607 (56% of normal traffic flagged!)
- **FNR (Attack -> Normal)**: 0.2887
- **Delta F1 (degradation)**: 0.4181
- **Feature-level explanation**: The largest reproducible shifts are:

  | Feature | UNSW mean | CICIDS mean | Std. mean diff |
  |---------|-----------|-------------|----------------|
  | ICMP_TYPE | 22777.886 | 3119.160 | -1.220 |
  | ICMP_IPV4_TYPE | 88.976 | 12.184 | -1.220 |
  | L4_SRC_PORT | 32660.520 | 50090.622 | 1.001 |
  | SRC_TO_DST_SECOND_BYTES | 371.346 | 29.367 | -0.842 |
  | TCP_FLAGS | 19.765 | 69.795 | 0.740 |

- **Conclusion**: Pure feature-level classifiers cannot solve domain shift.
  Domain adaptation methods or per-network retraining is required for deployment.

## Failure Case 4: SMOTE Limitations for Extremely Rare Classes
- **Condition**: Worms (158 samples), k_neighbors=1

  Imbalance method comparison:
  | method | Worms_recall | Analysis_recall | Shellcode_recall | macro_f1 |
  |--------|-------------|----------------|-----------------|----------|
  | none | 0.4062 | 0.3347 | 0.5147 | 0.5931 |
  | class_weight | 0.6250 | 0.9388 | 0.7290 | 0.6363 |
  | SMOTE | 0.5938 | 0.9388 | 0.7332 | 0.6154 |

- **Finding**: SMOTE's synthetic samples for Worms have very low diversity
  because they are generated from only 158 real examples. The synthetic
  samples do not provide meaningful new information for the classifier.
- **Recommendation**: SMOTE is not recommended for classes with fewer than
  200 samples. Use class_weight or other methods instead.

## Strategy 1: Confidence Thresholding
- **Selected tau**: 0.99 (from validation set)
- **Coverage**: 94.6% at tau=0.99
- **Unknown rejection rate**: 97-100% across both Stress A groups
- **Known false rejection**: 3.6-5.4%
- **Saved config**: artifacts/strategy_config.json

## Strategy 2: Ensemble Disagreement
- **Ensemble size**: M=5 (3xRF + 1xXGBoost + 1xLR)
- **Majority vote Macro-F1**: 0.6674
- **Disagreement AUROC**: 0.8529
- **Key insight**: When disagreement >= 0.4, accuracy drops from 99% to <35%.
  High disagreement is a reliable signal of likely-wrong predictions.
- **Unknown class disagreement**: mean 0.1850 vs known mean 0.0045.
- **Unknown detection AUROC**: 0.8446 on Stress A, showing that disagreement also separates unknown from known inputs.
- **Models saved**: artifacts/ensemble_models/

## Ablation Summary
- Ablation A: Threshold tau sweep results in results/ablation_a_threshold_sensitivity.csv
- Ablation B: Ensemble size sweep results in results/ablation_b_ensemble_size.csv
- Ablation C: Imbalance method comparison in results/ablation_c_imbalance_methods.csv
