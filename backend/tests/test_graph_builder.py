import sys
import os

# Add backend/ to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.graph_builder import (
    load_transactions,
    build_transaction_graph,
    graph_summary,
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(BASE_DIR, "data", "Refined_Ethereum_Transactions.csv")

df = load_transactions(CSV_PATH)
graph = build_transaction_graph(df)

summary = graph_summary(graph)
print("Graph Summary:", summary)

# Inspect a random edge
u, v, data = list(graph.edges(data=True))[0]
print("Sample Edge:")
print(u, "→", v)
print(data)
