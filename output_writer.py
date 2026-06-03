from mazegen import MazeGenerator
from config_parser import ConfigError


def write_maze(maze: MazeGenerator) -> None:
    """Write the maze grid, entry/exit coords,
    and solution directions to a file.

    Args:
        maze: A MazeGenerator instance with a populated grid and solution.

    Raises:
        ConfigError: If the output file cannot be written.
    """
    maze_str: str = ""
    for row in maze.grid:
        for cell in row:
            maze_str += f'{cell:X}'
        maze_str += '\n'
    content: str = (
        maze_str + '\n'
        + f'{maze.entry[0]},{maze.entry[1]}\n'
        + f'{maze.exit_[0]},{maze.exit_[1]}\n'
        + maze.path_str + '\n'
    )
    try:
        with open(maze.output_file, 'w') as f:
            f.write(content)
    except OSError as err:
        raise ConfigError(f"Output file error: {err}")
