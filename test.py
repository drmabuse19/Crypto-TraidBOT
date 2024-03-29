import requests
import sqlite3
from datetime import datetime
import os,time
import sys
import msvcrt
from datetime import timedelta
# Fetch XRP price from Coinbase
def get_xrp_price():
    URL = "https://api.coinbase.com/v2/prices/XRP-USD/spot"
    response = requests.get(URL)
    data = response.json()
    return float(data["data"]["amount"])

# Get last price from the database
def get_last_price_from_db():
    conn = sqlite3.connect('xrp_prices.db')
    c = conn.cursor()
    c.execute("SELECT price FROM prices ORDER BY date DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Get average price from the database
def get_average_price_from_db():
    conn = sqlite3.connect('xrp_prices.db')
    c = conn.cursor()
    c.execute("SELECT AVG(price) FROM prices")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Store price in local SQLite DB
def store_price_in_db(price):
    # Connect to local SQLite DB
    conn = sqlite3.connect('xrp_prices.db')
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS prices 
                (date text, price real)''')
    
    # Insert a new row of data
    c.execute("INSERT INTO prices VALUES (?, ?)", (datetime.now().isoformat(), price))

    # Commit changes and close connection
    conn.commit()
    conn.close()
def calculate_percentage_difference(current_price, average_price):
    if current_price == 0:
        return 0
    return ((current_price - average_price) / current_price) * 100

# Clear console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
def get_average_price_over_duration(duration_seconds):
    time_threshold = (datetime.now() - timedelta(seconds=duration_seconds)).isoformat()
    
    conn = sqlite3.connect('xrp_prices.db')
    c = conn.cursor()
    c.execute("SELECT AVG(price) FROM prices WHERE date >= ?", (time_threshold,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
if __name__ == "__main__":
    print("Press 'f' to stop fetching and storing XRP prices.")
    while True:
        time.sleep(.7)
        if msvcrt.kbhit():
            char = msvcrt.getch().decode('utf-8')
            if char.lower() == 'f':
                sys.exit()

        
        last_price = get_last_price_from_db()
        price = get_xrp_price()
        clear_console()
        if price != last_price:
            print(f"New XRP Price: ${price:.6f}")
            store_price_in_db(price)
            
        else:
            print(f"XRP Price remains the same: ${price:.6f}")

         # after fetching the current price, calculate averages for all durations
        durations = [60, 300, 600, 1200, 1800, 2400, 3000, 3600, 10800, 18000, 36000, 57600, 86400]  # in seconds
        labels = ['1 min', '5 min', '10 min', '20 min', '30 min', '40 min', '50 min', '1 hour', '3 hours', '5 hours', '10 hours', '16 hours', '24 hours']

        for duration, label in zip(durations, labels):
            avg_price = get_average_price_over_duration(duration)
            if avg_price is not None:
                percentage_diff = calculate_percentage_difference(price, avg_price)
                print(f"Average XRP Price over {label}: ${avg_price:.6f} (Difference: {percentage_diff:.2f}%)")
    