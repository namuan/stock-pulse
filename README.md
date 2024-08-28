# Stock Performance Comparison App

This is a Flask web application that allows users to compare the stock performance of multiple companies over a specified date range. The application fetches stock data using the Yahoo Finance API, calculates performance metrics, and displays the results in a graphical format.

## Features

- Fetch stock data for multiple tickers from Yahoo Finance.
- Calculate and display total percent change, average daily change, and standard deviation of daily change.
- Visualize stock performance over time using line charts.

## Requirements

- Python 3.x
- Flask
- pandas
- matplotlib
- seaborn
- yfinance

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask application:

   ```bash
   python app.py
   ```

2. Open your web browser and go to `http://localhost:5010`.

3. Enter the stock tickers, start date, and end date to compare stock performance.

## File Structure

- `app.py`: Main application file containing the Flask routes and logic.
- `templates/index.html`: HTML template for the web interface.
- `requirements.txt`: List of Python dependencies.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
