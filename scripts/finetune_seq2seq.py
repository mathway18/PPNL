#!/usr/bin/env python3
"""Fine-tune a small seq2seq model for single-goal grid path planning."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    set_seed,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.task2_prompts import build_prompt, list_prompt_styles, load_few_shot_records
from scripts.utils.actions import actions_to_str, extract_actions
from scripts.utils.io import read_jsonl


class GridPlanningDataset(Dataset):
    """Tokenized JSONL dataset for action-sequence supervision."""

    def __init__(
        self,
        records: Iterable[dict],
        tokenizer,
        prompt_style: str,
        few_shot_records: Optional[List[dict]],
        max_source_length: int,
        max_target_length: int,
    ) -> None:
        self.records = list(records)
        sources = [
            build_prompt(record, style=prompt_style, few_shot_records=few_shot_records)
            for record in self.records
        ]
        targets = [record["target"] for record in self.records]

        model_inputs = tokenizer(
            sources,
            max_length=max_source_length,
            truncation=True,
            padding=False,
        )
        labels = tokenizer(
            text_target=targets,
            max_length=max_target_length,
            truncation=True,
            padding=False,
        )
        model_inputs["labels"] = labels["input_ids"]
        self.features = [
            {key: values[idx] for key, values in model_inputs.items()}
            for idx in range(len(self.records))
        ]

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> Dict[str, List[int]]:
        return self.features[idx]


def _clean_action_string(text: str) -> str:
    actions = extract_actions(text)
    if actions is None:
        return ""
    return actions_to_str(actions)


def build_compute_metrics(tokenizer):
    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]

        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        pred_actions = [_clean_action_string(text) for text in decoded_preds]
        gold_actions = [_clean_action_string(text) for text in decoded_labels]
        n = max(len(pred_actions), 1)

        parse_rate = sum(1 for text in pred_actions if text) / n
        exact_match = sum(
            1 for pred, gold in zip(pred_actions, gold_actions) if pred == gold
        ) / n
        avg_pred_len = (
            sum(len(text.split()) for text in pred_actions if text) / max(sum(1 for t in pred_actions if t), 1)
        )
        avg_gold_len = sum(len(text.split()) for text in gold_actions) / n

        return {
            "parse_rate": round(parse_rate, 4),
            "action_exact_match": round(exact_match, 4),
            "avg_pred_len": round(avg_pred_len, 4),
            "avg_gold_len": round(avg_gold_len, 4),
        }

    return compute_metrics


def _training_args(output_dir: str, args: argparse.Namespace) -> Seq2SeqTrainingArguments:
    kwargs = {
        "output_dir": output_dir,
        "learning_rate": args.learning_rate,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "per_device_eval_batch_size": args.per_device_eval_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "num_train_epochs": args.num_train_epochs,
        "weight_decay": args.weight_decay,
        "warmup_ratio": args.warmup_ratio,
        "logging_steps": args.logging_steps,
        "save_steps": args.save_steps,
        "eval_steps": args.eval_steps,
        "save_total_limit": args.save_total_limit,
        "predict_with_generate": True,
        "generation_max_length": args.max_target_length,
        "generation_num_beams": args.num_beams,
        "fp16": args.fp16,
        "bf16": args.bf16,
        "report_to": [],
        "load_best_model_at_end": False,
        "seed": args.seed,
        "save_only_model": args.save_only_model,
    }

    params = inspect.signature(Seq2SeqTrainingArguments.__init__).parameters
    if "eval_strategy" in params:
        kwargs["eval_strategy"] = "steps"
    else:
        kwargs["evaluation_strategy"] = "steps"
    kwargs["save_strategy"] = args.save_strategy

    return Seq2SeqTrainingArguments(**kwargs)


def _maybe_limit(records: List[dict], max_samples: int) -> List[dict]:
    if max_samples and max_samples > 0:
        return records[:max_samples]
    return records


def finetune(args: argparse.Namespace) -> None:
    set_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Fine-tuning {args.model_name} on {device}")

    train_records = _maybe_limit(list(read_jsonl(args.train_file)), args.max_train_samples)
    valid_records = _maybe_limit(list(read_jsonl(args.valid_file)), args.max_valid_samples)
    few_shot_records = load_few_shot_records(
        args.few_shot_file,
        n_shots=args.n_shots,
        seed=args.seed,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    train_dataset = GridPlanningDataset(
        records=train_records,
        tokenizer=tokenizer,
        prompt_style=args.prompt_style,
        few_shot_records=few_shot_records,
        max_source_length=args.max_source_length,
        max_target_length=args.max_target_length,
    )
    valid_dataset = GridPlanningDataset(
        records=valid_records,
        tokenizer=tokenizer,
        prompt_style=args.prompt_style,
        few_shot_records=few_shot_records,
        max_source_length=args.max_source_length,
        max_target_length=args.max_target_length,
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        label_pad_token_id=-100,
    )
    training_args = _training_args(args.output_dir, args)
    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": train_dataset,
        "eval_dataset": valid_dataset,
        "data_collator": data_collator,
        "compute_metrics": build_compute_metrics(tokenizer),
    }
    trainer_params = inspect.signature(Seq2SeqTrainer.__init__).parameters
    if "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    else:
        trainer_kwargs["tokenizer"] = tokenizer
    trainer = Seq2SeqTrainer(**trainer_kwargs)

    trainer.train(resume_from_checkpoint=args.resume_from_checkpoint or None)
    metrics = trainer.evaluate()

    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.output_dir) / "task2_finetune_config.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "model_name": args.model_name,
                "train_file": args.train_file,
                "valid_file": args.valid_file,
                "prompt_style": args.prompt_style,
                "n_train": len(train_records),
                "n_valid": len(valid_records),
                "max_source_length": args.max_source_length,
                "max_target_length": args.max_target_length,
                "metrics": metrics,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"Fine-tuned model and config saved to {args.output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fine-tune T5/BART-style seq2seq models on PPNL single-goal data."
    )
    parser.add_argument("--model_name", default="google/flan-t5-small")
    parser.add_argument("--train_file", default="data/single_goal/6x6/train.jsonl")
    parser.add_argument("--valid_file", default="data/single_goal/6x6/valid.jsonl")
    parser.add_argument("--output_dir", required=True)
    parser.add_argument(
        "--prompt_style",
        default="finetune",
        choices=list_prompt_styles(),
        help="Use finetune for the recommended compact supervised schema.",
    )
    parser.add_argument("--few_shot_file", default=None)
    parser.add_argument("--n_shots", type=int, default=0)
    parser.add_argument("--max_source_length", type=int, default=768)
    parser.add_argument("--max_target_length", type=int, default=64)
    parser.add_argument("--learning_rate", type=float, default=3e-4)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--warmup_ratio", type=float, default=0.03)
    parser.add_argument("--num_train_epochs", type=float, default=20.0)
    parser.add_argument("--per_device_train_batch_size", type=int, default=8)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=8)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1)
    parser.add_argument("--eval_steps", type=int, default=50)
    parser.add_argument("--save_steps", type=int, default=100)
    parser.add_argument(
        "--save_strategy",
        choices=["no", "steps", "epoch"],
        default="steps",
        help="Use 'no' on low-disk machines; the script still saves the final model.",
    )
    parser.add_argument(
        "--save_only_model",
        action="store_true",
        help="Checkpoint only model weights, not optimizer/scheduler state.",
    )
    parser.add_argument("--logging_steps", type=int, default=10)
    parser.add_argument("--save_total_limit", type=int, default=2)
    parser.add_argument("--num_beams", type=int, default=4)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--max_train_samples", type=int, default=0)
    parser.add_argument("--max_valid_samples", type=int, default=0)
    parser.add_argument("--resume_from_checkpoint", default=None)
    args = parser.parse_args()

    finetune(args)


if __name__ == "__main__":
    main()
