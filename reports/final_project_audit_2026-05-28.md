# Final Project Audit

Audit date: 2026-05-28

## Scope

This audit covers the project proposal alignment, V3 dataset consistency,
active results, final figures, reports, notes, CLI behavior, and legacy-output
cleanup.

## Findings Fixed In This Pass

1. `results/strategy2_stress_a_lightweight_*.csv` files were still present in
   the active `results/` directory even though current scripts do not generate
   those names. They were moved to `reports/archive/legacy_outputs/`.
2. Strategy 2 documentation was updated to include the newly saved
   `unknown_detection_auroc` field:
   - Set 1: 0.8329
   - Set 2: 0.8562
   - Mean: 0.8446
3. `reports/notes/strategy_failure_analysis.md`,
   `reports/detailed_project_report.md`, and `README.md` now describe
   Strategy 2 unknown-class detection consistently.
4. `reports/notes/stress_test_results.md` no longer uses the obsolete sampled
   / KS-style Stress B feature-shift explanation. It now uses the reproducible
   `results/stress_b_feature_shift.csv` standardized-mean-difference results.
5. `reports/project_audit_report.md` and `reports/file_inventory.md` were
   updated so they no longer describe the old lightweight Strategy 2 files as
   active results.

## Current Status

- Dataset version: NF-UQ-NIDS-v3.
- Active source dataset: `data/NF-UNSW-NB15-v3.csv`.
- Active Stress B target dataset: `data/NF-CSE-CIC-IDS2018-v3.csv`.
- Final figure directory: `reports/figures_final/`.
- Final figure manifest: `reports/figures_final/figure_manifest.csv`.
- Formal final paper is still a writing task; the repository contains the
  technical base and final figure set.

## Remaining Non-Issues

- `Projectproposal.md` refers to NF-UQ-NIDS-v2 because it is the original
  assignment proposal. The project implementation and documentation explicitly
  state that this repository uses V3.
- `reports/archive/legacy_outputs/` is retained for traceability and ignored by
  `.gitignore`.
- `__pycache__/` files are local generated Python caches and ignored by
  `.gitignore`.

## Validation Note

Before this final documentation cleanup, the following checks passed:

```bash
python experiments/verify_8items.py
python experiments/verify_items.py
python experiments/check_consistency.py
python -m compileall experiments/run_strategies.py experiments/verify_8items.py
```

After the final documentation cleanup, command execution was blocked by the
local tool usage limit. The remaining changes after that point were limited to
documentation, archival movement of obsolete CSVs, and a small update to
`experiments/run_failure_analysis.py` so it reproduces the already-updated
Strategy 2 note text.
