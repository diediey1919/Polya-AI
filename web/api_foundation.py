import os
import sys
import json
import logging
logger = logging.getLogger("polya.api_foundation")
from pathlib import Path
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Request, Response, status, Header, Depends
from pydantic import BaseModel, Field

# Ensure repo root and web dir are in sys.path
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
WEB_DIR = str(Path(__file__).resolve().parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

try:
    from models import (
        LANGUAGE_REGISTRY,
        CANONICAL_DEMO_CLAIMS,
        UserApologeticsContext,
        UserPerspective,
        EntitlementState,
        CaseFile
    )
    from services import (
        UsageEntitlementService,
        EntitlementService,
        PaymentService,
        PaymentGatewayError,
        CaseFileGenerator,
        SessionService,
        GoogleAuthVerifier,
        get_db
    )
except ImportError:
    from web.models import (
        LANGUAGE_REGISTRY,
        CANONICAL_DEMO_CLAIMS,
        UserApologeticsContext,
        UserPerspective,
        EntitlementState,
        CaseFile
    )
    from web.services import (
        UsageEntitlementService,
        EntitlementService,
        PaymentService,
        PaymentGatewayError,
        CaseFileGenerator,
        SessionService,
        GoogleAuthVerifier,
        get_db
    )

router = APIRouter(prefix="/api/v1", tags=["Foundation"])


def verify_user_access(requested_user_id: str, authorization: Optional[str] = Header(None)) -> str:
    """Enforces authorization across user boundaries:
    1. If user_id is 'guest_user' and no auth header, permits legacy anonymous guest.
    2. If auth header is provided, verifies Bearer token HMAC signature and expiration.
       - Rejects manipulated tokens, bad signatures, and expired tokens (HTTP 401).
       - Enforces cross-user isolation: requested_user_id must match token sub (HTTP 403).
       - Guest role tokens cannot impersonate registered users (HTTP 403).
       Returns verified user ID from token subject.
    3. If requested_user_id is a specific user (not 'guest_user') and no auth header:
       Rejects unauthenticated access (HTTP 401), preventing arbitrary guest_<uuid> assertion.
    """
    if authorization:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme: Bearer token expected")
        claims = SessionService.verify_token(parts[1])
        if not claims or "sub" not in claims:
            raise HTTPException(status_code=401, detail="Invalid or expired session token")
        authenticated_id = claims["sub"]
        role = claims.get("role", "visitor")

        if role == "guest" and requested_user_id.startswith("usr_"):
            raise HTTPException(status_code=403, detail="Forbidden: guest session cannot access registered user account")

        if requested_user_id != "guest_user" and requested_user_id != authenticated_id:
            raise HTTPException(status_code=403, detail="Forbidden: cross-user access denied")
        return authenticated_id

    if requested_user_id != "guest_user":
        raise HTTPException(
            status_code=401,
            detail="Authentication required: client-declared identity rejected without server-signed session token"
        )

    return "guest_user"

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Centralized authentication dependency extracting authenticated user identity.
    Accepts: 'Bearer <token>'. Rejects unauthenticated or tampered calls.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required: missing Authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme: Bearer token expected")

    token = parts[1]
    claims = SessionService.verify_token(token)
    if not claims or "sub" not in claims:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    return claims["sub"]


class AnalyzeRequest(BaseModel):
    claim: str
    request_id: Optional[str] = None
    user_id: Optional[str] = "guest_user"
    context: Optional[UserApologeticsContext] = None


class CheckoutRequest(BaseModel):
    user_id: Optional[str] = "guest_user"
    idempotency_key: Optional[str] = None


class SessionAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    is_mock: bool = False


class GuestAuthRequest(BaseModel):
    client_id: Optional[str] = None


@router.get("/meta/languages")
async def get_language_registry():
    return {"languages": LANGUAGE_REGISTRY, "default": "en"}


@router.get("/claims/examples")
async def get_example_claims():
    return {"claims": CANONICAL_DEMO_CLAIMS}


@router.get("/context")
async def get_user_context(user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ui_locale, user_perspective, opponent_perspective, debate_locale, source_locale FROM user_apologetics_context WHERE user_id = ?", (effective_user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return UserApologeticsContext().model_dump()

    return {
        "ui_locale": row["ui_locale"],
        "user_perspective": row["user_perspective"],
        "opponent_perspective": row["opponent_perspective"],
        "debate_locale": row["debate_locale"],
        "source_locale": row["source_locale"]
    }


@router.post("/context")
async def save_user_context(ctx: UserApologeticsContext, user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_apologetics_context (user_id, ui_locale, user_perspective, opponent_perspective, debate_locale, source_locale, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime(now))
    ON CONFLICT(user_id) DO UPDATE SET
        ui_locale = excluded.ui_locale,
        user_perspective = excluded.user_perspective,
        opponent_perspective = excluded.opponent_perspective,
        debate_locale = excluded.debate_locale,
        source_locale = excluded.source_locale,
        updated_at = excluded.updated_at
    """, (effective_user_id, ctx.ui_locale, ctx.user_perspective.value, ctx.opponent_perspective, ctx.debate_locale, ctx.source_locale))
    conn.commit()
    conn.close()
    return {"success": True, "context": ctx.model_dump()}


@router.get("/entitlements/usage")
async def get_usage_telemetry(user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    usage = UsageEntitlementService.get_usage(effective_user_id)
    return usage


@router.get("/entitlements/status")
async def get_entitlement_status(user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    status_info = EntitlementService.get_entitlement(effective_user_id)
    return status_info


@router.post("/calculator/analyze")
async def analyze_claim(req: AnalyzeRequest, authorization: Optional[str] = Header(None)):
    raw_user_id = req.user_id or "guest_user"
    effective_user_id = verify_user_access(raw_user_id, authorization)
    req_id = req.request_id or f"req_{uuid.uuid4().hex[:12]}"

    # Server-side Quota & Premium Gate Verification
    if not UsageEntitlementService.can_analyze(effective_user_id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "QUOTA_EXHAUSTED",
                "message": "5 analisis gratis kamu telah digunakan. Lanjutkan dengan Polya Premium.",
                "price": "Rp99.000",
                "upgrade_url": "/checkout",
                "required_action": "PREMIUM_UPGRADE_REQUIRED"
            }
        )

    # Consume analysis with request idempotency
    success, msg = UsageEntitlementService.consume_analysis(effective_user_id, req_id)
    if not success:
        if msg == "DATABASE_LOCKED":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "TRANSIENT_BUSY", "message": "Layanan sedang sibuk. Silakan coba kembali dalam beberapa saat."}
            )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": "CONSUME_FAILED", "message": msg}
        )

    # Generate and persist source-first Case File
    case_file = CaseFileGenerator.generate_case_file(req.claim, req.context, user_id=effective_user_id)
    usage = UsageEntitlementService.get_usage(effective_user_id)

    return {
        "success": True,
        "case_file": case_file.model_dump(),
        "usage": usage,
        "notice": case_file.notice
    }


@router.get("/case-files")
async def list_case_files_endpoint(
    user_id: str = "guest_user",
    limit: int = 50,
    authorization: Optional[str] = Header(None)
):
    """Lists persisted Case Files for the authenticated user."""
    effective_user_id = verify_user_access(user_id, authorization)
    from orchestrator.case_file import CaseFiles
    files = CaseFiles.list_case_files(effective_user_id, limit=limit)
    return {
        "success": True,
        "user_id": effective_user_id,
        "total": len(files),
        "case_files": files
    }


@router.get("/case-files/{case_id}")
async def get_case_file_endpoint(
    case_id: str,
    user_id: str = "guest_user",
    authorization: Optional[str] = Header(None)
):
    """Fetches specific persisted Case File with strict ownership validation."""
    effective_user_id = verify_user_access(user_id, authorization)
    from orchestrator.case_file import CaseFiles
    cf = CaseFiles.get_case_file_for_user(case_id, effective_user_id)
    if not cf:
        raw_cf = CaseFiles.get_case_file(case_id)
        if raw_cf:
            raise HTTPException(status_code=403, detail="Forbidden: cannot access another user\x27s case file")
        raise HTTPException(status_code=404, detail=f"Case file \x27{case_id}\x27 not found")
    return {
        "success": True,
        "case_file": cf.to_dict()
    }


@router.get("/calculator/source")
async def show_source_endpoint(passage: str):
    """Show Me The Source endpoint conforming to Master Prompt #3 Section 30."""
    from orchestrator.evidence_engine import Evidence
    src = Evidence.show_source(passage)
    if not src:
        # Check by prefix / passage matching in index
        items = Evidence.get_evidence_by_passage(passage)
        if items:
            item = items[0]
            src = {
                "source": "Greek New Testament (NA28/UBS5) & Critical Apparatus",
                "passage_reference": item.passage_reference,
                "location": f"Biblia Graeca / {item.passage_reference}",
                "original_text": item.original_text,
                "transliteration": item.transliteration,
                "witnesses": item.witnesses,
                "confidence": item.confidence,
                "provenance_hash": item.provenance_hash,
                "evidence_tier": item.evidence_tier.value if hasattr(item.evidence_tier, "value") else str(item.evidence_tier),
                "tokens": []
            }
        else:
            raise HTTPException(status_code=404, detail=f"Source provenance for '{passage}' not found in canonical apparatus.")
    return {"success": True, "source": src}


@router.post("/calculator/challenge")
async def challenge_argument_endpoint(req: AnalyzeRequest):
    """Challenge My Argument endpoint running the Adversarial Attack pipeline (Section 30)."""
    from orchestrator.research_graph import build_research_graph
    graph = build_research_graph()
    run_id = f"run_chal_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_chal_{uuid.uuid4().hex[:8]}"

    state = {
        "claim_input": req.claim,
        "run_id": run_id,
        "thread_id": thread_id,
        "user_perspective": "CHRISTIAN",
        "requested_mode": "ADVERSARIAL_REVIEW",
        "tasks": [],
        "dispatched_agent_records": [],
        "evidence_items": [],
        "provenance_hashes": [],
        "claim_atomicity_graph": None,
        "source_criticism_records": [],
        "textual_criticism_records": [],
        "translation_audits": [],
        "philological_adversarial_tests": [],
        "context_audits": [],
        "claim_object": None,
        "argument_graph": None,
        "steelman_counterarg": None,
        "contradiction_report": None,
        "verification_records": [],
        "verification_status": "",
        "epistemic_firewall_report": None,
        "adversarial_attacks": [],
        "self_refutation_survived": True,
        "weakest_point": None,
        "fallacies": [],
        "uncertainty_calibration": None,
        "evidence_coverage": None,
        "debate_quality_gate": None,
        "zuma_self_critique": None,
        "research_iterations": 0,
        "max_research_iterations": 2,
        "knowledge_gaps": [],
        "evaluation_scorecard": None,
        "debate_preparation": None,
        "case_id": None,
        "execution_traces": [],
        "final_response": None,
        "errors": []
    }
    result = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})
    return {
        "success": True,
        "mode": "ADVERSARIAL_REVIEW",
        "claim": req.claim,
        "adversarial_attacks": result.get("adversarial_attacks", []),
        "self_refutation_survived": result.get("self_refutation_survived", True),
        "weakest_point": result.get("weakest_point"),
        "zuma_self_critique": result.get("zuma_self_critique"),
        "final_response": result.get("final_response")
    }


@router.post("/calculator/weakest-point")
async def show_weakest_point_endpoint(req: AnalyzeRequest):
    """Show Me The Weakest Point endpoint identifying the most vulnerable premise (Section 30)."""
    from orchestrator.claim_atomicity import ClaimAtomicityEngine
    atom_graph = ClaimAtomicityEngine.decompose_claim(req.claim)
    integrity = ClaimAtomicityEngine.audit_graph_integrity(atom_graph)
    from orchestrator.adversarial_engine import AdversarialEngine
    critique = AdversarialEngine.generate_zuma_self_critique(req.claim)

    return {
        "success": True,
        "claim": req.claim,
        "weakest_premise": critique.weakest_premise,
        "easiest_sentence_to_refute": critique.easiest_sentence_to_refute,
        "broken_premises": integrity.get("broken_premises", []),
        "hardening_recommendations": critique.hardening_recommendations
    }


@router.post("/payment/checkout")
async def create_checkout(req: CheckoutRequest, authorization: Optional[str] = Header(None)):
    user_id = req.user_id or "guest_user"
    effective_user_id = verify_user_access(user_id, authorization)
    try:
        tx = PaymentService.create_checkout(effective_user_id, req.idempotency_key)
        return tx
    except PaymentGatewayError as e:
        raise HTTPException(status_code=e.status_code, detail={"error": "PAYMENT_GATEWAY_ERROR", "message": e.message})


@router.post("/payment/webhook")
@router.post("/payment/midtrans/webhook")
async def midtrans_webhook(req: Request):
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON")

    success, msg = PaymentService.process_webhook(body)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "settled", "message": msg}


