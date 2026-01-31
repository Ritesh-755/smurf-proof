import networkx as nx
import numpy as np


def extract_node_features(G: nx.DiGraph) -> dict:
    """
    Returns:
        node_features[node] = {
            in_degree,
            out_degree,
            total_inflow,
            total_outflow,
            flow_imbalance,
            tx_count,
            active_time_span
        }
    """
    node_features = {}

    for node in G.nodes():
        in_edges = list(G.in_edges(node, data=True))
        out_edges = list(G.out_edges(node, data=True))

        in_degree = len(in_edges)
        out_degree = len(out_edges)

        total_inflow = sum(e[2]["amount"] for e in in_edges)
        total_outflow = sum(e[2]["amount"] for e in out_edges)

        tx_count = in_degree + out_degree

        timestamps = [e[2]["timestamp"] for e in in_edges + out_edges]
        if timestamps:
            active_time_span = (max(timestamps) - min(timestamps)).total_seconds()
        else:
            active_time_span = 0.0

        flow_imbalance = abs(total_inflow - total_outflow) / (
            total_inflow + total_outflow + 1e-9
        )

        node_features[node] = {
            "in_degree": in_degree,
            "out_degree": out_degree,
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "flow_imbalance": flow_imbalance,
            "tx_count": tx_count,
            "active_time_span": active_time_span,
        }

    return node_features


def extract_edge_features(G: nx.DiGraph) -> dict:
    """
    Returns:
        edge_features[(src, dst)] = {
            amount,
            time_delta,
            peeling_ratio
        }
    """
    edge_features = {}

    for u, v, data in G.edges(data=True):
        amount = data["amount"]
        timestamp = data["timestamp"]

        # Compute time delta from previous outgoing tx of u
        prev_times = [
            d["timestamp"]
            for _, _, d in G.out_edges(u, data=True)
            if d["timestamp"] < timestamp
        ]

        if prev_times:
            time_delta = (timestamp - max(prev_times)).total_seconds()
        else:
            time_delta = 0.0

        # Peeling ratio: how much is passed forward
        incoming_amounts = [
            d["amount"] for _, _, d in G.in_edges(u, data=True)
        ]
        if incoming_amounts:
            peeling_ratio = amount / (max(incoming_amounts) + 1e-9)
        else:
            peeling_ratio = 1.0

        edge_features[(u, v)] = {
            "amount": amount,
            "time_delta": time_delta,
            "peeling_ratio": peeling_ratio,
        }

    return edge_features
