# Final Project — Currency Wallet

Учебный консольный проект на Python, имитирующий работу валютного кошелька с поддержкой фиатных и криптовалют.

Проект состоит из двух слоёв:

- **Core Service** — управление пользователями, кошельками и портфелями, операции покупки/продажи, работа с локальным кешем курсов (`data/rates.json`).
- **Parser Service** — отдельный сервис, который обращается к внешним API (CoinGecko и ExchangeRate-API), обновляет курсы и ведёт историю в `data/exchange_rates.json`.

---

## Структура проекта

```text
finalproject_galimova_25555/
│
├── data/
│   ├── users.json              # пользователи
│   ├── portfolios.json         # портфели и кошельки
│   ├── rates.json              # актуальный кеш курсов для Core Service
│   └── exchange_rates.json     # история обновлений Parser Service
│
├── src/
│   └── valutatrade_hub/
│       ├── __init__.py
│       ├── logging_config.py       # настройка логирования и ротации
│       ├── decorators.py           # @log_action для доменных операций
│
│       ├── core/
│       │   ├── __init__.py
│       │   ├── constants.py        # константы и пути к файлам
│       │   ├── currencies.py       # иерархия Currency / FiatCurrency / CryptoCurrency
│       │   ├── exceptions.py       # доменные исключения
│       │   ├── models.py           # User, Wallet, Portfolio
│       │   ├── usecases.py         # бизнес-логика (register/login/buy/sell/get_rate)
│       │   └── utils.py            # работа с кешем курсов
│
│       ├── infra/
│       │   ├── __init__.py
│       │   ├── settings.py         # Singleton SettingsLoader
│       │   └── database.py         # Singleton DatabaseManager над JSON-хранилищем
│
│       ├── parser_service/
│       │   ├── __init__.py
│       │   ├── config.py           # ParserConfig: API-ключи, URL, списки валют
│       │   ├── api_clients.py      # CoinGeckoClient и ExchangeRateApiClient
│       │   ├── updater.py          # RatesUpdater: запускает обновление курсов
│       │   └── storage.py          # работа с rates.json и exchange_rates.json
│
│       └── cli/
│           ├── __init__.py
│           └── interface.py        # консольный интерфейс пользователя
│
├── main.py                         # точка входа (скрипт project)
├── Makefile
├── pyproject.toml
├── poetry.lock
└── README.md
```

---

# Установка

Требуется Python 3.11+ и Poetry.

## Клонирование репозитория

```bash
git clone <URL_репозитория>
cd finalproject_galimova_25555
```

## Установка зависимостей

```bash
make install
# или
poetry install
```

## Проверка стиля кода

```bash
make lint
# или
poetry run ruff check .
```

---

# Переменные окружения

Для работы с фиатными курсами (ExchangeRate-API) требуется API-ключ.

1. Зарегистрироваться: https://www.exchangerate-api.com/
2. Получить ключ вида:

```
xxxxxxxxxxxxxxxxxxxxxxx
```

3. Установить:

```bash
export EXCHANGERATE_API_KEY="xxxxxxxxxxxxxxxxxxxxxxx"
```

---

# Запуск проекта

```bash
make project
# или
poetry run project
```

---

# Основные команды

## Регистрация и вход

```bash
register --username alice --password secret
login --username alice --password secret
```

## Портфель

```bash
show-portfolio
```

## Покупка / продажа валюты

```bash
buy --currency BTC --amount 0.05
sell --currency BTC --amount 0.02
```

## Курсы валют

```bash
get-rate --from BTC --to USD
```

---

# Обновление курсов

## Вручную

```bash
update-rates
```

## Пример вывода

```
INFO: Starting rates update...
INFO: Fetching from CoinGecko... OK (3 rates)
INFO: Fetching from ExchangeRate-API... OK (3 rates)
INFO: Writing 6 rates to data/rates.json...
Update successful.
```

---

# Просмотр курсов

```bash
show-rates --top 2
```

Пример вывода:

```
Rates from cache (updated at 2025-12-08T12:52:32):
- BTC_USD: 91804.0
- ETH_USD: 3125.38
```

---

##  Asciinema 

Полный сценарий работы приложения:

- запуск (`make project`)
- регистрация/вход (`register`, `login`)
- операции (`buy`, `sell`)
- портфель (`show-portfolio`)
- обновление данных (`update-rates`)
- просмотр курсов (`show-rates`)
- ошибки и сообщения

 Нажмите для просмотра записи:

[![asciinema](https://asciinema.org/a/hiPXfV0IlAz7MSRDp3wCNuD30.svg)](https://asciinema.org/a/hiPXfV0IlAz7MSRDp3wCNuD30)
