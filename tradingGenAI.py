# Creating a stock network tracker using stock data and Python
import yfinance as yf
import pandas as pd

import networkx as nx
import matplotlib.pyplot as plt

tickers = ["AMZN", "AAPL", "GOOGL", "MSFT", "TSLA", "META", "NVDA", "NFLX", "AMD"]
print(tickers)

market_data = yf.download(tickers, start="2026-08-01", end="2026-09-01")
#print(market_data)

closing_prices = market_data['Close']
daily_returns = closing_prices.pct_change()


#using pandas to calculate the correlation matrix
correlation_matrix = daily_returns.corr()
#print(correlation_matrix)

threshold = 0.3
edges = []

for i in range(len(correlation_matrix)):
    for j in range(i):
        stock1 = correlation_matrix.columns[i]
        stock2 = correlation_matrix.columns[j]
        correlation = correlation_matrix.iloc[i,j]

        if abs(correlation) > threshold:
            edges.append((stock1, stock2, correlation))

#print(edges)

edge_weights = []
for stock1, stock2, corr in edges:
    edge_weights.append(corr*5)

#Graph object
G = nx.Graph()
G.add_weighted_edges_from(edges)

# Position nodes using a layout
pos = nx.spring_layout(G, k=0.5)

nx.draw(G, pos, with_labels=True, width=edge_weights, node_size=2000, font_size=10)
plt.show()

