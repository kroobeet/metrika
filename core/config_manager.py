"""Модуль для управления файлами конфигурации приложения."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from .models import ApiConfig
from .exceptions import ConfigError


logger = logging.getLogger(__name__)


@dataclass
class ConfigManagerSettings:
    """Настройки для ConfigManager."""
    config_dir: Path = Path("configs")
    api_config_file: str = "api_config.json"
    locations_file: str = "locations.json"


class ConfigManager:
    """Менеджер файлов конфигурации приложения."""

    def __init__(self, settings: Optional[ConfigManagerSettings] = None):
        """Инициализация с настройками"""
        self.settings = settings or ConfigManagerSettings()
        self._ensure_config_dir_exists()

    def _ensure_config_dir_exists(self) -> None:
        """Убедимся, что каталог конфигурации существует"""
        try:
            self.settings.config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Не удалось создать каталог конфигурации: %s", str(e), exc_info=True)
            raise ConfigError(f"Ошибка в каталоге конфигурации: {str(e)}") from e

    def load_api_config(self) -> ApiConfig:
        """Загружает конфигурацию API из файла.

        Returns:
            Объект конфигурации ApiConfig с загруженной конфигурацией

        Raises:
            ConfigError: Если конфигурационный файл недействителен
        """
        config_file = self.settings.config_dir / self.settings.api_config_file

        if not config_file.exists():
            logger.warning("Конфигурационный файл API не найден, возвращена пустая конфигурация")
            return ApiConfig("", "", "")

        try:
            with config_file.open("r", encoding="utf-8") as f:
                config_data = json.load(f)
                return ApiConfig(
                    client_id=config_data.get("client_id", ""),
                    client_secret=config_data.get("client_secret", ""),
                    api_token=config_data.get("api_token", ""),
                    refresh_token=config_data.get("refresh_token", "")
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Не удалось загрузить конфигурацию API: %s", str(e), exc_info=True)
            raise ConfigError(f"Ошибка загрузки конфигурации API: {str(e)}") from e

    def save_api_config(self, config: ApiConfig) -> None:
        """Сохранение конфигурации API в файл.

        Args:
            config: ApiConfig для сохранения

        Raises:
            ConfigError: Если конфигурация не может быть сохранена
        """
        config_file = self.settings.config_dir / self.settings.api_config_file

        try:
            with config_file.open("w", encoding="utf-8") as f:
                json.dump({
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "api_token": config.api_token,
                    "refresh_token": config.refresh_token,
                }, f, ensure_ascii=False, indent=2)
            logger.info("Конфигурация API успешно сохранена")
        except (OSError, TypeError) as e:
            logger.error("Не удалось сохранить конфигурацию API: %s", str(e), exc_info=True)
            raise ConfigError(f"Ошибка сохранения конфигурации API: {str(e)}") from e

    def load_locations(self) -> Dict[str, Any]:
        """Загрузка данных по локациям из файла.

        Returns:
            Словарь с данными по локациям

        Raises:
            ConfigError: Если файл локаций недействителен
        """
        locations_file = self.settings.config_dir / self.settings.locations_file

        if not locations_file.exists():
            logger.error("Файл локаций не найден")
            raise ConfigError(f"Файл локаций не найден")

        try:
            with locations_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Не удалось загрузить локации: %s", str(e), exc_info=True)
            raise ConfigError(f"Ошибка загрузки локаций: {str(e)}") from e

    def save_locations(self, locations_data: Dict[str, Any]) -> None:
        """Сохранение данных по локациям в файл.

        Args:
            locations_data: Словарь с данными по локациям

        Raises:
            ConfigError: Если локации не были сохранены
        """
        locations_file = self.settings.config_dir / self.settings.locations_file

        try:
            with locations_file.open("w", encoding="utf-8") as f:
                json.dump(locations_data, f, ensure_ascii=False, indent=2)
            logger.info("Данные по локациям были успешно сохранены")
        except (OSError, TypeError) as e:
            logger.error("Не удалось сохранить локации: %s", str(e), exc_info=True)
            raise ConfigError(f"Ошибка сохранения локаций: {str(e)}") from e
