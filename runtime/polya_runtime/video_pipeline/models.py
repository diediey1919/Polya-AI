"""Data Models and Enumerations for Video Intelligence Pipeline."""

from enum import Enum
from typing import Dict, List, Any, Optional

SCHEMA_VERSION = "1.0.0"

class ClaimType(str, Enum):
    FACT_CLAIM = "FACT_CLAIM"
    HISTORICAL_CLAIM = "HISTORICAL_CLAIM"
    THEOLOGICAL_CLAIM = "THEOLOGICAL_CLAIM"
    PHILOSOPHICAL_CLAIM = "PHILOSOPHICAL_CLAIM"
    SCIENTIFIC_CLAIM = "SCIENTIFIC_CLAIM"
    INTERPRETATION = "INTERPRETATION"
    INFERENCE = "INFERENCE"
    OPINION = "OPINION"
    VALUE_JUDGMENT = "VALUE_JUDGMENT"
    PREDICTION = "PREDICTION"
    UNVERIFIED_CLAIM = "UNVERIFIED_CLAIM"

class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    REFUTED = "refuted"

class ReviewStatus(str, Enum):
    AUTO_EXTRACTED = "AUTO_EXTRACTED"
    AI_ANALYZED = "AI_ANALYZED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    VERIFIED = "VERIFIED"
    CONTESTED = "CONTESTED"

class RelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    RESPONDS_TO = "responds_to"
    ATTACKS = "attacks"
    REBUTTED_BY = "rebutted_by"
    EVIDENCED_BY = "evidenced_by"
    QUALIFIES = "qualifies"
    EXTENDS = "extends"

class EvidenceType(str, Enum):
    SCRIPTURE = "scripture"
    HISTORICAL_DOCUMENT = "historical_document"
    BOOK = "book"
    ACADEMIC_PAPER = "academic_paper"
    QUOTATION = "quotation"
    PRIMARY_SOURCE = "primary_source"
    SECONDARY_SOURCE = "secondary_source"
    STATISTICAL_DATA = "statistical_data"
    ARCHAEOLOGICAL_EVIDENCE = "archaeological_evidence"
    PHILOSOPHICAL_ARGUMENT = "philosophical_argument"
    EYEWITNESS_ACCOUNT = "eyewitness_account"
    LOGICAL_DEDUCTION = "logical_deduction"
    UNSPECIFIED = "unspecified"
