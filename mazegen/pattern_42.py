import sys


def draw_42(width: int, height: int) -> set[tuple[int, int]]:
    if width < 9 or height < 7:
        print("Maze size is too small for the 42 pattern", file=sys.stderr)
        return set()
    grid_42: list[list[int]] = [
        [1, 0, 0, 0, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 0, 1, 1, 1],
        [0, 0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 1, 1, 1]
    ]
    grid_center: tuple[int, int] = (
        width // 2,
        height // 2
        )
    x, y = grid_center
    offset = x - 3, y - 2
    dx, dy = offset
    pattern: set[tuple[int, int]] = set()
    for row, line in enumerate(grid_42):
        for col, element in enumerate(line):
            if element == 1:
                pattern.add((col + dx, row + dy))
    return pattern
