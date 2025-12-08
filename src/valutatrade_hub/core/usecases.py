from __future__ import annotations
from .exceptions import InsufficientFundsError, CurrencyNotFoundError, ApiRequestError
from .currencies import get_currency
from ..decorators import log_action

from datetime import datetime
from typing import Dict, List

from .constants import (
    DEFAULT_BASE_CURRENCY,
    MIN_PASSWORD_LENGTH,
)
from .models import User, Portfolio

from .utils import (
    generate_salt,
    generate_user_id,
    get_rate,
    load_portfolio_for_user,
    load_users,
    save_portfolio,
    save_users,
)


# ===== Пользователи =====

@log_action("REGISTER", verbose=False)
def register_user(username: str, password: str) -> User:
    username = username.strip()
    if not username:
        raise ValueError("Имя пользователя не может быть пустым.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов."
        )

    users = load_users()
    for user in users:
        if user.username == username:
            raise ValueError(f"Имя пользователя '{username}' уже занято.")

    user_id = generate_user_id(users)
    salt = generate_salt()
    registration_date = datetime.utcnow()

    # временный пустой хеш — поменяем через change_password
    new_user = User(
        user_id=user_id,
        username=username,
        hashed_password="",
        salt=salt,
        registration_date=registration_date,
    )
    new_user.change_password(password)

    users.append(new_user)
    save_users(users)

    # создаём пустой портфель
    portfolio = Portfolio(user=new_user)
    save_portfolio(portfolio)

    return new_user

@log_action("LOGIN", verbose=False)
def login_user(username: str, password: str) -> User:
    username = username.strip()
    users = load_users()

    for user in users:
        if user.username == username:
            if user.verify_password(password):
                return user
            raise ValueError("Неверный пароль.")

    raise ValueError(f"Пользователь '{username}' не найден.")


# ===== Портфель =====


def get_portfolio_summary(
    user: User,
    base_currency: str = DEFAULT_BASE_CURRENCY,
) -> Dict:
    portfolio = load_portfolio_for_user(user)
    base = base_currency.upper()

    items: List[Dict] = []
    total_in_base = 0.0

    for code, wallet in portfolio.wallets.items():
        balance = wallet.balance
        if balance == 0:
            value_base = 0.0
        else:
            try:
                rate, _ = get_rate(code, base)
                value_base = balance * rate
            except ValueError:
                # если нет курса — считаем стоимость 0
                value_base = 0.0

        items.append(
            {
                "currency": code,
                "balance": balance,
                "value_in_base": value_base,
            }
        )
        total_in_base += value_base

    return {
        "username": user.username,
        "base_currency": base,
        "items": items,
        "total": total_in_base,
    }


# ===== Операции buy / sell =====

@log_action("BUY", verbose=True)
def buy_currency(
    user: User,
    currency_code: str,
    amount: float,
    base_currency: str = DEFAULT_BASE_CURRENCY,
) -> Dict:
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")
    get_currency(currency_code)
    portfolio = load_portfolio_for_user(user)
    code = currency_code.upper()

    try:
        wallet = portfolio.get_wallet(code)
        old_balance = wallet.balance
    except KeyError:
        wallet = portfolio.add_currency(code)
        old_balance = 0.0

    wallet.deposit(amount)
    new_balance = wallet.balance

    # оценочная стоимость покупки в базовой валюте
    rate, updated_at = get_rate(code, base_currency)
    estimated_value = amount * rate

    save_portfolio(portfolio)

    return {
        "currency": code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "rate": rate,
        "base_currency": base_currency.upper(),
        "estimated_value": estimated_value,
        "updated_at": updated_at,
    }

@log_action("SELL", verbose=True)
def sell_currency(
    user: User,
    currency_code: str,
    amount: float,
    base_currency: str = DEFAULT_BASE_CURRENCY,
) -> Dict:
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")
    get_currency(currency_code)
    portfolio = load_portfolio_for_user(user)
    code = currency_code.upper()

    try:
        wallet = portfolio.get_wallet(code)
    except KeyError as exc:
        raise ValueError(
            f"У вас нет кошелька '{code}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        ) from exc

    old_balance = wallet.balance

    if amount > old_balance:
        raise ValueError(
            f"Недостаточно средств: доступно {old_balance:.4f} {code}, "
            f"требуется {amount:.4f} {code}"
        )

    wallet.withdraw(amount)
    new_balance = wallet.balance

    rate, updated_at = get_rate(code, base_currency)
    estimated_revenue = amount * rate

    save_portfolio(portfolio)

    return {
        "currency": code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "rate": rate,
        "base_currency": base_currency.upper(),
        "estimated_revenue": estimated_revenue,
        "updated_at": updated_at,
    }


# ===== Курс валют =====


def get_rate_info(from_currency: str, to_currency: str) -> Dict:
    rate, updated_at = get_rate(from_currency, to_currency)
    reverse_rate, _ = get_rate(to_currency, from_currency)

    return {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "rate": rate,
        "reverse_rate": reverse_rate,
        "updated_at": updated_at,
    }

