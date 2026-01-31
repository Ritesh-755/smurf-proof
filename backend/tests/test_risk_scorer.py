import os
import sys

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

print("\n=== Phase 4: Base Risk Scores ===")

for wallet, data in sorted(
    base_risks.items(),
    key=lambda x: x[1]["base_risk"],
    reverse=True
)[:5]:
    print(f"\nWallet: {wallet}")
    print("Base Risk:", data["base_risk"])
    for r in data["reasons"]:
        print("  -", r)
