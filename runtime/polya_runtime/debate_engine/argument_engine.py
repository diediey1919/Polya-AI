"""
Debate Arena - Argument Engine & Graph Controller
Adheres to 07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md.
Maintains persistent Argument Graph, 12 relation types, attack/defense mapping,
rebuilds, concessions, and orphan protection.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide
)

class ArgumentRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    ATTACKS = "ATTACKS"
    DEFENDS = "DEFENDS"
    REFUTES = "REFUTES"
    QUALIFIES = "QUALIFIES"
    CONTRADICTS = "CONTRADICTS"
    DEPENDS_ON = "DEPENDS_ON"
    EXTENDS = "EXTENDS"
    REBUILDS = "REBUILDS"
    ABANDONS = "ABANDONS"
    CONCEDES = "CONCEDES"

class ArgumentHierarchy(str, Enum):
    CORE = "CORE"
    SUB_ARGUMENT = "SUB_ARGUMENT"
    SUPPORTING = "SUPPORTING"
    COUNTER_ARGUMENT = "COUNTER_ARGUMENT"
    REBUTTAL = "REBUTTAL"
    DEFENSE = "DEFENSE"

class ArgumentImportance(str, Enum):
    DECISIVE = "DECISIVE"
    CENTRAL = "CENTRAL"
    IMPORTANT = "IMPORTANT"
    SUPPORTING = "SUPPORTING"
    MINOR = "MINOR"

class ArgumentStatus(str, Enum):
    INTRODUCED = "INTRODUCED"
    DEVELOPED = "DEVELOPED"
    CHALLENGED = "CHALLENGED"
    DEFENDED = "DEFENDED"
    WEAKENED = "WEAKENED"
    REBUILT = "REBUILT"
    QUALIFIED = "QUALIFIED"
    ABANDONED = "ABANDONED"
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"

class AttackType(str, Enum):
    PREMISE_ATTACK = "PREMISE_ATTACK"
    EVIDENCE_ATTACK = "EVIDENCE_ATTACK"
    INFERENCE_ATTACK = "INFERENCE_ATTACK"
    CAUSALITY_ATTACK = "CAUSALITY_ATTACK"
    SCOPE_ATTACK = "SCOPE_ATTACK"
    DEFINITION_ATTACK = "DEFINITION_ATTACK"
    IMPACT_ATTACK = "IMPACT_ATTACK"
    CONSISTENCY_ATTACK = "CONSISTENCY_ATTACK"

class DefenseType(str, Enum):
    PREMISE_DEFENSE = "PREMISE_DEFENSE"
    EVIDENCE_DEFENSE = "EVIDENCE_DEFENSE"
    INFERENCE_DEFENSE = "INFERENCE_DEFENSE"
    SCOPE_QUALIFICATION = "SCOPE_QUALIFICATION"
    COUNTER_EVIDENCE = "COUNTER_EVIDENCE"
    CLARIFICATION = "CLARIFICATION"
    REBUILD = "REBUILD"
    CONCESSION = "CONCESSION"

class ConcessionType(str, Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    CONDITIONAL = "CONDITIONAL"
    STRATEGIC = "STRATEGIC"

class AnswerStatus(str, Enum):
    UNANSWERED = "UNANSWERED"
    PARTIALLY_ANSWERED = "PARTIALLY_ANSWERED"
    ANSWERED = "ANSWERED"
    INDIRECTLY_ANSWERED = "INDIRECTLY_ANSWERED"

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ArgumentAttackItem:
    attack_id: str
    attacker: SpeakerId
    attacker_team: TeamSide
    target_argument_id: str
    attack_type: AttackType
    reason: str
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.90
    timestamp: float = field(default_factory=time.time)

@dataclass
class ArgumentDefenseItem:
    defense_id: str
    defender: SpeakerId
    defender_team: TeamSide
    target_attack_id: str
    protected_argument_id: str
    defense_type: DefenseType
    reason: str
    evidence_refs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@dataclass
class ArgumentNode:
    argument_id: str
    speaker_id: SpeakerId
    team: TeamSide
    claim_text: str
    premises: List[str] = field(default_factory=list)
    conclusion: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    claim_refs: List[str] = field(default_factory=list)
    hierarchy: ArgumentHierarchy = ArgumentHierarchy.CORE
    importance: ArgumentImportance = ArgumentImportance.CENTRAL
    status: ArgumentStatus = ArgumentStatus.INTRODUCED
    answer_status: AnswerStatus = AnswerStatus.UNANSWERED
    parent_argument_id: Optional[str] = None
    target_argument_id: Optional[str] = None
    relation: Optional[ArgumentRelation] = None
    rebuilt_from_id: Optional[str] = None
    attacks: List[ArgumentAttackItem] = field(default_factory=list)
    defenses: List[ArgumentDefenseItem] = field(default_factory=list)
    confidence: float = 0.90
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

# ---------------------------------------------------------------------------
# Argument Graph Engine
# ---------------------------------------------------------------------------

class ArgumentGraphEngine:
    """Maintains official persistent Argument Graph with strict relational validation."""

    def __init__(self):
        self.nodes: Dict[str, ArgumentNode] = {}
        self._arg_counter: int = 0

    def register_argument(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        claim_text: str,
        premises: Optional[List[str]] = None,
        conclusion: str = "",
        evidence_refs: Optional[List[str]] = None,
        claim_refs: Optional[List[str]] = None,
        hierarchy: ArgumentHierarchy = ArgumentHierarchy.CORE,
        importance: ArgumentImportance = ArgumentImportance.CENTRAL,
        parent_argument_id: Optional[str] = None,
        target_argument_id: Optional[str] = None,
        relation: Optional[ArgumentRelation] = None
    ) -> ArgumentNode:
        # Orphan Protection: check parent or target existence if specified
        if parent_argument_id and parent_argument_id not in self.nodes:
            raise ValueError(f"Orphan Protection: Parent argument '{parent_argument_id}' does not exist.")
        if target_argument_id and target_argument_id not in self.nodes:
            raise ValueError(f"Orphan Protection: Target argument '{target_argument_id}' does not exist.")

        self._arg_counter += 1
        prefix = "PRO" if team == TeamSide.PROPOSITION else "CON"
        arg_id = f"{prefix}-ARG-{self._arg_counter:03d}"

        node = ArgumentNode(
            argument_id=arg_id,
            speaker_id=speaker_id,
            team=team,
            claim_text=claim_text,
            premises=premises or [],
            conclusion=conclusion,
            evidence_refs=evidence_refs or [],
            claim_refs=claim_refs or [],
            hierarchy=hierarchy,
            importance=importance,
            status=ArgumentStatus.INTRODUCED,
            parent_argument_id=parent_argument_id,
            target_argument_id=target_argument_id,
            relation=relation
        )
        self.nodes[arg_id] = node
        return node

    def add_attack(
        self,
        attacker: SpeakerId,
        attacker_team: TeamSide,
        target_argument_id: str,
        attack_type: AttackType,
        reason: str,
        evidence_refs: Optional[List[str]] = None,
        confidence: float = 0.90
    ) -> ArgumentAttackItem:
        if target_argument_id not in self.nodes:
            raise ValueError(f"Orphan Protection: Cannot attack nonexistent argument '{target_argument_id}'.")

        target_node = self.nodes[target_argument_id]
        attack_id = f"ATK-{uuid.uuid4().hex[:8]}"
        attack = ArgumentAttackItem(
            attack_id=attack_id,
            attacker=attacker,
            attacker_team=attacker_team,
            target_argument_id=target_argument_id,
            attack_type=attack_type,
            reason=reason,
            evidence_refs=evidence_refs or [],
            confidence=confidence
        )
        target_node.attacks.append(attack)
        target_node.status = ArgumentStatus.CHALLENGED
        target_node.updated_at = time.time()
        return attack

    def add_defense(
        self,
        defender: SpeakerId,
        defender_team: TeamSide,
        target_attack_id: str,
        protected_argument_id: str,
        defense_type: DefenseType,
        reason: str,
        evidence_refs: Optional[List[str]] = None
    ) -> ArgumentDefenseItem:
        if protected_argument_id not in self.nodes:
            raise ValueError(f"Orphan Protection: Cannot defend nonexistent argument '{protected_argument_id}'.")

        target_node = self.nodes[protected_argument_id]
        defense_id = f"DEF-{uuid.uuid4().hex[:8]}"
        defense = ArgumentDefenseItem(
            defense_id=defense_id,
            defender=defender,
            defender_team=defender_team,
            target_attack_id=target_attack_id,
            protected_argument_id=protected_argument_id,
            defense_type=defense_type,
            reason=reason,
            evidence_refs=evidence_refs or []
        )
        target_node.defenses.append(defense)
        target_node.status = ArgumentStatus.DEFENDED
        target_node.answer_status = AnswerStatus.ANSWERED
        target_node.updated_at = time.time()
        return defense

    def rebuild_argument(
        self,
        original_argument_id: str,
        speaker_id: SpeakerId,
        team: TeamSide,
        qualified_claim: str,
        new_premises: List[str],
        reason: str
    ) -> ArgumentNode:
        """Preserves original damaged argument while creating linked rebuilt version."""
        if original_argument_id not in self.nodes:
            raise ValueError(f"Orphan Protection: Original argument '{original_argument_id}' not found.")

        orig_node = self.nodes[original_argument_id]
        orig_node.status = ArgumentStatus.WEAKENED
        
        rebuilt = self.register_argument(
            speaker_id=speaker_id,
            team=team,
            claim_text=qualified_claim,
            premises=new_premises,
            hierarchy=orig_node.hierarchy,
            importance=orig_node.importance,
            parent_argument_id=original_argument_id,
            relation=ArgumentRelation.REBUILDS
        )
        rebuilt.rebuilt_from_id = original_argument_id
        rebuilt.status = ArgumentStatus.REBUILT
        orig_node.updated_at = time.time()
        return rebuilt

    def update_unanswered_status(self, argument_id: str, status: AnswerStatus):
        if argument_id in self.nodes:
            self.nodes[argument_id].answer_status = status
            self.nodes[argument_id].updated_at = time.time()
