"""
Polia AI Runtime - Knowledge Access Layer
Provides a stable, read-only interface to the file-backed Apologetica Knowledge Base.
"""

import os
import re
from typing import Dict, List, Optional, Any
from polya_runtime.errors import KnowledgeNotFoundError

class KnowledgeAccessLayer:
    """
    Abstractions for discovering and reading Knowledge Base entities.
    Does not mutate or duplicate existing records.
    """
    def __init__(self, primary_path: str = "/home/ubuntu/apologetica",
                 fallback_path: str = "/home/ubuntu/Polya-AI/apologetica"):
        self.primary_path = primary_path
        self.fallback_path = fallback_path
        self._sources_cache: Optional[Dict[str, str]] = None
        self._claims_cache: Optional[Dict[str, str]] = None
        self._analyses_cache: Optional[Dict[str, str]] = None

    def _resolve_file(self, rel_subpath: str) -> str:
        """Resolve file path checking primary then fallback."""
        p1 = os.path.join(self.primary_path, rel_subpath)
        if os.path.exists(p1):
            return p1
        p2 = os.path.join(self.fallback_path, rel_subpath)
        if os.path.exists(p2):
            return p2
        raise KnowledgeNotFoundError(f"Knowledge file not found: {rel_subpath}")

    def list_sources(self) -> List[str]:
        """List all unique source filenames available."""
        s = set()
        for base in [self.primary_path, self.fallback_path]:
            d = os.path.join(base, "knowledge", "sources")
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith(".md"):
                        s.add(f)
        return sorted(list(s))

    def list_claims(self) -> List[str]:
        """List all unique claim filenames available."""
        s = set()
        for base in [self.primary_path, self.fallback_path]:
            d = os.path.join(base, "knowledge", "claims")
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith(".md"):
                        s.add(f)
        return sorted(list(s))

    def list_analyses(self) -> List[str]:
        """List all unique analysis filenames available."""
        s = set()
        for base in [self.primary_path, self.fallback_path]:
            d = os.path.join(base, "knowledge", "analyses")
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith(".md"):
                        s.add(f)
        return sorted(list(s))

    def list_specialists(self) -> List[str]:
        """List all 12 specialist modules."""
        s = set()
        for base in [self.primary_path, self.fallback_path]:
            d = os.path.join(base, "specialists")
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith(".md"):
                        s.add(f)
        return sorted(list(s))

    def get_source_content(self, source_id_or_file: str) -> str:
        """Fetch raw content of a source record by filename or SOURCE_ID."""
        if not source_id_or_file.endswith(".md"):
            fn = f"{source_id_or_file}.md"
        else:
            fn = source_id_or_file
        path = self._resolve_file(os.path.join("knowledge", "sources", fn))
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def get_claim_content(self, claim_id_or_file: str) -> str:
        """Fetch raw content of a claim record by filename or CLAIM_ID."""
        if not claim_id_or_file.endswith(".md"):
            fn = f"{claim_id_or_file}.md"
        else:
            fn = claim_id_or_file
        path = self._resolve_file(os.path.join("knowledge", "claims", fn))
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def get_analysis_content(self, analysis_filename: str) -> str:
        """Fetch raw content of an analysis record."""
        path = self._resolve_file(os.path.join("knowledge", "analyses", analysis_filename))
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def get_specialist_content(self, specialist_name_or_file: str) -> str:
        """Fetch content of a specialist module."""
        if not specialist_name_or_file.endswith(".md"):
            fn = f"{specialist_name_or_file}.md"
        else:
            fn = specialist_name_or_file
        path = self._resolve_file(os.path.join("specialists", fn))
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def get_system_prompt_content(self) -> str:
        """Fetch Chief Apologetics Agent prompt (99_AI_SYSTEM_PROMPT.md)."""
        path = self._resolve_file(os.path.join("system", "99_AI_SYSTEM_PROMPT.md"))
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def get_counts(self) -> Dict[str, int]:
        """Return factual counts of all knowledge assets."""
        srcs = len(self.list_sources())
        clms = len(self.list_claims())
        ans = len(self.list_analyses())
        specs = len(self.list_specialists())
        return {
            "sources": srcs,
            "claims": clms,
            "analyses": ans,
            "specialists": specs,
            "total_primary_records": srcs + clms + ans
        }

    def find_analysis_by_step(self, step_number: str) -> Optional[str]:
        """Find analysis filename corresponding to a STEP number (e.g. '139' or '103R')."""
        clean_step = step_number.upper().strip()
        for fn in self.list_analyses():
            content = self.get_analysis_content(fn)
            m = re.search(r"\bSTEP\s*[:\-_]?\s*(\d+[A-Z]?)\b", content[:2500], re.IGNORECASE)
            if m and m.group(1).upper() == clean_step:
                return fn
        return None
