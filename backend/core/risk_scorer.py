import numpy as np
import networkx as nx


# -------------------------------------------------
# Individual Risk Components
# -------------------------------------------------
def compute_structural_risk(node_feats, patterns):
    risk = max(node_feats["in_degree"], node_feats["out_degree"])

    if patterns.get("fan_in"):
        risk = max(risk, 0.8)

    if patterns.get("fan_out"):
        risk = max(risk, 0.8)

    return min(risk, 1.0)


def compute_flow_risk(node_feats, patterns):
    # low imbalance = high pass-through risk
    risk = 1.0 - node_feats["flow_imbalance"]

    if patterns.get("mule_wallet"):
        risk = max(risk, 0.9)

    return min(risk, 1.0)


def compute_temporal_risk(node_feats, patterns):
    # short activity span = high risk
    risk = 1.0 - node_feats["active_time_span"]

    if patterns.get("peeling_chain") or patterns.get("multi_hop_convergence"):
        risk = max(risk, 0.8)

    return min(risk, 1.0)


def compute_proximity_risk(G, suspicious_wallets, wallet, max_hops=3):
    for s in suspicious_wallets:
        if wallet == s:
            return 1.0
        try:
            d = nx.shortest_path_length(G, wallet, s)
            if d <= max_hops:
                return 1.0 / (d + 1)
        except nx.NetworkXNoPath:
            continue

    return 0.0


# -------------------------------------------------
# Base Risk Aggregation
# -------------------------------------------------
def compute_base_risk(
    G,
    node_features,
    pattern_results,
    weights=(0.35, 0.30, 0.20, 0.15),
):
    base_risks = {}

    suspicious_wallets = {
        w for w, p in pattern_results.items()
        if any(v is True for k, v in p.items() if not k.endswith("_reason"))
    }

    for wallet, feats in node_features.items():
        patterns = pattern_results.get(wallet, {})

        structural = compute_structural_risk(feats, patterns)
        flow = compute_flow_risk(feats, patterns)
        temporal = compute_temporal_risk(feats, patterns)
        proximity = compute_proximity_risk(G, suspicious_wallets, wallet)

        base_risk = (
            weights[0] * structural +
            weights[1] * flow +
            weights[2] * temporal +
            weights[3] * proximity
        )

        reasons = []
        if structural > 0.7:
            reasons.append("Suspicious transaction structure (fan-in / fan-out)")
        if flow > 0.7:
            reasons.append("Pass-through money flow behavior")
        if temporal > 0.7:
            reasons.append("Highly coordinated transaction timing")
        if proximity > 0.0:
            reasons.append("Close proximity to suspicious wallets")

        base_risks[wallet] = {
            "base_risk": round(base_risk, 3),
            "structural_risk": round(structural, 3),
            "flow_risk": round(flow, 3),
            "temporal_risk": round(temporal, 3),
            "proximity_risk": round(proximity, 3),
            "reasons": reasons,
        }

    return base_risks
