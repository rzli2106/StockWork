"""Interactive Stock Correlation Network Tracker.

Downloads recent price history for a set of tickers, builds a graph where an
edge connects two stocks whose daily returns are correlated above a
threshold, and calls the Claude API to generate a short, plain-English
"what's driving this stock" for each ticker so the network is easier
to read.
"""

import os

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Stock Network Tracker", layout="wide")
st.title("Stock Network Tracker")
st.caption(
    "Builds a correlation network from real price data, then uses Claude to "
    "explain what's likely driving each stock."
)


user_tickers = st.text_input(
    "Enter stock tickers separated by commas (ex: AMZN, AAPL, GOOGL):",
    "AAPL, MSFT, GOOGL, AMZN, TSLA",
)

seen = set()
tickers_list = []
for raw in user_tickers.split(","):
    ticker = raw.strip().upper()
    if ticker and ticker not in seen:
        seen.add(ticker)
        tickers_list.append(ticker)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", pd.to_datetime("2026-08-01"))
with col2:
    end_date = st.date_input("End date", pd.to_datetime("2026-09-01"))

threshold = st.slider("Select correlation threshold:", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

#caching the data
@st.cache_data(ttl=3600, show_spinner="Downloading price data...")
def get_closing_prices(tickers: list[str], start, end) -> pd.DataFrame:
    """Download data and return just the closing prices in one column"""
    data = yf.download(tickers, start=start, end=end, progress=False)
    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        closes = data["Close"]
    else:
        closes = data[["Close"]].rename(columns={"Close": tickers[0]})

    return closes.dropna(axis=1, how="all")


if len(tickers_list) < 2:
    st.warning("Please enter at least two stock tickers to generate a network.")
    st.stop()

try:
    closing_prices = get_closing_prices(tickers_list, start_date, end_date)
except Exception as exc:
    st.error(f"Couldn't download price data: {exc}")
    st.stop()

if closing_prices.empty:
    st.error("No price data came back for those tickers/date range. Check the symbols and dates.")
    st.stop()

missing = [t for t in tickers_list if t not in closing_prices.columns]
if missing:
    st.warning(f"No data for: {', '.join(missing)} (skipping them).")

available_tickers = list(closing_prices.columns)
if len(available_tickers) < 2:
    st.error("Need at least two tickers with valid data to build a network.")
    st.stop()

#correlation network
daily_returns = closing_prices.pct_change().dropna(how="all")
correlation_matrix = daily_returns.corr()

edges = []
for i in range(len(correlation_matrix)):
    for j in range(i):
        stock1 = correlation_matrix.columns[i]
        stock2 = correlation_matrix.columns[j]
        correlation = correlation_matrix.iloc[i, j]
        if pd.notna(correlation) and abs(correlation) > threshold:
            edges.append((stock1, stock2, correlation))

G = nx.Graph()
G.add_nodes_from(available_tickers) 
G.add_weighted_edges_from(edges)

st.subheader("Correlation Network")

if not edges:
    st.info("No pairs are correlated above that threshold yet — try lowering the slider.")
else:
    pos = nx.spring_layout(G, k=0.5, seed=42)
    fig, ax = plt.subplots(figsize=(10, 8))

    nx.draw_networkx_nodes(G, pos, node_size=1800, node_color="#89CFF0", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)

    drawn_edges = list(G.edges(data="weight"))
    widths = [abs(w) * 6 for _, _, w in drawn_edges]
    colors = ["#1f77b4" if w >= 0 else "#d62728" for _, _, w in drawn_edges]
    nx.draw_networkx_edges(G, pos, width=widths, edge_color=colors, ax=ax)

    ax.axis("off")
    st.pyplot(fig)
    st.caption("Blue = positively correlated, red = negatively correlated. Thicker = stronger.")

with st.expander("Correlation matrix"):
    st.dataframe(correlation_matrix.style.format("{:.2f}"))


st.subheader("AI Stock Context")
st.caption(
    "For each ticker, ask for a quick plain-English take on the company and what's "
    "generally been moving it. This comes from the model's own knowledge, not a live news "
    "feed, so treat it as a starting point, not up-to-the-minute news."
)


def get_anthropic_client():
    """Look for an API key in Streamlit secrets first (for Community Cloud), then env."""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        # st.secrets raises if no secrets.toml exists at all (e.g. local dev with just a .env)
        api_key = None
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    from anthropic import Anthropic

    return Anthropic(api_key=api_key)


@st.cache_data(ttl=86400, show_spinner=False)
def get_ai_stock_context(ticker: str) -> str:
    client = get_anthropic_client()
    if client is None:
        return ""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=220,
        messages=[
            {
                "role": "user",
                "content": (
                    f"In 3-4 short sentences, explain what {ticker} is as a company "
                    "(sector + what it does) and, generally, what kinds of things tend to "
                    "move its stock (e.g. earnings, product launches, macro factors, "
                    "competition). Keep it factual and concise, no bullet points."
                ),
            }
        ],
    )
    return message.content[0].text


client_available = get_anthropic_client() is not None

if not client_available:
    st.info(
        "No Anthropic API key found, so AI context is disabled. Add one to a `.env` file "
        "as `ANTHROPIC_API_KEY=sk-ant-...` (see `.env.example`) and rerun the app.",
    )
else:
    if st.button("Generate AI context for these tickers"):
        for ticker in available_tickers:
            with st.expander(f"🤖 {ticker}", expanded=False):
                try:
                    with st.spinner(f"Asking Claude about {ticker}..."):
                        st.write(get_ai_stock_context(ticker))
                except Exception as exc:
                    st.error(f"Claude API call failed for {ticker}: {exc}")
