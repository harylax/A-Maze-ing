from .generator import MazeGenerator
"""
Maze Generator Package - A reusable maze generation library.

This module provides multiple maze generation
algorithms and solving capabilities.
It offers a flexible, extensible framework
for creating perfect and imperfect mazes
using different algorithmic approaches (Depth-First Search, Prim's algorithm).

The package is designed for reusability and has no external dependencies beyond
the Python standard library.

Quick Start:
    >>> from mazegen import MazeGenerator
    >>>
    >>>
    >>> generator = MazeGenerator()
    >>> generator.generate()
    >>> solution = generator.solution
    >>> print(f"Solution found: {len(solution)} steps")
    >>> print(f"Directions from entry to exit: {generator.path_str}")

Custom parameters:
    The generator accepts several optional parameters:
        generator = MazeGenerator(
        width=30,
        height=20,
        entry=(0, 0),
        exit_=(29, 19),
        seed=42,
        perfect=True,
        algo="prim"
    )
Parameters:
    - width: maze width in cells.
    - height: maze height in cells.
    - entry: starting cell coordinates (x, y).
    - exit_: ending cell coordinates (x, y).
    - seed: random seed for reproducible mazes.
    - perfect: if False, additional loops are added.
    - algo: generation algorithm ("DFS" or "prim").

Accessing Generated Data:
    - generator.solution: List of (x, y) coordinates from entry to exit.
    - generator.path_str: String of directions (N, E, W, S) from entry to exit.
    - generator.grid: 2D list of cell wall configurations.
    - generator.history: List of passages carved during generation.
    - generator.pattern_42: Set of coordinates containing the 42 pattern.

Attributes:
    __version__ (str): Package version.
    __all__ (list): Public API exports.
"""

__version__ = "1.0.0"
__all__ = ['MazeGenerator', 'path_to_directions', 'solve']
