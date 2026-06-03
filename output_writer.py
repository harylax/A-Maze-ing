from mazegen import MazeGenerator
from mazegen.solver import path_to_directions
from config_parser import ConfigError


def write_maze(maze: MazeGenerator) -> None:
    maze_str: str = ""
    for row in maze.grid:
        for cell in row:
            maze_str += f'{cell:X}'
        maze_str += '\n'
    directions_str: str = path_to_directions(maze.solution)
    content: str = (
        maze_str + '\n'
        + f'{maze.entry[0]},{maze.entry[1]}\n'
        + f'{maze.exit_[0]},{maze.exit_[1]}\n'
        + directions_str + '\n'
    )
    try:
        with open(maze.output_file, 'w') as f:
            f.write(content)
    except OSError as err:
        raise ConfigError(f"Output file error: {err}")
