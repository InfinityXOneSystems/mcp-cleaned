from fastapi import APIRouter, Query
from datetime import datetime, timedelta
import os, json

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# available systems
SYSTEMS = ["prediction", "real_estate", "loan"]

@router.get("/data")
async def get_dashboard_data(system: str = Query("all", description="Filter by system: prediction|real_estate|loan|all")):
    """
    Returns KPIs, recent inferences and simple aggregates.
    Use 'system' query param to scope data.
    """
    now = datetime.utcnow()

    # base mock KPIs per system
    base = {
        "prediction": [
            {"label":"Predictions Active","value": 24, "delta":"+4%"},
            {"label":"Avg Confidence","value":"81%","delta":"+2%"},
            {"label":"Model Runs Today","value": 12, "delta":"+20%"},
        ],
        "real_estate": [
            {"label":"Listings Monitored","value": 128, "delta":"-1%"},
            {"label":"Avg Valuation Certainty","value":"74%","delta":"-3%"},
            {"label":"New Leads","value": 18, "delta":"+8%"},
        ],
        "loan": [
            {"label":"Applications Active","value": 46, "delta":"+7%"},
            {"label":"Avg Risk Score","value":"62%","delta":"-2%"},
            {"label":"Approvals Today","value": 9, "delta":"+12%"},
        ],
    }

    # timeline mock (confidence/time)
    timeline = []
    for i in range(10):
        timeline.append({"ts": (now - timedelta(minutes=10*(9-i))).isoformat()+"Z", "confidence": 0.55 + i*0.04})

    # by_category sample - adjusted per system
    by_category_map = {
        "prediction": {"demand": 8, "supply": 6, "trend": 10},
        "real_estate": {"residential": 60, "commercial": 40, "valuation": 28},
        "loan": {"auto": 18, "mortgage": 12, "personal": 16},
    }

    # recent inferences (mock)
    recent_map = {
        "prediction": [
            {"created_at": (now - timedelta(minutes=5)).isoformat()+"Z", "agent":"predictor", "summary":"Short-term demand increase", "confidence":0.82},
            {"created_at": (now - timedelta(minutes=20)).isoformat()+"Z", "agent":"validator", "summary":"Model drift observed", "confidence":0.68},
        ],
        "real_estate": [
            {"created_at": (now - timedelta(minutes=8)).isoformat()+"Z", "agent":"ingestor", "summary":"New MLS feed ingested", "confidence":0.91},
            {"created_at": (now - timedelta(minutes=26)).isoformat()+"Z", "agent":"organizer", "summary":"Cluster: suburban rental growth", "confidence":0.79},
        ],
        "loan": [
            {"created_at": (now - timedelta(minutes=12)).isoformat()+"Z", "agent":"predictor", "summary":"Higher default risk in cohort X", "confidence":0.74},
            {"created_at": (now - timedelta(minutes=35)).isoformat()+"Z", "agent":"validator", "summary":"Verification pending for 3 apps", "confidence":0.66},
        ],
    }

    if system == "all":
        # aggregate overview (simple merge)
        kpis = [
            {"label":"Active Signals","value": 42, "delta":"+6%"},
            {"label":"Avg Confidence","value":"79%","delta":"-1%"},
            {"label":"New Items","value": 43, "delta":"+13%"},
        ]
        by_category = {"prediction":24, "real_estate":128, "loan":46}
        recent = sum([v for v in recent_map.values()], [])
    else:
        kpis = base.get(system, [])
        by_category = by_category_map.get(system, {})
        recent = recent_map.get(system, [])

    return {
        "updated_at": now.isoformat()+"Z",
        "systems": SYSTEMS,
        "system": system,
        "kpis": kpis,
        "timeline": timeline,
        "by_category": by_category,
        "recent": recent
    }

# Optional Firestore integration hint (commented):
# from omni_gateway import init_firestore
# db = init_firestore()
# docs = db.collection('mcp_memory').order_by('created_at', direction=firestore.Query.DESCENDING).limit(25).stream()
# transform docs into 'recent' list above.
# In production, replace mocks with Firestore queries filtering on a 'system' field in mcp_memory documents.
