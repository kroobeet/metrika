"""Клиент для взаимодействия с API Яндекс Метрики"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

import requests

from .models import ReportParams, Location
from .exceptions import MetrikaApiError


logger = logging.getLogger(__name__)


@dataclass
class ApiClientConfig:
    """Настройка для клиента Metrika API."""
    base_url: str = "https://api-metrika.yandex.net/stat/v1/data"
    timeout: int = 30


class MetrikaApiClient:
    """Управляет взаимодействием с API Яндекс Метрики."""

    TRAFFIC_MAPPING = {
        "search": "organic",
        "direct": "direct",
        "ad": "ad",
        "internal": "internal",
        "referral": "referral",
        "recommendation": "recommendation",
        "social": "social",
    }

    def __init__(self, oauth_token: str, config: Optional[ApiClientConfig] = None):
        """Инициализация с помощью токена OAuth и опциональной конфигурации."""
        self.oauth_token = oauth_token
        self.config = config or ApiClientConfig()

    def get_data(self, params: ReportParams) -> Dict[str, Any]:
        """Извлекает данные из API Яндекс Метрики.

        Args:
            params: Параметры отчета, включая диапазон дат, фильтры и т.д.

        Returns:
            Словарь с названиями местоположений в качестве ключей и ответами API в качестве значений.

        Raises:
            MetrikaApiError: Если запрос API завершится неудачей.
        """
        results = {}

        for location in filter(lambda loc: loc.selected, params.locations):
            try:
                response = self._make_api_request(params, location)
                results[f"{location.region} - {location.name}"] = response.json()
            except requests.RequestException as e:
                error_msg = f"Ошибка запроса для {location.name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise MetrikaApiError(error_msg) from e

        return results

    def _make_api_request(self, params: ReportParams, location: Location) -> requests.Response:
        """Выполнение запроса API для конкретного местоположения."""
        request_params = self._build_request_params(params, location)
        headers = {
            "Authorization": f"OAuth {self.oauth_token}",
            "Content-Type": "application/x-yametrika+json",
        }

        logger.debug(
            "API запрос для %s:\nПараметры: %s",
            location.name,
            json.dumps(request_params, indent=2, ensure_ascii=False),
        )

        try:
            response = requests.get(
                self.config.base_url,
                headers=headers,
                params=request_params,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error("API запрос не удался: %s", str(e), exc_info=True)
            raise

    def _build_request_params(self, params: ReportParams, location: Location) -> Dict[str, Any]:
        """Построение параметров запроса для вызова API"""
        grouping_map = {"По дням": "ym:s:date"}
        dimensions = grouping_map.get(params.grouping, "ym:s:date")

        if params.grouping == "По дням":
            dimensions += ",ym:s:trafficSource"

        request_params = {
            "ids": params.counter_id,
            "date1": params.date_from.strftime("%Y-%m-%d"),
            "date2": params.date_to.strftime("%Y-%m-%d"),
            "metrics": "ym:s:visits,ym:s:users,ym:s:pageviews",
            "dimensions": dimensions,
            "lang": "ru",
            "limit": 10000,
            "accuracy": "full",
        }

        # Построение фильтров
        filters = [
            f"ym:s:regionCityName=='{location.name}'",
        ]

        # Добавление фильтров источников трафика
        selected_sources = [
            src for src, selected in params.traffic_sources.items() if selected
        ]
        if selected_sources:
            sources_filter = " OR ".join(
                f"ym:s:trafficSource=='{self.TRAFFIC_MAPPING[src]}'"
                for src in selected_sources
            )
            filters.append(f"({sources_filter})")

        # Добавляем фильтр поведения
        if params.behavior == "human":
            filters.append("ym:s:isRobot=='No'")
        elif params.behavior == "robot":
            filters.append("ym:s:isRobot=='Yes'")

        if filters:
            request_params["filters"] = " AND ".join(filters)

        return request_params
