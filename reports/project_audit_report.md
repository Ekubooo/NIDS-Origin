# NetFlow NIDS 项目审计与修复报告

日期: 2026-05-19 ~ 2026-05-21

---

## Phase 1: 文件清单梳理 — 产出文件与脚本对应关系

### 目标

理清 `reports/figures/`（27 PNG）、`results/`（38 CSV）、`reports/notes/`（6 文件）各自的生成脚本，找出无对应脚本的孤立文件。

### 方法

1. 用 Glob 列出三个目录的全部文件。
2. 用 Grep 扫描所有 `experiments/*.py` 中的 `.to_csv()`、`savefig()`、`.png`、`.csv` 调用。
3. 逐个脚本核对其声称的产出路径与实际磁盘文件。
4. 将每个文件与产出它的脚本建立一对一映射。

### 发现

**有对应脚本的文件**: 55 个（24 图 + 29 表 + 2 笔记）

**孤立文件（12 个，无任何脚本产出）**:

| 目录 | 文件 | 原因 |
|---|---|---|
| `reports/figures/` | `confusion_matrix.png` | 旧无模型后缀图，已移至 `reports/archive/legacy_outputs/` |
| `reports/figures/` | `stress_a_unknown_confidence.png` | 旧汇总图，已移至 `reports/archive/legacy_outputs/` |
| `reports/figures/` | `stress_b_feature_distribution_top5.png` | 旧 sampled Stress B 图，已废弃；最终 Stress B 图位于 `reports/figures_final/08_*` 和 `09_*` |
| `results/` | `ablation_results.csv` | 旧汇总表，已移至 `reports/archive/legacy_outputs/` |
| `results/` | `stress_b_strategy_comparison.csv` | 旧表，已移至 `reports/archive/legacy_outputs/` |
| `results/` | `strategy2_stress_a_lightweight_*.csv` (3个) | 旧 supplementary 产物，已移至 `reports/archive/legacy_outputs/` |
| `reports/notes/` | `baseline_results.md` | 手写阶段笔记，当前保留 |
| `reports/notes/` | `data_eda_report.txt` | run_eda.py 生成的是 `data_and_eda_notes.md` |
| `reports/notes/` | `stress_test_results.md` | 手写阶段笔记，已同步当前 Stress B feature-shift 口径 |
| `reports/notes/` | `table_footnotes.txt` | 当前作为 Strategy 2 / Stress B 说明脚注保留，`check_consistency.py` 已检查该路径 |

另外发现: `strategies_comparison.csv` 和 `strategy_comparison.csv` 被 `run_strategies.py` 和 `aggregate_strategy_results.py` **两个脚本先后写入**，最终版本来自后者。

### 核心函数

- `experiments/run_eda.py` — `analyze_*()` 系列函数 + `save_notes()`
- `experiments/run_baseline.py` — `train_single_model()`, `evaluate_model()`
- `experiments/run_stress.py` — `run_stress_a_experiments()`, `run_stress_b_experiment()`, `run_stress_c_experiment()`
- `experiments/run_strategies.py` — `evaluate_strategy_stress_a()`, `evaluate_strategy_stress_b()`
- `experiments/aggregate_strategy_results.py` — `main()` 聚合逻辑

---

## Phase 2: CLI Prototype 可运行性检查

### 目标

验证 `predict.py` 的 4 条 CLI 命令是否全部能正常运行。

### 方法

1. 阅读 README.md 中 "CLI Prototype" 章节的预期命令。
2. 检查 `predict.py` 的 argparse 定义与 README 是否一致。
3. 检查所有依赖的 artifact 文件是否存在（`preprocessor.joblib`, `best_model.joblib`, `label_encoder.joblib`, ensemble models）。
4. 逐条执行 4 种策略命令，观察输出和错误。

### 发现与解决

#### 问题 1: ensemble / ensemble+threshold 策略崩溃

**错误**:
```
AttributeError: Can't get attribute '_XGBWrapper' on <module 'experiments.run_baseline'>
```

**根因**: `artifacts/ensemble_models/XGB.joblib` 在序列化时，`XGBWrapper` 类还叫 `_XGBWrapper`（带下划线前缀）。后来代码中将类重命名为 `XGBWrapper`，导致 `joblib.load()` 时找不到旧类名。其余 4 个模型 (LR + 3xRF) 不受影响。

**修复** (两处改动):

`experiments/run_baseline.py:175` — 添加向后兼容别名:
```python
_XGBWrapper = XGBWrapper  # backward-compat: old pickles reference _XGBWrapper
```

`predict.py:54` — 在 `load_ensemble_models()` 中提前导入模块，确保 joblib unpickle 时能在 `sys.modules` 中找到类:
```python
import experiments.run_baseline  # noqa: needed by joblib to unpickle _XGBWrapper/XGBWrapper
```

