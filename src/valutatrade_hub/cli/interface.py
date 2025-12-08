from __future__ import annotations

import shlex
from typing import Dict, List, Optional

from prettytable import PrettyTable

from ..core.constants import DEFAULT_BASE_CURRENCY, CURRENCY_REGISTRY
from ..core.models import User
from ..core import usecases
from ..core.exceptions import (
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
)


def _parse_args(tokens: List[str]) -> Dict[str, str]:
    """Примитивный парсер флагов вида --key value."""
    args: Dict[str, str] = {}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--"):
            key = token[2:]
            value = ""
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                value = tokens[i + 1]
                i += 1
            args[key] = value
        i += 1
    return args


def _require_logged_in(current_user: Optional[User]) -> User:
    if current_user is None:
        raise RuntimeError("Сначала выполните login.")
    return current_user


def main() -> None:
    """Главная точка входа CLI."""
    print("ValutaTrade Hub CLI")
    print(
        "Доступные команды: register, login, show-portfolio, "
        "buy, sell, get-rate, exit"
    )

    current_user: Optional[User] = None

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not line:
            continue

        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            print(f"Ошибка парсинга команды: {exc}")
            continue

        command = tokens[0]
        args_tokens = tokens[1:]
        args = _parse_args(args_tokens)

        if command in {"exit", "quit"}:
            print("Выход.")
            break

        if command == "register":
            username = args.get("username")
            password = args.get("password")

            if not username or not password:
                print("Использование: register --username <имя> --password <пароль>")
                continue

            try:
                user = usecases.register_user(
                    username=username,
                    password=password,
                )
            except ValueError as exc:
                print(exc)
                continue

            print(
                f"Пользователь '{user.username}' зарегистрирован (id={user.user_id}). "
                f"Войдите: login --username {user.username} --password ****"
            )

        elif command == "login":
            username = args.get("username")
            password = args.get("password")

            if not username or not password:
                print("Использование: login --username <имя> --password <пароль>")
                continue

            try:
                user = usecases.login_user(username=username, password=password)
            except ValueError as exc:
                print(exc)
                continue

            current_user = user
            print(f"Вы вошли как '{user.username}'")

        elif command == "show-portfolio":
            try:
                user = _require_logged_in(current_user)
            except RuntimeError as exc:
                print(exc)
                continue

            base = args.get("base", DEFAULT_BASE_CURRENCY)

            try:
                summary = usecases.get_portfolio_summary(
                    user=user,
                    base_currency=base,
                )
            except ValueError as exc:
                print(exc)
                continue

            print(
                f"Портфель пользователя '{summary['username']}' "
                f"(база: {summary['base_currency']}):"
            )

            table = PrettyTable()
            table.field_names = [
                "Валюта",
                "Баланс",
                f"В {summary['base_currency']}",
            ]

            for item in summary["items"]:
                table.add_row(
                    [
                        item["currency"],
                        f"{item['balance']:.4f}",
                        f"{item['value_in_base']:.2f}",
                    ]
                )

            print(table)
            print("-" * 33)
            print(
                f"ИТОГО: {summary['total']:.2f} {summary['base_currency']}"
            )

        elif command == "buy":
            try:
                user = _require_logged_in(current_user)
            except RuntimeError as exc:
                print(exc)
                continue

            currency = args.get("currency")
            amount_str = args.get("amount")

            if not currency or not amount_str:
                print(
                    "Использование: buy --currency <код> --amount <количество>"
                )
                continue

            try:
                amount = float(amount_str)
            except ValueError:
                print("'amount' должен быть числом.")
                continue

            try:
                result = usecases.buy_currency(
                    user=user,
                    currency_code=currency,
                    amount=amount,
                )
            except CurrencyNotFoundError as exc:
                print(exc)
                print(
                    "Используйте команду get-rate для проверки доступных валют."
                )
                continue
            except ApiRequestError as exc:
                print(exc)
                print(
                    "Повторите попытку позже или проверьте подключение."
                )
                continue
            except ValueError as exc:
                print(exc)
                continue

            print(
                f"Покупка выполнена: {result['amount']:.4f} {result['currency']} "
                f"по курсу {result['rate']:.5f} {result['base_currency']}/"
                f"{result['currency']}"
            )
            print("Изменения в портфеле:")
            print(
                f"- {result['currency']}: было {result['old_balance']:.4f} "
                f"→ стало {result['new_balance']:.4f}"
            )
            print(
                "Оценочная стоимость покупки: "
                f"{result['estimated_value']:.2f} {result['base_currency']}"
            )

        elif command == "sell":
            try:
                user = _require_logged_in(current_user)
            except RuntimeError as exc:
                print(exc)
                continue

            currency = args.get("currency")
            amount_str = args.get("amount")

            if not currency or not amount_str:
                print(
                    "Использование: sell --currency <код> --amount <количество>"
                )
                continue

            try:
                amount = float(amount_str)
            except ValueError:
                print("'amount' должен быть числом.")
                continue

            try:
                result = usecases.sell_currency(
                    user=user,
                    currency_code=currency,
                    amount=amount,
                )
            except InsufficientFundsError as exc:
                print(exc)
                continue
            except CurrencyNotFoundError as exc:
                print(exc)
                print(
                    "Используйте команду get-rate для проверки доступных валют."
                )
                continue
            except ApiRequestError as exc:
                print(exc)
                print(
                    "Повторите попытку позже или проверьте подключение."
                )
                continue
            except ValueError as exc:
                print(exc)
                continue

            print(
                f"Продажа выполнена: {result['amount']:.4f} {result['currency']} "
                f"по курсу {result['rate']:.5f} {result['base_currency']}/"
                f"{result['currency']}"
            )
            print("Изменения в портфеле:")
            print(
                f"- {result['currency']}: было {result['old_balance']:.4f} "
                f"→ стало {result['new_balance']:.4f}"
            )
            print(
                "Оценочная выручка: "
                f"{result['estimated_revenue']:.2f} {result['base_currency']}"
            )

        elif command == "get-rate":
            from_currency = args.get("from")
            to_currency = args.get("to")

            if not from_currency or not to_currency:
                print(
                    "Использование: get-rate --from <валюта> --to <валюта>"
                )
                continue

            try:
                info = usecases.get_rate_info(
                    from_currency=from_currency,
                    to_currency=to_currency,
                )
            except CurrencyNotFoundError as exc:
                print(exc)
                print(
                    "Доступные коды:",
                    ", ".join(sorted(CURRENCY_REGISTRY.keys())),
                )
                continue
            except ApiRequestError as exc:
                print(exc)
                print(
                    "Повторите попытку позже или проверьте подключение."
                )
                continue

            updated_at = info["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"Курс {info['from']}→{info['to']}: {info['rate']:.8f} "
                f"(обновлено: {updated_at})"
            )
            print(
                "Обратный курс "
                f"{info['to']}→{info['from']}: {info['reverse_rate']:.8f}"
            )

        else:
            print(f"Неизвестная команда: {command}")
            print(
                "Команды: register, login, show-portfolio, "
                "buy, sell, get-rate, exit"
            )
