"""
Polia AI Runtime - Multi-Turn Conversation & Debate State Tracking (Phase 14)
Maintains formal state of active motions, claims, concessions, evidentiary challenges, and turn history.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from polya_runtime.fallacy import DetectedFallacy
from polya_runtime.drift import DriftReport

@dataclass
class DebateTurn:
    turn_number: int
    speaker: str  # 'USER' or 'POLIA'
    content: str
    intent: str = "GENERAL"
    claims_raised: List[str] = field(default_factory=list)
    fallacies: List[str] = field(default_factory=list)
    drift_status: str = "NONE"
    active_steps: List[str] = field(default_factory=list)

@dataclass
class EvidentiaryChallenge:
    id: str
    target_claim: str
    demanded_evidence_tier: str
    challenger: str
    status: str = "OPEN"  # OPEN, MET, REFUTED, ABANDONED
    response_notes: str = ""

class DebateStateTracker:
    def __init__(self, initial_motion: str = "General Apologetics Inquiry"):
        self.active_motion = initial_motion
        self.turns: List[DebateTurn] = []
        self.conceded_points: List[str] = []
        self.contested_points: List[str] = []
        self.open_challenges: List[EvidentiaryChallenge] = []

    def set_motion(self, motion: str):
        self.active_motion = motion

    def record_turn(
        self,
        speaker: str,
        content: str,
        intent: str = "GENERAL",
        claims_raised: Optional[List[str]] = None,
        fallacies: Optional[List[DetectedFallacy]] = None,
        drift_report: Optional[DriftReport] = None,
        active_steps: Optional[List[str]] = None
    ) -> DebateTurn:
        turn_num = len(self.turns) + 1
        fallacy_names = [f.name for f in fallacies] if fallacies else []
        drift_str = drift_report.drift_type if drift_report else "NONE"

        turn = DebateTurn(
            turn_number=turn_num,
            speaker=speaker.upper(),
            content=content,
            intent=intent,
            claims_raised=claims_raised or [],
            fallacies=fallacy_names,
            drift_status=drift_str,
            active_steps=active_steps or []
        )
        self.turns.append(turn)

        # Track contested points if speaker is USER and claims are raised
        if speaker.upper() == "USER" and claims_raised:
            for c in claims_raised:
                if c not in self.contested_points and c not in self.conceded_points:
                    self.contested_points.append(c)

        return turn

    def concede_point(self, claim: str):
        if claim in self.contested_points:
            self.contested_points.remove(claim)
        if claim not in self.conceded_points:
            self.conceded_points.append(claim)

    def add_evidentiary_challenge(self, target_claim: str, demanded_tier: str, challenger: str = "POLIA") -> EvidentiaryChallenge:
        cid = f"CHALLENGE-{len(self.open_challenges) + 1}"
        ch = EvidentiaryChallenge(
            id=cid,
            target_claim=target_claim,
            demanded_evidence_tier=demanded_tier,
            challenger=challenger
        )
        self.open_challenges.append(ch)
        return ch

    def resolve_evidentiary_challenge(self, challenge_id: str, status: str, notes: str = ""):
        for ch in self.open_challenges:
            if ch.id == challenge_id:
                ch.status = status
                ch.response_notes = notes
                break

    def get_summary(self) -> Dict[str, Any]:
        return {
            "active_motion": self.active_motion,
            "total_turns": len(self.turns),
            "conceded_points_count": len(self.conceded_points),
            "contested_points_count": len(self.contested_points),
            "open_challenges_count": len([c for c in self.open_challenges if c.status == "OPEN"]),
            "conceded_points": self.conceded_points,
            "contested_points": self.contested_points,
            "open_challenges": [
                {"id": c.id, "claim": c.target_claim, "tier": c.demanded_evidence_tier, "status": c.status}
                for c in self.open_challenges if c.status == "OPEN"
            ]
        }

@dataclass
class SingularityTurnResult:
    user_input: str
    opponent_archetype: str
    deconstructed_axiom: Dict[str, str]
    forecast_report: Dict[str, Any]
    steelman_summary: Dict[str, Any]
    patch_report: Dict[str, Any]
    hyper_5d_verification: Dict[str, Any]
    socratic_weapon: Dict[str, Any]
    gravity_delivery: str
    persona_applied: str = "DEFAULT"
    zuma_strategy: Optional[Dict[str, Any]] = None
    zuma_ladder: Optional[List[str]] = None

class SingularityCognitiveLoop:
    """
    Polya AI Omni-Debate Singularity Cognitive Hyper-Loop (Level 2.0).
    Executes the 5 parallel phases:
    1. DECONSTRUCT: Root Presupposition Isolation
    2. PREDICT: Decision Tree Horizon Lookahead ($T+1$ to $T+10$) & Zugzwang
    3. STEELMAN & SHADOW RED-TEAM: 100x Boosting, Clone Battle, Auto-Patching
    4. 5D HYPER-MATRIX: Simultaneous Cross-Validation (Linguistics, History, Logic, Dogmatics, Manuscripts)
    5. WEAPONIZE & DELIVER: Maieutic Socratic Trap / Fatal Dilemma with Law of Gravity persona or ZUMA Strategic Layer.
    """
    def __init__(self):
        from polya_runtime.opponent_forecaster import OpponentForecaster
        from polya_runtime.socratic_engine import SocraticEngine
        from polya_runtime.hyper_matrix import HyperDimensionalMatrix
        from polya_runtime.shadow_redteam import ShadowRedTeam
        from polya_runtime.zuma_persona import ZumaDebatePersona

        self.forecaster = OpponentForecaster()
        self.socratic = SocraticEngine()
        self.hyper_matrix = HyperDimensionalMatrix()
        self.red_team = ShadowRedTeam()
        self.zuma = ZumaDebatePersona()

    def process_turn(self, user_content: str, tradition: str = "COMPARATIVE", turn_num: int = 1, persona: str = "default") -> SingularityTurnResult:
        # 1. DECONSTRUCT
        archetype = self.forecaster.profile_opponent(user_content)
        axiom = self.forecaster.presuppositional_scan(user_content)

        # 2. PREDICT
        forecast = self.forecaster.forecast(user_content, archetype=archetype, lookahead_depth=5)

        # 3. STEELMAN & SHADOW RED-TEAM
        steel = self.red_team.steelman_claim(user_content)
        raw_draft = (
            f"Klaim '{user_content}' pasti 100% salah karena teksnya sendiri menegaskan demikian, "
            f"dan semua sejarawan sepakat naskah tertulis persis pada tahun yang konsisten."
        )
        attacks = self.red_team.simulate_adversarial_attack(raw_draft)
        patched = self.red_team.auto_patch(raw_draft, attacks)

        # 4. HYPER-DIMENSIONAL VERIFICATION MATRIX (5D)
        verification = self.hyper_matrix.evaluate(user_content, tradition=tradition)

        # 5. WEAPONIZE (Socratic Trap / Fatal Dilemma)
        primary_artifacts_str = ", ".join(verification.primary_artifacts_cited[:3])
        traps = self.socratic.build_maieutic_trap(
            topic=user_content,
            target_claim=user_content,
            evidence_data=primary_artifacts_str
        )
        dilemma = self.socratic.generate_fatal_dilemma(
            claim=user_content,
            horn_1_name="Mempertahankan Doktrin Internal Sepihak",
            horn_1_effect="Mengabaikan data fisik manuskrip primer dan menerapkan standar ganda epistemik",
            horn_2_name="Menerima Metodologi Ilmiah Universal",
            horn_2_effect="Mengakui bahwa bukti fisik primer menggugurkan premis awal Anda"
        )

        zuma_strat = None
        zuma_ladder = None

        # 6. DELIVER (Persona Formulation)
        if persona.lower() == "zuma":
            zuma_analysis = self.zuma.analyze_claim_strategy(user_content)
            zuma_strat = zuma_analysis["primary_strategy"]
            zuma_ladder = self.zuma.generate_interrogation_ladder(user_content)
            delivery = self.zuma.apply_persona_delivery(
                target_claim=user_content,
                deconstructed_axiom={
                    "ontological": axiom.ontological_premise,
                    "epistemological": axiom.epistemological_premise,
                    "methodological": axiom.methodological_premise,
                    "peritrope_inversion": axiom.peritrope_inversion
                },
                verification_confidence=verification.overall_confidence_score,
                verification_tier=verification.confidence_tier,
                primary_artifacts=verification.primary_artifacts_cited,
                socratic_dilemma=dilemma.socratic_formulation,
                strategy_info=zuma_strat
            )
            persona_name = "ZUMA"
        else:
            delivery = (
                f"Setiap klaim tekstual dan historis tunduk pada hukum realitas objektif yang tak memihak.\n\n"
                f"Dalam membedah klaim Anda ('{user_content}'), data verifikasi 5 dimensi (Filologi, Kritik Historis, "
                f"Logika Modal S5, Dogmatika, dan Forensik Transmisi) menetapkan skor kepastian Bayesian pada "
                f"{round(verification.overall_confidence_score * 100, 1)}% [{verification.confidence_tier}] "
                f"berdasarkan saksi primer ({primary_artifacts_str}).\n\n"
                f"{dilemma.socratic_formulation}\n\n"
                f"— Kebenaran tidak memerlukan retorika emosi; ia berdiri di atas berat faktanya sendiri."
            )
            persona_name = "DEFAULT"

        return SingularityTurnResult(
            user_input=user_content,
            opponent_archetype=archetype.value,
            deconstructed_axiom={
                "ontological": axiom.ontological_premise,
                "epistemological": axiom.epistemological_premise,
                "methodological": axiom.methodological_premise,
                "peritrope_inversion": axiom.peritrope_inversion
            },
            forecast_report={
                "archetype": archetype.value,
                "zugzwang_detected": forecast.zugzwang_detected,
                "recommended_path": forecast.recommended_path,
                "branches_count": len(forecast.branches),
                "branches": [
                    {
                        "id": b.branch_id,
                        "label": b.label,
                        "probability": b.probability,
                        "expected_argument": b.opponent_expected_argument,
                        "pre_indexed_artifact": b.polya_pre_indexed_artifact,
                        "is_zugzwang": b.is_zugzwang
                    }
                    for b in forecast.branches
                ]
            },
            steelman_summary={
                "formulation": steel.steelmanned_formulation,
                "factor": steel.amplification_factor,
                "foundations": steel.key_scholarly_foundations
            },
            patch_report={
                "attacks_simulated": len(attacks),
                "patches_applied": patched.patches_applied,
                "is_impervious": patched.is_epistemically_impervious
            },
            hyper_5d_verification={
                "confidence_score": verification.overall_confidence_score,
                "confidence_tier": verification.confidence_tier,
                "primary_artifacts": verification.primary_artifacts_cited,
                "dimensions": {
                    k.value: {
                        "score": v.score,
                        "status": v.status,
                        "summary": v.forensic_summary
                    }
                    for k, v in verification.dimension_scores.items()
                }
            },
            socratic_weapon={
                "stage_1_probe": traps[0].prompt_question if len(traps) > 0 else "",
                "stage_2_ratify": traps[1].prompt_question if len(traps) > 1 else "",
                "stage_3_delivery": traps[2].prompt_question if len(traps) > 2 else "",
                "constructive_dilemma": dilemma.socratic_formulation,
                "convergence": dilemma.entropy_convergence
            },
            gravity_delivery=delivery,
            persona_applied=persona_name,
            zuma_strategy=zuma_strat,
            zuma_ladder=zuma_ladder
        )

