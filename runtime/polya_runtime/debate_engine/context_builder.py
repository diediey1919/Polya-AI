"""
Debate Arena - AI Context Builder
Strictly adheres to Priority Rules (Articles 41 & 44) of 02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md.
"""

import os
from typing import Dict, List, Optional, Any
from polya_runtime.debate_engine.models import (
    AIRole,
    EventStateObject,
    EventState
)

CONSTITUTION_PATH = "/home/ubuntu/Polya-AI/runtime/debate_prompts/01_DEBATE_CORE_CONSTITUTION.md"
PROTOCOL_PATH = "/home/ubuntu/Polya-AI/runtime/debate_prompts/02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md"

class OfficialArenaContextBuilder:
    """Constructs tiered, role-isolated prompt contexts for Official Arena (AI is NOT a debater)."""

    @staticmethod
    def load_cached_prompt(path: str) -> str:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return ""
        return ""

    @classmethod
    def build_context(
        cls,
        role: AIRole,
        state_obj: EventStateObject,
        role_instruction: str = "",
        specific_context: Optional[Dict[str, Any]] = None,
        persona_style: str = ""
    ) -> str:
        """
        Builds prompt following strict hierarchy:
        LEVEL 1: Core Constitution
        LEVEL 2: Event Protocol
        LEVEL 3: Current State
        LEVEL 4: Current Round Rules
        LEVEL 5: Role Instruction
        LEVEL 6: Current Context (Arguments/Claims/Evidence/Clashes)
        LEVEL 7: Persona/Style
        """
        constitution = cls.load_cached_prompt(CONSTITUTION_PATH)
        protocol = cls.load_cached_prompt(PROTOCOL_PATH)
        
        # State & Round Summary
        current_state_str = (
            f"=== LEVEL 3: CURRENT EVENT STATE ===\n"
            f"Event ID: {state_obj.event_id}\n"
            f"Topic: {state_obj.topic}\n"
            f"Current State: {state_obj.current_state.value}\n"
            f"Current Round: {state_obj.current_round}\n"
            f"Active Team: {state_obj.current_team.value if state_obj.current_team else 'NONE'}\n"
            f"Active Speaker: {state_obj.current_speaker.value if state_obj.current_speaker else 'NONE'}\n"
            f"Remaining Time: {state_obj.remaining_time}s / {state_obj.round_time}s\n"
            f"Paused: {state_obj.is_paused}\n"
        )
        
        round_rules_str = (
            f"=== LEVEL 4: CURRENT ROUND RULES ===\n"
            f"Allowed Actions: {[a.value for a in state_obj.allowed_actions]}\n"
            f"Forbidden Actions: {[a.value for a in state_obj.forbidden_actions]}\n"
        )
        
        role_str = (
            f"=== LEVEL 5: ACTIVE AI ROLE: {role.value} ===\n"
            f"{role_instruction}\n"
            f"CRITICAL CONSTRAINT: You are operating strictly as {role.value}. You must NOT act as a debater.\n"
        )
        
        # Level 6: Live context
        clashes_summary = "\n".join([f"- [{c.clash_id}] {c.title}: {c.description} (Advantage: {c.current_advantage})" for c in state_obj.active_clashes])
        args_summary = "\n".join([f"- [{a.argument_id} by {a.speaker_id.value}] {a.claim} (Status: {a.status})" for a in state_obj.active_arguments[-5:]])
        evidence_summary = "\n".join([f"- [{e.evidence_id} by {e.speaker_id.value}] {e.source_citation} ({e.source_type} - {e.verification_status.value})" for e in state_obj.active_evidence[-5:]])
        
        context_str = (
            f"=== LEVEL 6: RELEVANT LIVE CONTEXT ===\n"
            f"Active Critical Clashes:\n{clashes_summary or 'None registered yet'}\n\n"
            f"Recent Core Arguments:\n{args_summary or 'None'}\n\n"
            f"Recent Evidence Items:\n{evidence_summary or 'None'}\n"
        )
        if specific_context:
            context_str += f"\nAdditional Context: {specific_context}\n"

        persona_str = ""
        if persona_style:
            persona_str = (
                f"=== LEVEL 7: PERSONA / TONE / STYLE ===\n"
                f"{persona_style}\n"
                f"NOTE: Persona styling must never violate higher-level rules or state machine constraints.\n"
            )

        full_prompt = (
            f"{constitution}\n\n"
            f"{'='*60}\n\n"
            f"{protocol}\n\n"
            f"{'='*60}\n\n"
            f"{current_state_str}\n"
            f"{round_rules_str}\n"
            f"{role_str}\n"
            f"{context_str}\n"
            f"{persona_str}"
        )
        return full_prompt


