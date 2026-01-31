import pandas as pd
import networkx as nx
from datetime import datetime

REQUIRED_COLUMNS = {
    "Source_Wallet_ID",
    "Dest_Wallet_ID",
    "Timestamp",
    "Amount",
    "Token_Type",
}


def load_transactions(csv_path: str) -> pd.DataFrame:
    """
    Load and validate the transaction CSV.
    """
    df = pd.read_csv(csv_path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Basic type cleaning
    df["Amount"] = df["Amount"].astype(float)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    return df


def build_transaction_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Build a directed transaction graph from a DataFrame.
    """
    G = nx.DiGraph()

    for _, row in df.iterrows():
        src = row["Source_Wallet_ID"]
        dst = row["Dest_Wallet_ID"]

        G.add_edge(
            src,
            dst,
            amount=row["Amount"],
            timestamp=row["Timestamp"],
            token_type=row["Token_Type"],
        )

    return G


def graph_summary(G: nx.DiGraph) -> dict:
    """
    Basic sanity stats for the graph.
    """
    return {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "num_isolated_nodes": len(list(nx.isolates(G))),
    }
