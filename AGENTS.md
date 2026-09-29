# AGENTS.md

Инструкции для ИИ-агентов, которые работают с этим репозиторием.

## О проекте

`exchange-data-downloader` (пакет `exdata`) — библиотека для скачивания исторических данных бирж из публичных архивов:
- **Binance**: [data.binance.vision](https://data.binance.vision/)
- **Bybit**: [public.bybit.com](https://public.bybit.com/)

Библиотека только скачивает, кэширует и распаковывает файлы. CSV она **не парсит**.

Зависимости: только `loguru`. HTTP работает на стандартном `urllib`, новые зависимости без необходимости не добавлять.

## Структура

```
exdata/
├── __init__.py        # публичный API: BinanceDownloader, BybitDownloader, исключения, generate_intervals
├── base.py            # BaseDownloader: кэш, папки, скачивание, нормализация дат, 404 → NotFoundError
├── exceptions.py      # InvalidParamsError (плохие параметры), NotFoundError (файла нет на сервере)
├── utils.py           # generate_intervals — генерация дат для обхода периода
├── binance/
│   ├── downloader.py  # Downloader(BaseDownloader): ZIP, построение пути Binance
│   └── types.py       # Literal-типы: MarketTypes, PeriodTypes, DataTypes, Timeframes
└── bybit/
    ├── downloader.py  # Downloader(BaseDownloader): .csv.gz, построение пути Bybit
    └── types.py       # Literal-типы: MarketTypes, PeriodTypes, DataTypes
tests/                 # ручные скрипты с реальными скачиваниями, а не pytest
```

## Команды

```bash
uv sync                                   # установить окружение
uv run python -m tests.bybit_test         # тест-скрипты запускать ТОЛЬКО как модуль (-m),
uv run python -m tests.binance_test       # иначе будет ModuleNotFoundError: exdata
uv run pre-commit run --all-files         # ruff (с автоисправлением) + проверка больших файлов
uvx pyright                               # проверка типов, должно быть 0 errors
```

Тест-скрипты ходят в сеть и скачивают реальные файлы в `test_data/`. Один день сделок BTCUSDT на Bybit в распакованном виде весит около 300 МБ. Папка в `.gitignore`, но после проверки её нужно удалить.

## Как устроен загрузчик

Контракт, общий для всех бирж:
- **Параметры `download`.** Имена и порядок одинаковые: `symbol, year, month, day, data_type, market_type, [timeframe], period_type, unzip`. `timeframe` есть только там, где биржа отдаёт свечи. Допустимые значения каждая биржа описывает своими `Literal`-типами в `types.py`.
- **Даты.** `year`, `month` и `day` передаются числами, ведущие нули добавляет `BaseDownloader._normalize_*`.
- **Результат.** Метод возвращает путь к файлу. При `unzip=False` это архив в родном формате биржи, при `unzip=True` — распакованный `.csv`, а архив удаляется.
- **Локальные пути.** Они повторяют путь на сервере биржи: `{data_folder_path}/{endpoint}{extension}`.
- **Кэш.** Если целевой файл уже существует, он не скачивается повторно.
- **Ошибки.** Невалидная комбинация параметров → `InvalidParamsError`. HTTP 404 и сетевые ошибки → `NotFoundError`.

`BaseDownloader._download_endpoint(endpoint, unzip)` выполняет весь общий сценарий. Наследник отвечает только за биржевую специфику.

### Добавление новой биржи

1. Создать `exdata/<exchange>/types.py` с `Literal`-типами допустимых значений.
2. Создать `exdata/<exchange>/downloader.py` с `class Downloader(BaseDownloader)`:
   - задать атрибуты класса `_base_url` и `_archive_extension`;
   - реализовать `_extract_archive(extract_from, extract_to) -> str`: распаковать, удалить архив, вернуть путь к CSV;
   - реализовать `_compare_endpoint(...)`: собрать путь **без расширения**, бросить `InvalidParamsError` на неподдерживаемые комбинации;
   - реализовать публичный `download(...)` по контракту выше: нормализация дат → `_compare_endpoint` → `self._download_endpoint(...)`.
3. Экспортировать класс в `exdata/<exchange>/__init__.py` и в `exdata/__init__.py` как `<Exchange>Downloader`.
4. Добавить `tests/<exchange>_test.py` по образцу существующих.
5. Добавить раздел биржи в `README.md` и поднять MINOR-версию (см. «Версии»).

## Источники данных

### Binance

Путь: `{market_type}/{period_type}/{data_type}/{SYMBOL}/[{timeframe}/]{SYMBOL}-{timeframe|data_type}-{YYYY-MM[-DD]}.zip`

- Для kline-подобных `data_type` (`klines`, `markPriceKlines`, `indexPriceKlines`, `premiumIndexKlines`) нужен `timeframe`.
- Доступны `period_type`: `monthly` и `daily`.

### Bybit

| market_type | period_type | Путь |
|---|---|---|
| `futures` | `daily` | `trading/{S}/{S}{YYYY-MM-DD}.csv.gz` |
| `spot` | `daily` | `spot/{S}/{S}_{YYYY-MM-DD}.csv.gz` |
| `spot` | `monthly` | `spot/{S}/{S}-{YYYY-MM}.csv.gz` |

- Единственный `data_type` — `trades`. Monthly у фьючерсов нет.
- В `trading/` лежат USDT-, USDC- (`...PERP`), инверсные (`BTCUSD`) и срочные (`BTC-26DEC25`) контракты.
- Намеренно **не поддерживаются** `kline_for_metatrader4/` (23 символа, данные только до конца 2024), `premium_index/` и `spot_index/` (данные только за 2019–2020).
- Время в файлах: у фьючерсов секунды (float), у спота миллисекунды.

## Примеры использования

```python
from exdata import BinanceDownloader, BybitDownloader, InvalidParamsError, NotFoundError, generate_intervals

# Binance: месячные свечи 1h по USDT-M фьючерсам
path = BinanceDownloader("data/binance").download(
    symbol="BTCUSDT", year=2024, month=4, data_type="klines",
    market_type="futures/um", timeframe="1h", period_type="monthly", unzip=True,
)

# Bybit: сделки по фьючерсу за каждый день диапазона
bybit = BybitDownloader("data/bybit")
for d in generate_intervals(start_year=2025, start_month=1, start_day=1,
                            end_year=2025, end_month=1, end_day=7):
    try:
        bybit.download(symbol="BTCUSDT", year=d.year, month=d.month, day=d.day,
                       market_type="futures", period_type="daily", unzip=True)
    except NotFoundError:
        pass  # символа ещё не было в этот день или файл пока не опубликован
```

## Стиль кода

- **Python и типизация.** Минимальная версия Python 3.12. Type hints везде. Типы объявлять через `type X = Literal[...]` (PEP 695).
- **Ruff.** Включён `pydocstyle` (`D`), длина строки 100. Каталог `tests/` исключён из проверок.
- **Язык.** Docstring и комментарии на русском. Тексты **логов и исключений — на английском**. Исключение: сообщения из `BaseDownloader._normalize_*`, их пока не трогаем.
- **Логи.** Только f-строки, через `self._logger`. Это `loguru` или стандартный `logging.Logger`, переданный пользователем.
- **Приватность.** Всё, что не входит в публичный API, делать приватным (`_`).
- **Совместимость.** Сигнатуру `download` и формат локальных путей нельзя менять без MAJOR-версии: у пользователей на них завязан кэш.

## Версии и публикация

- SemVer, правила описаны в комментарии в `pyproject.toml`. После изменения версии выполнить `uv lock`, чтобы обновился `uv.lock`.
- Публикация в PyPI (`make pypi-build-and-publish`) и коммиты — **только по явной просьбе пользователя**.
