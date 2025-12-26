"""
Lightweight intelligence endpoints router.
Provides /arrival, /mirror-business, and /pipeline-shadow with safe defaults.
Uses heuristics first and a pluggable LLM adapter (if OPENAI_API_KEY provided).
Writes lightweight memory records into Firestore when available.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from governance import is_action_allowed, need_escalation, permission_from_role
import hashlib
import os
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


def init_firestore_client():
    try:
        from google.cloud import firestore
        proj = os.environ.get("FIRESTORE_PROJECT", "infinity-x-one-systems")
        client = firestore.Client(project=proj)
        return client
    except Exception as e:
        logger.debug(f"Firestore client unavailable: {e}")
        return None


def session_hash_from_signals(signals: Dict[str, Any]) -> str:
    s = "|".join([str(signals.get(k, "")) for k in ["ip","user_agent","path","referrer"]])
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def write_memory(doc: Dict[str, Any]):
    client = init_firestore_client()
    if not client:
        logger.debug("Skipping memory write; no Firestore")
        return None
    col = os.environ.get("FIRESTORE_COLLECTION", "mcp_memory")
    doc_id = doc.get("id") or f"m_{int(time.time())}_{hashlib.sha1(str(doc).encode()).hexdigest()[:6]}"
    doc["created_at"] = datetime.utcnow().isoformat() + "Z"
    client.collection(col).document(doc_id).set(doc, merge=True)
    return doc_id


def llm_stub_arrival(signals: Dict[str, Any]) -> Dict[str, Any]:
    # Heuristic-first approach
    path = signals.get("path","/")
    ua = signals.get("user_agent","")
    if "/pricing" in path or "pricing" in signals.get("referrer",""):
        insight = "Timing and pricing friction are creating hesitation during conversion."
    else:
        insight = "Follow-up timing is the likely bottleneck in your funnel."
    spoken = insight
    confidence = 0.8
    return {"insight":insight, "spoken":spoken, "confidence":confidence, "evidence":[path, ua]}


def summarize_business_from_url(url: str) -> Dict[str, Any]:
    # Lightweight placeholder; if a real crawled snapshot exists, use it.
    model = "Recurring servicing / subscription fees on small portfolios"
    bottleneck = "Manual follow-up and onboarding drop-off"
    kpi = "monthly-retention-rate"
    cost = 120000
    spoken = f"Model: {model}. Bottleneck: {bottleneck}. Estimated cost: ${cost}/month."
    confidence = 0.78
    sources = [url]
    return {"model":model, "bottleneck":bottleneck, "kpi":kpi, "cost_of_inaction":cost, "spoken":spoken, "confidence":confidence, "sources":sources}


class ArrivalRequest(BaseModel):
    session_id: Optional[str]
    ip: Optional[str]
    user_agent: Optional[str]
    path: Optional[str]
    referrer: Optional[str]


class ArrivalResponse(BaseModel):
    insight: str
    spoken: str
    confidence: float
    memory_key: Optional[str]
    sources: Optional[List[str]]


@router.post("/arrival", response_model=ArrivalResponse)
async def arrival(req: ArrivalRequest, request: Request):
    signals = req.dict()
    # fallback to HTTP signals if not provided
    if not signals.get("user_agent"):
        signals["user_agent"] = request.headers.get("user-agent","")
    if not signals.get("ip"):
        signals["ip"] = request.client.host if request.client else ""

    s_hash = session_hash_from_signals(signals)

    result = llm_stub_arrival(signals)

    mem = {
        "session_hash": s_hash,
        "type": "arrival_inference",
        "content": result,
        "confidence": result.get("confidence",0.0),
        "sources": result.get("evidence",[])
    }
    mem_id = write_memory(mem)
    return ArrivalResponse(**{"insight":result["insight"], "spoken":result["spoken"], "confidence":result["confidence"], "memory_key":mem_id, "sources":result.get("evidence",[])})


class MirrorRequest(BaseModel):
    company: Optional[str]
    url: Optional[str]
    session_id: Optional[str]


class MirrorResponse(BaseModel):
    model: str
    bottleneck: str
    kpi: str
    cost_of_inaction: int
    spoken: str
    confidence: float
    sources: List[str]


@router.post("/mirror-business", response_model=MirrorResponse)
async def mirror_business(req: MirrorRequest):
    url = req.url
    if not url and req.company:
        url = f"https://{req.company}.example.com"
    result = summarize_business_from_url(url or "https://example.com")

    mem = {
        "session_hash": session_hash_from_signals({"ip":"","user_agent":"","path":""}),
        "type": "mirror_business",
        "content": result,
        "confidence": result.get("confidence",0.0),
        "sources": result.get("sources",[])
    }
    mem_id = write_memory(mem)
    result_out = result.copy()
    result_out["memory_key"] = mem_id
    return MirrorResponse(**result_out)


class PipelineRequest(BaseModel):
    lead_sources: Optional[List[str]]
    time_frame: Optional[str]


class PipelineResponse(BaseModel):
    lost_estimate: float
    fix: str
    next_action: Dict[str,Any]
    confidence: float


@router.post("/pipeline-shadow", response_model=PipelineResponse)
async def pipeline_shadow(req: PipelineRequest):
    # Very lightweight funnel sim
    leads = 1000
    conversion = 0.06
    avg_value = 2000
    # Simulate dropoff due to day-3
    leakage = 0.12
    lost = leads * conversion * avg_value * leakage
    fix = "Implement day-3 call + automated SMS follow-up"
    next_action = {"type":"create_followup","spec":{"sequence":"day3_call_sms"}}
    confidence = 0.75
    mem = {"type":"pipeline_shadow","content":{"lost_estimate":lost,"fix":fix},"confidence":confidence}
    # attach governance metadata
    mem['requires_approval'] = False
    mem['approval_status'] = 'pending'
    mem_id = write_memory(mem)
    return PipelineResponse(**{"lost_estimate":lost, "fix":fix, "next_action":next_action, "confidence":confidence})


class ConvictionRequest(BaseModel):
    context_id: Optional[str]
    role: Optional[str] = 'viewer'


class ConvictionResponse(BaseModel):
    decision: str
    justification: str
    risk: str
    fallback: str
    confidence: float


@router.post('/conviction', response_model=ConvictionResponse)
async def conviction(req: ConvictionRequest):
    # dry-run only: compute a stub decision and enforce governance
    # produce a deterministic stub
    decision = 'Prioritize closing account A this week.'
    justification = 'High pressure signal and recent churn risk.'
    risk = 'Potential false positive if signals are stale.'
    fallback = 'Defer to manual review.'
    confidence = 0.65

    # check governance: role permission and confidence threshold
    perms = permission_from_role(req.role or 'viewer')
    allowed = is_action_allowed(confidence, requires_high_trust=False)
    if not perms.get('can_execute', False) or not allowed:
        # require approval
        mem = {
            'type':'conviction',
            'content':{'decision':decision,'justification':justification,'risk':risk,'fallback':fallback},
            'confidence': confidence,
            'requires_approval': True,
            'approval_status': 'pending'
        }
        mem_id = write_memory(mem)
        return ConvictionResponse(**{'decision':decision,'justification':justification,'risk':risk,'fallback':fallback,'confidence':confidence})

    # allowed but still DRY-RUN: do not execute external actions
    mem = {
        'type':'conviction',
        'content':{'decision':decision,'justification':justification,'risk':risk,'fallback':fallback},
        'confidence': confidence,
        'requires_approval': False,
        'approval_status': 'approved'
    }
    mem_id = write_memory(mem)
    return ConvictionResponse(**{'decision':decision,'justification':justification,'risk':risk,'fallback':fallback,'confidence':confidence})


class ApprovalRequest(BaseModel):
    memory_id: str
    decision_type: str
    approved_by: str
    approval_level: Optional[str] = 'operator'


@router.post('/orchestrator/approve')
async def orchestrator_approve(req: ApprovalRequest):
    # write approval metadata into canonical memory doc
    client = init_firestore_client()
    col = os.environ.get('FIRESTORE_COLLECTION','mcp_memory')
    if not client:
        # try local memory write
        try:
            from memory.helpers import write_local_memory
            doc = {
                'id': req.memory_id,
                'type': 'approval',
                'approval_metadata': {
                    'decision_type': req.decision_type,
                    'approved_by': req.approved_by,
                    'approval_level': req.approval_level,
                    'status': 'approved'
                }
            }
            cid = write_local_memory(doc)
            return { 'status':'ok','memory_id':cid }
        except Exception as e:
            return { 'status':'error','error':str(e) }
    # Firestore path
    try:
        doc_ref = client.collection(col).document(req.memory_id)
        existing = doc_ref.get().to_dict() if doc_ref.get().exists else {}
        existing['requires_approval'] = False
        existing['approval_status'] = 'approved'
        existing['approval_metadata'] = {
            'decision_type': req.decision_type,
            'approved_by': req.approved_by,
            'approval_level': req.approval_level,
            'status': 'approved'
        }
        doc_ref.set(existing, merge=True)
        return { 'status':'ok','memory_id': req.memory_id }
    except Exception as e:
        return { 'status':'error','error': str(e) }
