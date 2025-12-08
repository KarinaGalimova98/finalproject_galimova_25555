from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..infra.settings import SettingsLoader


COINGECKO_SOURCE_NAME = "CoinGecko"
EXCHANGERATE_SOURCE_NAME = "ExchangeRate-API"


@dataclass(frozen=True)
class ParserConfig:
    """Конфигурация Parser Service.

    Все изменяемые параметры собраны здесь, без хардкода в логике.
    """

    # Ключ для ExchangeRate-API берём из переменной окружения
    EXCHANGERATE_API_KEY: str

    # Эндпоинты
    COINGECKO_URL: str
    EXCHANGERATE_API_URL: str

    # Списки валют
    BASE_CURRENCY: str
    FIAT_CURRENCIES: tuple[str, ...]
    CRYPTO_CURRENCIES: tuple[str, ...]
    CRYPTO_ID_MAP: dict[str, str]

    # Пути к файлам
    RATES_FILE_PATH: Path
    HISTORY_FILE_PATH: Path

    # Сетевые параметры
    REQUEST_TIMEOUT: int

    @classmethod
    def from_env(cls) -> "ParserConfig":
        settings = SettingsLoader()
        api_key = os.getenv("EXCHANGERATE_API_KEY", "")

        return cls(
            EXCHANGERATE_API_KEY=api_key,
            COINGECKO_URL="https://api.coingecko.com/api/v3/simple/price",
            EXCHANGERATE_API_URL="https://v6.exchangerate-api.com/v6",
            BASE_CURRENCY="USD",
            FIAT_CURRENCIES=("EUR", "GBP", "RUB"),
            CRYPTO_CURRENCIES=("BTC", "ETH", "SOL"),
            CRYPTO_ID_MAP={
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            },
            RATES_FILE_PATH=Path(settings.get("rates_file")),
            HISTORY_FILE_PATH=Path(settings.get("history_file")),
            REQUEST_TIMEOUT=10,
        )

