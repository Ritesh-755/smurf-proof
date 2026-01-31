import numpy as np


def prepare_gnn_data(
    G,
    node_features,
    base_risks,
    edge_features,
):
    """
    Prepares NumPy-based GNN inputs.
    NO torch, NO torch-geometric.
    """

    # ----------------------------------
    # 1. Node index mapping
    # ----------------------------------
    wallets = list(G.nodes())
    wallet_to_idx = {w: i for i, w in enumerate(wallets)}
    idx_to_wallet = {i: w for w, i in wallet_to_idx.items()}

    # ----------------------------------
    # 2. Node feature matrix X
    # ----------------------------------
    X = np.zeros((len(wallets), 12), dtype=np.float32)

    for wallet, idx in wallet_to_idx.items():
        nf = node_features[wallet]
        br = base_risks[wallet]

        X[idx] = [
            nf["in_degree"],
            nf["out_degree"],
            nf["total_inflow"],
            nf["total_outflow"],
            nf["flow_imbalance"],
            nf["tx_count"],
            nf["active_time_span"],
            br["structural_risk"],
            br["flow_risk"],
            br["temporal_risk"],
            br["proximity_risk"],
            br["base_risk"],
        ]

    # ----------------------------------
    # 3. Edge index & edge attributes
    # ----------------------------------
    src, dst = [], []
    edge_attr = []

    for (u, v), ef in edge_features.items():
        src.append(wallet_to_idx[u])
        dst.append(wallet_to_idx[v])

        edge_attr.append([
            ef["amount"],
            ef["time_delta"],
            ef["peeling_ratio"],
        ])

    edge_index = np.array([src, dst], dtype=np.int64)
    edge_attr = np.array(edge_attr, dtype=np.float32)

    return {
        "X": X,
        "edge_index": edge_index,
        "edge_attr": edge_attr,
        "wallet_to_idx": wallet_to_idx,
        "idx_to_wallet": idx_to_wallet,
    }
