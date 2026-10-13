"""
Canonical Passages Grid Generator & Validator (Task 5E).

Produces deterministic provisional pericopes and canonical passages for the 66-book canon.
Enforces strict manifest verification, atomic transactions, conflict detection,
and explicit idempotency without hiding mutations behind INSERT OR IGNORE.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.migrations import compute_association_id


class CanonicalGridError(Exception):
    """Base exception for canonical grid errors."""
    pass


class ManifestValidationError(CanonicalGridError):
    """Raised when manifest validation fails."""
    pass


class ManifestIncompleteError(ManifestValidationError):
    """Raised when manifest does not cover all required books/chapters."""
    pass


class ManifestChecksumMismatchError(ManifestValidationError):
    """Raised when manifest content hash does not match expected checksum."""
    pass


class ManifestDuplicateCoordinateError(ManifestValidationError):
    """Raised when manifest contains duplicate chapter/verse coordinates."""
    pass


class ManifestInvalidOrderError(ManifestValidationError):
    """Raised when manifest books/chapters violate canonical ordering."""
    pass


class CanonicalGridConflictError(CanonicalGridError):
    """Raised when existing database records conflict with manifest data."""
    pass


def compute_manifest_checksum(books_payload: List[Dict[str, Any]]) -> str:
    """Compute deterministic SHA-256 hash of canonical JSON books structure."""
    canonical_repr = json.dumps(books_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest().lower()


def compute_manifest_payload_checksum(manifest_payload: Dict[str, Any]) -> str:
    """
    Deterministic SHA-256 calculation for complete manifest payload.
    Excludes 'manifest_checksum_sha256' and 'checksum_sha256' fields.
    """
    clean_payload = {
        k: v
        for k, v in manifest_payload.items()
        if k not in ("manifest_checksum_sha256", "checksum_sha256")
    }
    canonical_repr = json.dumps(clean_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest().lower()


def compute_passage_id(book_id: str, chapter: int, verse: int) -> str:
    """Generate canonical passage ID string: PAS-{BOOK_ID}.{CHAPTER}.{VERSE}."""
    return f"PAS-{book_id}.{chapter}.{verse}"


def compute_provisional_pericope_id(book_id: str, chapter: int) -> str:
    """Generate deterministic provisional pericope ID per chapter."""
    return f"PER-PROV-{book_id}-CH{chapter:03d}"


@dataclass(frozen=True)
class ChapterSpec:
    chapter: int
    verse_count: int


@dataclass(frozen=True)
class BookSpec:
    book_id: str
    canonical_order: int
    standard_name: str
    chapter_count: int
    chapters: Tuple[ChapterSpec, ...]


@dataclass(frozen=True)
class ValidatedManifest:
    manifest_id: str
    canon_id: str
    edition: str
    checksum_sha256: str
    books: Tuple[BookSpec, ...]
    total_books: int
    total_chapters: int
    total_verses: int


@dataclass(frozen=True)
class GenerationSummary:
    books_processed: int
    pericopes_inserted: int
    passages_inserted: int
    associations_inserted: int
    pericopes_replayed: int
    passages_replayed: int
    associations_replayed: int
    total_verses: int


class CanonicalGridValidator:
    """
    Validates canonical coordinate manifests against schema invariants and DB books baseline.
    Decoupled strictly from database insertion execution.
    """

    @classmethod
    def validate(
        cls,
        manifest_data: Dict[str, Any],
        conn: sqlite3.Connection,
        require_full_canon: bool = True,
    ) -> ValidatedManifest:
        """
        Validate manifest against database books table and structural invariants.
        Raises ManifestValidationError on any discrepancy.
        """
        # Check required fields
        for req_field in ("manifest_id", "canon_id", "books"):
            if req_field not in manifest_data:
                raise ManifestValidationError(f"Missing required manifest field: '{req_field}'")

        has_payload_checksum = "manifest_checksum_sha256" in manifest_data
        has_books_checksum = "checksum_sha256" in manifest_data
        if not has_payload_checksum and not has_books_checksum:
            raise ManifestValidationError(
                "Missing required checksum field ('manifest_checksum_sha256' or 'checksum_sha256')"
            )

        books_data = manifest_data["books"]
        if not isinstance(books_data, list) or not books_data:
            raise ManifestValidationError("Manifest 'books' must be a non-empty list.")

        expected_payload_chk: Optional[str] = None
        expected_books_chk: Optional[str] = None

        if has_payload_checksum:
            expected_payload_chk = manifest_data["manifest_checksum_sha256"].strip().lower()
            actual_payload_chk = compute_manifest_payload_checksum(manifest_data)
            if actual_payload_chk != expected_payload_chk:
                raise ManifestChecksumMismatchError(
                    f"Payload checksum mismatch: expected '{expected_payload_chk}', computed '{actual_payload_chk}'"
                )

        if has_books_checksum:
            expected_books_chk = manifest_data["checksum_sha256"].strip().lower()
            actual_books_chk = compute_manifest_checksum(books_data)
            if actual_books_chk != expected_books_chk:
                raise ManifestChecksumMismatchError(
                    f"Checksum mismatch: expected '{expected_books_chk}', computed '{actual_books_chk}'"
                )

        recorded_checksum = expected_payload_chk if has_payload_checksum else (expected_books_chk or "")

        # Query baseline books from database
        cursor = conn.cursor()
        cursor.execute(
            "SELECT book_id, canonical_order, standard_name, chapter_count FROM books ORDER BY canonical_order ASC;"
        )
        db_rows = cursor.fetchall()
        if not db_rows:
            raise ManifestValidationError("Database 'books' table is empty. Baseline books required.")

        db_books_map = {row[0]: (row[1], row[2], row[3]) for row in db_rows}
        db_order_list = [row[0] for row in db_rows]

        if require_full_canon and len(books_data) != len(db_rows):
            raise ManifestIncompleteError(
                f"Manifest contains {len(books_data)} books; database defines {len(db_rows)} books."
            )

        validated_books: List[BookSpec] = []
        seen_books: Set[str] = set()
        seen_coordinates: Set[Tuple[str, int, int]] = set()
        last_order = 0
        total_verses = 0
        total_chapters = 0

        for b_entry in books_data:
            for bf in ("book_id", "canonical_order", "chapter_count", "chapters"):
                if bf not in b_entry:
                    raise ManifestValidationError(f"Book entry missing field '{bf}': {b_entry}")

            b_id = b_entry["book_id"]
            if b_id in seen_books:
                raise ManifestValidationError(f"Duplicate book_id in manifest: '{b_id}'")
            seen_books.add(b_id)

            if b_id not in db_books_map:
                raise ManifestValidationError(f"Book '{b_id}' not found in database books table.")

            db_order, db_name, db_chap_count = db_books_map[b_id]
            b_order = b_entry["canonical_order"]
            b_chap_count = b_entry["chapter_count"]

            if b_order != db_order:
                raise ManifestInvalidOrderError(
                    f"Canonical order mismatch for '{b_id}': manifest={b_order}, db={db_order}"
                )
            if b_order <= last_order:
                raise ManifestInvalidOrderError(
                    f"Manifest books are not strictly sorted by canonical_order. Saw {b_order} after {last_order}."
                )
            last_order = b_order

            if b_chap_count != db_chap_count:
                raise ManifestValidationError(
                    f"Chapter count mismatch for '{b_id}': manifest={b_chap_count}, db={db_chap_count}"
                )

            chapters_list = b_entry["chapters"]
            if not isinstance(chapters_list, list) or len(chapters_list) != b_chap_count:
                raise ManifestIncompleteError(
                    f"Book '{b_id}' requires exactly {b_chap_count} chapter specs, got {len(chapters_list)}."
                )

            validated_chapters: List[ChapterSpec] = []
            for expected_ch, ch_entry in enumerate(chapters_list, start=1):
                if not isinstance(ch_entry, dict) or "chapter" not in ch_entry or "verse_count" not in ch_entry:
                    raise ManifestValidationError(f"Malformed chapter spec in book '{b_id}': {ch_entry}")

                ch_num = ch_entry["chapter"]
                v_count = ch_entry["verse_count"]

                if ch_num != expected_ch:
                    raise ManifestInvalidOrderError(
                        f"Non-sequential chapter in '{b_id}': expected {expected_ch}, got {ch_num}"
                    )
                if not isinstance(v_count, int) or v_count < 1:
                    raise ManifestValidationError(
                        f"Invalid verse_count {v_count} in '{b_id}' chapter {ch_num} (must be >= 1)."
                    )

                for v in range(1, v_count + 1):
                    coord = (b_id, ch_num, v)
                    if coord in seen_coordinates:
                        raise ManifestDuplicateCoordinateError(f"Duplicate coordinate in manifest: {coord}")
                    seen_coordinates.add(coord)

                validated_chapters.append(ChapterSpec(chapter=ch_num, verse_count=v_count))
                total_verses += v_count
                total_chapters += 1

            validated_books.append(
                BookSpec(
                    book_id=b_id,
                    canonical_order=b_order,
                    standard_name=db_name,
                    chapter_count=b_chap_count,
                    chapters=tuple(validated_chapters),
                )
            )

        if require_full_canon:
            expected_seq = [b.book_id for b in validated_books]
            if expected_seq != db_order_list:
                raise ManifestInvalidOrderError("Manifest books sequence does not match DB canonical books.")

        if "total_books" in manifest_data and manifest_data["total_books"] != len(validated_books):
            raise ManifestValidationError(
                f"Manifest declared total_books={manifest_data['total_books']}, but found {len(validated_books)}"
            )
        if "total_chapters" in manifest_data and manifest_data["total_chapters"] != total_chapters:
            raise ManifestValidationError(
                f"Manifest declared total_chapters={manifest_data['total_chapters']}, but found {total_chapters}"
            )
        if "total_verses" in manifest_data and manifest_data["total_verses"] != total_verses:
            raise ManifestValidationError(
                f"Manifest declared total_verses={manifest_data['total_verses']}, but found {total_verses}"
            )

        return ValidatedManifest(
            manifest_id=manifest_data["manifest_id"],
            canon_id=manifest_data["canon_id"],
            edition=manifest_data.get("edition", "STANDARD"),
            checksum_sha256=str(recorded_checksum or ""),
            books=tuple(validated_books),
            total_books=len(validated_books),
            total_chapters=total_chapters,
            total_verses=total_verses,
        )


class CanonicalGridGenerator:
    """
    Executes isolated, transactional canonical grid generation using a pre-validated manifest.
    Detects conflicts without INSERT OR IGNORE.
    """

    PROVISIONAL_WITNESS_ID = "WIT-SEG-PROVISIONAL-CHAPTER"

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def generate(self, manifest: ValidatedManifest) -> GenerationSummary:
        """
        Execute deterministic generation in an atomic transaction.
        Rolls back completely on any error.
        """
        # Ensure foreign keys are enabled
        self.conn.execute("PRAGMA foreign_keys = ON;")

        # Verify provisional segmentation witness exists
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM segmentation_witnesses WHERE segmentation_id = ?;",
            (self.PROVISIONAL_WITNESS_ID,),
        )
        if not cursor.fetchone():
            raise CanonicalGridError(
                f"Missing required provisional segmentation witness '{self.PROVISIONAL_WITNESS_ID}'."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        pericopes_inserted = 0
        passages_inserted = 0
        assoc_inserted = 0
        pericopes_replayed = 0
        passages_replayed = 0
        assoc_replayed = 0

        # Run inside explicit transaction
        in_tx = self.conn.in_transaction
        if not in_tx:
            self.conn.execute("BEGIN IMMEDIATE;")

        try:
            current_sort_order = 1

            for book in manifest.books:
                for ch_spec in book.chapters:
                    ch_num = ch_spec.chapter
                    v_count = ch_spec.verse_count

                    pericope_id = compute_provisional_pericope_id(book.book_id, ch_num)
                    reference = f"{book.standard_name} {ch_num}:1-{v_count}"

                    # 1. Check or Insert Pericope
                    cursor.execute(
                        "SELECT book_id, segmentation_id, start_chapter, start_verse, end_chapter, end_verse "
                        "FROM pericopes WHERE pericope_id = ?;",
                        (pericope_id,),
                    )
                    existing_p = cursor.fetchone()
                    if existing_p:
                        # Verify exact match
                        if (
                            existing_p[0] != book.book_id
                            or existing_p[1] != self.PROVISIONAL_WITNESS_ID
                            or existing_p[2] != ch_num
                            or existing_p[3] != 1
                            or existing_p[4] != ch_num
                            or existing_p[5] != v_count
                        ):
                            raise CanonicalGridConflictError(
                                f"Conflict on pericope '{pericope_id}': existing record differs from manifest."
                            )
                        pericopes_replayed += 1
                    else:
                        cursor.execute(
                            """
                            INSERT INTO pericopes (
                                pericope_id, book_id, segmentation_id, reference,
                                start_chapter, start_verse, end_chapter, end_verse,
                                genre, boundary_source, boundary_confidence, status,
                                version, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PROVISIONAL_PARTITION',
                                      'CANONICAL_CHAPTER_FALLBACK', 'HIGH', 'REGISTERED', '1.0', ?);
                            """,
                            (
                                pericope_id,
                                book.book_id,
                                self.PROVISIONAL_WITNESS_ID,
                                reference,
                                ch_num,
                                1,
                                ch_num,
                                v_count,
                                now_iso,
                            ),
                        )
                        pericopes_inserted += 1

                    # 2. Process Passages and Associations
                    for v_num in range(1, v_count + 1):
                        passage_id = compute_passage_id(book.book_id, ch_num, v_num)

                        # Check existing passage
                        cursor.execute(
                            "SELECT pericope_id, book_id, chapter, verse, sort_order "
                            "FROM passages WHERE passage_id = ?;",
                            (passage_id,),
                        )
                        existing_pas = cursor.fetchone()

                        # Also check unique(book_id, chapter, verse)
                        cursor.execute(
                            "SELECT passage_id, sort_order FROM passages WHERE book_id = ? AND chapter = ? AND verse = ?;",
                            (book.book_id, ch_num, v_num),
                        )
                        coord_pas = cursor.fetchone()

                        if existing_pas:
                            if (
                                existing_pas[0] != pericope_id
                                or existing_pas[1] != book.book_id
                                or existing_pas[2] != ch_num
                                or existing_pas[3] != v_num
                            ):
                                raise CanonicalGridConflictError(
                                    f"Conflict on passage '{passage_id}': existing record differs from manifest."
                                )
                            passages_replayed += 1
                        elif coord_pas:
                            raise CanonicalGridConflictError(
                                f"Coordinate conflict: ({book.book_id}, {ch_num}, {v_num}) already assigned to '{coord_pas[0]}'."
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO passages (
                                    passage_id, pericope_id, book_id, chapter, verse, sort_order
                                ) VALUES (?, ?, ?, ?, ?, ?);
                                """,
                                (
                                    passage_id,
                                    pericope_id,
                                    book.book_id,
                                    ch_num,
                                    v_num,
                                    current_sort_order,
                                ),
                            )
                            passages_inserted += 1

                        # 3. Association in pericope_passages
                        assoc_id = compute_association_id(
                            self.PROVISIONAL_WITNESS_ID, pericope_id, passage_id
                        )
                        cursor.execute(
                            "SELECT pericope_id, passage_id, ordinal FROM pericope_passages WHERE association_id = ?;",
                            (assoc_id,),
                        )
                        existing_assoc = cursor.fetchone()
                        if existing_assoc:
                            if existing_assoc[0] != pericope_id or existing_assoc[1] != passage_id:
                                raise CanonicalGridConflictError(
                                    f"Conflict on pericope_passage '{assoc_id}'."
                                )
                            assoc_replayed += 1
                        else:
                            if v_count == 1:
                                b_pos = "SINGLE_VERSE_PERICOPE"
                            elif v_num == 1:
                                b_pos = "START_BOUNDARY"
                            elif v_num == v_count:
                                b_pos = "END_BOUNDARY"
                            else:
                                b_pos = "INTERNAL"

                            cursor.execute(
                                """
                                INSERT INTO pericope_passages (
                                    association_id, segmentation_id, pericope_id,
                                    passage_id, ordinal, containment_type,
                                    boundary_position, created_at
                                ) VALUES (?, ?, ?, ?, ?, 'FULL_VERSE', ?, ?);
                                """,
                                (
                                    assoc_id,
                                    self.PROVISIONAL_WITNESS_ID,
                                    pericope_id,
                                    passage_id,
                                    v_num,
                                    b_pos,
                                    now_iso,
                                ),
                            )
                            assoc_inserted += 1

                        current_sort_order += 1

            if not in_tx:
                self.conn.execute("COMMIT;")

            return GenerationSummary(
                books_processed=len(manifest.books),
                pericopes_inserted=pericopes_inserted,
                passages_inserted=passages_inserted,
                associations_inserted=assoc_inserted,
                pericopes_replayed=pericopes_replayed,
                passages_replayed=passages_replayed,
                associations_replayed=assoc_replayed,
                total_verses=manifest.total_verses,
            )
        except Exception:
            if not in_tx:
                self.conn.execute("ROLLBACK;")
            raise
