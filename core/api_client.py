import requests
import json
import logging
from typing import Dict, Any
from .models import ReportParams, Location

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetrikaApiClient:
    def __init__(self, oauth_token: str):
        self.oauth_token = oauth_token
        self.base_url = "https://api-metrika.yandex.net/stat/v1/data"

    def get_data(self, params: ReportParams) -> Dict[str, Any]:
        """Получение данных из API Яндекс.Метрики"""
        results = {}

        for location in params.locations:
            if not location.selected:
                continue

            request_params = self._build_request_params(params, location)

            # Логируем параметры запроса
            logger.info(f"Запрос для локации {location.name}:")
            logger.info(f"URL: {self.base_url}")
            logger.info(f"Параметры: {json.dumps(request_params, indent=2, ensure_ascii=False)}")

            headers = {
                "Authorization": f"OAuth {self.oauth_token}",
                "Content-Type": "application/x-yametrika+json"
            }

            try:
                response = requests.get(
                    self.base_url,
                    headers=headers,
                    params=request_params,
                    timeout=30
                )
                response.raise_for_status()

                # Логируем ответ
                logger.info(f"Ответ для {location.name}:")
                logger.info(f"Статус: {response.status_code}")
                logger.info(f"Данные: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

                results[f"{location.region} - {location.name}"] = response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка запроса для {location.name}: {str(e)}")
                raise Exception(f"Ошибка при запросе для {location.name}: {str(e)}")

        return results

    @staticmethod
    def _build_request_params(params: ReportParams, location: Location) -> Dict[str, Any]:
        """Формирование параметров запроса"""
        group_map = {
            "По дням": "ym:s:date",
            "По неделям": "ym:s:week",
            "По месяцам": "ym:s:month"
        }

        traffic_mapping = {
            "search": "organic",
            "direct": "direct",
            "ad": "ad",
            "internal": "internal",
            "referral": "referral",
            "recommendation": "recommendation",
            "social": "social"
        }

        # Основные параметры с увеличенным лимитом
        request_params = {
            "ids": params.counter_id,
            "date1": params.date_from.strftime("%Y-%m-%d"),
            "date2": params.date_to.strftime("%Y-%m-%d"),
            "metrics": "ym:s:visits,ym:s:users,ym:s:pageviews",
            "dimensions": f"{group_map.get(params.grouping, 'ym:s:date')},ym:s:trafficSource",
            "lang": "ru",
            "limit": 10000,
            "accuracy": "full"
        }

        # Фильтры
        filters = [f"ym:s:regionCityName=='{location.name}'"]

        # Фильтры по источникам трафика
        selected_sources = [k for k, v in params.traffic_sources.items() if v]
        if selected_sources:
            sources_filter = [f"ym:s:trafficSource=='{traffic_mapping[src]}'" for src in selected_sources]
            filters.append(f"({' OR '.join(sources_filter)})")

        # Фильтр по типу трафика
        if params.behavior == "human":
            filters.append("ym:s:isRobot=='No'")
        elif params.behavior == "robot":
            filters.append("ym:s:isRobot=='Yes'")

        request_params["filters"] = " AND ".join(filters)

        return request_params