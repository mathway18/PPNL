# Part 2 Failure Analysis

## Aggregate Failure Types

| Category | Count |
|---|---:|
| optimal_success | 119 |
| obstacle_collision | 66 |
| wrong_final_cell | 13 |
| out_of_bounds | 2 |

## Representative Cases

### test_iid_000004 - wrong_final_cell

- Start: [4, 5]  Goal: [1, 2]
- Gold actions: `up up up left left left`
- Pred actions: `up up left left left`
- Final position: [2, 2]  Distance to goal: 1

Grid:
```text
# . . . . .
# # G . . .
. # . . . .
. . # . . .
. . . . # S
. . . # . #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [4, 5] | up | [3, 5] | ok |
| 2 | [3, 5] | up | [2, 5] | ok |
| 3 | [2, 5] | left | [2, 4] | ok |
| 4 | [2, 4] | left | [2, 3] | ok |
| 5 | [2, 3] | left | [2, 2] | ok |

### test_iid_000005 - obstacle_collision

- Start: [1, 3]  Goal: [4, 0]
- Gold actions: `down down down down left left up left`
- Pred actions: `down down down left left left`
- Final position: [4, 3]  Distance to goal: 3

Grid:
```text
. . . . . .
# . . S # .
# . . . . .
# # . . . .
G . # . . #
# . . . . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [1, 3] | down | [2, 3] | ok |
| 2 | [2, 3] | down | [3, 3] | ok |
| 3 | [3, 3] | down | [4, 3] | ok |
| 4 | [4, 3] | left | [4, 2] | obstacle_collision |

### test_iid_000011 - obstacle_collision

- Start: [3, 2]  Goal: [1, 3]
- Gold actions: `right up up`
- Pred actions: `up up right`
- Final position: [3, 2]  Distance to goal: 3

Grid:
```text
. # . . # #
. . . G . .
. . # . . .
. . S . # .
. . # . . .
# # . . . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [3, 2] | up | [2, 2] | obstacle_collision |

### test_iid_000015 - obstacle_collision

- Start: [5, 2]  Goal: [0, 1]
- Gold actions: `up up up left up up`
- Pred actions: `up up up up up left`
- Final position: [2, 2]  Distance to goal: 3

Grid:
```text
. G . . . .
. . # . # .
. . . . . .
. . . . . .
. . . . . .
. . S . # .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [5, 2] | up | [4, 2] | ok |
| 2 | [4, 2] | up | [3, 2] | ok |
| 3 | [3, 2] | up | [2, 2] | ok |
| 4 | [2, 2] | up | [1, 2] | obstacle_collision |

### test_iid_000016 - obstacle_collision

- Start: [2, 0]  Goal: [1, 1]
- Gold actions: `right up`
- Pred actions: `up right`
- Final position: [2, 0]  Distance to goal: 2

Grid:
```text
. . . . . .
# G # . . .
S . . . . .
. . . . . .
. # . . . .
. . . . . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [2, 0] | up | [1, 0] | obstacle_collision |

### test_iid_000018 - obstacle_collision

- Start: [0, 4]  Goal: [3, 1]
- Gold actions: `down left down down left left`
- Pred actions: `down down down left left left`
- Final position: [1, 4]  Distance to goal: 5

Grid:
```text
. . . . S #
. . # . . .
. . # . # .
. G . . . .
. . . . . .
. . . . . #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [0, 4] | down | [1, 4] | ok |
| 2 | [1, 4] | down | [2, 4] | obstacle_collision |

### test_iid_000020 - wrong_final_cell

- Start: [5, 5]  Goal: [2, 4]
- Gold actions: `up up up left`
- Pred actions: `up up left left`
- Final position: [3, 3]  Distance to goal: 2

Grid:
```text
. . . # . .
# . . . . #
. . . . G .
# . . . . .
. . . . . .
# # . . # S
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [5, 5] | up | [4, 5] | ok |
| 2 | [4, 5] | up | [3, 5] | ok |
| 3 | [3, 5] | left | [3, 4] | ok |
| 4 | [3, 4] | left | [3, 3] | ok |

### test_iid_000022 - obstacle_collision

- Start: [0, 3]  Goal: [3, 0]
- Gold actions: `left down down down left left`
- Pred actions: `down down down left left left`
- Final position: [0, 3]  Distance to goal: 6

Grid:
```text
. . . S . .
. # . # . .
. . . . . .
G . . . . .
. . # . . #
. # . . . #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [0, 3] | down | [1, 3] | obstacle_collision |

### test_iid_000024 - obstacle_collision

- Start: [1, 0]  Goal: [4, 3]
- Gold actions: `up right right down down down down right`
- Pred actions: `down down down right right right`
- Final position: [1, 0]  Distance to goal: 6

Grid:
```text
. . . . . .
S # . . . #
# . . # . .
. . . . . #
. . . G . #
# . # . . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [1, 0] | down | [2, 0] | obstacle_collision |

### test_iid_000025 - obstacle_collision

- Start: [4, 0]  Goal: [2, 5]
- Gold actions: `up up right right right right right`
- Pred actions: `up up up right right right right right`
- Final position: [1, 0]  Distance to goal: 6

Grid:
```text
. . . . . .
. # . . . .
. . . . . G
. . . . . .
S . . # . .
. . # . . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [4, 0] | up | [3, 0] | ok |
| 2 | [3, 0] | up | [2, 0] | ok |
| 3 | [2, 0] | up | [1, 0] | ok |
| 4 | [1, 0] | right | [1, 1] | obstacle_collision |

### test_iid_000027 - obstacle_collision

- Start: [4, 2]  Goal: [2, 5]
- Gold actions: `left up up right right right right`
- Pred actions: `up up right right right`
- Final position: [4, 2]  Distance to goal: 5

Grid:
```text
. . # # . .
. . . . # .
# . . . . G
. . # . . #
. . S # . .
. . . # . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [4, 2] | up | [3, 2] | obstacle_collision |

### test_iid_000030 - obstacle_collision

- Start: [5, 1]  Goal: [3, 1]
- Gold actions: `left up up right`
- Pred actions: `up up`
- Final position: [5, 1]  Distance to goal: 2

Grid:
```text
. . . # # .
. . . . # .
. . . . . .
. G # . . .
. # . . # .
. S . # . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [5, 1] | up | [4, 1] | obstacle_collision |
