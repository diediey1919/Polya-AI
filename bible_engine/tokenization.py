"""
POLYA PHILOLOGICAL BIBLE ENGINE
Tokenization Subsystem (Task 2.2)

Deterministic tokenization layer that derives tokens from immutable Source Text
without modifying, mutating, or replacing the original source text.
Adheres strictly to Architecture v2.0 FROZEN specification.

Guarantees:
  - TOKEN != SOURCE TEXT: Tokens are derived observations with explicit lineage.
  - POSITIONAL PROVENANCE: Exact Unicode code-point and UTF-8 byte offsets.
  - RAW SOURCE PROTECTION: Tokenization never mutates or rewrites source_texts.
  - TOKEN IDENTITY: Deterministic identity independent of LLM or surface text collisions.
  - NORMALIZATION FIREWALL: Explicit declaration of RAW vs NORMALIZED input text.
  - TOKEN IMMUTABILITY: Database-level triggers prevent mutation and unauthorized deletion.
  - VERSION & PROVENANCE INTEGRATION: Full version lineage and cryptographic provenance.
  - RECONSTRUCTION: Source spans reconstructable without single character or byte drift.
  - STRICT ARCHITECTURAL BOUNDARY: Zero morphology, lemma, POS, or semantic analysis.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateTokenError,
    InvalidTokenTypeError,
    SourceTextNotFoundError,
    TokenError,
    TokenImmutabilityError,
    TokenInvalidProvenanceError,
    TokenInvalidVersionError,
    TokenLanguageMismatchError,
    TokenNormalizationFirewallError,
    TokenNotFoundError,
    TokenOffsetError,
    TokenReconstructionError,
    TokenSourceNotFoundError,
)
from bible_engine.provenance import (
    ProvenanceRecord,
    ProvenanceTracker,
    TargetType,
    TransformationType,
)
from bible_engine.source_text import (
    RepresentationType,
    SourceTextLanguage,
    SourceTextManager,
    SourceTextRecord,
    compute_content_hash,
    validate_content_hash,
)
from bible_engine.versioning import (
    ChangeReason,
    ObjectVersion,
    VersionManager,
    VersionStatus,
)


# =============================================================================
# CONTROLLED TAXONOMIES & ENUMERATIONS
# =============================================================================

class TokenType(str, Enum):
    """Controlled structural token taxonomy for Bible Engine Level 1 tokens."""
    WORD = "WORD"
    PUNCTUATION = "PUNCTUATION"
    NUMBER = "NUMBER"
    WHITESPACE = "WHITESPACE"
    OTHER = "OTHER"


class TokenOffsetUnit(str, Enum):
    """Offset measurement systems supported by Bible Engine."""
    CODE_POINT = "CODE_POINT"  # Unicode scalar value / code point (0-indexed)
    UTF8_BYTE = "UTF8_BYTE"    # UTF-8 encoded byte offset (0-indexed)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class TokenRecord:
    """Immutable Level 1 linguistic token representation."""
    token_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    tokenization_id: Optional[str] = None
    passage_id: Optional[str] = None
    token_index: int = 0
    position: int = 0
    token_type: TokenType = TokenType.WORD
    surface_form: str = ""
    surface_original: str = ""
    surface_cleaned: Optional[str] = None
    normalized_form: Optional[str] = None
    start_offset: int = 0
    end_offset: int = 0
    start_byte: int = 0
    end_byte: int = 0
    language: SourceTextLanguage = SourceTextLanguage.GREEK
    representation_type: RepresentationType = RepresentationType.RAW
    lemma_id: Optional[str] = None
    is_immutable: bool = True
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "tokenization_id": self.tokenization_id,
            "source_text_id": self.source_text_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "passage_id": self.passage_id,
            "token_index": self.token_index,
            "position": self.position,
            "token_type": self.token_type.value if isinstance(self.token_type, TokenType) else str(self.token_type),
            "surface_form": self.surface_form,
            "surface_original": self.surface_original,
            "surface_cleaned": self.surface_cleaned,
            "normalized_form": self.normalized_form,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "language": self.language.value if isinstance(self.language, SourceTextLanguage) else str(self.language),
            "representation_type": self.representation_type.value if isinstance(self.representation_type, RepresentationType) else str(self.representation_type),
            "lemma_id": self.lemma_id,
            "is_immutable": 1 if self.is_immutable else 0,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> TokenRecord:
        d = dict(row)
        raw_tt = d.get("token_type") or "WORD"
        try:
            tt = TokenType(raw_tt)
        except ValueError:
            tt = TokenType.OTHER

        raw_lang = d.get("language") or "GREEK"
        try:
            lang = SourceTextLanguage(raw_lang)
        except ValueError:
            lang = SourceTextLanguage.OTHER

        raw_rep = d.get("representation_type") or "RAW"
        try:
            rep = RepresentationType(raw_rep)
        except ValueError:
            rep = RepresentationType.RAW

        s_form = d.get("surface_form") or d.get("surface_original") or ""
        s_orig = d.get("surface_original") or s_form

        return cls(
            token_id=str(d["token_id"]),
            tokenization_id=str(d["tokenization_id"]) if d.get("tokenization_id") else None,
            source_text_id=str(d["source_text_id"]),
            version_id=str(d.get("version_id") or ""),
            provenance_id=str(d.get("provenance_id") or ""),
            passage_id=str(d["passage_id"]) if d.get("passage_id") else None,
            token_index=int(d.get("token_index") if d.get("token_index") is not None else d.get("position", 0)),
            position=int(d.get("position") if d.get("position") is not None else d.get("token_index", 0)),
            token_type=tt,
            surface_form=s_form,
            surface_original=s_orig,
            surface_cleaned=str(d["surface_cleaned"]) if d.get("surface_cleaned") else None,
            normalized_form=str(d["normalized_form"]) if d.get("normalized_form") else None,
            start_offset=int(d.get("start_offset", 0)),
            end_offset=int(d.get("end_offset", 0)),
            start_byte=int(d.get("start_byte", 0)),
            end_byte=int(d.get("end_byte", 0)),
            language=lang,
            representation_type=rep,
            lemma_id=str(d["lemma_id"]) if d.get("lemma_id") else None,
            is_immutable=bool(d.get("is_immutable", 1)),
            created_at=str(d.get("created_at") or ""),
        )


@dataclass(frozen=True)
class TokenizationRunRecord:
    """Immutable metadata ledger row for a tokenization derivation event."""
    tokenization_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    tokenizer_id: str
    tokenizer_version: str
    representation_type: RepresentationType
    language: SourceTextLanguage
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    token_count: int
    is_exact_reproducible: bool
    created_at: str
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokenization_id": self.tokenization_id,
            "source_text_id": self.source_text_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "tokenizer_id": self.tokenizer_id,
            "tokenizer_version": self.tokenizer_version,
            "representation_type": self.representation_type.value,
            "language": self.language.value,
            "configuration_hash": self.configuration_hash,
            "input_content_hash": self.input_content_hash,
            "output_hash": self.output_hash,
            "token_count": self.token_count,
            "is_exact_reproducible": 1 if self.is_exact_reproducible else 0,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> TokenizationRunRecord:
        d = dict(row)
        raw_rep = d.get("representation_type") or "RAW"
        try:
            rep = RepresentationType(raw_rep)
        except ValueError:
            rep = RepresentationType.RAW

        raw_lang = d.get("language") or "GREEK"
        try:
            lang = SourceTextLanguage(raw_lang)
        except ValueError:
            lang = SourceTextLanguage.OTHER

        return cls(
            tokenization_id=str(d["tokenization_id"]),
            source_text_id=str(d["source_text_id"]),
            version_id=str(d["version_id"]),
            provenance_id=str(d["provenance_id"]),
            tokenizer_id=str(d["tokenizer_id"]),
            tokenizer_version=str(d["tokenizer_version"]),
            representation_type=rep,
            language=lang,
            configuration_hash=str(d["configuration_hash"]),
            input_content_hash=str(d["input_content_hash"]),
            output_hash=str(d["output_hash"]),
            token_count=int(d["token_count"]),
            is_exact_reproducible=bool(d["is_exact_reproducible"]),
            created_at=str(d["created_at"]),
            is_immutable=bool(d.get("is_immutable", 1)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class TokenizerConfig:
    """Deterministic configuration for structural tokenization."""
    tokenizer_id: str = "polya-structural-tokenizer"
    tokenizer_version: str = "1.0.0"
    include_whitespace: bool = False
    representation_type: RepresentationType = RepresentationType.RAW
    normalize_nfc: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokenizer_id": self.tokenizer_id,
            "tokenizer_version": self.tokenizer_version,
            "include_whitespace": self.include_whitespace,
            "representation_type": self.representation_type.value,
            "normalize_nfc": self.normalize_nfc,
        }

    def compute_config_hash(self) -> str:
        serialized = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


@dataclass(frozen=True)
class TokenizationResult:
    """Aggregated result of tokenizing a source text artifact."""
    run: TokenizationRunRecord
    tokens: List[TokenRecord]
    source_representation: str


# =============================================================================
# PURE TOKENIZATION & RECONSTRUCTION LOGIC
# =============================================================================

def compute_tokens_output_hash(tokens: List[TokenRecord]) -> str:
    """Compute deterministic SHA-256 hash over canonical serialized token list."""
    token_dicts = [
        {
            "token_index": t.token_index,
            "token_type": t.token_type.value if isinstance(t.token_type, TokenType) else str(t.token_type),
            "surface_form": t.surface_form,
            "start_offset": t.start_offset,
            "end_offset": t.end_offset,
            "start_byte": t.start_byte,
            "end_byte": t.end_byte,
        }
        for t in sorted(tokens, key=lambda x: x.token_index)
    ]
    serialized = json.dumps(token_dicts, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


def tokenize_text(
    text: str,
    language: Union[SourceTextLanguage, str],
    config: Optional[TokenizerConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Pure, deterministic language-aware structural tokenization.
    
    Splits text into discrete tokens with precise Unicode code-point and UTF-8 byte offsets.
    Does NOT perform morphology, POS tagging, lemmatization, or semantic analysis.
    
    Language boundaries supported:
      - Greek (Polytonic accents, breathings, ano teleia, erotimatiko)
      - Hebrew (Niqqud, cantillation, sof pasuq, paseq, maqaf)
      - Aramaic (Biblical Aramaic consonants and marks)
      - Latin, Syriac, Coptic, Other, Multilingual
    """
    if config is None:
        config = TokenizerConfig()

    tokens: List[Dict[str, Any]] = []
    i = 0
    n = len(text)
    token_index = 0

    # Pre-encode text to UTF-8 for exact byte offset indexing
    encoded_text = text.encode("utf-8")
    
    # Cumulative byte offset mapping: code_point_index -> byte_index
    # Built efficiently once per tokenization run
    code_point_to_byte = [0] * (n + 1)
    current_byte = 0
    for idx, char in enumerate(text):
        code_point_to_byte[idx] = current_byte
        current_byte += len(char.encode("utf-8"))
    code_point_to_byte[n] = current_byte

    while i < n:
        c = text[i]
        cat = unicodedata.category(c)

        # 1. Whitespace handling
        if c.isspace() or cat.startswith("Z"):
            start = i
            while i < n and (text[i].isspace() or unicodedata.category(text[i]).startswith("Z")):
                i += 1
            if config.include_whitespace:
                span_str = text[start:i]
                start_byte = code_point_to_byte[start]
                end_byte = code_point_to_byte[i]
                tokens.append({
                    "token_index": token_index,
                    "token_type": TokenType.WHITESPACE,
                    "surface_form": span_str,
                    "normalized_form": unicodedata.normalize("NFC", span_str) if config.normalize_nfc else span_str,
                    "start_offset": start,
                    "end_offset": i,
                    "start_byte": start_byte,
                    "end_byte": end_byte,
                })
                token_index += 1
            continue

        # 2. Word tokens: Begins with a letter (L*), continues with letters or combining marks (M*)
        if cat.startswith("L"):
            start = i
            while i < n:
                next_cat = unicodedata.category(text[i])
                if next_cat.startswith("L") or next_cat.startswith("M"):
                    i += 1
                else:
                    break
            span_str = text[start:i]
            start_byte = code_point_to_byte[start]
            end_byte = code_point_to_byte[i]
            tokens.append({
                "token_index": token_index,
                "token_type": TokenType.WORD,
                "surface_form": span_str,
                "normalized_form": unicodedata.normalize("NFC", span_str) if config.normalize_nfc else span_str,
                "start_offset": start,
                "end_offset": i,
                "start_byte": start_byte,
                "end_byte": end_byte,
            })
            token_index += 1
            continue

        # 3. Number tokens: Sequence of decimal/numeric characters (N*)
        if cat.startswith("N"):
            start = i
            while i < n and unicodedata.category(text[i]).startswith("N"):
                i += 1
            span_str = text[start:i]
            start_byte = code_point_to_byte[start]
            end_byte = code_point_to_byte[i]
            tokens.append({
                "token_index": token_index,
                "token_type": TokenType.NUMBER,
                "surface_form": span_str,
                "normalized_form": unicodedata.normalize("NFC", span_str) if config.normalize_nfc else span_str,
                "start_offset": start,
                "end_offset": i,
                "start_byte": start_byte,
                "end_byte": end_byte,
            })
            token_index += 1
            continue

        # 4. Punctuation tokens: (P*) or language punctuation marks
        if cat.startswith("P"):
            span_str = text[i : i + 1]
            start_byte = code_point_to_byte[i]
            end_byte = code_point_to_byte[i + 1]
            tokens.append({
                "token_index": token_index,
                "token_type": TokenType.PUNCTUATION,
                "surface_form": span_str,
                "normalized_form": unicodedata.normalize("NFC", span_str) if config.normalize_nfc else span_str,
                "start_offset": i,
                "end_offset": i + 1,
                "start_byte": start_byte,
                "end_byte": end_byte,
            })
            token_index += 1
            i += 1
            continue

        # 5. Other characters (Symbols, orphan marks, unclassified glyphs)
        span_str = text[i : i + 1]
        start_byte = code_point_to_byte[i]
        end_byte = code_point_to_byte[i + 1]
        tokens.append({
            "token_index": token_index,
            "token_type": TokenType.OTHER,
            "surface_form": span_str,
            "normalized_form": unicodedata.normalize("NFC", span_str) if config.normalize_nfc else span_str,
            "start_offset": i,
            "end_offset": i + 1,
            "start_byte": start_byte,
            "end_byte": end_byte,
        })
        token_index += 1
        i += 1

    return tokens


