"""Основная точка входа в приложение"""

import sys
import logging
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from core.config_manager import ConfigManager
from ui.main_window import MainWindow


@dataclass
class AppConfig:
    """Конфигурация приложения."""
    temp_dir: Path = Path("temp")
    logs_dir: Path = temp_dir / "logs"
    reports_dir: Path = temp_dir / "reports"
    presets_dir: Path = temp_dir / "presets"
    log_file: Path = logs_dir / "app.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level: int = logging.INFO


def setup_logging(config: AppConfig):
    """Конфигурация логирования приложения."""
    config.temp_dir.mkdir(exist_ok=True)
    config.logs_dir.mkdir(exist_ok=True)
    config.reports_dir.mkdir(exist_ok=True)
    config.presets_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=config.log_level,
        format=config.log_format,
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler()
        ]
    )

def main() -> None:
    """Точка входа в приложение."""
    config = AppConfig()
    setup_logging(config)
    logger = logging.getLogger(__name__)

    window = None

    try:
        app = QApplication(sys.argv)
        config_manager = ConfigManager()
        window = MainWindow(config_manager)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical("Ошибка приложения: %s", str(e), exc_info=True)
        # Создаем временное QApplication, если основное не было создано
        if not QApplication.instance():
            temp_app = QApplication(sys.argv)
        msg_box = QMessageBox.critical(
            window if 'window' in locals() else None,  # Используем window если он существует
            "Критическая ошибка",
            f"Не удалось запустить приложение: {str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
