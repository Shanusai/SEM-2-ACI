"""Smart Waste Collection Agent - IDA* implementation.

This module contains the same solver logic from the notebook
`ida_star_waste_collection.ipynb`.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any


class PathStack:
    """
    Stack data structure used to maintain the current DFS path in IDA*.
    Has a fixed capacity (= number of nodes in the graph) since the path
    can never be longer than visiting every node once.

    The stack methods print informative error messages when a push is
    attempted on a full stack or when pop/peek is attempted on an empty stack.
    """

    def __init__(self, capacity: int) -> None:
        self._stack: list[str] = []
        self._capacity = capacity
        self._items_set: set[str] = set()

    def push(self, item: str) -> bool:
        if len(self._stack) >= self._capacity:
            print(
                f"Stack overflow: Cannot push '{item}' - path stack is full (capacity={self._capacity})"
            )
            return False
        self._stack.append(item)
        self._items_set.add(item)
        return True

    def pop(self) -> str | None:
        if len(self._stack) == 0:
            print("Stack underflow: Cannot pop - path stack is empty!")
            return None
        item = self._stack.pop()
        self._items_set.discard(item)
        return item

    def peek(self) -> str | None:
        if len(self._stack) == 0:
            print("Stack empty: Nothing to peek!")
            return None
        return self._stack[-1]

    def __contains__(self, item: str) -> bool:
        return item in self._items_set

    def __len__(self) -> int:
        return len(self._stack)

    def to_list(self) -> list[str]:
        return list(self._stack)

    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def is_full(self) -> bool:
        return len(self._stack) >= self._capacity


def read_input(filename: Path) -> list[dict[str, Any]] | None:
    try:
        with filename.open("r", encoding="utf-8") as handle:
            content = handle.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' does not exist!")
        return None
    except IOError as error:
        print(f"Error: Could not read file - {error}")
        return None

    lines = [line.strip() for line in content.splitlines() if line.strip()]

    if len(lines) == 0:
        print("Error: Input file is empty!")
        return None

    cases: list[dict[str, Any]] = []
    i = 0

    while i < len(lines):
        while i < len(lines) and "road connections" not in lines[i].lower():
            i += 1
        if i >= len(lines):
            break
        i += 1

        edges: list[tuple[str, str, int]] = []
        while i < len(lines) and not lines[i].lower().startswith("source"):
            line = lines[i]
            parts = line.split()

            if len(parts) == 3:
                u, v = parts[0], parts[1]
                try:
                    w = int(parts[2])
                except ValueError:
                    print(f"Error: Weight '{parts[2]}' is not a valid integer in line: {line}")
                    return None
            else:
                print(
                    f"Error: Don't know how to parse this edge line: '{line}' - expected format 'U V W'"
                )
                return None

            if u == v:
                print(f"Error: Edge endpoints must be distinct, got '{u}-{v}'")
                return None

            if w <= 0:
                print(f"Error: Edge weight must be positive, got {w} for {u}-{v}")
                return None

            edges.append((u, v, w))
            i += 1

        if i >= len(lines) or "source" not in lines[i].lower():
            print("Error: Expected 'Source:' line but didn't find it")
            return None
        if ":" not in lines[i]:
            print("Error: Expected 'Source:' line to include a ':' separator")
            return None
        source = lines[i].split(":", 1)[1].strip()
        if not source:
            print("Error: Source is blank!")
            return None
        i += 1

        if i >= len(lines) or "destination" not in lines[i].lower():
            print("Error: Expected 'Destination:' line but didn't find it")
            return None
        if ":" not in lines[i]:
            print("Error: Expected 'Destination:' line to include a ':' separator")
            return None
        destination = lines[i].split(":", 1)[1].strip()
        if not destination:
            print("Error: Destination is blank!")
            return None
        i += 1

        if len(edges) == 0:
            print("Error: No edges found for this case")
            return None

        cases.append({"edges": edges, "source": source, "destination": destination})

    if len(cases) == 0:
        print("Error: Couldn't find any valid test cases in the file")
        return None

    return cases


def build_graph(edges: list[tuple[str, str, int]]) -> dict[str, list[tuple[str, int]]]:
    graph: dict[str, list[tuple[str, int]]] = {}

    for u, v, w in edges:
        graph.setdefault(u, []).append((v, w))
        graph.setdefault(v, []).append((u, w))

    if len(graph) == 0:
        print("Warning: Graph is empty, nothing was added")

    return graph


def print_graph(graph: dict[str, list[tuple[str, int]]]) -> None:
    print("\nGraph (Adjacency List):")
    if len(graph) == 0:
        print("  <empty graph>")
        return
    for node in sorted(graph.keys()):
        connections = [f"{nbr}({w})" for nbr, w in graph[node]]
        print(f"  {node} --> {connections}")


def resolve_input_path(input_pattern: str) -> Path | None:
    candidate = Path(input_pattern)
    if candidate.exists() and candidate.is_file():
        return candidate

    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()

    search_dirs: list[Path] = []
    if candidate.parent in (Path('.'), Path('')):
        search_dirs = [cwd, script_dir]
    else:
        search_dirs = [cwd / candidate.parent, script_dir / candidate.parent]

    exact_matches: list[Path] = []
    for directory in search_dirs:
        path = directory / candidate.name
        if path.exists() and path.is_file():
            exact_matches.append(path)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        print(f"Error: Multiple exact files match '{input_pattern}':")
        for path in exact_matches:
            print(f"  - {path}")
        return None

    # If no exact file found, try regex matching.
    regex_dirs = [d for d in search_dirs if d.exists() and d.is_dir()]
    if not regex_dirs:
        print(
            f"Error: Cannot search for input file; no valid directories found for pattern '{input_pattern}'."
        )
        return None

    try:
        matcher = re.compile(input_pattern)
    except re.error as error:
        print(f"Error: Invalid input regex '{input_pattern}': {error}")
        return None

    matches: list[Path] = []
    for directory in regex_dirs:
        for path in directory.iterdir():
            if path.is_file() and matcher.fullmatch(path.name):
                matches.append(path)

    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        dir_list = ", ".join(str(d) for d in regex_dirs)
        print(
            f"Error: No files match the input regex '{input_pattern}' in {dir_list}"
        )
        return None

    print(f"Error: Multiple files match the input regex '{input_pattern}':")
    for path in matches:
        print(f"  - {path}")
    return None


def validate_paths(input_path: Path, output_path: Path) -> bool:
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        return False
    if not input_path.is_file():
        print(f"Error: Input path '{input_path}' is not a file.")
        return False

    output_dir = output_path.parent
    if output_dir and not output_dir.exists():
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return False
    if output_dir and not output_dir.is_dir():
        print(f"Error: Output path '{output_dir}' is not a directory.")
        return False

    return True


def compute_heuristic(graph: dict[str, list[tuple[str, int]]], goal: str) -> dict[str, float]:
    if goal not in graph:
        print(f"Error: Goal '{goal}' is not present in the graph.")
        return {}

    min_weight = math.inf
    for node in graph:
        for _, w in graph[node]:
            if w < min_weight:
                min_weight = w

    if min_weight == math.inf:
        print("Error: Graph has no edges!")
        return {}

    hops: dict[str, int] = {goal: 0}
    queue = deque([goal])

    while queue:
        curr = queue.popleft()
        for neighbor, _ in graph[curr]:
            if neighbor not in hops:
                hops[neighbor] = hops[curr] + 1
                queue.append(neighbor)

    h: dict[str, float] = {}
    for node in graph:
        h[node] = hops.get(node, math.inf) * min_weight

    return h


def ida_star(
    graph: dict[str, list[tuple[str, int]]],
    source: str,
    destination: str,
) -> tuple[list[str] | None, int, int, list[list[str]]]:
    if source not in graph:
        print(f"Error: Source '{source}' doesn't exist in the graph!")
        return None, -1, 0, []

    if destination not in graph:
        print(f"Error: Destination '{destination}' doesn't exist in the graph!")
        return None, -1, 0, []

    if source == destination:
        return [source], 0, 1, [[source]]

    h = compute_heuristic(graph, destination)
    print(f"\n Heuristic values: {h}")

    if h.get(source, math.inf) == math.inf:
        print(f"Error: '{source}' cannot reach '{destination}' - no connecting path!")
        return None, -1, 0, []

    path = PathStack(capacity=len(graph))
    path.push(source)
    print(f" Initial threshold = h({source}) = {h[source]}")

    nodes_explored = [0]
    visited_per_iteration: list[list[str]] = []
    current_iter_visited: list[str] = []
    answer: list[Any] = [None]

    def dfs(g: int, threshold: float) -> float:
        node = path.peek()
        if node is None:
            return math.inf

        f = g + h[node]
        if f > threshold:
            print(
                f"   Pruned {node}: f({node}) = g({g}) + h({h[node]}) = {f} > threshold({threshold})"
            )
            return f

        nodes_explored[0] += 1
        current_iter_visited.append(node)
        print(f"   Exploring {node}: g={g}, h={h[node]}, f={f} <= threshold({threshold})")
        print(f"   Current path: {' -> '.join(path.to_list())}")

        if node == destination:
            answer[0] = (path.to_list(), g)
            print(f"   *** GOAL REACHED at {node} with cost {g} ***")
            print(f"   Final path: {' -> '.join(path.to_list())}")
            return -1

        next_threshold = math.inf
        for neighbor, cost in graph[node]:
            if neighbor in path:
                print(f"   Skipping {neighbor} (already in path - cycle avoided)")
                continue

            path.push(neighbor)
            t = dfs(g + cost, threshold)

            if t == -1:
                return -1
            if t < next_threshold:
                next_threshold = t

            path.pop()

        return next_threshold

    threshold = h[source]

    while True:
        current_iter_visited.clear()
        print(f" --- Iteration {len(visited_per_iteration) + 1}, threshold = {threshold} ---")
        t = dfs(0, threshold)
        visited_per_iteration.append(list(current_iter_visited))

        if t == -1:
            print(f" Goal found in iteration {len(visited_per_iteration)}!")
            result = answer[0]
            if result is None:
                return None, -1, nodes_explored[0], visited_per_iteration
            path_list, cost = result
            return path_list, cost, nodes_explored[0], visited_per_iteration

        if t == math.inf:
            print("Search exhausted - no path to destination.")
            return None, -1, nodes_explored[0], visited_per_iteration

        print(f" Threshold raised: {threshold} -> {t}")
        while not path.is_empty():
            path.pop()
        path.push(source)
        threshold = t


def solve(cases: list[dict[str, Any]], output_file: Path = Path("outputPSXX.txt")) -> None:
    output_lines: list[str] = []

    for idx, case in enumerate(cases, start=1):
        print(f"\n{'=' * 55}")
        print(f"  CASE {idx}")
        print(f"{'=' * 55}")

        graph = build_graph(case["edges"])
        print_graph(graph)

        src = case["source"]
        dst = case["destination"]
        print(f"\nSource: {src}")
        print(f"Destination: {dst}")

        path, cost, explored, visited = ida_star(graph, src, dst)

        print(f"\n--- Results ---")
        if path is not None:
            path_str = " -> ".join(path)
            iter_strs = [" -> ".join(nodes) for nodes in visited]
            visited_str = " | ".join(iter_strs)

            print(f"Optimal Path: {path_str}")
            print(f"Total Travel Cost: {cost}")
            print(f"Nodes Explored: {explored}")
            print("\nVisited Sequence (per iteration, separated by |):")
            for i, nodes in enumerate(visited, start=1):
                print(f"  Iteration {i}: {' -> '.join(nodes)}")

            output_lines.extend([
                f"Case {idx}:",
                f"Source: {src}",
                f"Destination: {dst}",
                f"Optimal Path: {path_str}",
                f"Total Travel Cost: {cost}",
                f"Nodes Explored: {explored}",
                f"Visited Sequence: {visited_str}",
                "",
            ])
        else:
            print("No path found.")
            output_lines.extend([f"Case {idx}: No path found", ""])

    try:
        with output_file.open("w", encoding="utf-8") as handle:
            handle.write("\n".join(output_lines))
        print(f"\n\nResults saved to '{output_file}'")
    except IOError as error:
        print(f"Error: Could not write to output file - {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Solve the waste collection problem using IDA* from a text input file."
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path or regex pattern for the input text file.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the output text file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = resolve_input_path(args.input)
    if input_path is None:
        return 1

    if not validate_paths(input_path, args.output):
        return 1

    cases = read_input(input_path)
    if cases is None:
        return 1

    print(f"Successfully loaded {len(cases)} case(s) from '{input_path}'")
    try:
        solve(cases, args.output)
    except Exception as error:
        print(f"Unexpected error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
