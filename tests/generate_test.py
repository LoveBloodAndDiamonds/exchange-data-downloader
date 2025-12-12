from exdata import generate_intervals, BinanceDownloader


def main() -> None:
    """Main entry point for the application."""

    downloader = BinanceDownloader("test_data")
    intervals = generate_intervals(start_year=2024, start_month=1, end_year=2024, end_month=12)

    for i in intervals:
        print(i)
        # path = downloader.download(
        #     symbol="TRXUSDT",
        #     year=i.year,
        #     month=i.month,
        #     timeframe="1d",
        # )
        # print(path)


if __name__ == "__main__":
    main()
