# File Inventory — reports/figures & results & reports/notes

Generated: 2026-05-19

---

## 一、执行脚本与产出文件对应关系

### 1. `experiments/run_eda.py` — 探索性数据分析

| 产出文件 | 类型 |
|---|---|
| `reports/figures/l7_proto_quality.png` | 图 |
| `reports/figures/class_distribution.png` | 图 |
| `reports/figures/correlation_heatmap.png` | 图 |
| `reports/figures/feature_distribution_by_class.png` | 图 |
| `reports/figures/protocol_by_class.png` | 图 |
| `reports/notes/data_and_eda_notes.md` | 笔记 |

### 2. `experiments/run_baseline.py` — 基线模型训练与评估

| 产出文件 | 类型 |
|---|---|
| `reports/figures/confusion_matrix_Majority.png` | 图 |
| `reports/figures/confusion_matrix_LogisticRegression.png` | 图 |
| `reports/figures/confusion_matrix_RandomForest.png` | 图 |
| `reports/figures/confusion_matrix_XGBoost.png` | 图 |
| `results/per_class_report_Majority.csv` | 表 |
| `results/per_class_report_LogisticRegression.csv` | 表 |
| `results/per_class_report_RandomForest.csv` | 表 |
| `results/per_class_report_XGBoost.csv` | 表 |
| `results/baseline_results.csv` | 汇总表 |

### 3. `experiments/run_stress.py` — 压力测试 A / B / C

| 产出文件 | 类型 |
|---|---|
| `reports/figures/stress_a_confidence_set1_Worms_Analysis_Shellcode.png` | Stress A 图 |
| `reports/figures/stress_a_confusion_set1_Worms_Analysis_Shellcode.png` | Stress A 图 |
| `reports/figures/stress_a_full_confusion_set1_Worms_Analysis_Shellcode.png` | Stress A 图 |
| `reports/figures/stress_a_confidence_set2_Backdoor_DoS_Fuzzers.png` | Stress A 图 |
| `reports/figures/stress_a_confusion_set2_Backdoor_DoS_Fuzzers.png` | Stress A 图 |
| `reports/figures/stress_a_full_confusion_set2_Backdoor_DoS_Fuzzers.png` | Stress A 图 |
| `results/stress_a_results.csv` | Stress A 汇总 |
| `results/stress_a_full_confusion_set1_Worms_Analysis_Shellcode.csv` | Stress A 表 |
| `results/stress_a_report_set1_Worms_Analysis_Shellcode.csv` | Stress A 表 |
| `results/stress_a_mapping_set1_Worms_Analysis_Shellcode.csv` | Stress A 表 |
| `results/stress_a_full_confusion_set2_Backdoor_DoS_Fuzzers.csv` | Stress A 表 |
| `results/stress_a_report_set2_Backdoor_DoS_Fuzzers.csv` | Stress A 表 |
| `results/stress_a_mapping_set2_Backdoor_DoS_Fuzzers.csv` | Stress A 表 |
| `results/stress_c_results.csv` | Stress C 汇总 |
| `reports/figures/stress_c_degradation_curve.png` | Stress C 图 |

### 4. `experiments/run_stress_b_full.py` — Stress B 全量评估

| 产出文件 | 类型 |
|---|---|
| `results/stress_b_full_results.csv` | 表 |

### 5. `experiments/run_strategies.py` — 鲁棒性策略评估

| 产出文件 | 类型 |
|---|---|
| `reports/figures/coverage_accuracy_curve.png` | 图 |
| `reports/figures/disagreement_histogram.png` | 图 |
| `reports/figures/disagreement_auroc.png` | 图 |
| `results/strategy1_summary.csv` | 表 |
| `results/strategy1_stress_a.csv` | 表 |
| `results/strategy2_summary.csv` | 表 |
| `results/strategy2_stress_a.csv` | 表 |
| `results/strategy2_stress_b_full_results.csv` | 表 |
| `results/mcnemar_s1.csv` | 表 |
| `results/mcnemar_s2.csv` | 表 |
| `results/mcnemar_results.csv` | 表 |
| `results/strategies_comparison.csv` | 汇总表 (后被 aggregate 覆盖) |
| `results/strategy_comparison.csv` | 汇总表 (后被 aggregate 覆盖) |

