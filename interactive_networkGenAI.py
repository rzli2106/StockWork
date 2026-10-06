"""Stockwork: an interactive stock correlation network and company context app."""

from datetime import date, timedelta
import os

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Stockwork | Market connections",
    page_icon="assets/stockwork-favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
      :root { --ink:#172b45; --muted:#64748b; --line:#e4eaf1; --paper:#f5f8fb; --teal:#087f8c; }
      html, body, [class*="css"] { font-family:'DM Sans', sans-serif; }
      .stApp { background:var(--paper); color:var(--ink); }
      [data-testid="stHeader"] { background:rgba(245,248,251,.9); }
      [data-testid="stMainBlockContainer"] { max-width:1320px; padding-top:2.2rem; padding-bottom:4rem; }
      [data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
      [data-testid="stSidebar"] > div:first-child { padding-top:1.4rem; }
      h1, h2, h3 { color:var(--ink); font-family:'Manrope', sans-serif; letter-spacing:-.035em; }
      h1 { font-size:2.2rem !important; font-weight:800 !important; }
      h2 { font-size:1.45rem !important; font-weight:700 !important; }
      h3 { font-size:1.08rem !important; font-weight:700 !important; }
      p, label, [data-testid="stCaptionContainer"] { color:var(--muted); }
      .brand-intro { margin:.25rem 0 1.5rem; color:#64748b; font-size:1rem; max-width:740px; line-height:1.6; }
      .eyebrow { color:var(--teal); text-transform:uppercase; font-weight:700; font-size:.72rem; letter-spacing:.13em; margin:.4rem 0 .55rem; }
      [data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:15px; padding:1rem 1.1rem; box-shadow:0 5px 18px rgba(23,43,69,.025); }
      [data-testid="stMetricLabel"] p { color:#738197; font-size:.78rem; font-weight:600; }
      [data-testid="stMetricValue"] { color:var(--ink); font-family:'Manrope',sans-serif; font-size:1.7rem; font-weight:800; }
      .stButton > button { border-radius:10px; border:0; background:#087f8c; color:white; font-weight:700; min-height:2.8rem; }
      .stButton > button:hover { background:#066a76; color:white; }
      [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
      [data-testid="stAlert"] { border-radius:12px; }
      hr { border-color:var(--line); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.image("assets/stockwork-logo.svg", width=245)
st.markdown('<div class="eyebrow">A clearer view of market relationships</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="brand-intro">Explore how stocks move together. Build a correlation network from historical returns, then add concise company context to make the connections easier to understand.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Build your network")
    st.caption("Choose symbols and a history window to explore.")
    user_tickers = st.text_area(
        "Stock symbols",
        "AAPL, MSFT, GOOGL, AMZN, TSLA",
        height=90,
        help="Separate symbols with commas.",
    )
    today = date.today()
    start_date = st.date_input("From", value=today - timedelta(days=365))
    end_date = st.date_input("To", value=today)
    threshold = st.slider(
        "Minimum correlation",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
        help="A connection appears when the absolute correlation exceeds this value.",
    )
    st.markdown("---")
    st.caption("Positive links show stocks that tended to move together. Negative links show stocks that tended to move in opposite directions.")

seen = set()
tickers_list = []
for raw in user_tickers.split(","):
    ticker = raw.strip().upper()
    if ticker and ticker not in seen:
        seen.add(ticker)
        tickers_list.append(ticker)

if start_date >= end_date:
    st.error("Choose a start date that comes before the end date.")
    st.stop()
if len(tickers_list) < 2:
    st.warning("Enter at least two stock symbols to build a network.")
    st.stop()


@st.cache_data(ttl=3600, show_spinner="Downloading price history…")
def get_closing_prices(tickers: list[str], start, end) -> pd.DataFrame:
    """Download daily closing prices and normalize yfinance's column formats."""
    data = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        closes = data["Close"]
    else:
        closes = data[["Close"]].rename(columns={"Close": tickers[0]})
    return closes.dropna(axis=1, how="all")


try:
    closing_prices = get_closing_prices(tickers_list, start_date, end_date + timedelta(days=1))
except Exception as exc:
    st.error(f"Could not download price data: {exc}")
    st.stop()

if closing_prices.empty:
    st.error("No price data was returned for those symbols and dates. Check the symbols and try another date range.")
    st.stop()

missing = [ticker for ticker in tickers_list if ticker not in closing_prices.columns]
if missing:
    st.warning(f"No price data for {', '.join(missing)}; those symbols were skipped.")
available_tickers = list(closing_prices.columns)
if len(available_tickers) < 2:
    st.error("At least two symbols need valid price history to build a network.")
    st.stop()

daily_returns = closing_prices.pct_change().dropna(how="all")
correlation_matrix = daily_returns.corr()
edges = []
for i in range(len(correlation_matrix)):
    for j in range(i):
        correlation = correlation_matrix.iloc[i, j]
        if pd.notna(correlation) and abs(correlation) >= threshold:
            edges.append((correlation_matrix.columns[i], correlation_matrix.columns[j], correlation))

graph = nx.Graph()
graph.add_nodes_from(available_tickers)
graph.add_weighted_edges_from(edges)

positive_count = sum(weight >= 0 for _, _, weight in edges)
negative_count = len(edges) - positive_count
observations = len(daily_returns)

st.markdown('<div class="eyebrow">Your market snapshot</div>', unsafe_allow_html=True)
metric_cols = st.columns(4)
metric_cols[0].metric("Symbols", len(available_tickers))
metric_cols[1].metric("Connections", len(edges))
metric_cols[2].metric("Positive links", positive_count)
metric_cols[3].metric("Trading days", observations)
st.caption(f"{start_date:%b %d, %Y} – {end_date:%b %d, %Y} · Adjusted daily returns · Correlation threshold {threshold:.2f}")

st.markdown("## Correlation network")
if not edges:
    st.info("No stock pairs meet this threshold. Lower the minimum correlation in the sidebar to reveal more connections.")
else:
    positions = nx.spring_layout(graph, k=0.7, seed=42, weight="weight")
    fig, ax = plt.subplots(figsize=(12, 7.2), facecolor="#ffffff")
    ax.set_facecolor("#ffffff")
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        edgelist=[(a, b) for a, b, _ in edges],
        width=[1.4 + abs(weight) * 5 for _, _, weight in edges],
        edge_color=["#0c9b83" if weight >= 0 else "#e4776d" for _, _, weight in edges],
        alpha=0.68,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=ax,
        node_size=1850,
        node_color="#183653",
        edgecolors="#ffffff",
        linewidths=2.5,
    )
    nx.draw_networkx_labels(
        graph,
        positions,
        ax=ax,
        font_size=9,
        font_weight="bold",
        font_color="#ffffff",
        font_family="DejaVu Sans",
    )
    ax.margins(0.17)
    ax.axis("off")
    fig.tight_layout(pad=1)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.markdown("🟢 **Positive** · stocks tended to move together　　🔴 **Negative** · stocks tended to move in opposite directions　　Line width reflects strength")
with st.expander("View correlation matrix"):
    st.dataframe(correlation_matrix.style.format("{:.2f}"), use_container_width=True)

st.markdown("## Company context")
st.markdown(
    "Short, AI-generated introductions to each company and the forces that can move its stock. Context is based on model knowledge, not a live news feed."
)


def get_anthropic_client():
    """Read the API key from Streamlit secrets or the local environment."""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
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
                    "(sector and what it does) and what kinds of things generally move "
                    "its stock (such as earnings, product launches, macro factors, or "
                    "competition). Keep it factual and concise, with no bullets."
                ),
            }
        ],
    )
    return message.content[0].text


if get_anthropic_client() is None:
    st.info("AI context is unavailable because no Anthropic API key was found. Add `ANTHROPIC_API_KEY` to Streamlit secrets or your `.env` file to enable it.")
elif st.button("Generate company context"):
    for ticker in available_tickers:
        with st.expander(ticker, expanded=False):
            try:
                with st.spinner(f"Writing context for {ticker}…"):
                    st.write(get_ai_stock_context(ticker))
            except Exception as exc:
                st.error(f"Could not generate context for {ticker}: {exc}")
