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
                traffic_source = row['dimensions'][1]['name']
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

        for item in data:
            try:
                source = getattr(item, 'traffic_source', 'other')

                # Update overall totals
                totals['all']['visits'] += item.visits
                totals['all']['users'] += item.users
                totals['all']['pageviews'] += item.pageviews

                # Update source-specific totals
                if source not in totals['sources']:
                    totals['sources'][source] = {
                        'visits': 0,
                        'users': 0,
                        'pageviews': 0
                    }

                totals['sources'][source]['visits'] += item.visits
                totals['sources'][source]['users'] += item.users
                totals['sources'][source]['pageviews'] += item.pageviews

            except (KeyError, IndexError, ValueError) as e:
                error_msg = f"Failed to calculate totals: {str(e)}"
                logger.error(error_msg)
                raise DataProcessingError(error_msg) from e

        return totals
