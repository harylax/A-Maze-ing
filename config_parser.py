from sys import argv
from typing import Any


class ConfigError(Exception):
    """Raised when the config file is missing,
    malformed, or has invalid values."""
    pass


class MazeConfig:
    """Read and validate maze settings from a config file.

    Attributes:
        width: Number of columns in the maze.
        height: Number of rows in the maze.
        entry: (x, y) coordinates of the maze entry point.
        exit_: (x, y) coordinates of the maze exit point.
        output_file: Path where the maze will be saved.
        perfect: If True, generate a perfect maze (no loops).
        seed: Random seed for reproducibility. None means random.
        algo: Generation algorithm, either 'DFS' or 'prim'.
    """
    def __init__(self) -> None:
        """Stores internally the config read."""
        self.width: int = 0
        self.height: int = 0
        self.entry: tuple[int, int] = (0, 0)
        self.exit_: tuple[int, int] = (0, 0)
        self.output_file: str = "maze.txt"
        self.perfect: bool = True
        self.seed: int | None = None
        self.algo: str = 'DFS'

    def parse_config(self) -> None:
        """Read the config file from argv and populate all attributes.

        Raises:
            ConfigError: If the file is missing or contains invalid data.
        """
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
        """Check that width, height, entry, and exit are consistent.

        Raises:
            ConfigError: If any value is out of range or entry == exit.
        """
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
        """Parse raw file text into a {KEY: value} string dictionary.

        Args:
            content: Full text of the config file.

        Returns:
            Dictionary of uppercased keys mapped to their raw string values.

        Raises:
            ConfigError: If a line is not in KEY=VALUE format.
        """
        content = content.strip()
        if not content:
            raise ConfigError("The configuration file is empty.")
        raw: dict[str, str] = {}
        lines: list[str] = content.splitlines()
        for line in lines:
            if '#' in line:
                i: int = line.index('#')
                line = line[:i]
            line = line.strip()
            if not line:
                continue
            if '=' not in line:
                raise ConfigError(
                    "The configuration file must contain one "
                    "'KEY=VALUE' pair per line."
                    )
            key, _, value = line.partition('=')
            key = key.strip().upper()
            value = value.strip()
            if not key or not value:
                raise ConfigError(
                    "The configuration file must contain one "
                    "'KEY=VALUE' pair per line."
                )
            if key in raw:
                raise ConfigError(f"Got a duplicate key: {key}")
            raw[key] = value
        return raw

    @staticmethod
    def _parse_dict(raw: dict[str, str]) -> dict[str, Any]:
        """Convert the raw string dictionary into typed Python values.

        Args:
            raw: Dictionary of string keys and string values.

        Returns:
            Dictionary with values cast to int, bool, or tuple as needed.

        Raises:
            ConfigError: If a mandatory key is missing
            or a value has the wrong type.
        """
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
