import os, sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from core.graph_builder import load_transactions, build_transaction_graph
from core.feature_extractor import extract_node_features, extract_edge_features
from core.normalizer import min_max_normalize
from core.pattern_detector import (
    detect_fan_out,
    detect_fan_in,
    detect_multi_hop_convergence,
    detect_peeling_chains,
    detect_mule_wallets,
    aggregate_patterns,
)
from core.risk_scorer import compute_base_risk
from core.gnn_preparer import prepare_gnn_data

CSV_PATH = os.path.join(BASE_DIR, "data", "Refined_Ethereum_Transactions.csv")

df = load_transactions(CSV_PATH)
G = build_transaction_graph(df)

node_feats = min_max_normalize(extract_node_features(G))
edge_feats = min_max_normalize(extract_edge_features(G))

patterns = aggregate_patterns(
    detect_fan_out(node_feats),
    detect_fan_in(node_feats),
    detect_multi_hop_convergence(G),
    detect_peeling_chains(edge_feats),
    detect_mule_wallets(node_feats),
)

base_risks = compute_base_risk(G, node_feats, patterns)

gnn_data = prepare_gnn_data(G, node_feats, base_risks, edge_feats)

print("X shape:", gnn_data["X"].shape)
print("edge_index shape:", gnn_data["edge_index"].shape)
print("edge_attr shape:", gnn_data["edge_attr"].shape)

print("\nSample node feature vector:")
print(gnn_data["X"][0])
