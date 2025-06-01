from typing import Dict, List, Any
from datetime import datetime
from .models import ReportData, Location


class DataProcessor:
    @staticmethod
    def process_api_response(data: Dict[str, Any], location: Location) -> List[ReportData]:
        """Обработка ответа от API Яндекс.Метрики"""
        processed_data = []

        if not data.get('data'):
            return processed_data

        for row in data['data']:
            try:
                date_str = row['dimensions'][0]['name']
                traffic_source = row['dimensions'][1]['name']
                date = datetime.strptime(date_str, '%Y-%m-%d').date()

                processed_data.append(ReportData(
                    location=location,
                    date=date,
                    visits=row['metrics'][0],
                    users=row['metrics'][1],
                    pageviews=row['metrics'][2],
                    traffic_source=traffic_source
                ))
            except (KeyError, IndexError, ValueError) as e:
                continue

        return processed_data

    @staticmethod
    def calculate_totals(data: List[ReportData]) -> Dict[str, Dict[str, int]]:
        """Расчет итоговых значений с разбивкой по источникам трафика"""
        totals = {
            'all': {'visits': 0, 'users': 0, 'pageviews': 0},
            'sources': {}
        }

        for item in data:
            source = getattr(item, 'traffic_source', 'other')

            # Общие итоги
            totals['all']['visits'] += item.visits
            totals['all']['users'] += item.users
            totals['all']['pageviews'] += item.pageviews

            # Итоги по источникам
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