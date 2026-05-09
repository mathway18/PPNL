#!/usr/bin/env python3
"""Trace prediction failures for single-goal grid path planning."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.actions import actions_to_str, extract_actions, str_to_actions
from scripts.utils.grid import ACTION_DELTAS, OBSTACLE, render_grid
from scripts.utils.io import read_jsonl, write_jsonl


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def trace_actions(
    world: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    actions: List[str],
) -> dict:
    rows = len(world)
    cols = len(world[0])
    pos = start
    trace = []
    feasible = True
    first_goal_step: Optional[int] = None
    failure_reason: Optional[str] = None

    for step_idx, action in enumerate(actions, start=1):
        dr, dc = ACTION_DELTAS[action]
        attempted = (pos[0] + dr, pos[1] + dc)
        step = {
            "step": step_idx,
            "from": list(pos),
            "action": action,
            "attempted": list(attempted),
        }

        if not (0 <= attempted[0] < rows and 0 <= attempted[1] < cols):
            feasible = False
            failure_reason = "out_of_bounds"
            step["status"] = "invalid"
            step["reason"] = failure_reason
            trace.append(step)
            break

        if world[attempted[0]][attempted[1]] == OBSTACLE:
            feasible = False
            failure_reason = "obstacle_collision"
            step["status"] = "invalid"
            step["reason"] = failure_reason
            trace.append(step)
            break

        pos = attempted
        step["to"] = list(pos)
        step["status"] = "ok"
        if pos == goal and first_goal_step is None:
            first_goal_step = step_idx
            step["reached_goal"] = True
        trace.append(step)

    success = pos == goal
    if failure_reason is None:
        if success and first_goal_step is not None and first_goal_step < len(actions):
            failure_reason = "extra_actions_after_goal"
        elif not success:
            failure_reason = "wrong_final_cell"
        else:
            failure_reason = "success"

    return {
        "trace": trace,
        "feasible": feasible,
        "success": success,
        "final_pos": list(pos),
        "first_goal_step": first_goal_step,
        "failure_reason": failure_reason,
        "distance_to_goal": manhattan(pos, goal),
    }


def classify_case(parse_ok: bool, trace_result: Optional[dict], pred_len: int, gold_len: int) -> str:
    if not parse_ok:
        return "parse_failure"
    assert trace_result is not None
    reason = trace_result["failure_reason"]
    if reason in {"out_of_bounds", "obstacle_collision", "extra_actions_after_goal"}:
        return reason
    if trace_result["success"] and pred_len <= gold_len:
        return "optimal_success"
    if trace_result["success"]:
        return "nonoptimal_success"
    return "wrong_final_cell"


def analyze(data_file: str, pred_file: str) -> List[dict]:
    data_map = {record["id"]: record for record in read_jsonl(data_file)}
    cases = []

    for pred_record in read_jsonl(pred_file):
        sample_id = pred_record.get("id")
        if sample_id not in data_map:
            continue
        record = data_map[sample_id]
        prediction = str(pred_record.get("prediction", ""))
        raw_prediction = str(pred_record.get("raw_prediction", prediction))
        actions = extract_actions(prediction)
        parse_ok = actions is not None
        gold_actions = str_to_actions(record["target"]) or []

        trace_result = None
        if parse_ok and actions is not None:
            trace_result = trace_actions(
                record["world"],
                tuple(record["start"]),
                tuple(record["goal"]),
                actions,
            )

        category = classify_case(
            parse_ok=parse_ok,
            trace_result=trace_result,
            pred_len=len(actions or []),
            gold_len=len(gold_actions),
        )

        case = {
            "id": sample_id,
            "category": category,
            "parse_ok": int(parse_ok),
            "grid_size": record["grid_size"],
            "start": record["start"],
            "goal": record["goal"],
            "grid": render_grid(record["world"]),
            "prediction": prediction,
            "raw_prediction": raw_prediction,
            "pred_actions": actions_to_str(actions) if actions else "",
            "gold_actions": record["target"],
            "pred_len": len(actions or []),
            "gold_len": len(gold_actions),
        }
        if trace_result is not None:
            case.update(trace_result)
            case["optimal"] = int(trace_result["success"] and len(actions or []) <= len(gold_actions))
        else:
            case.update(
                {
                    "trace": [],
                    "feasible": 0,
                    "success": 0,
                    "optimal": 0,
                    "final_pos": record["start"],
                    "first_goal_step": None,
                    "failure_reason": "parse_failure",
                    "distance_to_goal": manhattan(tuple(record["start"]), tuple(record["goal"])),
                }
            )
        cases.append(case)

    return cases


def _trace_table(case: dict) -> str:
    if not case["trace"]:
        return "No executable action trace because the prediction could not be parsed."

    lines = [
        "| Step | From | Action | Attempted | Result |",
        "|---:|---|---|---|---|",
    ]
    for step in case["trace"]:
        result = step["status"]
        if step.get("reason"):
            result = step["reason"]
        elif step.get("reached_goal"):
            result = "reached_goal"
        lines.append(
            f"| {step['step']} | {step['from']} | {step['action']} | "
            f"{step['attempted']} | {result} |"
        )
    return "\n".join(lines)


def write_markdown(cases: List[dict], out_md: str, max_cases: int, include_success: bool) -> None:
    counts = Counter(case["category"] for case in cases)
    selected = [
        case
        for case in cases
        if include_success or case["category"] not in {"optimal_success", "nonoptimal_success"}
    ][:max_cases]

    lines = ["# Part 2 Failure Analysis", ""]
    lines.append("## Aggregate Failure Types")
    lines.append("")
    lines.extend(["| Category | Count |", "|---|---:|"])
    for category, count in counts.most_common():
        lines.append(f"| {category} | {count} |")

    lines.extend(["", "## Representative Cases", ""])
    if not selected:
        lines.append("No cases selected.")

    for case in selected:
        lines.append(f"### {case['id']} - {case['category']}")
        lines.append("")
        lines.append(f"- Start: {case['start']}  Goal: {case['goal']}")
        lines.append(f"- Gold actions: `{case['gold_actions']}`")
        lines.append(f"- Pred actions: `{case['pred_actions'] or case['prediction']}`")
        lines.append(
            f"- Final position: {case['final_pos']}  Distance to goal: {case['distance_to_goal']}"
        )
        lines.append("")
        lines.append("Grid:")
        lines.append("```text")
        lines.append(case["grid"])
        lines.append("```")
        lines.append("")
        lines.append(_trace_table(case))
        lines.append("")

    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate detailed failure traces from model predictions."
    )
    parser.add_argument("--data_file", required=True)
    parser.add_argument("--pred_file", required=True)
    parser.add_argument("--out_jsonl", required=True)
    parser.add_argument("--out_md", default=None)
    parser.add_argument("--max_cases", type=int, default=12)
    parser.add_argument("--include_success", action="store_true")
    args = parser.parse_args()

    cases = analyze(args.data_file, args.pred_file)
    write_jsonl(cases, args.out_jsonl)

    counts = Counter(case["category"] for case in cases)
    print("Failure categories:")
    for category, count in counts.most_common():
        print(f"  {category}: {count}")

    if args.out_md:
        write_markdown(cases, args.out_md, args.max_cases, args.include_success)
        print(f"Markdown report written to {args.out_md}")


if __name__ == "__main__":
    main()
