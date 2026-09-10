"""
Polia AI Runtime - Knowledge Normalization Layer
Converts raw Markdown records into structured in-memory representations.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class NormalizedRecord:
    id: str
    filename: str
    category: str  # 'source', 'claim', 'analysis', 'specialist'
    title: str
    sub_type: str = "GENERAL"
    tradition: str = "GENERAL"
    step: Optional[str] = None
    content: str = ""
    summary: str = ""
    sources_referenced: List[str] = field(default_factory=list)
    claims_referenced: List[str] = field(default_factory=list)
    steps_referenced: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    claim_tests_count: int = 0
    case_studies_count: int = 0
    steelmen_count: int = 0
    error_codes_count: int = 0
    status: str = "VALID"
    size_bytes: int = 0
    line_count: int = 0

class KnowledgeNormalizer:
    """Normalizes raw markdown text into NormalizedRecord objects."""

    @staticmethod
    def normalize_source(filename: str, content: str) -> NormalizedRecord:
        m_id = re.search(r"SOURCE_ID:\s*([A-Z0-9_\-]+)", content)
        sid = m_id.group(1) if m_id else os.path.splitext(filename)[0]

        m_title = re.search(r"TITLE:\s*(.+)", content)
        if not m_title:
            m_h = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            title = m_h.group(1).strip() if m_h else filename
        else:
            title = m_title.group(1).strip()

        m_type = re.search(r"TYPE:\s*(.+)", content)
        sub_type = m_type.group(1).strip() if m_type else "SOURCE"

        # Determine tradition
        tradition = "GENERAL"
        content_lower = content.lower()
        if any(w in content_lower for w in ["qur'an", "quran", "hadith", "sunnah", "islamic", "hijazi", "uthman"]):
            tradition = "ISLAMIC"
        elif any(w in content_lower for w in ["gospel", "patristic", "paul", "nicene", "chalcedon", "testament", "christ"]):
            tradition = "CHRISTIAN"
        elif any(w in content_lower for w in ["dead sea scrolls", "qumran", "torah", "tanakh", "jewish", "rabbinic"]):
            tradition = "JEWISH"

        lines = content.splitlines()
        summary = "\n".join(lines[:15]) if len(lines) > 15 else content

        return NormalizedRecord(
            id=sid,
            filename=filename,
            category="source",
            title=title,
            sub_type=sub_type,
            tradition=tradition,
            content=content,
            summary=summary,
            size_bytes=len(content),
            line_count=len(lines)
        )

    @staticmethod
    def normalize_claim(filename: str, content: str) -> NormalizedRecord:
        m_id = re.search(r"CLAIM_ID:\s*([A-Z0-9_\-]+)", content)
        cid = m_id.group(1) if m_id else os.path.splitext(filename)[0]

        m_title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
        title = m_title.group(1).strip() if m_title else filename

        m_src = re.search(r"SOURCE_ID:\s*([A-Z0-9_\-]+)", content)
        src_refs = [m_src.group(1)] if m_src else []

        lines = content.splitlines()
        summary = "\n".join(lines[:12]) if len(lines) > 12 else content

        return NormalizedRecord(
            id=cid,
            filename=filename,
            category="claim",
            title=title,
            content=content,
            summary=summary,
            sources_referenced=src_refs,
            size_bytes=len(content),
            line_count=len(lines)
        )

    @staticmethod
    def normalize_analysis(filename: str, content: str) -> NormalizedRecord:
        aid = f"ANALYSIS:{filename}"

        m_title = re.search(r"^#\s+(.+)", content, re.MULTILINE)
        title = m_title.group(1).strip() if m_title else filename

        m_step = re.search(r"\bSTEP\s*[:\-_]?\s*(\d+[A-Z]?)\b", content[:2500], re.IGNORECASE)
        step_num = m_step.group(1).upper() if m_step else None

        # Extract references
        src_refs = sorted(list(set(re.findall(r"\b(SRC-[A-Z0-9_\-]+)\b", content))))
        clm_refs = sorted(list(set(re.findall(r"\b(CLAIM-[A-Z0-9_\-]+)\b", content))))
        step_refs = sorted(list(set(re.findall(r"\bSTEP\s+(\d+[A-Z]?)\b", content))))

        # Counts of internal blocks
        ct_count = len(re.findall(r"### TEST\s+[A-Z]{1,2}\b", content)) or len(re.findall(r"^\|\s*[A-Z]{1,2}\s*\|", content, re.MULTILINE))
        cs_count = len(re.findall(r"### CASE\s+\d+", content))
        sm_count = len(re.findall(r"### STEELMAN\s+\d+", content))
        err_count = len(set(re.findall(r"\bE\d{1,2}\b", content)))

        status = "VALID"
        if "PASS FINAL" in content[-2000:]: status = "PASS FINAL"
        elif "PASS" in content[-2000:]: status = "PASS"

        # Tradition classification
        tradition = "CROSS_RELIGIOUS"
        title_lower = title.lower()
        if any(w in title_lower for w in ["quran", "hadith", "sirah", "shii", "sunni", "kalam", "naskh", "sanaa", "uthman"]):
            tradition = "ISLAMIC"
        elif any(w in title_lower for w in ["gospel", "paul", "nicene", "chalcedon", "ephesus", "reunion", "christology", "trinity", "patristic", "athanasius", "arius", "filioque"]):
            tradition = "CHRISTIAN"

        lines = content.splitlines()
        summary = "\n".join(lines[:25]) if len(lines) > 25 else content

        return NormalizedRecord(
            id=aid,
            filename=filename,
            category="analysis",
            title=title,
            step=step_num,
            tradition=tradition,
            content=content,
            summary=summary,
            sources_referenced=src_refs,
            claims_referenced=clm_refs,
            steps_referenced=step_refs,
            claim_tests_count=ct_count,
            case_studies_count=cs_count,
            steelmen_count=sm_count,
            error_codes_count=err_count,
            status=status,
            size_bytes=len(content),
            line_count=len(lines)
        )
