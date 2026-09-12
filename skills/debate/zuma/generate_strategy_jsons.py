import os
import json

strat_dir = "/home/ubuntu/skills/debate/zuma/strategies"

q_strat = {
    "name": "ZUMA Questioning Strategies",
    "strategies": [
        {
            "id": "Q-STRAT-PRECISION-LOCK",
            "name": "Precision Variable Locking",
            "trigger": "Opponent introduces broad theological terms",
            "execution": "Ask single-choice question: 'Ada berapa?' or 'Siapa yang memerintahkan?'"
        },
        {
            "id": "Q-STRAT-SOCRATIC-TRAP",
            "name": "Moral/Justice Inception Trap",
            "trigger": "Opponent defends atonement doctrine",
            "execution": "Ask: 'Apakah adil menghukum orang suci untuk dosa penjahat?'"
        }
    ]
}

cx_strat = {
    "name": "ZUMA Cross-Examination Strategies",
    "strategies": [
        {
            "id": "CX-STRAT-SEQUENTIAL-LADDER",
            "name": "5-Step Sequential Interrogation Ladder",
            "steps": ["Confirm Bible authority", "Extract Jesus supremacy rule", "Cite contradictory Pauline verse", "Ask reconciliation", "Lock contradiction"]
        }
    ]
}

reb_strat = {
    "name": "ZUMA Rebuttal Strategies",
    "strategies": [
        {
            "id": "REB-STRAT-CONTEXT-EXPANSION",
            "name": "Context Expansion Rebuttal",
            "trigger": "Opponent cherry-picks half-verse",
            "execution": "Read previous and subsequent verses, reveal inverted meaning"
        },
        {
            "id": "REB-STRAT-CANON-COLLISION",
            "name": "Intra-Canon Collision",
            "trigger": "Opponent quotes Paul to abolish Law",
            "execution": "Project Matthew 5:17-19 directly against Galatians 3:13"
        }
    ]
}

ctl_strat = {
    "name": "ZUMA Conversation Control Strategies",
    "strategies": [
        {
            "id": "CTL-STRAT-EVASION-KILL",
            "name": "Hard Anchor Evasion Interception",
            "trigger": "Opponent talks about family, folklore, or irrelevant stories > 20s",
            "execution": "Interrupt firmly, reject new branch, restate initial closed question"
        }
    ]
}

with open(os.path.join(strat_dir, "questioning-strategies.json"), "w", encoding="utf-8") as f:
    json.dump(q_strat, f, indent=2)
with open(os.path.join(strat_dir, "cross-examination-strategies.json"), "w", encoding="utf-8") as f:
    json.dump(cx_strat, f, indent=2)
with open(os.path.join(strat_dir, "rebuttal-strategies.json"), "w", encoding="utf-8") as f:
    json.dump(reb_strat, f, indent=2)
with open(os.path.join(strat_dir, "conversation-control-strategies.json"), "w", encoding="utf-8") as f:
    json.dump(ctl_strat, f, indent=2)

print("Generated all strategy JSON files!")
