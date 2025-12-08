from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from .constants import (
    FIRST_USER_ID,
    RATES_SOURCE_NAME,
    RATES_TO_USD,
    SALT_LENGTH,
)
from .models import User, Portfolio
from .exceptions import ApiRequestError
from .currencies import get_currency
from ..infra.database import DatabaseManager
from ..infra.settings import SettingsLoader
import random
import string


db = DatabaseManager()
settings = SettingsLoader()


# ===== Пользователи =====


def load_users() -> List[User]:
    return db.load_users()


def save_users(users: List[User]) -> None:
    db.save_users(users)


def generate_user_id(users: List[User]) -> int:
    if not users:
        return FIRST_USER_ID
    return max(user.user_id for user in users) + 1


def generate_salt() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(SALT_LENGTH))


# ===== Портфели =====


def load_portfolio_for_user(user: User) -> Portfolio:
    raw_list: List[Dict[str, Any]] = db.load_portfolios_raw()
    for item in raw_list:
        if item.get("user_id") == user.user_id:
            return Portfolio.from_dict(user=user, data=item)

    portfolio = Portfolio(user=user)
    save_portfolio(portfolio)
    return portfolio


def save_portfolio(portfolio: Portfolio) -> None:
    raw_list: List[Dict[str, Any]] = db.load_portfolios_raw()
    updated = False
    for idx, item in enumerate(raw_list):
        if item.get("user_id") == portfolio.user_id:
            raw_list[idx] = portfolio.to_dict()
            updated = True
            break

    if not updated:
        raw_list.append(portfolio.to_dict())

    db.save_portfolios_raw(raw_list)


# ===== Курсы валют =====


def load_rates() -> Dict[str, Any]:
    return db.load_rates_raw()


def save_rates(data: Dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat()
    data["source"] = RATES_SOURCE_NAME
    data["last_refresh"] = now
    db.save_rates_raw(data)


def _is_rate_fresh(updated_at_str: str) -> bool:
    ttl = settings.get("rates_ttl_seconds")
    updated_at = datetime.fromisoformat(updated_at_str)
    age = datetime.utcnow() - updated_at
    return age <= timedelta(seconds=ttl)


def get_rate(from_currency: str, to_currency: str) -> Tuple[float, datetime]:
    """Получить курс from -> to с учётом TTL и кэша.

    Валидация кодов делается через get_currency().
    Если курса нет и невозможно вычислить — ApiRequestError.
    """
    from_code = get_currency(from_currency).code
    to_code = get_currency(to_currency).code

    if from_code == to_code:
        now = datetime.utcnow()
        return 1.0, now

    rates_data = load_rates()
    pair_key = f"{from_code}_{to_code}"

    pair_info = rates_data.get(pair_key)
    if pair_info is not None:
        updated_at_str = pair_info.get("updated_at")
        if isinstance(updated_at_str, str) and _is_rate_fresh(updated_at_str):
            return float(pair_info["rate"]), datetime.fromisoformat(updated_at_str)

    # Пытаемся вычислить курс через RATES_TO_USD как заглушку ParserService
    if from_code not in RATES_TO_USD or to_code not in RATES_TO_USD:
        raise ApiRequestError(f"Курс {from_code}->{to_code} недоступен.")

    usd_from = RATES_TO_USD[from_code]
    usd_to = RATES_TO_USD[to_code]

    rate = usd_from / usd_to
    now = datetime.utcnow()

    rates_data[pair_key] = {"rate": rate, "updated_at": now.isoformat()}
    save_rates(rates_data)

    return rate, now
