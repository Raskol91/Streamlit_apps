import yfinance as yf
import streamlit as st
import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Stock Analysis",
    layout="wide"
)

# Sidebar
st.sidebar.header("Stock Parameters")

# Get S&P 500 components
@st.cache_data
def get_sp500_components():
    try:
        df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = df[0]
        tickers = df["Symbol"].to_list()
        tickers_companies_dict = dict(zip(df["Symbol"], df["Security"]))
        return tickers, tickers_companies_dict
    except Exception as e:
        st.error(f"Error fetching S&P 500 components: {str(e)}")
        return [], {}

# Get available tickers
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
    datetime.date(2023, 1, 1)
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

# Volume toggle
volume_flag = st.sidebar.checkbox("Show Volume")

# SMA
sma_expander = st.sidebar.expander("Simple Moving Average (SMA)")
sma_flag = sma_expander.checkbox("Add SMA")
sma_periods = sma_expander.number_input(
    "SMA Periods",
    min_value=1,
    max_value=50,
    value=20,
    step=1
)

# Bollinger Bands
bb_expander = st.sidebar.expander("Bollinger Bands")
bb_flag = bb_expander.checkbox("Add Bollinger Bands")
bb_periods = bb_expander.number_input(
    "BB Periods",
    min_value=1,
    max_value=50,
    value=20,
    step=1
)
bb_std = bb_expander.number_input(
    "Standard Deviations",
    min_value=1,
    max_value=4,
    value=2,
    step=1
)

# RSI
rsi_expander = st.sidebar.expander("Relative Strength Index")
rsi_flag = rsi_expander.checkbox("Add RSI")
rsi_periods = rsi_expander.number_input(
    "RSI Periods",
    min_value=1,
    max_value=50,
    value=14,
    step=1
)
rsi_upper = rsi_expander.number_input(
    "RSI Upper",
    min_value=50,
    max_value=90,
    value=70,
    step=1
)
rsi_lower = rsi_expander.number_input(
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

# Download data
@st.cache_data
def load_data(symbol, start, end):
    try:
        return yf.download(symbol, start, end)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Technical Analysis Functions
def calculate_sma(data, periods):
    return data['Close'].rolling(window=periods).mean()

def calculate_bollinger_bands(data, periods, std_dev):
    sma = data['Close'].rolling(window=periods).mean()
    std = data['Close'].rolling(window=periods).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, lower_band

def calculate_rsi(data, periods):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Load data
df = load_data(ticker, start_date, end_date)

if not df.empty:
    # Data preview section
    data_expander = st.expander("Preview Data")
    with data_expander:
        st.dataframe(df)
        
        # Download button
        csv = df.to_csv().encode('utf-8')
        st.download_button(
            "Download Data (CSV)",
            csv,
            f"{ticker}_stock_data.csv",
            "text/csv",
            key='download-csv'
        )

    # Create subplots
    row_heights = []
    specs = []
    if rsi_flag:
        row_heights = [0.6, 0.2, 0.2] if volume_flag else [0.7, 0.3]
        specs = [[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]] if volume_flag else [[{"secondary_y": True}], [{"secondary_y": False}]]
    elif volume_flag:
        row_heights = [0.7, 0.3]
        specs = [[{"secondary_y": True}], [{"secondary_y": False}]]
    else:
        row_heights = [1]
        specs = [[{"secondary_y": True}]]

    fig = make_subplots(
        rows=len(row_heights),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=row_heights,
        specs=specs
    )

    # Add candlestick chart
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
        colors = ['red' if row['Open'] - row['Close'] >= 0 
                 else 'green' for index, row in df.iterrows()]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name="Volume",
                marker_color=colors
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
        yaxis_title="Price",
        xaxis_title="Date",
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    if volume_flag:
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    if rsi_flag:
        fig.update_yaxes(title_text="RSI", row=3 if volume_flag else 2, col=1)

    # Show plot
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("No data available for the selected stock and date range.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and Yahoo Finance")
