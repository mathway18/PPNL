# Part 2 Failure Analysis

## Aggregate Failure Types

| Category | Count |
|---|---:|
| obstacle_collision | 96 |
| optimal_success | 93 |
| wrong_final_cell | 9 |
| out_of_bounds | 2 |

## Representative Cases

### test_ood_000001 - obstacle_collision

- Start: [5, 4]  Goal: [4, 3]
- Gold actions: `right up up left left down`
- Pred actions: `up left left up`
- Final position: [5, 4]  Distance to goal: 2

Grid:
```text
# . # # # .
. # . # . #
. # # . . .
# . . . . .
. . . G # .
# . # # S .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [5, 4] | up | [4, 4] | obstacle_collision |

### test_ood_000003 - obstacle_collision

- Start: [5, 3]  Goal: [1, 5]
- Gold actions: `right up up up right up`
- Pred actions: `up up up up right right up`
- Final position: [5, 3]  Distance to goal: 6

Grid:
```text
. . # # # #
. . # # # G
. . . # . .
. . . . . .
. # . # . .
# . # S . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [5, 3] | up | [4, 3] | obstacle_collision |

### test_ood_000006 - obstacle_collision

- Start: [5, 4]  Goal: [3, 1]
- Gold actions: `up left up up left left down`
- Pred actions: `left left left up`
- Final position: [5, 3]  Distance to goal: 4

Grid:
```text
# # . . # #
. # # # . .
# . . . . #
. G # . # #
. # # . . .
. . # . S .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [5, 4] | left | [5, 3] | ok |
| 2 | [5, 3] | left | [5, 2] | obstacle_collision |

### test_ood_000009 - obstacle_collision

- Start: [5, 4]  Goal: [0, 0]
- Gold actions: `up up up left left left up left up`
- Pred actions: `up up up up left left left left up`
- Final position: [2, 4]  Distance to goal: 6

Grid:
```text
G # . # # .
. . # . # #
# . . . . .
. # # . . #
. . # # . #
# # . . S .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [5, 4] | up | [4, 4] | ok |
| 2 | [4, 4] | up | [3, 4] | ok |
| 3 | [3, 4] | up | [2, 4] | ok |
| 4 | [2, 4] | up | [1, 4] | obstacle_collision |

### test_ood_000010 - obstacle_collision

- Start: [2, 1]  Goal: [3, 4]
- Gold actions: `right down right right`
- Pred actions: `down right right right`
- Final position: [2, 1]  Distance to goal: 4

Grid:
```text
. # # . . #
. . . # . .
# S . # # .
. # . . G .
# # # . . .
. . . # # #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [2, 1] | down | [3, 1] | obstacle_collision |

### test_ood_000011 - wrong_final_cell

- Start: [0, 2]  Goal: [1, 2]
- Gold actions: `down`
- Pred actions: `down left`
- Final position: [1, 1]  Distance to goal: 1

Grid:
```text
. # S # # #
. . G . . .
# # . # . .
# # . # # #
. # # . # #
. . . . # .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [0, 2] | down | [1, 2] | reached_goal |
| 2 | [1, 2] | left | [1, 1] | ok |

### test_ood_000018 - obstacle_collision

- Start: [2, 3]  Goal: [0, 1]
- Gold actions: `down down left left left up up up up right`
- Pred actions: `up left left left up`
- Final position: [2, 3]  Distance to goal: 4

Grid:
```text
. G # # . .
. . # # . .
. . # S . #
. # # . . #
. . . . # #
. . # . . #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [2, 3] | up | [1, 3] | obstacle_collision |

### test_ood_000021 - obstacle_collision

- Start: [1, 5]  Goal: [5, 0]
- Gold actions: `left left left up left left down down down down down`
- Pred actions: `left left down down down left left left`
- Final position: [1, 3]  Distance to goal: 7

Grid:
```text
. . . # . .
. # . . . S
. . # # # .
. . . # # .
. # # . . #
G . . . # #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [1, 5] | left | [1, 4] | ok |
| 2 | [1, 4] | left | [1, 3] | ok |
| 3 | [1, 3] | down | [2, 3] | obstacle_collision |

### test_ood_000023 - obstacle_collision

- Start: [4, 3]  Goal: [1, 4]
- Gold actions: `up right up up`
- Pred actions: `up up right up`
- Final position: [3, 3]  Distance to goal: 3

Grid:
```text
# # # . . .
# # . # G .
. # # # . .
. . # . . .
. . # S . .
# # # # . #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [4, 3] | up | [3, 3] | ok |
| 2 | [3, 3] | up | [2, 3] | obstacle_collision |

### test_ood_000026 - obstacle_collision

- Start: [4, 4]  Goal: [2, 0]
- Gold actions: `left up left up up left left down`
- Pred actions: `left left left left up`
- Final position: [4, 3]  Distance to goal: 5

Grid:
```text
. . . . # #
. . . # # .
G # . # # #
. # . . # #
# # # . S .
# . . # . .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [4, 4] | left | [4, 3] | ok |
| 2 | [4, 3] | left | [4, 2] | obstacle_collision |

### test_ood_000029 - obstacle_collision

- Start: [4, 2]  Goal: [1, 4]
- Gold actions: `up right up up right`
- Pred actions: `up up up right right`
- Final position: [3, 2]  Distance to goal: 4

Grid:
```text
# # . . # #
# . . . G .
. # # . # .
# . . . . #
# # S # . #
. # . # # .
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [4, 2] | up | [3, 2] | ok |
| 2 | [3, 2] | up | [2, 2] | obstacle_collision |

### test_ood_000030 - obstacle_collision

- Start: [0, 2]  Goal: [5, 3]
- Gold actions: `down down down right down down`
- Pred actions: `left down down down right right down down`
- Final position: [0, 1]  Distance to goal: 7

Grid:
```text
. . S # . .
. # . . . #
# # . # . #
. . . . . .
. # # . # .
# . # G # #
```

| Step | From | Action | Attempted | Result |
|---:|---|---|---|---|
| 1 | [0, 2] | left | [0, 1] | ok |
| 2 | [0, 1] | down | [1, 1] | obstacle_collision |
