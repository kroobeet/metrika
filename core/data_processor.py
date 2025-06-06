from typing import Dict, List, Any
from datetime import datetime
import logging

from .models import ReportData, Location
from .exceptions import DataProcessingError


logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes raw API responses into structured data."""

    @staticmethod
    def process_api_response(data: Dict[str, Any], location: Location) -> List[ReportData]:
        """Process API response into list of ReportData objects.

        Args:
            data: Raw API response data
            location: Location associated with the data

        Returns:
            List of processed ReportData objects

        Raises:
            DataProcessingError: If data is invalid processing fails
        """
        processed_data = []

        if not data['data']:
            logger.warning("No data found in API response for %s", location.name)
            return processed_data

        for row in data['data']:
            try:
                date_str = row['dimensions'][0]['name']
                # Безопасное получение источника трафика (если есть)
                traffic_source = row['dimensions'][1]['name'] if len(row['dimensions']) > 1 else None
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                processed_data.append(ReportData(
                    location=location,
                    date=date_obj,
                    visits=row['metrics'][0],
                    users=row['metrics'][1],
                    pageviews=row['metrics'][2],
                    traffic_source=traffic_source
                ))
            except (KeyError, IndexError, ValueError) as e:
                error_msg = f"Skipping invalid data row: {str(e)}"
                logger.error(error_msg)
                raise DataProcessingError(error_msg) from e

        return processed_data

    @staticmethod
    def aggregate_traffic_data(raw_data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """Aggregate traffic data by city and source type.

        Args:
            raw_data: Raw API response data

        Returns:
            Dictionary with city names as keys and traffic source counts as values
        """

        def extract_city_name(full_name: str) -> str:
            """Extract city name from full region-city string"""
            parts = full_name.split(' - ')
            return parts[-1] if len(parts) > 1 else full_name

        traffic_data = {}

        # Initialize data structure for all cities
        for region_city in raw_data.keys():
            city = extract_city_name(region_city)
            traffic_data[city] = {
                "organic": 0,  # Поисковые системы
                "direct": 0,  # Прямые заходы
                "ad": 0,  # Реклама
                "internal": 0,  # Внутренние переходы
                "referral": 0,  # Ссылки
                "recommendation": 0,  # Рекомендации
                "social": 0  # Соцсети
            }

        # Process data for all cities
        for region_city, region_data in raw_data.items():
            city = extract_city_name(region_city)
            for item in region_data["data"]:
                if len(item["dimensions"]) > 1:  # Check if traffic source exists
                    traffic_type = item["dimensions"][1]["id"]
                    visits = item["metrics"][0]
                    if traffic_type in traffic_data[city]:
                        traffic_data[city][traffic_type] += visits

        return traffic_data

    @staticmethod
    def calculate_totals(data: List[ReportData]) -> Dict[str, Dict[str, int]]:
        """Calculate totals from processed data.

        Args:
            data: List of ReportData objects

        Returns:
            Dictionary with calculated totals for all data and by traffic source
        """
        totals = {
            'all': {'visits': 0, 'users': 0, 'pageviews': 0},
            'sources': {}
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
            try:
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
            except (KeyError, IndexError, ValueError) as e:
                error_msg = f"Failed to calculate totals: {str(e)}"
                logger.error(error_msg)
                raise DataProcessingError(error_msg) from e
        return totals
