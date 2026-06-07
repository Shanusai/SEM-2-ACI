# Assignment 1 – PS1: Smart Waste Collection Agent

## Problem Statement

The city of Bengaluru has implemented a Smart City initiative for waste management. A robot agent needs to find the cheapest route from a starting waste collection center to a target processing unit. The city's road network is modeled as a weighted undirected graph where nodes are locations and edges are roads with travel costs.

We need to implement IDA* (Iterative Deepening A*) to solve this efficiently.

---

## 1. PEAS Analysis

| Component | Description |
|-----------|-------------|
| **Performance** | Minimize total travel cost from source to destination; find the optimal (shortest cost) path |
| **Environment** | Static weighted graph representing Bengaluru's waste management road network; positive edge weights (travel cost/fuel) |
| **Actuators** | Robot moves along edges from one node to an adjacent connected node |
| **Sensors** | Robot knows its current location, adjacent roads and their costs, and the goal location |

**Agent Type:** Goal-based, single agent operating in a fully observable, deterministic, static, discrete environment.

---

## 2. Heuristic Function

We use a **hop-based admissible heuristic**:

```
h(n) = min_hops(n, goal) × min_edge_weight
```

Where:
- `min_hops(n, goal)` = shortest number of edges from node n to the goal (computed via BFS on the unweighted graph)
- `min_edge_weight` = smallest edge weight in the entire graph

**Why is this admissible?**

Since every edge costs at least `min_edge_weight`, and we need at least `min_hops` edges to reach the goal, the product gives a lower bound on the actual cost. It never overestimates, so IDA* with this heuristic is guaranteed to find the optimal solution.

**Why is this consistent?**

For any edge (n, n') with cost c:
- h(n) - h(n') ≤ min_edge_weight ≤ c

So the heuristic satisfies the consistency (monotonicity) condition as well.

---

## 3. Cost Function

IDA* uses the evaluation function:

```
f(n) = g(n) + h(n)
```

- **g(n)** = actual cost of the path from source to node n (sum of edge weights along the path taken so far)
- **h(n)** = heuristic estimate of remaining cost from n to goal

The algorithm maintains a cost threshold. In each iteration, it does a depth-first search and prunes any path where f(n) exceeds the threshold. If the goal isn't found, the threshold is raised to the smallest f-value that exceeded the previous threshold, and the search repeats.

---

## 4. Why IDA* ?

IDA* was chosen over other algorithms because:

1. **Optimal**: With an admissible heuristic, IDA* guarantees finding the least-cost path (same as A*)
2. **Memory efficient**: Unlike A* which stores the entire frontier in a priority queue (O(b^d) space), IDA* only keeps the current path in memory (O(d) space, where d is depth)
3. **Informed search**: Uses heuristic guidance to avoid exploring clearly suboptimal paths, unlike blind searches like BFS or DFS
4. **Suitable for route planning**: The robot operates on limited battery, so we need an algorithm that is both optimal and doesn't consume excessive computational resources

The trade-off is that IDA* may re-expand some nodes across iterations, but for moderately sized city graphs this is acceptable given the memory savings.

---

## 5. Implementation

The solution is implemented in a single Jupyter notebook: **ida_star_waste_collection.ipynb**

Key components:
- `read_input()` – parses the input file using explicit edge lines `node1 node2 weight`
- `build_graph()` – constructs adjacency list representation
- `compute_heuristic()` – BFS-based hop heuristic calculation
- `ida_star_search()` – core IDA* with cycle detection and threshold iteration
- `solve_and_display()` – runs all cases and writes output file

Notes:
- The command-line script now requires both input and output arguments.
- Input file selection supports an exact path or a regex pattern that matches a single file name.
- Edges must be provided explicitly as `U V W`; compact tokens like `AB3` are rejected.
- The `PathStack` data structure reports `Stack overflow` when `push()` is called on a full stack, and `Stack underflow` when `pop()` is called on an empty stack.
- The reported node count is `Nodes Explored`, counting total nodes visited during search.
- `Visited Sequence` lists the deepest path explored in each IDA* iteration, not the optimal path itself.

Files:
- `ida_star_waste_collection.ipynb` – main notebook with code
- `inputPSXX.txt` – test input
- `outputPSXX.txt` – generated output

---

## 6. Alternate Modeling Approach

**Alternative: Dijkstra's Algorithm (Uniform Cost Search)**

Instead of IDA*, we could model this as a standard shortest-path problem using Dijkstra's algorithm with a min-heap priority queue.

| Aspect | IDA* | Dijkstra |
|--------|------|----------|
| Optimality | Yes (with admissible h) | Yes |
| Time | O(b^d) worst case, but heuristic prunes | O((V+E) log V) |
| Space | O(d) – only current path | O(V) – stores all visited + frontier |
| Heuristic | Uses h(n) for pruning | No heuristic (uninformed) |
| Nodes expanded | Fewer with good heuristic | May expand more nodes |

**Performance implication**: For large city graphs with thousands of nodes, Dijkstra would use more memory to maintain the priority queue and visited set. IDA* uses minimal memory but may revisit nodes across iterations. For our problem size, both work well, but IDA* better demonstrates intelligent search with heuristic guidance.

---

## 7. How to Run

From the notebook:
1. Place `ida_star_waste_collection.ipynb` and `inputPSXX.txt` in the same directory.
2. Open the notebook in Jupyter and run all cells.
3. Output will be printed in the notebook and saved to `outputPSXX.txt`.

From the Python module:
```bash
python3 AS-1/ida_star_waste_collection.py AS-1/inputPSXX.txt AS-1/outputPSXX.txt
```

The module also supports regex-based input selection when the pattern matches exactly one file name:
```bash
python3 AS-1/ida_star_waste_collection.py 'input.*\.txt' AS-1/outputPSXX.txt
```

### Output meanings
- `Optimal Path`: the lowest-cost route found by IDA*
- `Total Travel Cost`: total edge weight along the optimal path
- `Nodes Explored`: unique nodes visited during the search
- `Visited Sequence`: deepest path explored in each IDA* iteration

---

## 8. Sample Output

**Case 1** (Bengaluru locations):
- Optimal Path: MG_Road → Electronic_City → Whitefield → Yelahanka
- Total Cost: 8
- Nodes Explored: 4
- Visited Sequence: MG_Road → Electronic_City → Whitefield | MG_Road → Electronic_City → Whitefield → Yelahanka

**Case 2** (Abstract nodes):
- Optimal Path: A → C → D → E
- Total Cost: 5
- Nodes Explored: 5
- Visited Sequence: A | A → C | A → C → D | A → B → C → D → E
