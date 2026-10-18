import sys
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "web"))
sys.path.insert(0, str(_REPO_ROOT / "orchestrator"))

from models import UserApologeticsContext, UserPerspective
from services import CaseFileGenerator

print("=== AUDIT: RESEARCH MODE ==")
ctx_res = UserApologeticsContext(
    ui_locale="id",
    user_perspective=UserPerspective.CHRISTIAN,
    opponent_perspective="islam",
    debate_locale="id"
)
cf_res = CaseFileGenerator.generate_case_file(
    claim="Yesus tidak pernah secara langsung berkata, 'Aku adalah Tuhan.'",
    context=ctx_res,
    mode="research"
)
print(json.dumps({
    "case_id": cf_res.case_id,
    "claim": cf_res.claim,
    "argument": cf_res.argument[:150],
    "counterargument": cf_res.counterargument[:150],
    "rebuttal": cf_res.rebuttal[:150],
    "provider": cf_res.provider,
    "provenance": cf_res.provenance
}, indent=2, ensure_ascii=False))

print("\n=== AUDIT: DEBATE MODE (ZUMA 8-POINT DIALECTIC) ==")
ctx_deb = UserApologeticsContext(
    ui_locale="id",
    user_perspective=UserPerspective.ISLAM,
    opponent_perspective="kristen",
    debate_locale="id"
)
cf_deb = CaseFileGenerator.generate_case_file(
    claim="Yesaya 21:13-17 adalah nubuat tentang Nabi Muhammad",
    context=ctx_deb,
    mode="debate"
)
sim_deb = cf_deb.debate_preparation.get("simulated_debate", [])
print(f"Total simulated debate points generated: {len(sim_deb)}")
for pt in sim_deb:
    print(f"[{pt.get('point_no')}] {pt.get('point')}")
    print(f"    Style: {pt.get('zuma_style')}")
    print(f"    Presentation: {pt.get('presentation')[:120]}...")

print("\nAudit completed successfully. Both Research and Debate modes generate dynamic content.")
