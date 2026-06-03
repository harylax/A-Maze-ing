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
    """Raised when the MLX window or image cannot be created."""
    pass


class MazeMLX:
    """Render and animate the maze in a MiniLibX window.

    Attributes:
        maze: The MazeGenerator instance to render.
        mlx: The Mlx wrapper object.
        mlx_ptr: MLX instance pointer.
        cell_size: Pixel size of each maze cell.
        win_width: Window width in pixels.
        win_height: Window height in pixels (includes status bar).
        win_ptr: MLX window pointer.
        img_ptr: MLX image pointer used for drawing.
        show_solution: Whether the solution path is currently shown.
        wall_color: Current ARGB color used for walls.
    """
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
        """Raise an error if the maze is too large to fit on screen.

        Args:
            screen_w: Screen width in pixels.
            screen_h: Screen height in pixels.

        Raises:
            MazeRendererError: If the maze exceeds the minimum cell size limit.
        """
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
        """Compute the largest cell size that fits the maze on the screen.

        Returns:
            Cell size in pixels, at least 16.
        """
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
        """Create a new MLX image and store its data buffer and metadata.

        Returns:
            The MLX image pointer.
        """
        img_ptr: Any = self.mlx.mlx_new_image(
            self.mlx_ptr, self.win_width, self.win_height
            )
        self.data, self.bpp, self.line_size, self.fmt = \
            self.mlx.mlx_get_data_addr(img_ptr)
        return img_ptr

    def render(self) -> None:
        """Start the maze generation animation from the beginning."""
        self._fill_background()
        self._set_animation(self._maze_animation)

    def show_path(self) -> None:
        """Toggle the solution path animation on or off."""
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
        """Register a loop hook function as the current animation callback.

        Args:
            callback: Function called on every MLX loop tick.
        """
        self._animation_index = 0
        self.mlx.mlx_loop_hook(self.mlx_ptr, None, None)
        self.mlx.mlx_loop_hook(self.mlx_ptr, callback, None)

    def _put_pixel(self, x: int, y: int, color: int) -> None:
        """Write a single pixel to the image buffer.

        Args:
            x: Horizontal position in pixels.
            y: Vertical position in pixels.
            color: ARGB color as an integer.
        """
        if not (0 <= x < self.win_width and 0 <= y < self.win_height):
            return
        i = self.bpp // 8
        offset = y * self.line_size + x * i
        color_bytes = color.to_bytes(i, 'little')
        self.data[offset:offset + i] = color_bytes

    def _fill_background(self) -> None:
        """Fill the entire image with the background color."""
        for y in range(self.win_height):
            for x in range(self.win_width):
                self._put_pixel(x, y, BG_COLOR)

    def _draw_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        """Draw a filled rectangle on the image.

        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            w: Width in pixels.
            h: Height in pixels.
            color: ARGB fill color.
        """
        for j in range(y, y + h):
            for i in range(x, x + w):
                self._put_pixel(i, j, color)

    def _draw_cell(self, margin: int, cx: int, cy: int, color: int) -> None:
        """Draw a cell interior with an optional inset margin.

        Args:
            margin: Pixel inset on each side.
            cx: Cell column index.
            cy: Cell row index.
            color: ARGB fill color.
        """
        px = cx * self.cell_size + margin
        py = cy * self.cell_size + margin
        self._draw_rect(
            px, py,
            self.cell_size - margin * 2,
            self.cell_size - margin * 2,
            color
            )

    def _draw_full_maze(self) -> None:
        """Redraw every cell, wall, pattern, and entry/exit marker at once."""
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
        """Draw the maze with the solution path, skipping the animation."""
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
        """Loop hook that draws one generation step per tick.

        Args:
            param: Unused MLX hook parameter.
        """
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
        """Loop hook that draws one solution step per tick.

        Args:
            param: Unused MLX hook parameter.
        """
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
        """Print the keyboard shortcut hint at the bottom of the window."""
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
        """Highlight all cells that belong to the '42' pattern."""
        for px, py in self.maze.pattern_42:
            self._draw_cell(1, px, py, P42_COLOR)

    def _draw_walls(self, cx: int, cy: int, color: int) -> None:
        """Draw the walls of a single cell based on its bitmask.

        Args:
            cx: Cell column index.
            cy: Cell row index.
            color: ARGB wall color.
        """
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
        """Draw the entry and exit cells with their dedicated colors."""
        sx, sy = self.maze.entry
        ex, ey = self.maze.exit_
        self._draw_cell(2, sx, sy, ENTRY_COLOR)
        self._draw_cell(2, ex, ey, EXIT_COLOR)

    def _key_hook(self, keycode: int, param: Any) -> int:
        """Handle keyboard input from the MLX window.

        Args:
            keycode: The key code received from MLX.
            param: Unused MLX hook parameter.

        Returns:
            0 to signal success to MLX.
        """
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
        """Regenerate the maze with an incremented seed."""
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
        """Start the MLX event loop and listen for key events."""
        self.mlx.mlx_key_hook(self.win_ptr, self._key_hook, None)
        self.mlx.mlx_loop(self.mlx_ptr)
