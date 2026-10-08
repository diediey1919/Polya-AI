"""
Polya Apologetika — Foundation API Router
Phase-1 Web Foundation
"""
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

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
    CaseFileGenerator,
    get_db
)

router = APIRouter(prefix="/api/v1", tags=["Foundation"])


class AnalyzeRequest(BaseModel):
    claim: str
    request_id: str
    user_id: Optional[str] = "guest_user"
    context: Optional[UserApologeticsContext] = None


class CheckoutRequest(BaseModel):
    user_id: Optional[str] = "guest_user"
    idempotency_key: Optional[str] = None


class SessionAuthRequest(BaseModel):
    token: Optional[str] = None
    email: Optional[str] = "scholar@polya-apologetika.org"
    name: Optional[str] = "Apologist Researcher"
    avatar: Optional[str] = "https://lh3.googleusercontent.com/a/default-user"
    is_mock: bool = True


@router.get("/meta/languages")
async def get_language_registry():
    return {"languages": LANGUAGE_REGISTRY, "default": "en"}


@router.get("/claims/examples")
async def get_example_claims():
    return {"claims": CANONICAL_DEMO_CLAIMS}


@router.get("/context")
async def get_user_context(user_id: str = "guest_user"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ui_locale, user_perspective, opponent_perspective, debate_locale, source_locale FROM user_apologetics_context WHERE user_id = ?", (user_id,))
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
async def save_user_context(ctx: UserApologeticsContext, user_id: str = "guest_user"):
    conn = get_db()
    cursor = conn.cursor()
    now_iso = ctx.model_dump()
    cursor.execute("""
    INSERT INTO user_apologetics_context (user_id, ui_locale, user_perspective, opponent_perspective, debate_locale, source_locale, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    ON CONFLICT(user_id) DO UPDATE SET
        ui_locale = excluded.ui_locale,
        user_perspective = excluded.user_perspective,
        opponent_perspective = excluded.opponent_perspective,
        debate_locale = excluded.debate_locale,
        source_locale = excluded.source_locale,
        updated_at = excluded.updated_at
    """, (user_id, ctx.ui_locale, ctx.user_perspective.value, ctx.opponent_perspective, ctx.debate_locale, ctx.source_locale))
    conn.commit()
    conn.close()
    return {"success": True, "context": ctx.model_dump()}


@router.get("/entitlements/usage")
async def get_usage_telemetry(user_id: str = "guest_user"):
    usage = UsageEntitlementService.get_usage(user_id)
    return usage


@router.get("/entitlements/status")
async def get_entitlement_status(user_id: str = "guest_user"):
    status_info = EntitlementService.get_entitlement(user_id)
    return status_info


@router.post("/calculator/analyze")
async def analyze_claim(req: AnalyzeRequest):
    user_id = req.user_id or "guest_user"

    # Server-side Quota & Premium Gate Verification
    if not UsageEntitlementService.can_analyze(user_id):
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
    success, msg = UsageEntitlementService.consume_analysis(user_id, req.request_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": "CONSUME_FAILED", "message": msg}
        )

    # Generate source-first Case File fixture
    case_file = CaseFileGenerator.generate_case_file(req.claim, req.context)
    usage = UsageEntitlementService.get_usage(user_id)

    return {
        "success": True,
        "case_file": case_file.model_dump(),
        "usage": usage,
        "notice": case_file.notice
    }


@router.get("/calculator/source")
async def show_source_endpoint(passage: str):
    """Show Me The Source endpoint conforming to Master Prompt #3 Section 30."""
    from orchestrator.evidence_engine import Evidence
    src = Evidence.show_source(passage)
    if not src:
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
    tx = PaymentService.create_checkout(user_id, req.idempotency_key)
    return tx


@router.post("/payment/webhook")
@router.post("/payment/midtrans/webhook")
async def midtrans_webhook(req: Request):
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON")

    success, msg = PaymentService.process_webhook(body, allow_simulator=True)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "settled", "message": msg}


@router.get("/account/billing")
async def get_account_billing(user_id: str = "guest_user"):
    entitlement = EntitlementService.get_entitlement(user_id)
    usage = UsageEntitlementService.get_usage(user_id)
    transactions = PaymentService.get_user_transactions(user_id)

    return {
        "user_id": user_id,
        "entitlement": entitlement,
        "usage": usage,
        "transactions": transactions
    }


@router.post("/auth/session")
async def auth_session(req: SessionAuthRequest):
    user_id = f"usr_{abs(hash(req.email)) % 1000000}"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO arena_users (user_id, email, name, avatar_url, bio, role, created_at)
    VALUES (?, ?, ?, ?, 'Polya Researcher', 'apologist', datetime('now'))
    ON CONFLICT(user_id) DO UPDATE SET
        name = excluded.name,
        avatar_url = excluded.avatar_url
    """, (user_id, req.email, req.name, req.avatar))
    conn.commit()
    conn.close()

    usage = UsageEntitlementService.get_usage(user_id)
    entitlement = EntitlementService.get_entitlement(user_id)

    user_data = {
        "user_id": user_id,
        "email": req.email,
        "name": req.name,
        "avatar": req.avatar,
        "role": "apologist"
    }

    return {
        "success": True,
        "session_token": f"polya_tok_{uuid.uuid4().hex}",
        "user": user_data,
        "profile": user_data,
        "usage": usage,
        "entitlement": entitlement,
        "auth_provider": "google",
        "is_mock": req.is_mock
    }
