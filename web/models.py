"""
Polya Apologetika — Domain Models & Data Contracts
Phase-1 Web Foundation
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UserPerspective(str, Enum):
    CHRISTIAN = "christian"
    ISLAM = "islam"


class EntitlementState(str, Enum):
    FREE = "FREE"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PREMIUM_ACTIVE = "PREMIUM_ACTIVE"
    PREMIUM_EXPIRED = "PREMIUM_EXPIRED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CANCELLED = "CANCELLED"


class UserApologeticsContext(BaseModel):
    """Production-shaped apologetics context model."""
    ui_locale: str = Field(default="id", description="Language of UI")
    user_perspective: UserPerspective = Field(default=UserPerspective.CHRISTIAN, description="Perspective for preparation")
    opponent_perspective: Optional[str] = Field(default="islam", description="Opponent perspective")
    debate_locale: str = Field(default="id", description="Debate language")
    source_locale: Optional[str] = Field(default="el", description="Primary text source language (e.g., el, he, ar)")


class CaseFile(BaseModel):
    """Canonical 10-point Apologetics Case File Schema."""
    case_id: str
    claim: str
    context: str
    evidence: List[Dict[str, Any]]
    argument: str
    counterargument: str
    rebuttal: str
    weakness: str
    sources: List[Dict[str, str]]
    open_questions: List[str]
    debate_preparation: Dict[str, Any]
    is_demo: bool = True
    notice: str = "DEMO / MOCK DATA — Strictly for testing UI and structure"
    synthesis_status: str = ""
    retrieval_status: str = ""
    fallback_used: bool = False


class PaymentTransaction(BaseModel):
    """Production-shaped payment transaction contract."""
    transactionId: str
    userId: str
    orderId: str
    amount: int = 99000
    currency: str = "IDR"
    provider: str = "midtrans"
    providerStatus: str = "pending"
    internalStatus: EntitlementState = EntitlementState.PAYMENT_PENDING
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verifiedAt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    idempotencyKey: str


# 10 Canonical Demo Claims
CANONICAL_DEMO_CLAIMS = [
    "Yesus tidak pernah secara langsung berkata, 'Aku adalah Tuhan.'",
    "Yohanes 10:30 hanya berarti Yesus dan Bapa memiliki tujuan yang sama, bukan bahwa mereka satu hakikat.",
    "Paulus menghapus kewajiban Taurat bagi orang Kristen.",
    "Jika Yesus adalah Tuhan, mengapa Yesus berdoa kepada Tuhan di Getsemani?",
    "Al-Qur’an tidak mengajarkan bahwa Yesus disalibkan.",
    "Doktrin Tritunggal adalah doktrin yang muncul kemudian dan bukan ajaran asli Yesus.",
    "Alkitab telah mengalami perubahan sehingga tidak dapat dijadikan dasar yang dapat dipercaya.",
    "Muhammad tidak pernah disebut atau dinubuatkan dalam Alkitab.",
    "Keselamatan dalam Kekristenan bertentangan dengan keadilan karena manusia dihukum akibat dosa Adam.",
    "Jika Al-Qur’an benar-benar berasal dari Tuhan, mengapa terdapat perbedaan dengan kitab-kitab sebelumnya?"
]

# Canonical 17 Languages Registry
LANGUAGE_REGISTRY = [
    {"code": "en", "name": "English", "native": "English", "dir": "ltr"},
    {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia", "dir": "ltr"},
    {"code": "ar", "name": "Arabic", "native": "العربية", "dir": "rtl"},
    {"code": "tr", "name": "Turkish", "native": "Türkçe", "dir": "ltr"},
    {"code": "ur", "name": "Urdu", "native": "اردو", "dir": "rtl"},
    {"code": "fa", "name": "Persian", "native": "فارسی", "dir": "rtl"},
    {"code": "hi", "name": "Hindi", "native": "हिन्दी", "dir": "ltr"},
    {"code": "bn", "name": "Bengali", "native": "বাংলা", "dir": "ltr"},
    {"code": "zh", "name": "Chinese", "native": "中文", "dir": "ltr"},
    {"code": "ja", "name": "Japanese", "native": "日本語", "dir": "ltr"},
    {"code": "ko", "name": "Korean", "native": "한국어", "dir": "ltr"},
    {"code": "es", "name": "Spanish", "native": "Español", "dir": "ltr"},
    {"code": "fr", "name": "French", "native": "Français", "dir": "ltr"},
    {"code": "pt", "name": "Portuguese", "native": "Português", "dir": "ltr"},
    {"code": "de", "name": "German", "native": "Deutsch", "dir": "ltr"},
    {"code": "it", "name": "Italian", "native": "Italiano", "dir": "ltr"},
    {"code": "ru", "name": "Russian", "native": "Русский", "dir": "ltr"},
]
