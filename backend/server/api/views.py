import os
import tempfile
import time
import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.pipeline import run_full_analysis

# -------------------------------------------------
# Logging
# -------------------------------------------------
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# In-memory session cache this is done for being on the safe of the hackathon
# ----------------------------------------------------------------------------
ANALYSIS_CACHE = {}


# -------------------------------------------------
# Health Check
# -------------------------------------------------
@api_view(["GET"])
def health(request):
    return Response({"status": "API is running"})


# -------------------------------------------------
# CSV Upload (Phase 8.1 Hardened)
# -------------------------------------------------
@api_view(["POST"])
def upload_csv(request):
    file = request.FILES.get("file")

    if not file:
        return Response(
            {"error": "CSV file required"},
            status=400
        )

    MAX_FILE_SIZE_MB = 10

    if not file.name.lower().endswith(".csv"):
        return Response(
            {"error": "Only CSV files are supported"},
            status=400
        )

    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return Response(
            {"error": "CSV file too large (max 10MB)"},
            status=400
        )

    # Clean up old temp file if exists
    old_csv = ANALYSIS_CACHE.get("csv_path")
    if old_csv and os.path.exists(old_csv):
        try:
            os.remove(old_csv)
        except Exception:
            logger.warning("Failed to delete old CSV temp file")

    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp.close()

    except Exception as e:
        logger.exception("CSV save failed")
        return Response(
            {
                "error": "Failed to save uploaded CSV",
                "details": str(e)
            },
            status=500
        )

    ANALYSIS_CACHE.clear()
    ANALYSIS_CACHE["csv_path"] = tmp.name

    logger.info("CSV uploaded: %s", file.name)

    return Response({"message": "CSV uploaded successfully"})


# -------------------------------------------------
# Analysis Trigger (Phase 5.2 + Phase 8 Guardrails)
# -------------------------------------------------
@api_view(["POST"])
def analyze(request):
    csv_path = ANALYSIS_CACHE.get("csv_path")

    if not csv_path or not os.path.exists(csv_path):
        logger.warning("Analyze called without CSV")
        return Response(
            {"error": "No CSV uploaded. Upload CSV before analysis."},
            status=400
        )

    try:
        start = time.time()
        results = run_full_analysis(csv_path)
        duration = time.time() - start

        if duration > 5:
            logger.error("Analysis timeout: %.2fs", duration)
            return Response(
                {"error": "Analysis exceeded time limit"},
                status=500
            )

    except Exception as e:
        logger.exception("Analysis failed")
        return Response(
            {
                "error": "Analysis failed",
                "details": str(e)
            },
            status=500
        )

    ANALYSIS_CACHE["results"] = results
    logger.info("Analysis completed in %.2fs", duration)

    return Response({"message": "Analysis completed"})


# -------------------------------------------------
# Graph Endpoint
# -------------------------------------------------
@api_view(["GET"])
def get_graph(request):
    results = ANALYSIS_CACHE.get("results")

    if not results:
        return Response(
            {"error": "Run analysis before requesting graph."},
            status=400
        )

    G = results.get("graph")
    base_risks = results.get("base_risks", {})
    patterns = results.get("patterns", {})

    involved_wallets = {
        w for w, p in patterns.items()
        if any(v is True for k, v in p.items() if not k.endswith("_reason"))
    }

    nodes = []
    for node in G.nodes():
        risk_info = base_risks.get(node, {})
        risk = risk_info.get("base_risk", 0.0)

        is_wallet = node.startswith("0x")

        nodes.append({
            "id": node,
            "risk": risk,
            "is_risky": risk >= 0.5,
            "is_involved": node in involved_wallets,
            "entity_type": "wallet" if is_wallet else "service",
            "reasons": risk_info.get("reasons", []),
        })

    edges = []
    for u, v, data in G.edges(data=True):
        p = patterns.get(u, {})
        edges.append({
            "source": u,
            "target": v,
            "amount": data.get("amount", 0.0),
            "is_suspicious": p.get("fan_out", False) or p.get("peeling_chain", False),
            "pattern": (
                "smurfing" if p.get("fan_out")
                else "peeling" if p.get("peeling_chain")
                else None
            )
        })

    return Response({"nodes": nodes, "edges": edges})


# -------------------------------------------------
# Risk Scores Endpoint (Phase 5.4)
# -------------------------------------------------
@api_view(["GET"])
def get_risk_scores(request):
    results = ANALYSIS_CACHE.get("results")

    if not results:
        return Response(
            {"error": "Run analysis before requesting risk scores."},
            status=400
        )

    base_risks = results.get("base_risks", {})

    wallets = []
    for wallet, risk_info in base_risks.items():
        base = risk_info.get("base_risk", 0.0)

        wallets.append({
            "id": wallet,
            "base_risk": base,
            "structural_risk": risk_info.get("structural_risk", 0.0),
            "flow_risk": risk_info.get("flow_risk", 0.0),
            "temporal_risk": risk_info.get("temporal_risk", 0.0),
            "proximity_risk": risk_info.get("proximity_risk", 0.0),
            "is_risky": base >= 0.5,
            "entity_type": "wallet" if wallet.startswith("0x") else "service",
            "reasons": risk_info.get("reasons", []),
        })

    return Response({"wallets": wallets})


# -------------------------------------------------
# Final Risk Fusion (Phase 5.5 Optional)
# -------------------------------------------------
@api_view(["GET"])
def get_final_risk(request):
    results = ANALYSIS_CACHE.get("results")

    if not results:
        return Response(
            {"error": "Run analysis before requesting final risk."},
            status=400
        )

    base_risks = results.get("base_risks", {})
    gnn_risks = results.get("gnn_risks") or {}

    ALPHA = 0.6
    wallets = []

    for wallet, info in base_risks.items():
        base = info.get("base_risk", 0.0)
        gnn = gnn_risks.get(wallet, base)

        final = round(ALPHA * base + (1 - ALPHA) * gnn, 3)

        wallets.append({
            "id": wallet,
            "base_risk": base,
            "gnn_risk": round(gnn, 3),
            "final_risk": final,
            "delta": round(final - base, 3),
            "reasons": info.get("reasons", []),
        })

    return Response({
        "alpha": ALPHA,
        "gnn_enabled": bool(gnn_risks),
        "wallets": wallets
    })
