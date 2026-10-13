"""
Builder for Canonical Versification Manifest (Task 5F-C).
Extracts vm_kjv array from CrossWire canon_kjv.h, associates with 66 canon books,
and produces strictly validated manifest and TVTMS artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

import jsonschema

from bible_engine.canonical_grid import compute_manifest_payload_checksum


def build_canonical_manifest(
    canon_kjv_path: Path,
    db_path: Path,
    output_paths: List[Path],
    schema_path: Path,
) -> Dict[str, Any]:
    # 1. Verify canon_kjv.h hash
    with open(canon_kjv_path, "rb") as f:
        raw_bytes = f.read()
    file_sha256 = hashlib.sha256(raw_bytes).hexdigest().lower()
    expected_src_sha256 = "cf2f2844f0f8c8c1c66988c90dffff7708aada634b89d31e5e1ab1bcbb5fd88e"
    if file_sha256 != expected_src_sha256:
        raise ValueError(
            f"Source canon_kjv.h SHA-256 mismatch: expected {expected_src_sha256}, got {file_sha256}"
        )

    content = raw_bytes.decode("utf-8")

    # 2. Extract vm_kjv[] array
    match = re.search(r"int vm_kjv\[\]\s*=\s*\{([^}]+)\};", content, re.DOTALL)
    if not match:
        raise ValueError("Failed to locate vm_kjv[] definition in canon_kjv.h")

    vm_raw = match.group(1)
    vm_clean = re.sub(r"//[^\n]*", "", vm_raw)
    verses = [int(x.strip()) for x in vm_clean.replace("\n", " ").split(",") if x.strip()]

    if len(verses) != 1189:
        raise ValueError(f"Expected exactly 1189 chapter verse counts, parsed {len(verses)}")

    total_verses = sum(verses)
    if total_verses != 31102:
        raise ValueError(f"Expected total 31102 verses, computed {total_verses}")

    # 3. Read canonical books from database in read-only mode
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT book_id, canonical_order, standard_name, english_name, chapter_count "
        "FROM books ORDER BY canonical_order ASC;"
    )
    db_books = cursor.fetchall()
    conn.close()

    if len(db_books) != 66:
        raise ValueError(f"Expected 66 books from database, got {len(db_books)}")

    # 4. Associate chapters and verses
    v_idx = 0
    manifest_books: List[Dict[str, Any]] = []
    for book_row in db_books:
        b_id, c_order, std_name, eng_name, ch_count = book_row
        chaps_data = []
        book_verses = 0
        for ch in range(1, ch_count + 1):
            v_cnt = verses[v_idx]
            v_idx += 1
            if v_cnt <= 0:
                raise ValueError(f"Non-positive verse count {v_cnt} at {b_id} chapter {ch}")
            book_verses += v_cnt
            chaps_data.append({"chapter": ch, "verse_count": v_cnt})

        manifest_books.append(
            {
                "book_id": b_id,
                "canonical_order": c_order,
                "standard_name": std_name,
                "chapter_count": ch_count,
                "total_verses": book_verses,
                "chapters": chaps_data,
            }
        )

    if v_idx != 1189:
        raise ValueError(f"Did not consume all 1189 chapters, stopped at index {v_idx}")

    # 5. Build manifest payload
    manifest_payload: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "manifest_id": "MANIFEST-CANONICAL-KJV-STANDARD",
        "canon_id": "CANON-PROTESTANT-66",
        "versification_system": "PROTESTANT_KJV_STANDARD",
        "source_name": "CrossWire SWORD Tools canon_kjv.h",
        "source_version": "SVN-r568",
        "source_url": "https://crosswire.org/svn/sword-tools/trunk/versification/basicv11ns/canon_kjv.h",
        "license": "GPL-2.0",
        "source_checksum_sha256": expected_src_sha256,
        "total_books": 66,
        "total_chapters": 1189,
        "total_verses": 31102,
        "normalization_method": "DETERMINISTIC_EXTRACTION_VM_KJV_HEADER_PARSER",
        "books": manifest_books,
    }

    # 6. Compute manifest checksum without checksum field
    manifest_checksum = compute_manifest_payload_checksum(manifest_payload)
    manifest_payload["manifest_checksum_sha256"] = manifest_checksum

    # 7. Validate with jsonschema
    with open(schema_path, "r", encoding="utf-8") as sf:
        schema_json = json.load(sf)
    jsonschema.validate(instance=manifest_payload, schema=schema_json)

    # 8. Write to output paths
    payload_str = json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n"
    for out_path in output_paths:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(payload_str)

    return manifest_payload


def build_tvtms_artifact(
    tvtms_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    with open(tvtms_path, "rb") as f:
        raw_bytes = f.read()
    file_sha256 = hashlib.sha256(raw_bytes).hexdigest().lower()
    expected_sha256 = "63058e0f20201af4bdaa7d830da5be8f493455d947c5f147d84840b33db9ddf8"
    if file_sha256 != expected_sha256:
        raise ValueError(
            f"TVTMS SHA-256 mismatch: expected {expected_sha256}, got {file_sha256}"
        )

    text = raw_bytes.decode("utf-8", errors="replace")
    mappings = re.findall(
        r"([A-Za-z0-9]+\.\d+\.\d+(?:![ab])?=[A-Za-z0-9]+\.\d+\.\d+(?:![ab])?)", text
    )

    tvtms_artifact = {
        "schema_version": "1.0.0",
        "dataset_id": "DATASET-STEPBIBLE-TVTMS-MAPPINGS",
        "title": "Translators Versification Traditions with Methodology for Standardisation",
        "source_name": "STEPBible TVTMS Dataset",
        "source_version": "master-blob-4fdcb4fd761ba8a680a3f0cc95ad65f591e18d4b",
        "source_url": "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Versification/TVTMS%20-%20Translators%20Versification%20Traditions%20with%20Methodology%20for%20Standardisation%20for%20Eng%2BHeb%2BLat%2BGrk%2BOthers%20-%20STEPBible.org%20CC%20BY.txt",
        "license": "CC-BY-4.0",
        "attribution": "Data created by www.STEPBible.org based on work at Tyndale House Cambridge (CC BY 4.0)",
        "source_checksum_sha256": expected_sha256,
        "traditions": [
            "ENGLISH_KJV",
            "HEBREW_MASORETIC",
            "GREEK_SEPTUAGINT_NT",
            "LATIN_VULGATE",
        ],
        "extracted_rules_count": len(mappings),
        "sample_mappings": mappings[:30],
    }

    canonical_repr = json.dumps(
        {k: v for k, v in tvtms_artifact.items() if k != "artifact_checksum_sha256"},
        sort_keys=True,
        separators=(",", ":"),
    )
    tvtms_artifact["artifact_checksum_sha256"] = hashlib.sha256(
        canonical_repr.encode("utf-8")
    ).hexdigest().lower()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(tvtms_artifact, out_f, indent=2, ensure_ascii=False)
        out_f.write("\n")

    return tvtms_artifact


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    canon_kjv = repo_root / "tests" / "_test_staging_versification" / "canon_kjv.h"
    db_file = Path("/home/ubuntu/.polya/bible_engine.db")
    schema_f = (
        repo_root
        / "schemas"
        / "bible_engine"
        / "canonical_manifest.schema.json"
    )
    out_manifests = [
        repo_root
        / "schemas"
        / "bible_engine"
        / "canonical_versification_manifest.json",
        repo_root
        / "data"
        / "canonical"
        / "canonical_versification_manifest.json",
    ]
    manifest = build_canonical_manifest(canon_kjv, db_file, out_manifests, schema_f)
    print("Canonical Manifest Built successfully.")
    print(f"Manifest ID: {manifest['manifest_id']}")
    print(f"Total Books: {manifest['total_books']}")
    print(f"Total Chapters: {manifest['total_chapters']}")
    print(f"Total Verses: {manifest['total_verses']}")
    print(f"Manifest Checksum: {manifest['manifest_checksum_sha256']}")

    tvtms_file = (
        repo_root / "tests" / "_test_staging_versification" / "TVTMS_versification.txt"
    )
    tvtms_out = repo_root / "data" / "canonical" / "stepbible_tvtms_mappings.json"
    tvtms_art = build_tvtms_artifact(tvtms_file, tvtms_out)
    print("STEPBible TVTMS Artifact Built successfully.")
    print(f"Dataset ID: {tvtms_art['dataset_id']}")
    print(f"Rules Count: {tvtms_art['extracted_rules_count']}")
    print(f"Artifact Checksum: {tvtms_art['artifact_checksum_sha256']}")
