import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from core.graph_builder import load_transactions, build_transaction_graph
from core.feature_extractor import extract_node_features, extract_edge_features
from core.normalizer import min_max_normalize

CSV_PATH = os.path.join(BASE_DIR, "data", "Refined_Ethereum_Transactions.csv")

df = load_transactions(CSV_PATH)
G = build_transaction_graph(df)

node_features = extract_node_features(G)
edge_features = extract_edge_features(G)

norm_node_features = min_max_normalize(node_features)
norm_edge_features = min_max_normalize(edge_features)

sample_node = list(norm_node_features.keys())[0]
sample_edge = list(norm_edge_features.keys())[0]

print("Sample Node:", sample_node)
print("Normalized Node Features:", norm_node_features[sample_node])

print("\nSample Edge:", sample_edge)
print("Normalized Edge Features:", norm_edge_features[sample_edge])
