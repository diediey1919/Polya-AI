import os
import sys
from pathlib import Path
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Request, Response, status, Header, Depends
from pydantic import BaseModel, Field

# Ensure repo root is in sys.path for orchestrator and internal packages
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

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

router = APIRouter(prefix="/api/v1", tags=["Foundation"])


def verify_user_access(requested_user_id: str, authorization: Optional[str] = Header(None)) -> str:
    """Enforces authorization across user boundaries:
    1. If user_id is \x27guest_user\x27 and no auth header, permits guest.
    2. If auth header is provided, verifies Bearer token.
       If requested_user_id != token[\x27sub\x27] and requested_user_id != \x27guest_user\x27, raises HTTP 403 Forbidden.
       Returns verified user ID from token subject.
    3. If requested_user_id is a specific user (not \x27guest_user\x27) and no auth header, raises HTTP 401 Unauthorized.
    """
    if authorization:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme: Bearer token expected")
        claims = SessionService.verify_token(parts[1])
        if not claims or "sub" not in claims:
            raise HTTPException(status_code=401, detail="Invalid or expired session token")
        authenticated_id = claims["sub"]
        if requested_user_id != "guest_user" and requested_user_id != authenticated_id:
            raise HTTPException(status_code=403, detail="Forbidden: cross-user access denied")
        return authenticated_id

    if requested_user_id != "guest_user":
        raise HTTPException(status_code=401, detail="Authentication required to access user account")

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
async def create_checkout(req: CheckoutRequest):
    user_id = req.user_id or "guest_user"
    try:
        tx = PaymentService.create_checkout(user_id, req.idempotency_key)
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
