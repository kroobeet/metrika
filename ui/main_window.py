"""Главное окно приложения для аналитики Яндекс.Метрики"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget,
                               QHBoxLayout, QPushButton, QLabel, QFileDialog,
                               QMessageBox)
from PySide6.QtCore import Qt, Signal

from core.api_client import MetrikaApiClient
from core.data_processor import DataProcessor
from core.excel_exporter import ExcelExporter
from core.models import ReportParams, Location

from .api_tab import ApiTab
from .locations_tab import LocationsTab
from .params_tab import ParamsTab


@dataclass
class MainWindowConfig:
    """Конфигурация для главного окна"""
    window_title: str = "Yandex.Metrika Analytics"
    window_geometry: tuple = (300, 300, 800, 600)  # x, y, width, height
    get_data_btn_text: str = "Получить данные"
    export_btn_text: str = "Экспорт в Excel"
    default_report_dir: Path = Path("temp/reports")
    default_report_name: str = "metrika_report_{timestamp}.xlsx"
    result_label_text: str = "Результаты будут отображены здесь"


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    report_generated = Signal()  # Отправляет сигнал при успешной генерации отчёта

    def __init__(self, config_manager, config: Optional[MainWindowConfig] = None):
        super().__init__()
        self.config_manager = config_manager
        self.ui_config = config or MainWindowConfig()
        self.results: Dict[str, Dict] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        """Инициализация компонентов пользовательского интерфейса"""
        self.setWindowTitle(self.ui_config.window_title)
        self.setGeometry(*self.ui_config.window_geometry)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Вкладки
        self.tabs = QTabWidget()
        self.locations_tab = LocationsTab(self.config_manager)
        self.params_tab = ParamsTab()
        self.api_tab = ApiTab(self.config_manager)

        self.tabs.addTab(self.locations_tab, "Локации")
        self.tabs.addTab(self.params_tab, "Параметры запроса")
        self.tabs.addTab(self.api_tab, "Настройки API")

        main_layout.addWidget(self.tabs)

        # Кнопки действий
        action_layout = QHBoxLayout()

        self.get_data_btn = QPushButton(self.ui_config.get_data_btn_text)
        self.get_data_btn.clicked.connect(self.get_metrika_data)
        action_layout.addWidget(self.get_data_btn)

        self.export_btn = QPushButton(self.ui_config.export_btn_text)
        self.export_btn.clicked.connect(self.export_to_excel)
        action_layout.addWidget(self.export_btn)

        main_layout.addLayout(action_layout)

        # Отображение результатов
        self.result_label = QLabel(self.ui_config.result_label_text)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_label.setWordWrap(True)
        main_layout.addWidget(self.result_label)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def get_metrika_data(self) -> None:
        """Извлекает данные из API Яндекс.Метрики"""
        oauth_token = self.api_tab.get_auth_code()
        if not oauth_token:
            self._show_error("API не настроен! Пожалуйста, настройте API на соответствующей вкладке.")
            self.tabs.setCurrentIndex(2)
            return

        locations = self.locations_tab.get_selected_locations()
        if not locations:
            self._show_error("Пожалуйста, выберите как минимум один регион или город!")
            return

        try:
            report_params = self.params_tab.get_report_params(locations)
        except ValueError as e:
            self._show_error(str(e))
            return

        try:
            api_client = MetrikaApiClient(oauth_token)
            raw_data = api_client.get_data(report_params)
            self._process_api_data(raw_data, locations)
            self._display_results(report_params)
            self._show_info("Данные успешно получены")
            self.report_generated.emit()
        except Exception as e:
            self._show_error(f"Не удалось получить данные: {str(e)}")

    def _process_api_data(self, raw_data: Dict, locations: List[Location]) -> None:
        """Обрабатывает данные ответа API."""
        self.results = {}
        for location_key, data in raw_data.items():
            location_obj = next(
                (loc for loc in locations
                if f"{loc.region} - {loc.name}" == location_key),
                None
            )
            if not location_obj:
                continue

            processed_data = DataProcessor.process_api_response(data, location_obj)
            self.results[location_key] = {
                'data': processed_data,
                'totals': DataProcessor.calculate_totals(processed_data)
            }

    def export_to_excel(self) -> None:
        """Экспорт отчёта в Excel."""
        if not self.results:
            self._show_error("Нет данных для экспорта. Пожалуйста, сперва получите данные.")
            return

        try:
            locations = self.locations_tab.get_selected_locations()
            report_params = self.params_tab.get_report_params(locations)
        except ValueError as e:
            self._show_error(str(e))
            return

        filters = []
        if report_params.behavior == "human":
            filters.append("robots = 'no'")
        elif report_params.behavior == "robot":
            filters.append("robots = 'yes'")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранение отчёта",
            str(self.ui_config.default_report_dir /
                self.ui_config.default_report_name.format(
                    timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
                )),
            "Excel Files (*.xlsx)",
        )

        if not file_path:
            return

        try:
            exporter = ExcelExporter()
            exporter.export_report(
                data={loc: res['data'] for loc, res in self.results.items()},
                file_path=Path(file_path),
                date_from=report_params.date_from.strftime("%Y-%m-%d"),
                date_to=report_params.date_to.strftime("%Y-%m-%d"),
                filters=" AND ".join(filters) if filters else "",
            )
            self._show_info(f"Отчет сохранён в {file_path}")
        except Exception as e:
            self._show_error(f"Не удалось экспортировать: {str(e)}")

    def _display_results(self, params: ReportParams) -> None:
        """Отображает результат отчёта в пользовательском интерфейсе"""
        result_text = f"Данные за период с {params.date_from} по {params.date_to}:\n\n"

        for location, data in self.results.items():
            result_text += f"--- {location} ---\n"
            result_text += f"Всего: {data['totals']['all']['visits']} посещений\n"

            if data['totals']['sources']:
                result_text += "\nПо источникам трафика:\n"
                for source, stats in data['totals']['sources'].items():
                    percentage = (stats['visits'] / data['totals']['all']['visits'] * 100
                                  if data['totals']['all']['visits'] > 0 else 0)
                    result_text += (f"- {source}: {stats['visits']} посещений "
                                    f"({percentage:.2f}%)\n")

            if data['data']:
                result_text += "\nПримерные данные:\n"
                for row in data['data'][:5]:
                    result_text += (f"{row.date.strftime('%Y-%m-%d')} "
                                    f"[{row.traffic_source}]: {row.visits} посещений\n")
            else:
                result_text += "Нет данных\n"

            result_text += "\n"

        self.result_label.setText(result_text)

    def _show_error(self, message: str) -> None:
        """Показывает сообщение об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)

    def _show_info(self, message: str) -> None:
        """Показывает информационное сообщение"""
        QMessageBox.information(self, "Информация", message)
