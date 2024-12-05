import yfinance as yf
import streamlit as st
import datetime
import pandas as pd
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="Stock Analysis",
    layout="wide"
)

# Sidebar
st.sidebar.header("Stock Parameters")

# Stock selection
ticker = st.sidebar.text_input(
    "Enter Stock Symbol",
    value="AAPL"
)

# Date selection
start_date = st.sidebar.date_input(
    "Start Date",
    datetime.date(2023, 1, 1)
)
end_date = st.sidebar.date_input(
    "End Date",
    datetime.date.today()
)

# Technical indicators
show_sma = st.sidebar.checkbox("Show SMA")
sma_period = st.sidebar.number_input("SMA Period", value=20, min_value=1, max_value=100)
show_volume = st.sidebar.checkbox("Show Volume")

# Main app
st.title("Stock Technical Analysis")

# Download data
@st.cache_data
def load_data(symbol, start, end):
    try:
        df = yf.download(symbol, start, end)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data
df = load_data(ticker, start_date, end_date)

if df is not None and not df.empty:
    # Create figure
    fig = go.Figure()
    
    # Add candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC'
        )
    )
    
    # Add SMA if selected
    if show_sma:
        sma = df['Close'].rolling(window=sma_period).mean()
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=sma,
                name=f'SMA {sma_period}',
                line=dict(color='orange')
            )
        )
    
    # Update layout
    fig.update_layout(
        title=f'{ticker} Stock Price',
        yaxis_title='Price',
        xaxis_title='Date',
        height=600
    )
    
    # Display chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Display volume chart if selected
    if show_volume:
        volume_fig = go.Figure()
        volume_fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume'
            )
        )
        volume_fig.update_layout(
            title='Trading Volume',
            yaxis_title='Volume',
            xaxis_title='Date',
            height=300
        )
        st.plotly_chart(volume_fig, use_container_width=True)
    
    # Display raw data
    with st.expander("Show Raw Data"):
        st.dataframe(df)
else:
    st.error("No data available for the selected stock and date range.")
