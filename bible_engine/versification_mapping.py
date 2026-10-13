"""
Versification Mapping Module (Task 5E Structural Alignment Layer).

Provides structural data structures and validation for versification mappings
between source verse coordinates and canonical passage coordinates.

DISCLAIMER:
Structural mapping only. Carries zero scholarly or exegetical validity assertion
without external philological evidence adjudication and textual witness provenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple


class VersificationMappingType(str, Enum):
    EXACT_ONE_TO_ONE = "EXACT_ONE_TO_ONE"
    ONE_TO_MANY_SPLIT = "ONE_TO_MANY_SPLIT"
    MANY_TO_ONE_MERGE = "MANY_TO_ONE_MERGE"
    FRAGMENT = "FRAGMENT"


class VersificationMappingError(Exception):
    """Base exception for versification mapping errors."""
    pass


class InvalidMappingCoordinateError(VersificationMappingError):
    """Raised when a coordinate string is malformed or invalid."""
    pass


class InvalidMappingStructureError(VersificationMappingError):
    """Raised when structural mapping constraints are violated."""
    pass


def compute_mapping_id(
    verse_record_id: str,
    canonical_passage_id: str,
    sub_verse: str,
    rule_hash: str,
) -> str:
    """
    Deterministic Mapping ID generator matching Migration 027 contract:
    SHA-256(verse_record_id + ":" + canonical_passage_id + ":" + sub_verse + ":" + rule_hash)
    """
    raw = f"{verse_record_id}:{canonical_passage_id}:{sub_verse}:{rule_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest().lower()


def compute_rule_hash(rule_payload: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of canonical JSON rule definition."""
    canonical_json = json.dumps(rule_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest().lower()


@dataclass(frozen=True)
class MappingEntry:
    mapping_id: str
    verse_record_id: str
    canonical_passage_id: str
    source_text_id: Optional[str]
    mapping_provenance_id: str
    mapping_type: VersificationMappingType
    sub_verse: str
    rule_hash: str
    mapping_version: int
    status: str


class VersificationMapper:
    """
    Structural validator and generator for versification mapping entries.
    Encapsulates ONE_TO_ONE, ONE_TO_MANY_SPLIT, and MANY_TO_ONE_MERGE logic.
    """

    @staticmethod
    def build_one_to_one(
        verse_record_id: str,
        canonical_passage_id: str,
        mapping_provenance_id: str,
        rule_payload: Dict[str, Any],
        source_text_id: Optional[str] = None,
        mapping_version: int = 1,
    ) -> MappingEntry:
        if not verse_record_id or not canonical_passage_id:
            raise InvalidMappingCoordinateError("verse_record_id and canonical_passage_id must not be empty.")
        if not canonical_passage_id.startswith("PAS-"):
            raise InvalidMappingCoordinateError(f"Invalid canonical_passage_id prefix: '{canonical_passage_id}'")

        rule_hash = compute_rule_hash(rule_payload)
        sub_verse = ""
        m_id = compute_mapping_id(verse_record_id, canonical_passage_id, sub_verse, rule_hash)

        return MappingEntry(
            mapping_id=m_id,
            verse_record_id=verse_record_id,
            canonical_passage_id=canonical_passage_id,
            source_text_id=source_text_id,
            mapping_provenance_id=mapping_provenance_id,
            mapping_type=VersificationMappingType.EXACT_ONE_TO_ONE,
            sub_verse=sub_verse,
            rule_hash=rule_hash,
            mapping_version=mapping_version,
            status="ACTIVE",
        )

    @staticmethod
    def build_split(
        verse_record_id: str,
        targets: Sequence[Tuple[str, str]],  # List of (canonical_passage_id, sub_verse)
        mapping_provenance_id: str,
        rule_payload: Dict[str, Any],
        source_text_id: Optional[str] = None,
        mapping_version: int = 1,
    ) -> List[MappingEntry]:
        if not verse_record_id:
            raise InvalidMappingCoordinateError("verse_record_id must not be empty.")
        if len(targets) < 2:
            raise InvalidMappingStructureError(
                f"ONE_TO_MANY_SPLIT requires at least 2 target passages, got {len(targets)}."
            )

        rule_hash = compute_rule_hash(rule_payload)
        entries: List[MappingEntry] = []
        seen_targets = set()

        for canonical_passage_id, sub_verse in targets:
            if not canonical_passage_id.startswith("PAS-"):
                raise InvalidMappingCoordinateError(f"Invalid canonical_passage_id prefix: '{canonical_passage_id}'")
            if not sub_verse:
                raise InvalidMappingStructureError("Split targets must provide distinct non-empty sub_verse labels.")

            key = (canonical_passage_id, sub_verse)
            if key in seen_targets:
                raise InvalidMappingStructureError(f"Duplicate split target: {key}")
            seen_targets.add(key)

            m_id = compute_mapping_id(verse_record_id, canonical_passage_id, sub_verse, rule_hash)
            entries.append(
                MappingEntry(
                    mapping_id=m_id,
                    verse_record_id=verse_record_id,
                    canonical_passage_id=canonical_passage_id,
                    source_text_id=source_text_id,
                    mapping_provenance_id=mapping_provenance_id,
                    mapping_type=VersificationMappingType.ONE_TO_MANY_SPLIT,
                    sub_verse=sub_verse,
                    rule_hash=rule_hash,
                    mapping_version=mapping_version,
                    status="ACTIVE",
                )
            )

        return entries

    @staticmethod
    def build_merge(
        source_verse_record_ids: Sequence[str],
        canonical_passage_id: str,
        mapping_provenance_id: str,
        rule_payload: Dict[str, Any],
        source_text_id: Optional[str] = None,
        mapping_version: int = 1,
    ) -> List[MappingEntry]:
        if not canonical_passage_id.startswith("PAS-"):
            raise InvalidMappingCoordinateError(f"Invalid canonical_passage_id prefix: '{canonical_passage_id}'")
        if len(source_verse_record_ids) < 2:
            raise InvalidMappingStructureError(
                f"MANY_TO_ONE_MERGE requires at least 2 source verses, got {len(source_verse_record_ids)}."
            )

        rule_hash = compute_rule_hash(rule_payload)
        entries: List[MappingEntry] = []
        seen_verses = set()

        for idx, v_id in enumerate(source_verse_record_ids, start=1):
            if not v_id:
                raise InvalidMappingCoordinateError("verse_record_id must not be empty.")
            if v_id in seen_verses:
                raise InvalidMappingStructureError(f"Duplicate source verse in merge: {v_id}")
            seen_verses.add(v_id)

            sub_verse = f"src_{idx}"
            m_id = compute_mapping_id(v_id, canonical_passage_id, sub_verse, rule_hash)
            entries.append(
                MappingEntry(
                    mapping_id=m_id,
                    verse_record_id=v_id,
                    canonical_passage_id=canonical_passage_id,
                    source_text_id=source_text_id,
                    mapping_provenance_id=mapping_provenance_id,
                    mapping_type=VersificationMappingType.MANY_TO_ONE_MERGE,
                    sub_verse=sub_verse,
                    rule_hash=rule_hash,
                    mapping_version=mapping_version,
                    status="ACTIVE",
                )
            )

        return entries
