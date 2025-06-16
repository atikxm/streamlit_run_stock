import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta
import time
from plotly.subplots import make_subplots
import yfinance as yf

# Set page configuration
st.set_page_config(
    page_title="Real-Time Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
    }
    .stTextInput>div>div>input {
        padding: 10px;
        border-radius: 5px;
    }
    .stSelectbox>div>div>select {
        padding: 8px;
        border-radius: 5px;
    }
    .css-1aumxhk {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("📈 Real-Time Stock Market Dashboard")
st.markdown("""
    Track and visualize live stock market data with real-time updates.
    Select stocks from the sidebar to get started.
    """)

# Sidebar for user input
with st.sidebar:
    st.header("Dashboard Configuration")
    
    # Stock selection
    default_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX"]
    selected_stocks = st.multiselect(
        "Select stocks to track",
        default_stocks,
        default=default_stocks[:3]
    )
    
    # Timeframe selection
    timeframe = st.selectbox(
        "Select timeframe",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=2
    )
    
    # Update frequency
    update_freq = st.selectbox(
        "Update frequency (seconds)",
        [10, 30, 60, 300],
        index=1
    )
    
    # Technical indicators
    st.subheader("Technical Indicators")
    show_sma = st.checkbox("Show Simple Moving Average (SMA)", value=True)
    sma_period = st.slider("SMA Period", 5, 50, 20, disabled=not show_sma)
    
    show_rsi = st.checkbox("Show Relative Strength Index (RSI)", value=True)
    rsi_period = st.slider("RSI Period", 5, 30, 14, disabled=not show_rsi)
    
    show_macd = st.checkbox("Show MACD", value=False)
    
    # Display options
    st.subheader("Display Options")
    dark_mode = st.checkbox("Dark Mode", value=False)
    chart_style = st.selectbox("Chart Style", ["line", "candle"], index=0)

# Function to fetch stock data
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_stock_data(tickers, period):
    data = yf.download(tickers, period=period, group_by='ticker', progress=False)
    return data

# Function to calculate technical indicators
def calculate_technical_indicators(df, ticker, sma_period=20, rsi_period=14):
    if ticker not in df.columns.get_level_values(0):
        return None
    
    stock_df = df[ticker].copy()
    
    # Calculate SMA
    if show_sma:
        stock_df['SMA'] = stock_df['Close'].rolling(window=sma_period).mean()
    
    # Calculate RSI
    if show_rsi:
        delta = stock_df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        
        rs = avg_gain / avg_loss
        stock_df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate MACD
    if show_macd:
        exp12 = stock_df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = stock_df['Close'].ewm(span=26, adjust=False).mean()
        stock_df['MACD'] = exp12 - exp26
        stock_df['Signal'] = stock_df['MACD'].ewm(span=9, adjust=False).mean()
    
    return stock_df

# Function to create stock chart
def create_stock_chart(stock_df, ticker, chart_style="line", dark_mode=False):
    if stock_df is None:
        return None
    
    # Create subplots
    rows = 1
    if show_rsi:
        rows += 1
    if show_macd:
        rows += 1
    
    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f"{ticker} Price", "RSI", "MACD")[:rows]
    )
    
    # Price chart
    if chart_style == "line":
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['Close'],
                name='Close Price',
                line=dict(color='#4CAF50'),
                mode='lines'
            ),
            row=1, col=1
        )
    else:  # candle chart
        fig.add_trace(
            go.Candlestick(
                x=stock_df.index,
                open=stock_df['Open'],
                high=stock_df['High'],
                low=stock_df['Low'],
                close=stock_df['Close'],
                name='OHLC',
                increasing_line_color='#4CAF50',
                decreasing_line_color='#F44336'
            ),
            row=1, col=1
        )
    
    # Add SMA
    if show_sma and 'SMA' in stock_df.columns:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['SMA'],
                name=f'SMA {sma_period}',
                line=dict(color='#FF9800', width=1.5),
                mode='lines'
            ),
            row=1, col=1
        )
    
    # Add RSI
    if show_rsi and 'RSI' in stock_df.columns:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['RSI'],
                name='RSI',
                line=dict(color='#2196F3'),
                mode='lines'
            ),
            row=2, col=1
        )
        fig.add_hline(y=70, row=2, col=1, line=dict(color="#F44336", width=1, dash="dash"))
        fig.add_hline(y=30, row=2, col=1, line=dict(color="#4CAF50", width=1, dash="dash"))
    
    # Add MACD
    if show_macd and 'MACD' in stock_df.columns and 'Signal' in stock_df.columns:
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['MACD'],
                name='MACD',
                line=dict(color='#2196F3'),
                mode='lines'
            ),
            row=3 if show_rsi else 2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=stock_df.index,
                y=stock_df['Signal'],
                name='Signal',
                line=dict(color='#FF9800'),
                mode='lines'
            ),
            row=3 if show_rsi else 2, col=1
        )
    
    # Update layout
    fig.update_layout(
        height=600 if rows == 1 else 800,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='black' if not dark_mode else 'white'),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    if dark_mode:
        fig.update_layout(
            paper_bgcolor='rgb(30, 30, 30)',
            plot_bgcolor='rgb(30, 30, 30)',
            font=dict(color='white')
        )
    
    return fig

# Function to display stock summary
def display_stock_summary(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Price", f"${info.get('currentPrice', info.get('regularMarketPrice', 'N/A')):,.2f}")
            st.metric("52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A'):,.2f}")
            st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A'):,.2f}")
        
        with col2:
            st.metric("Previous Close", f"${info.get('previousClose', 'N/A'):,.2f}")
            st.metric("52 Week Low", f"${info.get('fiftyTwoWeekLow', 'N/A'):,.2f}")
            st.metric("Market Cap", f"${info.get('marketCap', 'N/A')/1e9:,.2f}B")
        
        with col3:
            st.metric("Open", f"${info.get('open', 'N/A'):,.2f}")
            st.metric("Volume", f"{info.get('volume', 'N/A'):,}")
            st.metric("Beta", f"{info.get('beta', 'N/A'):,.2f}")
        
    except Exception as e:
        st.error(f"Could not fetch summary data for {ticker}: {str(e)}")

# Main dashboard
placeholder = st.empty()
last_update_time = st.empty()

while True:
    with placeholder.container():
        if not selected_stocks:
            st.warning("Please select at least one stock from the sidebar.")
        else:
            # Get stock data
            stock_data = get_stock_data(selected_stocks, timeframe)
            
            # Display each stock
            for i, ticker in enumerate(selected_stocks):
                st.markdown(f"### {ticker} - {yf.Ticker(ticker).info.get('longName', '')}")
                
                # Display summary metrics
                display_stock_summary(ticker)
                
                # Calculate indicators and create chart
                stock_df = calculate_technical_indicators(
                    stock_data, ticker, sma_period, rsi_period
                )
                fig = create_stock_chart(stock_df, ticker, chart_style, dark_mode)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Could not display chart for {ticker}")
                
                if i < len(selected_stocks) - 1:
                    st.markdown("---")
        
        # Display last update time
        last_update_time.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait for the specified interval before updating
    time.sleep(update_freq)