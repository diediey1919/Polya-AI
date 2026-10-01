"""
Hierarchical Synthesis Engine (Task 3.7).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principle:
  SYNTHESIS IS AGGREGATION, NOT INVENTION.
  HIGHER SCOPES DO NOT CREATE NEW EVIDENCE.

Epistemic Firewalls & Invariants:
  1. Directionality Invariant:
     Strict bottom-up induction: PERICOPE -> SECTION -> BOOK -> CORPUS -> CANON.
     Reverse dependencies and circular scope references are strictly forbidden.
  2. Bottom-up Epistemic Derivation:
     Every higher-scope claim must trace to constituent support from lower-level records.
  3. Anti-Harmonization Firewall:
     Divergent authors and traditions are never forced into false consensus.
     Unresolved conflicts are persisted explicitly as TENSION / COMPETING / UNRESOLVED.
  4. Weakest-Critical-Dependency Propagation:
     Confidence of synthesis claim <= min(critical constituent confidences).
     No arithmetic averaging, vote counts, or frequency escalation.
  5. Authorial Distinctives:
     Author-specific theological claims remain separated unless explicit dependency exists.
  6. Reception Firewall:
     E11/E12 reception history cannot be converted into original authorial intent (E0-E5).
  7. Evidence Tier Protection:
     E0-E12 and T0-T4 classifications are preserved across all synthesis scopes.
  8. Immutability & Provenance:
     All synthesis records trace to cryptographic provenance; UPDATE/DELETE blocked.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    SynthesisAuthorialDistinctiveViolationError,
    SynthesisCircularDependencyError,
    SynthesisConcurrencyError,
    SynthesisConfidenceInflationError,
    SynthesisEvidenceTierViolationError,
    SynthesisHarmonizationError,
    SynthesisImmutabilityError,
    SynthesisInvalidProvenanceError,
    SynthesisInvalidVersionError,
    SynthesisMissingConstituentError,
    SynthesisNotFoundError,
    SynthesisReceptionAuthorialFirewallError,
    SynthesisReverseScopeError,
    SynthesisScopeJumpError,
    SynthesisSubsystemError,
    SynthesisValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class SynthesisScope(str, Enum):
    PERICOPE = "PERICOPE"
    SECTION = "SECTION"
    BOOK = "BOOK"
    CORPUS = "CORPUS"
    CANON = "CANON"


# Strict hierarchical order for bottom-up progression
SCOPE_ORDER: Dict[SynthesisScope, int] = {
    SynthesisScope.PERICOPE: 1,
    SynthesisScope.SECTION: 2,
    SynthesisScope.BOOK: 3,
    SynthesisScope.CORPUS: 4,
    SynthesisScope.CANON: 5,
}


class SynthesisRunStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


class SynthesisClaimStatus(str, Enum):
    CONVERGENT = "CONVERGENT"
    TENSION = "TENSION"
    COMPETING = "COMPETING"
    UNRESOLVED = "UNRESOLVED"
    SUPERSEDED = "SUPERSEDED"


class SynthesisTensionType(str, Enum):
    AUTHORIAL_DIVERGENCE = "AUTHORIAL_DIVERGENCE"
    CHRONOLOGICAL_DEVELOPMENT = "CHRONOLOGICAL_DEVELOPMENT"
    GENRE_DISPARITY = "GENRE_DISPARITY"
    COMPETING_THEOLOGICAL_EMPHASIS = "COMPETING_THEOLOGICAL_EMPHASIS"
    UNRESOLVED_ANTINOMY = "UNRESOLVED_ANTINOMY"


class SynthesisTensionResolution(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    PRESERVED_TENSION = "PRESERVED_TENSION"
    HISTORICAL_DEVELOPMENT = "HISTORICAL_DEVELOPMENT"
    SUPERSEDED = "SUPERSEDED"


def compute_canonical_hash(payload: Any) -> str:
    """Compute deterministic SHA-256 hash of a serializable object."""
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


# =============================================================================
# INPUT & RECORD DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class ConstituentInput:
    """Input definition for a constituent evidence / adjudication link."""
    constituent_scope: SynthesisScope
    constituent_target_id: str
    constituent_confidence: float
    is_critical_dependency: bool = True
    constituent_claim_id: Optional[str] = None
    constituent_adjudication_verdict_id: Optional[str] = None
    constituent_graph_node_id: Optional[str] = None
    constituent_evidence_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisClaimInput:
    """Input definition for a synthesized claim."""
    claim_id: str
    claim_tier: ClaimTier
    primary_evidence_class: EvidenceClass
    claim_text: str
    epistemic_status: SynthesisClaimStatus
    authorial_context: str
    constituents: Sequence[ConstituentInput]
    is_harmonized: bool = False
    explicit_confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisTensionInput:
    """Input definition for an explicit tension record between divergent claims."""
    tension_id: str
    tension_type: SynthesisTensionType
    primary_claim_id: str
    secondary_claim_id: str
    description: str
    preservation_rationale: str
    resolution_status: SynthesisTensionResolution = SynthesisTensionResolution.UNRESOLVED
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisRunConfig:
    """Execution configuration for a hierarchical synthesis run."""
    synthesizer_id: str = "POLYA-HIERARCHICAL-SYNTHESIS-V2"
    synthesizer_version: str = "2.0.0"
    enforce_strict_scope_hierarchy: bool = True
    enforce_anti_harmonization: bool = True
    enforce_authorial_distinctives: bool = True
    enforce_reception_firewall: bool = True
    allow_direct_pericope_to_book: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisRunRecord:
    run_id: str
    scope: SynthesisScope
    target_id: str
    parent_scope: Optional[SynthesisScope]
    parent_target_id: Optional[str]
    synthesizer_id: str
    synthesizer_version: str
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    aggregate_confidence: float
    status: SynthesisRunStatus
    is_exact_reproducible: bool
    provenance_id: str
    version_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisClaimRecord:
    claim_id: str
    run_id: str
    scope: SynthesisScope
    target_id: str
    claim_tier: ClaimTier
    primary_evidence_class: EvidenceClass
    claim_text: str
    epistemic_status: SynthesisClaimStatus
    synthesized_confidence: float
    weakest_constituent_confidence: float
    authorial_context: str
    is_harmonized: bool
    provenance_id: str
    version_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisTensionRecord:
    tension_id: str
    run_id: str
    scope: SynthesisScope
    target_id: str
    tension_type: SynthesisTensionType
    primary_claim_id: str
    secondary_claim_id: str
    description: str
    preservation_rationale: str
    resolution_status: SynthesisTensionResolution
    provenance_id: str
    version_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisConstituentRecord:
    constituent_link_id: str
    run_id: str
    claim_id: str
    constituent_scope: SynthesisScope
    constituent_target_id: str
    constituent_claim_id: Optional[str]
    constituent_adjudication_verdict_id: Optional[str]
    constituent_graph_node_id: Optional[str]
    constituent_evidence_id: Optional[str]
    constituent_confidence: float
    is_critical_dependency: bool
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SynthesisRunResult:
    run_id: str
    scope: SynthesisScope
    target_id: str
    status: SynthesisRunStatus
    aggregate_confidence: float
    claims_created: int
    tensions_created: int
    constituents_linked: int
    provenance_id: str
    version_id: str
    input_content_hash: str
    configuration_hash: str
    output_hash: str
    created_at: str


# =============================================================================
# HIERARCHICAL SYNTHESIS MANAGER
# =============================================================================

class HierarchicalSynthesisManager:
    """
    Subsystem manager for Hierarchical Synthesis Engine (Task 3.7).
    Aggregates evidence inductively across PERICOPE -> SECTION -> BOOK -> CORPUS -> CANON.
    Enforces directionality, anti-harmonization, weakest-link confidence, and epistemic firewalls.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        version_manager: VersionManager,
        provenance_tracker: ProvenanceTracker,
    ) -> None:
        self.engine = engine
        self.version_manager = version_manager
        self.provenance_tracker = provenance_tracker

    # -------------------------------------------------------------------------
    # 1. SYNTHESIS EXECUTION & BUILD
    # -------------------------------------------------------------------------

    def create_synthesis_run(
        self,
        scope: SynthesisScope,
        target_id: str,
        claims: Sequence[SynthesisClaimInput],
        tensions: Sequence[SynthesisTensionInput] = (),
        parent_scope: Optional[SynthesisScope] = None,
        parent_target_id: Optional[str] = None,
        config: Optional[SynthesisRunConfig] = None,
        run_id: Optional[str] = None,
    ) -> SynthesisRunResult:
        """
        Atomically persist a hierarchical synthesis run with claims, constituents, and tensions.
        Enforces bottom-up directionality, weakest-link confidence, and anti-harmonization firewalls.
        """
        cfg = config or SynthesisRunConfig()
        now = datetime.now(timezone.utc).isoformat()
        actual_run_id = run_id or f"SYNTH-RUN-{hashlib.sha256(now.encode('utf-8')).hexdigest()[:12].upper()}"

        # 1. Structural & invariant validation
        if not isinstance(scope, SynthesisScope):
            raise SynthesisValidationError(f"Invalid scope: {scope}")
        if not target_id or not target_id.strip():
            raise SynthesisValidationError("Synthesis target_id cannot be empty.")
        if not claims:
            raise SynthesisValidationError(f"Synthesis run at scope {scope.value} must contain at least one claim.")

        # Check self-feeding, circularity, and duplicate claim IDs
        seen_claim_ids: Set[str] = set()
        for c in claims:
            if c.claim_id in seen_claim_ids:
                raise SynthesisValidationError(
                    f"Duplicate claim_id '{c.claim_id}' detected in synthesis claims batch."
                )
            seen_claim_ids.add(c.claim_id)

            for con in c.constituents:
                if con.constituent_scope == scope and con.constituent_target_id == target_id:
                    raise SynthesisCircularDependencyError(
                        f"Circular synthesis rejected: target '{target_id}' at scope '{scope.value}' "
                        f"cannot use itself as constituent."
                    )

        # 2. Validate scope progression & firewalls on claims
        computed_claim_confidences: Dict[str, Tuple[float, float]] = {}
        for c in claims:
            synth_conf, weakest_conf = self._validate_and_compute_claim_confidence(
                scope=scope,
                target_id=target_id,
                claim_input=c,
                config=cfg,
            )
            computed_claim_confidences[c.claim_id] = (synth_conf, weakest_conf)

        # 3. Validate tensions
        claim_map = {c.claim_id: c for c in claims}
        self._validate_tensions(tensions, claim_map, scope, target_id, cfg)

        # 4. Compute aggregate run confidence: weakest link of all claims
        all_claim_confs = [c_conf[0] for c_conf in computed_claim_confidences.values()]
        aggregate_confidence = min(all_claim_confs) if all_claim_confs else 0.0

        # 5. Compute deterministic hashes
        input_payload = {
            "scope": scope.value,
            "target_id": target_id,
            "parent_scope": parent_scope.value if parent_scope else None,
            "parent_target_id": parent_target_id,
            "claims": [
                {
                    "claim_id": c.claim_id,
                    "claim_tier": c.claim_tier.value,
                    "primary_evidence_class": c.primary_evidence_class.value,
                    "claim_text": c.claim_text,
                    "epistemic_status": c.epistemic_status.value,
                    "authorial_context": c.authorial_context,
                    "is_harmonized": c.is_harmonized,
                    "explicit_confidence": c.explicit_confidence,
                    "metadata": c.metadata,
                    "constituents": [
                        {
                            "constituent_scope": con.constituent_scope.value,
                            "constituent_target_id": con.constituent_target_id,
                            "constituent_confidence": con.constituent_confidence,
                            "is_critical_dependency": con.is_critical_dependency,
                            "constituent_claim_id": con.constituent_claim_id,
                            "constituent_adjudication_verdict_id": con.constituent_adjudication_verdict_id,
                            "constituent_graph_node_id": con.constituent_graph_node_id,
                            "constituent_evidence_id": con.constituent_evidence_id,
                            "metadata": con.metadata,
                        }
                        for con in c.constituents
                    ],
                }
                for c in claims
            ],
            "tensions": [asdict(t) for t in tensions],
        }
        input_hash = compute_canonical_hash(input_payload)
        config_hash = compute_canonical_hash(asdict(cfg))
        output_hash = compute_canonical_hash({
            "run_id": actual_run_id,
            "scope": scope.value,
            "target_id": target_id,
            "aggregate_confidence": aggregate_confidence,
            "claim_count": len(claims),
            "tension_count": len(tensions),
        })

        # 6. Database Atomic Write Transaction
        with self.engine.transaction() as conn:
            # Check duplicate run_id
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM synthesis_runs WHERE run_id = ?", (actual_run_id,))
            if cursor.fetchone():
                raise SynthesisConcurrencyError(f"Duplicate synthesis run_id '{actual_run_id}'.")

            # Check constituent foreign keys if specified
            self._verify_constituent_references(conn, claims)

            # Create provenance and version for the run
            prov_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.INTERPRETATION,
                target_id=actual_run_id,
                content=f"SYNTH_RUN:{actual_run_id}:{output_hash}",
                input_data=input_hash,
                agent_id=cfg.synthesizer_id,
                agent_version=cfg.synthesizer_version,
                conn=conn,
            )

            ver_rec = self.version_manager.create_version(
                object_id=actual_run_id,
                object_type="SYNTHESIS_RUN",
                content_hash=output_hash,
                change_reason=ChangeReason.INITIAL_CREATION,
                provenance_id=prov_rec.provenance_id,
                created_by=cfg.synthesizer_id,
                conn=conn,
            )

            # Insert synthesis_run
            conn.execute(
                """
                INSERT INTO synthesis_runs (
                    run_id, scope, target_id, parent_scope, parent_target_id,
                    synthesizer_id, synthesizer_version, configuration_hash,
                    input_content_hash, output_hash, aggregate_confidence,
                    status, is_exact_reproducible, provenance_id, version_id,
                    created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    actual_run_id,
                    scope.value,
                    target_id,
                    parent_scope.value if parent_scope else None,
                    parent_target_id,
                    cfg.synthesizer_id,
                    cfg.synthesizer_version,
                    config_hash,
                    input_hash,
                    output_hash,
                    aggregate_confidence,
                    SynthesisRunStatus.COMPLETED.value,
                    1,
                    prov_rec.provenance_id,
                    ver_rec.version_id,
                    now,
                    json.dumps(cfg.metadata) if cfg.metadata else None,
                ),
            )

            # Insert claims and constituents
            total_constituents = 0
            for c in claims:
                synth_conf, weakest_conf = computed_claim_confidences[c.claim_id]
                c_hash = compute_canonical_hash(asdict(c))

                claim_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.CLAIM,
                    target_id=c.claim_id,
                    content=f"SYNTH_CLAIM:{c.claim_id}:{c_hash}",
                    parent_provenance_id=prov_rec.provenance_id,
                    agent_id=cfg.synthesizer_id,
                    agent_version=cfg.synthesizer_version,
                    conn=conn,
                )

                claim_ver = self.version_manager.create_version(
                    object_id=c.claim_id,
                    object_type="SYNTHESIS_CLAIM",
                    content_hash=c_hash,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    provenance_id=claim_prov.provenance_id,
                    created_by=cfg.synthesizer_id,
                    conn=conn,
                )

                conn.execute(
                    """
                    INSERT INTO synthesis_claims (
                        claim_id, run_id, scope, target_id, claim_tier,
                        primary_evidence_class, claim_text, epistemic_status,
                        synthesized_confidence, weakest_constituent_confidence,
                        authorial_context, is_harmonized, provenance_id, version_id,
                        created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        c.claim_id,
                        actual_run_id,
                        scope.value,
                        target_id,
                        c.claim_tier.value,
                        c.primary_evidence_class.value,
                        c.claim_text,
                        c.epistemic_status.value,
                        synth_conf,
                        weakest_conf,
                        c.authorial_context,
                        1 if c.is_harmonized else 0,
                        claim_prov.provenance_id,
                        claim_ver.version_id,
                        now,
                        json.dumps(c.metadata) if c.metadata else None,
                    ),
                )

                # Insert constituents
                for con in c.constituents:
                    con_sig = f"{c.claim_id}_{con.constituent_scope.value}_{con.constituent_target_id}_{total_constituents}"
                    link_id = f"CONST-{hashlib.sha256(con_sig.encode('utf-8')).hexdigest()[:12].upper()}"
                    conn.execute(
                        """
                        INSERT INTO synthesis_constituents (
                            constituent_link_id, run_id, claim_id, constituent_scope,
                            constituent_target_id, constituent_claim_id,
                            constituent_adjudication_verdict_id, constituent_graph_node_id,
                            constituent_evidence_id, constituent_confidence,
                            is_critical_dependency, created_at, is_immutable, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                        """,
                        (
                            link_id,
                            actual_run_id,
                            c.claim_id,
                            con.constituent_scope.value,
                            con.constituent_target_id,
                            con.constituent_claim_id,
                            con.constituent_adjudication_verdict_id,
                            con.constituent_graph_node_id,
                            con.constituent_evidence_id,
                            con.constituent_confidence,
                            1 if con.is_critical_dependency else 0,
                            now,
                            json.dumps(con.metadata) if con.metadata else None,
                        ),
                    )
                    total_constituents += 1

            # Insert tensions
            for t in tensions:
                t_hash = compute_canonical_hash(asdict(t))
                t_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.INTERPRETATION,
                    target_id=t.tension_id,
                    content=f"SYNTH_TENSION:{t.tension_id}:{t_hash}",
                    parent_provenance_id=prov_rec.provenance_id,
                    agent_id=cfg.synthesizer_id,
                    agent_version=cfg.synthesizer_version,
                    conn=conn,
                )

                t_ver = self.version_manager.create_version(
                    object_id=t.tension_id,
                    object_type="SYNTHESIS_TENSION",
                    content_hash=t_hash,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    provenance_id=t_prov.provenance_id,
                    created_by=cfg.synthesizer_id,
                    conn=conn,
                )

                conn.execute(
                    """
                    INSERT INTO synthesis_tensions (
                        tension_id, run_id, scope, target_id, tension_type,
                        primary_claim_id, secondary_claim_id, description,
                        preservation_rationale, resolution_status, provenance_id,
                        version_id, created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        t.tension_id,
                        actual_run_id,
                        scope.value,
                        target_id,
                        t.tension_type.value,
                        t.primary_claim_id,
                        t.secondary_claim_id,
                        t.description,
                        t.preservation_rationale,
                        t.resolution_status.value,
                        t_prov.provenance_id,
                        t_ver.version_id,
                        now,
                        json.dumps(t.metadata) if t.metadata else None,
                    ),
                )

        return SynthesisRunResult(
            run_id=actual_run_id,
            scope=scope,
            target_id=target_id,
            status=SynthesisRunStatus.COMPLETED,
            aggregate_confidence=aggregate_confidence,
            claims_created=len(claims),
            tensions_created=len(tensions),
            constituents_linked=total_constituents,
            provenance_id=prov_rec.provenance_id,
            version_id=ver_rec.version_id,
            input_content_hash=input_hash,
            configuration_hash=config_hash,
            output_hash=output_hash,
            created_at=now,
        )

    # -------------------------------------------------------------------------
    # 2. EPISTEMIC FIREWALL & CONFIDENCE VALIDATION
    # -------------------------------------------------------------------------

    def _validate_and_compute_claim_confidence(
        self,
        scope: SynthesisScope,
        target_id: str,
        claim_input: SynthesisClaimInput,
        config: SynthesisRunConfig,
    ) -> Tuple[float, float]:
        """
        Validate epistemic firewalls and calculate weakest-link confidence.
        Returns: (synthesized_confidence, weakest_constituent_confidence)
        """
        if not claim_input.claim_id or not claim_input.claim_id.strip():
            raise SynthesisValidationError("Claim definition missing valid claim_id.")
        if not claim_input.claim_text or not claim_input.claim_text.strip():
            raise SynthesisValidationError(f"Claim '{claim_input.claim_id}' claim_text cannot be empty.")
        if not claim_input.authorial_context or not claim_input.authorial_context.strip():
            raise SynthesisValidationError(f"Claim '{claim_input.claim_id}' must specify authorial_context.")

        # Require at least one constituent
        if not claim_input.constituents:
            raise SynthesisMissingConstituentError(
                f"Bottom-up derivation violation: Claim '{claim_input.claim_id}' has no constituent evidence."
            )

        current_level = SCOPE_ORDER[scope]
        critical_confidences: List[float] = []

        for con in claim_input.constituents:
            if not (0.0 <= con.constituent_confidence <= 1.0):
                raise SynthesisConfidenceInflationError(
                    f"Constituent confidence {con.constituent_confidence} out of bounds [0.0, 1.0]."
                )

            con_level = SCOPE_ORDER[con.constituent_scope]

            # Invariant 1: Directionality - constituents MUST be strictly lower scope
            if con_level >= current_level:
                raise SynthesisReverseScopeError(
                    f"Directionality Invariant Violated: Synthesis at scope '{scope.value}' "
                    f"cannot consume equal or higher scope constituent '{con.constituent_scope.value}'."
                )

            # Invariant 2: Scope hierarchy progression
            if config.enforce_strict_scope_hierarchy:
                expected_lower = current_level - 1
                if con_level != expected_lower:
                    # Check exception: PERICOPE -> BOOK allowed if configured
                    if not (config.allow_direct_pericope_to_book and scope == SynthesisScope.BOOK and con.constituent_scope == SynthesisScope.PERICOPE):
                        raise SynthesisScopeJumpError(
                            f"Scope Progression Violated: Synthesis at scope '{scope.value}' (level {current_level}) "
                            f"cannot skip directly to constituent '{con.constituent_scope.value}' (level {con_level})."
                        )

            if con.is_critical_dependency:
                critical_confidences.append(con.constituent_confidence)

        # Invariant 3: Reception Firewall
        # E11/E12 cannot be synthesized as authorial corpus or book theology without qualification
        if config.enforce_reception_firewall:
            is_reception = claim_input.primary_evidence_class in (
                EvidenceClass.E11_EARLY_RECEPTION,
                EvidenceClass.E12_LATER_INTERPRETATION,
            )
            is_authorial_scope = scope in (SynthesisScope.BOOK, SynthesisScope.CORPUS)
            if is_reception and is_authorial_scope:
                # Unless explicitly tagged as reception history in authorial_context
                if "RECEPTION" not in claim_input.authorial_context.upper():
                    raise SynthesisReceptionAuthorialFirewallError(
                        f"Reception Firewall: E11/E12 reception evidence on claim '{claim_input.claim_id}' "
                        f"cannot be converted into original authorial meaning at scope '{scope.value}'."
                    )

        # Invariant 4: Anti-Harmonization Check
        # Forced harmonization (is_harmonized=True without TENSION) is rejected
        if config.enforce_anti_harmonization and claim_input.is_harmonized:
            if claim_input.epistemic_status not in (SynthesisClaimStatus.TENSION, SynthesisClaimStatus.COMPETING, SynthesisClaimStatus.UNRESOLVED):
                raise SynthesisHarmonizationError(
                    f"Anti-Harmonization Firewall: Claim '{claim_input.claim_id}' marked is_harmonized=True "
                    f"but status is '{claim_input.epistemic_status.value}'. Forced harmonization without tension is forbidden."
                )

        # Invariant 5: Weakest-Link Confidence
        all_confidences = [con.constituent_confidence for con in claim_input.constituents]
        weakest_constituent = min(critical_confidences) if critical_confidences else min(all_confidences)

        if claim_input.explicit_confidence is not None:
            if not (0.0 <= claim_input.explicit_confidence <= 1.0):
                raise SynthesisConfidenceInflationError(
                    f"Explicit confidence {claim_input.explicit_confidence} out of bounds [0.0, 1.0]."
                )
            # Cannot exceed weakest constituent
            if claim_input.explicit_confidence > weakest_constituent + 0.00001:
                raise SynthesisConfidenceInflationError(
                    f"Confidence Inflation Rejected: Claim '{claim_input.claim_id}' confidence "
                    f"{claim_input.explicit_confidence:.4f} exceeds weakest critical constituent "
                    f"{weakest_constituent:.4f}."
                )
            synth_conf = claim_input.explicit_confidence
        else:
            synth_conf = weakest_constituent

        return synth_conf, weakest_constituent

    def _validate_tensions(
        self,
        tensions: Sequence[SynthesisTensionInput],
        claim_map: Dict[str, SynthesisClaimInput],
        scope: SynthesisScope,
        target_id: str,
        config: SynthesisRunConfig,
    ) -> None:
        """Validate tension pairs, self-reference prevention, and authorial distinctives."""
        tension_ids = set()
        for t in tensions:
            if not t.tension_id or not t.tension_id.strip():
                raise SynthesisValidationError("Tension missing valid tension_id.")
            if t.tension_id in tension_ids:
                raise SynthesisValidationError(f"Duplicate tension_id '{t.tension_id}'.")
            tension_ids.add(t.tension_id)

            if t.primary_claim_id == t.secondary_claim_id:
                raise SynthesisValidationError(
                    f"Tension '{t.tension_id}' cannot connect claim '{t.primary_claim_id}' to itself."
                )

            # Both claims must exist in batch or database
            primary = claim_map.get(t.primary_claim_id) or self._get_synthesis_claim(t.primary_claim_id)
            secondary = claim_map.get(t.secondary_claim_id) or self._get_synthesis_claim(t.secondary_claim_id)

            if not primary:
                raise SynthesisNotFoundError(f"Primary claim '{t.primary_claim_id}' not found for tension '{t.tension_id}'.")
            if not secondary:
                raise SynthesisNotFoundError(f"Secondary claim '{t.secondary_claim_id}' not found for tension '{t.tension_id}'.")

            # Authorial distinctives check
            if config.enforce_authorial_distinctives:
                if t.tension_type == SynthesisTensionType.AUTHORIAL_DIVERGENCE:
                    p_author = primary.authorial_context if isinstance(primary, SynthesisClaimInput) else primary.authorial_context
                    s_author = secondary.authorial_context if isinstance(secondary, SynthesisClaimInput) else secondary.authorial_context
                    if p_author.strip().lower() == s_author.strip().lower():
                        raise SynthesisAuthorialDistinctiveViolationError(
                            f"Authorial Divergence Tension '{t.tension_id}' requires distinct authors, "
                            f"both claims have '{p_author}'."
                        )

    def _verify_constituent_references(
        self,
        conn: sqlite3.Connection,
        claims: Sequence[SynthesisClaimInput],
    ) -> None:
        """Verify that referenced verdict, node, or evidence IDs exist if specified."""
        cursor = conn.cursor()
        for c in claims:
            for con in c.constituents:
                if con.constituent_adjudication_verdict_id:
                    cursor.execute(
                        "SELECT 1 FROM adjudicated_verdicts WHERE verdict_id = ?",
                        (con.constituent_adjudication_verdict_id,),
                    )
                    if not cursor.fetchone():
                        raise SynthesisNotFoundError(
                            f"Constituent adjudication verdict '{con.constituent_adjudication_verdict_id}' not found."
                        )

                if con.constituent_graph_node_id:
                    cursor.execute(
                        "SELECT 1 FROM graph_nodes WHERE node_id = ?",
                        (con.constituent_graph_node_id,),
                    )
                    if not cursor.fetchone():
                        raise SynthesisNotFoundError(
                            f"Constituent graph node '{con.constituent_graph_node_id}' not found."
                        )

                if con.constituent_evidence_id:
                    cursor.execute(
                        "SELECT 1 FROM evidence_ledger WHERE evidence_id = ?",
                        (con.constituent_evidence_id,),
                    )
                    if not cursor.fetchone():
                        raise SynthesisNotFoundError(
                            f"Constituent evidence '{con.constituent_evidence_id}' not found."
                        )

                if con.constituent_claim_id:
                    cursor.execute(
                        """
                        SELECT 1 FROM synthesis_claims WHERE claim_id = ?
                        UNION
                        SELECT 1 FROM claims WHERE claim_id = ?
                        """,
                        (con.constituent_claim_id, con.constituent_claim_id),
                    )
                    if not cursor.fetchone():
                        raise SynthesisNotFoundError(
                            f"Constituent claim '{con.constituent_claim_id}' not found."
                        )

    # -------------------------------------------------------------------------
    # 3. RETRIEVAL & QUERY INTERFACES
    # -------------------------------------------------------------------------

    def get_synthesis_run(self, run_id: str) -> SynthesisRunRecord:
        """Retrieve synthesis run metadata by ID."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT run_id, scope, target_id, parent_scope, parent_target_id,
                       synthesizer_id, synthesizer_version, configuration_hash,
                       input_content_hash, output_hash, aggregate_confidence,
                       status, is_exact_reproducible, provenance_id, version_id,
                       created_at, metadata_json
                FROM synthesis_runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise SynthesisNotFoundError(f"Synthesis run '{run_id}' not found.")
            return SynthesisRunRecord(
                run_id=row[0],
                scope=SynthesisScope(row[1]),
                target_id=row[2],
                parent_scope=SynthesisScope(row[3]) if row[3] else None,
                parent_target_id=row[4],
                synthesizer_id=row[5],
                synthesizer_version=row[6],
                configuration_hash=row[7],
                input_content_hash=row[8],
                output_hash=row[9],
                aggregate_confidence=row[10],
                status=SynthesisRunStatus(row[11]),
                is_exact_reproducible=bool(row[12]),
                provenance_id=row[13],
                version_id=row[14],
                created_at=row[15],
                metadata=json.loads(row[16]) if row[16] else None,
            )

    def _get_synthesis_claim(self, claim_id: str) -> Optional[SynthesisClaimRecord]:
        """Internal helper to retrieve claim or None."""
        try:
            return self.get_synthesis_claim(claim_id)
        except SynthesisNotFoundError:
            return None

    def get_synthesis_claim(self, claim_id: str) -> SynthesisClaimRecord:
        """Retrieve synthesis claim by ID."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT claim_id, run_id, scope, target_id, claim_tier,
                       primary_evidence_class, claim_text, epistemic_status,
                       synthesized_confidence, weakest_constituent_confidence,
                       authorial_context, is_harmonized, provenance_id, version_id,
                       created_at, metadata_json
                FROM synthesis_claims
                WHERE claim_id = ?
                """,
                (claim_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise SynthesisNotFoundError(f"Synthesis claim '{claim_id}' not found.")
            return SynthesisClaimRecord(
                claim_id=row[0],
                run_id=row[1],
                scope=SynthesisScope(row[2]),
                target_id=row[3],
                claim_tier=ClaimTier(row[4]),
                primary_evidence_class=EvidenceClass(row[5]),
                claim_text=row[6],
                epistemic_status=SynthesisClaimStatus(row[7]),
                synthesized_confidence=row[8],
                weakest_constituent_confidence=row[9],
                authorial_context=row[10],
                is_harmonized=bool(row[11]),
                provenance_id=row[12],
                version_id=row[13],
                created_at=row[14],
                metadata=json.loads(row[15]) if row[15] else None,
            )

    def get_claims_for_target(
        self,
        scope: SynthesisScope,
        target_id: str,
        include_superseded: bool = False,
    ) -> List[SynthesisClaimRecord]:
        """Retrieve all synthesis claims for a given scope and target."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            status_clause = (
                ""
                if include_superseded
                else "AND sc.epistemic_status != 'SUPERSEDED' AND sr.status != 'SUPERSEDED'"
            )
            cursor.execute(
                f"""
                SELECT sc.claim_id, sc.run_id, sc.scope, sc.target_id, sc.claim_tier,
                       sc.primary_evidence_class, sc.claim_text, sc.epistemic_status,
                       sc.synthesized_confidence, sc.weakest_constituent_confidence,
                       sc.authorial_context, sc.is_harmonized, sc.provenance_id, sc.version_id,
                       sc.created_at, sc.metadata_json
                FROM synthesis_claims sc
                JOIN synthesis_runs sr ON sc.run_id = sr.run_id
                WHERE sc.scope = ? AND sc.target_id = ? {status_clause}
                ORDER BY sc.created_at ASC
                """,
                (scope.value, target_id),
            )
            claims = []
            for row in cursor.fetchall():
                claims.append(
                    SynthesisClaimRecord(
                        claim_id=row[0],
                        run_id=row[1],
                        scope=SynthesisScope(row[2]),
                        target_id=row[3],
                        claim_tier=ClaimTier(row[4]),
                        primary_evidence_class=EvidenceClass(row[5]),
                        claim_text=row[6],
                        epistemic_status=SynthesisClaimStatus(row[7]),
                        synthesized_confidence=row[8],
                        weakest_constituent_confidence=row[9],
                        authorial_context=row[10],
                        is_harmonized=bool(row[11]),
                        provenance_id=row[12],
                        version_id=row[13],
                        created_at=row[14],
                        metadata=json.loads(row[15]) if row[15] else None,
                    )
                )
            return claims

    def get_tensions_for_target(
        self,
        scope: SynthesisScope,
        target_id: str,
        include_superseded: bool = False,
    ) -> List[SynthesisTensionRecord]:
        """Retrieve all synthesis tensions for a given scope and target."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            status_clause = (
                ""
                if include_superseded
                else "AND st.resolution_status != 'SUPERSEDED' AND sr.status != 'SUPERSEDED'"
            )
            cursor.execute(
                f"""
                SELECT st.tension_id, st.run_id, st.scope, st.target_id, st.tension_type,
                       st.primary_claim_id, st.secondary_claim_id, st.description,
                       st.preservation_rationale, st.resolution_status, st.provenance_id,
                       st.version_id, st.created_at, st.metadata_json
                FROM synthesis_tensions st
                JOIN synthesis_runs sr ON st.run_id = sr.run_id
                WHERE st.scope = ? AND st.target_id = ? {status_clause}
                ORDER BY st.created_at ASC
                """,
                (scope.value, target_id),
            )
            tensions = []
            for row in cursor.fetchall():
                tensions.append(
                    SynthesisTensionRecord(
                        tension_id=row[0],
                        run_id=row[1],
                        scope=SynthesisScope(row[2]),
                        target_id=row[3],
                        tension_type=SynthesisTensionType(row[4]),
                        primary_claim_id=row[5],
                        secondary_claim_id=row[6],
                        description=row[7],
                        preservation_rationale=row[8],
                        resolution_status=SynthesisTensionResolution(row[9]),
                        provenance_id=row[10],
                        version_id=row[11],
                        created_at=row[12],
                        metadata=json.loads(row[13]) if row[13] else None,
                    )
                )
            return tensions

    def get_constituents_for_claim(self, claim_id: str) -> List[SynthesisConstituentRecord]:
        """Retrieve all constituent links for a synthesis claim."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT constituent_link_id, run_id, claim_id, constituent_scope,
                       constituent_target_id, constituent_claim_id,
                       constituent_adjudication_verdict_id, constituent_graph_node_id,
                       constituent_evidence_id, constituent_confidence,
                       is_critical_dependency, created_at, metadata_json
                FROM synthesis_constituents
                WHERE claim_id = ?
                ORDER BY created_at ASC
                """,
                (claim_id,),
            )
            constituents = []
            for row in cursor.fetchall():
                constituents.append(
                    SynthesisConstituentRecord(
                        constituent_link_id=row[0],
                        run_id=row[1],
                        claim_id=row[2],
                        constituent_scope=SynthesisScope(row[3]),
                        constituent_target_id=row[4],
                        constituent_claim_id=row[5],
                        constituent_adjudication_verdict_id=row[6],
                        constituent_graph_node_id=row[7],
                        constituent_evidence_id=row[8],
                        constituent_confidence=row[9],
                        is_critical_dependency=bool(row[10]),
                        created_at=row[11],
                        metadata=json.loads(row[12]) if row[12] else None,
                    )
                )
            return constituents

    # -------------------------------------------------------------------------
    # 4. IMMUTABILITY & SUPERSESSION
    # -------------------------------------------------------------------------

    def supersede_synthesis_run(self, run_id: str, reason: str) -> None:
        """Mark an active synthesis run as SUPERSEDED."""
        run = self.get_synthesis_run(run_id)
        if run.status == SynthesisRunStatus.SUPERSEDED:
            raise SynthesisImmutabilityError(f"Synthesis run '{run_id}' is already SUPERSEDED.")
        if run.status != SynthesisRunStatus.COMPLETED:
            raise SynthesisImmutabilityError(
                f"Cannot supersede synthesis run '{run_id}' with status '{run.status.value}'. "
                f"Only COMPLETED runs can be superseded."
            )

        with self.engine.transaction() as conn:
            conn.execute(
                "UPDATE synthesis_runs SET status = 'SUPERSEDED' WHERE run_id = ?",
                (run_id,),
            )

    def supersede_synthesis_claim(self, claim_id: str, reason: str) -> None:
        """Mark an active synthesis claim as SUPERSEDED."""
        claim = self.get_synthesis_claim(claim_id)
        if claim.epistemic_status == SynthesisClaimStatus.SUPERSEDED:
            raise SynthesisImmutabilityError(f"Synthesis claim '{claim_id}' is already SUPERSEDED.")

        with self.engine.transaction() as conn:
            conn.execute(
                "UPDATE synthesis_claims SET epistemic_status = 'SUPERSEDED' WHERE claim_id = ?",
                (claim_id,),
            )