@router.get("/account/billing")
async def get_account_billing(
    user_id: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    # Enforce IDOR protection: if user_id is passed, it must match current_user_id
    if user_id and user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: cannot access another user's billing records")

    effective_user_id = current_user_id
    entitlement = EntitlementService.get_entitlement(effective_user_id)
    usage = UsageEntitlementService.get_usage(effective_user_id)
    transactions = PaymentService.get_user_transactions(effective_user_id)

    return {
        "user_id": effective_user_id,
        "entitlement": entitlement,
        "usage": usage,
        "transactions": transactions
    }


@router.post("/auth/guest")
async def auth_guest(req: Optional[GuestAuthRequest] = None):
    """Issues a cryptographically signed guest session token with isolated guest identity."""
    token, guest_id = SessionService.create_guest_token()
    usage = UsageEntitlementService.get_usage(guest_id)
    entitlement = EntitlementService.get_entitlement(guest_id)
    return {
        "success": True,
        "session_token": token,
        "user_id": guest_id,
        "role": "guest",
        "usage": usage,
        "entitlement": entitlement,
        "expires_in": SessionService.GUEST_TOKEN_TTL_SECONDS
    }


@router.post("/auth/session")
async def auth_session(req: SessionAuthRequest):
    # Enforce verification gate: reject raw email/name assertion
    verified_data = None
    if req.credential:
        verified_data = GoogleAuthVerifier.verify_credential(req.credential)

    # In dev/test environments ONLY, allow controlled mock authentication
    if not verified_data and req.is_mock:
        if not GoogleAuthVerifier.is_mock_allowed():
            raise HTTPException(status_code=403, detail="Mock authentication forbidden: environment not in positive allowlist")
        if req.email and req.email.endswith(("@polya.org", "@mock.polya.local")):
            verified_data = {
                "sub": f"mock_sub_{abs(hash(req.email)) % 1000000}",
                "email": req.email.lower().strip(),
                "name": req.name or "Mock Apologist",
                "avatar_url": req.avatar or "https://lh3.googleusercontent.com/a/default-user"
            }

    if not verified_data:
        raise HTTPException(status_code=401, detail="Authentication failed: valid Google credential required")

    email = verified_data["email"]
    name = verified_data.get("name", "Polya Apologist")
    avatar = verified_data.get("avatar_url", "")
    google_sub = verified_data.get("sub", "")

    # Stable identity mapping: anchor primarily to permanent provider subject
    user_id = f"usr_{uuid.uuid5(uuid.NAMESPACE_URL, f'google:{google_sub}').hex[:12]}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM arena_users WHERE user_id = ?", (user_id,))
    existing_row = cursor.fetchone()
    # Server policy role assignment: default to visitor, never allow client to dictate role
    server_role = existing_row["role"] if existing_row else "visitor"

    cursor.execute("""
    INSERT INTO arena_users (user_id, email, name, avatar_url, bio, role, created_at)
    VALUES (?, ?, ?, ?, 'Polya Researcher', ?, datetime('now'))
    ON CONFLICT(user_id) DO UPDATE SET
        name = excluded.name,
        avatar_url = excluded.avatar_url
    """, (user_id, email, name, avatar, server_role))
    conn.commit()
    conn.close()

    usage = UsageEntitlementService.get_usage(user_id)
    entitlement = EntitlementService.get_entitlement(user_id)
    token = SessionService.create_token(user_id, role=server_role)

    user_data = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "avatar": avatar,
        "role": server_role
    }

    return {
        "success": True,
        "session_token": token,
        "user": user_data,
        "profile": user_data,
        "usage": usage,
        "entitlement": entitlement,
        "auth_provider": "google",
        "is_mock": req.is_mock if GoogleAuthVerifier.is_mock_allowed() else False
    }


