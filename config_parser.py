from sys import argv
from typing import Any


class ConfigError(Exception):
    pass


class MazeConfig:
    def __init__(self) -> None:
        self.width: int = 0
        self.height: int = 0
        self.entry: tuple[int, int] = (0, 0)
        self.exit_: tuple[int, int] = (0, 0)
        self.output_file: str = "maze.txt"
        self.perfect: bool = True
        self.seed: int | None = None
        self.algo: str = 'DFS'

    def parse_config(self) -> None:
        if len(argv) < 2:
            raise ConfigError("Usage: python3 a_maze_ing.py <config_file>")
        content: str | None = None
        try:
            with open(argv[1]) as f:
                content = f.read()
        except OSError as err:
            raise ConfigError(f"Configuration file error: {err}")
        if not content:
            raise ConfigError("The configuration file is empty.")

        raw: dict[str, str] = self._content_to_dict(content)
        config: dict[str, Any] = self._parse_dict(raw)

        self.width = config['WIDTH']
        self.height = config['HEIGHT']
        self.entry = config['ENTRY']
        self.exit_ = config['EXIT']
        self.output_file = config['OUTPUT_FILE']
        self.perfect = config['PERFECT']
        self.seed = config.get('SEED')
        self.algo = config.get('ALGORITHM', 'DFS')
        self._validate_config()

    def _validate_config(self) -> None:
        if self.width < 2:
            raise ConfigError("WIDTH must be a positive value > 2.")
        if self.height < 2:
            raise ConfigError("HEIGHT must be a positive value > 2.")
        if (not 0 <= self.entry[0] < self.width
                or not 0 <= self.entry[1] < self.height):
            raise ConfigError("ENTRY is out of the maze boundaries")
        if (not 0 <= self.exit_[0] < self.width
                or not 0 <= self.exit_[1] < self.height):
            raise ConfigError("EXIT is out of the maze boundaries")
        if self.entry == self.exit_:
            raise ConfigError("ENTRY and EXIT must be different.")

    @staticmethod
    def _content_to_dict(content: str) -> dict[str, str]:
        content = content.strip()
        if not content:
            raise ConfigError("The configuration file is empty.")
        raw: dict[str, str] = {}
        lines: list[str] = content.splitlines()
        for line in lines:
            if not line or '#' in line:
                continue
            if '=' not in line:
                raise ConfigError(
                    "The configuration file must contain one "
                    "'KEY=VALUE' pair per line."
                    )
            key, _, value = line.partition('=')
            if not key or not value:
                raise ConfigError(
                    "The configuration file must contain one "
                    "'KEY=VALUE' pair per line."
                )
            raw[key.strip().upper()] = value.strip()
        return raw

    @staticmethod
    def _parse_dict(raw: dict[str, str]) -> dict[str, Any]:

        mandatory: set[str] = {
                'WIDTH', 'HEIGHT', 'ENTRY', 'EXIT', 'OUTPUT_FILE', 'PERFECT'
        }
        missing: set[str] = mandatory.difference(raw.keys())
        if missing:
            raise ConfigError(
                "The following keys are missing: "
                f"{', '.join(missing)}"
                )

        config: dict[str, Any] = {}
        for key, value in raw.items():
            if key in ['WIDTH', 'HEIGHT', 'SEED']:
                try:
                    config[key] = int(value)
                except ValueError:
                    raise ConfigError(f"{key} must be an integer!")
            elif key in ['ENTRY', 'EXIT']:
                x, y = value.split(',', 1)
                try:
                    config[key] = (int(x.strip()), int(y.strip()))
                except ValueError:
                    raise ConfigError(f"{key} must have the format x,y")
            elif key == 'PERFECT':
                if value.capitalize() not in ['True', 'False']:
                    raise ConfigError(f"{key} must be 'True' or 'False'")
                if value.capitalize() == 'True':
                    config[key] = True
                else:
                    config[key] = False
            else:
                config[key] = value
        return config
