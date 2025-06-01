import openpyxl
from typing import Dict, List, Any
from pathlib import Path
from openpyxl.styles import Font, Alignment
from .models import ReportData


class ExcelExporter:
    def __init__(self):
        self._header_font = Font(bold=True)
        self._center_alignment = Alignment(horizontal='center')

    def export_report(self, data: Dict[str, List[ReportData]], file_path: Path,
                      date_from: str, date_to: str, filters: str = "") -> bool:
        """Экспорт отчета в Excel файл"""
        try:
            wb = openpyxl.Workbook()
            wb.remove(wb.active)

            # Создаем сводный лист
            self._create_summary_sheet(wb, data, date_from, date_to, filters)

            # Создаем листы для каждого города
            for location, report_data in data.items():
                self._create_city_sheet(wb, location, report_data, date_from, date_to, filters)

            # Сохраняем файл
            wb.save(file_path)
            return True
        except Exception as e:
            raise Exception(f"Ошибка при экспорте в Excel: {str(e)}")

    def _create_summary_sheet(self, wb, data, date_from, date_to, filters):
        """Создание сводного листа"""
        ws = wb.create_sheet(title="Сводка")

        # Заголовок отчета
        ws.append([f"Отчет за период с {date_from} по {date_to}"])
        ws.append(["Название отчета: Яндекс.Метрика - Аналитика по городам"])

        if filters:
            ws.append([f"Фильтры: {filters}"])

        ws.append(["Атрибуция: Последний значимый переход"])
        ws.append([])

        # Заголовок таблицы
        headers = [
            "Регион", "Город", "Визиты", "Посетители", "Просмотры",
            "Глубина просмотра"
        ]

        # Добавляем заголовки для всех возможных источников трафика
        traffic_headers = {
            'organic': "Поисковые",
            'direct': "Прямые",
            'ad': "Реклама",
            'internal': "Внутренние",
            'referral': "Ссылки",
            'recommendation': "Рекомендации",
            'social': "Соцсети"
        }

        # Добавляем заголовки источников
        for header in traffic_headers.values():
            headers.append(header)

        ws.append(headers)

        # Применяем стили к заголовкам
        for cell in ws[7]:
            cell.font = self._header_font
            cell.alignment = self._center_alignment

        # Данные
        for location, report_data in data.items():
            region, city = location.split(" - ")
            totals = self._calculate_totals(report_data)
            all_visits = totals['all']['visits']

            # Создаем строку с данными
            row_data = [
                region,
                city,
                totals['all']['visits'],
                totals['all']['users'],
                totals['all']['pageviews'],
                totals['all']['pageviews'] / totals['all']['visits'] if totals['all']['visits'] > 0 else 0
            ]

            # Добавляем данные по всем источникам трафика в том же порядке, что и заголовки
            for source_key in traffic_headers.keys():
                row_data.append(totals['sources'].get(source_key, {}).get('visits', 0))

            ws.append(row_data)

    def _create_city_sheet(self, wb, location, report_data, date_from, date_to, filters):
        """Создание листа для конкретного города"""
        _, city = location.split(" - ")
        ws = wb.create_sheet(title=city[:31])  # Ограничение длины названия листа

        # Заголовок отчета
        ws.append([f"Отчет за период с {date_from} по {date_to}"])
        ws.append([f"Название отчета: Яндекс.Метрика - {city}"])

        if filters:
            ws.append([f"Фильтры: {filters} и Город = '{city}'"])

        ws.append(["Атрибуция: Последний значимый переход"])  # Исправлено - добавлены квадратные скобки
        ws.append([])

        # Заголовки таблицы
        headers = [
            "Дата", "Визиты", "Посетители", "Глубина просмотра"
        ]
        ws.append(headers)

        # Применяем стили к заголовкам
        for cell in ws[6]:
            cell.font = self._header_font
            cell.alignment = self._center_alignment

        # Данные
        for item in report_data:
            ws.append([
                item.date.strftime("%Y-%m-%d"),
                item.visits,
                item.users,
                item.pageviews / item.visits if item.visits > 0 else 0
            ])

    @staticmethod
    def _calculate_totals(data: List[ReportData]) -> Dict[str, Any]:
        """Расчет итоговых значений для набора данных с разбивкой по источникам"""
        totals = {
            'all': {
                'visits': 0,
                'users': 0,
                'pageviews': 0
            },
            'sources': {}
        }

        # Маппинг для соответствия ключей
        source_mapping = {
            'search': 'organic',
            'direct': 'direct',
            'ad': 'ad',
            'internal': 'internal',
            'referral': 'referral',
            'recommendation': 'recommendation',
            'social': 'social'
        }

        for item in data:
            # Общие итоги
            totals['all']['visits'] += item.visits
            totals['all']['users'] += item.users
            totals['all']['pageviews'] += item.pageviews

            # Итоги по источникам трафика
            source = getattr(item, 'traffic_source', 'other')
            # Преобразуем источник согласно маппингу
            mapped_source = source_mapping.get(source, source)

            if mapped_source not in totals['sources']:
                totals['sources'][mapped_source] = {
                    'visits': 0,
                    'users': 0,
                    'pageviews': 0
                }

            totals['sources'][mapped_source]['visits'] += item.visits
            totals['sources'][mapped_source]['users'] += item.users
            totals['sources'][mapped_source]['pageviews'] += item.pageviews

        return totals