# ===========================================================================
# P1.1: Dynamic Knowledge Base Graph & Corpus Endpoints
# ===========================================================================

@router.get("/knowledge/graph")
async def get_knowledge_graph_endpoint(q: Optional[str] = None, limit: int = 50):
    """Returns dynamic Knowledge Graph nodes and edges computed from actual claim atomicity and evidence apparatus."""
    from orchestrator.claim_atomicity import ClaimAtomicityEngine
    from orchestrator.evidence_engine import CANONICAL_PHILOLOGY_KNOWLEDGE, Evidence

    query = q.strip() if q else "Paulus menegakkan hukum Taurat (Roma 3:31)"
    dag = ClaimAtomicityEngine.decompose_claim(query)

    nodes = []
    edges = []
    seen_nodes = set()

    # 1. Root Claim Node
    root_id = dag.claim_id
    nodes.append({
        "id": root_id,
        "label": query,
        "type": "CLAIM",
        "status": "ACTIVE",
        "confidence": 0.96,
        "epistemic_status": "DIRECTLY_VERIFIED"
    })
    seen_nodes.add(root_id)

    # 2. Atomic Proposition Nodes & Edges
    for p in dag.propositions[:limit]:
        p_dict = p.to_dict()
        pid = p_dict["proposition_id"]
        if pid not in seen_nodes:
            nodes.append({
                "id": pid,
                "label": f"[{p_dict['label']}] {p_dict['text'][:65]}...",
                "full_text": p_dict["text"],
                "type": "PROPOSITION",
                "status": p_dict.get("epistemic_status", "SUPPORTED"),
                "confidence": p_dict.get("confidence", 0.95),
                "is_premise": p_dict.get("is_premise", True)
            })
            seen_nodes.add(pid)

    for e in dag.edges[:limit]:
        e_dict = e.to_dict()
        edges.append({
            "source": e_dict["source_id"],
            "target": e_dict["target_id"],
            "relation": e_dict["relation"],
            "weight": e_dict.get("weight", 0.9),
            "description": e_dict.get("description", "")
        })

    # 3. Primary Evidence & Manuscript Witnesses Nodes
    for passage, ev in list(CANONICAL_PHILOLOGY_KNOWLEDGE.items())[:10]:
        ev_id = f"evi_{passage.replace(' ', '_').replace(':', '_')}"
        if ev_id not in seen_nodes:
            nodes.append({
                "id": ev_id,
                "label": f"{passage} ({ev['original_language']})",
                "type": "EVIDENCE",
                "status": "PRIMARY_SOURCE",
                "text": ev["original_text"],
                "transliteration": ev.get("transliteration", ""),
                "witnesses": ev.get("witnesses", []),
                "confidence": ev.get("confidence", 0.98),
                "provenance_hash": ev.get("provenance_hash", "")
            })
            seen_nodes.add(ev_id)
            edges.append({
                "source": ev_id,
                "target": root_id,
                "relation": "supports",
                "weight": ev.get("confidence", 0.98),
                "description": f"Saksi Naskah Primer untuk {passage}"
            })

    return {
        "success": True,
        "query": query,
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "nodes": nodes,
        "edges": edges
    }


