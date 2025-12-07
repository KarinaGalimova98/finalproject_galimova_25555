from __future__ import annotations

from pathlib import Path
from typing import Dict

# Директория с данными
DATA_DIR = Path("data")

# Пути к JSON-файлам
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"

# Минимальная длина пароля
MIN_PASSWORD_LENGTH = 4

# Базовая валюта по умолчанию
DEFAULT_BASE_CURRENCY = "USD"

# Фиктивные курсы валют к USD (сколько USD за 1 единицу валюты)
RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.1,
    "BTC": 60_000.0,
    "ETH": 3_000.0,
}

# Настройки кошелька
DEFAULT_WALLET_BALANCE = 0.0
MIN_TRANSACTION_AMOUNT = 0.0

# Пользователи
FIRST_USER_ID = 1
SALT_LENGTH = 8

# Кэш курсов
RATE_FRESHNESS_SECONDS = 300  # 5 минут
RATES_SOURCE_NAME = "ParserServiceStub"