#### 问题 2: README 中示例路径不存在

README 中 `--input sample.csv` 实际不存在，应为 `data/sample_test.csv`。修复: 全部 5 处替换。

#### 问题 3: check_consistency.py 路径错误

`check_consistency.py:58` 检查 `results/table_footnotes.txt`，但实际文件位于 `reports/notes/table_footnotes.txt`。修复: 更正路径。

### 验证结果

| 策略 | 修复前 | 修复后 |
|---|---|---|
| `none` | ✅ | ✅ |
| `confidence_threshold` | ✅ | ✅ |
| `ensemble` | ❌ AttributeError | ✅ |
| `ensemble+threshold` | ❌ AttributeError | ✅ |

### 核心函数

- `predict.py:load_model_and_artifacts()` — 加载 preprocessor + best_model + label_encoder
- `predict.py:load_ensemble_models()` — 加载 5 个 ensemble 成员模型
- `predict.py:predict_none()` — 直接预测
- `predict.py:predict_confidence_threshold()` — Strategy 1: 置信度阈值拒绝
- `predict.py:predict_ensemble()` — Strategy 2: 5 模型多数投票 + disagreement
- `predict.py:predict_ensemble_threshold()` — Strategy 1+2 组合

---

## Phase 3: GPU / PyTorch 使用情况排查

### 目标

确定项目中哪些文件使用了 PyTorch 或 GPU 训练。

### 方法

全项目搜索 `torch`、`cuda`、`gpu`、`device` 关键词。

### 发现

- **PyTorch**: 零引用，不是项目依赖，`requirements.txt` 中也没有。
- **GPU 范围**: 仅 XGBoost，通过 `device="cuda"` + `tree_method="hist"` 实现。
- **核心函数**: `models/chosen_model.py:get_xgb_device()` — 用 10 行随机数据试跑 CUDA，失败则自动打印 warning 并切回 CPU。

### GPU 相关文件清单

| 文件 | 函数 | 角色 |
|---|---|---|
| `models/chosen_model.py` | `get_xgb_device()` | GPU 检测与自动降级 |
| `models/chosen_model.py` | `train_xgboost()` | 调用 get_xgb_device 并传入 XGBClassifier |
| `experiments/run_baseline.py` | `train_single_model()` | CLI 参数 `--use-gpu` / `--no-gpu` |
| `experiments/run_stress.py` | `run_stress_a_experiments()` | Stress A 训练时传递 use_gpu |
| `experiments/run_strategies.py` | `evaluate_strategy_stress_a()` | Strategy 2 ensemble 训练时传递 use_gpu |
| `experiments/run_ablation.py` | `run_ablation_b()` | 消融实验 ensemble 训练 |
| `robustness/strategies.py` | `train_heterogeneous_ensemble()` | 构建 5-model ensemble 中的 XGB |
| `robustness/stress_tests.py` | `_train_model()` | Stress test 中训练 XGBoost |
| `robustness/streaming_ensemble.py` | `_make_xgb()`, `build_member_specs()` | 流式 ensemble 中的 XGB 构建 |

---

## Phase 4: 项目整体架构梳理

通过以上各阶段的审计，摸清了项目的完整结构:

```
数据流: data/*.csv → preprocessing/ → models/ → evaluation/
                            ↓
                    experiments/ (编排层)
                            ↓
              results/ + reports/figures/ + reports/notes/
                            ↓
                    predict.py (CLI 推理)
```

### 模块职责

| 模块 | 职责 |
|---|---|
| `config.py` | 全局路径、列定义、超参数、随机种子 |
| `preprocessing/` | ColumnTransformer pipeline、SMOTE 平衡 |
| `models/` | Majority/LR/RF 基线 + XGBoost (含 GPU) |
| `evaluation/` | metrics 计算 + plots 可视化 |
| `robustness/` | Stress A/B/C 测试 + Strategy 1/2 策略 + 流式 ensemble |
| `experiments/` | 14 个编排脚本，逐一运行各实验阶段 |
| `predict.py` | CLI 推理入口，支持 4 种预测策略 |
| `artifacts/` | joblib 序列化的训练产物 |

---

## 总结

| 阶段 | 关键操作 | 问题数 | 已解决 |
|---|---|---|---|
| Phase 1: 文件清单 | 梳理 77 个产出文件的来源 | 12 个孤立文件 | 已标注 |
| Phase 2: CLI 审计 | 验证 predict.py 4 条命令 | 3 个 bug | 全部修复 |
| Phase 3: GPU 排查 | 全项目搜索 torch/cuda 引用 | 0 (torch 未使用) | N/A |