# Alias for backwards compatibility
AIContextBuilder = OfficialArenaContextBuilder


class TrainingContextBuilder:
    """Constructs tiered prompt contexts for Training Mode (AI Debater / Examiner / Coach)."""

    @classmethod
    def build_training_context(
        cls,
        session_obj: Any,
        role_instruction: str = "",
        adaptive_profile: Optional[Dict[str, Any]] = None,
        persona_style: str = ""
    ) -> str:
        """
        Builds prompt following strict Training Prompt Hierarchy (Prompt 14 Section 39):
        1. SYSTEM SAFETY
        2. TRAINING MODE CONTRACT
        3. TRAINING STATE
        4. ROUND RULES
        5. OPPONENT ROLE & TRAINING TYPE
        6. STRATEGY & ADAPTIVE PROFILE
        7. PERSONA
        8. STYLE
        """
        # 1. System Safety
        level_1 = (
            "=== LEVEL 1: SYSTEM SAFETY & FAIRNESS ===\n"
            "You are a rigorous, fair AI training partner. Do not fabricate citations or facts.\n"
            "If using hypothetical examples, explicitly label them as HYPOTHETICAL.\n"
            "Never leak private user evaluation data or cheat using unprovided information.\n"
        )

        # 2. Training Mode Contract
        level_2 = (
            "=== LEVEL 2: TRAINING MODE CONTRACT ===\n"
            "EXECUTION CONTEXT: TRAINING_MODE\n"
            "AI ROLE: AI_TRAINING_DEBATER / EXAMINER / COACH\n"
            "You are authorized to engage as an active debate participant inside this Training Session.\n"
            "Your objective: Train and challenge the user's debate skills rigorously, without bias.\n"
        )

        # 3. Training State
        level_3 = (
            f"=== LEVEL 3: TRAINING STATE ===\n"
            f"Session ID: {session_obj.training_session_id}\n"
            f"Topic: {session_obj.topic}\n"
            f"Current State: {session_obj.current_state.value}\n"
            f"User Position: {session_obj.user_position.value}\n"
            f"AI Position: {session_obj.ai_position.value}\n"
            f"Training Type: {session_obj.training_type.value}\n"
            f"Difficulty: {session_obj.difficulty.value}\n"
            f"Active Speaker: {session_obj.active_speaker.value if session_obj.active_speaker else 'NONE'}\n"
            f"Remaining Time: {session_obj.remaining_time}s\n"
        )

        # 4. Round Rules
        level_4 = (
            f"=== LEVEL 4: ROUND RULES & PROTOCOL ===\n"
            f"Current Round: {session_obj.round_name}\n"
            f"Protocol: Adhere strictly to the debate phase ({session_obj.current_state.value}).\n"
        )

        # 5. Opponent Role
        level_5 = (
            f"=== LEVEL 5: OPPONENT ROLE & INSTRUCTION ===\n"
            f"{role_instruction}\n"
        )

        # 6. Strategy & Adaptive Profile
        adaptive_str = ""
        if adaptive_profile:
            adaptive_str = f"Adaptive Target Weaknesses: {adaptive_profile.get('weaknesses', [])}\n"
            adaptive_str += f"Focus Strategy: {adaptive_profile.get('strategy', 'Standard challenge')}\n"
        
        args_summary = "\n".join([f"- [{a.argument_id} by {a.speaker_id.value}] {a.claim}" for a in session_obj.arguments[-5:]])
        clashes_summary = "\n".join([f"- [{c.clash_id}] {c.title}: {c.description}" for c in session_obj.clashes[-3:]])
        evidence_summary = "\n".join([f"- [{e.evidence_id}] {e.source_citation}" for e in session_obj.evidence[-5:]])

        level_6 = (
            f"=== LEVEL 6: STRATEGY & RELEVANT CONTEXT ===\n"
            f"{adaptive_str}"
            f"Arguments:\n{args_summary or 'None'}\n\n"
            f"Clashes:\n{clashes_summary or 'None'}\n\n"
            f"Evidence:\n{evidence_summary or 'None'}\n"
        )

        # 7 & 8. Persona & Style
        level_7_8 = (
            f"=== LEVEL 7-8: PERSONA & STYLE ({session_obj.persona.value}) ===\n"
            f"{persona_style or 'Maintain analytical rigor, sharp questioning, and precise dialectics.'}\n"
        )

        return f"{level_1}\n\n{level_2}\n\n{level_3}\n\n{level_4}\n\n{level_5}\n\n{level_6}\n\n{level_7_8}"
