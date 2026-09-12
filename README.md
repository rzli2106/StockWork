# Quantitative Asset Correlation Network

## Overview
StockWork an interactive web application that visualizes the network
topology of financial assets. It downloads real market data, computes a correlation
matrix of daily returns, and renders a graph where nodes are equities and edges
represent statistically significant correlation between them (blue = move together,
red = move oppositely; thicker = stronger).

**Generative AI:** the app also calls the Claude API (Anthropic) to generate a short,
plain-English "what is this company and what tends to move it" blurb for every ticker
in the network, so the graph is readable even if you don't already know the names.

## Installation & Usage

1. Clone this repository:
   `git clone https://github.com/rzli2106/trading_network`
2. Navigate into the project directory:
   `cd trading_network`
3. Create a virtual environment and install dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Set up your Anthropic API key (needed for the AI Stock Context feature):
   ```
   cp .env.example .env
   ```
   then edit `.env` and paste in a real key from
   [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys).
   Without a key the app still runs and shows the correlation network — it just skips
   the AI section.
5. Launch the local web server:
   `streamlit run interactive_network.py`


## Streamlit
https://tradingnetworkgenai-ffpwxvbjfvc4zfapvih5gy.streamlit.app/