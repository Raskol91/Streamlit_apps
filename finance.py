import yfinance as yf
import streamlit as st
import datetime
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

# Configure page settings
st.set_page_config(
    page_title="Stock Technical Analysis",
    page_icon="📈",
    layout="wide"
)

# Cache functions for better performance
@st.cache_data
def get_sp500_components():
    """Get S&P 500 components from Wikipedia"""
    try:
        df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = df[0]
        tickers = df["Symbol"].to_list()
        tickers_companies_dict = dict(zip(df["Symbol"], df["Security"]))
        return tickers, tickers_companies_dict
    except Exception as e:
        st.error(f"Error fetching S&P 500 components: {str(e)}")
        return [], {}

@st.cache_data
def load_data(symbol, start, end):
    """Load stock data from Yahoo Finance"""
    try:
        return yf.download(symbol, start, end)
    except Exception as e:
        st.error(f"Error downloading data for {symbol}: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def convert_df_to_csv(df):
    """Convert dataframe to CSV format"""
    return df.to_csv().encode("utf-8")

# Technical Analysis Functions
def calculate_sma(data, periods):
    """Calculate Simple Moving Average"""
    return data['Close'].rolling(window=periods).mean()

def calculate_bollinger_bands(data, periods, std_dev):
    """Calculate Bollinger Bands"""
    sma = data['Close'].rolling(window=periods).mean()
    std = data['Close'].rolling(window=periods).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, lower_band

def calculate_rsi(data, periods):
    """Calculate Relative Strength Index"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Sidebar configuration
st.sidebar.header("Stock Parameters")

# Get S&P 500 components
available_tickers, tickers_companies_dict = get_sp500_components()

# Stock selection
ticker = st.sidebar.selectbox(
    "Select Stock",
    available_tickers,
    format_func=lambda x: f"{x} - {tickers_companies_dict.get(x, '')}"
)

# Date selection
start_date = st.sidebar.date_input(
    "Start Date",
    datetime.date(2019, 1, 1)
)
end_date = st.sidebar.date_input(
    "End Date",
    datetime.date.today()
)

if start_date > end_date:
    st.sidebar.error("End date must be after start date")
    st.stop()

# Technical Analysis Parameters
st.sidebar.header("Technical Analysis Parameters")

# Volume
volume_flag = st.sidebar.checkbox("Show Volume")

# SMA
exp_sma = st.sidebar.expander("Simple Moving Average (SMA)")
sma_flag = exp_sma.checkbox("Add SMA")
sma_periods = exp_sma.number_input(
    "SMA Periods",
    min_value=1,
    max_value=50,
    value=20,
    step=1
)

# Bollinger Bands
exp_bb = st.sidebar.expander("Bollinger Bands")
bb_flag = exp_bb.checkbox("Add Bollinger Bands")
bb_periods = exp_bb.number_input(
    "BB Periods",
    min_value=1,
    max_value=50,
    value=20,
    step=1
)
bb_std = exp_bb.number_input(
    "Standard Deviations",
    min_value=1,
    max_value=4,
    value=2,
    step=1
)

# RSI
exp_rsi = st.sidebar.expander("Relative Strength Index")
rsi_flag = exp_rsi.checkbox("Add RSI")
rsi_periods = exp_rsi.number_input(
    "RSI Periods",
    min_value=1,
    max_value=50,
    value=14,
    step=1
)
rsi_upper = exp_rsi.number_input(
    "RSI Upper",
    min_value=50,
    max_value=90,
    value=70,
    step=1
)
rsi_lower = exp_rsi.number_input(
    "RSI Lower",
    min_value=10,
    max_value=50,
    value=30,
    step=1
)

# Main app
st.title("Stock Technical Analysis Dashboard")
st.markdown("""
### Features
* Select any company from S&P 500
* Customize technical indicators
* Download historical data
* Interactive charts
""")

# Load data
df = load_data(ticker, start_date, end_date)

if df.empty:
    st.warning("No data available for the selected stock and date range.")
    st.stop()

# Data preview section
data_exp = st.expander("Preview Data")
available_cols = df.columns.tolist()
columns_to_show = data_exp.multiselect(
    "Select Columns",
    available_cols,
    default=available_cols
)

if columns_to_show:
    data_exp.dataframe(df[columns_to_show])
    
    # Download button
    csv_file = convert_df_to_csv(df[columns_to_show])
    data_exp.download_button(
        "Download Selected Data (CSV)",
        csv_file,
        f"{ticker}_stock_prices.csv",
        "text/csv"
    )

# Create plots
fig = make_subplots(
    rows=3 if rsi_flag else (2 if volume_flag else 1),
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.6, 0.2, 0.2] if rsi_flag else ([0.7, 0.3] if volume_flag else [1])
)

# Main price plot
fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="OHLC"
    ),
    row=1, col=1
)

# Add SMA
if sma_flag:
    sma = calculate_sma(df, sma_periods)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=sma,
            name=f"SMA ({sma_periods})",
            line=dict(color='orange')
        ),
        row=1, col=1
    )

# Add Bollinger Bands
if bb_flag:
    upper_bb, lower_bb = calculate_bollinger_bands(df, bb_periods, bb_std)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=upper_bb,
            name=f"Upper BB ({bb_periods}, {bb_std}σ)",
            line=dict(color='gray', dash='dash')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=lower_bb,
            name=f"Lower BB ({bb_periods}, {bb_std}σ)",
            line=dict(color='gray', dash='dash'),
            fill='tonexty'
        ),
        row=1, col=1
    )

# Add Volume
if volume_flag:
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name="Volume",
            marker_color='rgb(158,202,225)'
        ),
        row=2, col=1
    )

# Add RSI
if rsi_flag:
    rsi = calculate_rsi(df, rsi_periods)
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=rsi,
            name=f"RSI ({rsi_periods})",
            line=dict(color='purple')
        ),
        row=3 if volume_flag else 2, col=1
    )
    # Add RSI levels
    fig.add_hline(
        y=rsi_upper,
        line_dash="dash",
        line_color="red",
        row=3 if volume_flag else 2
    )
    fig.add_hline(
        y=rsi_lower,
        line_dash="dash",
        line_color="green",
        row=3 if volume_flag else 2
    )

# Update layout
fig.update_layout(
    title=f"{tickers_companies_dict[ticker]} ({ticker}) Stock Analysis",
    xaxis_title="Date",
    yaxis_title="Price",
    height=800,
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)

# Display plot
st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and Yahoo Finance")
