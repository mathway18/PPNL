# PPNL – Part 1: Single-Goal Grid Navigation Pipeline

This repository contains the **data generation, preprocessing, evaluation and sanity-check pipeline** for single-goal grid path-planning experiments (Part 1 of the PPNL project).

---

## Directory Structure

```text
PPNL/
├── README.md
├── requirements.txt
├── run_all_baselines.sh          # Batch execution script 
├── scripts/
│   ├── generate_single_goal_data.py # Generate IID / OOD JSONL datasets
│   ├── data_preprocess.py           # Validate & normalise to standard schema
│   ├── sanity_check.py              # Gold-path / bad-action self-tests
│   ├── run_baseline.py              # HF Transformers inference script for LLMs
│   ├── evaluate_executor.py         # Parse predictions + compute metrics
│   ├── summarize_results.py         # Aggregate JSON metrics into a Markdown table
│   └── utils/
│       ├── actions.py               # Action parsing & normalisation
│       ├── grid.py                  # BFS shortest path, grid rendering
│       └── io.py                    # JSONL I/O, seed utilities
├── data/
│   └── single_goal/
│       ├── 5x5/                     # OOD (Smaller size)
│       ├── 6x6/                     # IID (Training/Validation/Test)
│       ├── 6x6_dense/               # OOD (Higher obstacle density)
│       └── 7x7/                     # OOD (Larger size)
└── outputs/                         # Stores .jsonl predictions & .json metrics
```

---

## Conventions

| Concept | Value |
|---|---|
| Grid size | 6 × 6 |
| World encoding | `0` empty · `1` obstacle · `2` start · `3` goal |
| Valid actions | `up` `down` `left` `right` (lower-case) |
| Action separator | space |
| IID obstacle density | 10 – 25 % of all cells |
| OOD obstacle density | 35 – 50 % of all cells |
| Coordinate system | `(row, col)`, 0-indexed, origin top-left |
| Movement | `up` → row−1 · `down` → row+1 · `left` → col−1 · `right` → col+1 |

---

## JSONL Schema

Each line in every data file is a JSON object with the following fields:

```json
{
  "id":          "train_000001",
  "grid_size":   [6, 6],
  "world":       [[0,0,0,0,1,2], "..."],
  "start":       [0, 5],
  "goal":        [3, 2],
  "input_coord": "Grid 6x6. Start: (row=0, col=5). Goal: (row=3, col=2). Obstacles: [(0,4), ...].",
  "input_grid":  ". . . . # S\n. . . # . .\n...",
  "target":      "down down left left down left",
  "meta": {
    "obstacle_count":   7,
    "obstacle_density": 0.1944,
    "path_length":      6,
    "split":            "train"
  }
}
```

---

## Quick Start

```bash
# Install dependencies (Python >= 3.8, no mandatory third-party packages)
pip install -r requirements.txt
```

### 1 · Generate data

```bash
# IID splits
python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split train    --n_samples 1000 --seed 42

python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split valid    --n_samples 200  --seed 43

python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split test_iid --n_samples 200  --seed 44

# OOD split (dense obstacles)
python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6_dense --split test_ood --n_samples 200 \
    --dense --seed 45

python scripts/generate_single_goal_data.py --out_dir data/single_goal/5x5 --split test_ood --rows 5 --cols 5 --n_samples 200 --seed 55

python scripts/generate_single_goal_data.py --out_dir data/single_goal/7x7 --split test_ood --rows 7 --cols 7 --n_samples 200 --seed 77
```

All data files are already committed to this repository and do **not** need to be regenerated unless you wish to change the parameters.

### 2 · Preprocess / validate

