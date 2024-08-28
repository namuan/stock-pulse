import base64
import io
import os

import matplotlib
import seaborn as sns
from flask import Flask, render_template, request, jsonify

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

app = Flask(__name__)


def output_dir():
    output_directory = "output"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    return output_directory


def download_ticker_data(ticker, start, end):
    try:
        ticker_df = yf.download(ticker, start=start, end=end)
        ticker_df.to_csv(f"{output_dir()}/{ticker}.csv")
        return ticker_df
    except:
        print(f"Unable to fetch data for ticker: {ticker}")
        return pd.DataFrame()


def fetch_stock_data(ticker, start_date, end_date):
    try:
        stock_data = download_ticker_data(ticker, start_date, end_date)
        return stock_data["Adj Close"]
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


if __name__ == '__main__':
    app.run(debug=True, port=5010)
