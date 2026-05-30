# 网络入侵检测项目 — 完整实施方案（最终版）

> 项目: Robust Multi-Class Network Intrusion Detection
> 课程: ML Innovation - Spring 2026, Kean University
> 数据集: NF-UQ-NIDS-v3 (NF-UNSW-NB15-v3 + NF-CSE-CIC-IDS2018-v3)
> 模型栈: Majority Class + Logistic Regression + Random Forest + XGBoost
> 改进策略: 置信度阈值拒绝 + 集成学习不一致检测

---

## Language Convention

All code, comments, docstrings, variable names, figure titles, plot labels,
legends, tables, logs, reports, notes, and documentation in this project
must be written entirely in English.

Chinese should not appear in source code, experiment outputs, visualizations,
or final report artifacts in order to maintain consistency, reproducibility,
and academic professionalism.


## 数据验证发现（2026-04-28 验证）

在编写本方案前，已完成对实际数据文件的验证，以下发现已纳入方案：

| # | 发现 | 影响 |
|---|------|------|
| 1 | 数据是 **v3** 版本（非 omar.md 中的 v2），原始 CSV 共 55 列（含标签列、IP列、时间戳列），建模用特征列由最终特征列表确定 | config.py 特征列表已适配 v3 |
| 2 | **`Label` 列是二值（0=Benign, 1=Attack），`Attack` 列才是多类目标**（与 omar.md 描述相反） | 多类分类目标列 = `Attack` |
| 3 | UNSW 数据无 >30% 缺失率列（v3 已预清理） | 缺失值处理策略调整为语义填充 |
| 4 | L7_PROTO 含 ~24k 非整数值（如 7.126, 7.212, 7.253） | 必须先 round+int 再编码 |
| 5 | Worms 仅 158 条（0.007%），极度稀有 | 默认使用 `class_weight` / `sample_weight` 处理类别不平衡。如果消融实验中使用 SMOTE，则 `k_neighbors=1`，报告中讨论 SMOTE 对极少样本类的局限性 |
| 6 | CICIDS2018 有 2011 万行 | Stress B 评估必须采样（10%），否则内存溢出 |

### NF-UQ-NIDS-v3 Column Description（来自 modify.md）

This project uses the NF-UQ-NIDS-v3 dataset collection. The raw CSV files contain 55 columns in total, including feature columns, label columns, timestamp columns, and IP address columns.

For modeling, the following columns are removed:
- `Attack` (target, kept separately as y)
- `Label` (binary label, for auxiliary evaluation)
- `FLOW_START_MILLISECONDS`, `FLOW_END_MILLISECONDS` (timestamps)
- `IPV4_SRC_ADDR`, `IPV4_DST_ADDR` (IP addresses)

The final modeling feature list is determined after removing label columns, IP address columns, and timestamp columns. The selected raw feature columns will be saved to `data/metadata/feature_columns.json`. This avoids hard-coding an incorrect feature count and ensures that all experiments use the same feature list.

### 实际类别分布（NF-UNSW-NB15-v3, 总计 2,365,424 行）

| 类别 | 样本数 | 占比 | 稀有度 |
|------|--------|------|--------|
| Benign | 2,237,731 | 94.60% | 多数 |
| Exploits | 42,748 | 1.81% | — |
| Fuzzers | 33,816 | 1.43% | — |
| Generic | 19,651 | 0.83% | — |
| Reconnaissance | 17,074 | 0.72% | — |
| DoS | 5,980 | 0.25% | — |
| Backdoor | 4,659 | 0.20% | — |
| Shellcode | 2,381 | 0.10% | 稀有 |
| Analysis | 1,226 | 0.05% | 稀有 |
| Worms | **158** | 0.007% | 极度稀有 |

---

## 报告与实验追踪策略（来自 final_advice.md）

本项目采用 **"阶段性记录 + 最终统一整理"** 的方式，不在每完成一个阶段后单独撰写完整正式报告，而是在每个阶段保存必要的实验产物（结果表、关键图表、简短实验记录和模型配置），最终统一整合进 `final_report.md`。

### 核心原则

- 每个实验阶段保存 `.csv` 格式的结果表
- 每个重要分析保存 `.png` 或 `.pdf` 图表
- 每个阶段维护简短的 `.md` notes
- 每个训练流程保存关键配置（feature list, class mapping, threshold, model parameters）

### 推荐目录结构（与 final_advice.md 对齐）

```
project/
├── data/
│   ├── NF-UNSW-NB15-v3.csv
│   ├── NF-CSE-CIC-IDS2018-v3.csv
│   ├── processed/
│   └── metadata/
│       ├── feature_columns.json
│       ├── common_features_unsw_cicids.json
│       └── class_mapping.json
│
├── preprocessing/
│   ├── __init__.py
│   ├── preprocess.py
│   └── balance.py
│
├── models/
│   ├── __init__.py
│   ├── baseline.py
│   └── chosen_model.py
│
├── robustness/
│   ├── __init__.py
│   ├── stress_tests.py
│   └── strategies.py
│
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py
│   └── plots.py
│
├── experiments/
│   ├── validate_data.py
│   ├── run_eda.py
│   ├── prepare_data.py
│   ├── run_baseline.py
│   ├── run_stress.py
│   ├── run_strategies.py
│   ├── run_ablation.py
│   └── run_failure_analysis.py
│
├── results/
│   ├── baseline_results.csv
│   ├── stress_a_results.csv
│   ├── stress_b_results.csv
│   ├── stress_c_results.csv
│   ├── strategy_comparison.csv
│   └── ablation_results.csv
│
├── reports/
│   ├── figures/
│   │   ├── class_distribution.png
│   │   ├── confusion_matrix.png
│   │   ├── stress_a_unknown_confidence.png
│   │   ├── stress_b_domain_shift.png
│   │   └── stress_c_degradation_curve.png
│   ├── notes/
│   │   ├── data_and_eda_notes.md
│   │   ├── baseline_results.md
│   │   ├── stress_test_results.md
│   │   └── strategy_failure_analysis.md
│   └── final_report.md
│
├── artifacts/
│   ├── best_model.joblib
│   ├── preprocessor.joblib
│   ├── class_mapping.json
│   ├── strategy_config.json
│   ├── training_config.json
│   └── ensemble_models/
│
├── README.md
└── implementation_plan.md
```

### 数据集角色（来自 final_advice.md §5）

| 数据集 | 角色 |
|--------|------|
| **NF-UNSW-NB15-v3** | 主训练和评估数据集；用于 Baseline 多类分类、Stress Test A、Stress Test C、训练鲁棒性策略 |
| **NF-CSE-CIC-IDS2018-v3** | 外部测试数据集；用于 Stress Test B、评估跨数据集泛化能力 |

### Label 列说明

- `Attack`: 多类目标列，用于主分类任务
- `Label`: 二值标签列（0=Benign, 1=Attack），仅用于二值攻击/正常评估

### Target Column Rule（来自 modify.md）

The main multi-class classification task uses:

```python
y = df["Attack"]
```

The `Label` column is not used as the target for the main multi-class classification task. `Label` is only used for binary attack / normal evaluation, especially in Stress Test B or auxiliary binary analysis.

| Column   | Meaning                              | Usage                      |
| -------- | ------------------------------------ | -------------------------- |
| `Attack` | Multi-class attack category          | Main classification target |
| `Label`  | Binary label, 0 = Benign, 1 = Attack | Binary evaluation only     |

### File Naming and Path Convention（来自 modify.md）

All raw dataset CSV files are stored directly under the `data/` directory (not `data/raw/`).

Required datasets:

```text
data/NF-UNSW-NB15-v3.csv
data/NF-CSE-CIC-IDS2018-v3.csv
```

`NF-UNSW-NB15-v3.csv` is the main training and in-domain evaluation dataset.

`NF-CSE-CIC-IDS2018-v3.csv` is the external target-domain dataset used for Stress Test B.

The shorter name `NF-CICIDS2018-v3.csv` will not be used in the implementation to avoid file path ambiguity.

Processed data, metadata, and split files will be saved under:

```text
data/processed/
data/metadata/
```

### Output Convention（来自 modify.md）

All numeric result tables will be saved under `results/`.

All report-ready figures will be saved under `reports/figures/`.

All short stage notes will be saved under `reports/notes/`.

All trained models, fitted preprocessors, label encoders, and configuration files will be saved under `artifacts/`.

### Feature Column Metadata（来自 modify.md）

The final raw feature list used for model training will be saved to `data/metadata/feature_columns.json`. This file records the feature columns after removing labels, IP address columns, and timestamp columns.

It is used for:
- consistent train / validation / test preprocessing;
- Stress B common-feature alignment;
- validating input columns in `predict.py`;
- ensuring reproducibility of final experiments.

### Stage-Level Notes（最少维护 4 个）

| Notes 文件 | 位置 | 用途 |
|------------|------|------|
| `data_and_eda_notes.md` | `reports/notes/` | 数据准备、版本、字段验证、EDA 发现 |
| `baseline_results.md` | `reports/notes/` | 基线模型结果、最佳模型选择、混淆矩阵分析 |
| `stress_test_results.md` | `reports/notes/` | Stress A/B/C 设置与结果 |
| `strategy_failure_analysis.md` | `reports/notes/` | 策略实现、消融研究、失败案例分析 |

### 可复现性

- 所有实验使用固定随机种子: `SEED = 42`
- 保存 artifacts 以确保可复现:
  - `best_model.joblib` — 最佳模型
  - `preprocessor.joblib` — 拟合后的预处理器
  - `class_mapping.json` — 类别映射
  - `strategy_config.json` — 策略配置（含选定阈值）
  - `training_config.json` — 训练配置

---

## 目录

