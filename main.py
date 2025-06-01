import sys
import logging
from PySide6.QtWidgets import QApplication
from core.config_manager import ConfigManager
from ui.main_window import MainWindow


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Точка входа в приложение"""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        app = QApplication(sys.argv)

        # Инициализация менеджера конфигурации
        config_manager = ConfigManager()

        # Создание и отображение главного окна
        window = MainWindow(config_manager)
        window.show()

        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()