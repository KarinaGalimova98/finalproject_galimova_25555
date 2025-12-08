from __future__ import annotations

from pathlib import Path
from typing import Dict, Literal, TypedDict


# ===== Пути =====

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# JSON-файлы
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"

# ===== Пользователи =====

MIN_PASSWORD_LENGTH = 4
FIRST_USER_ID = 1
SALT_LENGTH = 8

# ===== Валюты =====

DEFAULT_BASE_CURRENCY = "USD"

RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.1,
    "BTC": 60_000.0,
    "ETH": 3_000.0,
}

DEFAULT_WALLET_BALANCE = 0.0
MIN_TRANSACTION_AMOUNT = 0.0


class FiatCurrencyConfig(TypedDict):
    kind: Literal["fiat"]
    name: str
    issuing_country: str


class CryptoCurrencyConfig(TypedDict):
    kind: Literal["crypto"]
    name: str
    algorithm: str
    market_cap: float


CurrencyConfig = FiatCurrencyConfig | CryptoCurrencyConfig

# Реестр валют (данные для фабрики в currencies.py)
CURRENCY_REGISTRY: Dict[str, CurrencyConfig] = {
    "USD": {
        "kind": "fiat",
        "name": "US Dollar",
        "issuing_country": "United States",
    },
    "EUR": {
        "kind": "fiat",
        "name": "Euro",
        "issuing_country": "Eurozone",
    },
    "BTC": {
        "kind": "crypto",
        "name": "Bitcoin",
        "algorithm": "SHA-256",
        "market_cap": 1.12e12,
    },
    "ETH": {
        "kind": "crypto",
        "name": "Ethereum",
        "algorithm": "Ethash",
        "market_cap": 4.5e11,
    },
}

# ===== Кэш курсов =====

RATE_FRESHNESS_SECONDS = 300  # 5 минут
RATES_SOURCE_NAME = "ParserServiceStub"

# ===== Логирование =====

LOG_FILE = LOG_DIR / "actions.log"
LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 1_000_000  # ~1 МБ
LOG_BACKUP_COUNT = 3       # сколько файлов истории держать
LOG_FORMAT = (
    "%(levelname)s %(asctime)s %(message)s"
)  # формат можно описать в README
