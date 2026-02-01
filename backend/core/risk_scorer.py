import networkx as nx

# -------------------------------------------------
# AML Risk Component Thresholds
# -------------------------------------------------
FAN_OUT_THRESHOLD = 3
FAN_IN_THRESHOLD = 3
MIN_TX_TEMPORAL = 3
LOW_IMBALANCE_THRESHOLD = 0.2


# -------------------------------------------------
# Individual Risk Components (FIXED)
# -------------------------------------------------
def compute_structural_risk(node_feats, patterns):
    """
    Structural risk exists ONLY if fan-in or fan-out
    exceeds laundering thresholds.
    """
    if node_feats["out_degree"] >= FAN_OUT_THRESHOLD:
        return 1.0
    if node_feats["in_degree"] >= FAN_IN_THRESHOLD:
        return 1.0
    return 0.0


def compute_flow_risk(node_feats, patterns):
    """
    Flow risk exists ONLY for pass-through behavior:
    multiple incoming + outgoing with low imbalance.
    """
    incoming = node_feats.get("in_degree", 0)
    outgoing = node_feats.get("out_degree", 0)
    imbalance = node_feats.get("flow_imbalance", 1.0)

    if incoming >= 2 and outgoing >= 1 and imbalance <= LOW_IMBALANCE_THRESHOLD:
        return 1.0

    return 0.0


def compute_temporal_risk(node_feats, patterns):
    """
    Temporal risk exists ONLY when multiple transactions
    occur in a short time window.
    """
    tx_count = node_feats.get("tx_count", 0)
    time_span = node_feats.get("active_time_span", 1.0)

    if tx_count < MIN_TX_TEMPORAL:
        return 0.0

    # time_span is assumed normalized [0,1]
    if time_span <= 0.3:
        return 1.0

    return 0.0


def compute_proximity_risk(G, suspicious_wallets, wallet, max_hops=3):
    """
    Proximity risk propagates suspicion through the graph.
    """
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
# Base Risk Aggregation (GATED)
# -------------------------------------------------
def compute_base_risk(
    G,
    node_features,
    pattern_results,
    weights=(0.4, 0.3, 0.2, 0.1),
):
    """
    AML-grade base risk computation.

    RULE:
    - No structural OR flow anomaly → base_risk = 0
    """

    base_risks = {}

    suspicious_wallets = {
        w for w, p in pattern_results.items()
        if any(v is True for k, v in p.items() if not k.endswith("_reason"))
    }

    for wallet, feats in node_features.items():

        # Skip non-wallet entities
        if not wallet.startswith("0x"):
            continue

        patterns = pattern_results.get(wallet, {})

        structural = compute_structural_risk(feats, patterns)
        flow = compute_flow_risk(feats, patterns)

        # 🚨 HARD GATE (this fixes your issue)
        if structural == 0.0 and flow == 0.0:
            base_risk = 0.0
            temporal = 0.0
            proximity = 0.0
        else:
            temporal = compute_temporal_risk(feats, patterns)
            proximity = compute_proximity_risk(G, suspicious_wallets, wallet)

            base_risk = (
                weights[0] * structural +
                weights[1] * flow +
                weights[2] * temporal +
                weights[3] * proximity
            )

        base_risk = round(min(base_risk, 1.0), 3)

        reasons = []
        if structural:
            reasons.append("Suspicious transaction structure (fan-in / fan-out)")
        if flow:
            reasons.append("Pass-through money flow behavior")
        if temporal:
            reasons.append("Highly coordinated transaction timing")
        if proximity > 0:
            reasons.append("Close proximity to suspicious wallets")

        base_risks[wallet] = {
            "base_risk": base_risk,
            "structural_risk": structural,
            "flow_risk": flow,
            "temporal_risk": temporal,
            "proximity_risk": round(proximity, 3),
            "reasons": reasons,
        }

    return base_risks
