import json
from pathlib import Path
from typing import Dict, Any
from .models import ApiConfig


class ConfigManager:
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def load_api_config(self) -> ApiConfig:
        """Загрузка конфигурации API из файла"""
        config_file = self.config_dir / "api_config.json"

        if not config_file.exists():
            return ApiConfig("", "", "")

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            return ApiConfig(
                client_id=config_data.get("client_id", ""),
                client_secret=config_data.get("client_secret", ""),
                api_token=config_data.get("api_token", ""),
                refresh_token=config_data.get("refresh_token", "")
            )

    def save_api_config(self, config: ApiConfig) -> bool:
        """Сохранение конфигурации API в файл"""
        config_file = self.config_dir / "api_config.json"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "api_token": config.api_token,
                    "refresh_token": config.refresh_token
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            raise Exception(f"Не удалось сохранить конфигурацию API: {str(e)}")

    def load_locations(self) -> Dict[str, Any]:
        """Загрузка данных о локациях"""
        locations_file = self.config_dir / "locations.json"

        if not locations_file.exists():
            raise FileNotFoundError("Файл локаций не найден")

        with open(locations_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_locations(self, locations_data: Dict[str, Any]) -> bool:
        """Сохранение данных о локациях"""
        locations_file = self.config_dir / "locations.json"

        try:
            with open(locations_file, "w", encoding="utf-8") as f:
                json.dump(locations_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            raise Exception(f"Не удалось сохранить данные локаций: {str(e)}")
