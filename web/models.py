"""
Polya Apologetika — Domain Models & Data Contracts
Phase-1 Web Foundation
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UserPerspective(str, Enum):
    CHRISTIAN_PROTESTANT = "christian_protestant"
    CHRISTIAN_CATHOLIC = "christian_catholic"
    ISLAM = "islam"
    JUDAISM = "judaism"
    ATHEIST_SECULAR = "atheist_secular"
    # Backward compatibility alias for legacy value "christian"
    CHRISTIAN = "christian_protestant"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("christian", "protestant"):
                return cls.CHRISTIAN_PROTESTANT
            elif v in ("catholic", "katolik", "christian_catholic"):
                return cls.CHRISTIAN_CATHOLIC
            elif v in ("islam", "muslim"):
                return cls.ISLAM
            elif v in ("judaism", "jewish", "yahudi"):
                return cls.JUDAISM
            elif v in ("atheist", "secular", "atheist_secular", "ateis"):
                return cls.ATHEIST_SECULAR
        return super()._missing_(value)


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
    user_perspective: UserPerspective = Field(default=UserPerspective.CHRISTIAN_PROTESTANT, description="Perspective for preparation")
    opponent_perspective: Optional[str] = Field(default="islam", description="Opponent perspective")
    debate_locale: str = Field(default="id", description="Debate language")
    source_locale: Optional[str] = Field(default="el", description="Primary text source language (e.g., el, he, ar, la, en)")


class InterlinearWordToken(BaseModel):
    index: int                                      # Urutan kata dalam klausa (1, 2, 3...)
    strong_number: str                              # Kode Strong (misal: H5315, H2398, G3056)
    original_text: str                              # Aksara asli bervokal/cantillation (Ibrani/Yunani/Aramaik/Arab)
    transliteration: str                            # Ejaan fonetis akademis
    lemma: str                                      # Bentuk akar/kamus dasar (Root/Lemma)
    morphology_code: str                            # Kode tag morfologi resmi standar BibleHub (misal: Prep-b | N-fs, V-Qal-Imperf-3fs)
    morphology_expanded: str                        # Uraian parsing lengkap (Part of Speech, Stem/Binyan, Tense/Aspect, Person, Gender, Number, State/Case)
    literal_gloss: str                              # Terjemahan harfiah kata tersebut
    syntactic_role: str                             # Peran sintaksis dalam klausa (Subjek, Predikat, Objek, Konstruk, dll.)
    lexical_entry: Dict[str, str] = {}              # Definisi kamus standar: {"source": "BDB / HALOT / BDAG", "definition": "...", "semantic_range": "..."}
    exegetical_note: str = ""                       # Catatan signifikansi teologis/yuridis dari kata spesifik ini


class ExegeticalContext(BaseModel):
    literary_genre: str = ""                        # Genre sastra (misal: Hukum Yuridis Casuistic, Narasi Historis, Orakel Profetik, Epistola Didaktik)
    immediate_context: str = ""                     # Analisis perikop dekat (ayat-ayat sebelum & sesudah dalam pasal yang sama)
    historical_cultural_setting: str = ""           # Latar belakang historis / Sitz im Leben (kondisi penulis, audiens awal, dan polemik zaman itu)


class LinguisticExegesisPackage(BaseModel):
    passage_reference: str                          # Referensi Kitab, Pasal, dan Ayat utama
    original_language: str                          # "Biblical Hebrew" | "Koine Greek" | "Biblical Aramaic" | "Classical Arabic"
    source_text_full: str                           # Teks lengkap naskah kritis (BHS Codex Leningradensis / NA28 / UBS5)
    interlinear_tokens: List[InterlinearWordToken] = []
    literal_translation: str = ""                   # Rekonstruksi terjemahan kata-per-kata secara kaku sesuai sintaksis asli
    natural_translation: str = ""                   # Rekonstruksi terjemahan bahasa Indonesia yang mengalir dan akurat
    exegetical_context: Optional[ExegeticalContext] = None
    syntactic_exegesis: Dict[str, str] = {}         # Bedah struktur kalimat: Aspek Verba, klausa kondisional/hukum, pemakaian artikel definit, dll.
    manuscript_witnesses: List[Dict[str, str]] = [] # Perbandingan saksi naskah kuno (MT Leningradensis, LXX Septuaginta, DSS 4Q, Sinaiticus, Vaticanus) + status varian
    translation_comparison: List[Dict[str, str]] = [] # Audit terjemahan populer (TB LAI, KJV, ESV, NIV) vs Teks Asli (deteksi pergeseran makna/interpolasi)
    corpus_cross_references: List[Dict[str, str]] = [] # Konkordansi lintas-ayat: bagaimana kata/konsep kunci dipakai di ayat lain (Internal Kitab & Lintas-Kanon)
    exegetical_synthesis: str = ""                  # Kesimpulan akhir eksegesis historis-gramatikal secara objektif, akademis, dan komprehensif


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
    canonical_simulation: Optional[Dict[str, Any]] = None
    linguistic_exegesis: Optional[Any] = None
    is_demo: bool = True
    notice: str = "DEMO / MOCK DATA — Strictly for testing UI and structure"
    synthesis_status: str = ""
    retrieval_status: str = ""
    fallback_used: bool = False
    # Provenance fields — Recovery-015C. Fail-closed defaults to "unknown".
    provider: str = "unknown"
    provenance: str = "unknown"


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
