from __future__ import annotations
from .exceptions import InsufficientFundsError

import hashlib
from datetime import datetime
from typing import Dict, Optional

from .constants import (
    DEFAULT_BASE_CURRENCY,
    DEFAULT_WALLET_BALANCE,
    MIN_PASSWORD_LENGTH,
    MIN_TRANSACTION_AMOUNT,
    RATES_TO_USD,
)
# User, Wallet, Portfolio


class User:
    """Пользователь системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        self._user_id = user_id
        self.username = username  # через setter
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    # ---- Внутренний метод для хеширования ----
    def _hash_password(self, password: str) -> str:
        """Возвращает hex-строку sha256(password + salt)."""
        data = (password + self._salt).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    # ---- Методы по заданию ----
    def get_user_info(self) -> dict:
        """Информация о пользователе без пароля."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """Изменить пароль с хешированием."""
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов."
            )

        self._hashed_password = self._hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        """Проверяет, совпадает ли пароль с сохранённым хешем."""
        return self._hash_password(password) == self._hashed_password

    # ---- Свойства (геттеры / сеттеры) ----
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    # ---- Для сохранения в JSON ----
    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"]),
        )


class Wallet:
    """Кошелёк для одной валюты."""

    def __init__(
        self,
        currency_code: str,
        balance: float = DEFAULT_WALLET_BALANCE,
    ) -> None:
        self.currency_code = currency_code.upper()
        self.balance = balance  # через setter

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом.")
        if amount <= MIN_TRANSACTION_AMOUNT:
            raise ValueError("Сумма пополнения должна быть положительной.")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        """Снятие средств."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом.")
        if amount <= MIN_TRANSACTION_AMOUNT:
            raise ValueError("Сумма снятия должна быть положительной.")
        if amount > self._balance:
            raise InsufficientFundsError(
                available=self._balance,
                required=amount,
                code=self.currency_code,
            )
        self._balance -= float(amount)

    def get_balance_info(self) -> dict:
        """Информация о балансе."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    # ---- Свойство balance ----
    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < DEFAULT_WALLET_BALANCE:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    # ---- Для JSON ----
    def to_dict(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        return cls(
            currency_code=data["currency_code"],
            balance=data.get("balance", DEFAULT_WALLET_BALANCE),
        )


class Portfolio:
    """Портфель одного пользователя (набор кошельков)."""

    def __init__(
        self,
        user: User,
        wallets: Optional[Dict[str, Wallet]] = None,
    ) -> None:
        self._user = user
        self._user_id = user.user_id
        self._wallets: Dict[str, Wallet] = wallets or {}

    def add_currency(self, currency_code: str) -> Wallet:
        """Добавляет новый кошелёк, если его ещё нет."""
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Валютный кошелёк {code} уже существует.")
        wallet = Wallet(currency_code=code)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        code = currency_code.upper()
        if code not in self._wallets:
            raise KeyError(f"Кошелёк {code} не найден.")
        return self._wallets[code]

    def get_total_value(self, base_currency: str = DEFAULT_BASE_CURRENCY) -> float:
        """Общая стоимость портфеля в base_currency.

        Для простоты используем фиксированные курсы из констант.
        """
        base_currency = base_currency.upper()

        rates_to_usd = RATES_TO_USD

        if base_currency not in rates_to_usd:
            raise ValueError(f"Неизвестная базовая валюта: {base_currency}")

        total_usd = 0.0
        for code, wallet in self._wallets.items():
            if code not in rates_to_usd:
                # неизвестная валюта — пропускаем
                continue
            rate = rates_to_usd[code]
            total_usd += wallet.balance * rate

        if base_currency == "USD":
            return total_usd

        return total_usd / rates_to_usd[base_currency]

    # ---- Свойства ----
    @property
    def user(self) -> User:
        """Объект пользователя (без сеттера)."""
        return self._user

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Копия словаря кошельков."""
        return dict(self._wallets)

    # ---- Для JSON ----
    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "wallets": {
                code: {"balance": wallet.balance}
                for code, wallet in self._wallets.items()
            },
        }

    @classmethod
    def from_dict(cls, user: User, data: dict) -> "Portfolio":
        wallets_dict: Dict[str, Wallet] = {}
        raw_wallets = data.get("wallets", {})
        for code, w_data in raw_wallets.items():
            wallets_dict[code] = Wallet(
                currency_code=code,
                balance=w_data.get("balance", DEFAULT_WALLET_BALANCE),
            )
        return cls(user=user, wallets=wallets_dict)
