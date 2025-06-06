from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget,
                               QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt

from core.api_client import MetrikaApiClient
from core.data_processor import DataProcessor
from core.excel_exporter import ExcelExporter
from core.models import ReportParams

from .api_tab import ApiTab
from .locations_tab import LocationsTab
from .params_tab import ParamsTab


class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setWindowTitle("Аналитика Яндекс.Метрики")
        self.setGeometry(300, 300, 800, 600)

        self._init_ui()

    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Табы для разных режимов
        self.tabs = QTabWidget()

        # Создаем вкладки
        self.locations_tab = LocationsTab(self.config_manager)
        self.params_tab = ParamsTab()
        self.api_tab = ApiTab(self.config_manager)

        # Добавляем вкладки
        self.tabs.addTab(self.locations_tab, "Выбор локаций")
        self.tabs.addTab(self.params_tab, "Параметры запроса")
        self.tabs.addTab(self.api_tab, "Подключение API")

        main_layout.addWidget(self.tabs)

        # Кнопки действий
        action_layout = QHBoxLayout()

        self.get_data_btn = QPushButton("Получить данные")
        self.get_data_btn.clicked.connect(self.get_metrika_data)
        action_layout.addWidget(self.get_data_btn)

        self.export_btn = QPushButton("Экспорт в Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        action_layout.addWidget(self.export_btn)

        main_layout.addLayout(action_layout)

        # Область для вывода результатов
        self.result_label = QLabel("Результаты будут отображены здесь")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_label.setWordWrap(True)
        main_layout.addWidget(self.result_label)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def get_metrika_data(self):
        """Получение данных из Яндекс.Метрики"""
        # Получаем OAuth токен из вкладки API
        oauth_token = self.api_tab.get_oauth_token()
        if not oauth_token:
            self._show_error("API токен не настроен! Пожалуйста, настройте API на соответствующей вкладке.")
            self.tabs.setCurrentIndex(2)
            return

        # Получаем выбранные локации
        locations = self.locations_tab.get_selected_locations()
        if not locations:
            self._show_error("Выберите хотя бы один регион или город!")
            return

        # Получаем параметры отчета
        report_params = self.params_tab.get_report_params(locations)
        if not report_params.counter_id:
            self._show_error("Введите ID счётчика!")
            return

        # Создаем клиент API и получаем данные
        try:
            api_client = MetrikaApiClient(oauth_token)
            raw_data = api_client.get_data(report_params)

            # Сохраняем raw_data для использования в экспорте
            self.raw_data = raw_data

            # Обрабатываем данные
            self.results = {}
            for location_key, data in raw_data.items():
                # Находим соответствующий объект Location
                location_obj = next((loc for loc in locations
                                     if f"{loc.region} - {loc.name}" == location_key), None)
                if not location_obj:
                    continue

                processed_data = DataProcessor.process_api_response(data, location_obj)
                self.results[location_key] = {
                    'data': processed_data,
                    'totals': DataProcessor.calculate_totals(processed_data)
                }

            # Создаем клиент API и получаем данные
            api_client = MetrikaApiClient(oauth_token)
            raw_data = api_client.get_data(report_params)

            # Логируем полученные данные
            import json
            print("Полученные данные из API:")
            print(json.dumps(raw_data, indent=2, ensure_ascii=False))

            with open('temp/api_response.json', 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)

            # Отображаем результаты
            self._display_results(report_params)
            self._show_info("Данные успешно получены!")

        except Exception as e:
            import traceback
            print(f"Ошибка при получении данных: {str(e)}")
            print(traceback.format_exc())
            self._show_error(f"Ошибка при получении данных: {str(e)}")

    def export_to_excel(self):
        """Экспорт результатов в Excel файл"""
        if not hasattr(self, "results") or not self.results:
            self._show_error("Сначала получите данные!")
            return

        # Получаем параметры отчета для дат и фильтров
        locations = self.locations_tab.get_selected_locations()
        report_params = self.params_tab.get_report_params(locations)

        # Формируем строку фильтров
        filters = []
        if report_params.behavior == "human":
            filters.append("Роботность = 'Люди'")
        elif report_params.behavior == "robot":
            filters.append("Роботность = 'Роботы'")
        filters_str = " и ".join(filters) if filters else ""

        # Запрашиваем путь для сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчет",
            f"temp/reports/metrika_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        # Экспортируем данные
        exporter = ExcelExporter()
        data_to_export = {
            loc: res['data'] for loc, res in self.results.items()
        }

        # Передаем raw_data в экспортер
        exporter.export_report(
            data=data_to_export,
            file_path=Path(file_path),
            date_from=report_params.date_from.strftime("%Y-%m-%d"),
            date_to=report_params.date_to.strftime("%Y-%m-%d"),
            filters=filters_str,
        )
        self._show_info(f"Отчет сохранен в {file_path}")

    def _display_results(self, params: ReportParams):
        """Отображение результатов в интерфейсе"""
        result_text = f"Данные за период с {params.date_from} по {params.date_to}: \n\n"

        for location, data in self.results.items():
            result_text += f"___ {location} ___\n"
            result_text += f"Всего: {data['totals']['all']['visits']} посещений\n"

            # Добавляем данные по источникам трафика
            if data['totals']['sources']:
                result_text += f"\n По источникам трафика:\n"
                for source, stats in data['totals']['sources'].items():
                    result_text += f"- {source}: {stats['visits']} посещений ({round(stats['visits']/data['totals']['all']['visits']*100, 1)}%)\n"

            # Показываем первые 5 записей
            if data['data']:
                result_text += f"\nПервые записи:\n"
                for row in data['data'][:5]:
                    result_text += (
                        f"{row.date.strftime('%Y-%m-%d')} [{row.traffic_source}]: "
                        f"{row.visits} посещений\n"
                    )
            else:
                result_text += "Нет данных\n"

            result_text += "\n"

        self.result_label.setText(result_text)

    def _show_error(self, message: str):
        """Показать сообщение об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)

    def _show_info(self, message: str):
        """Показать информационное сообщение"""
        QMessageBox.information(self, "Информация", message)