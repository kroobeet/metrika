import json
from pathlib import Path
from typing import Dict, Any
import logging

from .models import ApiConfig
from .exceptions import ConfigError


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration files."""

    DEFAULT_CONFIG_DIR = "configs"

    def __init__(self, config_dir: str = DEFAULT_CONFIG_DIR):
        """Initialize config manager with config directory.

        Args:
            config_dir: Path to directory containing config files.
        """
        self.config_dir = Path(config_dir)
        self._ensure_config_dir_exists()

    def _ensure_config_dir_exists(self) -> None:
        """Ensure config directory exists, create if not."""
        try:
            self.config_dir.mkdir(exist_ok=True, parents=True)
        except OSError as e:
            error_msg = f"Failed to create config directory {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg) from e

    def load_api_config(self) -> ApiConfig:
        """Load API configuration from file.

        Returns:
            ApiConfig object with loaded configuration.

        Raises:
            ConfigError: If config file is invalid or can't be read
        """
        config_file = self.config_dir / "api_config.json"

        if not config_file.exists():
            logger.warning("API config file not found, returning empty config.")
            return ApiConfig("", "", "")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                return ApiConfig(
                    client_id=config_data["client_id", ""],
                    client_secret=config_data["client_secret", ""],
                    api_token=config_data["api_token", ""],
                    refresh_token=config_data["refresh_token", ""],
                )
        except (json.JSONDecodeError, OSError) as e:
            error_msg = f"Failed to load API config: {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg) from e

    def save_api_config(self, config: ApiConfig) -> None:
        """Save API configuration to file.

        Args:
            config: ApiConfig object to save.

        Raises:
            ConfigError: If config can't be saved.
        """
        config_file = self.config_dir / "api_config.json"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "api_token": config.api_token,
                    "refresh_token": config.refresh_token,
                }, f, ensure_ascii=False, indent=2)
                logger.info("API config saved successfully")
        except (OSError, TypeError) as e:
            error_msg = f"Failed to save API config: {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg) from e

    def load_locations(self) -> Dict[str, Any]:
        """Load locations data from file

        Returns:
            Dictionary with locations data.

        Raises:
            ConfigError: If locations file is invalid or can't be read
        """
        locations_file = self.config_dir / "locations.json"

        if not locations_file.exists():
            error_msg = "Locations file not found"
            logger.error(error_msg)
            raise ConfigError(error_msg)

        try:
            with open(locations_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            error_msg = f"Failed to load locations data: {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg) from e

    def save_locations(self, locations_data: Dict[str, Any]) -> None:
        """Save locations data to file.

        Args:
            locations_data: Dictionary with locations data to save.

        Raises:
            ConfigError: If locations can't be saved
        """
        locations_file = self.config_dir / "locations.json"

        try:
            with open(locations_file, "w", encoding="utf-8") as f:
                json.dump(locations_data, f, ensure_ascii=False, indent=2)
            logger.info("Location data saved successfully")
        except (OSError, TypeError) as e:
            error_msg = f"Failed to save locations data: {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg) from e
