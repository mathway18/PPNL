# Part 2 Failure Analysis

## Aggregate Failure Types

| Category | Count |
|---|---:|
| parse_failure | 170 |
| out_of_bounds | 14 |
| obstacle_collision | 10 |
| wrong_final_cell | 6 |

## Representative Cases

### test_iid_000001 - parse_failure

- Start: [5, 2]  Goal: [4, 4]
- Gold actions: `up right right`
- Pred actions: `[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,`
- Final position: [5, 2]  Distance to goal: 3

Grid:
```text
. . . . . .
# . . . . .
. # . . . #
. . . . # .
. # . . G .
. . S . . .
```

No executable action trace because the prediction could not be parsed.

### test_iid_000002 - out_of_bounds

- Start: [3, 1]  Goal: [3, 0]
- Gold actions: `left`
- Pred actions: `up down left right down right right right left right right right right right right right right right right right right right right right`
- Final position: [4, 5]  Distance to goal: 6

Grid:
```text
# . . . . .
. . . . . .
. . . . . #
G S . . . .
. . . . . .
. . # . . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [3, 1] | up | [2, 1] | ok |
| 2 | [2, 1] | down | [3, 1] | ok |
| 3 | [3, 1] | left | [3, 0] | reached_goal |
| 4 | [3, 0] | right | [3, 1] | ok |
| 5 | [3, 1] | down | [4, 1] | ok |
| 6 | [4, 1] | right | [4, 2] | ok |
| 7 | [4, 2] | right | [4, 3] | ok |
| 8 | [4, 3] | right | [4, 4] | ok |
| 9 | [4, 4] | left | [4, 3] | ok |
| 10 | [4, 3] | right | [4, 4] | ok |
| 11 | [4, 4] | right | [4, 5] | ok |
| 12 | [4, 5] | right | [4, 6] | out_of_bounds |

### test_iid_000003 - parse_failure

- Start: [1, 2]  Goal: [4, 1]
- Gold actions: `down down down left`
- Pred actions: `Plan a path. Plan a path. Plan a path. Plan a path. Plan a path. Plan a path. Plan a path. Plan a path. Plan a path. Plan a path.`
- Final position: [1, 2]  Distance to goal: 4

Grid:
```text
. . # . . .
# . S . . .
. . . . . #
. . . . . .
. G . . . .
. . . # . .
```

No executable action trace because the prediction could not be parsed.

### test_iid_000004 - parse_failure

- Start: [4, 5]  Goal: [1, 2]
- Gold actions: `up up up left left left`
- Pred actions: `[(0, 0), (1, 1), (2, 1), (3, 2), (4, 4), (5, 3), (5, 5)]`
- Final position: [4, 5]  Distance to goal: 6

Grid:
```text
# . . . . .
# # G . . .
. # . . . .
. . # . . .
. . . . # S
. . . # . #
```

No executable action trace because the prediction could not be parsed.

### test_iid_000005 - parse_failure

- Start: [1, 3]  Goal: [4, 0]
- Gold actions: `down down down down left left up left`
- Pred actions: `[(1, 0), (1, 0), (3, 0), (3, 0), (4, 0), (5, 0), (5, 0), (5, 0), (5, 0), (5, 0`
- Final position: [1, 3]  Distance to goal: 6

Grid:
```text
. . . . . .
# . . S # .
# . . . . .
# # . . . .
G . # . . #
# . . . . .
```

No executable action trace because the prediction could not be parsed.
