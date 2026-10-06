# Stockwork

An interactive web app for exploring how stocks move together. Stockwork turns
historical price data into a correlation network and can add concise AI-generated
company context.

## Overview
Stockwork downloads historical prices, calculates correlations between daily
returns, and draws a network where each node is an equity. Green connections
show stocks that moved together; coral connections show stocks that moved in
opposite directions. Wider connections indicate a stronger correlation.

The optional company context feature uses the Anthropic API to generate a short
plain-English introduction to each company and common factors that can move its
stock. It is based on model knowledge rather than live news.

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
5. Launch the local web app:
   `streamlit run interactive_networkGenAI.py`


## Live app

https://stockwork-ibfna6kakk7mpsybxhtndb.streamlit.app/
