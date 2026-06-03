import random
import sys
from .solver import solve
from .pattern_42 import draw_42

NORTH: int = 0b0001
EAST:  int = 0b0010
SOUTH: int = 0b0100
WEST:  int = 0b1000

sys.setrecursionlimit(100000)


class MazeGenerator:
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
        self.pattern_42: set[tuple[int, int]] = set()
        self.history: list[tuple[tuple[int, int], tuple[int, int]]] = []

    @staticmethod
    def _validate_parameters(
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_: tuple[int, int]
    ) -> None:
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

    def _add_loops(self) -> None:
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
        return 0 <= x < self.width and 0 <= y < self.height

    def _validate_entry_exit(self) -> None:
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
        if self.algo.lower() == 'prim':
            self._prim()
        else:
            self._dfs_recursive(self.entry)

    def _close_all_borders(self) -> None:
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

    def _remove_wall(self,
                     current: tuple[int, int],
                     neighbor: tuple[int, int]
                     ) -> None:
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
