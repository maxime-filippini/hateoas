import argparse
import sqlite3
from typing import Sequence
import pandas as pd
import yfinance as yf

SYMBOLS = [
    "AAPL",
    "MSFT",
    "TSLA",
    "NVDA",
    "SPY"
]

def prep_database(path: str) -> None:
    t = yf.Tickers(" ".join(SYMBOLS))
    df_history: pd.DataFrame = t.history(period="max", interval="1d")
    print(df_history.columns)

    df_final = (
        df_history
        .loc[:, "Close"] # No adjustment for now - don't care
        # .loc[:, ["Close", "Dividend", "Stock Splits"]]
        .reset_index()
        .rename(columns={"Date": "date", "Close": "close_raw"})
        .melt(id_vars=["date"], var_name="symbol", value_name="raw_close_price")
        .assign(date=lambda df: pd.to_datetime(df["date"]))
        .dropna()
    )
    
    with sqlite3.connect(path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                date TEXT,
                symbol TEXT,
                raw_close_price NUMERIC,
                PRIMARY KEY (date, symbol)
            )
            """
        )

        con.execute("DELETE FROM prices")

        df_final.to_sql("prices", con=con, if_exists="replace", index=False)

    print("DB creation successful!")

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dbpath", action="store")

    args = parser.parse_args(argv)

    prep_database(path=args.dbpath)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())