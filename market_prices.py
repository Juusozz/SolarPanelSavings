import pandas as pd
import streamlit as st
import datetime
import requests
import numpy as np

def fetch_market_prices(start_time, end_time):
    # Formatter for date and hour
    date_format = "%Y-%m-%d"
    hour_format = "%H"
    
    # Create a DatetimeIndex with hourly frequency within the range
    times = pd.date_range(start=start_time, end=end_time, freq='h')
    
    # List to hold row data for DataFrame
    market_prices = []

    # Iterate over each datetime object in the range
    for current_time in times:
        current_date = current_time.strftime(date_format)
        current_hour = current_time.strftime(hour_format)
        
        # Build the URL
        url = f'https://api.porssisahko.net/v1/price.json?date={current_date}&hour={current_hour}'
        
        # Make the request
        response = requests.get(url)
        
        # Check if the response is okay
        if response.status_code == 200:
            data = response.json()
            # Assuming the JSON structure contains 'price' field, you might need to adjust based on actual API response.
            price = data["price"] if "price" in data else None
        else:
            price = None
        
        # Append the data
        if price > 0:
            market_prices.append({'time': current_time, 'c/kWh': price})
        else:
            market_prices.append({'time': current_time, 'c/kWh': np.nan})
    
    # Create DataFrame from data
    
    return pd.DataFrame(market_prices).set_index('time')