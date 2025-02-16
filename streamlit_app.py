import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import requests

def get_exchange_rates():
    """
    Get current exchange rates for USD to EUR and NPR
    """
    try:
        response = requests.get('https://open.er-api.com/v6/latest/USD')
        rates = response.json()
        return {
            'EUR': rates['rates']['EUR'],
            'NPR': rates['rates']['NPR'],
            'last_updated': rates['time_last_update_utc']
        }
    except:
        # Fallback rates if API fails
        return {
            'EUR': 0.93,
            'NPR': 132.0,
            'last_updated': 'Unable to fetch latest rates'
        }

def convert_price(price_usd, target_currency, exchange_rates):
    """
    Convert price from USD to target currency
    """
    if target_currency == 'USD':
        return price_usd, '$'
    elif target_currency == 'EUR':
        return price_usd * exchange_rates['EUR'], '€'
    else:  # NPR
        return price_usd * exchange_rates['NPR'], 'रू'

def get_gold_data(timeframe_days):
    """
    Fetch gold price data using GLD ETF as a proxy
    """
    gld = yf.Ticker("GLD")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=timeframe_days)
    df = gld.history(start=start_date, end=end_date)
    return df

def calculate_price_changes(df, exchange_rates, currency):
    """
    Calculate price changes over different time periods
    """
    current_price_usd = df['Close'][-1]
    current_price, symbol = convert_price(current_price_usd, currency, exchange_rates)
    
    # Calculate changes
    one_day_change = ((current_price_usd - df['Close'][-2]) / df['Close'][-2]) * 100
    
    ten_day_price = df['Close'][-11] if len(df) >= 11 else df['Close'][0]
    ten_day_change = ((current_price_usd - ten_day_price) / ten_day_price) * 100
    
    month_start_price = df['Close'][0]
    month_change = ((current_price_usd - month_start_price) / month_start_price) * 100
    
    return current_price, symbol, one_day_change, ten_day_change, month_change

def check_price_alerts(current_price, alert_prices, currency, symbol):
    """
    Check if any price alerts have been triggered
    """
    triggered_alerts = []
    for price in alert_prices:
        if price['price'] >= current_price and price['type'] == 'below':
            triggered_alerts.append(f"Price fell below {symbol}{price['price']:.2f}")
        elif price['price'] <= current_price and price['type'] == 'above':
            triggered_alerts.append(f"Price rose above {symbol}{price['price']:.2f}")
    return triggered_alerts

def main():
    # Set page config
    st.set_page_config(page_title="Gold Price Tracker", layout="wide")
    
    # Initialize session state for alerts
    if 'price_alerts' not in st.session_state:
        st.session_state.price_alerts = []
    
    # Title
    st.title("📈 Gold Price Tracker")
    
    # Get exchange rates
    exchange_rates = get_exchange_rates()
    
    # Display exchange rates in a container at the top
    with st.container():
        st.subheader("Current Exchange Rates")
        rate_col1, rate_col2, rate_col3 = st.columns(3)
        
        with rate_col1:
            st.metric(
                "USD to EUR",
                f"€{exchange_rates['EUR']:.4f}",
                help="1 USD = X EUR"
            )
        
        with rate_col2:
            st.metric(
                "USD to NPR",
                f"रू{exchange_rates['NPR']:.2f}",
                help="1 USD = X NPR"
            )
            
        with rate_col3:
            st.info(f"Last Updated: {exchange_rates['last_updated']}")
    
    # Add a separator
    st.markdown("---")
    
    # Currency selector
    currency_options = {
        'US Dollar': 'USD',
        'Euro': 'EUR',
        'Nepali Rupee': 'NPR'
    }
    
    # Timeframe options
    timeframe_options = {
        '1 Week': 7,
        '1 Month': 30,
        '3 Months': 90,
        '6 Months': 180,
        '1 Year': 365
    }
    
    col1, col2 = st.columns(2)
    with col1:
        selected_currency = st.selectbox('Select Currency', list(currency_options.keys()))
    with col2:
        selected_timeframe = st.selectbox('Select Timeframe', list(timeframe_options.keys()))
    
    currency_code = currency_options[selected_currency]
    
    try:
        # Get data
        df = get_gold_data(timeframe_options[selected_timeframe])
        
        # Calculate metrics
        current_price, symbol, one_day_change, ten_day_change, month_change = calculate_price_changes(
            df, exchange_rates, currency_code
        )
        
        # Price Alerts Section
        st.sidebar.header("Price Alerts")
        
        # Add new alert
        col1, col2 = st.sidebar.columns(2)
        alert_price = col1.number_input(f"Alert Price ({currency_code})", 
                                      min_value=0.0, 
                                      value=current_price)
        alert_type = col2.selectbox("Alert Type", ['above', 'below'])
        
        if st.sidebar.button("Add Alert"):
            st.session_state.price_alerts.append({
                'price': alert_price,
                'type': alert_type
            })
        
        # Display active alerts
        st.sidebar.subheader("Active Alerts")
        for idx, alert in enumerate(st.session_state.price_alerts):
            col1, col2 = st.sidebar.columns([3, 1])
            col1.write(f"{symbol}{alert['price']:.2f} ({alert['type']})")
            if col2.button("Delete", key=f"delete_{idx}"):
                st.session_state.price_alerts.pop(idx)
                st.experimental_rerun()
        
        # Check for triggered alerts
        triggered_alerts = check_price_alerts(current_price, st.session_state.price_alerts, 
                                           currency_code, symbol)
        if triggered_alerts:
            for alert in triggered_alerts:
                st.warning(alert)
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                f"Current Gold Price ({currency_code})",
                f"{symbol}{current_price:.2f}",
            )
        
        with col2:
            st.metric(
                "24h Change",
                f"{one_day_change:.2f}%",
                delta=f"{one_day_change:.2f}%"
            )
            
        with col3:
            st.metric(
                "10-Day Change",
                f"{ten_day_change:.2f}%",
                delta=f"{ten_day_change:.2f}%"
            )
            
        with col4:
            st.metric(
                "1-Month Change",
                f"{month_change:.2f}%",
                delta=f"{month_change:.2f}%"
            )
        
        # Convert historical prices for chart
        df_converted = df.copy()
        if currency_code != 'USD':
            df_converted['Close'] = df['Close'] * exchange_rates[currency_code]
        
        # Price Chart
        st.subheader(f"Gold Price Chart ({selected_timeframe})")
        st.line_chart(df_converted['Close'])
        
        # Display raw data
        st.subheader("Historical Data")
        st.dataframe(df_converted)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try refreshing the page.")

if __name__ == "__main__":
    main()
