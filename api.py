from flask import Flask, jsonify
import requests
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Fetch current XRP price from Coinbase
def get_xrp_price():
    URL = "https://api.coinbase.com/v2/prices/XRP-USD/spot"
    response = requests.get(URL)
    data = response.json()
    return float(data["data"]["amount"])

# Get average price from the database over the given duration in seconds
def get_average_price_over_duration(duration_seconds):
    time_threshold = (datetime.now() - timedelta(seconds=duration_seconds)).isoformat()
    
    conn = sqlite3.connect('xrp_prices.db')
    c = conn.cursor()
    c.execute("SELECT AVG(price) FROM prices WHERE date >= ?", (time_threshold,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

@app.route('/averages', methods=['GET'])
def get_averages():
    price = get_xrp_price()
    durations = [60, 300, 600, 1200, 1800, 2400, 3000, 3600, 10800, 18000, 36000, 57600, 86400]  # in seconds
    labels = ['1 min', '5 min', '10 min', '20 min', '30 min', '40 min', '50 min', '1 hour', '3 hours', '5 hours', '10 hours', '16 hours', '24 hours']

    averages = {}
    for duration, label in zip(durations, labels):
        avg_price = get_average_price_over_duration(duration)
        if avg_price is not None:
            difference_percentage = ((price - avg_price) / price) * 100
            averages[label] = {
                'average_price': avg_price,
                'difference_percentage': difference_percentage
            }

    return jsonify({'current_price': price, 'averages': averages})

if __name__ == '__main__':
    app.run(debug=True)
