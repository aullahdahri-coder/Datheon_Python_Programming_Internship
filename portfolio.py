"""Investment Portfolio Tracker (console).

Enter ticker symbols, buy prices and share quantities. The program looks up
current prices, computes the total portfolio value and the % gain/loss per
holding, then logs a summary to 'portfolio_summary.csv'.

Price sources (in order):
  1. 'prices.csv' next to this script (columns: ticker,price) - e.g. the
     downloaded S&P 500 dataset, if it has a price column.
  2. Live prices via yfinance, if installed (pip install yfinance).
  3. Built-in sample prices.
  4. Ask the user to type the current price.

Run: python portfolio.py
"""

import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRICES_FILE = os.path.join(BASE_DIR, "prices.csv")
SUMMARY_FILE = os.path.join(BASE_DIR, "portfolio_summary.csv")

SAMPLE_PRICES = {
    "AAPL": 230.00, "MSFT": 420.00, "GOOGL": 175.00, "AMZN": 190.00,
    "TSLA": 250.00, "NVDA": 130.00, "META": 560.00, "JPM": 215.00,
    "V": 275.00, "KO": 68.00,
}

FIELDS = ["timestamp", "ticker", "shares", "buy_price", "current_price",
          "invested", "market_value", "gain_loss", "gain_loss_pct"]


def load_csv_prices():
    """Read ticker->price from prices.csv if it exists and has price data."""
    prices = {}
    if not os.path.exists(PRICES_FILE):
        return prices
    with open(PRICES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return prices
        cols = {c.lower().strip(): c for c in reader.fieldnames}
        t_col = cols.get("ticker") or cols.get("symbol")
        p_col = cols.get("price") or cols.get("close") or cols.get("current_price")
        if not (t_col and p_col):
            return prices
        for row in reader:
            try:
                prices[row[t_col].strip().upper()] = float(row[p_col])
            except (ValueError, AttributeError):
                continue
    return prices


def live_price(ticker):
    """Try to fetch a live price with yfinance; return None on any failure."""
    try:
        import yfinance as yf
        hist = yf.Ticker(ticker).history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None


def get_current_price(ticker, csv_prices):
    if ticker in csv_prices:
        return csv_prices[ticker]
    price = live_price(ticker)
    if price is not None:
        return price
    if ticker in SAMPLE_PRICES:
        return SAMPLE_PRICES[ticker]
    return read_float(f"  Current price for {ticker} not found. Enter it: $")


def read_float(prompt, minimum=0.0):
    while True:
        try:
            value = float(input(prompt).strip().replace(",", ""))
            if value > minimum:
                return value
            print(f"  Value must be greater than {minimum}.")
        except ValueError:
            print("  Please enter a valid number.")


def read_ticker():
    while True:
        t = input("Ticker symbol (or press Enter to finish): ").strip().upper()
        if t == "":
            return None
        if t.replace(".", "").replace("-", "").isalpha():
            return t
        print("  Invalid ticker. Use letters only (e.g. AAPL).")


def collect_positions():
    """Return dict: ticker -> {'shares': float, 'buy_price': float}."""
    portfolio = {}
    print("Add your holdings.\n")
    while True:
        ticker = read_ticker()
        if ticker is None:
            if portfolio:
                break
            print("  Add at least one holding first.")
            continue
        buy_price = read_float("  Buy price per share: $")
        shares = read_float("  Number of shares: ")
        if ticker in portfolio:
            # Merge into weighted-average cost
            old = portfolio[ticker]
            total_shares = old["shares"] + shares
            avg = (old["shares"] * old["buy_price"] + shares * buy_price) / total_shares
            portfolio[ticker] = {"shares": total_shares, "buy_price": avg}
            print(f"  Updated {ticker} (avg buy price ${avg:,.2f}).")
        else:
            portfolio[ticker] = {"shares": shares, "buy_price": buy_price}
        print()
    return portfolio


def evaluate(portfolio):
    csv_prices = load_csv_prices()
    rows = []
    for ticker, pos in portfolio.items():
        current = get_current_price(ticker, csv_prices)
        invested = pos["shares"] * pos["buy_price"]
        value = pos["shares"] * current
        gain = value - invested
        pct = gain / invested * 100
        rows.append({
            "ticker": ticker, "shares": pos["shares"],
            "buy_price": pos["buy_price"], "current_price": current,
            "invested": invested, "market_value": value,
            "gain_loss": gain, "gain_loss_pct": pct,
        })
    return rows


def print_report(rows):
    header = (f"{'Ticker':<8}{'Shares':>9}{'Buy':>11}{'Current':>11}"
              f"{'Invested':>13}{'Value':>13}{'Gain/Loss':>13}{'%':>9}")
    line = "-" * len(header)
    print("\n" + line)
    print(header)
    print(line)
    for r in rows:
        print(f"{r['ticker']:<8}{r['shares']:>9,.2f}{r['buy_price']:>11,.2f}"
              f"{r['current_price']:>11,.2f}{r['invested']:>13,.2f}"
              f"{r['market_value']:>13,.2f}{r['gain_loss']:>+13,.2f}"
              f"{r['gain_loss_pct']:>+8.2f}%")
    print(line)
    invested = sum(r["invested"] for r in rows)
    value = sum(r["market_value"] for r in rows)
    gain = value - invested
    pct = gain / invested * 100 if invested else 0
    print(f"{'TOTAL':<8}{'':>9}{'':>11}{'':>11}{invested:>13,.2f}"
          f"{value:>13,.2f}{gain:>+13,.2f}{pct:>+8.2f}%")
    print(line)
    return invested, value, gain, pct


def save_summary(rows, totals):
    """Append this run's summary to portfolio_summary.csv."""
    new_file = not os.path.exists(SUMMARY_FILE)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUMMARY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        for r in rows:
            out = {k: (round(v, 2) if isinstance(v, float) else v)
                   for k, v in r.items()}
            out["timestamp"] = stamp
            writer.writerow(out)
        invested, value, gain, pct = totals
        writer.writerow({
            "timestamp": stamp, "ticker": "TOTAL", "shares": "",
            "buy_price": "", "current_price": "",
            "invested": round(invested, 2), "market_value": round(value, 2),
            "gain_loss": round(gain, 2), "gain_loss_pct": round(pct, 2),
        })
    print(f"\nSummary saved to {SUMMARY_FILE}")


def main():
    print("=== PORTFOLIO TRACKER ===\n")
    portfolio = collect_positions()
    rows = evaluate(portfolio)
    totals = print_report(rows)
    save_summary(rows, totals)


if __name__ == "__main__":
    main()
