"""
Configuration loader utility for AutoJobFinder
"""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    # Python < 3.11 fallback
    import tomli as tomllib
from loguru import logger


class ConfigLoader:
    """Configuration loader class for managing application settings."""

    def __init__(self, config_path: Path):
        """
        Initialize the configuration loader.

        Args:
            config_path (Path): Path to the TOML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        Load and validate the TOML configuration file.

        Returns:
            dict: Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            tomllib.TOMLDecodeError: If config file is invalid TOML
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_path}"
                )

            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)

            self._validate_config(config)
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return config

        except Exception as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise

    def _validate_config(self, config: dict) -> None:
        """
        Validate the configuration structure and required fields.

        Args:
            config (dict): Configuration dictionary to validate

        Raises:
            ValueError: If required configuration fields are missing
        """
        required_sections = [
            "search",
            "application",
            "platforms",
            "browser",
            "delays",
            "logging",
        ]

        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate search settings
        search_fields = ["keywords", "location", "experience_level"]
        for field in search_fields:
            if field not in config["search"]:
                raise ValueError(f"Missing required search field: {field}")

        # Validate platform settings
        platforms = ["linkedin", "indeed", "glassdoor"]
        for platform in platforms:
            if platform not in config["platforms"]:
                raise ValueError(f"Missing platform configuration: {platform}")

            if "enabled" not in config["platforms"][platform]:
                raise ValueError(f"Missing 'enabled' field for platform: {platform}")

    def get(self, key: str, default=None):
        """
        Get a configuration value by key.

        Args:
            key (str): Configuration key (dot notation supported)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            value = self.config
            for k in key.split("."):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def update(self, key: str, value) -> None:
        """
        Update a configuration value.

        Args:
            key (str): Configuration key (dot notation supported)
            value: New value to set
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            config = config.setdefault(k, {})

        config[keys[-1]] = value
        logger.info(f"Configuration updated: {key} = {value}")

    def save(self) -> None:
        """Save the current configuration back to the TOML file."""
        try:
            # Note: tomllib is read-only. Use tomli_w for writing if needed.
            # For now, warn that save is not supported with standard library tomllib
            logger.warning(
                "Config save is not supported with tomllib. Use external tool to edit config.toml"
            )
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
