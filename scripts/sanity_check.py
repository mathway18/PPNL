#!/usr/bin/env python3
"""
Sanity check: verify data integrity and executor correctness.

Checks:
  1. Gold path check: running the gold "target" actions on each sample should
     yield success=1 and feasible=1.
  2. Bad action check: running a clearly wrong sequence (all "up") should
     yield success=0 on almost every sample.

Usage:
  python scripts/sanity_check.py --data_dir data/single_goal
  python scripts/sanity_check.py --data_file data/single_goal/6x6/train.jsonl
"""

import argparse
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.actions import str_to_actions
from scripts.utils.grid import execute_actions
from scripts.utils.io import read_jsonl


def check_file(path: str, n_samples: int = 0) -> dict:
    """Run sanity checks on a single JSONL file."""
    records = list(read_jsonl(path))
    if n_samples > 0:
        records = records[:n_samples]

    if not records:
        return {"path": path, "status": "empty", "n": 0}

    gold_pass = 0
    gold_fail_ids: List[str] = []
    bad_fail = 0
    bad_pass_ids: List[str] = []

    for record in records:
        world = record["world"]
        start = tuple(record["start"])
        goal = tuple(record["goal"])
        target = record["target"]
        sample_id = record.get("id", "?")

        # ── Check 1: gold path ────────────────────────────────────────────
        gold_actions = str_to_actions(target)
        if gold_actions is None:
            gold_fail_ids.append(f"{sample_id}(parse_fail)")
        else:
            result = execute_actions(world, start, goal, gold_actions)
            if result["success"] and result["feasible"]:
                gold_pass += 1
            else:
                gold_fail_ids.append(
                    f"{sample_id}(success={result['success']},feasible={result['feasible']})"
                )

        # ── Check 2: bad action (all "up") ────────────────────────────────
        rows = len(world)
        bad_actions = ["up"] * (rows * 2)  # Enough steps to hit the wall
        bad_result = execute_actions(world, start, goal, bad_actions)
        if not bad_result["success"]:
            bad_fail += 1
        else:
            bad_pass_ids.append(sample_id)

    n = len(records)
    gold_rate = gold_pass / n
    bad_fail_rate = bad_fail / n

    status = "PASS" if (gold_rate == 1.0 and bad_fail_rate >= 0.95) else "FAIL"

    result_dict = {
        "path": path,
        "status": status,
        "n": n,
        "gold_success_rate": round(gold_rate, 4),
        "bad_action_fail_rate": round(bad_fail_rate, 4),
    }
    if gold_fail_ids:
        result_dict["gold_failures"] = gold_fail_ids[:10]  # Show at most 10
    if bad_pass_ids:
        result_dict["bad_action_passed"] = bad_pass_ids[:10]

    return result_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanity check PPNL data files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data_dir", help="Check all *.jsonl files under this directory")
    group.add_argument("--data_file", help="Check a single JSONL file")
    parser.add_argument(
        "--n_samples",
        type=int,
        default=0,
        help="Number of samples to check per file (0 = all)",
    )
    args = parser.parse_args()

    files: List[str] = []
    if args.data_dir:
        files = sorted(str(p) for p in Path(args.data_dir).rglob("*.jsonl"))
        if not files:
            print(f"No JSONL files found under {args.data_dir}", file=sys.stderr)
            sys.exit(1)
    else:
        files = [args.data_file]

    all_pass = True
    for f in files:
        result = check_file(f, args.n_samples)
        status = result["status"]
        n = result["n"]
        gold_rate = result.get("gold_success_rate", 0)
        bad_rate = result.get("bad_action_fail_rate", 0)

        mark = "OK" if status == "PASS" else "FAIL"
        print(
            f"[{mark}] {f}  n={n}  gold_success={gold_rate:.4f}  bad_fail={bad_rate:.4f}  [{status}]"
        )
        if "gold_failures" in result:
            print(f"      Gold failures: {result['gold_failures']}")
        if "bad_action_passed" in result:
            print(f"      Bad-action passed (unexpected): {result['bad_action_passed']}")
        if status != "PASS":
            all_pass = False

    print()
    if all_pass:
        print("All sanity checks passed.")
    else:
        print("Some sanity checks FAILED. See details above.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
