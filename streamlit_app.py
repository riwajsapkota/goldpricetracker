import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def get_gold_data(timeframe_days):
    """
    Fetch gold price data using GLD ETF as a proxy
    """
    # Get GLD data
    gld = yf.Ticker("GLD")
    
    # Get historical data for the selected timeframe
    end_date = datetime.now()
    start_date = end_date - timedelta(days=timeframe_days)
    
    df = gld.history(start=start_date, end=end_date)
    return df

def calculate_price_changes(df):
    """
    Calculate price changes over different time periods
    """
    current_price = df['Close'][-1]
    
    # Calculate changes
    one_day_change = ((current_price - df['Close'][-2]) / df['Close'][-2]) * 100
    
    # Last 10 days
    ten_day_price = df['Close'][-11] if len(df) >= 11 else df['Close'][0]
    ten_day_change = ((current_price - ten_day_price) / ten_day_price) * 100
    
    # Last month
    month_start_price = df['Close'][0]
    month_change = ((current_price - month_start_price) / month_start_price) * 100
    
    return current_price, one_day_change, ten_day_change, month_change

def calculate_volume_metrics(df):
    """
    Calculate volume analysis metrics
    """
    current_volume = df['Volume'][-1]
    avg_volume = df['Volume'].mean()
    volume_change = ((current_volume - df['Volume'][-2]) / df['Volume'][-2]) * 100
    
    # Calculate Volume Moving Averages
    df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()
    df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
    
    return current_volume, avg_volume, volume_change, df

def check_price_alerts(current_price, alert_prices):
    """
    Check if any price alerts have been triggered
    """
    triggered_alerts = []
    for price in alert_prices:
        if price['price'] >= current_price and price['type'] == 'below':
            triggered_alerts.append(f"Price fell below ${price['price']:.2f}")
        elif price['price'] <= current_price and price['type'] == 'above':
            triggered_alerts.append(f"Price rose above ${price['price']:.2f}")
    return triggered_alerts

def main():
    # Set page config
    st.set_page_config(page_title="Gold Price Tracker", layout="wide")
    
    # Initialize session state for alerts
    if 'price_alerts' not in st.session_state:
        st.session_state.price_alerts = []
    
    # Title
    st.title("📈 Gold Price Tracker")
    
    # Timeframe selector
    timeframe_options = {
        '1 Week': 7,
        '1 Month': 30,
        '3 Months': 90,
        '6 Months': 180,
        '1 Year': 365
    }
    selected_timeframe = st.selectbox('Select Timeframe', list(timeframe_options.keys()))
    
    try:
        # Get data
        df = get_gold_data(timeframe_options[selected_timeframe])
        
        # Calculate metrics
        current_price, one_day_change, ten_day_change, month_change = calculate_price_changes(df)
        current_volume, avg_volume, volume_change, df = calculate_volume_metrics(df)
        
        # Price Alerts Section
        st.sidebar.header("Price Alerts")
        
        # Add new alert
        col1, col2 = st.sidebar.columns(2)
        alert_price = col1.number_input("Alert Price ($)", min_value=0.0, value=current_price)
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
            col1.write(f"${alert['price']:.2f} ({alert['type']})")
            if col2.button("Delete", key=f"delete_{idx}"):
                st.session_state.price_alerts.pop(idx)
                st.experimental_rerun()
        
        # Check for triggered alerts
        triggered_alerts = check_price_alerts(current_price, st.session_state.price_alerts)
        if triggered_alerts:
            for alert in triggered_alerts:
                st.warning(alert)
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current Gold Price (USD)",
                f"${current_price:.2f}",
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
        
        # Volume Analysis Section
        st.subheader("Volume Analysis")
        vol_col1, vol_col2, vol_col3 = st.columns(3)
        
        with vol_col1:
            st.metric(
                "Current Volume",
                f"{current_volume:,.0f}",
                delta=f"{volume_change:.2f}%"
            )
        
        with vol_col2:
            st.metric(
                "Average Volume",
                f"{avg_volume:,.0f}"
            )
        
        with vol_col3:
            volume_ratio = (current_volume / avg_volume - 1) * 100
            st.metric(
                "Volume vs Average",
                f"{volume_ratio:.2f}%",
                delta=f"{volume_ratio:.2f}%"
            )
        
        # Charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("Price Chart")
            st.line_chart(df['Close'])
        
        with chart_col2:
            st.subheader("Volume Chart")
            st.bar_chart(df['Volume'])
        
        # Technical Analysis
        st.subheader("Volume Moving Averages")
        st.line_chart(df[['Volume', 'Volume_MA5', 'Volume_MA20']])
        
        # Display raw data
        st.subheader("Historical Data")
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try refreshing the page.")

if __name__ == "__main__":
    main()