- [Phase 1: 项目骨架搭建 + 全局配置](#phase-1-项目骨架搭建--全局配置)
- [Phase 2a: EDA — 探索性数据分析](#phase-2a-eda--探索性数据分析)
- [Phase 2b: 预处理流水线](#phase-2b-预处理流水线)
- [Phase 3: 基线分类器](#phase-3-基线分类器)
- [Phase 4a: Stress Test A — 保留攻击类（开集条件）](#phase-4a-stress-test-a--保留攻击类开集条件)
- [Phase 4b: Stress Test B + C — 分布偏移 + 特征退化](#phase-4b-stress-test-b--c--分布偏移--特征退化)
- [Phase 5a: 改进策略 1 — 置信度阈值拒绝](#phase-5a-改进策略-1--置信度阈值拒绝)
- [Phase 5b: 改进策略 2 — 集成学习不一致检测](#phase-5b-改进策略-2--集成学习不一致检测)
- [Phase 5c: run_strategies.py + 统计显著性](#phase-5c-run_strategiespy--统计显著性)
- [Phase 6: 消融研究 + 失败分析](#phase-6-消融研究--失败分析)
- [Phase 7: predict.py + 报告 + README](#phase-7-predictpy--报告--readme)
- [附录 A: 关键警告清单](#附录-a-关键警告清单)
- [附录 B: 执行时间线](#附录-b-执行时间线)

---

## Phase 1: 项目骨架搭建 + 全局配置

### 1.1 目录结构

```
E:\AgentPV\
├── data/
│   └── README.md               # 数据集下载说明（不提交原始数据）
├── preprocessing/
│   ├── __init__.py
│   ├── preprocess.py            # 清洗、编码、归一化、划分
│   └── balance.py               # SMOTE + class_weight 计算
├── models/
│   ├── __init__.py
│   ├── baseline.py              # Majority + LogisticRegression + RandomForest
│   └── chosen_model.py          # XGBoost
├── robustness/
│   ├── __init__.py
│   ├── stress_tests.py          # Stress A / B / C 实现
│   └── strategies.py            # 策略1（阈值拒绝）+ 策略2（集成不一致）
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py               # 所有评估指标函数
│   └── plots.py                 # 所有可视化函数
├── experiments/
│   ├── run_baseline.py          # Phase 3: 可复现基线实验
│   ├── run_stress.py            # Phase 4: 可复现压力测试
│   └── run_strategies.py        # Phase 5: 可复现策略实验
├── results/                     # 所有输出图表和报告
├── config.py                    # 全局配置
├── requirements.txt
├── predict.py                   # CLI 原型
└── README.md                    # 项目说明 + 复现指南
```

### 1.2 config.py — 全局配置（最终版）

```python
"""
全局配置: 所有模块共享的配置参数。
随机种子统一管理，确保可复现性。

数据版本: NF-UQ-NIDS-v3
主训练集: NF-UNSW-NB15-v3 (2,365,424 rows × 55 cols)
目标列说明: Label = 二值 (0=Benign), Attack = 多类字符串 (10类)
"""

import random
import numpy as np

# ==================== 随机种子 ====================
SEED = 42

def set_seed(seed=SEED):
    """统一设置所有随机种子"""
    random.seed(seed)
    np.random.seed(seed)

# ==================== 数据路径 ====================
DATA_DIR = "data/"
UNSW_PATH     = DATA_DIR + "NF-UNSW-NB15-v3.csv"      # 主训练集, 2.37M 行
CICIDS_PATH   = DATA_DIR + "NF-CSE-CIC-IDS2018-v3.csv"       # Stress B 目标域, 20.1M 行
BOTIOT_PATH   = DATA_DIR + "NF-BoT-IoT-v3.csv"          # Stress B 第二目标域 (可选)
TONIOT_PATH   = DATA_DIR + "NF-ToN-IoT-v3.csv"          # Stress B 第三目标域 (可选)

# ==================== 预处理参数 ====================
TEST_SIZE  = 0.2
VAL_SIZE   = 0.1          # → train 0.7 / val 0.1 / test 0.2
RANDOM_STATE = SEED

# ==================== 列定义（原始 CSV 55 列，经删除和特征选择后确定最终建模特征列表） ====================
# 删除列: 时间戳 + IP 地址（标识信息，非泛化特征）
DROP_COLUMNS = [
    "FLOW_START_MILLISECONDS", "FLOW_END_MILLISECONDS",
    "IPV4_SRC_ADDR", "IPV4_DST_ADDR",
]

# 类别特征: 协议相关，必须编码
# PROTOCOL: 整数 {1=ICMP, 6=TCP, 17=UDP} → LabelEncoder
# L7_PROTO: 应用层协议，含非整数值需先清理 → LabelEncoder
CATEGORICAL_FEATURES = ["PROTOCOL", "L7_PROTO"]

# 数值特征: 排除类别列和删除列后的数值列（最终建模特征列表保存到 feature_columns.json）
NUMERIC_FEATURES = [
    "L4_SRC_PORT", "L4_DST_PORT",
    "IN_BYTES", "IN_PKTS", "OUT_BYTES", "OUT_PKTS",
    "TCP_FLAGS", "CLIENT_TCP_FLAGS", "SERVER_TCP_FLAGS",
    "FLOW_DURATION_MILLISECONDS", "DURATION_IN", "DURATION_OUT",
    "MIN_TTL", "MAX_TTL",
    "LONGEST_FLOW_PKT", "SHORTEST_FLOW_PKT",
    "MIN_IP_PKT_LEN", "MAX_IP_PKT_LEN",
    "SRC_TO_DST_SECOND_BYTES", "DST_TO_SRC_SECOND_BYTES",
    "RETRANSMITTED_IN_BYTES", "RETRANSMITTED_IN_PKTS",
    "RETRANSMITTED_OUT_BYTES", "RETRANSMITTED_OUT_PKTS",
    "SRC_TO_DST_AVG_THROUGHPUT", "DST_TO_SRC_AVG_THROUGHPUT",
    "NUM_PKTS_UP_TO_128_BYTES", "NUM_PKTS_128_TO_256_BYTES",
    "NUM_PKTS_256_TO_512_BYTES", "NUM_PKTS_512_TO_1024_BYTES",
    "NUM_PKTS_1024_TO_1514_BYTES",
    "TCP_WIN_MAX_IN", "TCP_WIN_MAX_OUT",
    "ICMP_TYPE", "ICMP_IPV4_TYPE",
    "DNS_QUERY_ID", "DNS_QUERY_TYPE", "DNS_TTL_ANSWER",
    "FTP_COMMAND_RET_CODE",
    "SRC_TO_DST_IAT_MIN", "SRC_TO_DST_IAT_MAX",
    "SRC_TO_DST_IAT_AVG", "SRC_TO_DST_IAT_STDDEV",
    "DST_TO_SRC_IAT_MIN", "DST_TO_SRC_IAT_MAX",
    "DST_TO_SRC_IAT_AVG", "DST_TO_SRC_IAT_STDDEV",
]

# 协议相关特征（缺失时填充 0，因 0 = 协议不适用，有语义意义）
# 注意: 这些列必须从 NUMERIC_FEATURES 中排除，使用单独的 protocol pipeline
PROTOCOL_FEATURES = [
    "ICMP_TYPE", "ICMP_IPV4_TYPE",
    "DNS_QUERY_ID", "DNS_QUERY_TYPE", "DNS_TTL_ANSWER",
    "FTP_COMMAND_RET_CODE",
]

# 从 NUMERIC_FEATURES 中排除 PROTOCOL_FEATURES（必须在 PROTOCOL_FEATURES 定义之后执行）
NUMERIC_FEATURES = [c for c in NUMERIC_FEATURES if c not in PROTOCOL_FEATURES]

# 目标列: Label = 二值, Attack = 多类（注意 v3 与 omar.md 描述相反）
LABEL_COL   = "Label"     # 二值: 0=Benign, 1=Attack
ATTACK_COL  = "Attack"    # 多类目标: "Benign", "DoS", "Exploits", ...

# ==================== 模型参数（网格搜索范围） ====================
LR_PARAMS = {
    "C": [0.01, 0.1, 1, 10],
    "penalty": ["l2"],
    "solver": ["lbfgs"],
    "max_iter": [1000],
}
RF_PARAMS = {
    "n_estimators": [100, 200],
    "max_depth": [10, 20, None],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [1, 2],
    "class_weight": ["balanced"],
}
XGB_PARAMS = {
    "n_estimators": [100, 200],
    "max_depth": [6, 10],
    "learning_rate": [0.01, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
}

# ==================== Stress Test 参数 ====================
# 策略: 第一组选3个最稀有类，第二组选3个中等频率类
HELD_OUT_CLASSES_SETS = [
    ["Worms", "Analysis", "Shellcode"],     # 最稀有3类
    ["Backdoor", "DoS", "Fuzzers"],          # 中等频率3类
]

GAUSSIAN_NOISE_STDS = [0.1, 0.5, 1.0]
MASKING_RATES       = [0.1, 0.25, 0.5]
FEATURE_DROPOUT_COUNTS = [2, 4, 6]          # 按特征重要性排序丢弃
SIGNIFICANCE_RUNS   = 5                      # 统计显著性重复次数
SIGNIFICANCE_SEEDS  = [42, 123, 456, 789, 1111]

# Stress B: CICIDS 数据集巨大 (20M行)，必须采样
STRESS_B_SAMPLE_FRAC = 0.1  # 10% 分层采样 ≈ 200万行

# ==================== 改进策略参数 ====================
TAU_RANGE = (0.5, 0.99, 0.01)    # start, stop, step
ENSEMBLE_SIZE = 5
ENSEMBLE_MODELS = ["rf", "rf", "xgb", "lr", "rf"]  # 异构集成
```

### 1.3 requirements.txt

```txt
pandas>=2.0.0
numpy>=1.26.0
scikit-learn>=1.5.0
xgboost>=2.0.0
imbalanced-learn>=0.12.0
matplotlib>=3.9.0
seaborn>=0.13.0
scipy>=1.13.0
```

---

## Phase 2a: EDA — 探索性数据分析

**文档警告: 不跳过 EDA。跳过 EDA 的组通常在 Week 5 才发现数据问题，为时已晚。**

### 2a.1 数据加载与概览

```python
df = pd.read_csv(UNSW_PATH, low_memory=False)
print("Shape:", df.shape)              # (2365424, 55)
print("Memory:", df.memory_usage(deep=True).sum() / 1e6, "MB")
print("Dtypes:\n", df.dtypes.value_counts())
```

### 2a.2 缺失值分析

```python
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_report = pd.DataFrame({"count": missing, "pct": missing_pct})
missing_report = missing_report[missing_report["count"] > 0].sort_values("count", ascending=False)
```

**决策规则**:
| 缺失率 | 策略 |
|--------|------|
| > 50% | 分析原因后决定：删除或标记为"不适用" |
| 5%–50% | 协议相关列 → 填 0；流量统计列 → 填中位数 |
| < 5% | 中位数填充 |

### 2a.3 L7_PROTO 数据质量检查（v3 特有）

```python
# L7_PROTO 是 float64，含非整数值 (如 7.126, 7.212, 7.253)
l7 = df['L7_PROTO'].dropna()
decimal_mask = l7 % 1 != 0
print(f"非整数值: {decimal_mask.sum()} / {len(l7)} ({decimal_mask.mean()*100:.2f}%)")
print("非整数值样例:", sorted(l7[decimal_mask].unique())[:30])
# 预期: ~24k 非整数值
# 处理: fillna(0) → round() → astype(int) → LabelEncoder
```

### 2a.4 类别分布分析

```python
class_dist = df[ATTACK_COL].value_counts()
class_dist_pct = df[ATTACK_COL].value_counts(normalize=True) * 100
# 生成 class_distribution.png（柱状图，对数 y 轴）
```

**关注点**: Worms(158) 极度稀有。SMOTE 对该类的合成样本可能不真实，需在报告中讨论。

### 2a.5 特征统计量

```python
desc = df[NUMERIC_FEATURES].describe().T
# 关注:
# - 量纲差异 (IN_BYTES max 可达 10^9)
# - 是否需要 log 变换
# - FLOW_DURATION_MILLISECONDS 分布形态（通常高度偏态）
```

### 2a.6 相关性分析

```python
corr = df[NUMERIC_FEATURES].corr()
# 标注 |r| > 0.85 的高相关对
# 高相关对 → Stress C 中删除其中一个不会显著影响性能
```

### 2a.7 按攻击类别的特征分布

```python
# 选取关键特征: IN_BYTES, OUT_BYTES, FLOW_DURATION_MILLISECONDS, PROTOCOL
# 按 Attack 类别分组画箱线图 / KDE
# 意义: 为 Stress A 的定性分析提供特征层面的证据
```

### 2a.8 按攻击类别的 PROTOCOL 分布

```python
# 某些攻击可能只在特定协议上发生
# pd.crosstab(df[ATTACK_COL], df['PROTOCOL'], normalize='index')
# 意义: 如果 Worms 只出现在 TCP → 分类器可能基于 PROTOCOL 区分
```

### EDA 产出检查清单

- [ ] `data_eda_report.txt` — 所有统计量汇总
- [ ] `class_distribution.png` — 类别分布柱状图（对数坐标）
- [ ] `correlation_heatmap.png` — 特征相关性热力图
- [ ] `feature_distribution_by_class.png` — IN_BYTES/OUT_BYTES/DURATION 按类分布
- [ ] `protocol_by_class.png` — 各类的 PROTOCOL 分布
- [ ] `l7_proto_quality.png` — L7_PROTO 非整数值分布
- [ ] 缺失值报告 + 处理决策

---

## Phase 2b: 预处理流水线

### 2b.1 preprocess.py — 基于 sklearn Pipeline / ColumnTransformer 的预处理

**核心原则: 使用 sklearn Pipeline + ColumnTransformer 管理所有预处理步骤。fit 只发生在训练集，transform 应用于 val/test。ColumnTransformer 自动区分数值列和类别列的不同处理路径，防止数据泄露。**

```
数据流:
┌──────────┐     ┌──────────┐     ┌───────────────┐
│ 原始数据  │ ──→ │ train 70% │ ──→ │ fit Imputer   │
│          │     │ val   10% │     │ fit Encoder   │
│          │     │ test  20% │     │ fit Scaler    │
└──────────┘     └──────────┘     └───────┬───────┘
                                          ↓
                                transform train/val/test
```

**函数接口**:

```python
def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    1. 读取 CSV (low_memory=False, 处理混合类型)
    2. 删除 DROP_COLUMNS (时间戳 + IP地址)
    3. 基本类型检查和清理
    返回清洗后 DataFrame
    """

def clean_l7_proto(df: pd.DataFrame) -> pd.DataFrame:
    """
    L7_PROTO 特殊处理 (v3关键步骤):
    1. fillna(0) — NaN 表示无应用层协议
    2. round() → astype(int) — 清理 7.126 等非整数值
    3. 转为 category 类型
    注意: 此函数必须在 split 之前调用，确保所有划分一致
    """

def split_data(df, stratify_col=ATTACK_COL):
    """
    70/10/20 分层划分 → 固定 random_state=SEED
    验证各类在 train/val/test 中比例一致
    返回 (X_train, X_val, X_test, y_train, y_val, y_test)
    """

def build_preprocessor() -> ColumnTransformer:
    """
    构建 sklearn ColumnTransformer，包含两条处理路径:

    numeric pipeline:
      SimpleImputer(strategy='median') → StandardScaler()

    categorical pipeline:
      SimpleImputer(strategy='constant', fill_value=0) → OrdinalEncoder

    协议相关特征 (ICMP_TYPE, DNS_*, FTP_* 等) 的缺失值用 0 填充
    (语义: 0 = 协议不适用)，此逻辑通过 categorical pipeline 的
    constant imputer 或单独定义 PROTOCOL_FEATURES 的 pipeline 处理。

    返回 ColumnTransformer 对象 (未 fit)
    """

def fit_preprocessor(X_train: pd.DataFrame) -> ColumnTransformer:
    """
    在训练集上 fit ColumnTransformer。
    之后用同一个 preprocessor.transform() 处理 val 和 test。
    返回 fit 好的 ColumnTransformer
    """

def preprocess_pipeline(filepath: str) -> dict:
    """
    端到端调用:

    1. load_and_clean_data(filepath)     → 原始清洗
    2. clean_l7_proto(df)                → L7_PROTO 非整数值处理
    3. split_data(df)                    → 分层 70/10/20 划分
    4. build_preprocessor()              → 构建 ColumnTransformer
    5. preprocessor.fit(X_train)         → 只在 train 上 fit
    6. X_train = preprocessor.transform(X_train)
       X_val   = preprocessor.transform(X_val)
       X_test  = preprocessor.transform(X_test)

    返回 dict: {
        X_train, X_val, X_test,
        y_train, y_val, y_test,
        preprocessor, class_names
    }
    """
```

**ColumnTransformer 结构示例**（来自 modify.md）:

Protocol-specific features such as `ICMP_TYPE`, `DNS_QUERY_ID`, `DNS_QUERY_TYPE`, and `FTP_COMMAND_RET_CODE` are processed separately from regular numeric features. Their missing values are filled with 0 because 0 has semantic meaning: the protocol-specific field is not applicable to the current flow. This prevents protocol-related missing values from being replaced by median values, which would be semantically incorrect.

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder

def build_preprocessor(
    numeric_features=NUMERIC_FEATURES,
    protocol_features=PROTOCOL_FEATURES,
    categorical_features=CATEGORICAL_FEATURES
):
    """
    numeric_features:     Median imputation + standard scaling.
    protocol_features:    Constant 0 imputation + standard scaling.
    categorical_features: Constant 0 imputation + OrdinalEncoder.
    """

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    protocol_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
        ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value",
                                    unknown_value=-1)),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipeline, numeric_features),
        ("protocol", protocol_pipeline, protocol_features),
        ("cat", categorical_pipeline, categorical_features),
    ])

    return preprocessor
```

**与 Stress B 的兼容性**: 训练阶段 fit 好的 preprocessor 保存为文件 (joblib)，Stress B 加载 CICIDS 数据后直接调用 `preprocessor.transform()`，不再重新 fit。这与 Stress B 的 "UNSW 训练 → CICIDS 测试" 设计一致。

### Multi-Class Label Encoding for XGBoost（来自 modify.md）

The main target column `Attack` contains string labels (`Benign`, `Exploits`, `Fuzzers`, etc.). Before training XGBoost, these labels must be encoded into integer class IDs. The label encoder must be fitted only on the training labels and then reused for validation, test, stress tests, and inference.

```python
from sklearn.preprocessing import LabelEncoder
import joblib
import json

label_encoder = LabelEncoder()

y_train_enc = label_encoder.fit_transform(y_train)
y_val_enc = label_encoder.transform(y_val)
y_test_enc = label_encoder.transform(y_test)

joblib.dump(label_encoder, "artifacts/label_encoder.joblib")

class_mapping = {
    int(i): str(cls)
    for i, cls in enumerate(label_encoder.classes_)
}

with open("artifacts/class_mapping.json", "w") as f:
    json.dump(class_mapping, f, indent=2)
```

During inference, predicted integer class IDs will be converted back to attack names using the saved label encoder.

**XGBoost LabelEncoder Usage Rule（来自 modify.md）**: For every XGBoost training or prediction step across the entire project, `y_train`, `y_val`, and `y_test` must be encoded with the saved `LabelEncoder`. Random Forest and Logistic Regression may use string labels directly, but XGBoost should consistently use encoded integer labels. After prediction, encoded class IDs must be converted back to attack names before reporting or binary mapping. This applies to all phases: baseline, Stress A, Stress B, Stress C, ensemble, and ablation experiments.

The following files must be saved:
- `artifacts/label_encoder.joblib`
- `artifacts/class_mapping.json`

### Categorical Encoding Decision（来自 modify.md）

This project uses `OrdinalEncoder` for categorical features such as `PROTOCOL` and `L7_PROTO` to reduce memory usage on the large v3 datasets. This encoding is acceptable for tree-based models such as Random Forest and XGBoost.

Logistic Regression is included as a simple baseline model. Since linear models can be sensitive to artificial ordinal relationships introduced by ordinal encoding, Logistic Regression results will be interpreted mainly as a baseline reference rather than the primary final model.

If time allows, Logistic Regression will use a separate preprocessing pipeline with OneHotEncoder for categorical features, while Random Forest and XGBoost will use OrdinalEncoder for memory efficiency. However, adopting the simpler approach (OrdinalEncoder for all models) is acceptable for this project.

### 2b.2 balance.py — 类平衡处理

**默认策略: class_weight / sample_weight。SMOTE 仅作为 Phase 6 消融实验的可选对比项，不纳入默认训练流程。**

理由: SMOTE 在网络流量数据上容易产生不真实的合成样本，尤其是对极度稀有类 (Worms=158, k_neighbors=1 时合成多样性严重受限)。class_weight / sample_weight 是 sklearn/XGBoost 内建支持的方案，不改变数据分布，更安全可靠。

```python
def get_class_weights(y_train) -> dict:
    """
    计算 class_weight = n_samples / (n_classes * np.bincount(y))
    用于 sklearn 模型的 class_weight 参数 (LR, RF)
    """

def compute_sample_weights(y_train) -> np.ndarray:
    """
    返回每个样本的权重数组，用于 XGBoost 的 sample_weight 参数
    权重 = n_samples / (n_classes * count_per_class)
    """

def apply_smote(X_train, y_train, random_state=SEED):
    """
    [仅用于 Phase 6 消融实验]
    SMOTE 过采样少数类。

    特殊处理: 对 Worms(158条) 类，SMOTE 的 k_neighbors 必须
    ≤ min(class_count) - 1。默认 k_neighbors=5 对 Worms 会报错，
    需设 k_neighbors=1 (权衡: 合成多样性差但不会报错)。

    打印: 处理前/后各类样本数
    返回 (X_resampled, y_resampled)
    """
```

**类别不平衡处理总结**:

| 策略 | 默认使用 | 说明 |
|------|---------|------|
| class_weight='balanced' | LR, RF 的默认参数 | sklearn 内建，自动计算逆频率权重 |
| sample_weight | XGBoost 的默认参数 | 同上，通过 sample_weight 参数传入 |
| SMOTE | 仅 Phase 6 消融 | 合成少数类样本，需在报告中讨论其对极度稀有类的局限性 |

### 2b.3 metrics.py — 评估指标库

```python
def classification_report_full(y_true, y_pred, classes, digits=4):
    """Per-class precision/recall/f1 + macro + weighted F1, 格式化表格"""

def confusion_matrix_df(y_true, y_pred, classes):
    """带行列标签的混淆矩阵 DataFrame"""

def macro_f1_score(y_true, y_pred):
    """宏平均 F1 (对所有类平等)"""

def weighted_f1_score(y_true, y_pred):
    """加权平均 F1 (按样本数加权)"""

def confidence_analysis(y_prob, y_true, classes):
    """
    每个样本: 预测类, 置信度(max概率), 是否正确, 真实类
    返回 DataFrame — 用于 Stress A 置信度分布分析
    """

def coverage_accuracy_curve(y_prob, y_true, tau_range):
    """
    扫描 τ: 每个 τ → (coverage, accuracy)
    coverage = 置信度 ≥ τ 的样本占比
    accuracy  = 覆盖样本中的正确率
    返回 DataFrame
    """

def per_class_confidence_stats(y_prob, y_true, classes):
    """
    每类的平均置信度、标准差、中位数
    区分 正确预测 和 错误预测 的置信度
    """

def degradation_curve_table(degradation_levels, metric_values):
    """退化数据表: 退化等级 × metric"""

def run_statistics(results: list):
    """
    输入: 5次运行的 metric 值列表
    返回: f"{mean:.4f} ± {std:.4f}"
    """

def mcnemar_test(y_true, pred_a, pred_b):
    """
    McNemar's 检验: 比较两个分类器的预测差异是否显著
    返回: (chi2_statistic, p_value)
    """

def kl_divergence(p, q, epsilon=1e-10):
    """KL散度 — 量化 Stress B 中特征分布偏移"""

def ks_test_two_samples(sample1, sample2):
    """KS 检验 — 比较两个分布是否来自同一总体"""

def calculate_ece(y_prob, y_true, n_bins=10):
    """
    Expected Calibration Error
    [Future Work] 校准分析不纳入本次实验范围。
    若后续需要，可用于评估模型的概率校准质量。
    """

def disagreement_auroc(disagreement_scores, y_true_is_wrong):
    """
    AUROC of disagreement score as wrong-prediction detector
    用于策略2评估
    """
```

### 2b.4 plots.py — 可视化函数

```python
def plot_class_distribution(y, class_names, save_path):
    """类别分布柱状图 (对数 y 轴)"""

def plot_confusion_matrix(cm, classes, save_path, normalize=False):
    """混淆矩阵热力图"""

def plot_feature_importance(importances, feature_names, save_path, top_k=20):
    """特征重要性 Top-K 柱状图"""

def plot_confidence_distribution(conf_df, save_path):
    """
    置信度分布箱线图:
    - 按类别分组
    - 区分 correct / wrong
    - 标注 unknown class
    """

def plot_coverage_accuracy_curve(tau_results, save_path):
    """覆盖率-准确率曲线 (策略1)"""

def plot_degradation_curve(degradation_dict, save_path):
    """
    退化曲线: 多条线 (噪声/掩码/丢弃) × 多个等级
    x=退化程度, y=Macro-F1
    """

def plot_disagreement_histogram(disagreement, is_wrong, save_path):
    """不一致度分布: 正确预测 vs 错误预测 重叠直方图"""

def plot_feature_distribution_comparison(source_values, target_values,
                                          feature_name, save_path):
    """源域 vs 目标域 某特征分布对比 (Stress B)"""

def plot_reliability_diagram(y_prob, y_true, n_bins, save_path):
    """可靠性图 [Future Work: 校准分析]"""
```

### Phase 2b 产出检查清单

- [ ] `preprocess.py` — 基于 sklearn ColumnTransformer 的流水线 (含 L7_PROTO 清理)
- [ ] `balance.py` — class_weight + sample_weight (SMOTE 仅消融用)
- [ ] `metrics.py` — 全部评估函数
- [ ] `plots.py` — 全部绘图函数
- [ ] **数据泄露检查**: ColumnTransformer 只 fit train, transform val/test
- [ ] **分层划分验证**: train/val/test 各类比例一致
- [ ] **L7_PROTO 验证**: 编码前无 NaN，无小数

---

## Phase 3: 基线分类器

### 3.1 models/baseline.py

```python
class MajorityClassifier:
    """总是预测训练集中出现次数最多的类 (floor baseline)"""
    def fit(self, X, y):
        self.majority_class = y.value_counts().index[0]
        self.classes_ = sorted(y.unique())
    def predict(self, X):
        return np.full(len(X), self.majority_class)
    def predict_proba(self, X):
        proba = np.zeros((len(X), len(self.classes_)))
        idx = self.classes_.index(self.majority_class)
        proba[:, idx] = 1.0
        return proba

def train_logistic_regression(X_train, y_train, X_val, y_val, param_grid=LR_PARAMS):
    """
    LogisticRegression(max_iter=1000, class_weight='balanced')
    GridSearchCV on 10% tuning subset → best_params_ → full training
    返回 (best_model, best_params, cv_results_df)
    """

def train_random_forest(X_train, y_train, X_val, y_val, param_grid=RF_PARAMS):
    """
    RandomForestClassifier(n_jobs=-1, random_state=SEED)
    GridSearchCV on 10% tuning subset → best_params_ → full training
    返回 (best_model, best_params, cv_results_df)
    """
```

### 3.2 models/chosen_model.py

```python
def train_xgboost(X_train, y_train, X_val, y_val, param_grid=XGB_PARAMS):
    """
    XGBClassifier(
        objective='multi:softprob',
        eval_metric='mlogloss',
        early_stopping_rounds=20,
        random_state=SEED,
        n_jobs=-1,
    )
    GridSearchCV on 10% tuning subset → best_params_ → full training
    返回 (best_model, best_params, cv_results_df)
    """
```

### 3.3 GPU 加速（来自 final_advice.md §10）

由于 NF-UQ-NIDS-v3 数据规模较大，部分模型训练可能需要较长时间。GPU 加速不是项目成功的必要条件，但可以显著减少训练时间。

**各模型 GPU 支持情况**:

| 模型 | GPU 支持 | 本项目使用 |
|------|----------|-----------|
| Majority Classifier | 不需要 | CPU only |
| Logistic Regression | 通常 CPU | CPU only |
| Random Forest | 通常 CPU | CPU only |
| XGBoost | 支持 GPU | **GPU preferred** |

**XGBoost GPU 配置**:

```python
from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    eval_metric="mlogloss",
    tree_method="hist",
    device="cuda",          # GPU 加速
    random_state=42
)
```

**CPU 降级方案** (当 GPU 不可用时):

```python
model = XGBClassifier(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    eval_metric="mlogloss",
    tree_method="hist",     # 仍使用 hist 但无 device="cuda"
    random_state=42
)
```

**降低训练成本的策略**:
- 使用小规模验证集进行超参数搜索
- 保存模型和预处理器（joblib）
- 使用 `class_weight` 而非 SMOTE
- 仅对 XGBoost 使用 GPU
- 如果时间有限，限制可选实验

**GPU Availability and CPU Fallback（来自 modify.md）**:

GPU acceleration is optional. The implementation should automatically fall back to CPU training if CUDA is not available.

```python
def get_xgb_device(use_gpu: bool):
    if use_gpu:
        return {
            "tree_method": "hist",
            "device": "cuda",
        }
    else:
        return {
            "tree_method": "hist",
        }
```

If GPU training fails due to unavailable CUDA or incompatible XGBoost installation, the script should print a warning and rerun XGBoost on CPU. This ensures that all experiments remain reproducible even without GPU access.

### 3.4 调优策略（效率优化）

由于全量数据 236 万行，不在全量上做网格搜索：

```
1. 从 train 中分层抽取 10% (~16.5万行) 作为调优子集
2. 在子集上用 3-fold CV 搜索最佳参数
3. 用最佳参数在全量 train 上训练最终模型
4. 在 full test 上评估
→ 调优时间从数小时降至 ~15分钟，参数质量几乎不变
```

### 3.5 评估每个模型

对每个模型（Majority / LR / RF / XGBoost）：

```python
# 1. 测试集预测
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)

# 2. Per-class 指标
report = classification_report_full(y_test, y_pred, classes)

# 3. 混淆矩阵 + 绘图
cm = confusion_matrix_df(y_test, y_pred, classes)
plot_confusion_matrix(cm, classes, "results/confusion_matrix_{model}.png")

# 4. 训练/推理时间
train_time = t1 - t0
infer_time = per_1000_samples * 1000

# 5. 5次不同种子重复 → mean ± std
for seed in SIGNIFICANCE_SEEDS:
    result = run_one_experiment(seed)
    results.append(result)
print(f"{model}: Macro-F1 = {np.mean(results):.4f} ± {np.std(results):.4f}")
```

### 3.6 定性混淆分析（文档核心要求）

不止报告数字，要分析**为什么**。以下为期望的分析深度：

```markdown
### Shellcode → Exploits (混淆率 ~52%)
- 原因: Shellcode 和 Exploits 都涉及代码执行攻击
- 特征层面: IN_BYTES, OUT_BYTES, FLOW_DURATION 分布高度重叠
- 数量偏差: Shellcode(2381) << Exploits(42748) → 模型偏向多数类

### Worms → Backdoor (混淆率 ~82%)
- 原因: Worms 仅有 158 样本，模型几乎无法学习其特征
- 端口使用模式: Worms 和 Backdoor 在 L4_DST_PORT 上相似
- 结论: 这是数据限制，非模型缺陷

### Reconnaissance → Benign (混淆率 ~15%)
- 原因: 侦查流量的特征（少量包、短连接）与正常 DNS/NTP 流量相似
- 在 PROTOCOL=17(UDP) 上混淆更严重 — UDP 缺乏连接状态信息
```

### Phase 3 产出检查清单

- [ ] 3 个基线 + 1 个自选模型全部训练完成
- [ ] per-class precision/recall/F1 表格
- [ ] 混淆矩阵 × 4 + 定性分析 (≥3 个混淆对)
- [ ] 5次重复的 mean ± std
- [ ] 训练时间 + 推理时间对比表
- [ ] `run_baseline.py` 一键可复现
- [ ] 输出保存到 `results/baseline_*`

---

## Phase 4a: Stress Test A — 保留攻击类（开集条件）

### 4a.1 实验设置

```python
held_out_sets = [
    ["Worms", "Analysis", "Shellcode"],     # 最稀有3类
    ["Backdoor", "DoS", "Fuzzers"],          # 中等频率3类
]

for held_out_classes in held_out_sets:
    # 1. Remove held-out classes from train AND validation
    known_train_mask = ~y_train.isin(held_out_classes)
    known_val_mask = ~y_val.isin(held_out_classes)

    X_train_known = X_train[known_train_mask]
    y_train_known = y_train[known_train_mask]

    X_val_known = X_val[known_val_mask]
    y_val_known = y_val[known_val_mask]

    # 2. Train only on known classes (use known val for early stopping / tuning)
    model = train_on_known(
        X_train_known, y_train_known,
        X_val_known, y_val_known
    )

    # 3. Evaluate on full test set (contains both known and unknown classes)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
```

**Important**: In Stress Test A, held-out classes must be removed from both the training set and the validation set. The model and any strategy thresholds should be selected using only known-class validation samples. The full test set should still contain both known and unknown classes — this allows evaluation of how the model behaves when it encounters unseen attack types.

### Strict Preprocessing Option for Stress Test A（来自 modify.md）

The strict version fits the preprocessor only on known-class training data. This is more rigorous because unknown classes do not influence imputation, encoding, or scaling parameters.

Strict process:

1. Split raw data into train / validation / test.
2. Remove held-out classes from raw train and raw validation.
3. Fit the preprocessor only on known-class raw training data.
4. Transform known-class train, known-class validation, and full test.
5. Train the model on known-class train.
6. Evaluate on full test.

This strict version is recommended if time allows. If implementation time is limited, the minimum required condition is that held-out classes must not be used for model training or threshold selection.

### 4a.2 测量指标

| 指标 | 方法 | 意义 |
|------|------|------|
| Known-class Macro-F1 | 只计算7个已知类的F1 | 与全量训练基线对比 ΔF1 |
| Unknown→Known 映射矩阵 | 每个unknown类→top-3预测分布 | 显示系统性混淆方向 |
| Unknown置信度分布 | unknown样本的 max(p) 分布 | 模型是否"自信地犯错" |
| AUROC of max(p) as unknown detector | ROC曲线 | 量化置信度检测unknown的能力 |
| 语义分析 | 每个unknown类: 为什么映射到特定known类 | 定性理解 |

### 4a.3 表格模板

**Stress A 结果: 保留类 = {Worms, Analysis, Shellcode}**

| 真实类 | 状态 | Top-3 预测 | 平均置信度 | 正确吗 |
|--------|------|-----------|-----------|--------|
| Worms | unknown | Backdoor(43%), Generic(28%), Exploits(15%) | 0.67 | ❌ 全错 |
| Analysis | unknown | Fuzzers(38%), Exploits(31%), Recon(12%) | 0.55 | ❌ 全错 |
| Shellcode | unknown | Exploits(52%), Generic(22%), DoS(8%) | 0.72 | ❌ 全错 |
| Benign | known | Benign(98%) | 0.98 | ✓ |
| Exploits | known | Exploits(85%), Fuzzers(8%) | 0.88 | ✓ |
| ... | ... | ... | ... | ... |

**定性分析示例**:
> Shellcode 被高度自信地误分类为 Exploits (52%, 置信度 0.72)。
> 特征解释: 两者 IN_BYTES 和 OUT_BYTES 分布高度重叠，均值差异 < 0.3σ。
> 语义解释: 两者都涉及代码执行，在 NetFlow 层面无法区分"利用漏洞"和"执行 shellcode"。
> 这在安全监控的语义上是合理的混淆——两种流量都需要安全分析师审查。

### 4a.4 两组必须都做

文档明确规定: **必须至少2组不同的保留类**。只选最稀有类 → 可能结果看起来更好 → 违规。

### Phase 4a 产出检查清单

- [ ] 2组保留类 × 全部指标
- [ ] Known-class ΔF1 vs 基线对比表
- [ ] Unknown 置信度分布箱线图 (known-correct / known-wrong / unknown 三条)
- [ ] AUROC of confidence as unknown detector
- [ ] Unknown→Known 映射矩阵可视化
- [ ] 定性分析 ≥ 3 个具体混淆案例含特征解释
- [ ] 写入 `run_stress.py`

---

## Phase 4b: Stress Test B + C — 分布偏移 + 特征退化

### Stress Test B: 跨数据集分布偏移

#### Stress B 前置: 特征兼容性检查

在执行 UNSW → CICIDS 跨数据集测试前，**必须先检查两个 v3 子集的特征列是否一致**。不能默认直接跑。

**检查内容**:

```text
1. 特征名是否一致
2. 特征数量是否一致
3. 数据类型是否一致
4. 类别特征是否一致 (PROTOCOL, L7_PROTO)
5. 是否存在某些列只在 UNSW 有、CICIDS 没有，或反过来
6. 目标列 Attack 和 Label 是否都存在
```

**检查流程**:

```python
# Step 1: 读取两个数据集的 header
df_unsw = pd.read_csv(UNSW_PATH, nrows=5, low_memory=False)
df_cicids = pd.read_csv(CICIDS_PATH, nrows=5, low_memory=False)

# Step 2: 排除非特征列
exclude_cols = [ATTACK_COL, LABEL_COL] + DROP_COLUMNS
unsw_feature_cols = [c for c in df_unsw.columns if c not in exclude_cols]
cicids_feature_cols = [c for c in df_cicids.columns if c not in exclude_cols]

# Step 3: 比较
only_in_unsw = set(unsw_feature_cols) - set(cicids_feature_cols)
only_in_cicids = set(cicids_feature_cols) - set(unsw_feature_cols)
common_features = sorted(set(unsw_feature_cols).intersection(set(cicids_feature_cols)))

print(f"UNSW 特征数: {len(unsw_feature_cols)}")
print(f"CICIDS 特征数: {len(cicids_feature_cols)}")
print(f"共同特征数: {len(common_features)}")
print(f"仅在 UNSW: {only_in_unsw}")
print(f"仅在 CICIDS: {only_in_cicids}")
```

**决策规则**:

| 检查结果 | 策略 |
|---------|------|
| 特征列**完全一致** | 直接复用 UNSW 训练的 preprocessor，对 CICIDS 做 transform |
| 特征列**不完全一致** | 取 `common_features` 交集，用 common_features 重新训练 UNSW 模型，再用相同 preprocessor 处理 CICIDS |

**使用 common_features 的代码**:

```python
# 如果不一致，用共同特征重新训练
common_features = sorted(
    set(unsw_feature_cols).intersection(set(cicids_feature_cols))
)

X_unsw = df_unsw[common_features]
X_cicids = df_cicids[common_features]

# 使用 common_features 时，必须将共同特征拆分为三类再传入 build_preprocessor
common_numeric_features = [
    c for c in NUMERIC_FEATURES
    if c in common_features
]

common_protocol_features = [
    c for c in PROTOCOL_FEATURES
    if c in common_features
]

common_categorical_features = [
    c for c in CATEGORICAL_FEATURES
    if c in common_features
]

preprocessor = build_preprocessor(
    numeric_features=common_numeric_features,
    protocol_features=common_protocol_features,
    categorical_features=common_categorical_features,
)
preprocessor.fit(X_unsw)
model.fit(preprocessor.transform(X_unsw), y_unsw)
```

**不推荐的策略**: 直接 `X_cicids = df_cicids[UNSW_FEATURES]`（如果 CICIDS 缺列会报错）；也不建议随便给缺失列补 0（除非能解释语义）。

**Important Rule for Common Feature Subset（来自 modify.md）**: If UNSW and CICIDS2018 do not have exactly the same feature columns, the original full-feature UNSW model must not be reused. Instead, the model and preprocessor must be retrained on UNSW using only `common_features`:

1. Identify `common_features`.
2. Select `X_unsw_common = df_unsw[common_features]`.
3. Select `X_cicids_common = df_cicids[common_features]`.
4. Fit a new preprocessor on UNSW common-feature training data only.
5. Train a new UNSW model using common features.
6. Transform CICIDS using the same fitted preprocessor.
7. Evaluate on CICIDS binary attack / normal labels.

This ensures that train and target-domain test inputs have identical columns and preprocessing.

#### Stress B 主体流程

**关键决策**: CICIDS2018 有 20,115,529 行，必须采样。采样必须使用按 `Attack` 分层采样以保持原始攻击类别分布，而不能使用简单随机采样（否则可能破坏少数类比例）。

```python
df_cicids_sampled = (
    df_cicids
    .groupby(ATTACK_COL, group_keys=False)
    .apply(lambda x: x.sample(frac=STRESS_B_SAMPLE_FRAC, random_state=SEED))
    .reset_index(drop=True)
)
```

```python
# 1. 执行特征兼容性检查（见上方）
common_features = check_feature_compatibility(UNSW_PATH, CICIDS_PATH)

# 2. 在 NF-UNSW-NB15-v3 全量训练集上训练最佳模型
model = train_best_model(X_unsw_train[common_features], y_unsw_train)

# 3. 加载目标数据集 + 采样
df_cicids = load_and_clean_data(CICIDS_PATH)
# Stratified sampling by Attack to preserve class distribution
df_cicids = (
    df_cicids
    .groupby(ATTACK_COL, group_keys=False)
    .apply(lambda x: x.sample(frac=STRESS_B_SAMPLE_FRAC, random_state=SEED))
    .reset_index(drop=True)
)

# 4. 用相同的预处理器 transform（绝不重新 fit！）
X_cicids = preprocessor.transform(df_cicids[common_features])

# 5. 标签: 不同子集的攻击类型不同 → 统一为二值
#    Attack=Benign → 0 (Normal), 其他 → 1 (Attack)
y_cicids_binary = (df_cicids[ATTACK_COL] != "Benign").astype(int)
y_unsw_binary  = (y_unsw_test != "Benign").astype(int)
```

**为什么使用二值映射（来自 final_advice.md §7）**:

UNSW 和 CICIDS2018 具有不同的攻击类别体系（例如 UNSW 的 "Exploits" 对应 CICIDS 的 "BruteForce"，UNSW 的 "Fuzzers" 对应 CICIDS 的 "Web Attacks"），多类标签无法直接对齐。因此 Stress Test B 统一按二值（attack/normal）任务评估。多类预测结果通过以下方式转换为二值（来自 modify.md）：

```python
# True CICIDS labels → binary
y_true_binary = (df_cicids[ATTACK_COL] != "Benign").astype(int)

# UNSW model predictions → binary (via label_encoder inverse transform)
y_pred_multiclass = label_encoder.inverse_transform(y_pred_encoded)
y_pred_binary = (y_pred_multiclass != "Benign").astype(int)
```

| Multi-class label    | Binary label |
| -------------------- | ------------ |
| `Benign`             | 0 = Normal   |
| Any non-Benign class | 1 = Attack   |

**标签映射表**:

| UNSW Attack | CICIDS Attack | 统一二值 |
|-------------|---------------|---------|
| Benign | Benign | 0 (Normal) |
| Exploits | BruteForce | 1 (Attack) |
| DoS | DoS / DDoS | 1 (Attack) |
| Fuzzers | Web Attacks | 1 (Attack) |
| ... | ... | 1 (Attack) |

**评估指标**:

```python
metrics = {
    "accuracy":  accuracy_score(y_true, y_pred_binary),
    "precision": precision_score(y_true, y_pred_binary),
    "recall":    recall_score(y_true, y_pred_binary),
    "f1":        f1_score(y_true, y_pred_binary),
    "fpr":       false_positive_rate,     # Benign → Alert
    "fnr":       false_negative_rate,     # Attack → Normal
    "delta_f1":  f1_in_distribution - f1_target,  # 相对退化
}
```

**特征分布偏移量化**:

```python
for feature in NUMERIC_FEATURES:
    # 1. 基本统计量对比
    src_mean, tgt_mean = df_unsw[feature].mean(), df_cicids[feature].mean()

    # 2. KL 散度
    kl = kl_divergence(histogram(src), histogram(tgt))

    # 3. KS 检验 (scipy.stats.ks_2samp)
    ks_stat, ks_pval = ks_2samp(src_sample, tgt_sample)

    # 取 KS 统计量最大的 TOP-5 特征 → 解释为什么这些特征漂移最大

# 可选: t-SNE 可视化源域和目标域样本
```

### Stress Test C: 特征退化

**核心原则: 所有扰动 (noise / masking / feature dropout) 都在 raw 特征层面进行，然后再通过已 fit 的 preprocessor.transform()。不在 OneHotEncoder 后的 processed matrix 上做列丢弃，避免 column index mapping 的复杂性。**

```
数据流 (Stress C):
X_test_raw (copy) → raw-level 扰动 → preprocessor.transform() → model.predict()
```

这样设计的优势:
- 实现最简单，不需要处理 OneHotEncoder 后的列索引
- 与"某个原始特征不可用"的真实部署场景一致
- 避免了 processed-level dropout 需要维护 feature name mapping 的复杂度

**条件 1: 高斯噪声 (仅对数值列)**

```python
for sigma in GAUSSIAN_NOISE_STDS:
    X_noisy_raw = X_test_raw.copy()
    for col in NUMERIC_FEATURES:
        noise = np.random.normal(0, sigma, size=len(X_noisy_raw))
        X_noisy_raw[col] = X_noisy_raw[col] + noise

    # 通过已 fit 的 preprocessor 变换
    X_noisy = preprocessor.transform(X_noisy_raw)
    f1 = evaluate(model, X_noisy, y_test)
```

**条件 2: 随机掩码 (仅对数值列)**

```python
for p in MASKING_RATES:
    X_masked_raw = X_test_raw.copy()
    mask = np.random.rand(*X_masked_raw[NUMERIC_FEATURES].shape) < p
    X_masked_raw[NUMERIC_FEATURES] = X_masked_raw[NUMERIC_FEATURES].mask(mask, 0)

    # 通过已 fit 的 preprocessor 变换
    X_masked = preprocessor.transform(X_masked_raw)
    f1 = evaluate(model, X_masked, y_test)
```

**条件 3: Feature dropout (对指定 raw 列置零, k ∈ [2, 4, 6])**

**Feature Importance Mapping for Stress Test C（来自 modify.md）**: 模型的 `feature_importances_` 对应的是预处理后的 feature matrix，而 Stress C 在 raw feature 层面操作。为避免类别编码后列数或列名变化带来的映射复杂性，主实验只对 numeric raw features 做 feature dropout。

按**数值特征**重要性排序后丢弃:

```python
# 只获取数值特征的重要性（排除类别特征避免 encoded feature mapping 问题）
importances = model.feature_importances_  # 需映射回 numeric raw features
ranked_numeric_features = np.argsort(numeric_importances)

for k in FEATURE_DROPOUT_COUNTS:  # [2, 4, 6]
    # Round A: 丢弃最重要的 k 个 numeric raw features
    drop_topk_cols = [NUMERIC_FEATURES[i] for i in ranked_numeric_features[-k:]]
    X_dropped_raw = X_test_raw.copy()
    for col in drop_topk_cols:
        X_dropped_raw[col] = 0
    X_dropped = preprocessor.transform(X_dropped_raw)
    f1_top = evaluate(model, X_dropped, y_test)

    # Round B: 丢弃最不重要的 k 个 numeric raw features（验证冗余度）
    drop_bottomk_cols = [
        NUMERIC_FEATURES[i]
        for i in ranked_numeric_features[:k]
    ]
    X_dropped_raw2 = X_test_raw.copy()
    for col in drop_bottomk_cols:
        X_dropped_raw2[col] = 0
    X_dropped2 = preprocessor.transform(X_dropped_raw2)
    f1_bottom = evaluate(model, X_dropped2, y_test)

# 这直接回答:
# - "哪个特征对性能影响最大？" (丢弃后 F1 降最多)
# - "哪些特征是冗余的？" (丢弃后 F1 基本不变)
```

**辅助函数**:

```python
def apply_feature_dropout_raw(X_raw, feature_names_to_drop):
    """在 raw DataFrame 层面将指定特征列置零"""
    X_corrupted = X_raw.copy()
    for col in feature_names_to_drop:
        X_corrupted[col] = 0
    return X_corrupted
```

### Phase 4b 产出检查清单

- [ ] Stress B 前置: 特征兼容性检查报告 (common_features 列表)
- [ ] Stress B: 二值分类指标表 + ΔF1
- [ ] Stress B: TOP-5 漂移最大特征 + KS 统计量
- [ ] Stress B: 特征分布对比图 (>=5 个关键特征的源域 vs 目标域)
- [ ] Stress C: 退化曲线图 (3条线: 噪声/掩码/丢弃)
- [ ] Stress C: 按重要性丢弃的 F1 影响排序表 (含 top-k 和 bottom-k)
- [ ] Stress C: 扰动均在 raw level 进行，确认无数据泄露
- [ ] 全部写入 `run_stress.py`

---

## Phase 5a: 改进策略 1 — 置信度阈值拒绝

### 5a.1 机制

```python
def predict_with_rejection(model, X, tau):
    """
    输入: 模型, 特征矩阵 X, 阈值 τ ∈ [0.5, 0.99]
    输出: (预测类数组, 是否拒绝数组)

    Rule:
      if max(p) ≥ τ → ŷ = argmax(p)
      else           → ŷ = REJECT (−1)
    """
    y_prob = model.predict_proba(X)
    max_probs = np.max(y_prob, axis=1)
    y_pred = np.argmax(y_prob, axis=1)

    rejected = max_probs < tau
    y_pred[rejected] = -1  # REJECT class
    return y_pred, rejected, max_probs
```

### 5a.2 实验

**Threshold Selection Rule（来自 modify.md）**: 置信度阈值 `tau` 必须在 validation set 上选择，不可在 test set 上调优。

Validation procedure:

1. Run prediction on the validation set.
2. Sweep `tau` from 0.50 to 0.99.
3. For each `tau`, compute: coverage, accepted accuracy, macro-F1 on accepted samples, rejection rate.
4. Select the best `tau` under a minimum coverage constraint (e.g., coverage ≥ 85%).
5. Save the selected `tau` to `artifacts/strategy_config.json`.
6. Evaluate the selected `tau` once on the test set.

```python
best_tau = select_tau_on_validation(
    y_val, y_val_prob,
    min_coverage=0.85
)

test_results = evaluate_threshold_on_test(
    y_test, y_test_prob,
    tau=best_tau
)
```

The test set is used only for final evaluation, not for threshold tuning.

**Sweep τ (on validation)**:

```python
results = []
for tau in np.arange(0.5, 0.99, 0.01):
    y_pred, rejected, _ = predict_with_rejection(model, X_val, tau)
    coverage = 1 - rejected.mean()
    acc = accuracy_score(y_val[~rejected], y_pred[~rejected])
    results.append({"tau": tau, "coverage": coverage, "accuracy": acc})

# 生成: coverage-accuracy 曲线图
```

**在 Stress A 条件下评估**:

```python
# unknown 类: 正确拒绝率应该高
is_unknown = y_test.isin(held_out_classes)
unknown_rejection_rate = rejected[is_unknown].mean()

# known 类: 错误拒绝率应该低
known_false_rej = rejected[known_mask & (y_pred[~rejected] == y_test[~rejected])].mean()

# 推荐 τ: 在 coverage ≥ 85% 的前提下最大化 accuracy
```

**Per-class 阈值（消融素材）**:

```python
# 不为所有类设同一个 τ，而是为每个 known 类分别设 τ_k
# 基于 validation 上的 per-class 置信度分布确定
# 对比: 全局 τ vs per-class τ → 哪个在 Stress A 下更好?
```

### Phase 5a 产出检查清单

- [ ] `predict_with_rejection()` 函数
- [ ] 覆盖率-准确率曲线图
- [ ] Stress A 下的 unknown 拒绝率 + known 误拒率
- [ ] 部署建议: 推荐 τ + 理由
- [ ] (消融素材) 全局 τ vs per-class τ 对比

---

## Phase 5b: 改进策略 2 — 集成学习不一致检测

### 5b.1 机制 — 异构集成

```python
def train_heterogeneous_ensemble(X_train, y_train):
    """
    训练 M=5 异构集成:
      - RF × 3 (不同 seed: 42, 123, 456)
      - XGBoost × 1
      - LogisticRegression × 1
    异构成员的不一致度比同构更可靠。
    """
    models = []

    # 3× Random Forest with different seeds
    for seed in [42, 123, 456]:
        rf = RandomForestClassifier(
            n_estimators=200, max_depth=20,
            random_state=seed, class_weight="balanced", n_jobs=-1,
        )
        rf.fit(X_train, y_train)
        models.append(("rf", rf))

    # 1× XGBoost
    xgb = XGBClassifier(
        n_estimators=200, max_depth=10, learning_rate=0.1,
        random_state=SEED, eval_metric="mlogloss",
    )
    xgb.fit(X_train, y_train)
    models.append(("xgb", xgb))

    # 1× LogisticRegression
    lr = LogisticRegression(max_iter=1000, class_weight="balanced")
    lr.fit(X_train, y_train)
    models.append(("lr", lr))

    return models

def ensemble_disagreement(models, X):
    """
    输入: 模型列表, 特征矩阵
    输出: (disagreement_scores, majority_vote_predictions)

    disagreement(x) = 1 − (1/M) * Σᵢ 𝟙[ŷᵢ(x) == ŷ_majority(x)]
    """
    all_preds = np.array([m.predict(X) for _, m in models])  # (M, N)
    from scipy.stats import mode
    majority, _ = mode(all_preds, axis=0, keepdims=False)
    majority = majority.flatten()
    agreement = (all_preds == majority).mean(axis=0)
    disagreement = 1 - agreement
    return disagreement, majority
```

### 5b.2 实验

**Disagreement Threshold Selection（来自 modify.md）**: 如果使用 disagreement threshold `delta`，必须也在 validation set 上选择，不可在 test set 上调优。

Validation procedure:

1. Train ensemble members on training data.
2. Compute disagreement scores on the validation set.
3. Sweep candidate `delta` values.
4. Select `delta` based on validation performance (e.g., maximizing wrong-prediction detection AUROC or achieving a desired uncertainty flag rate).
5. Save selected `delta` to `artifacts/strategy_config.json`.
6. Evaluate the selected `delta` on the test set.

```python
# 1. 全量测试集（使用 validation 上选定的 delta 评估）
disagreement, majority_vote = ensemble_disagreement(models, X_test)
is_wrong = majority_vote != y_test

# 2. Disagreement 分桶准确率
bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
for i in range(len(bins)-1):
    mask = (disagreement >= bins[i]) & (disagreement < bins[i+1])
    print(f"disagreement [{bins[i]}, {bins[i+1]}): "
          f"count={mask.sum()}, accuracy={accuracy_score(y_test[mask], majority_vote[mask]):.3f}")

# 预期:
# disagreement 0.0:     准确率 ~98% (全部同意 = 高度确定)
# disagreement 0.2-0.4: 准确率 ~85% (有分歧 = 不确定)
# disagreement 0.6+:    准确率 ~40% (严重分歧 = 几乎肯定错误)

# 3. AUROC of disagreement as wrong-prediction detector
auroc = roc_auc_score(is_wrong, disagreement)

# 4. Stress A 条件下
is_unknown = y_test.isin(held_out_classes)
print(f"Unknown mean disagreement: {disagreement[is_unknown].mean():.3f}")
print(f"Known   mean disagreement: {disagreement[~is_unknown].mean():.3f}")
# 预期: unknown 类的 disagreement 显著更高
```

### Phase 5b 产出检查清单

- [ ] `train_heterogeneous_ensemble()` 和 `ensemble_disagreement()` 函数
- [ ] Disagreement 分桶准确率表 + 柱状图
- [ ] AUROC of disagreement as wrong-prediction detector
- [ ] Stress A 下 unknown vs known 的 disagreement 分布对比图
- [ ] (消融素材) M=1,3,5,10 的 AUROC 变化

---

## Phase 5c: run_strategies.py + 统计显著性

### 实验脚本

```python
"""
python experiments/run_strategies.py

实验流程:
1. 加载 Phase 3 训练的最佳模型
2. 策略1: sweep tau → coverage-accuracy curve → 选最佳 tau
3. 策略2: 训练异构集成 → disagreement AUROC
4. 在 Clean / Stress A / Stress B / Stress C 条件下分别评估
5. 所有结果 vs 无改进基线对比
6. 5次随机种子重复 → mean +/- std
7. McNemar's test: 策略 vs 基线

输出:
  results/strategies_comparison.csv
  results/coverage_accuracy_curve.png
  results/disagreement_auroc.png
  results/statistical_significance.csv
"""
```

**策略1+2 组合**: 不做为默认实验内容。仅在时间充裕时作为 bonus 探索（将 rejection 和 ensemble disagreement 串联: ensemble 投票 + max_prob < tau 时拒绝）。不在最终对比表中列为独立方法。

### 最终对比表模板

| 方法 | Clean Macro-F1 | Stress A Macro-F1 | Stress B F1 | Stress C F1 (sigma=0.5) |
|------|---------------|-------------------|-------------|-------------------------|
| 无改进基线 | 0.85+/-0.01 | 0.42+/-0.03 | 0.68+/-0.02 | 0.72+/-0.02 |
| 策略1: tau=0.85 | 0.84+/-0.01 | 0.55+/-0.02 | 0.69+/-0.01 | 0.73+/-0.02 |
| 策略2: M=5 | 0.86+/-0.01 | 0.58+/-0.02 | 0.70+/-0.01 | 0.74+/-0.01 |

---

## Phase 6: 消融研究 + 失败分析

### 消融 A: 策略1 — 阈值灵敏度

```python
for tau in [0, 0.5, 0.7, 0.85, 0.9, 0.95]:
    # tau=0 → 等同无策略
    # 在 Stress A 条件下:
    # 测量: coverage, accepted accuracy, unknown rejection rate
```

### 消融 B: 策略2 — 集成大小

```python
for M in [1, 3, 5, 10]:
    # M=1 → 等同单模型, disagreement 始终 0
    # 测量: AUROC of disagreement, 训练时间, 推理时间
    # 预期: M≥5 后 AUROC 趋于饱和
```

### 消融 C: 类不平衡处理方法（新增）

```python
# 对比三种策略在少数类 recall 上的效果:
methods = {
    "none":           X_train_raw,                              # 原始不平衡数据
    "class_weight":   RandomForestClassifier(class_weight="balanced"),  # 内置权重
    "SMOTE":          apply_smote(X_train, y_train),            # SMOTE 过采样
}
# 特别关注: Worms, Analysis, Shellcode 三类的 recall
# 这直接回答: "SMOTE 是否真的有效？"
```

### 失败分析（≥3 个具体案例）

```markdown
### 失败案例 1: Worms 在所有条件下无法学习
- 条件: 任何训练配置 (SMOTE / class_weight 都无效)
- 表现: Worms recall = 0.00, 100% 被分为 Backdoor
- 原因: 158 样本 + 特征空间完全被 Backdoor 覆盖
- 策略效果: 策略1 (τ=0.9) 只拒绝了 12% 的 Worms
- 改进方向: 需要 few-shot 学习或一类分类器
- 实际意义: Worms 传播模式正在演化，传统特征无法捕捉

### 失败案例 2: 策略1 覆盖率在 τ>0.95 时崩溃
- 条件: τ=0.95, 全量测试集
- 表现: coverage=34%, accepted_accuracy=99.2%
- 问题: 66% 流量需要人工审查 → 不可部署
- 建议: 操作点 τ ≤ 0.85, 此时 coverage ≥ 85%

### 失败案例 3: Stress B 中特定攻击的召回率崩塌
- 条件: UNSW 训练 → CICIDS 测试
- 表现: 某类攻击 recall 从 0.91 → 0.23
- 原因: UNSW 和 CICIDS 虽协议相同，但流量采集环境不同
- 特征层面: FLOW_DURATION_MILLISECONDS 均值差异 > 5×
- 结论: 纯特征级分类器无法解决域偏移，需要域适应方法

### 失败案例 4: SMOTE 对极度稀有类的局限性
- 条件: Worms(158), k_neighbors=1
- 表现: SMOTE 后 Worms 合成样本十分相似(低方差)
- 原因: 基于极少数真实样本合成 → 多样性严重受限
- 报告讨论: SMOTE 不适用于样本数 < 200 的类
```

---

## Phase 7: predict.py + 报告 + README

### predict.py — CLI 原型

```python
"""
用法:
  python predict.py --input sample_flow.csv \
                    --strategy confidence_threshold \
                    --tau 0.8

策略选项:
  - none:                   直接输出预测
  - confidence_threshold:   置信度阈值拒绝 (需 --tau)
  - ensemble:               集成投票 + 不一致度检测
  - ensemble+threshold:     组合策略

输出格式:
  Flow ID: 42
  Predicted class: Reconnaissance
  Confidence: 0.91
  Decision: ALERT (above threshold)

  Flow ID: 77
  Predicted class: [UNKNOWN]
  Confidence: 0.43
  Decision: FLAG FOR REVIEW (below threshold)
"""
```

**predict.py 结构**:

```python
import argparse
import pandas as pd
import joblib
from preprocessing.preprocess import preprocess_pipeline_for_inference
from robustness.strategies import predict_with_rejection, ensemble_disagreement

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--strategy", default="none",
                        choices=["none", "confidence_threshold", "ensemble",
                                 "ensemble+threshold"])
    parser.add_argument("--tau", type=float, default=0.8)
    args = parser.parse_args()

    # 加载模型 + 预处理器
    model, preprocessors = load_model_and_preprocessors()

    # 读取 + 预处理输入
    df = pd.read_csv(args.input)
    X = preprocess_pipeline_for_inference(df, preprocessors)

    # 预测
    results = apply_strategy(model, X, args.strategy, args.tau)

    # 输出
    for _, row in results.iterrows():
        print(f"Flow ID: {row['flow_id']}")
        print(f"Predicted class: {row['prediction']}")
        print(f"Confidence: {row['confidence']:.2f}")
        print(f"Decision: {row['decision']}")
        print()
```

**Inference Rule（来自 modify.md）**: 推理阶段 `predict.py` 必须从 `artifacts/` 加载已拟合的 preprocessor，绝不能对推理数据调用 `fit()` 或 `fit_transform()`。

Correct inference process:

```python
preprocessor = joblib.load("artifacts/preprocessor.joblib")
model = joblib.load("artifacts/best_model.joblib")
label_encoder = joblib.load("artifacts/label_encoder.joblib")

X_raw = pd.read_csv(args.input)
X = preprocessor.transform(X_raw)          # transform only, NEVER fit
y_pred_encoded = model.predict(X)
y_pred_labels = label_encoder.inverse_transform(y_pred_encoded)
```

This ensures that inference uses the same preprocessing parameters learned from training data.

### 报告结构 (IEEE 格式, 8–12 页)

| 章节 | 内容 | 页数 |
|------|------|------|
| **Abstract** | 150–200字: 问题、方法、关键发现、贡献 | 1/3 |
| **1. Introduction** | 动机、问题陈述、贡献总结 | 1 |
| **2. Related Work** | >=8篇，分主题组织 (NIDS / Open-Set / Distribution Shift) | 1.5 |
| **3. Dataset & Preprocessing** | NF-UQ-NIDS-v3、预处理决策、类分布统计 | 1 |
| **4. Methodology** | Component 1/2/3 + 方程 | 2 |
| **5. Experiments** | 全部表格+图表 (Section 6 of omar.md) | 2.5 |
| **6. Ablation Study** | 消融 A/B/C | 1 |
| **7. Failure Analysis** | ≥3 个具体失败案例 | 1 |
| **8. Limitations & Future Work** | 诚实讨论限制 + 校准分析作为 future work | 0.5 |
| **9. Conclusion** | 总结，无新声明 | 0.5 |
| **References** | 格式规范，全部文中引用 | — |

### README.md

```markdown
# Robust Multi-Class Network Intrusion Detection

## 项目简介
NF-UQ-NIDS-v3 数据集上的多类入侵检测 + 鲁棒性系统评估。
训练集: NF-UNSW-NB15-v3 (2.37M flows, 10 classes)
目标域: NF-CSE-CIC-IDS2018-v3 (20.1M flows)

## 依赖安装
pip install -r requirements.txt

## 数据准备
将数据集 CSV 文件放入 data/ 目录:
- NF-UNSW-NB15-v3.csv
- NF-CSE-CIC-IDS2018-v3.csv
下载: https://staff.itee.uq.edu.au/marius/NIDS_datasets/

## 复现所有实验

# Phase 3: 基线分类器
python experiments/run_baseline.py

# Phase 4: 压力测试 (Stress A/B/C)
python experiments/run_stress.py

# Phase 5: 改进策略
python experiments/run_strategies.py

## CLI 原型
python predict.py --input sample.csv --strategy confidence_threshold --tau 0.8

## 项目结构
E:\AgentPV\
├── config.py              # 全局配置
├── predict.py             # CLI 原型
├── preprocessing/         # 预处理流水线
├── models/                # 分类器
├── robustness/            # 压力测试 + 改进策略
├── evaluation/            # 指标 + 可视化
├── experiments/           # 可复现实验脚本
└── results/               # 所有输出
```

### Phase 7 产出检查清单

- [ ] `predict.py` 四种策略均可运行
- [ ] 报告初稿 (含所有表格和图表)
- [ ] `README.md` 含完整的复现指令
- [ ] `requirements.txt` 测试通过
- [ ] 所有实验 `python experiments/*.py` 一键可复现
- [ ] 代码通过 review: 无 `print("TODO")`, 无 dead code

---

## 附录 A: 关键警告清单（来自项目文档）

| # | 警告 | 阶段 | 不遵守的后果 |
|---|------|------|------------|
| 1 | Scaler/Imputer/Encoder 只 fit 训练集 | Phase 2b | 数据泄露，结果无效 |
| 2 | 使用 Macro-F1，不用 Accuracy | Phase 3+ | 不平衡数据下结果误导 |
| 3 | Stress A 必须做 2 组保留类 | Phase 4a | 评审拒稿 |
| 4 | 各 Stress 条件独立运行 | Phase 4a/4b | 结果混淆，不可解释 |
| 5 | 改进策略必须 vs 基线对比 | Phase 5 | 无法证明改进 |
| 6 | 必须包含失败分析 (≥3 案例) | Phase 6 | 报告扣分 |
| 7 | 必须包含消融研究 | Phase 6 | 声明不可信 |
| 8 | 必须报告统计显著性 | Phase 3–5 | 无法区分随机波动 vs 真实改进 |
| 9 | 单命令可复现 | Phase 3–5 | 实验不可验证 |
| 10 | 不跳过 EDA | Phase 2a | 后期才发现数据问题 |

---

## 附录 B: 执行时间线

| 周次 | 里程碑 | 产出 |
|------|--------|------|
| **W1** | 项目骨架 + EDA | 目录结构、config.py、EDA 报告 (class dist + missing + correlation + L7_PROTO) |
| **W2** | 预处理 + 基线 | preprocess.py、balance.py、metrics.py、LR/RF/Majority 结果 |
| **W3** | 自选模型 + Stress A | XGBoost 结果、2组保留类 × 全部指标、置信度分布分析 |
| **W4** | Stress B + C | 分布偏移结果、退化曲线、特征丢弃影响排序 |
| **W5** | 改进策略 | 策略1+2 实现、全部对比表、统计显著性 |
| **W6** | 消融 + 失败分析 | 消融 A/B/C、≥3 失败案例、写入报告 |
| **W7** | 最终化 | predict.py、报告定稿、README、代码清理 |

---

## 附录 C: Stage Notes 模板（来自 final_advice.md §5–§8）

本附录提供 4 个必需的 stage-level notes 文件模板。这些文件不是正式报告，而是为最终报告整合提供结构化实验记录。

### C.1 data_and_eda_notes.md

文件位置: `reports/notes/data_and_eda_notes.md`

```markdown
# Data and EDA Notes

## Dataset Version

This project uses the NF-UQ-NIDS-v3 dataset collection.

Main datasets:
- NF-UNSW-NB15-v3
- NF-CSE-CIC-IDS2018-v3

## Label Columns

- `Attack`: multi-class target column, used for the main classification task.
- `Label`: binary label column, used only for binary attack / normal evaluation.

## Dataset Roles

- NF-UNSW-NB15-v3:
  - Used as the main training and evaluation dataset.
  - Used for baseline multi-class classification.
  - Used for Stress Test A.
  - Used for Stress Test C.
  - Used for training robustness strategies.

- NF-CSE-CIC-IDS2018-v3:
  - Used as the external testing dataset.
  - Used for Stress Test B.
  - Used to evaluate cross-dataset generalization under distribution shift.

## Feature Compatibility Check

Before Stress Test B, the feature columns of UNSW and CICIDS2018 must be compared.

Items to check:
- Number of feature columns in UNSW.
- Number of feature columns in CICIDS2018.
- Common feature columns.
- Columns only present in UNSW.
- Columns only present in CICIDS2018.
- Data type consistency.
- Categorical feature consistency, especially `PROTOCOL` and `L7_PROTO`.

If the two datasets do not have exactly the same feature columns, Stress Test B will use the common feature subset.

```python
common_features = sorted(
    set(unsw_feature_cols).intersection(set(cicids_feature_cols))
)
```

## EDA Findings

The EDA stage should record:
- Class distribution.
- Minority classes.
- Missing values.
- Feature skewness.
- Highly correlated features.
- Suspicious or low-quality features.
- Dataset imbalance level.

## Implications for Modeling

Important implications:
- Accuracy alone is not enough because the dataset is highly imbalanced.
- Macro-F1 and per-class recall should be reported.
- Minority classes such as Worms, Shellcode, Analysis, or Backdoor require special attention.
- Class imbalance should be handled using class_weight or sample_weight.
- SMOTE is not used as the default training strategy due to dataset scale.
```

### C.2 baseline_results.md

文件位置: `reports/notes/baseline_results.md`

```markdown
# Baseline Results Notes

## Models Evaluated

The following baseline models are evaluated:
1. Majority Classifier
2. Logistic Regression
3. Random Forest
4. XGBoost

## Target Column

All multi-class classification experiments use:
```python
y = df["Attack"]
```
The `Label` column is not used as the target for the main multi-class task.

## Evaluation Metrics

The following metrics are reported:
- Accuracy
- Macro-F1
- Weighted-F1
- Per-class precision
- Per-class recall
- Per-class F1
- Confusion matrix

**Macro-F1 is emphasized because the dataset is highly imbalanced.**

## Result Table

Baseline results are saved to: `results/baseline_results.csv`

| Model | Accuracy | Macro-F1 | Weighted-F1 | Minority Recall | Training Time |
|-------|----------|----------|-------------|-----------------|---------------|
| Majority Classifier | | | | | |
| Logistic Regression | | | | | |
| Random Forest | | | | | |
| XGBoost | | | | | |

## Best Model Selection

The best model is selected based mainly on:
- Macro-F1
- Minority-class recall
- Stability across classes
- Computational cost
- Suitability for stress testing

## Confusion Matrix

The confusion matrix of the best model should be saved to: `reports/figures/confusion_matrix.png`

The analysis should identify:
- Which classes are most frequently confused.
- Whether minority attack classes are misclassified as Benign.
- Whether similar attack types are confused with each other.
```

### C.3 stress_test_results.md

文件位置: `reports/notes/stress_test_results.md`

```markdown
# Stress Test Results Notes

## Stress Test A: Unknown Attack Classes

Stress Test A evaluates how the model behaves when it encounters attack classes that were not seen during training.

### Setup

Two held-out class groups are used.

Example:
- Held-out Set 1: [Worms, Shellcode, Analysis]
- Held-out Set 2: [Backdoor, DoS, Fuzzers]

The exact held-out groups should be selected based on class distribution and project requirements.

### Important Rule

Held-out classes must be removed from training.
The model is trained only on known classes and evaluated on a test set that includes both known and unknown classes.

### Recommended Strict Version

If time allows, preprocessing should also be fitted only on known-class training data:
1. Split train / validation / test.
2. Remove held-out classes from train and validation.
3. Fit imputer, encoder, and scaler only on known-class train.
4. Transform known train, known validation, and full test.
5. Train the model on known-class train.
6. Evaluate on full test.

### Outputs

Save results to: `results/stress_a_results.csv`

## Stress Test B: Cross-Dataset Generalization

Stress Test B evaluates whether a model trained on UNSW can generalize to CICIDS2018.

### Setup

- Train: NF-UNSW-NB15-v3
- Test: NF-CSE-CIC-IDS2018-v3

### Feature Compatibility

Before running Stress Test B, UNSW and CICIDS2018 feature columns must be compared.

If they do not match exactly, use the common feature subset:
```python
common_features = sorted(
    set(unsw_feature_cols).intersection(set(cicids_feature_cols))
)
```

### Binary Mapping

Because UNSW and CICIDS2018 have different attack category systems, Stress Test B is evaluated as a binary attack / normal task.

```python
y_true_binary = (df_cicids["Attack"] != "Benign").astype(int)
y_pred_binary = (y_pred_multiclass != "Benign").astype(int)
```

### Outputs

Save results to: `results/stress_b_results.csv`

## Stress Test C: Feature Degradation

Stress Test C evaluates model robustness under corrupted or missing features.

### Corruption Types

- Gaussian noise
- Random masking
- Feature dropout

### Feature Dropout Levels

```python
FEATURE_DROPOUT_COUNTS = [2, 4, 6]
```

### Pipeline Handling

Corruption is applied to raw test data before calling the fitted preprocessor.

```python
X_test_corrupted_raw = X_test_raw.copy()
for col in drop_feature_names:
    X_test_corrupted_raw[col] = 0

X_test_corrupted = preprocessor.transform(X_test_corrupted_raw)
y_pred = model.predict(X_test_corrupted)
```

### Outputs

Save results to: `results/stress_c_results.csv`
Save figure to: `reports/figures/stress_c_degradation_curve.png`
```

### C.4 strategy_failure_analysis.md

文件位置: `reports/notes/strategy_failure_analysis.md`

```markdown
# Strategy, Ablation, and Failure Analysis Notes

## Strategy 1: Confidence Thresholding

```python
if max_confidence < tau:
    decision = "UNKNOWN"
else:
    decision = predicted_class
```

Save selected threshold to: `artifacts/strategy_config.json`

## Strategy 2: Ensemble Disagreement

Disagreement can be measured by:
- Vote entropy
- Number of unique predicted classes
- Difference between top predicted probabilities
- Variance of predicted probabilities

```python
if disagreement > delta:
    decision = "UNCERTAIN"
else:
    decision = predicted_class
```

## Optional Combined Strategy

```python
if max_confidence < tau:
    decision = "UNKNOWN"
elif disagreement > delta:
    decision = "UNCERTAIN"
else:
    decision = predicted_class
```

## Ablation Study

Recommended: Threshold sensitivity analysis

```python
tau ∈ {0.50, 0.60, 0.70, 0.80, 0.90}
```

## Failure Analysis

Analyze at least three failure cases.

### Failure Case 1
- True label:
- Predicted label:
- Confidence:
- Decision:
- Important features:
- Possible reason:

### Failure Case 2
- ...

### Failure Case 3
- ...
```

---

---

## 附录 D: Manual Execution Checklist（来自 modify.md）

After the implementation is completed, the following scripts must be manually executed to generate result tables, figures, notes, and artifacts for the final report.

ChatGPT can help write code and interpret results, but the actual training, evaluation, figure generation, and final report material collection must be executed manually in the local or server environment.

### Execution Table

| Stage | Command | Expected Outputs |
|---|---|---|
| Data validation | `python experiments/validate_data.py` | feature lists, compatibility report, metadata JSON files |
| EDA | `python experiments/run_eda.py` | class distribution, missing value plots, correlation plots |
| Preprocessing check | `python experiments/prepare_data.py` | train/val/test split files, fitted preprocessor |
| Baseline training | `python experiments/run_baseline.py` | `results/baseline_results.csv`, confusion matrices, best model |
| Baseline with GPU | `python experiments/run_baseline.py --use-gpu` | GPU-accelerated XGBoost results |
| Stress tests | `python experiments/run_stress.py` | Stress A/B/C result tables and figures |
| Strategies | `python experiments/run_strategies.py` | threshold results, ensemble disagreement results |
| Ablation | `python experiments/run_ablation.py` | ablation tables and plots |
| Failure analysis | `python experiments/run_failure_analysis.py` | representative failure cases |
| CLI test | `python predict.py --input sample.csv --strategy confidence_threshold --tau 0.8` | sample predictions in terminal or output CSV |

### Recommended Manual Running Order

```bash
python experiments/validate_data.py
python experiments/run_eda.py
python experiments/prepare_data.py
python experiments/run_baseline.py --use-gpu
python experiments/run_stress.py
python experiments/run_strategies.py --use-gpu
python experiments/run_ablation.py
python experiments/run_failure_analysis.py
python predict.py --input sample.csv --strategy confidence_threshold --tau 0.8
```

If GPU is not available, remove the `--use-gpu` flag:

```bash
python experiments/run_baseline.py
python experiments/run_strategies.py
```

### Manual Checks After Running

After each script is executed, the project member should manually check:

- whether the expected `.csv` result files are generated;
- whether figures are saved under `results/` or `reports/figures/`;
- whether `artifacts/` contains the fitted model, preprocessor, label encoder, and strategy config;
- whether the result values are reasonable;
- whether there are obvious signs of data leakage;
- whether the generated results can support the final report claims.

---

## 最终修改检查清单（来自 modify.md §24）

在提交最终 plan 前，确认以下所有修改已完成：

- [x] 全文路径统一为 `data/`，不使用 `data/raw/`
- [x] CICIDS 文件名统一为 `NF-CSE-CIC-IDS2018-v3.csv`
- [x] 修正 v3 特征数量描述，不再混用 "43 features" 和 "55 columns"
- [x] `config.py` 中路径为 `DATA_DIR = "data/"`
- [x] 补充 XGBoost 的 `Attack` 标签编码流程 (LabelEncoder)
- [x] 将 `PROTOCOL_FEATURES` 从普通 numeric pipeline 中分离出来，缺失值填 0
- [x] Stress A 中 validation set 也要移除 held-out classes
- [x] Stress B 使用按 `Attack` 分层采样
- [x] Stress B 使用 common_features 时必须重新训练 common-feature model
- [x] `tau` 和 `delta` 必须在 validation set 上选择
- [x] Stress C feature dropout 说明只针对 numeric raw features
- [x] SMOTE 只作为可选消融实验，不作为默认训练流程
- [x] README 数据准备路径改为 `data/`
- [x] 新增 Manual Execution Checklist (附录 D)
- [x] 明确 `predict.py` 推理阶段不能重新 fit preprocessor
- [x] 补充 GPU 自动降级逻辑
- [x] 补充 OrdinalEncoder 对 Logistic Regression 影响的说明
- [x] 统一 results/、reports/figures/、reports/notes/、artifacts/ 的输出约定

完成以上修改后，本 plan 覆盖：
- NF-UQ-NIDS-v3 数据版本说明
- `Attack` / `Label` 的正确任务定义
- Baseline 多类分类
- Stress Test A/B/C
- 置信度阈值拒绝 + 集成学习不一致检测策略
- 消融研究 + 失败分析
- GPU 加速与 CPU fallback
- 手动运行流程
- final report 所需的结果表、图表和 notes 管理

---

*文档版本: 5.1 | 最后更新: 2026-05-07 | 整合 final_advice.md + modify.md 全部修改（含 5 个小修正） | 基于实际数据验证*
