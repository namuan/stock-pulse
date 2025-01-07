#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "PyQt6",
#   "flask",
#   "gunicorn",
#   "matplotlib",
#   "pandas",
#   "yfinance",
#   "seaborn",
#   "PyQt6-WebEngine",
#   "flask-cors",
# ]
# ///
"""
Stock Performance Comparison Tool

This script provides a GUI application that allows users to:
- Compare stock performance for multiple tickers
- Generate performance comparison plots
- View summary statistics for selected stocks

The application combines Flask for backend processing and PyQt6 for the GUI.

Usage:
./app.py
Or
./app.py --server-only

Features:
- Interactive web interface
- Real-time stock data fetching using yfinance
- Comparative visualization of stock performance
- Statistical analysis including total change, percent change, and volatility metrics
"""
import argparse
import base64
import faulthandler
import io
import os
import sys
import threading

import matplotlib
import seaborn as sns
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication
from flask import Flask
from flask import render_template, request, jsonify

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

faulthandler.enable()

app = Flask(__name__)


def output_dir():
    output_directory = "output"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    return output_directory


def download_ticker_data(ticker, start, end):
    try:
        return yf.download(ticker, start=start, end=end, multi_level_index=False)
    except:
        print(f"Unable to fetch data for ticker: {ticker}")
        return pd.DataFrame()


def fetch_stock_data(ticker, start_date, end_date):
    try:
        stock_data = download_ticker_data(ticker, start_date, end_date)
        return stock_data["Close"]
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def calculate_percent_change(stock_data):
    return stock_data.pct_change().fillna(0).add(1).cumprod().sub(1).mul(100)


def calculate_summary_stats(stock_data, ticker):
    total_change = stock_data.iloc[-1] - stock_data.iloc[0]
    total_pct_change = (stock_data.iloc[-1] / stock_data.iloc[0] - 1) * 100
    avg_daily_change = stock_data.pct_change().mean() * 100
    std_daily_change = stock_data.pct_change().std() * 100

    return {
        "Ticker": ticker,
        "Total Change": round(total_change, 2),
        "Total Percent Change (%)": round(total_pct_change, 2),
        "Average Daily Change (%)": round(avg_daily_change, 2),
        "Standard Deviation of Daily Change (%)": round(std_daily_change, 2),
    }


def plot_stock_performance(stock_data_list, ticker_list, start_date, end_date):
    plt.figure(figsize=(12, 6))
    sns.set_style("white")

    for stock_data, ticker in zip(stock_data_list, ticker_list):
        if stock_data is not None and not stock_data.empty:
            stock_pc = calculate_percent_change(stock_data)
            plt.plot(stock_pc.index, stock_pc, label=ticker)

    plt.title(f"Stock Performance Comparison ({start_date} to {end_date})")
    plt.xlabel("Date")
    plt.ylabel("Percent Change (%)")
    plt.legend(loc="upper left")

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return plot_url


@app.route('/')
def index():
    from datetime import date
    current_date = date.today().isoformat()
    return render_template('index.html', current_date=current_date)


@app.route('/compare', methods=['POST'])
def compare():
    tickers = request.form['tickers'].split(',')
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    ticker_list = [ticker.strip().upper() for ticker in tickers]
    stock_data_list = []
    summary_stats = []

    for ticker in ticker_list:
        stock_data = fetch_stock_data(ticker, start_date, end_date)
        stock_data_list.append(stock_data)
        if stock_data is not None and not stock_data.empty:
            summary_stats.append(calculate_summary_stats(stock_data, ticker))

    plot_url = plot_stock_performance(stock_data_list, ticker_list, start_date, end_date)

    return jsonify({
        'plot_url': plot_url,
        'summary_stats': summary_stats
    })


def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True, use_reloader=False)


class Browser:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.web = QWebEngineView()
        self.web.setGeometry(100, 100, 800, 600)
        self.web.setWindowTitle("StockPulse")
        self.web.load(QUrl("http://127.0.0.1:5000"))
        self.web.show()

        # Add cleanup handling
        self.web.destroyed.connect(self._on_destroy)

    def _on_destroy(self):
        self.qt_app.quit()

    def run(self):
        # Start Flask server in a separate thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        # Use aboutToQuit instead of directly calling sys.exit
        self.qt_app.aboutToQuit.connect(self._cleanup)
        self.qt_app.exec()

    def _cleanup(self):
        self.web.close()
        self.web.deleteLater()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--server-only', action='store_true', help='Run only the Flask server without GUI')
    args = parser.parse_args()

    if args.server_only:
        run_flask()
    else:
        browser = Browser()
        browser.run()


if __name__ == "__main__":
    main()
