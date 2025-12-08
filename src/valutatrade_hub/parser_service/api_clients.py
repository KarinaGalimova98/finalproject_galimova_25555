from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict

import requests

from ..core.exceptions import ApiRequestError
from ..core.constants import RATES_TO_USD
from .config import ParserConfig, COINGECKO_SOURCE_NAME, EXCHANGERATE_SOURCE_NAME


class BaseApiClient(ABC):
    """Базовый клиент внешнего API."""

    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Имя источника (для логирования и meta)."""

    @abstractmethod
    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        """Получить курсы в стандартизованном виде.

        Возвращает словарь:
        {
            "BTC_USD": {
                "rate": 59337.21,
                "source": "...",
                "meta": {...},
            },
            ...
        }
        """
        raise NotImplementedError


class CoinGeckoClient(BaseApiClient):
    """Клиент CoinGecko для криптовалют."""

    @property
    def source_name(self) -> str:
        return COINGECKO_SOURCE_NAME

    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        ids: list[str] = []
        code_by_id: Dict[str, str] = {}

        for code in self.config.CRYPTO_CURRENCIES:
            coin_id = self.config.CRYPTO_ID_MAP.get(code)
            if coin_id:
                ids.append(coin_id)
                code_by_id[coin_id] = code

        if not ids:
            return {}

        params = {
            "ids": ",".join(ids),
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }

        start_ms = int(time.time() * 1000)
        try:
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(
                f"CoinGecko request failed: {exc}",
            ) from exc

        elapsed_ms = int(time.time() * 1000) - start_ms
        if response.status_code != 200:
            raise ApiRequestError(
                f"CoinGecko returned status {response.status_code}",
            )

        data = response.json()
        result: Dict[str, Dict[str, Any]] = {}
        etag = response.headers.get("ETag", "")
        base_key = self.config.BASE_CURRENCY.lower()

        for coin_id, payload in data.items():
            code = code_by_id.get(coin_id)
            if not code:
                continue
            if base_key not in payload:
                continue

            rate = float(payload[base_key])
            pair_key = f"{code}_{self.config.BASE_CURRENCY}"
            result[pair_key] = {
                "rate": rate,
                "source": self.source_name,
                "meta": {
                    "raw_id": coin_id,
                    "request_ms": elapsed_ms,
                    "status_code": response.status_code,
                    "etag": etag,
                    "used_fallback": False,
                },
            }

        return result


class ExchangeRateApiClient(BaseApiClient):
    """Клиент ExchangeRate-API для фиатных валют."""

    @property
    def source_name(self) -> str:
        return EXCHANGERATE_SOURCE_NAME

    def fetch_rates(self) -> Dict[str, Dict[str, Any]]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError(
                "Не задан ключ EXCHANGERATE_API_KEY в переменных окружения.",
            )

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )

        start_ms = int(time.time() * 1000)
        try:
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(
                f"ExchangeRate-API request failed: {exc}",
            ) from exc

        elapsed_ms = int(time.time() * 1000) - start_ms
        if response.status_code != 200:
            raise ApiRequestError(
                f"ExchangeRate-API returned status {response.status_code}",
            )

        data = response.json()
        if data.get("result") != "success":
            raise ApiRequestError(
                "ExchangeRate-API result is not success: "
                f"{data.get('result')}",
            )

        rates = data.get("rates", {})
        result: Dict[str, Dict[str, Any]] = {}
        etag = response.headers.get("ETag", "")

        for code in self.config.FIAT_CURRENCIES:
            if code == self.config.BASE_CURRENCY:
                continue

            value = rates.get(code)
            used_fallback = False

            # Если API не вернул курс — пытаемся взять заглушку из RATES_TO_USD
            if value is None:
                fallback = RATES_TO_USD.get(code)
                if fallback is None:
                    # ни в API, ни в заглушках — пропускаем
                    continue
                value = fallback
                used_fallback = True

            rate = float(value)
            pair_key = f"{code}_{self.config.BASE_CURRENCY}"
            result[pair_key] = {
                "rate": rate,
                "source": self.source_name,
                "meta": {
                    "raw_id": code,
                    "request_ms": elapsed_ms,
                    "status_code": response.status_code,
                    "etag": etag,
                    "used_fallback": used_fallback,
                },
            }

        return result
