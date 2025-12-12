from exdata.binance import Downloader, MarketTypes, PeriodTypes, DataTypes, Timeframes


def main() -> None:
    """Main entry point for the application."""
    downloader = Downloader("test_data")
    path = downloader.download(
        symbol="TRXUSDT",
        year=2025,
        month=10,
        timeframe="15m",
    )
    print(path)


if __name__ == "__main__":
    main()