### 6. `experiments/run_ablation.py` — 消融实验

| 产出文件 | 类型 |
|---|---|
| `results/ablation_a_threshold_sensitivity.csv` | 表 |
| `results/ablation_b_ensemble_size.csv` | 表 |
| `results/ablation_c_imbalance_methods.csv` | 表 |
| `results/per_class_tau_ablation.csv` | 表 |

### 7. `experiments/run_significance.py` — 统计显著性检验

| 产出文件 | 类型 |
|---|---|
| `results/statistical_significance.csv` | 表 |

### 8. `experiments/aggregate_strategy_results.py` — 策略结果聚合

| 产出文件 | 类型 |
|---|---|
| `results/strategies_comparison.csv` | **覆盖** run_strategies.py 的同名输出 |
| `results/strategy_comparison.csv` | **覆盖** run_strategies.py 的同名输出 |
| `results/strategies_comparison_raw.csv` | 表 |

### 9. `experiments/run_failure_analysis.py` — 失败模式分析

| 产出文件 | 类型 |
|---|---|
| `reports/notes/strategy_failure_analysis.md` | 笔记 |

---

## 二、无对应脚本的孤立文件（建议删除）

以下文件曾经存在于活跃结果/报告目录中，但没有当前 Python 脚本会产出它们。
已确认的旧产物已移至 `reports/archive/legacy_outputs/`，避免和正式结果混淆。

### reports/figures/（旧产物，已归档）

| 文件 | 说明 |
|---|---|
| `confusion_matrix.png` | 无模型后缀；run_baseline.py 只生成带模型名的 `confusion_matrix_{Model}.png`；已归档 |
| `stress_a_unknown_confidence.png` | run_stress.py 只生成分组的 `stress_a_confidence_set1/set2_*.png`，无此汇总版；已归档 |
| `stress_b_feature_distribution_top5.png` | 旧 sampled Stress B 图，已不再保留；最终使用 `reports/figures_final/08_*` 和 `09_*` |

### results/（旧产物，已归档）

| 文件 | 说明 |
|---|---|
| `ablation_results.csv` | run_ablation.py 生成的是 `ablation_a/b/c_*.csv`，无此汇总版；已归档 |
| `stress_b_strategy_comparison.csv` | 无任何脚本产出此文件；已归档 |
| `strategy2_stress_a_lightweight_group1_supplementary.csv` | 旧 supplementary 产物，已移至 `reports/archive/legacy_outputs/` |
| `strategy2_stress_a_lightweight_group2_supplementary.csv` | 旧 supplementary 产物，已移至 `reports/archive/legacy_outputs/` |
| `strategy2_stress_a_lightweight_groups.csv` | 旧 supplementary 产物，已移至 `reports/archive/legacy_outputs/` |

### reports/notes/（manual notes / old note cleanup）

| 文件 | 说明 |
|---|---|
| `baseline_results.md` | 手写阶段笔记，当前保留 |
| `data_eda_report.txt` | 无脚本产出；run_eda.py 生成的是 `data_and_eda_notes.md` |
| `stress_test_results.md` | 无脚本产出 |
| `table_footnotes.txt` | 无脚本产出；`check_consistency.py` 检查的路径是 `results/table_footnotes.txt`，与此位置不符 |

---

## 三、备注

1. `strategies_comparison.csv` 和 `strategy_comparison.csv` 被 **两个脚本先后写入**：`run_strategies.py` 先生成，`aggregate_strategy_results.py` 随后覆盖。最终版本来自 `aggregate_strategy_results.py`。
2. `strategies_comparison_raw.csv` 仅由 `aggregate_strategy_results.py` 生成（纯数值版，无 N/A 标记）。
3. 无 Jupyter notebook，所有产出均来自 `.py` 脚本。
