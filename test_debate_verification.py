import sys
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "web"))
sys.path.insert(0, str(_REPO_ROOT / "orchestrator"))

from models import UserApologeticsContext, UserPerspective
from services import CaseFileGenerator
from orchestrator.zuma_skill_engine import ZumaSkillEngine

claim = "Yesaya 21:13-17 adalah nubuat tentang Nabi Muhammad"
ctx = UserApologeticsContext(
    ui_locale="id",
    user_perspective=UserPerspective.ISLAM,
    opponent_perspective="kristen",
    debate_locale="id"
)

case_file = CaseFileGenerator.generate_case_file(
    claim=claim,
    context=ctx,
    mode="debate"
)

print("--- CASE FILE DEBATE PREPARATION SIMULATED DEBATE ---")
sim_debate = case_file.debate_preparation.get("simulated_debate", [])
print(json.dumps(sim_debate, indent=2, ensure_ascii=False))
