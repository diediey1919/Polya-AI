"""
Polia AI Runtime - Observability, Tracing, and Logging (Phase 22)
Structured telemetry, latency measurement, and JSONL audit trail for all runtime events.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any

PRIMARY_LOG_PATH = "/home/ubuntu/.polya/logs/polya_runtime.jsonl"
FALLBACK_LOG_PATH = "/home/ubuntu/Polya-AI/.polya/logs/polya_runtime.jsonl"

class RuntimeObservability:
    def __init__(self, log_path: Optional[str] = None):
        if log_path:
            self.log_path = log_path
        elif os.path.exists(os.path.dirname(PRIMARY_LOG_PATH)) and os.access(os.path.dirname(PRIMARY_LOG_PATH), os.W_OK):
            self.log_path = PRIMARY_LOG_PATH
        else:
            self.log_path = FALLBACK_LOG_PATH

        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Append a structured JSON line to the runtime audit log."""
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            "details": details
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass  # Non-blocking telemetry

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Read the most recent N log events."""
        if not os.path.exists(self.log_path):
            return []

        records = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except Exception:
                            pass
        except Exception:
            return []

        return records[-limit:]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Aggregate performance and operational statistics."""
        logs = self.get_recent_logs(200)
        total_queries = sum(1 for l in logs if l.get("event_type") == "RETRIEVAL_PIPELINE")
        total_fallacies = sum(len(l.get("details", {}).get("fallacies", [])) for l in logs if l.get("event_type") == "RETRIEVAL_PIPELINE")
        latencies = [l.get("details", {}).get("latency_ms", 0) for l in logs if l.get("event_type") == "RETRIEVAL_PIPELINE"]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        return {
            "log_path": self.log_path,
            "total_logged_events": len(logs),
            "total_queries_recorded": total_queries,
            "total_fallacies_intercepted": total_fallacies,
            "average_latency_ms": avg_latency
        }