```bash
python scripts/data_preprocess.py \
    --input  data/single_goal/6x6/train.jsonl \
    --output data/single_goal/6x6/train.jsonl

python scripts/data_preprocess.py --input data/single_goal/6x6/valid.jsonl --output data/single_goal/6x6/valid.jsonl
python scripts/data_preprocess.py --input data/single_goal/6x6/test_iid.jsonl --output data/single_goal/6x6/test_iid.jsonl

#preprocess OOD
python scripts/data_preprocess.py --input data/single_goal/5x5/test_ood.jsonl --output data/single_goal/5x5/test_ood.jsonl
python scripts/data_preprocess.py --input data/single_goal/7x7/test_ood.jsonl --output data/single_goal/7x7/test_ood.jsonl
python scripts/data_preprocess.py --input data/single_goal/6x6_dense/test_ood.jsonl --output data/single_goal/6x6_dense/test_ood.jsonl
```

This validates required fields and normalises the `target` action string in-place.

### 3 · Sanity Check

Before proceeding to baseline evaluation or model training, it is crucial to verify that the generated datasets are logically consistent. The `sanity_check.py` script simulates the environment executor to validate the physical consistency of the data.

### Batch Check All Datasets
You can scan the entire `data/single_goal` directory to verify all grid sizes (5x5, 6x6, 7x7) and obstacle densities (6x6_dense) simultaneously:
```bash
# Check all generated .jsonl files (including IID and OOD splits)
python scripts/sanity_check.py --data_dir data/single_goal

# Check the 7x7 OOD test set specifically
python scripts/sanity_check.py --data_file data/single_goal/7x7/test_ood.jsonl
```

### 4 · Evaluate model predictions

Create a predictions JSONL file where each line has:
```json
{"id": "test_iid_000001", "prediction": "right down right down left"}
```

Then run:

```bash
python scripts/evaluate_executor.py \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --pred_file outputs/predictions.jsonl \
    --out_file  outputs/metrics.json
```

Example output:

```
=== Evaluation Results ===
  Samples evaluated : 200
  ParseRate         : 0.9850
  Feasibility       : 0.9200
  Success Rate      : 0.8750
  Optimality        : 0.8300
```

---

## Metrics

| Metric | Definition |
|---|---|
| **ParseRate** | Fraction of predictions that can be parsed into a valid action sequence |
| **Feasibility** | Fraction of predictions that make no out-of-bounds or obstacle-collision moves |
| **Success Rate** | Fraction of predictions where the agent reaches the goal |
| **Optimality** | Fraction of successful predictions whose length <= gold (shortest) path length |

---

## Reproducibility

All data files included in this repository were generated with fixed seeds:

| Split | Seed | Samples |
|---|---|---|
| train | 42 | 1 000 |
| valid | 43 | 200 |
| test_iid | 44 | 200 |
| test_ood (dense) | 45 | 200 |
| test 5×5 | 55 | 200 |
| test 7×7 | 77 | 200 |


baseline result:
| Model | Parse Rate | Feasibility | Success Rate | Optimality |
|---|---|---|---|---|
| bart-base | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-base | 0.0150 | 0.0100 | 0.0000 | 0.0000 |
| flan-t5-small | 0.1500 | 0.0300 | 0.0000 | 0.0000 |

---

## Part 2 · Prompting, Failure Analysis, and Fine-tuning

Part 2 adds a reproducible reasoning/fine-tuning layer on top of the Part 1
single-goal executor. The recommended comparison is:

1. **Prompting**: zero-shot structured prompt, CoT prompt, few-shot prompt, and
   CoT few-shot prompt.
2. **Fine-tuning**: supervised seq2seq training with a compact grid schema and
   action-only targets.
3. **Failure analysis**: step-by-step executor traces for parse failures,
   out-of-bounds moves, obstacle collisions, wrong final cells, and
   non-optimal successes.

### Prompting Experiments

`run_baseline.py` now supports Part 2 prompt styles:

```bash
python scripts/run_baseline.py \
    --model google/flan-t5-small \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --out_file outputs/task2/flan-t5-small_cot_iid_preds.jsonl \
    --prompt_style cot \
    --batch_size 4 \
    --max_new_tokens 96 \
    --num_beams 4

python scripts/evaluate_executor.py \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --pred_file outputs/task2/flan-t5-small_cot_iid_preds.jsonl \
    --out_file outputs/task2/flan-t5-small_cot_iid_metrics.json
```

