from exdata import InvalidParamsError
from exdata.bybit import Downloader, MarketTypes, PeriodTypes, DataTypes


def main() -> None:
    """Main entry point for the application."""
    downloader = Downloader("test_data/bybit")

    # Фьючерсы: только daily trades, распаковываем в CSV
    path = downloader.download(
        symbol="BTCUSDT",
        year=2026,
        month=9,
        day=28,
        market_type="futures",
        unzip=True,
    )
    print(path)

    # Спот: monthly trades, оставляем архив .csv.gz
    path = downloader.download(
        symbol="TRXUSDT",
        year=2026,
        month=8,
        market_type="spot",
        period_type="monthly",
        unzip=False,
    )
    print(path)

    # Monthly для фьючерсов на Bybit не существует — ожидаем ошибку
    try:
        downloader.download(symbol="BTCUSDT", year=2026, month=8, period_type="monthly")
    except InvalidParamsError as e:
        print(f"Expected error: {e}")


if __name__ == "__main__":
    main()