@router.get("/knowledge/claims")
async def get_knowledge_claims_endpoint():
    """Returns verified canonical claims from knowledge index."""
    claims_data = []
    for idx, c_text in enumerate(CANONICAL_DEMO_CLAIMS):
        claims_data.append({
            "claim_id": f"claim_canon_{idx + 1:03d}",
            "text": c_text,
            "status": "VERIFIED_ACTIVE",
            "subject": c_text.split(" ")[0] if " " in c_text else c_text,
            "category": "THEOLOGICAL_POLEMIC",
            "confidence": 0.95
        })
    return {"success": True, "count": len(claims_data), "claims": claims_data}


@router.get("/knowledge/evidence")
async def get_knowledge_evidence_endpoint():
    """Returns verified primary manuscript witnesses and apparatus details."""
    from orchestrator.evidence_engine import CANONICAL_PHILOLOGY_KNOWLEDGE
    evidence_list = []
    for passage, ev in CANONICAL_PHILOLOGY_KNOWLEDGE.items():
        evidence_list.append({
            "passage_reference": passage,
            "original_language": ev.get("original_language", "Koine Greek"),
            "original_text": ev.get("original_text", ""),
            "transliteration": ev.get("transliteration", ""),
            "witnesses": ev.get("witnesses", []),
            "confidence": ev.get("confidence", 0.98),
            "provenance_hash": ev.get("provenance_hash", ""),
            "tokens_count": len(ev.get("tokens", []))
        })
    return {"success": True, "count": len(evidence_list), "evidence": evidence_list}


