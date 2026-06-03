import random
import sys
from .solver import solve, path_to_directions
from .pattern_42 import draw_42

NORTH: int = 0b0001
EAST:  int = 0b0010
SOUTH: int = 0b0100
WEST:  int = 0b1000

sys.setrecursionlimit(100000)


class MazeGenerator:
    """Generate a 2D maze using DFS or Prim's algorithm.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        entry: (x, y) start cell.
        exit_: (x, y) end cell.
        output_file: File path for saving the maze.
        perfect: If True, no loops are added (pure spanning tree).
        seed: Random seed. None means unpredictable.
        algo: 'DFS' or 'prim'.
        grid: 2D list of cell wall bitmasks.
        visited: 2D list tracking which cells have been carved.
        solution: Ordered list of (x, y) cells from entry to exit.
        path: Directions in string from entry to exit.
        pattern_42: Set of (x, y) cells reserved for the '42' pattern.
        history: List of (current, neighbor) pairs recorded during carving.
    """
    def __init__(
            self,
            width: int = 20,
            height: int = 15,
            entry: tuple[int, int] = (0, 0),
            exit_: tuple[int, int] = (19, 14),
            output_file: str = "maze.txt",
            perfect: bool = True,
            seed: int | None = None,
            algo: str = 'DFS'
            ) -> None:
        self._validate_parameters(width, height, entry, exit_)
        self.width: int = width
        self.height: int = height
        self.entry: tuple[int, int] = entry
        self.exit_: tuple[int, int] = exit_
        self.output_file: str = output_file
        self.perfect: bool = perfect
        self.seed: int | None = seed
        self.algo: str = algo
        self.grid: list[list[int]] = []
        self.visited: list[list[bool]] = []
        self.solution: list[tuple[int, int]] = []
        self.path_str: str = ""
        self.pattern_42: set[tuple[int, int]] = set()
        self.history: list[tuple[tuple[int, int], tuple[int, int]]] = []

    @staticmethod
    def _validate_parameters(
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_: tuple[int, int]
    ) -> None:
        """Check that dimensions and entry/exit coordinates are valid.

        Args:
            width: Maze width.
            height: Maze height.
            entry: Entry coordinates.
            exit_: Exit coordinates.

        Raises:
            ValueError: If any value is out of range or entry == exit.
        """
        if width < 2:
            raise ValueError("WIDTH must be a positive value > 2.")
        if height < 2:
            raise ValueError("HEIGHT must be a positive value > 2.")
        if not 0 <= entry[0] < width or not 0 <= entry[1] < height:
            raise ValueError("ENTRY is out of the maze boundaries")
        if not 0 <= exit_[0] < width or not 0 <= exit_[1] < height:
            raise ValueError("EXIT is out of the maze boundaries")
        if entry == exit_:
            raise ValueError("ENTRY and EXIT must be different.")

    def generate(self) -> None:
        """Run the full maze generation pipeline.

        Seeds the RNG, initialises the grid, places the 42 pattern,
        carves passages, optionally adds loops, closes borders, and solves.
        """
        if self.seed is not None:
            random.seed(self.seed)
        self._init_grid()
        self.pattern_42 = draw_42(self.width, self.height)
        self._validate_entry_exit()
        self._apply_pattern_42()
        self._carve_passages()
        if not self.perfect:
            self._add_loops()
        self._close_all_borders()
        self.solution = solve(
            self.grid,
            self.width,
            self.height,
            self.entry,
            self.exit_
            )
        self.path_str = path_to_directions(self.solution)

    def _add_loops(self) -> None:
        """Remove randomly 10% of walls to create extra paths.

        Create imperfect maze when the perfect configuration is set to False.
        """
        cells: list[tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.pattern_42:
                    continue
                cells.append((x, y))
        random.shuffle(cells)
        num_loops: int = len(cells) // 10
        count: int = 0
        for x, y in cells:
            if count >= num_loops:
                return
            directions: list[tuple[int, int]] = [(1, 0), (0, 1)]
            dx, dy = random.choice(directions)
            nx, ny = x + dx, y + dy
            if (nx, ny) in self.pattern_42:
                continue
            if not self._is_valid_cell(nx, ny):
                continue
            self._remove_wall((x, y), (nx, ny))
            count += 1

    def _is_valid_cell(self, x: int, y: int) -> bool:
        """Return True if (x, y) is inside the maze bounds.

        Args:
            x: Column index.
            y: Row index.
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def _validate_entry_exit(self) -> None:
        """Raise an error if entry or exit falls inside the 42 pattern.

        Raises:
            ValueError: If entry or exit overlaps the pattern.
        """
        if self.entry in self.pattern_42:
            raise ValueError(
                "Invalid ENTRY coordinates, got "
                f"{self.entry} inside the 42 pattern"
                )
        if self.exit_ in self.pattern_42:
            raise ValueError(
                "Invalid EXIT coordinates, got "
                f"{self.exit_} inside the 42 pattern"
                )

    def _init_grid(self) -> None:
        """Fill grid with all-walls cells and mark all cells as unvisited."""
        self.grid = []
        self.visited = []
        for _ in range(self.height):
            row_int: list[int] = []
            row_bool: list[bool] = []
            for _ in range(self.width):
                walls: int = 0b1111
                visited: bool = False
                row_int.append(walls)
                row_bool.append(visited)
            self.grid.append(row_int)
            self.visited.append(row_bool)

    def _carve_passages(self) -> None:
        """Dispatch to the correct carving algorithm (DFS or Prim)."""
        if self.algo.lower() == 'prim':
            self._prim()
        else:
            self._dfs_recursive(self.entry)

    def _close_all_borders(self) -> None:
        """Set the outer border walls on all edge cells."""
        for y in range(self.height):
            for x in range(self.width):
                if y == 0:
                    self.grid[y][x] |= NORTH
                if y == self.height - 1:
                    self.grid[y][x] |= SOUTH
                if x == 0:
                    self.grid[y][x] |= WEST
                if x == self.width - 1:
                    self.grid[y][x] |= EAST

    def _apply_pattern_42(self) -> None:
        """Mark pattern cells as visited and wall off their neighbours."""
        directions: list[tuple[int, int, int]] = [
            (0, -1, SOUTH),
            (0, 1, NORTH),
            (-1, 0, EAST),
            (1, 0, WEST)
        ]
        for (px, py) in self.pattern_42:
            self.visited[py][px] = True
            for dx, dy, wall_to_close in directions:
                nx, ny = px + dx, py + dy
                if not self._is_valid_cell(nx, ny):
                    continue
                if (nx, ny) in self.pattern_42:
                    continue
                self.grid[ny][nx] |= wall_to_close

    def _remove_wall(
            self,
            current: tuple[int, int],
            neighbor: tuple[int, int]
    ) -> None:
        """Open the wall between two adjacent cells and record the step.

        Args:
            current: (x, y) of the first cell.
            neighbor: (x, y) of the adjacent cell.
        """
        x, y = current
        nx, ny = neighbor
        if x > nx:
            self.grid[y][x] &= ~WEST
            self.grid[ny][nx] &= ~EAST
        if x < nx:
            self.grid[y][x] &= ~EAST
            self.grid[ny][nx] &= ~WEST
        if y > ny:
            self.grid[y][x] &= ~NORTH
            self.grid[ny][nx] &= ~SOUTH
        if y < ny:
            self.grid[y][x] &= ~SOUTH
            self.grid[ny][nx] &= ~NORTH
        self.history.append((current, neighbor))

    def _dfs_recursive(self, current: tuple[int, int]) -> None:
        """Carve passages via recursive depth-first search.

        Args:
            current: (x, y) of the cell being visited.
        """
        x, y = current
        self.visited[y][x] = True
        directions: list[tuple[int, int]] = [
            (1, 0), (-1, 0), (0, 1), (0, -1)
        ]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if not self._is_valid_cell(nx, ny):
                continue
            if self.visited[ny][nx]:
                continue
            if (nx, ny) in self.pattern_42:
                continue
            self._remove_wall(current, (nx, ny))
            self._dfs_recursive((nx, ny))

    def _get_neighbors(
            self, current: tuple[int, int]
            ) -> list[tuple[int, int]]:
        """Return valid, non-pattern neighbours of a cell.

        Args:
            current: (x, y) of the source cell.

        Returns:
            List of (x, y) tuples for each reachable neighbour.
        """
        directions: list[tuple[int, int]] = [
            (1, 0), (-1, 0), (0, 1), (0, -1)
        ]
        neighbors: list[tuple[int, int]] = []
        x, y = current
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if not self._is_valid_cell(nx, ny):
                continue
            if (nx, ny) in self.pattern_42:
                continue
            neighbors.append((nx, ny))
        return neighbors

    def _prim(self) -> None:
        """Carve passages using a randomised Prim's algorithm."""
        x, y = self.entry
        self.visited[y][x] = True
        walls: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for (nx, ny) in self._get_neighbors((x, y)):
            if (nx, ny) in self.pattern_42:
                continue
            walls.append(((x, y), (nx, ny)))
        while walls:
            index: int = random.randrange(len(walls))
            current, neighbor = walls.pop(index)
            nx, ny = neighbor
            if self.visited[ny][nx]:
                continue
            self.visited[ny][nx] = True
            self._remove_wall(current, neighbor)
            for nnx, nny in self._get_neighbors(neighbor):
                if self.visited[nny][nnx]:
                    continue
                if (nnx, nny) in self.pattern_42:
                    continue
                walls.append((neighbor, (nnx, nny)))
