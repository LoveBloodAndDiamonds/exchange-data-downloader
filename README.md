# Exchange Data Downloader

`exchange-data-downloader` — простая библиотека для скачивания и распаковки исторических данных с криптовалютных бирж. Она автоматически создаёт структуру папок, кэширует уже загруженные файлы и умеет работать с разными типами данных (klines, trades, funding и др.). Отлично подходит для бэктестов, аналитических пайплайнов и подготовки датасетов.

## Установка

```bash
pip install exchange-data-downloader
```
или
```bash
uv add exchange-data-downloader
```
или
```bash
poetry add exchange-data-downloader
```

## Быстрый старт

```python
from exdata.binance import Downloader

downloader = Downloader(data_folder_path="data/binance")
csv_path = downloader.download(
    symbol="BTCUSDT",
    year=2024,
    month=4,
    timeframe="1h",
    market_type="futures/um",
    period_type="monthly",
    data_type="klines",
)

print(f"Файл сохранён по пути: {csv_path}")
```

- `year`, `month`, `day` передаются числами — библиотека сама добавит ведущие нули.
- Если файл уже скачан и распакован, повторный вызов просто вернёт путь из кэша.

## Дополнительные примеры

### Загрузка дневных trades

```python
csv_path = downloader.download(
    symbol="TRXUSDT",
    year=2025,
    month=3,
    day=15,
    data_type="trades",
    period_type="daily",
    market_type="spot",
)
```

### Обход диапазона дат

```python
from exdata.utils import generate_intervals

intervals = generate_intervals(
    start_year=2024,
    start_month=12,
    start_day=1,
    end_year=2025,
    end_month=1,
    end_day=5,
)

for current in intervals:
    downloader.download(
        symbol="ETHUSDT",
        year=current.year,
        month=current.month,
        day=current.day,
        data_type="aggTrades",
        period_type="daily",
        market_type="futures/um",
        timeframe=None,
    )
```

Функция `generate_intervals` возвращает кортеж объектов `date`, что упрощает обход диапазонов.

## Полезные замечания

- Для kline-подобных типов (`klines`, `markPriceKlines`, `indexPriceKlines` и т.д.) параметр `timeframe` обязателен.
- Для `period_type="daily"` необходимо указать день (`day`), для `monthly` — наоборот, `day` не используется.
- Библиотека выбрасывает `InvalidParamsError`, если параметры указаны некорректно, и `NotFoundError`, если источник не вернул данные.

Используйте `exchange-data-downloader`, чтобы не тратить время на ручные скачивания и сосредоточиться на аналитике. Удачных тестов!
