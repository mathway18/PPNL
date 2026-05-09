#!/usr/bin/env python3
"""Batch runner for Part 2 prompting/fine-tuned checkpoint experiments."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analyze_failures import analyze, write_markdown
from scripts.evaluate_executor import evaluate
from scripts.run_baseline import run_inference
from scripts.task2_prompts import list_prompt_styles
from scripts.utils.io import write_jsonl


def _parse_eval_files(items) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Expected split_name=path, got {item!r}")
        name, path = item.split("=", 1)
        result[name.strip()] = path.strip()
    return result


def _safe_name(text: str) -> str:
    name = Path(text).name if Path(text).exists() else text
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Part 2 prompt/checkpoint inference, executor metrics, and optional failure traces."
    )
    parser.add_argument("--model", default="google/flan-t5-small")
    parser.add_argument(
        "--prompt_styles",
        nargs="+",
        default=["structured_zero", "cot"],
        choices=list_prompt_styles(),
    )
    parser.add_argument(
        "--eval_files",
        nargs="+",
        default=[
            "iid=data/single_goal/6x6/test_iid.jsonl",
            "ood_dense=data/single_goal/6x6_dense/test_ood.jsonl",
        ],
        help="One or more split_name=path entries.",
    )
    parser.add_argument("--output_dir", default="outputs/task2")
    parser.add_argument("--few_shot_file", default="data/single_goal/6x6/train.jsonl")
    parser.add_argument("--n_shots", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--max_source_length", type=int, default=768)
    parser.add_argument("--max_new_tokens", type=int, default=96)
    parser.add_argument("--num_beams", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--analyze_failures", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_files = _parse_eval_files(args.eval_files)
    model_tag = _safe_name(args.model)

    for style in args.prompt_styles:
        for split_name, data_file in eval_files.items():
            run_tag = f"{model_tag}_{style}_{split_name}"
            pred_file = output_dir / f"{run_tag}_preds.jsonl"
            metric_file = output_dir / f"{run_tag}_metrics.json"

            n_shots = args.n_shots if style in {"few_shot", "cot_few_shot"} else 0
            few_shot_file = args.few_shot_file if n_shots > 0 else None

            run_inference(
                model_name=args.model,
                data_path=data_file,
                out_path=str(pred_file),
                prompt_style=style,
                few_shot_file=few_shot_file,
                n_shots=n_shots,
                batch_size=args.batch_size,
                max_source_length=args.max_source_length,
                max_new_tokens=args.max_new_tokens,
                num_beams=args.num_beams,
                prediction_mode="actions",
                include_prompt=False,
                limit=args.limit,
                seed=args.seed,
            )
            evaluate(data_file=data_file, pred_file=str(pred_file), out_file=str(metric_file))

            if args.analyze_failures:
                failure_jsonl = output_dir / f"{run_tag}_failures.jsonl"
                failure_md = output_dir / f"{run_tag}_failures.md"
                cases = analyze(data_file, str(pred_file))
                write_jsonl(cases, str(failure_jsonl))
                write_markdown(cases, str(failure_md), max_cases=12, include_success=False)


if __name__ == "__main__":
    main()
