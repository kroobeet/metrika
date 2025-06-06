import json
from openpyxl import load_workbook
from typing import Dict


class ExcelTrafficProcessor:
    """
    Класс для обработки и агрегации данных о трафике из JSON и их записи в Excel файл.

    Атрибуты:
        ``json_path`` (str): Путь к JSON файлу с данными о трафике.\n
        ``excel_file_path`` (str): Путь к Excel файлу для обновления.\n
        ``sheet_name`` (str): Название листа в Excel файле, который нужно обработать.\n
        ``city_column`` (str): Буква столбца, содержащего названия городов (например, 'B').\n
        ``traffic_columns`` (Dict[str, str]): Словарь, сопоставляющий типы трафика с буквами столбцов.\n
        ``traffic_data`` (Dict[str, Dict[str, int]]): Словарь для хранения агрегированных данных по городам.
    """

    def __init__(
        self,
        json_path: str = "temp/api_response.json",  # Измененный путь
        excel_file_path: str = "",
        sheet_name: str = "Сводка",
        city_column: str = "B",
        traffic_columns: Dict[str, str] = None,
    ):
        """
        Инициализирует экземпляр класса ExcelTrafficProcessor.

        Аргументы:
            ``json_path`` (str): Путь к JSON файлу с данными о трафике. По умолчанию '../api_response.json'.\n
            ``excel_file_path`` (str): Путь к Excel файлу для обновления. По умолчанию ''.\n
            ``sheet_name`` (str): Название листа в Excel файле. По умолчанию 'Сводка'.\n
            ``city_column`` (str): Буква столбца с названиями городов. По умолчанию 'B'.\n
            ``traffic_columns`` (Dict[str, str]): Сопоставление типов трафика и столбцов. Если None, используется стандартное.
        """
        self.json_path = json_path
        self.excel_file_path = excel_file_path
        self.sheet_name = sheet_name
        self.city_column = city_column

        # Стандартное сопоставление типов трафика и столбцов, если не предоставлено
        if traffic_columns is None:
            self.traffic_columns = {
                "organic": "G",  # Поисковые системы
                "direct": "H",   # Прямые заходы
                "ad": "I",       # Реклама
                "internal": "J",  # Внутренние переходы
                "referral": "K",  # Ссылки
                "recommendation": "L",  # Рекомендации
                "social": "M",    # Соцсети
            }
        else:
            self.traffic_columns = traffic_columns

        self.traffic_data: Dict[str, Dict[str, int]] = {}

    @staticmethod
    def extract_city_name(full_name: str) -> str:
        """
        Извлекает название города из полного имени региона.

        Аргументы:
            ``full_name`` (str): Полное имя региона, например, 'Регион - Город'.

        Возвращает:
            ``str``: Название города или исходную строку, если разделитель не найден.
        """
        parts = full_name.split(" - ")
        return parts[-1] if len(parts) > 1 else full_name

    def load_traffic_data(self) -> None:
        """
        Загружает данные из JSON файла и агрегирует их по городам и типам трафика.
        """
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Инициализация структуры данных для всех городов
        for region_city in data.keys():
            city = self.extract_city_name(region_city)
            self.traffic_data[city] = {key: 0 for key in self.traffic_columns.keys()}

        # Агрегация данных по городам и типам трафика
        for region_city, region_data in data.items():
            city = self.extract_city_name(region_city)
            for item in region_data["data"]:
                traffic_type = item["dimensions"][1]["id"]
                visits = item["metrics"][0]
                if traffic_type in self.traffic_data[city]:
                    self.traffic_data[city][traffic_type] += visits

    def update_excel(self, output_path: str = "metrika_report.xlsx") -> None:
        """
        Обновляет Excel файл данными о трафике и сохраняет его.

        Аргументы:
            ``output_path`` (str): Путь для сохранения обновленного файла. По умолчанию 'metrika_report.xlsx'.
        """
        wb = load_workbook(self.excel_file_path)
        sheet = wb[self.sheet_name]

        for row in range(1, sheet.max_row + 1):
            city = sheet[f"{self.city_column}{row}"].value
            if city in self.traffic_data:
                for traffic_type, column in self.traffic_columns.items():
                    sheet[f"{column}{row}"] = self.traffic_data[city][traffic_type]

        wb.save(output_path)
        print(f"Файл успешно обновлен и сохранен как {output_path}")

    def process(self, output_path: str = "metrika_report.xlsx") -> None:
        """
        Выполняет полный процесс обработки: загрузка данных, обновление Excel и сохранение.

        Аргументы:
            output_path (str): Путь для сохранения обновленного файла. По умолчанию 'metrika_report.xlsx'.
        """
        self.load_traffic_data()
        self.update_excel(output_path)
