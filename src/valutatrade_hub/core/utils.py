from __future__ import annotations

import json
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

from .constants import (
    DATA_DIR,
    FIRST_USER_ID,
    PORTFOLIOS_FILE,
    RATE_FRESHNESS_SECONDS,
    RATES_FILE,
    RATES_SOURCE_NAME,
    RATES_TO_USD,
    SALT_LENGTH,
    USERS_FILE,
)
from .models import User, Portfolio


# ===== Общие JSON-утилиты =====


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path, default: Any) -> Any:
    _ensure_data_dir()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path, data: Any) -> None:
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===== Пользователи =====


def load_users() -> List[User]:
    raw = _load_json(USERS_FILE, [])
    return [User.from_dict(item) for item in raw]


def save_users(users: List[User]) -> None:
    data = [user.to_dict() for user in users]
    _save_json(USERS_FILE, data)


def generate_user_id(users: List[User]) -> int:
    if not users:
        return FIRST_USER_ID
    return max(user.user_id for user in users) + 1


def generate_salt() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(SALT_LENGTH))


# ===== Портфели =====


def load_portfolio_for_user(user: User) -> Portfolio:
    raw_list = _load_json(PORTFOLIOS_FILE, [])
    for item in raw_list:
        if item.get("user_id") == user.user_id:
            return Portfolio.from_dict(user=user, data=item)

    # если портфеля нет — создаём пустой
    portfolio = Portfolio(user=user)
    save_portfolio(portfolio)
    return portfolio


def save_portfolio(portfolio: Portfolio) -> None:
    raw_list = _load_json(PORTFOLIOS_FILE, [])

    updated = False
    for idx, item in enumerate(raw_list):
        if item.get("user_id") == portfolio.user_id:
            raw_list[idx] = portfolio.to_dict()
            updated = True
            break

    if not updated:
        raw_list.append(portfolio.to_dict())

    _save_json(PORTFOLIOS_FILE, raw_list)


# ===== Курсы валют =====


def load_rates() -> Dict[str, Any]:
    return _load_json(RATES_FILE, {})


def save_rates(data: Dict[str, Any]) -> None:
    # обновляем метаинформацию
    now = datetime.utcnow().isoformat()
    data["source"] = RATES_SOURCE_NAME
    data["last_refresh"] = now
    _save_json(RATES_FILE, data)


def get_rate(from_currency: str, to_currency: str) -> Tuple[float, datetime]:
    """Получить курс from -> to.

    1) Проверяем кеш в rates.json.
    2) Если нет или устарел — используем фиктивные курсы RATES_TO_USD,
       пересчитываем и обновляем кеш.
    """
    from_code = from_currency.upper()
    to_code = to_currency.upper()

    if from_code == to_code:
        now = datetime.utcnow()
        return 1.0, now

    rates_data = load_rates()
    pair_key = f"{from_code}_{to_code}"

    # проверка свежести
    pair_info = rates_data.get(pair_key)
    if pair_info is not None:
        updated_at_str = pair_info.get("updated_at")
        if updated_at_str is not None:
            updated_at = datetime.fromisoformat(updated_at_str)
            age = datetime.utcnow() - updated_at
            if age <= timedelta(seconds=RATE_FRESHNESS_SECONDS):
                return float(pair_info["rate"]), updated_at

    # если в кеше нет или устарел — пересчитываем из RATES_TO_USD
    if from_code not in RATES_TO_USD or to_code not in RATES_TO_USD:
        raise ValueError(f"Курс {from_code}->{to_code} недоступен.")

    usd_from = RATES_TO_USD[from_code]
    usd_to = RATES_TO_USD[to_code]

    # сколько to за 1 from
    rate = usd_from / usd_to
    now = datetime.utcnow()

    rates_data[pair_key] = {
        "rate": rate,
        "updated_at": now.isoformat(),
    }

    save_rates(rates_data)
    return rate, now