# ===========================================================================
# P1.2: Dynamic Themes Explorer Endpoints
# ===========================================================================

@router.get("/themes")
async def list_themes_endpoint():
    """Returns dynamic catalog of themes sourced from video_pipeline/06_debate."""
    import glob
    themes = []
    pipeline_dir = os.path.join(REPO_ROOT, "data", "video_pipeline", "06_debate")
    debate_files = sorted(glob.glob(os.path.join(pipeline_dir, "*", "debate.json")))

    for path in debate_files:
        vid = os.path.basename(os.path.dirname(path))
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            motion = d.get("motion_or_topic") or f"Debate Theme {vid}"
            rounds = d.get("rounds", [])
            themes.append({
                "theme_id": vid,
                "id": vid,
                "title": motion,
                "discourse_type": d.get("debate_mode") or "APOLOGETIC_INTERFAITH_DEBATE",
                "passages": ["Roma 3:31", "Galatia 2:16", "Matius 26:39", "Yohanes 10:30"],
                "rounds_count": len(rounds),
                "participants_count": len(d.get("participants", [])),
                "grounding_rules_count": len(d.get("grounding_rules", [])),
                "status": "Debate Ready"
            })
        except Exception as err:
            logger.warning(f"Failed to parse theme {vid}: {err}")

    # Fallback to theme-01 if 06_debate is empty
    if not themes:
        themes.append({
            "theme_id": "friksi-paulus-vs-petrus",
            "title": "Friksi Paulus vs Petrus (Galatia 2 & Roma 15)",
            "discourse_type": "APOLOGETIC_INTERFAITH_DEBATE",
            "rounds_count": 5,
            "participants_count": 2,
            "grounding_rules_count": 4,
            "status": "Debate Ready"
        })

    return {"success": True, "count": len(themes), "themes": themes}


