from mazegen import MazeGenerator
from mlx import Mlx
from typing import Any
from output_writer import write_maze
import random


NORTH: int = 0b0001
EAST:  int = 0b0010
SOUTH: int = 0b0100
WEST:  int = 0b1000

BG_COLOR:    int = 0xFF0F172A
CELL_COLOR:  int = 0xFF222222
ENTRY_COLOR: int = 0xFF60A5FA
EXIT_COLOR:  int = 0xFFFB7185
PATH_COLOR:  int = 0xFF22C55E
P42_COLOR:   int = 0xFFA855F7
TEXT_COLOR:  int = 0xFFFFFFFF

WALL_COLORS: list[int] = [
    0xFFFFFFFF,
    0xFFFF00FF,
    0xFFFF0000,
    0xFFFFFF00,
    0xFF0000FF,
    0xFF00FFFF
]


class MazeRendererError(Exception):
    pass


class MazeMLX:
    def __init__(self, maze: MazeGenerator) -> None:
        self.maze: MazeGenerator = maze
        self.mlx: Mlx = Mlx()
        self.mlx_ptr: Any = self.mlx.mlx_init()
        self.cell_size: int = self._cell_size()
        self.win_width: int = self.maze.width * self.cell_size
        self.win_height: int = self.maze.height * self.cell_size + 50
        self.win_ptr: Any = self.mlx.mlx_new_window(
            self.mlx_ptr, self.win_width,
            self.win_height, "Ayano.Rai"
            )
        self.data: Any
        self.bpp: int
        self.line_size: int
        self.fmt: int
        self.img_ptr: Any = self._create_image()
        self.show_solution: bool = False
        self._animation_index: int = 0
        self._path_displayed: bool = False
        self._is_animating_path: bool = False
        self.wall_color: int = WALL_COLORS[0]

    def _validate_size(self, screen_w: int, screen_h: int) -> None:
        min_cell_size: int = 16
        if (
            self.maze.width * min_cell_size > screen_w
            or self.maze.height * min_cell_size + 100 > screen_h
        ):
            raise MazeRendererError(
                "The size of the maze exceed screen size, "
                f"max width: {screen_w // min_cell_size}, "
                f"max height: {screen_h // min_cell_size - 7}."
                )

    def _cell_size(self) -> int:
        width = self.maze.width
        height = self.maze.height
        _, screen_w, screen_h = self.mlx.mlx_get_screen_size(
            self.mlx_ptr
            )
        min_cell_size: int = 16
        self._validate_size(screen_w, screen_h)
        cell_size: int = max(min_cell_size, min(
            (screen_w // 2) // width,
            (screen_h // 2) // height
            ))
        return cell_size

    def _create_image(self) -> Any:
        img_ptr: Any = self.mlx.mlx_new_image(
            self.mlx_ptr, self.win_width, self.win_height
            )
        self.data, self.bpp, self.line_size, self.fmt = \
            self.mlx.mlx_get_data_addr(img_ptr)
        return img_ptr

    def render(self) -> None:
        self._fill_background()
        self._set_animation(self._maze_animation)

    def show_path(self) -> None:
        if not self._path_displayed:
            self._fill_background()
            self._draw_full_maze()
            self._animation_index = 0
            self._set_animation(self._path_animation)
            self._path_displayed = False
            self._is_animating_path = True
        else:
            self._fill_background()
            self._draw_full_maze()
            self._path_displayed = False
            self._animation_index = 0

    def _set_animation(self, callback: Any) -> None:
        self._animation_index = 0
        self.mlx.mlx_loop_hook(self.mlx_ptr, None, None)
        self.mlx.mlx_loop_hook(self.mlx_ptr, callback, None)

    def _put_pixel(self, x: int, y: int, color: int) -> None:
        if not (0 <= x < self.win_width and 0 <= y < self.win_height):
            return
        i = self.bpp // 8
        offset = y * self.line_size + x * i
        color_bytes = color.to_bytes(i, 'little')
        self.data[offset:offset + i] = color_bytes

    def _fill_background(self) -> None:
        for y in range(self.win_height):
            for x in range(self.win_width):
                self._put_pixel(x, y, BG_COLOR)

    def _draw_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        for j in range(y, y + h):
            for i in range(x, x + w):
                self._put_pixel(i, j, color)

    def _draw_cell(self, margin: int, cx: int, cy: int, color: int) -> None:
        px = cx * self.cell_size + margin
        py = cy * self.cell_size + margin
        self._draw_rect(
            px, py,
            self.cell_size - margin * 2,
            self.cell_size - margin * 2,
            color
            )

    def _draw_full_maze(self) -> None:
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                self._draw_cell(1, x, y, CELL_COLOR)
                self._draw_walls(x, y, self.wall_color)
        self._draw_42_pattern()
        self._draw_entry_exit()
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
        )
        self._interactive_str()

    def _show_path_without_animation(self) -> None:
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                self._draw_cell(1, x, y, CELL_COLOR)
                self._draw_walls(x, y, self.wall_color)
        self._draw_42_pattern()
        for x, y in self.maze.solution:
            self._draw_cell(0, x, y, PATH_COLOR)
            self._draw_walls(x, y, self.wall_color)
        self._draw_entry_exit()
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
        )
        self._interactive_str()

    def _maze_animation(self, param: Any) -> None:
        if self._animation_index > len(self.maze.history) - 1:
            self._draw_42_pattern()
            self._draw_entry_exit()
            self.mlx.mlx_put_image_to_window(
                self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
                )
            self._interactive_str()
            self.mlx.mlx_loop_hook(self.mlx_ptr, None, None)
            return
        current, neighbor = self.maze.history[self._animation_index]
        cx, cy = current
        nx, ny = neighbor
        self._draw_cell(1, cx, cy, CELL_COLOR)
        self._draw_walls(cx, cy, self.wall_color)
        self._draw_cell(1, nx, ny, CELL_COLOR)
        self._draw_walls(nx, ny, self.wall_color)
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
        )
        self._interactive_str()
        self._animation_index += 1

    def _path_animation(self, param: Any) -> None:
        if self._animation_index > len(self.maze.solution) - 1:
            self._draw_entry_exit()
            self.mlx.mlx_put_image_to_window(
                self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
                )
            self._interactive_str()
            self.mlx.mlx_loop_hook(self.mlx_ptr, None, None)
            return
        x, y = self.maze.solution[self._animation_index]
        self._draw_cell(0, x, y, PATH_COLOR)
        self._draw_walls(x, y, self.wall_color)
        self._draw_entry_exit()
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img_ptr, 0, 0
        )
        self._interactive_str()
        self._animation_index += 1
        self._is_animating_path = False
        self._path_displayed = True

    def _interactive_str(self) -> None:
        if self.win_width < 600:
            self.mlx.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                10,
                self.win_height - 50,
                TEXT_COLOR,
                f"[a] {self.maze.algo.upper()} | "
                "[r] regenerate | [p] path"
                )
            self.mlx.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                10,
                self.win_height - 25,
                TEXT_COLOR,
                "[c] color | [esc] quit"
                )
        else:
            self.mlx.mlx_string_put(
                self.mlx_ptr,
                self.win_ptr,
                10,
                self.win_height - 30,
                TEXT_COLOR,
                f"[a] {self.maze.algo.upper()} | [r] regenerate | "
                "[p] path | [c] color | [esc] quit"
                )

    def _draw_42_pattern(self) -> None:
        for px, py in self.maze.pattern_42:
            self._draw_cell(1, px, py, P42_COLOR)

    def _draw_walls(self, cx: int, cy: int, color: int) -> None:
        cell: int = self.maze.grid[cy][cx]
        cs = self.cell_size
        x = cx * cs
        y = cy * cs
        wall: int = cs // 7
        if cell & NORTH:
            self._draw_rect(x, y, cs, wall, color)
        if cell & EAST:
            self._draw_rect(x + cs - wall, y, wall, cs, color)
        if cell & SOUTH:
            self._draw_rect(x, y + cs - wall, cs, wall, color)
        if cell & WEST:
            self._draw_rect(x, y, wall, cs, color)

    def _draw_entry_exit(self) -> None:
        sx, sy = self.maze.entry
        ex, ey = self.maze.exit_
        self._draw_cell(2, sx, sy, ENTRY_COLOR)
        self._draw_cell(2, ex, ey, EXIT_COLOR)

    def _key_hook(self, keycode: int, param: Any) -> int:
        if keycode == 65307:
            self.mlx.mlx_loop_exit(self.mlx_ptr)
        elif keycode in (ord('r'), ord('R')):
            self._regenerate()
        elif keycode in (ord('a'), ord('A')):
            if self.maze.algo.lower() == 'prim':
                self.maze.algo = 'DFS'
            else:
                self.maze.algo = 'prim'
            self._regenerate()
        elif keycode in (ord('p'), ord('P')):
            if self.maze.solution:
                self.show_path()
        elif keycode in (ord('c'), ord('C')):
            colors: list[int] = [
                c for c in WALL_COLORS if c != self.wall_color
                ]
            self.wall_color = random.choice(colors)
            self._draw_full_maze()
        elif keycode in [65293, 65421]:
            if self._is_animating_path:
                self.mlx.mlx_loop_hook(self.mlx_ptr, None, None)
                self._show_path_without_animation()
                self._is_animating_path = False
                self._path_displayed = True
            elif self._path_displayed:
                self._show_path_without_animation()
            else:
                self._draw_full_maze()
        return 0

    def _regenerate(self) -> None:
        self.maze = MazeGenerator(
            self.maze.width, self.maze.height,
            self.maze.entry, self.maze.exit_,
            self.maze.output_file, self.maze.perfect,
            self.maze.seed, self.maze.algo
            )
        if self.maze.seed is None:
            self.maze.seed = 0
        self.maze.seed += 1
        self.maze.generate()
        self._animation_index = 0
        self._path_displayed = False
        write_maze(self.maze)
        self.render()

    def run(self) -> None:
        self.mlx.mlx_key_hook(self.win_ptr, self._key_hook, None)
        self.mlx.mlx_loop(self.mlx_ptr)
