import os
import sys

# Resolve backend path safely
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

# -------------------------------------------------
# Load data & build graph
# -------------------------------------------------
CSV_PATH = os.path.join(BASE_DIR, "data", "Refined_Ethereum_Transactions.csv")

df = load_transactions(CSV_PATH)
G = build_transaction_graph(df)

node_features = min_max_normalize(extract_node_features(G))
edge_features = min_max_normalize(extract_edge_features(G))

# -------------------------------------------------
# Run pattern detectors
# -------------------------------------------------
patterns = aggregate_patterns(
    detect_fan_out(node_features),
    detect_fan_in(node_features),
    detect_multi_hop_convergence(G),
    detect_peeling_chains(edge_features),
    detect_mule_wallets(node_features),
)

# -------------------------------------------------
# Pretty-print results
# -------------------------------------------------
print("\n=== Phase 3: Rule-Based Pattern Detection ===")

suspicious_count = 0

for wallet, flags in patterns.items():
    reasons = [
        v for k, v in flags.items()
        if k.endswith("_reason") and v is not None
    ]

    if reasons:
        suspicious_count += 1
        print(f"\nWallet: {wallet}")
        for r in reasons:
            print("  -", r)

# -------------------------------------------------
# Summary
# -------------------------------------------------
print("\n==========================================")
print(f"Total wallets analyzed   : {len(patterns)}")
print(f"Suspicious wallets found : {suspicious_count}")

if suspicious_count == 0:
    print("Note: Dataset is mostly benign (expected for real Ethereum data).")
