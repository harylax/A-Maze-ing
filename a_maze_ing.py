from config_parser import MazeConfig, ConfigError
from mazegen import MazeGenerator
from output_writer import write_maze
from mlx_renderer import MazeMLX, MazeRendererError
from sys import stderr


def main() -> None:
    config = MazeConfig()
    config.parse_config()
    maze: MazeGenerator = MazeGenerator(
        config.width, config.height,
        config.entry, config.exit_,
        config.output_file, config.perfect,
        config.seed, config.algo
        )
    maze.generate()
    write_maze(maze)
    visual = MazeMLX(maze)
    visual.render()
    visual.run()


if __name__ == "__main__":
    try:
        main()
    except ConfigError as err:
        print(f"Configuration Error: {err}", file=stderr)
    except MazeRendererError as err:
        print(f"Minilibx Error: {err}", file=stderr)
    except BaseException as err:
        print(f"Maze Error: {err}", file=stderr)
