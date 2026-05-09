"""Prompt builders for Part 2 single-goal grid path planning experiments."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

try:
    from scripts.utils.actions import str_to_actions
    from scripts.utils.grid import ACTION_DELTAS
    from scripts.utils.io import read_jsonl
except ImportError:  # Allows running from inside scripts/.
    from utils.actions import str_to_actions
    from utils.grid import ACTION_DELTAS
    from utils.io import read_jsonl


PROMPT_STYLES = (
    "baseline",
    "structured_zero",
    "cot",
    "few_shot",
    "cot_few_shot",
    "finetune",
)


def list_prompt_styles() -> Tuple[str, ...]:
    return PROMPT_STYLES


def grid_size(record: dict) -> Tuple[int, int]:
    rows, cols = record["grid_size"]
    return int(rows), int(cols)


def obstacle_cells(record: dict) -> List[Tuple[int, int]]:
    """Return sorted obstacle coordinates from the world matrix."""
    obstacles: List[Tuple[int, int]] = []
    for r, row in enumerate(record["world"]):
        for c, value in enumerate(row):
            if value == 1:
                obstacles.append((r, c))
    return sorted(obstacles)


def format_coord(coord: Sequence[int]) -> str:
    return f"(row={int(coord[0])}, col={int(coord[1])})"


def format_obstacles(record: dict) -> str:
    obstacles = obstacle_cells(record)
    if not obstacles:
        return "none"
    return ", ".join(f"(row={r}, col={c})" for r, c in obstacles)


def format_indexed_grid(record: dict) -> str:
    """Render a grid with row/column indices so prompts are less ambiguous."""
    rows, cols = grid_size(record)
    rendered_rows = record["input_grid"].splitlines()
    header = "      " + " ".join(f"c{c}" for c in range(cols))
    body = [header]
    for r in range(rows):
        body.append(f"r{r:<2}  {rendered_rows[r]}")
    return "\n".join(body)


def planning_facts(record: dict, include_grid: bool = True) -> str:
    rows, cols = grid_size(record)
    parts = [
        f"Grid size: {rows} rows x {cols} columns.",
        f"Start: {format_coord(record['start'])}.",
        f"Goal: {format_coord(record['goal'])}.",
        f"Obstacles: {format_obstacles(record)}.",
    ]
    if include_grid:
        parts.append("Grid map (. empty, # obstacle, S start, G goal):")
        parts.append(format_indexed_grid(record))
    return "\n".join(parts)


def trace_gold_path(record: dict) -> str:
    """Create a compact gold-path trace for demonstrations."""
    actions = str_to_actions(record.get("target", ""))
    if not actions:
        return "No valid reference path is available."

    pos = (int(record["start"][0]), int(record["start"][1]))
    lines = [f"Start at {format_coord(pos)}."]
    for idx, action in enumerate(actions, start=1):
        dr, dc = ACTION_DELTAS[action]
        nxt = (pos[0] + dr, pos[1] + dc)
        lines.append(f"Step {idx}: {action} -> {format_coord(nxt)}.")
        pos = nxt
    lines.append(f"Reach the goal at {format_coord(record['goal'])}.")
    return "\n".join(lines)


def _base_instruction() -> str:
    return (
        "You are solving a single-goal grid path-planning task.\n"
        "Coordinates are 0-indexed as (row, col), with row 0 at the top and "
        "col 0 at the left.\n"
        "Allowed actions: up decreases row by 1; down increases row by 1; "
        "left decreases col by 1; right increases col by 1.\n"
        "Never move outside the grid and never enter an obstacle cell."
    )


def _answer_contract(final_answer: bool) -> str:
    if final_answer:
        return (
            "Reason about the path briefly, then end with exactly one line:\n"
            "Final answer: <space-separated actions using only up down left right>"
        )
    return "Return only the space-separated actions using up, down, left, and right."


def _example_block(record: dict, cot: bool) -> str:
    lines = ["Example:", planning_facts(record, include_grid=True)]
    if cot:
        lines.extend(["Reasoning:", trace_gold_path(record)])
        lines.append(f"Final answer: {record['target']}")
    else:
        lines.append(f"Actions: {record['target']}")
    return "\n".join(lines)


def _built_in_examples() -> List[dict]:
    return [
        {
            "id": "builtin_001",
            "grid_size": [3, 3],
            "world": [[2, 0, 0], [1, 1, 0], [0, 0, 3]],
            "start": [0, 0],
            "goal": [2, 2],
            "input_grid": "S . .\n# # .\n. . G",
            "target": "right right down down",
        },
        {
            "id": "builtin_002",
            "grid_size": [4, 4],
            "world": [[0, 0, 3, 0], [0, 1, 1, 0], [2, 0, 0, 0], [0, 0, 0, 0]],
            "start": [2, 0],
            "goal": [0, 2],
            "input_grid": ". . G .\n. # # .\nS . . .\n. . . .",
            "target": "up up right right",
        },
    ]


def load_few_shot_records(
    path: Optional[str],
    n_shots: int,
    seed: int = 13,
) -> List[dict]:
    if n_shots <= 0:
        return []

    if path:
        records = list(read_jsonl(path))
    else:
        records = _built_in_examples()

    rng = random.Random(seed)
    records = list(records)
    rng.shuffle(records)
    return records[:n_shots]


def build_prompt(
    record: dict,
    style: str = "structured_zero",
    few_shot_records: Optional[Iterable[dict]] = None,
) -> str:
    """Build a prompt for one grid-planning record."""
    style = style.lower().strip()
    if style not in PROMPT_STYLES:
        raise ValueError(f"Unknown prompt style {style!r}; choose from {PROMPT_STYLES}")

    if style == "baseline":
        return (
            f"Plan a path. {record['input_coord']} "
            "Output only actions separated by spaces: up, down, left, right."
        )

    if style == "finetune":
        return (
            "grid_path_planning\n"
            f"{planning_facts(record, include_grid=True)}\n"
            "actions:"
        )

    cot = style in {"cot", "cot_few_shot"}
    few_shot = style in {"few_shot", "cot_few_shot"}
    examples = list(few_shot_records or [])

    prompt_parts: List[str] = [_base_instruction()]
    if few_shot:
        if not examples:
            examples = _built_in_examples()
        prompt_parts.append(
            "Study the examples. The answer must be a feasible shortest path when possible."
        )
        for example in examples:
            prompt_parts.append(_example_block(example, cot=cot))

    prompt_parts.extend(
        [
            "Now solve this task.",
            planning_facts(record, include_grid=True),
            _answer_contract(final_answer=cot),
        ]
    )
    return "\n\n".join(prompt_parts)


def build_targets(records: Iterable[dict]) -> List[str]:
    """Return action-only training targets for seq2seq fine-tuning."""
    return [record["target"] for record in records]
