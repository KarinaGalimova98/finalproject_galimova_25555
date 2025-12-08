# Final Project — Currency Wallet

Учебный консольный проект по Python, имитирующий работу валютного кошелька с поддержкой фиатных и криптовалют.

Проект состоит из двух слоёв:

- **Core Service** — управление пользователями, кошельками и портфелями, операция покупки/продажи, работа с локальным кэшем курсов (`data/rates.json`).
- **Parser Service** — отдельный сервис, который обращается к внешним API (CoinGecko и ExchangeRate-API), обновляет курсы и ведёт историю в `data/exchange_rates.json`.

Структура проекта

finalproject_galimova_25555/
├── data/
│   ├── users.json             # пользователи
│   ├── portfolios.json        # портфели и кошельки
│   ├── rates.json             # актуальный кэш курсов для Core Service
│   └── exchange_rates.json    # история обновлений Parser Service
├── src/
│   └── valutatrade_hub/
│       ├── __init__.py
│       ├── logging_config.py  # настройка логирования и ротации
│       ├── decorators.py      # @log_action для доменных операций
│       ├── core/
│       │   ├── __init__.py
│       │   ├── constants.py   # константы и пути к файлам
│       │   ├── currencies.py  # иерархия Currency / FiatCurrency / CryptoCurrency
│       │   ├── exceptions.py  # доменные исключения
│       │   ├── models.py      # User, Wallet, Portfolio
│       │   ├── usecases.py    # бизнес-логика (register/login/buy/sell/get_rate)
│       │   └── utils.py       # работа с кэшем курсов
│       ├── infra/
│       │   ├── __init__.py
│       │   ├── settings.py    # Singleton SettingsLoader
│       │   └── database.py    # Singleton DatabaseManager над JSON-хранилищем
│       ├── parser_service/
│       │   ├── __init__.py
│       │   ├── config.py      # ParserConfig: API-ключи, URL, списки валют
│       │   ├── storage.py     # работа с rates.json и exchange_rates.json
│       │   ├── api_clients.py # CoinGeckoClient и ExchangeRateApiClient
│       │   └── updater.py     # RatesUpdater: запускает обновление курсов
│       └── cli/
│           ├── __init__.py
│           └── interface.py   # консольный интерфейс пользователя
├── main.py                    # точка входа (скрипт project)
├── Makefile
├── pyproject.toml
├── poetry.lock
└── README.md

Установка

Требуется Python 3.11+ и Poetry.

# Клонирование репозитория
git clone <URL_репозитория>
cd finalproject_galimova_25555

# Установка зависимостей
make install
# или
poetry install

Проверка стиля кода:

make lint
# или
poetry run ruff check .

Переменные окружения

Для работы с фиатными курсами (ExchangeRate-API) требуется API-ключ.

Зарегистрироваться на https://www.exchangerate-api.com/
.

Получить ключ вида xxxxxxxxxxxxxxxxxxxxxx.

Установить переменную окружения, например:

export EXCHANGERATE_API_KEY="ваш_ключ"

Для постоянной настройки можно добавить строку в ~/.bashrc:
echo 'export EXCHANGERATE_API_KEY="ваш_ключ"' >> ~/.bashrc
source ~/.bashrc



Запуск приложения

make project
# или
poetry run project


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
