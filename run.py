import requests
import time
import json
import statistics
import datetime
import os
import sqlite3

API_URL = 'https://api.coinbase.com/v2/'
API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'
TEST_MODE = True  # Set to False for real trades

CURRENCIES = ["BTC", "LTC", "ETH", "XRP"]
CURRENCY = "XRP"
if CURRENCY not in CURRENCIES:
    raise ValueError("Invalid currency selected!")
PAIR = f"{CURRENCY}-USD"

BUY_DROP_PERCENTAGE = 1.0
SELL_RISE_PERCENTAGE = 1.0
BUY_AMOUNT = 00.1

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_SECRET}',
    'CB-ACCESS-KEY': API_KEY,
}

all_prices = []

start_time = datetime.datetime.now()

DATABASE_NAME = 'price_data.db'

def create_or_connect_database():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def setup_database():
    conn = create_or_connect_database()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS prices
                     (timestamp TEXT, currency TEXT, price REAL)''')
    conn.commit()
    conn.close()

def fetch_all_prices_from_db(currency):
    conn = create_or_connect_database()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM prices WHERE currency=?", (currency,))
    prices = [row[0] for row in cursor.fetchall()]
    conn.close()
    return prices

def store_price_in_db(currency, price):
    timestamp = datetime.datetime.now().isoformat()
    conn = create_or_connect_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prices (timestamp, currency, price) VALUES (?, ?, ?)", (timestamp, currency, price))
    conn.commit()
    conn.close()

def get_time_elapsed():
    current_time = datetime.datetime.now()
    elapsed = current_time - start_time
    hours, remainder = divmod(elapsed.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_current_price():
    response = requests.get(API_URL + f'prices/{PAIR}/spot', headers=headers)
    data = response.json()
    price = float(data['data']['amount'])
    all_prices.append(price)
    store_price_in_db(CURRENCY, price)
    return price

def get_median_average(prices):
    median = statistics.median(prices)
    average = sum(prices) / len(prices)
    return median, average

def calculate_percentage_difference(current, reference):
    if reference == 0:
        return 0
    difference = current - reference
    percentage_difference = (difference / reference) * 100
    return percentage_difference

def save_to_json(data, filename="trades.json"):
    try:
        with open(filename, 'r') as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    existing_data.append(data)

    with open(filename, 'w') as file:
        json.dump(existing_data, file)
def place_order(side, amount):
    if TEST_MODE:
        trade_data = {
            "action": side,
            "amount": amount,
            "price": get_current_price(),
            "timestamp": time.time()
        }
        save_to_json(trade_data)
        return {"message": "Trade saved in test mode."}
    else:
        order_data = {
            'type': 'market',
            'side': side,
            'amount': str(amount),
            'product_id': PAIR
        }
        response = requests.post(API_URL + 'orders', headers=headers, json=order_data)
        return response.json()

def trading_bot():
    global all_prices
    previous_prices = fetch_all_prices_from_db(CURRENCY)
    if previous_prices:
        all_prices.extend(previous_prices)
        
    while True:
        current_price = get_current_price()
        time_elapsed = get_time_elapsed()
     
        
        # Calculate median & average for lifetime, the last 10 minutes, and the last hour
        lifetime_median, lifetime_avg = get_median_average(all_prices)
        last_10_min_prices = all_prices[-60:] if len(all_prices) >= 60 else all_prices
        last_10_min_median, last_10_min_avg = get_median_average(last_10_min_prices)
        last_hour_prices = all_prices[-360:] if len(all_prices) >= 360 else all_prices
        last_hour_median, last_hour_avg = get_median_average(last_hour_prices)
        lifetime_median, lifetime_avg = get_median_average(all_prices)
        
        last_10_seconds_prices = all_prices[-10:] if len(all_prices) >= 10 else all_prices
        last_10_seconds_median, last_10_seconds_avg = get_median_average(last_10_seconds_prices)

        last_1_min_prices = all_prices[-60:] if len(all_prices) >= 60 else all_prices
        last_1_min_median, last_1_min_avg = get_median_average(last_1_min_prices)
        
        last_5_min_prices = all_prices[-300:] if len(all_prices) >= 300 else all_prices
        last_5_min_median, last_5_min_avg = get_median_average(last_5_min_prices)

        last_10_min_prices = all_prices[-600:] if len(all_prices) >= 600 else all_prices
        last_10_min_median, last_10_min_avg = get_median_average(last_10_min_prices)
        
        last_hour_prices = all_prices[-3600:] if len(all_prices) >= 3600 else all_prices
        last_hour_median, last_hour_avg = get_median_average(last_hour_prices)
        
        # Calculate percentage differences
        lifetime_median_diff = calculate_percentage_difference(current_price, lifetime_median)
        lifetime_avg_diff = calculate_percentage_difference(current_price, lifetime_avg)
        last_10_min_median_diff = calculate_percentage_difference(current_price, last_10_min_median)
        last_10_min_avg_diff = calculate_percentage_difference(current_price, last_10_min_avg)
        last_hour_median_diff = calculate_percentage_difference(current_price, last_hour_median)
        last_hour_avg_diff = calculate_percentage_difference(current_price, last_hour_avg)
        os.system('cls')
        print("----------------------------------------------------")
        print(f"*******Time elapsed since bot started: {time_elapsed}*******")
        print("----------------------------------------------------")
        if TEST_MODE:
            print("******* BOT IS IN TESTING MODE *******")
        print("----------------------------------------------------")
        print(f"Current price for {CURRENCY}: ${current_price}")

        print("\n------------------- Median Prices -------------------")
        print(f"Bot's lifetime: ${lifetime_median} ({'+' if lifetime_median_diff > 0 else ''}{lifetime_median_diff:.2f}%)")
        print(f"Last hour: ${last_hour_median} ({'+' if last_hour_median_diff > 0 else ''}{last_hour_median_diff:.2f}%)")
        print(f"Last 10 minutes: ${last_10_min_median} ({'+' if last_10_min_median_diff > 0 else ''}{last_10_min_median_diff:.2f}%)")
        print(f"Last 5 minutes: ${last_5_min_median} ({'+' if calculate_percentage_difference(current_price, last_5_min_median) > 0 else ''}{calculate_percentage_difference(current_price, last_5_min_median):.2f}%)")
        print(f"Last 1 minute: ${last_1_min_median} ({'+' if calculate_percentage_difference(current_price, last_1_min_median) > 0 else ''}{calculate_percentage_difference(current_price, last_1_min_median):.2f}%)")
        print(f"Last 10 seconds: ${last_10_seconds_median} ({'+' if calculate_percentage_difference(current_price, last_10_seconds_median) > 0 else ''}{calculate_percentage_difference(current_price, last_10_seconds_median):.2f}%)")

        print("\n------------------- Average Prices -------------------")
        print(f"Bot's lifetime: ${lifetime_avg} ({'+' if lifetime_avg_diff > 0 else ''}{lifetime_avg_diff:.2f}%)")
        print(f"Last hour: ${last_hour_avg} ({'+' if last_hour_avg_diff > 0 else ''}{last_hour_avg_diff:.2f}%)")
        print(f"Last 10 minutes: ${last_10_min_avg} ({'+' if last_10_min_avg_diff > 0 else ''}{last_10_min_avg_diff:.2f}%)")
        print(f"Last 5 minutes: ${last_5_min_avg} ({'+' if calculate_percentage_difference(current_price, last_5_min_avg) > 0 else ''}{calculate_percentage_difference(current_price, last_5_min_avg):.2f}%)")
        print(f"Last 1 minute: ${last_1_min_avg} ({'+' if calculate_percentage_difference(current_price, last_1_min_avg) > 0 else ''}{calculate_percentage_difference(current_price, last_1_min_avg):.2f}%)")
        print(f"Last 10 seconds: ${last_10_seconds_avg} ({'+' if calculate_percentage_difference(current_price, last_10_seconds_avg) > 0 else ''}{calculate_percentage_difference(current_price, last_10_seconds_avg):.2f}%)")

        reference_price = calculate_percentage_difference(current_price, last_10_min_avg_diff)

        if current_price >= reference_price * (1 + BUY_DROP_PERCENTAGE/100):
            print(current_price,reference_price,reference_price * (1 + BUY_DROP_PERCENTAGE/100))
            print(f"Price of {CURRENCY} dropped below threshold, buying!")
            response = place_order('buy', BUY_AMOUNT)
            print(response)

        elif current_price <= reference_price * (1 - SELL_RISE_PERCENTAGE/100):
            print(current_price,reference_price,reference_price * (1 + BUY_DROP_PERCENTAGE/100))
            print(f"Price of {CURRENCY} rose above threshold, selling!")
            response = place_order('sell', BUY_AMOUNT)
            print(response)

        time.sleep(1)

if __name__ == "__main__":
    setup_database()
    trading_bot()