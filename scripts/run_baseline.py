#!/usr/bin/env python3
"""Run seq2seq inference for Part 1 baselines and Part 2 prompt variants."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.task2_prompts import build_prompt, list_prompt_styles, load_few_shot_records
from scripts.utils.actions import actions_to_str, extract_actions
from scripts.utils.io import read_jsonl, write_jsonl


ANSWER_MARKERS = (
    "final answer:",
    "final:",
    "answer:",
    "actions:",
    "action sequence:",
    "path:",
)


def _batched(records: List[dict], batch_size: int) -> Iterable[List[dict]]:
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def _answer_region(text: str) -> str:
    """Prefer the text after the last explicit answer marker."""
    lower = text.lower()
    best_pos = -1
    best_marker = ""
    for marker in ANSWER_MARKERS:
        pos = lower.rfind(marker)
        if pos > best_pos:
            best_pos = pos
            best_marker = marker
    if best_pos >= 0:
        return text[best_pos + len(best_marker) :]
    return text


def postprocess_prediction(raw_text: str, prediction_mode: str) -> str:
    """Convert model text into the action-only field consumed by the executor."""
    cleaned = re.sub(r"\s+", " ", raw_text).strip()
    if prediction_mode == "raw":
        return cleaned

    candidate = _answer_region(cleaned)
    actions = extract_actions(candidate)
    if actions is None and candidate != cleaned:
        actions = extract_actions(cleaned)
    if actions is None:
        return cleaned
    return actions_to_str(actions)


def run_inference(
    model_name: str,
    data_path: str,
    out_path: str,
    prompt_style: str = "baseline",
    few_shot_file: Optional[str] = None,
    n_shots: int = 0,
    batch_size: int = 4,
    max_source_length: int = 768,
    max_new_tokens: int = 64,
    num_beams: int = 4,
    prediction_mode: str = "actions",
    include_prompt: bool = False,
    limit: int = 0,
    seed: int = 13,
    do_sample: bool = False,
    temperature: float = 1.0,
    top_p: float = 1.0,
) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    print(f"Loading {model_name} on {device}...")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    model.eval()

    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    records = list(read_jsonl(data_path))
    if limit > 0:
        records = records[:limit]

    few_shot_records = load_few_shot_records(few_shot_file, n_shots=n_shots, seed=seed)
    predictions = []

    print(
        f"Starting inference for {len(records)} samples "
        f"(prompt_style={prompt_style}, batch_size={batch_size})..."
    )

    generate_kwargs = {
        "max_new_tokens": max_new_tokens,
        "num_beams": num_beams,
        "do_sample": do_sample,
    }
    if do_sample:
        generate_kwargs.update({"temperature": temperature, "top_p": top_p})

    done = 0
    for batch in _batched(records, batch_size):
        prompts = [
            build_prompt(record, style=prompt_style, few_shot_records=few_shot_records)
            for record in batch
        ]
        inputs = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_source_length,
        ).to(device)

        with torch.inference_mode():
            output_ids = model.generate(**inputs, **generate_kwargs)

        raw_texts = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        for record, prompt, raw_text in zip(batch, prompts, raw_texts):
            pred_record = {
                "id": record["id"],
                "prediction": postprocess_prediction(raw_text, prediction_mode),
                "raw_prediction": raw_text,
                "prompt_style": prompt_style,
                "model": model_name,
            }
            if include_prompt:
                pred_record["prompt"] = prompt
            predictions.append(pred_record)

        done += len(batch)
        if done % max(batch_size * 10, 1) == 0 or done == len(records):
            print(f"Processed {done}/{len(records)}")

    write_jsonl(predictions, out_path)
    print(f"Predictions saved to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run HF seq2seq inference for grid path planning."
    )
    parser.add_argument(
        "--model",
        default="google/flan-t5-small",
        help="HF model name or local fine-tuned checkpoint directory.",
    )
    parser.add_argument("--data_file", required=True, help="Input JSONL file.")
    parser.add_argument("--out_file", required=True, help="Output JSONL predictions.")
    parser.add_argument(
        "--prompt_style",
        default="baseline",
        choices=list_prompt_styles(),
        help="Prompting schema for Part 2 experiments.",
    )
    parser.add_argument(
        "--few_shot_file",
        default=None,
        help="Training JSONL used as the source of few-shot examples.",
    )
    parser.add_argument("--n_shots", type=int, default=0)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--max_source_length", type=int, default=768)
    parser.add_argument("--max_new_tokens", type=int, default=64)
    parser.add_argument("--num_beams", type=int, default=4)
    parser.add_argument(
        "--prediction_mode",
        choices=["actions", "raw"],
        default="actions",
        help="actions extracts final action tokens; raw stores untouched model text.",
    )
    parser.add_argument("--include_prompt", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Debug on the first N records.")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--do_sample", action="store_true")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_p", type=float, default=1.0)
    args = parser.parse_args()

    run_inference(
        model_name=args.model,
        data_path=args.data_file,
        out_path=args.out_file,
        prompt_style=args.prompt_style,
        few_shot_file=args.few_shot_file,
        n_shots=args.n_shots,
        batch_size=args.batch_size,
        max_source_length=args.max_source_length,
        max_new_tokens=args.max_new_tokens,
        num_beams=args.num_beams,
        prediction_mode=args.prediction_mode,
        include_prompt=args.include_prompt,
        limit=args.limit,
        seed=args.seed,
        do_sample=args.do_sample,
        temperature=args.temperature,
        top_p=args.top_p,
    )


if __name__ == "__main__":
    main()
