import torch


class SimpleRiskGNN(torch.nn.Module):
    """
    CPU-only GNN for risk refinement.
    """

    def __init__(self, in_features):
        super().__init__()
        self.linear = torch.nn.Linear(in_features, 1)

    def forward(self, X, edge_index):
        """
        X: (N, F) node features
        edge_index: (2, E)
        """
        N = X.size(0)
        agg = torch.zeros_like(X)

        src, dst = edge_index

        # Message passing: mean aggregation
        for i in range(src.size(0)):
            agg[dst[i]] += X[src[i]]

        # Normalize by degree
        deg = torch.zeros(N, device=X.device)
        for d in dst:
            deg[d] += 1

        deg = deg.unsqueeze(1).clamp(min=1)
        agg = agg / deg

        # Linear projection → risk score
        out = self.linear(agg)
        return torch.sigmoid(out).squeeze()

def run_gnn_inference(gnn_data):
    """
    Runs CPU-only GNN inference.
    """
    X = torch.tensor(gnn_data["X"], dtype=torch.float32)
    edge_index = torch.tensor(gnn_data["edge_index"], dtype=torch.long)

    model = SimpleRiskGNN(X.shape[1])
    model.eval()

    with torch.no_grad():
        gnn_risk = model(X, edge_index)

    return gnn_risk.numpy()
