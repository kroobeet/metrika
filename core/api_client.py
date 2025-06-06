import json
import logging
from typing import Dict, Any
import requests

from .models import ReportParams, Location
from .exceptions import MetrikaApiError

logger = logging.getLogger(__name__)


class MetrikaApiClient:
    """Client for interacting with Yandex Metrika API."""

    BASE_URL = "https://api-metrika.yandex.net/stat/v1/data"
    TIMEOUT = 30

    def __init__(self, oauth_token: str):
        """Initialize the client. with OAuth token.

        Args:
            oauth_token: Yandex Metrika OAuth token for API authentication.
        """
        self.oauth_token = oauth_token

    def get_data(self, params: ReportParams) -> Dict[str, Any]:
        """Fetch data from Yandex Metrika API for given parameters.

        Args:
            params: Report parameters including data range, filters etc.

        Returns:
            Dictionary with location names as keys and API responses as values.

        Raises:
            MetrikaApiError: If there's an error during API request.
        """
        results = {}

        for location in params.locations:
            if not location.selected:
                continue

            try:
                response = self._make_api_request(params, location)
                results[f"{location.region} - {location.name}"] = response.json()
            except requests.exceptions.RequestException as e:
                error_msg = f"Request error for {location.name}: {str(e)}"
                logger.error(error_msg)
                raise MetrikaApiError(error_msg) from e

        return results

    def _make_api_request(self, params: ReportParams, location: Location) -> requests.Response:
        """Make an API request for specific location.

        Args:
            params: Report parameters
            location: Location to request data for

        Returns:
            API response

        Raises:
            requests.exceptions.RequestException: If request fails.
        """
        request_params = self._build_request_params(params, location)
        headers = {
            "Authorization": f"OAuth {self.oauth_token}",
            "Content-Type": "application/x-yametrika+json",
        }

        logger.info(
            "Request for location %s:\nURL:%s\nParams:%s",
            location.name,
            self.BASE_URL,
            json.dumps(request_params, indent=2, ensure_ascii=False),
        )

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=request_params,
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()

        logger.info(
            "Response for %s:\nStatus: %s\nData: %s",
            location.name,
            response.status_code,
            json.dumps(response.json(), indent=2, ensure_ascii=False),
        )

        return response

    @staticmethod
    def _build_request_params(params: ReportParams, location: Location) -> Dict[str, Any]:
        """Build request parameters for API call.

        Args:
            params: Report parameters
            location: Location to build parameters for

        Returns:
            Dictionary of request parameters
        """
        GROUP_MAP = {
            "По дням": "ym:s:date"
        }

        TRAFFIC_MAPPING = {
            "search": "organic",
            "direct": "direct",
            "ad": "ad",
            "internal": "internal",
            "referral": "referral",
            "recommendation": "recommendation",
            "social": "social",
        }

        request_params = {
            "ids": params.counter_id,
            "date1": params.date_from.strftime("%Y-%m-%d"),
            "date2": params.date_to.strftime("%Y-%m-%d"),
            "metrics": "ym:s:visits,ym:s:users,ym:s:pageviews",
            "lang": "ru",
            "limit": 10000,
            "accuracy": "full",
            "dimensions": GROUP_MAP.get(params.grouping, "ym:s:date")
        }
        # Если нужен источник трафика, добавьте его в dimensions
        if params.grouping == "По дням":
            request_params["dimensions"] += ",ym:s:trafficSource"  # Добавляем источник трафика

        # Filters
        filters = []

        city_filter = f"ym:s:regionCityName=='{location.name}'"
        filters.append(city_filter)

        # Traffic sources filters (only for daily grouping)
        selected_sources = [k for k, v in params.traffic_sources.items() if v]
        if selected_sources:
            sources_filter = [
                f"ym:s:trafficSource=='{TRAFFIC_MAPPING[src]}'"
                for src in selected_sources
            ]
            filters.append(f"({' OR '.join(sources_filter)})")


        # Traffic type filter (works for all groupings)
        if params.behavior == "human":
            filters.append("ym:s:isRobot=='No'")
        elif params.behavior == "robot":
            filters.append("ym:s:isRobot=='Yes'")

        if filters:
            request_params["filters"] = " AND ".join(filters)

        return request_params