def reconstruct_source_span(source_text: str, token: TokenRecord) -> str:
    """
    Extract source slice corresponding to token offsets and verify exact fidelity.
    Raises TokenReconstructionError on any discrepancy.
    """
    if token.start_offset < 0 or token.end_offset > len(source_text) or token.start_offset > token.end_offset:
        raise TokenOffsetError(
            f"Token offsets [{token.start_offset}:{token.end_offset}] out of bounds for source length {len(source_text)}"
        )
    span = source_text[token.start_offset : token.end_offset]
    if span != token.surface_form:
        raise TokenReconstructionError(
            f"Token '{token.token_id}' surface_form '{token.surface_form}' does not match "
            f"source span '{span}' at offsets [{token.start_offset}:{token.end_offset}]"
        )
    return span


def reconstruct_text_from_tokens(
    tokens: List[TokenRecord],
    source_text: str,
) -> str:
    """
    Losslessly reconstruct the original source text using tokens and positional gaps.
    Guarantees zero character drift across the entire passage.
    """
    if not tokens:
        return source_text

    sorted_tokens = sorted(tokens, key=lambda t: t.token_index)
    reconstructed_parts: List[str] = []
    last_end = 0

    for t in sorted_tokens:
        if t.start_offset < last_end:
            raise TokenOffsetError(
                f"Overlapping or out-of-order token '{t.token_id}' at start_offset {t.start_offset} < last_end {last_end}"
            )
        # Capture inter-token gap (whitespace, separators)
        gap = source_text[last_end : t.start_offset]
        reconstructed_parts.append(gap)

        # Validate token span
        span = reconstruct_source_span(source_text, t)
        reconstructed_parts.append(span)
        last_end = t.end_offset

    # Trailing gap
    reconstructed_parts.append(source_text[last_end:])
    full_reconstructed = "".join(reconstructed_parts)

    if full_reconstructed != source_text:
        raise TokenReconstructionError(
            f"Reconstructed source text failed fidelity check against original text: "
            f"reconstructed len {len(full_reconstructed)} != original len {len(source_text)}"
        )
    return full_reconstructed