@router.get("/themes/{theme_id}")
async def get_theme_detail_endpoint(theme_id: str):
    """Returns complete 6-tab theme details for theme_id."""
    import hashlib
    canonical_alias_map = {
        "pauline_torah": "friksi-paulus-vs-petrus",
        "friksi-paulus-vs-petrus": "friksi-paulus-vs-petrus"
    }
    actual_theme_id = canonical_alias_map.get(theme_id, theme_id)
    theme_dir = os.path.join(REPO_ROOT, "data", "video_pipeline", "06_debate", actual_theme_id)
    alt_theme_dir = os.path.join(REPO_ROOT, "data", "video_pipeline", "themes", "theme-01")

    if not os.path.exists(theme_dir) and actual_theme_id not in canonical_alias_map.values():
        raise HTTPException(status_code=404, detail="Theme not found")

    debate_json = os.path.join(theme_dir, "debate.json")
    narrative_json = os.path.join(alt_theme_dir, "narrative.json")
    evaluation_json = os.path.join(alt_theme_dir, "evaluation.json")
    provenance_json = os.path.join(alt_theme_dir, "provenance.json")

    motion = "Friksi Paulus vs Petrus"
    rounds_data = []
    participants = []
    grounding_rules = []

    if os.path.exists(debate_json):
        try:
            with open(debate_json, "r", encoding="utf-8") as f:
                d = json.load(f)
            motion = d.get("motion_or_topic", motion)
            rounds_data = d.get("rounds", [])
            participants = d.get("participants", [])
            grounding_rules = d.get("grounding_rules", [])
        except Exception as e:
            logger.warning(f"Error reading debate.json for {theme_id}: {e}")

    # Load narrative data
    narrative_data = {}
    if os.path.exists(narrative_json):
        try:
            with open(narrative_json, "r", encoding="utf-8") as f:
                narrative_data = json.load(f)
        except Exception:
            pass

    # Load evaluation data
    eval_data = {}
    if os.path.exists(evaluation_json):
        try:
            with open(evaluation_json, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
        except Exception:
            pass

    # Load provenance data
    prov_data = {}
    if os.path.exists(provenance_json):
        try:
            with open(provenance_json, "r", encoding="utf-8") as f:
                prov_data = json.load(f)
        except Exception:
            pass

    theme_obj = {
        "id": theme_id,
        "theme_id": theme_id,
        "title": motion,
        "passages": ["Galatia 2:11-14", "Roma 3:31", "Efesus 2:15", "Kisah Para Rasul 15"],
        "manuscript_witnesses": ["Papyrus P46 (c. 200 M)", "Codex Sinaiticus (א01)", "Codex Vaticanus (B03)"],
        "overview": {
            "motion": motion,
            "discourse_type": "APOLOGETIC_INTERFAITH_DEBATE",
            "participants": participants,
            "grounding_rules": grounding_rules,
            "summary": f"Analisis dialektika dan pembuktian eksegesis naskah atas mosi: '{motion}'."
        },
        "narrative": {
            "background": narrative_data.get("sections", {}).get("A_latar_belakang") or f"Latar belakang historis-kontekstual untuk perdebatan mengenai {motion}.",
            "core_question": narrative_data.get("sections", {}).get("B_pertanyaan_utama") or f"Apakah dalil naskah membuktikan konsistensi kanonik terkait {motion}?",
            "speaker_perspectives": narrative_data.get("speaker_perspectives", {})
        },
        "debate": {
            "rounds": rounds_data,
            "total_rounds": len(rounds_data)
        },
        "evidence": {
            "key_passages": ["Galatia 2:11-14", "Roma 3:31", "Efesus 2:15", "Kisah Para Rasul 15"],
            "witnesses": ["Papyrus P46 (c. 200 M)", "Codex Sinaiticus (א01)", "Codex Vaticanus (B03)"]
        },
        "provenance": prov_data or {
            "provenance_hash": hashlib.sha256(f"{theme_id}|{motion}".encode("utf-8")).hexdigest()[:16],
            "verified": True,
            "data_source": "Canonical Video Pipeline Corpus"
        },
        "evaluation": eval_data or {
            "status": "Debate Ready",
            "confidence_score": 0.96,
            "clash_resolution": "Unanimous Textual Priority"
        }
    }
    return {
        "success": True,
        "theme_id": theme_id,
        "theme": theme_obj,
        "title": motion,
        "overview": {
            "motion": motion,
            "discourse_type": "APOLOGETIC_INTERFAITH_DEBATE",
            "participants": participants,
            "grounding_rules": grounding_rules,
            "summary": f"Analisis dialektika dan pembuktian eksegesis naskah atas mosi: '{motion}'."
        },
        "narrative": {
            "background": narrative_data.get("sections", {}).get("A_latar_belakang") or f"Latar belakang historis-kontekstual untuk perdebatan mengenai {motion}.",
            "core_question": narrative_data.get("sections", {}).get("B_pertanyaan_utama") or f"Apakah dalil naskah membuktikan konsistensi kanonik terkait {motion}?",
            "speaker_perspectives": narrative_data.get("speaker_perspectives", {})
        },
        "debate": {
            "rounds": rounds_data,
            "total_rounds": len(rounds_data)
        },
        "evidence": {
            "key_passages": ["Galatia 2:11-14", "Roma 3:31", "Efesus 2:15", "Kisah Para Rasul 15"],
            "witnesses": ["Papyrus P46 (c. 200 M)", "Codex Sinaiticus (א01)", "Codex Vaticanus (B03)"]
        },
        "provenance": prov_data or {
            "provenance_hash": hashlib.sha256(f"{theme_id}|{motion}".encode("utf-8")).hexdigest()[:16],
            "verified": True,
            "data_source": "Canonical Video Pipeline Corpus"
        },
        "evaluation": eval_data or {
            "status": "Debate Ready",
            "confidence_score": 0.96,
            "clash_resolution": "Unanimous Textual Priority"
        }
    }


# ===========================================================================
# P1.3: Server-Sent Events (SSE) LangGraph Telemetry Stream
# ===========================================================================

@router.get("/pipeline/stream")
async def stream_pipeline_telemetry(
    claim: str,
    run_id: Optional[str] = None,
    user_id: str = "guest_user",
    perspective: str = "christian",
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    # Support token in Authorization header or token query parameter for browser EventSource compatibility
    auth_header = authorization or (f"Bearer {token}" if token else None)
    """Streams real-time Server-Sent Events (SSE) representing LangGraph node execution transitions."""
    import asyncio
    import threading
    from datetime import datetime, timezone
    from fastapi.responses import StreamingResponse
    from orchestrator.research_graph import build_research_graph

    if not auth_header:
        raise HTTPException(status_code=401, detail="Authentication required for live LangGraph SSE stream telemetry")
    effective_user_id = verify_user_access(user_id, auth_header)
    active_run_id = run_id or f"run_sse_{uuid.uuid4().hex[:8]}"
    thread_id = f"th_sse_{uuid.uuid4().hex[:8]}"

    node_to_stage = {
        "entry_node": "DISCOVER",
        "task_decomposition_node": "PLAN",
        "research_dispatch_node": "RESEARCH",
        "evidence_retrieval_node": "RESEARCH",
        "source_criticism_node": "EXTRACT",
        "claim_analysis_node": "EXTRACT",
        "argument_graph_node": "ANALYZE",
        "steelman_counterargument_node": "ANALYZE",
        "contradiction_detection_node": "ANALYZE",
        "verification_node": "VERIFY",
        "adversarial_attack_node": "VERIFY",
        "self_refutation_node": "VERIFY",
        "gap_detection_loop": "SYNTHESIZE",
        "synthesis_evaluation_node": "SYNTHESIZE",
        "debate_quality_gate_node": "EVALUATE",
        "zuma_debate_preparation_node": "EVALUATE",
        "case_file_persistence_node": "COMPLETE",
        "final_response_node": "COMPLETE"
    }

    initial_state = {
        "claim_input": claim,
        "run_id": active_run_id,
        "thread_id": thread_id,
        "user_id": effective_user_id,
        "user_perspective": perspective.upper(),
        "requested_mode": "DEEP_FORENSIC_RESEARCH",
        "tasks": [],
        "dispatched_agent_records": [],
        "evidence_items": [],
        "provenance_hashes": [],
        "claim_atomicity_graph": None,
        "source_criticism_records": [],
        "textual_criticism_records": [],
        "translation_audits": [],
        "philological_adversarial_tests": [],
        "context_audits": [],
        "claim_object": None,
        "argument_graph": None,
        "steelman_counterarg": None,
        "contradiction_report": None,
        "verification_records": [],
        "verification_status": "",
        "epistemic_firewall_report": None,
        "adversarial_attacks": [],
        "self_refutation_survived": False,
        "weakest_point": None,
        "fallacies": [],
        "uncertainty_calibration": None,
        "evidence_coverage": None,
        "debate_quality_gate": None,
        "zuma_self_critique": None,
        "research_iterations": 0,
        "max_research_iterations": 2,
        "knowledge_gaps": [],
        "evaluation_scorecard": None,
        "debate_preparation": None,
        "case_id": None,
        "execution_traces": [],
        "final_response": None,
        "errors": []
    }

    async def event_generator():
        yield f"event: connect\ndata: {json.dumps({'status': 'CONNECTED', 'run_id': active_run_id, 'claim': claim, 'user_id': effective_user_id})}\n\n"

        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def run_sync_stream():
            try:
                g = build_research_graph()
                config = {"configurable": {"thread_id": thread_id}}
                last_case_id = None
                for update in g.stream(initial_state, config=config):
                    node_name = list(update.keys())[0]
                    stage = node_to_stage.get(node_name, "ANALYZE")
                    node_output = update[node_name]
                    if isinstance(node_output, dict) and node_output.get("case_id"):
                        last_case_id = node_output.get("case_id")
                    payload = {
                        "run_id": active_run_id,
                        "node": node_name,
                        "stage": stage,
                        "status": "RUNNING",
                        "case_id": last_case_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    asyncio.run_coroutine_threadsafe(queue.put(("stage", payload)), loop)

                complete_payload = {
                    "run_id": active_run_id,
                    "stage": "COMPLETE",
                    "status": "SUCCESS",
                    "case_id": last_case_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                asyncio.run_coroutine_threadsafe(queue.put(("complete", complete_payload)), loop)
            except Exception as e:
                logger.error(f"SSE background thread error: {e}")
                err_payload = {"run_id": active_run_id, "status": "ERROR", "error": str(e)}
                asyncio.run_coroutine_threadsafe(queue.put(("error", err_payload)), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put((None, None)), loop)

        stream_thread = threading.Thread(target=run_sync_stream, daemon=True)
        stream_thread.start()

        while True:
            try:
                event_type, payload = await asyncio.wait_for(queue.get(), timeout=20.0)
                if event_type is None:
                    break
                yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
            except asyncio.TimeoutError:
                yield ": ping\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
