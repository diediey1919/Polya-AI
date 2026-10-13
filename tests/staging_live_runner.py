import json
import time
import uuid
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8001"

def get_guest_auth(client_id_prefix="cli_staging"):
    cid = f"{client_id_prefix}_{uuid.uuid4().hex[:8]}"
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/guest",
        data=json.dumps({"client_id": cid}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["user_id"], data["session_token"]

def send_analyze(claim, mode=None, user_id=None, token=None):
    payload = {"claim": claim}
    if mode is not None:
        payload["mode"] = mode
    if user_id:
        payload["user_id"] = user_id
    payload["request_id"] = f"req_stg_{uuid.uuid4().hex[:10]}"

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/calculator/analyze",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            dur = time.time() - t0
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, dur, body
    except urllib.error.HTTPError as he:
        dur = time.time() - t0
        err_body = he.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw": err_body}
        return he.code, dur, err_json
    except Exception as exc:
        dur = time.time() - t0
        return -1, dur, {"error": str(exc)}

def main():
    print("=== LIVE STAGING VALIDATION SUITE ===")
    results = []

    # 1. Invalid Mode Gate
    uid, tok = get_guest_auth("stg_inv")
    st, dur, resp = send_analyze("Tes invalid mode", mode="unrecognized_mode", user_id=uid, token=tok)
    print(f"Gate 1: Invalid Mode -> HTTP {st} in {dur:.2f}s (Expect 422)")
    assert st == 422, f"Expected 422 but got {st}"

    # 2. Legacy Request Without Mode
    uid, tok = get_guest_auth("stg_legacy")
    st, dur, resp = send_analyze("Apakah ada bukti naskah kuno?", mode=None, user_id=uid, token=tok)
    assert st == 200, f"Expected 200 but got {st}"
    cf_data = resp.get("case_file", {}) if isinstance(resp, dict) else {}
    print(f"Gate 2: Legacy (No Mode) -> HTTP {st} in {dur:.2f}s | Context: {cf_data.get('context', '')[:50]}")
    assert "RESEARCH" in cf_data.get("context", "")

    # Test cases: 4 claims x 2 modes
    test_claims = [
        ("A", "Yesus tidak pernah secara langsung berkata, 'Aku adalah Tuhan'."),
        ("B", "Doktrin Tritunggal muncul kemudian dan bukan ajaran asli Yesus."),
        ("C", "Air mendidih pada 100°C pada tekanan 1 atmosfer."),
        ("D", "Spekulasi kosmologi kuantum XZ99.")
    ]

    for label, claim in test_claims:
        for mode in ["debate", "research"]:
            uid, tok = get_guest_auth(f"stg_{label}_{mode}")
            print(f"\nRunning Claim {label} [{mode.upper()}]...")
            st, dur, resp = send_analyze(claim, mode=mode, user_id=uid, token=tok)
            cf = resp.get("case_file", {})
            evidence = cf.get("evidence", [])
            sources = cf.get("sources", [])
            notice = cf.get("notice", "")
            arg = cf.get("argument", "")
            rebuttal = cf.get("rebuttal", "")

            res_entry = {
                "label": label,
                "claim": claim,
                "mode": mode,
                "status_code": st,
                "duration_s": round(dur, 2),
                "notice": notice,
                "evidence_count": len(evidence),
                "evidence_refs": [e.get("source_text", "")[:40] for e in evidence],
                "sources_count": len(sources),
                "sources": sources[:2],
                "argument_preview": arg[:80],
                "rebuttal_preview": rebuttal[:80]
            }
            results.append(res_entry)
            print(f"  -> HTTP {st} ({dur:.2f}s) | Notice: {notice}")
            print(f"  -> Evidence Count: {len(evidence)} | Sources: {len(sources)}")
            print(f"  -> Argument: {arg[:70]}...")

    with open("/home/ubuntu/Polya-AI/tests/staging_live_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== ALL STAGING LIVE REQUESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