# =============================================================================
# TOKENIZATION SUBSYSTEM MANAGER
# =============================================================================

class TokenizationManager:
    """
    Authoritative manager for deriving, persisting, and querying Level 1 linguistic tokens.
    
    Invariants:
      - Raw source text is NEVER mutated.
      - Every token resolves to an explicit source_text_id, object_version, and provenance_record.
      - Tokens are database-level immutable once persisted.
      - Full atomic transactional rollback on failure.
      - Zero morphology, lemma, POS, or semantic analysis leakage.
    """

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine
        self.version_mgr = VersionManager(engine)
        self.provenance_tracker = ProvenanceTracker(engine)
        self.source_text_mgr = SourceTextManager(engine)

    def tokenize_source_text(
        self,
        source_text: Union[str, SourceTextRecord],
        config: Optional[TokenizerConfig] = None,
        agent: str = "system:polya-tokenizer",
        passage_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> TokenizationResult:
        """
        Derive deterministic tokens from an immutable source text.
        
        Args:
            source_text: Either a SourceTextRecord or a source_text_id string.
            config: Optional TokenizerConfig specifying representation_type, whitespace, etc.
            agent: Provenance agent identifier.
            passage_id: Optional canonical verse address if known at tokenization time.
            conn: Optional existing database connection/transaction.
            
        Returns:
            TokenizationResult containing run record, tokens, and verified source representation.
        """
        if config is None:
            config = TokenizerConfig()

        # 1. Resolve source text record
        if isinstance(source_text, str):
            try:
                record = self.source_text_mgr.get_source_text(source_text)
            except SourceTextNotFoundError:
                raise TokenSourceNotFoundError(f"Source text with ID '{source_text}' does not exist.")
            if record is None:
                raise TokenSourceNotFoundError(f"Source text with ID '{source_text}' does not exist.")
        elif isinstance(source_text, SourceTextRecord):
            record = source_text
        else:
            raise TypeError(f"Expected str or SourceTextRecord, got {type(source_text).__name__}")

        # 2. Record source text hash before tokenization to verify source immutability
        source_hash_before = record.content_hash

        # 3. Normalization Firewall: select exact representation text
        if config.representation_type == RepresentationType.RAW:
            input_text = record.raw_content or record.raw_source_string
            # Verify input content hash matches source record
            calc_hash = compute_content_hash(input_text)
            if calc_hash != record.content_hash:
                raise TokenNormalizationFirewallError(
                    f"Raw content hash {calc_hash} mismatch with source_text content_hash {record.content_hash}"
                )
        elif config.representation_type == RepresentationType.NORMALIZED:
            input_text = record.normalized_content or record.normalized_source_string
        else:
            raise TokenNormalizationFirewallError(
                f"Unsupported representation_type '{config.representation_type}' for tokenization."
            )

        if not isinstance(input_text, str):
            raise TokenNormalizationFirewallError("Source text content string is empty or invalid.")

        # Resolve language as SourceTextLanguage enum
        if isinstance(record.language, SourceTextLanguage):
            source_lang = record.language
        else:
            try:
                source_lang = SourceTextLanguage(str(record.language).upper())
            except ValueError:
                source_lang = SourceTextLanguage.OTHER

        # 4. Pure structural tokenization
        raw_tokens = tokenize_text(input_text, language=source_lang, config=config)

        # 5. Generate deterministic run ID and hashes
        config_hash = config.compute_config_hash()
        input_hash = compute_content_hash(input_text)
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Deterministic tokenization ID incorporates source ID and config hash prefix
        tokenization_id = f"TRUN-{record.source_text_id[:16]}-{config_hash[:8]}-{input_hash[:8]}"

        # 6. Build TokenRecord instances
        token_records: List[TokenRecord] = []
        for item in raw_tokens:
            idx = item["token_index"]
            token_id = f"TOK-{tokenization_id}-{idx:05d}"
            s_form = item["surface_form"]
            t_rec = TokenRecord(
                token_id=token_id,
                source_text_id=record.source_text_id,
                version_id="",  # Populated during atomic version creation
                provenance_id="",  # Populated during atomic provenance creation
                tokenization_id=tokenization_id,
                passage_id=passage_id or record.passage_id,
                token_index=idx,
                position=idx + 1,  # 1-indexed for compatibility with 001 schema
                token_type=item["token_type"],
                surface_form=s_form,
                surface_original=s_form,
                surface_cleaned=None,  # Not inferred; strictly left for Phase 3
                normalized_form=item["normalized_form"],
                start_offset=item["start_offset"],
                end_offset=item["end_offset"],
                start_byte=item["start_byte"],
                end_byte=item["end_byte"],
                language=source_lang,
                representation_type=config.representation_type,
                lemma_id=None,  # Zero morphology leakage
                is_immutable=True,
                created_at=now_iso,
            )
            token_records.append(t_rec)

        # 7. Verification: Verify every token can reconstruct its exact span
        reconstruct_text_from_tokens(token_records, input_text)

        # 8. Compute output hash over all verified tokens
        output_hash = compute_tokens_output_hash(token_records)

        # 9. Atomic Transactional Persistence
        with self.engine.transaction(conn=conn) as tx_conn:
            # Check for existing identical tokenization run
            cur = tx_conn.cursor()
            cur.execute("SELECT tokenization_id FROM tokenization_runs WHERE tokenization_id = ?;", (tokenization_id,))
            if cur.fetchone() is not None:
                raise DuplicateTokenError(
                    f"Tokenization run '{tokenization_id}' has already been registered."
                )

            # 9a. Record Provenance
            prov_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.DERIVED_ARTIFACT,
                target_id=tokenization_id,
                content=output_hash,
                parent_provenance_id=record.provenance_id,
                input_data={
                    "source_text_id": record.source_text_id,
                    "representation_type": config.representation_type.value,
                    "input_content_hash": input_hash,
                    "config_hash": config_hash,
                },
                agent_id=agent,
                config=config.to_dict(),
                conn=tx_conn,
            )

            # 9b. Create Object Version
            ver_rec = self.version_mgr.create_version(
                object_id=tokenization_id,
                object_type="tokenization",
                content_hash=output_hash,
                provenance_id=prov_rec.provenance_id,
                created_by=agent,
                change_reason=ChangeReason.INITIAL_CREATION,
                status=VersionStatus.ACTIVE,
                conn=tx_conn,
            )

            # 9c. Persist Tokenization Run
            cur.execute(
                """
                INSERT INTO tokenization_runs (
                    tokenization_id, source_text_id, version_id, provenance_id,
                    tokenizer_id, tokenizer_version, representation_type, language,
                    configuration_hash, input_content_hash, output_hash,
                    token_count, is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    tokenization_id,
                    record.source_text_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    config.tokenizer_id,
                    config.tokenizer_version,
                    config.representation_type.value,
                    source_lang.value,
                    config_hash,
                    input_hash,
                    output_hash,
                    len(token_records),
                    1,
                    now_iso,
                    1,
                    json.dumps(config.to_dict()),
                ),
            )

            # 9d. Persist Tokens with populated version_id and provenance_id
            final_tokens: List[TokenRecord] = []
            for t in token_records:
                updated_t = TokenRecord(
                    token_id=t.token_id,
                    source_text_id=t.source_text_id,
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    tokenization_id=t.tokenization_id,
                    passage_id=t.passage_id,
                    token_index=t.token_index,
                    position=t.position,
                    token_type=t.token_type,
                    surface_form=t.surface_form,
                    surface_original=t.surface_original,
                    surface_cleaned=t.surface_cleaned,
                    normalized_form=t.normalized_form,
                    start_offset=t.start_offset,
                    end_offset=t.end_offset,
                    start_byte=t.start_byte,
                    end_byte=t.end_byte,
                    language=t.language,
                    representation_type=t.representation_type,
                    lemma_id=t.lemma_id,
                    is_immutable=True,
                    created_at=now_iso,
                )
                final_tokens.append(updated_t)

                cur.execute(
                    """
                    INSERT INTO tokens (
                        token_id, tokenization_id, source_text_id, version_id, provenance_id,
                        passage_id, token_index, position, token_type, surface_form,
                        surface_original, surface_cleaned, normalized_form,
                        start_offset, end_offset, start_byte, end_byte,
                        language, representation_type, lemma_id, is_immutable, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        updated_t.token_id,
                        updated_t.tokenization_id,
                        updated_t.source_text_id,
                        updated_t.version_id,
                        updated_t.provenance_id,
                        updated_t.passage_id,
                        updated_t.token_index,
                        updated_t.position,
                        updated_t.token_type.value,
                        updated_t.surface_form,
                        updated_t.surface_original,
                        updated_t.surface_cleaned,
                        updated_t.normalized_form,
                        updated_t.start_offset,
                        updated_t.end_offset,
                        updated_t.start_byte,
                        updated_t.end_byte,
                        updated_t.language.value,
                        updated_t.representation_type.value,
                        updated_t.lemma_id,
                        1,
                        updated_t.created_at,
                    ),
                )

        # 10. Verify source text content hash after tokenization remains strictly identical
        source_after = self.source_text_mgr.get_source_text(record.source_text_id)
        if source_after is None or source_after.content_hash != source_hash_before:
            raise TokenImmutabilityError("CRITICAL: Source text content hash changed during tokenization!")

        run_record = TokenizationRunRecord(
            tokenization_id=tokenization_id,
            source_text_id=record.source_text_id,
            version_id=ver_rec.version_id,
            provenance_id=prov_rec.provenance_id,
            tokenizer_id=config.tokenizer_id,
            tokenizer_version=config.tokenizer_version,
            representation_type=config.representation_type,
            language=source_lang,
            configuration_hash=config_hash,
            input_content_hash=input_hash,
            output_hash=output_hash,
            token_count=len(final_tokens),
            is_exact_reproducible=True,
            created_at=now_iso,
            is_immutable=True,
            metadata_json=json.dumps(config.to_dict()),
        )

        return TokenizationResult(
            run=run_record,
            tokens=final_tokens,
            source_representation=input_text,
        )

    def get_tokenization_run(
        self,
        tokenization_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[TokenizationRunRecord]:
        """Retrieve tokenization run by primary key."""
        def _get(c: sqlite3.Connection) -> Optional[TokenizationRunRecord]:
            cur = c.cursor()
            cur.execute("SELECT * FROM tokenization_runs WHERE tokenization_id = ?;", (tokenization_id,))
            row = cur.fetchone()
            return TokenizationRunRecord.from_row(row) if row else None

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as c:
            return _get(c)

    def get_tokens_for_run(
        self,
        tokenization_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[TokenRecord]:
        """Retrieve all tokens belonging to a specific tokenization run in deterministic index order."""
        def _get(c: sqlite3.Connection) -> List[TokenRecord]:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM tokens WHERE tokenization_id = ? ORDER BY token_index ASC;",
                (tokenization_id,),
            )
            return [TokenRecord.from_row(r) for r in cur.fetchall()]

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as c:
            return _get(c)

    def get_tokens_for_source_text(
        self,
        source_text_id: str,
        representation_type: Optional[RepresentationType] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[TokenRecord]:
        """Retrieve all active tokens for a source text in deterministic index order."""
        def _get(c: sqlite3.Connection) -> List[TokenRecord]:
            cur = c.cursor()
            if representation_type is not None:
                cur.execute(
                    """
                    SELECT * FROM tokens
                    WHERE source_text_id = ? AND representation_type = ?
                    ORDER BY token_index ASC;
                    """,
                    (source_text_id, representation_type.value),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM tokens
                    WHERE source_text_id = ?
                    ORDER BY token_index ASC;
                    """,
                    (source_text_id,),
                )
            return [TokenRecord.from_row(r) for r in cur.fetchall()]

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as c:
            return _get(c)

    def get_token_by_id(
        self,
        token_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[TokenRecord]:
        """Retrieve a single token by token_id."""
        def _get(c: sqlite3.Connection) -> Optional[TokenRecord]:
            cur = c.cursor()
            cur.execute("SELECT * FROM tokens WHERE token_id = ?;", (token_id,))
            row = cur.fetchone()
            return TokenRecord.from_row(row) if row else None

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as c:
            return _get(c)

    def retokenise(
        self,
        source_text_id: str,
        new_config: TokenizerConfig,
        reason: str = "CONFIG_CHANGE",
        agent: str = "system:polya-tokenizer",
    ) -> TokenizationResult:
        """
        Create a new tokenization version for a source text, superseding prior versions
        while preserving all historical runs and token records.
        """
        source_rec = self.source_text_mgr.get_source_text(source_text_id)
        if source_rec is None:
            raise TokenSourceNotFoundError(f"Source text '{source_text_id}' not found.")

        # Find prior tokenization runs
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT tokenization_id, version_id FROM tokenization_runs
                WHERE source_text_id = ? AND representation_type = ?
                ORDER BY created_at DESC;
                """,
                (source_text_id, new_config.representation_type.value),
            )
            rows = cur.fetchall()

        prior_tokenization_id = rows[0][0] if rows else None
        prior_version_id = rows[0][1] if rows else None

        # Execute new tokenization
        new_result = self.tokenize_source_text(source_rec, config=new_config, agent=agent)

        # Supersede prior version if one existed
        if prior_tokenization_id and prior_version_id:
            with self.engine.transaction() as conn:
                try:
                    self.version_mgr.supersede_version(
                        version_id=prior_version_id,
                        superseded_by_version_id=new_result.run.version_id,
                        conn=conn,
                    )
                except Exception:
                    # Non-fatal if prior object_id differs from new tokenization_id
                    pass

        return new_result
