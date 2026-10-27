#!/usr/bin/env python3
"""
Polya Database Synchronization Script: Injil -> Bible & 4 Canonical Gospels
Enforces Polya Nomenklatur Directives across SQLite databases.

Operations:
1. Automated Safety Backup: creates <db>.bak-injil-sync-<timestamp> before transaction.
2. Sanitizes case_files_v2.claim_text.
3. Sanitizes case_files_v2.case_data_json (recursive walk).
4. Sanitizes execution_traces.trace_data_json.
5. Protects Islamic theological phrases (e.g. 'Injil Nabi Isa', 'wahyu Injil', 'Qur'anic Injil').
6. Converts 4 canonical gospels & apocrypha to 'kitab [Nama]'.
7. Converts collective & general references to 'Bible'.
8. Post-migration verification with detailed audit reporting.
"""

import sys
import os
import sqlite3
import json
import re
import shutil
import time
from typing import Any, List, Tuple

def sanitize_db_string(text: str) -> str:
    if not text or not isinstance(text, str):
        return text

    # 1. Protect Islamic theological phrases
    protected_matches: List[str] = []
    def stash_match(m):
        idx = len(protected_matches)
        protected_matches.append(m.group(0))
        return f"___POLYA_ISLAMIC_PROTECT_{idx}___"

    islamic_pattern = re.compile(
        r"\b(?:wahyu\s+Injil|Qur['’]?anic\s+Injil|Injil\s+Nabi\s+Isa(?:\s+Al-Masih|\s+al-Masih)?(?:\s+a\.s\.)?|Injil\s+(?:dalam|menurut)\s+Al-Qur['’]an|Injil\s+sejati\s+Nabi\s+Isa)\b",
        re.IGNORECASE
    )
    text = islamic_pattern.sub(stash_match, text)

    # 2. Specific 4 Canonical Gospels & Apocryphal Gospels
    text = re.sub(r"\bTeks\s+Injil\s+Yohanes\b", "Teks kitab Yohanes", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTeks\s+Injil\s+Lukas\b", "Teks kitab Lukas", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTeks\s+Injil\s+Matius\b", "Teks kitab Matius", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTeks\s+Injil\s+Markus\b", "Teks kitab Markus", text, flags=re.IGNORECASE)

    text = re.sub(
        r"\bInjil\s+(Yohanes|Lukas|Matius|Markus|Thomas|Tomas|Barnabas|Yudas|Maria(?:\s+Magdalena)?|Petrus|Filipus)\b",
        r"kitab \1",
        text,
        flags=re.IGNORECASE
    )

    # 3. Collective / canonical / general Injil phrases
    text = re.sub(r"\b(?:korpus\s+)?(?:empat|4)\s+Injil\s+kanonik\b", "korpus empat kitab kanonik Bible", text, flags=re.IGNORECASE)
    text = re.sub(r"\bketiga\s+Injil\s+Sinoptik\b", "ketiga kitab Sinoptik", text, flags=re.IGNORECASE)
    text = re.sub(r"\bInjil\s+Sinoptik\b", "kitab Sinoptik", text, flags=re.IGNORECASE)
    text = re.sub(r"\binjil\s+sinoptik\b", "kitab sinoptik", text)
    text = re.sub(r"\bantar-Injil\b", "antar-kitab Bible", text)
    text = re.sub(r"\bantar-injil\b", "antar-kitab bible", text)
    text = re.sub(r"\bTeks\s+Injil\s+Kanonikal\s*\(Kanon\s*66\s*Kitab\)", "Teks Kanonikal Bible (Kanon 66 Kitab)", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTeks\s+Injil\s+Kanonikal\b", "Teks Kanonikal Bible", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:kitab-kitab\s+Injil|Injil-Injil)\b", "kitab-kitab narasi Bible", text, flags=re.IGNORECASE)
    text = re.sub(r"\bnarasi\s+Injil\b", "narasi Bible", text, flags=re.IGNORECASE)

    text = re.sub(r"\bINJILNYA\b", "BIBLENYA", text)
    text = re.sub(r"\bInjilnya\b", "Biblenya", text)
    text = re.sub(r"\binjilnya\b", "biblenya", text)
    text = re.sub(r"\bINJIL\b", "BIBLE", text)
    text = re.sub(r"\bInjil\b", "Bible", text)
    text = re.sub(r"\binjil\b", "bible", text)

    # 4. Alkitab terms
    text = re.sub(r"\bAlkitabiah\b", "Biblika", text)
    text = re.sub(r"\balkitabiah\b", "biblika", text)
    text = re.sub(r"\balkitabiyah\b", "biblika", text)
    text = re.sub(r"\bALKITABNYA\b", "BIBLENYA", text)
    text = re.sub(r"\bAlkitabnya\b", "Biblenya", text)
    text = re.sub(r"\balkitabnya\b", "biblenya", text)
    text = re.sub(r"\bAlkitabmu\b", "Biblemu", text)
    text = re.sub(r"\balkitabmu\b", "biblemu", text)
    text = re.sub(r"\bAlkitabku\b", "Bibleku", text)
    text = re.sub(r"\balkitabku\b", "bibleku", text)
    text = re.sub(r"\bAlkitabu\b", "Biblemu", text)
    text = re.sub(r"\bALKITAB\b", "BIBLE", text)
    text = re.sub(r"\bAlkitab\b", "Bible", text)
    text = re.sub(r"\balkitab\b", "bible", text)

    # 5. Restore protected Islamic theological text
    for idx, orig in enumerate(protected_matches):
        text = text.replace(f"___POLYA_ISLAMIC_PROTECT_{idx}___", orig)

    return text

def walk_and_sanitize(obj: Any) -> Any:
    if isinstance(obj, str):
        return sanitize_db_string(obj)
    elif isinstance(obj, list):
        return [walk_and_sanitize(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: walk_and_sanitize(v) for k, v in obj.items()}
    return obj

def process_database(db_path: str) -> None:
    if not os.path.exists(db_path):
        # Check in /home/ubuntu/Polya-AI/ if relative
        alt_path = os.path.join("/home/ubuntu/Polya-AI", db_path)
        if os.path.exists(alt_path):
            db_path = alt_path
        else:
            print(f"[ERROR] Database file not found: {db_path}", file=sys.stderr)
            return

    db_path = os.path.abspath(db_path)
    print(f"\n=======================================================")
    print(f"Target Database: {db_path}")
    print(f"=======================================================")

    # 1. Safety Backup
    ts = int(time.time())
    backup_path = f"{db_path}.bak-injil-sync-{ts}"
    shutil.copy2(db_path, backup_path)
    print(f"[BACKUP] Safety copy created -> {backup_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # 2. Process case_files_v2.claim_text
        cur.execute("SELECT case_id, claim_text FROM case_files_v2 WHERE claim_text LIKE '%injil%' OR claim_text LIKE '%alkitab%';")
        claim_rows = cur.fetchall()
        claim_updated = 0
        for cid, claim_text in claim_rows:
            sanitized_claim = sanitize_db_string(claim_text)
            if sanitized_claim != claim_text:
                cur.execute("UPDATE case_files_v2 SET claim_text = ? WHERE case_id = ?;", (sanitized_claim, cid))
                claim_updated += 1

        print(f"[MIGRATION] case_files_v2.claim_text: checked {len(claim_rows)}, updated {claim_updated}")

        # 3. Process case_files_v2.case_data_json
        cur.execute("SELECT case_id, case_data_json FROM case_files_v2 WHERE case_data_json LIKE '%injil%' OR case_data_json LIKE '%alkitab%';")
        case_rows = cur.fetchall()
        cases_updated = 0
        for cid, cjson in case_rows:
            try:
                data = json.loads(cjson)
                sanitized_data = walk_and_sanitize(data)
                sanitized_json = json.dumps(sanitized_data, ensure_ascii=False)
                if sanitized_json != cjson:
                    cur.execute("UPDATE case_files_v2 SET case_data_json = ? WHERE case_id = ?;", (sanitized_json, cid))
                    cases_updated += 1
            except Exception as e:
                print(f"[WARN] Failed parsing JSON for case {cid}: {e}")

        print(f"[MIGRATION] case_files_v2.case_data_json: checked {len(case_rows)}, updated {cases_updated}")

        # 4. Process execution_traces.trace_data_json
        cur.execute("SELECT trace_id, trace_data_json FROM execution_traces WHERE trace_data_json LIKE '%injil%' OR trace_data_json LIKE '%alkitab%';")
        trace_rows = cur.fetchall()
        traces_updated = 0
        for tid, tjson in trace_rows:
            try:
                data = json.loads(tjson)
                sanitized_data = walk_and_sanitize(data)
                sanitized_json = json.dumps(sanitized_data, ensure_ascii=False)
                if sanitized_json != tjson:
                    cur.execute("UPDATE execution_traces SET trace_data_json = ? WHERE trace_id = ?;", (sanitized_json, tid))
                    traces_updated += 1
            except Exception as e:
                print(f"[WARN] Failed parsing JSON for trace {tid}: {e}")

        print(f"[MIGRATION] execution_traces.trace_data_json: checked {len(trace_rows)}, updated {traces_updated}")

        conn.commit()
        print("[TRANSACTION] All changes committed successfully.")

        # 5. Verification
        cur.execute("SELECT case_id, claim_text FROM case_files_v2 WHERE claim_text LIKE '%injil%';")
        res_claims = cur.fetchall()
        islamic_claims = [r for r in res_claims if re.search(r"Injil\s+Nabi\s+Isa|wahyu\s+Injil|Qur['’]?anic\s+Injil", r[1], re.I)]
        unauth_claims = [r for r in res_claims if r not in islamic_claims]

        cur.execute("SELECT case_id, case_data_json FROM case_files_v2 WHERE case_data_json LIKE '%injil%';")
        res_cases = cur.fetchall()
        unauth_cases = []
        for cid, cjson in res_cases:
            matches = re.findall(r'\b\w*\s*injil\s*\w*\b', cjson, re.I)
            unauth_matches = [m for m in matches if not re.search(r"Injil\s+Nabi\s+Isa|wahyu\s+Injil|Qur['’]?anic\s+Injil", m, re.I)]
            if unauth_matches:
                unauth_cases.append((cid, unauth_matches))

        cur.execute("SELECT trace_id, trace_data_json FROM execution_traces WHERE trace_data_json LIKE '%injil%';")
        res_traces = cur.fetchall()

        print("\n--- VERIFICATION AUDIT ---")
        print(f"Remaining claim_text with 'injil': {len(res_claims)} (Protected Islamic: {len(islamic_claims)}, Unauthorized: {len(unauth_claims)})")
        print(f"Remaining case_data_json with unauthorized 'injil': {len(unauth_cases)}")
        print(f"Remaining execution_traces with 'injil': {len(res_traces)}")

        if unauth_claims or unauth_cases or res_traces:
            print("[WARN] Some unauthorized occurrences remain. Inspecting:")
            for cid, m in unauth_cases[:5]:
                print(f"  Case {cid}: {m}")
        else:
            print("[SUCCESS] Zero unauthorized 'injil' residues in database!")

    except Exception as e:
        conn.rollback()
        print(f"[FATAL] Transaction failed and rolled back: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

def main():
    db_targets = sys.argv[1:] if len(sys.argv) > 1 else [
        "data/polya_arena.db",
        "data/polya_arena_staging.db"
    ]
    for db in db_targets:
        process_database(db)

if __name__ == "__main__":
    main()
