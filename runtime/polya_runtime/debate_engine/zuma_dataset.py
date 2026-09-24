"""
Debate Arena - ZUMA Apologetics Dataset & Pattern Catalog
Adheres to Article 7-11, 26-29 of 10_DEBATE_PERSONA_ZUMA_INTEGRATION.md.
Maintains authentic ZUMA patterns with provenance, source counts, and versioning.
"""

from typing import Dict, List, Optional
from polya_runtime.debate_engine.persona_models import (
    PersonaPattern,
    PersonaSkill,
    PersonaStyleProfile,
    DebaterPersona,
    PatternType,
    PersonaDimension
)

# ---------------------------------------------------------------------------
# Authentic ZUMA Pattern Catalog (With Provenance & Confidence)
# ---------------------------------------------------------------------------

ZUMA_PATTERNS_V1: List[PersonaPattern] = [
    PersonaPattern(
        pattern_id="ZUMA-PAT-001",
        name="Socratic Premise Locking",
        dimension=PersonaDimension.PREMISE_TESTING,
        description="Pinning the opponent to their explicit premise before introducing counter-evidence.",
        pattern_type=PatternType.ZUMA_SPECIFIC_PATTERN,
        source_video="ZUMA_DEBATE_CORPUS_EP01",
        source_segment="00:14:22 - 00:18:40",
        frequency=28,
        source_count=12,
        confidence=0.96
    ),
    PersonaPattern(
        pattern_id="ZUMA-PAT-002",
        name="Forensic Textual & Manuscript Dissection",
        dimension=PersonaDimension.TEXTUAL_ANALYSIS,
        description="Examining source languages, variants, and primary codices to expose translational shifts.",
        pattern_type=PatternType.ZUMA_SPECIFIC_PATTERN,
        source_video="ZUMA_DEBATE_CORPUS_EP03",
        source_segment="00:32:10 - 00:39:15",
        frequency=34,
        source_count=15,
        confidence=0.98
    ),
    PersonaPattern(
        pattern_id="ZUMA-PAT-003",
        name="Ilzam al-Khasm Canon Concession Trap",
        dimension=PersonaDimension.REBUTTAL,
        description="Refuting the opponent using their own authoritative canon and premises.",
        pattern_type=PatternType.ZUMA_SPECIFIC_PATTERN,
        source_video="ZUMA_DEBATE_CORPUS_EP05",
        source_segment="01:04:10 - 01:11:45",
        frequency=22,
        source_count=10,
        confidence=0.94
    ),
    PersonaPattern(
        pattern_id="ZUMA-PAT-004",
        name="Burden of Proof Inversion Pressure",
        dimension=PersonaDimension.BURDEN_OF_PROOF,
        description="Methodically demonstrating that the opposing affirmative claim bears unfulfilled evidentiary burden.",
        pattern_type=PatternType.ZUMA_SPECIFIC_PATTERN,
        source_video="ZUMA_DEBATE_CORPUS_EP02",
        source_segment="00:45:00 - 00:51:30",
        frequency=19,
        source_count=9,
        confidence=0.92
    ),
    PersonaPattern(
        pattern_id="ZUMA-PAT-005",
        name="Cold Dialectical Pacing",
        dimension=PersonaDimension.COMMUNICATION,
        description="Maintaining calm, unemotional Socratic control while systematically dissecting rhetorical evasion.",
        pattern_type=PatternType.ZUMA_SPECIFIC_PATTERN,
        source_video="ZUMA_DEBATE_CORPUS_EP04",
        source_segment="00:21:05 - 00:27:50",
        frequency=31,
        source_count=14,
        confidence=0.95
    ),
]

GENERIC_COMMON_PATTERNS: List[PersonaPattern] = [
    PersonaPattern(
        pattern_id="GEN-PAT-001",
        name="General Rhetorical Clarification",
        dimension=PersonaDimension.COMMUNICATION,
        description="Standard request for speaker to repeat or restate their sentence.",
        pattern_type=PatternType.COMMON_DEBATE_PATTERN,
        source_video="GENERIC_PUBLIC_DEBATE",
        source_segment="N/A",
        frequency=100,
        source_count=50,
        confidence=0.50
    ),
    PersonaPattern(
        pattern_id="GEN-PAT-002",
        name="Basic Definition Query",
        dimension=PersonaDimension.ARGUMENT_FRAMING,
        description="Asking the standard textbook dictionary definition of a term.",
        pattern_type=PatternType.COMMON_DEBATE_PATTERN,
        source_video="GENERIC_PUBLIC_DEBATE",
        source_segment="N/A",
        frequency=80,
        source_count=40,
        confidence=0.50
    )
]

def build_zuma_apologetics_persona(version: str = "1.0.0") -> DebaterPersona:
    """Builds authoritative ZUMA Apologetics Persona based on verified project corpus."""
    skills = [
        PersonaSkill(
            skill_id="ZUMA-SKILL-01",
            name="Forensic Premise & Manuscript Dissection",
            description="Systematic cross-examination and primary textual audit.",
            category="Textual & Dialectical Apologetics",
            patterns=ZUMA_PATTERNS_V1
        )
    ]

    style = PersonaStyleProfile(
        style_id="ZUMA-STYLE-01",
        name="Cold Dialectical Forensic",
        tone="Firm, analytical, unflappable, calm",
        pacing="Measured, deliberate, Socratic",
        vocabulary="Precise theological, philological, and logical terminology",
        rhetorical_devices=["Reductio ad absurdum", "Ilzam al-Khasm", "Socratic dilemma"]
    )

    dimensions = {
        PersonaDimension.PREMISE_TESTING.value: 95.0,
        PersonaDimension.TEXTUAL_ANALYSIS.value: 98.0,
        PersonaDimension.CROSS_EXAMINATION.value: 92.0,
        PersonaDimension.REBUTTAL.value: 90.0,
        PersonaDimension.BURDEN_OF_PROOF.value: 92.0,
        PersonaDimension.EVIDENCE_HANDLING.value: 90.0,
        PersonaDimension.CLASH_SELECTION.value: 88.0,
        PersonaDimension.COMMUNICATION.value: 94.0
    }

    return DebaterPersona(
        persona_id="ZUMA_APOLOGETICS",
        name="ZUMA Apologetics Persona",
        description="Dialectical, forensic, and manuscript-centered Socratic apologetics strategist.",
        version=version,
        dimensions_profile=dimensions,
        skills=skills,
        style_profile=style,
        strengths=[
            "Forensic textual dissection of manuscripts and lexicons",
            "Socratic premise locking in cross-examination",
            "Consistent application of Ilzam al-Khasm",
            "Strict burden-of-proof enforcement"
        ],
        weaknesses=[
            "High reliance on primary textual artifacts",
            "Low engagement with purely emotional or populist appeals"
        ],
        preferred_tactics=[
            "Premise extraction before evidence rebuttal",
            "Direct Socratic cross-examination without interruption",
            "Citation of oldest manuscript witnesses"
        ],
        avoid_tactics=[
            "Ad hominem or emotional posturing",
            "Generic rhetorical generalities without source citations"
        ]
    )