Available prompt styles:

| Style | Purpose |
|---|---|
| `structured_zero` | Explicit grid rules, indexed grid map, action-only answer |
| `cot` | Same schema plus reasoning and a final answer line |
| `few_shot` | Demonstrations from the train set with action-only answers |
| `cot_few_shot` | Demonstrations with compact step traces |
| `finetune` | Compact supervised schema used for seq2seq fine-tuning |
| `baseline` | Original Part 1 prompt for comparison |

Batch run for IID plus one OOD split:

```bash
python scripts/run_task2_experiments.py \
    --model google/flan-t5-small \
    --prompt_styles structured_zero cot few_shot cot_few_shot \
    --eval_files iid=data/single_goal/6x6/test_iid.jsonl ood_dense=data/single_goal/6x6_dense/test_ood.jsonl \
    --few_shot_file data/single_goal/6x6/train.jsonl \
    --n_shots 3 \
    --output_dir outputs/task2 \
    --analyze_failures
```

### Fine-tuning

Recommended full run on a GPU:

```bash
python scripts/finetune_seq2seq.py \
    --model_name google/flan-t5-small \
    --train_file data/single_goal/6x6/train.jsonl \
    --valid_file data/single_goal/6x6/valid.jsonl \
    --output_dir outputs/finetuned/flan-t5-small-grid \
    --prompt_style finetune \
    --num_train_epochs 20 \
    --learning_rate 3e-4 \
    --per_device_train_batch_size 8 \
    --gradient_accumulation_steps 2 \
    --eval_steps 50 \
    --save_steps 100 \
    --num_beams 4
```

Quick CPU smoke test:

```bash
python scripts/finetune_seq2seq.py \
    --model_name google/flan-t5-small \
    --output_dir outputs/finetuned/debug-smoke \
    --prompt_style finetune \
    --max_train_samples 16 \
    --max_valid_samples 8 \
    --num_train_epochs 1 \
    --per_device_train_batch_size 2 \
    --per_device_eval_batch_size 2
```

Evaluate a fine-tuned checkpoint on IID and OOD:

```bash
python scripts/run_baseline.py \
    --model outputs/finetuned/flan-t5-small-grid \
    --prompt_style finetune \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --out_file outputs/task2/ft_flan-t5-small_iid_preds.jsonl

python scripts/evaluate_executor.py \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --pred_file outputs/task2/ft_flan-t5-small_iid_preds.jsonl \
    --out_file outputs/task2/ft_flan-t5-small_iid_metrics.json

python scripts/run_baseline.py \
    --model outputs/finetuned/flan-t5-small-grid \
    --prompt_style finetune \
    --data_file data/single_goal/6x6_dense/test_ood.jsonl \
    --out_file outputs/task2/ft_flan-t5-small_ood_dense_preds.jsonl

python scripts/evaluate_executor.py \
    --data_file data/single_goal/6x6_dense/test_ood.jsonl \
    --pred_file outputs/task2/ft_flan-t5-small_ood_dense_preds.jsonl \
    --out_file outputs/task2/ft_flan-t5-small_ood_dense_metrics.json
```

### Failure Case Analysis

Generate detailed failure traces for any prediction file:

```bash
python scripts/analyze_failures.py \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --pred_file outputs/flan-t5-small_preds.jsonl \
    --out_jsonl outputs/task2/flan-t5-small_iid_failures.jsonl \
    --out_md outputs/task2/flan-t5-small_iid_failures.md \
    --max_cases 12
```

The Markdown report contains representative inference/executor steps, including
the attempted coordinate at each action and whether the model went out of
bounds, hit an obstacle, stopped in the wrong cell, or reached the goal with a
non-optimal path.
