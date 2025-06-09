"""Модуль для обработки необработанных ответов API в структурированные данные."""

import logging
from datetime import datetime
from typing import Dict, List, Any, TypedDict

from .models import ReportData, Location
from .exceptions import DataProcessingError


logger = logging.getLogger(__name__)


class TrafficSourceTotals(TypedDict):
    """Определение типа для итоговых значений источников трафика."""
    visits: int
    users: int
    pageviews: int


class TrafficTotals(TypedDict):
    """Определение типа для итоговых значений трафика"""
    all: TrafficSourceTotals
    sources: Dict[str, TrafficSourceTotals]


class DataProcessor:
    """Обрабатывает необработанные данные API в структурированные форматы"""

    SOURCE_MAPPING = {
        'organic': 'organic',
        'direct': 'direct',
        'ad': 'ad',
        'internal': 'internal',
        'referral': 'referral',
        'recommendation': 'recommendation',
        'social': 'social',
    }

    @staticmethod
    def process_api_response(data: Dict[str, Any], location: Location) -> List[ReportData]:
        """Преобразует ответ API в объекты ReportData.

        Args:
            data: Необработанный ответ API
            location: Связанная локация

        Returns:
            Список обрабатываемых объектов ReportData

        Raises:
            DataProcessingError: Если обработка данных завершится сбоем
        """
        if not data.get('data'):
            logger.warning("В API нет данных для %s", location.name)
            return []

        processed_data = []

        for row in data['data']:
            try:
                date_str = row['dimensions'][0]['name']
                traffic_source = (
                    row['dimensions'][1]['name']
                    if len(row['dimensions']) > 1
                    else None
                )

                processed_data.append(ReportData(
                    location=location,
                    date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                    visits=row['metrics'][0],
                    users=row['metrics'][1],
                    pageviews=row['metrics'][2],
                    traffic_source=traffic_source,
                ))
            except (KeyError, IndexError, ValueError) as e:
                logger.error("Invalid data row: %s", str(e), exc_info=True)
                raise DataProcessingError(f"Invalid data row: {str(e)}") from e

        return processed_data

    @staticmethod
    def aggregate_traffic_data(raw_data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """Агрегирует данные о трафике по городу и источнику трафика

        Args:
            raw_data: Необработанные данные ответа API

        Returns:
            Словарь с названиями городов и количеством источников трафика
        """
        def extract_city_name(full_name: str) -> str:
            """Извлекает название города из полной строки регион-город"""
            return full_name.split(' - ')[-1]

        traffic_data = {}

        # Инициализация структуры данных
        for region_city in raw_data:
            city = extract_city_name(region_city)
            traffic_data[city] = {
                "organic": 0,
                "direct": 0,
                "ad": 0,
                "internal": 0,
                "referral": 0,
                "recommendation": 0,
                "social": 0
            }

        # Обработка данных
        for region_city, region_data in raw_data.items():
            city = extract_city_name(region_city)
            for item in region_data["data"]:
                if len(item["dimensions"]) > 1:
                    traffic_type = item["dimensions"][1]['id']
                    visits = item["metrics"][0]
                    if traffic_type in traffic_data[city]:
                        traffic_data[city][traffic_type] += visits

        return traffic_data

    @classmethod
    def calculate_totals(cls, data: List[ReportData]) -> TrafficTotals:
        """Рассчитывает итоговые значения на основе обработанных данных.

        Args:
            data: Список объектов ReportData

        Returns:
            Словарь с рассчитанными итоговыми значениями
        """
        totals: TrafficTotals = {
            'all': {'visits': 0, 'users': 0, 'pageviews': 0},
            'sources': {}
        }

        for item in data:
            # Обновляем общие итоги
            totals['all']['visits'] += item.visits
            totals['all']['users'] += item.users
            totals['all']['pageviews'] += item.pageviews

            # Обновляем итоговые данные по конкретным источникам
            if item.traffic_source in cls.SOURCE_MAPPING:
                source = cls.SOURCE_MAPPING[item.traffic_source]

                if source not in totals['sources']:
                    totals['sources'][source] = {
                        'visits': 0,
                        'users': 0,
                        'pageviews': 0
                    }

                totals['sources'][source]['visits'] += item.visits
                totals['sources'][source]['users'] += item.users
                totals['sources'][source]['pageviews'] += item.pageviews

        return totals
