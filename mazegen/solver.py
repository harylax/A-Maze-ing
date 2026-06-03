from collections import deque

NORTH: int = 0b0001
EAST: int = 0b0010
SOUTH: int = 0b0100
WEST: int = 0b1000


def solve(
        grid: list[list[int]],
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_: tuple[int, int],
        pattern_42: set[tuple[int, int]] | None = None
        ) -> list[tuple[int, int]]:
    """Find the shortest path from entry to exit using BFS.

    Args:
        grid: 2D list of cell bitmasks (walls encoded as NESW bits).
        width: Number of columns.
        height: Number of rows.
        entry: (x, y) starting cell.
        exit_: (x, y) target cell.
        pattern_42: Set of (x, y) isolated cells. Defaults to empty.

    Returns:
        List of (x, y) tuples from entry to exit.
        Or an empty list if no path exists.
    """
    if pattern_42 is None:
        pattern_42 = set()
    queue: deque[tuple[int, int]] = deque([entry])
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {entry: None}
    directions: dict[int, tuple[int, int]] = {
        NORTH: (0, -1),
        EAST: (1, 0),
        SOUTH: (0, 1),
        WEST: (-1, 0)
    }
    while queue:
        x, y = queue.popleft()
        if (x, y) == exit_:
            return _reconstruct_path(came_from, exit_)
        for direction, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in pattern_42:
                continue
            if (nx, ny) in came_from:
                continue
            if grid[y][x] & direction:
                continue
            came_from[(nx, ny)] = (x, y)
            queue.append((nx, ny))
    return []


def _reconstruct_path(
        came_from: dict[tuple[int, int], tuple[int, int] | None],
        exit_: tuple[int, int]
) -> list[tuple[int, int]]:
    """Trace the BFS parent map back from exit to entry.

    Args:
        came_from: Dict mapping each cell to the cell it was reached from.
        exit_: The target cell where reconstruction starts.

    Returns:
        Ordered list of (x, y) tuples from entry to exit.
    """
    path: list[tuple[int, int]] = []
    current: tuple[int, int] | None = exit_
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


def path_to_directions(path: list[tuple[int, int]]) -> str:
    """Convert a list of (x, y) positions into a compact direction string.

    Args:
        path: Ordered list of (x, y) tuples.

    Returns:
        String of N/E/S/W characters, e.g. 'NEESSWN'. Empty string if path < 2.
    """
    if len(path) < 2:
        return ""
    result: list[str] = []
    directions: dict[str, tuple[int, int]] = {
        'N': (0, -1),
        'E': (1, 0),
        'S': (0, 1),
        'W': (-1, 0)
    }
    for i in range(1, len(path)):
        x0, y0 = path[i - 1]
        x1, y1 = path[i]
        dx, dy = x1 - x0, y1 - y0
        for dir_letter, (ddx, ddy) in directions.items():
            if ddx == dx and ddy == dy:
                result.append(dir_letter)
                break
    return ''.join(result)
