import logging

from typing import Dict, List, Any
from pathlib import Path
from openpyxl.styles import Font, Alignment
from openpyxl.workbook import Workbook

from .data_processor import DataProcessor
from .models import ReportData
from .exceptions import ExcelExportError
from .excel_traffic_processor import ExcelTrafficProcessor

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Exports report data to Excel format."""

    HEADER_FONT = Font(bold=True)
    CENTER_ALIGNMENT = Alignment(horizontal='center')
    SHEET_NAME_MAX_LENGTH = 31

    TRAFFIC_HEADERS = {
        'organic': "Поисковые",
        'direct': "Прямые",
        'ad': "Реклама",
        'internal': "Внутренние",
        'referral': "Ссылки",
        'recommendation': "Рекомендации",
        'social': "Соцсети"
    }

    def export_report(
            self,
            data: Dict[str, List[ReportData]],
            file_path: Path,
            date_from: str,
            date_to: str,
            filters: str = ""
    ) -> None:
        """Export report data to Excel file.

        Args:
            data: Dictionary with location names as keys and report data as values
            file_path: Path to save Excel file
            date_from: Start date of report period
            date_to: End date of report period
            filters: Applied filters description

        Raises:
            ExcelExportError: If export fails
        """
        # Убедимся что папка temp существует
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)

        # Создаем временный файл для обработки
        temp_file_path = temp_dir / f"temp_{file_path.name}"

        try:
            wb = Workbook()
            wb.remove(wb.active)

            self._create_summary_sheet(wb, data, date_from, date_to, filters)

            for location, report_data in data.items():
                self._create_city_sheet(wb, location, report_data, date_from, date_to, filters)

            wb.save(temp_file_path)
            logger.info("Initial report successfully exported to %s", temp_file_path)

            # Обрабатываем данные трафика с помощью ExcelTrafficProcessor
            traffic_processor = ExcelTrafficProcessor(
                excel_file_path=str(temp_file_path),
            )
            traffic_processor.process(output_path=str(file_path))

            # Удаляем временный файл
            temp_file_path.unlink()
            logger.info("Temporary file %s removed", temp_file_path)

        except Exception as e:
            logger.error("Error during report export: %s", str(e))
            raise ExcelExportError(f"Failed to export report: {str(e)}")

    def _create_summary_sheet(
            self,
            wb: Workbook,
            data: Dict[str, List[ReportData]],
            date_from: str,
            date_to: str,
            filters: str
    ) -> None:
        """Create summary sheet in workbook."""
        ws = wb.create_sheet(title="Сводка")

        # Report header
        ws.append([f"Отчет за период с {date_from} по {date_to}"])
        ws.append(["Название отчета: Яндекс.Метрика - Аналитика по городам"])

        if filters:
            ws.append([f"Фильтры: {filters}"])

        ws.append([])

        # Table headers
        headers = [
            "Регион", "Город", "Визиты", "Посетители", "Просмотры",
            "Глубина просмотра"
        ]
        headers.extend(self.TRAFFIC_HEADERS.values())

        ws.append(headers)

        # Apply styles to headers
        header_row = ws.max_row
        for cell in ws[header_row]:
            cell.font = self.HEADER_FONT
            cell.alignment = self.CENTER_ALIGNMENT

        # Add data rows
        for location, report_data in data.items():
            region, city = location.split(" - ")
            totals = DataProcessor.calculate_totals(report_data)

            row_data = [
                region,
                city,
                totals['all']['visits'],
                totals['all']['users'],
                totals['all']['pageviews'],
                totals['all']['pageviews'] / totals['all']['visits'] if totals['all']['visits'] > 0 else 0
            ]

            # Add traffic source data from calculated totals
            row_data.extend(
                totals['sources'].get(source_key, {}).get('visits', 0)
                for source_key in self.TRAFFIC_HEADERS.keys()
            )

            ws.append(row_data)

    def _create_city_sheet(
            self,
            wb: Workbook,
            location: str,
            report_data: List[ReportData],
            date_from: str,
            date_to: str,
            filters: str
    ) -> None:
        """Create sheet for specific city."""
        _, city = location.split(" - ")
        ws = wb.create_sheet(title=city[:self.SHEET_NAME_MAX_LENGTH])

        # Report header
        ws.append([f"Отчет за период с {date_from} по {date_to}"])
        ws.append([f"Название отчета: Яндекс.Метрика - {city}"])

        if filters:
            ws.append([f"Фильтры: {filters} и Город = '{city}'"])

        ws.append([])

        # Table headers
        headers = ["Дата", "Источник трафика", "Визиты", "Посетители", "Глубина просмотра"]
        ws.append(headers)

        # Apply styles to headers
        for cell in ws[6]:
            cell.font = self.HEADER_FONT
            cell.alignment = self.CENTER_ALIGNMENT

        # Add data rows
        for item in report_data:
            source_name = self.TRAFFIC_HEADERS.get(item.traffic_source, item.traffic_source or "Другие")
            ws.append([
                item.date.strftime("%Y-%m-%d"),
                source_name,
                item.visits,
                item.users,
                item.pageviews / item.visits if item.visits > 0 else 0
            ])

    @staticmethod
    def _calculate_totals(data: List[ReportData]) -> Dict[str, Any]:
        """Calculate totals for report data."""
        totals = {
            'all': {'visits': 0, 'users': 0, 'pageviews': 0},
            'sources': {
                'organic': {'visits': 0, 'users': 0, 'pageviews': 0},
                'direct': {'visits': 0, 'users': 0, 'pageviews': 0},
                'ad': {'visits': 0, 'users': 0, 'pageviews': 0},
                'internal': {'visits': 0, 'users': 0, 'pageviews': 0},
                'referral': {'visits': 0, 'users': 0, 'pageviews': 0},
                'social': {'visits': 0, 'users': 0, 'pageviews': 0}
            }
        }

        SOURCE_MAPPING = {
            'organic': 'organic',
            'direct': 'direct',
            'ad': 'ad',
            'internal': 'internal',
            'referral': 'referral',
            'recommendation': 'recommendation',
            'social': 'social'
        }

        for item in data:
            # Update overall totals
            totals['all']['visits'] += item.visits
            totals['all']['users'] += item.users
            totals['all']['pageviews'] += item.pageviews

            # Update source-specific totals
            source = getattr(item, 'traffic_source', None)
            if source in SOURCE_MAPPING:
                mapped_source = SOURCE_MAPPING[source]

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
