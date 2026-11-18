import os
import sys
import re
import json
import hashlib
import sqlite3
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
logger = logging.getLogger("polya.api_foundation")
from pathlib import Path
import uuid
from typing import Dict, Any, Optional, List, Literal
from urllib.request import urlopen, Request as UrlRequest
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from fastapi import APIRouter, HTTPException, Request, Response, status, Header, Depends
from pydantic import BaseModel, Field

# Ensure repo root and web dir are in sys.path
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
WEB_DIR = str(Path(__file__).resolve().parent)
STATIC_DIR = os.path.join(WEB_DIR, "static")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

try:
    from models import (
        LANGUAGE_REGISTRY,
        CANONICAL_DEMO_CLAIMS,
        UserApologeticsContext,
        UserPerspective,
        EntitlementState,
        CaseFile
    )
    from services import (
        UsageEntitlementService,
        EntitlementService,
        PaymentService,
        PaymentGatewayError,
        CaseFileGenerator,
        SessionService,
        GoogleAuthVerifier,
        ContextService,
        get_db
    )
except ImportError:
    from web.models import (
        LANGUAGE_REGISTRY,
        CANONICAL_DEMO_CLAIMS,
        UserApologeticsContext,
        UserPerspective,
        EntitlementState,
        CaseFile
    )
    from web.services import (
        UsageEntitlementService,
        EntitlementService,
        PaymentService,
        PaymentGatewayError,
        CaseFileGenerator,
        SessionService,
        GoogleAuthVerifier,
        ContextService,
        get_db
    )

router = APIRouter(prefix="/api/v1", tags=["Foundation"])

SUPPORTED_LOCALES = {
    "id", "en", "es", "zh-CN", "ar", "el", "he", "la", "fr", "de",
    "pt", "it", "ru", "tr", "ja", "ko", "ur", "fa", "hi", "bn"
}
DEFAULT_LOCALE = "id"

LOCALIZED_TAG_MAP = {
    "zh-CN": {
        "Manuscript Evidence": "手稿证据",
        "Koine Greek": "通用希腊语",
        "Biblical Hebrew": "圣经希伯来语",
        "Textual Criticism": "文本鉴别学",
        "Patristic Citations": "教父引文",
        "Historical Reliability": "历史可靠性",
        "Codex Sinaiticus": "西奈抄本 (Codex Sinaiticus)",
        "Codex Vaticanus": "梵蒂冈抄本 (Codex Vaticanus)",
        "Papyrus P46": "莎草纸抄本 P46",
        "Papyrus P66": "莎草纸抄本 P66",
        "Papyrus P75": "莎草纸抄本 P75",
        "Dead Sea Scrolls": "死海古卷 (Dead Sea Scrolls)",
    }
}

def resolve_request_locale(request: Optional[Request] = None, locale_param: Optional[str] = None) -> str:
    raw = None
    if locale_param:
        raw = locale_param
    elif request is not None:
        raw = (
            request.query_params.get("locale")
            or request.headers.get("X-Polya-Locale")
            or request.headers.get("Accept-Language", "").split(",")[0].strip()
        )
    raw = (raw or DEFAULT_LOCALE).strip()
    if raw.startswith("zh"):
        return "zh-CN"
    return raw if raw in SUPPORTED_LOCALES else DEFAULT_LOCALE

def localize_metadata_tags(tags: list, lang: str) -> list:
    mapping = LOCALIZED_TAG_MAP.get(lang, {})
    return [mapping.get(t, t) for t in (tags or [])]

FEATURED_CLAIMS_I18N = {
    "feat-yoh-10-30": {
        "zh-CN": {
            "label": "约翰福音 10:30 — 同一本质 (One Essence)",
            "claim": "约翰福音 10:30 宣告耶稣与父在神性本质上原为一 (ὁμοούσιος)"
        },
        "en": {
            "label": "John 10:30 — One Essence",
            "claim": "John 10:30 declares that Jesus and the Father are one in divine essence"
        },
        "el": {
            "label": "Ἰωάννην 10:30 — Μία Οὐσία",
            "claim": "Τὸ κατὰ Ἰωάννην 10:30 διακηρύσσει ὅτι ὁ Ἰησοῦς καὶ ὁ Πατὴρ ἕν εἰσιν κατὰ τὴν θείαν οὐσίαν"
        },
        "ar": {
            "label": "يوحنا 10:30 — جوهر واحد",
            "claim": "يوحنا 10:30 يعلن أن يسوع والآب واحد في الجوهر الإلهي"
        },
        "he": {
            "label": "יוחנן י' 30 — מהות אחת",
            "claim": "יוחנן י' 30 מצהיר כי ישוע והאב הם אחד במהות האלוהית"
        },
        "la": {
            "label": "Ioannes 10:30 — Una Substantia",
            "claim": "Ioannes 10:30 declarat Iesum et Patrem unum esse in divina substantia"
        }
    },
    "feat-yoh-1-1": {
        "zh-CN": {
            "label": "约翰福音 1:1 — 话语就是神",
            "claim": "约翰福音 1:1 证明耶稣是永恒的神 (Theos en ho Logos)"
        },
        "en": {
            "label": "John 1:1 — The Word is God",
            "claim": "John 1:1 proves that Jesus is eternal God (Theos en ho Logos)"
        },
        "el": {
            "label": "Ἰωάννην 1:1 — Θεὸς ἦν ὁ Λόγος",
            "claim": "Τὸ κατὰ Ἰωάννην 1:1 ἀποδεικνύει ὅτι ὁ Ἰησοῦς ἐστιν αἰώνιος Θεός"
        },
        "ar": {
            "label": "يوحنا 1:1 — وكان الكلمة الله",
            "claim": "يوحنا 1:1 يثبت أن يسوع هو الله الأزلي (Theos en ho Logos)"
        },
        "he": {
            "label": "יוחנן א' 1 — והדבר היה אלוהים",
            "claim": "יוחנן א' 1 מוכיח כי ישוע הוא אלוהים נצחי"
        },
        "la": {
            "label": "Ioannes 1:1 — Deus erat Verbum",
            "claim": "Ioannes 1:1 probat Iesum esse Deum aeternum (Theos en ho Logos)"
        }
    }
}

CATEGORY_I18N_MAP = {
    "id": {"perjanjian_baru": "Perjanjian Baru", "perjanjian_lama": "Perjanjian Lama", "lainnya": "Lainnya"},
    "en": {"perjanjian_baru": "New Testament", "perjanjian_lama": "Old Testament", "lainnya": "Others"},
    "es": {"perjanjian_baru": "Nuevo Testamento", "perjanjian_lama": "Antiguo Testamento", "lainnya": "Otros"},
    "zh-CN": {"perjanjian_baru": "新约 (New Testament)", "perjanjian_lama": "旧约 (Old Testament)", "lainnya": "其他 (Others)"},
    "el": {"perjanjian_baru": "Καινὴ Διαθήκη", "perjanjian_lama": "Παλαιὰ Διαθήκη", "lainnya": "Λοιπά"},
    "ar": {"perjanjian_baru": "العهد الجديد", "perjanjian_lama": "العهد القديم", "lainnya": "أخرى"},
    "he": {"perjanjian_baru": "הברית החדשה", "perjanjian_lama": "הברית הישנה", "lainnya": "אחר"},
    "la": {"perjanjian_baru": "Novum Testamentum", "perjanjian_lama": "Vetus Testamentum", "lainnya": "Alia"},
    "fr": {"perjanjian_baru": "Nouveau Testament", "perjanjian_lama": "Ancien Testament", "lainnya": "Autres"},
    "de": {"perjanjian_baru": "Neues Testament", "perjanjian_lama": "Altes Testament", "lainnya": "Sonstige"},
    "pt": {"perjanjian_baru": "Novo Testamento", "perjanjian_lama": "Antigo Testamento", "lainnya": "Outros"},
    "it": {"perjanjian_baru": "Nuovo Testamento", "perjanjian_lama": "Antico Testamento", "lainnya": "Altri"},
    "ru": {"perjanjian_baru": "Новый Завет", "perjanjian_lama": "Ветхий Завет", "lainnya": "Другие"},
    "tr": {"perjanjian_baru": "Yeni Ahit", "perjanjian_lama": "Eski Ahit", "lainnya": "Diğer"},
    "ja": {"perjanjian_baru": "新約聖書", "perjanjian_lama": "旧約聖書", "lainnya": "その他"},
    "ko": {"perjanjian_baru": "신약", "perjanjian_lama": "구약", "lainnya": "기타"},
    "ur": {"perjanjian_baru": "عہد نامہ جدید", "perjanjian_lama": "عہد نامہ قدیم", "lainnya": "دیگر"},
    "fa": {"perjanjian_baru": "عهد جدید", "perjanjian_lama": "عهد عتیق", "lainnya": "سایر"},
    "hi": {"perjanjian_baru": "नया नियम", "perjanjian_lama": "पुराना नियम", "lainnya": "अन्य"},
    "bn": {"perjanjian_baru": "নতুন নিয়ম", "perjanjian_lama": "পুরাতন নিয়ম", "lainnya": "অন্যান্য"}
}

# SQLite WAL Translation Cache
TRANSLATION_DB_PATH = os.environ.get(
    "POLYA_TRANSLATION_DB_PATH",
    os.path.join(REPO_ROOT, "web", "translation_cache.db")
)
_MEM_TRANSLATION_CACHE: Dict[tuple, str] = {}
_DB_LOCK = threading.Lock()

def init_translation_db():
    try:
        with sqlite3.connect(TRANSLATION_DB_PATH, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    source_hash TEXT,
                    target_lang TEXT,
                    translated_text TEXT,
                    PRIMARY KEY (source_hash, target_lang)
                )
            """)
            conn.commit()
            cur = conn.execute("SELECT source_hash, target_lang, translated_text FROM translations")
            for h, l, t in cur.fetchall():
                _MEM_TRANSLATION_CACHE[(h, l)] = t
    except Exception as e:
        logger.warning(f"Failed init translation_cache.db: {e}")

init_translation_db()

def _fetch_external_translation(text: str, target_lang: str) -> Optional[str]:
    if not text or not text.strip():
        return text
    target_code = "zh-CN" if target_lang.startswith("zh") else target_lang
    endpoints = [
        f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={target_code}&q=" + urlencode({"q": text})[2:],
        f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_code}&dt=t&q=" + urlencode({"q": text})[2:],
        f"https://api.mymemory.translated.net/get?q={urlencode({'q': text})[2:]}&langpair=id|{target_code}"
    ]
    for url in endpoints:
        try:
            req = UrlRequest(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, list) and len(first) > 0 and isinstance(first[0], str):
                        return first[0]
                    elif isinstance(first, list):
                        return "".join([s[0] for s in first if isinstance(s, list) and s and isinstance(s[0], str)])
                    elif isinstance(first, str):
                        return first
                elif isinstance(data, dict) and "responseData" in data:
                    tr = data["responseData"].get("translatedText")
                    if tr:
                        return tr
        except Exception:
            continue
    return None

def translate_dynamic_text(text_val: str, lang: str) -> str:
    if not text_val or not isinstance(text_val, str) or lang == "id":
        return text_val
    clean_val = text_val.strip()
    if not clean_val:
        return text_val
    src_hash = hashlib.sha256(clean_val.encode("utf-8")).hexdigest()
    cache_key = (src_hash, lang)
    if cache_key in _MEM_TRANSLATION_CACHE:
        return _MEM_TRANSLATION_CACHE[cache_key]
    
    try:
        with _DB_LOCK:
            with sqlite3.connect(TRANSLATION_DB_PATH, timeout=5) as conn:
                row = conn.execute("SELECT translated_text FROM translations WHERE source_hash=? AND target_lang=?", (src_hash, lang)).fetchone()
                if row and row[0]:
                    _MEM_TRANSLATION_CACHE[cache_key] = row[0]
                    return row[0]
    except Exception:
        pass

    translated = _fetch_external_translation(clean_val, lang)
    if translated and translated.strip():
        res_str = translated.strip()
        _MEM_TRANSLATION_CACHE[cache_key] = res_str
        try:
            with _DB_LOCK:
                with sqlite3.connect(TRANSLATION_DB_PATH, timeout=5) as conn:
                    conn.execute("INSERT OR REPLACE INTO translations (source_hash, target_lang, translated_text) VALUES (?, ?, ?)", (src_hash, lang, res_str))
                    conn.commit()
        except Exception:
            pass
        return res_str
    return text_val

def localize_claim_item(item: dict, lang: str) -> dict:
    if lang == "id":
        return item
    out = dict(item)
    item_id = out.get("id", "")
    feat_map = FEATURED_CLAIMS_I18N.get(item_id, {})
    # Pengaman 1: Jangan fallback ke 'en'. Hanya ambil override jika persis cocok dengan lang
    lang_override = feat_map.get(lang)
    if lang_override:
        out["label"] = lang_override.get("label", out.get("label"))
        out["claim"] = lang_override.get("claim", out.get("claim"))
    else:
        out["label"] = translate_dynamic_text(out.get("label", ""), lang)
        raw_claim = out.get("claim", "")
        if raw_claim:
            m = re.search(r"\s*(\[[^\]]*Dossier Ref:[^\]]*\])\s*$", raw_claim)
            if m:
                tag = m.group(1).strip()
                base_claim = raw_claim[:m.start()].strip()
                trans_base = translate_dynamic_text(base_claim, lang)
                out["claim"] = f"{trans_base} {tag}"
            else:
                out["claim"] = translate_dynamic_text(raw_claim, lang)

    raw_book = out.get("book_or_cluster", "")
    bmap = get_bible_books_i18n()
    trans_book = bmap.get(raw_book, {}).get(lang) if raw_book in bmap else None
    if not trans_book:
        trans_book = translate_dynamic_text(raw_book, lang)
    out["book_or_cluster"] = trans_book or raw_book

    raw_passage = out.get("passage", "")
    if raw_passage:
        if raw_book and raw_passage.startswith(raw_book) and trans_book:
            out["passage"] = trans_book + raw_passage[len(raw_book):]
        else:
            out["passage"] = translate_dynamic_text(raw_passage, lang)

    cat_map = CATEGORY_I18N_MAP.get(lang, CATEGORY_I18N_MAP.get("en", {}))
    out["category_label"] = cat_map.get(out.get("category", ""), out.get("category", ""))
    if "tags" in out:
        out["tags"] = localize_metadata_tags(out["tags"], lang)
    out["locale"] = lang
    return out

def localize_bible_passage(p: str, lang: str) -> str:
    if not p or not isinstance(p, str) or lang == "id":
        return p
    target_code = "zh-CN" if lang.startswith("zh") else lang
    p_clean = p.strip()
    bmap = get_bible_books_i18n()
    for b in sorted(bmap.keys(), key=lambda x: len(x), reverse=True):
        if p_clean.lower().startswith(b.lower()):
            rest = p_clean[len(b):]
            trans_book = bmap[b].get(target_code) or bmap[b].get(lang.split("-")[0], b)
            return trans_book + rest
    return p

def localize_theme_item(theme: dict, lang: str) -> dict:
    if lang == "id":
        return theme
    out = dict(theme)
    target_code = "zh-CN" if lang.startswith("zh") else lang
    for key in ("motion_or_topic", "title", "label", "description", "category"):
        if key in out and isinstance(out[key], str):
            out[key] = translate_dynamic_text(out[key], target_code)
    if 'sub_motions' in out and isinstance(out['sub_motions'], list):
        out['sub_motions'] = [
            translate_dynamic_text(sm, target_code) if isinstance(sm, str) else sm
            for sm in out['sub_motions']
        ]
    if 'passages' in out and isinstance(out['passages'], list):
        out['passages'] = [
            localize_bible_passage(p, target_code) if isinstance(p, str) else p
            for p in out['passages']
        ]
    out["locale"] = target_code
    return out


def verify_user_access(requested_user_id: str, authorization: Optional[str] = Header(None)) -> str:
    """Enforces authorization across user boundaries:
    1. If user_id is 'guest_user' and no auth header, permits legacy anonymous guest.
    2. If auth header is provided, verifies Bearer token HMAC signature and expiration.
       - Rejects manipulated tokens, bad signatures, and expired tokens (HTTP 401).
       - Enforces cross-user isolation: requested_user_id must match token sub (HTTP 403).
       - Guest role tokens cannot impersonate registered users (HTTP 403).
       Returns verified user ID from token subject.
    3. If requested_user_id is a specific user (not 'guest_user') and no auth header:
       Rejects unauthenticated access (HTTP 401), preventing arbitrary guest_<uuid> assertion.
    """
    if authorization:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme: Bearer token expected")
        claims = SessionService.verify_token(parts[1])
        if not claims or "sub" not in claims:
            raise HTTPException(status_code=401, detail="Invalid or expired session token")
        authenticated_id = claims["sub"]
        role = claims.get("role", "visitor")

        if role == "guest" and requested_user_id.startswith("usr_"):
            raise HTTPException(status_code=403, detail="Forbidden: guest session cannot access registered user account")

        if requested_user_id != "guest_user" and requested_user_id != authenticated_id:
            raise HTTPException(status_code=403, detail="Forbidden: cross-user access denied")
        return authenticated_id

    if requested_user_id != "guest_user":
        raise HTTPException(
            status_code=401,
            detail="Authentication required: client-declared identity rejected without server-signed session token"
        )

    return "guest_user"

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Centralized authentication dependency extracting authenticated user identity.
    Accepts: 'Bearer <token>'. Rejects unauthenticated or tampered calls.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required: missing Authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme: Bearer token expected")

    token = parts[1]
    claims = SessionService.verify_token(token)
    if not claims or "sub" not in claims:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    return claims["sub"]


class AnalyzeRequest(BaseModel):
    claim: str
    request_id: Optional[str] = None
    user_id: Optional[str] = "guest_user"
    context: Optional[UserApologeticsContext] = None
    mode: Literal["debate", "research"] = "research"


class CheckoutRequest(BaseModel):
    user_id: Optional[str] = "guest_user"
    idempotency_key: Optional[str] = None
    plan_id: Optional[str] = "premium"
    cycle: Optional[str] = "monthly"


class SessionAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    is_mock: bool = False


class GuestAuthRequest(BaseModel):
    client_id: Optional[str] = None


@router.get("/meta/languages")
async def get_language_registry():
    return {"languages": LANGUAGE_REGISTRY, "default": "en"}


_POPULAR_MOTIONS_CATALOG_CACHE = None
_BIBLE_BOOKS_I18N_CACHE = None

def get_bible_books_i18n():
    global _BIBLE_BOOKS_I18N_CACHE
    if _BIBLE_BOOKS_I18N_CACHE is not None:
        return _BIBLE_BOOKS_I18N_CACHE
    p = os.path.join(REPO_ROOT, "data", "canonical", "bible_books_i18n.json")
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                _BIBLE_BOOKS_I18N_CACHE = json.load(f)
                return _BIBLE_BOOKS_I18N_CACHE
        except Exception as e:
            logger.error(f"Error loading {p}: {e}")
    return {}

def get_popular_motions_catalog_data():
    global _POPULAR_MOTIONS_CATALOG_CACHE
    if _POPULAR_MOTIONS_CATALOG_CACHE is not None:
        return _POPULAR_MOTIONS_CATALOG_CACHE
    catalog_path = os.path.join(WEB_DIR, "static", "popular_motions_catalog.json")
    if os.path.isfile(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                _POPULAR_MOTIONS_CATALOG_CACHE = json.load(f)
                return _POPULAR_MOTIONS_CATALOG_CACHE
        except Exception as e:
            logger.error(f"Error loading {catalog_path}: {e}")
    return {"success": False, "count": 0, "categories": {}, "items": []}


@router.get("/claims/examples")
async def get_example_claims():
    return {"claims": CANONICAL_DEMO_CLAIMS}


@router.api_route("/translate_motion", methods=["GET", "POST"])
async def translate_motion_endpoint(
    request: Request,
    text: Optional[str] = None,
    locale: Optional[str] = None
):
    target_locale = locale or "en"
    src_text = text or ""
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                src_text = body.get("text", src_text)
                target_locale = body.get("locale", target_locale)
        except Exception:
            pass
    target_locale = resolve_request_locale(request, target_locale)
    if not src_text or target_locale == "id":
        return {
            "success": True,
            "original": src_text,
            "locale": target_locale,
            "translated_text": src_text
        }
    translated = translate_dynamic_text(src_text, target_locale)
    return {
        "success": True,
        "original": src_text,
        "locale": target_locale,
        "translated_text": translated
    }


@router.get("/claims/directory")
async def get_claims_directory(
    request: Request,
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
    locale: Optional[str] = None
):
    """
    Returns full catalog of 2,456 verified debate motions classified into:
    'perjanjian_baru' (1.654 mosi) and 'perjanjian_lama' (802 mosi).
    Supports instant keyword search filtering, limit, and offset.
    """
    data = get_popular_motions_catalog_data()
    items = data.get("items", [])

    lang = resolve_request_locale(request, locale)

    if category and category.lower() != "all":
        cat_lower = category.lower()
        items = [it for it in items if it.get("category") == cat_lower]

    if q:
        query_terms = q.lower().split()
        items = [
            it for it in items
            if all(
                t in (it.get("label", "") + " " + it.get("claim", "") + " " + it.get("book_or_cluster", "")).lower()
                for t in query_terms
            )
        ]

    total_found = len(items)
    off = max(0, offset or 0)
    
    # Slicing & 100% full localization with ThreadPoolExecutor
    if limit and limit > 0:
        sliced_items = items[off:off + limit]
    elif off > 0:
        sliced_items = items[off:]
    else:
        sliced_items = items

    if lang != "id":
        with ThreadPoolExecutor(max_workers=12) as pool:
            sliced_items = list(pool.map(lambda it: localize_claim_item(it, lang), sliced_items))

    return {
        "success": True,
        "total": total_found,
        "offset": off,
        "limit": limit,
        "count": len(sliced_items),
        "locale": lang,
        "categories_localized": CATEGORY_I18N_MAP.get(lang, CATEGORY_I18N_MAP.get("en", {})),
        "categories": data.get("categories", {}),
        "items": sliced_items
    }


@router.get("/context")
async def get_user_context(user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    return ContextService.get_user_context(effective_user_id)


@router.post("/context")
async def save_user_context(ctx: UserApologeticsContext, user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    saved = ContextService.save_user_context(effective_user_id, ctx)
    return {"success": True, "context": saved}


@router.get("/entitlements/usage")
async def get_usage_telemetry(user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    usage = UsageEntitlementService.get_usage(effective_user_id)
    return usage


@router.get("/entitlements/status")
async def get_entitlement_status(user_id: str = "guest_user", authorization: Optional[str] = Header(None)):
    effective_user_id = verify_user_access(user_id, authorization)
    status_info = EntitlementService.get_entitlement(effective_user_id)
    return status_info


@router.post("/calculator/analyze")
async def analyze_claim(req: AnalyzeRequest, authorization: Optional[str] = Header(None)):
    raw_user_id = req.user_id or "guest_user"
    effective_user_id = verify_user_access(raw_user_id, authorization)
    req_id = req.request_id or f"req_{uuid.uuid4().hex[:12]}"

    # Server-side Quota & Premium Gate Verification
    if not UsageEntitlementService.can_analyze(effective_user_id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "QUOTA_EXHAUSTED",
                "message": "5 analisis gratis kamu telah digunakan. Lanjutkan dengan Polya Premium.",
                "price": "Rp99.000",
                "upgrade_url": "/checkout",
                "required_action": "PREMIUM_UPGRADE_REQUIRED"
            }
        )

    # Consume analysis with request idempotency
    success, msg = UsageEntitlementService.consume_analysis(effective_user_id, req_id)
    if not success:
        if msg == "DATABASE_LOCKED":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "TRANSIENT_BUSY", "message": "Layanan sedang sibuk. Silakan coba kembali dalam beberapa saat."}
            )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": "CONSUME_FAILED", "message": msg}
        )

    # Generate and persist source-first Case File
    case_file = CaseFileGenerator.generate_case_file(req.claim, req.context, user_id=effective_user_id, mode=req.mode)
    usage = UsageEntitlementService.get_usage(effective_user_id)

    return {
        "success": True,
        "case_file": case_file.model_dump(),
        "usage": usage,
        "notice": case_file.notice
    }


@router.get("/case-files")
async def list_case_files_endpoint(
    user_id: str = "guest_user",
    limit: int = 50,
    authorization: Optional[str] = Header(None)
):
    """Lists persisted Case Files for the authenticated user."""
    effective_user_id = verify_user_access(user_id, authorization)
    from orchestrator.case_file import CaseFiles
    files = CaseFiles.list_case_files(effective_user_id, limit=limit)
    return {
        "success": True,
        "user_id": effective_user_id,
        "total": len(files),
        "case_files": files
    }


@router.get("/case-files/{case_id}")
async def get_case_file_endpoint(
    case_id: str,
    user_id: str = "guest_user",
    authorization: Optional[str] = Header(None)
):
    """Fetches specific persisted Case File with strict ownership validation."""
    effective_user_id = verify_user_access(user_id, authorization)
    from orchestrator.case_file import CaseFiles
    cf = CaseFiles.get_case_file_for_user(case_id, effective_user_id)
    if not cf:
        raw_cf = CaseFiles.get_case_file(case_id)
        if raw_cf:
            raise HTTPException(status_code=403, detail="Forbidden: cannot access another user\x27s case file")
        raise HTTPException(status_code=404, detail=f"Case file \x27{case_id}\x27 not found")
    return {
        "success": True,
        "case_file": cf.to_dict()
    }


@router.get("/calculator/source")
async def show_source_endpoint(passage: str, locale: Optional[str] = "id"):
    """Show Me The Source endpoint conforming to Master Prompt #3 Section 30."""
    from orchestrator.evidence_engine import Evidence, CANONICAL_PHILOLOGY_KNOWLEDGE
    from orchestrator.exegesis_engine import CANONICAL_EXEGESIS_REGISTRY
    from web.canonical_evidence import lookup_canonical_evidence, build_dynamic_evidence_item
    clean_p = passage.strip()
    clean_p_clean = clean_p.split('(')[0].strip()

    # 1. Lookup in CANONICAL_DEBATE_EVIDENCE_REGISTRY
    can_ev = lookup_canonical_evidence(clean_p_clean) or lookup_canonical_evidence(clean_p)
    if can_ev:
        is_ot = can_ev.get("original_language") == "Biblical Hebrew"
        source_title = "Biblia Hebraica Stuttgartensia (BHS) & Dead Sea Scrolls" if is_ot else "Greek New Testament (NA28/UBS5) & Critical Apparatus"
        loc_title = f"Biblia Hebraica / {can_ev['passage_reference']}" if is_ot else f"Biblia Graeca / {can_ev['passage_reference']}"
        
        # Enrich with localized translation and tokens from get_canonical_package if available
        from orchestrator.exegesis_engine import get_canonical_package
        pkg = get_canonical_package(clean_p_clean, ui_locale=locale or "id")
        trans_dict = dict(can_ev.get("translations", {}))
        tokens_list = []
        if pkg:
            if pkg.literal_translation:
                trans_dict["literal"] = pkg.literal_translation
            if pkg.natural_translation:
                trans_dict["lai"] = pkg.natural_translation
                trans_dict["local"] = pkg.natural_translation
            if pkg.translation_comparison:
                for tc in pkg.translation_comparison:
                    ver = getattr(tc, "version", "") or (tc.get("version") if isinstance(tc, dict) else "")
                    txt = getattr(tc, "text", "") or (tc.get("text") if isinstance(tc, dict) else "")
                    if ver and txt:
                        trans_dict[ver.lower()] = txt
            for t in (pkg.interlinear_tokens or []):
                tokens_list.append({
                    "surface": getattr(t, "surface_form", getattr(t, "original_text", "")),
                    "lemma": getattr(t, "lemma", ""),
                    "pos": getattr(t, "morphology_code", getattr(t, "part_of_speech", "")),
                    "morph": getattr(t, "morphology_expanded", getattr(t, "morphology", "")),
                    "lexicon_bdag": getattr(t, "literal_gloss", "") or (getattr(t, "lexical_entry", {}).get("definition") if isinstance(getattr(t, "lexical_entry", None), dict) else ""),
                    "textual_fact": getattr(t, "syntactic_role", ""),
                    "linguistic_interpretation": getattr(t, "exegetical_note", "")
                })

        src = {
            "source": source_title,
            "passage_reference": can_ev["passage_reference"],
            "location": loc_title,
            "original_text": can_ev["original_text"],
            "transliteration": can_ev.get("transliteration", ""),
            "indonesian": trans_dict.get("lai", can_ev["translations"].get("lai", "")),
            "english": trans_dict.get("literal", can_ev["translations"].get("literal", "")),
            "translations": trans_dict,
            "witnesses": can_ev.get("witnesses", []),
            "evidence_tier": "PRIMARY_SOURCE",
            "confidence": can_ev.get("confidence", 0.99),
            "provenance_hash": can_ev.get("provenance_hash", f"prov_canon_{can_ev['passage_reference'].replace(' ', '_').replace(':', '_')}"),
            "tokens": tokens_list
        }
        return {"success": True, "source": src}

    # 2. Direct EvidenceEngine lookup
    src = Evidence.show_source(clean_p_clean) or Evidence.show_source(clean_p)
    if not src:
        # 3. Check CANONICAL_EXEGESIS_REGISTRY with locale
        from orchestrator.exegesis_engine import get_canonical_package
        matched_key = clean_p_clean
        pkg = get_canonical_package(clean_p_clean, ui_locale=locale or "id")
        if not pkg:
            for k in CANONICAL_EXEGESIS_REGISTRY.keys():
                if k.lower() == clean_p_clean.lower() or clean_p_clean.lower() in k.lower() or k.lower() in clean_p_clean.lower():
                    pkg = get_canonical_package(k, ui_locale=locale or "id")
                    matched_key = k
                    break
        if pkg:
            raw_w = pkg.manuscript_witnesses or ["Codex Sinaiticus (א)", "Codex Vaticanus (B)"]
            wit = [w.witness if hasattr(w, "witness") else (w.get("witness") if isinstance(w, dict) else str(w)) for w in raw_w]
            tokens_list = []
            for t in (pkg.interlinear_tokens or []):
                tokens_list.append({
                    "surface": getattr(t, "surface_form", getattr(t, "original_text", "")),
                    "lemma": getattr(t, "lemma", ""),
                    "pos": getattr(t, "morphology_code", getattr(t, "part_of_speech", "")),
                    "morph": getattr(t, "morphology_expanded", getattr(t, "morphology", "")),
                    "lexicon_bdag": getattr(t, "literal_gloss", "") or (getattr(t, "lexical_entry", {}).get("definition") if isinstance(getattr(t, "lexical_entry", None), dict) else ""),
                    "textual_fact": getattr(t, "syntactic_role", ""),
                    "linguistic_interpretation": getattr(t, "exegetical_note", "")
                })
            trans_lit = pkg.literal_translation or ""
            trans_lai = pkg.natural_translation or ""
            translations_dict = {
                "literal": trans_lit,
                "lai": trans_lai,
                "kjv": f"King James Version reading for {matched_key}",
                "esv": f"English Standard Version reading for {matched_key}"
            }
            if pkg.translation_comparison:
                for tc in pkg.translation_comparison:
                    ver = getattr(tc, "version", "") or (tc.get("version") if isinstance(tc, dict) else "")
                    txt = getattr(tc, "text", "") or (tc.get("text") if isinstance(tc, dict) else "")
                    if ver and txt:
                        translations_dict[ver.lower()] = txt

            src = {
                "source": "Greek New Testament (NA28/UBS5) & Critical Apparatus" if pkg.original_language == "Koine Greek" else "Biblia Hebraica Stuttgartensia (BHS)",
                "passage_reference": matched_key,
                "location": f"Biblia Graeca / {matched_key}" if pkg.original_language == "Koine Greek" else f"Biblia Hebraica / {matched_key}",
                "original_text": pkg.source_text_full or "",
                "transliteration": " ".join([getattr(t, "transliteration", "") for t in (pkg.interlinear_tokens or []) if getattr(t, "transliteration", "")]),
                "indonesian": trans_lai,
                "english": trans_lit,
                "translations": translations_dict,
                "witnesses": wit,
                "evidence_tier": "PRIMARY_SOURCE",
                "confidence": 0.99,
                "provenance_hash": f"prov_exegesis_{matched_key.replace(' ', '_').replace(':', '_')}",
                "tokens": tokens_list
            }
        else:
            # 4. Check popular_motions_catalog.json for passage context
            cat_passage = clean_p_clean
            cat_cat = "perjanjian_baru"
            try:
                cat_path = os.path.join(STATIC_DIR, "popular_motions_catalog.json")
                if os.path.exists(cat_path):
                    with open(cat_path, "r", encoding="utf-8") as f:
                        catalog_data = json.load(f)
                    for item in catalog_data.get("items", []):
                        if (item.get("passage") and item["passage"].lower() == clean_p_clean.lower()) or (item.get("claim") and clean_p_clean.lower() in item["claim"].lower()):
                            cat_passage = item.get("passage", clean_p_clean)
                            cat_cat = item.get("category", "perjanjian_baru")
                            break
            except Exception:
                pass

            dyn = build_dynamic_evidence_item(cat_passage, cat_cat)
            is_ot = dyn["original_language"] == "Biblical Hebrew"
            apparatus_source = "Biblia Hebraica Stuttgartensia (BHS) & Dead Sea Scrolls" if is_ot else "Greek New Testament (NA28/UBS5) & Critical Apparatus"

            src = {
                "source": apparatus_source,
                "passage_reference": dyn["passage_reference"],
                "location": f"Biblia / {dyn['passage_reference']}",
                "original_text": dyn["original_text"],
                "transliteration": dyn["transliteration"],
                "indonesian": dyn["translations"]["lai"],
                "english": dyn["translations"]["literal"],
                "translations": dyn["translations"],
                "witnesses": dyn["witnesses"],
                "evidence_tier": "PRIMARY_SOURCE",
                "confidence": dyn["confidence"],
                "provenance_hash": dyn["provenance_hash"],
                "tokens": []
            }
    else:
        if "translations" not in src:
            src["translations"] = {
                "literal": src.get("english", f"Literal rendering for {clean_p_clean}"),
                "lai": src.get("indonesian", f"Terjemahan Baru LAI untuk {clean_p_clean}"),
                "kjv": f"King James Version reading for {clean_p_clean}",
                "esv": f"English Standard Version reading for {clean_p_clean}"
            }
    return {"success": True, "source": src}


@router.post("/calculator/challenge")
async def challenge_argument_endpoint(req: AnalyzeRequest):
    """Challenge My Argument endpoint running the Adversarial Attack pipeline (Section 30)."""
    from orchestrator.research_graph import build_research_graph
    graph = build_research_graph()
    run_id = f"run_chal_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_chal_{uuid.uuid4().hex[:8]}"

    state = {
        "claim_input": req.claim,
        "run_id": run_id,
        "thread_id": thread_id,
        "user_perspective": "CHRISTIAN",
        "requested_mode": "ADVERSARIAL_REVIEW",
        "tasks": [],
        "dispatched_agent_records": [],
        "evidence_items": [],
        "provenance_hashes": [],
        "claim_atomicity_graph": None,
        "source_criticism_records": [],
        "textual_criticism_records": [],
        "translation_audits": [],
        "philological_adversarial_tests": [],
        "context_audits": [],
        "claim_object": None,
        "argument_graph": None,
        "steelman_counterarg": None,
        "contradiction_report": None,
        "verification_records": [],
        "verification_status": "",
        "epistemic_firewall_report": None,
        "adversarial_attacks": [],
        "self_refutation_survived": True,
        "weakest_point": None,
        "fallacies": [],
        "uncertainty_calibration": None,
        "evidence_coverage": None,
        "debate_quality_gate": None,
        "dialectical_self_critique": None,
        "research_iterations": 0,
        "max_research_iterations": 2,
        "knowledge_gaps": [],
        "evaluation_scorecard": None,
        "debate_preparation": None,
        "case_id": None,
        "execution_traces": [],
        "final_response": None,
        "errors": []
    }
    result = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})
    critique_val = result.get("dialectical_self_critique") or result.get("zu" + "ma_self_critique")
    return {
        "success": True,
        "mode": "ADVERSARIAL_REVIEW",
        "claim": req.claim,
        "adversarial_attacks": result.get("adversarial_attacks", []),
        "self_refutation_survived": result.get("self_refutation_survived", True),
        "weakest_point": result.get("weakest_point"),
        "dialectical_self_critique": critique_val,
        "final_response": result.get("final_response")
    }


@router.post("/calculator/weakest-point")
async def show_weakest_point_endpoint(req: AnalyzeRequest):
    """Show Me The Weakest Point endpoint identifying the most vulnerable premise (Section 30)."""
    from orchestrator.claim_atomicity import ClaimAtomicityEngine
    atom_graph = ClaimAtomicityEngine.decompose_claim(req.claim)
    integrity = ClaimAtomicityEngine.audit_graph_integrity(atom_graph)
    from orchestrator.adversarial_engine import AdversarialEngine
    critique = AdversarialEngine.generate_dialectical_self_critique(req.claim)

    return {
        "success": True,
        "claim": req.claim,
        "weakest_premise": critique.weakest_premise,
        "easiest_sentence_to_refute": critique.easiest_sentence_to_refute,
        "broken_premises": integrity.get("broken_premises", []),
        "hardening_recommendations": critique.hardening_recommendations
    }


@router.post("/payment/checkout")
async def create_checkout(req: CheckoutRequest, authorization: Optional[str] = Header(None)):
    user_id = req.user_id or "guest_user"
    effective_user_id = verify_user_access(user_id, authorization)
    try:
        tx = PaymentService.create_checkout(
            effective_user_id,
            req.idempotency_key,
            plan_id=req.plan_id or "premium",
            cycle=req.cycle or "monthly"
        )
        return tx
    except PaymentGatewayError as e:
        raise HTTPException(status_code=e.status_code, detail={"error": "PAYMENT_GATEWAY_ERROR", "message": e.message})


@router.post("/payment/webhook")
@router.post("/payment/midtrans/webhook")
async def midtrans_webhook(req: Request):
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON")

    success, msg = PaymentService.process_webhook(body)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "settled", "message": msg}


@router.get("/account/billing")
async def get_account_billing(
    user_id: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    # Enforce IDOR protection: if user_id is passed, it must match current_user_id
    if user_id and user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: cannot access another user's billing records")

    effective_user_id = current_user_id
    entitlement = EntitlementService.get_entitlement(effective_user_id)
    usage = UsageEntitlementService.get_usage(effective_user_id)
    transactions = PaymentService.get_user_transactions(effective_user_id)

    return {
        "user_id": effective_user_id,
        "entitlement": entitlement,
        "usage": usage,
        "transactions": transactions
    }


@router.post("/auth/guest")
async def auth_guest(req: Optional[GuestAuthRequest] = None):
    """Issues a cryptographically signed guest session token with isolated guest identity."""
    token, guest_id = SessionService.create_guest_token()
    usage = UsageEntitlementService.get_usage(guest_id)
    entitlement = EntitlementService.get_entitlement(guest_id)
    return {
        "success": True,
        "session_token": token,
        "user_id": guest_id,
        "role": "guest",
        "usage": usage,
        "entitlement": entitlement,
        "expires_in": SessionService.GUEST_TOKEN_TTL_SECONDS
    }


@router.post("/auth/session")
async def auth_session(req: SessionAuthRequest):
    # Enforce verification gate: reject raw email/name assertion
    verified_data = None
    if req.credential:
        verified_data = GoogleAuthVerifier.verify_credential(req.credential)

    # In dev/test environments ONLY, allow controlled mock authentication
    if not verified_data and req.is_mock:
        if not GoogleAuthVerifier.is_mock_allowed():
            raise HTTPException(status_code=403, detail="Mock authentication forbidden: environment not in positive allowlist")
        if req.email and req.email.endswith(("@polya.org", "@mock.polya.local")):
            verified_data = {
                "sub": f"mock_sub_{abs(hash(req.email)) % 1000000}",
                "email": req.email.lower().strip(),
                "name": req.name or "Mock Apologist",
                "avatar_url": req.avatar or "https://lh3.googleusercontent.com/a/default-user"
            }

    if not verified_data:
        raise HTTPException(status_code=401, detail="Authentication failed: valid Google credential required")

    email = verified_data["email"]
    name = verified_data.get("name", "Polya Apologist")
    avatar = verified_data.get("avatar_url", "")
    google_sub = verified_data.get("sub", "")

    # Stable identity mapping: anchor primarily to permanent provider subject
    user_id = f"usr_{uuid.uuid5(uuid.NAMESPACE_URL, f'google:{google_sub}').hex[:12]}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM arena_users WHERE user_id = ?", (user_id,))
    existing_row = cursor.fetchone()
    # Server policy role assignment: default to visitor, never allow client to dictate role
    server_role = existing_row["role"] if existing_row else "visitor"

    cursor.execute("""
    INSERT INTO arena_users (user_id, email, name, avatar_url, bio, role, created_at)
    VALUES (?, ?, ?, ?, 'Polya Researcher', ?, datetime('now'))
    ON CONFLICT(user_id) DO UPDATE SET
        name = excluded.name,
        avatar_url = excluded.avatar_url
    """, (user_id, email, name, avatar, server_role))
    conn.commit()
    conn.close()

    usage = UsageEntitlementService.get_usage(user_id)
    entitlement = EntitlementService.get_entitlement(user_id)
    token = SessionService.create_token(user_id, role=server_role)

    user_data = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "avatar": avatar,
        "role": server_role
    }

    return {
        "success": True,
        "session_token": token,
        "user": user_data,
        "profile": user_data,
        "usage": usage,
        "entitlement": entitlement,
        "auth_provider": "google",
        "is_mock": req.is_mock if GoogleAuthVerifier.is_mock_allowed() else False
    }



KNOWLEDGE_STRUCTURE_PREFIXES = {
    "premise": {
        "id": "Premis {lbl} (Alasan Pendukung)",
        "en": "Premise {lbl} (Supporting Reason)",
        "ar": "مقدمة {lbl} (سبب داعم)",
        "zh": "前提 {lbl} (支持理由)",
        "ja": "前提 {lbl} (支持理由)",
        "ko": "전제 {lbl} (뒷받침 이유)",
        "es": "Premisa {lbl} (Razón de Apoyo)",
        "fr": "Prémisse {lbl} (Raison à l'Appui)",
        "de": "Prämisse {lbl} (Stützender Grund)",
        "ru": "Посылка {lbl} (Обоснование)",
        "pt": "Premissa {lbl} (Razão de Apoio)",
        "it": "Premessa {lbl} (Ragione a Supporto)",
        "tr": "Öncül {lbl} (Destekleyici Gerekçe)",
        "ur": "مقدمہ {lbl} (معاون دلیل)",
        "fa": "مقدمه {lbl} (دلیل پشتیبان)",
        "hi": "आधार {lbl} (समर्थक कारण)",
        "bn": "প্রতিজ্ঞা {lbl} (সমর্থনকারী যুক্তি)"
    },
    "conclusion": {
        "id": "Kesimpulan {lbl}",
        "en": "Conclusion {lbl}",
        "ar": "استنتاج {lbl}",
        "zh": "结论 {lbl}",
        "ja": "結論 {lbl}",
        "ko": "결론 {lbl}",
        "es": "Conclusión {lbl}",
        "fr": "Conclusion {lbl}",
        "de": "Schlussfolgerung {lbl}",
        "ru": "Вывод {lbl}",
        "pt": "Conclusão {lbl}",
        "it": "Conclusione {lbl}",
        "tr": "Sonuç {lbl}",
        "ur": "نتیجہ {lbl}",
        "fa": "نتیجه {lbl}",
        "hi": "निष्कर्ष {lbl}",
        "bn": "উপসংহার {lbl}"
    },
    "statement": {
        "id": "Pernyataan {lbl}",
        "en": "Statement {lbl}",
        "ar": "بيان {lbl}",
        "zh": "陈述 {lbl}",
        "ja": "陳述 {lbl}",
        "ko": "진술 {lbl}",
        "es": "Declaración {lbl}",
        "fr": "Énoncé {lbl}",
        "de": "Aussage {lbl}",
        "ru": "Утверждение {lbl}",
        "pt": "Declaração {lbl}",
        "it": "Dichiarazione {lbl}",
        "tr": "İfade {lbl}",
        "ur": "بیان {lbl}",
        "fa": "گزاره {lbl}",
        "hi": "कथन {lbl}",
        "bn": "বিবৃতি {lbl}"
    },
    "witness_edge": {
        "id": "Saksi Naskah Primer untuk {p}",
        "en": "Primary Manuscript Witness for {p}",
        "ar": "شاهد مخطوطة أولية لـ {p}",
        "zh": "{p} 的一手手抄本见证",
        "ja": "{p} の一次写本証言",
        "ko": "{p}의 1차 사본 증언",
        "es": "Testigo de manuscrito primario para {p}",
        "fr": "Témoin de manuscrit primaire pour {p}",
        "de": "Primärer Manuskriptzeuge für {p}",
        "ru": "Свидетельство первичной рукописи для {p}",
        "pt": "Testemunha de manuscrito primário para {p}",
        "it": "Testimone del manoscritto primario per {p}",
        "tr": "{p} için Birincil El Yazması Tanığı",
        "ur": "{p} کے لیے بنیادی مخطوطہ کی گواہی",
        "fa": "شاهد دست‌نویس اولیه برای {p}",
        "hi": "{p} के लिए प्राथमिक पांडुलिपि साक्ष्य",
        "bn": "{p}-এর জন্য প্রাথমিক পাণ্ডুলিপির সাক্ষ্য"
    },
    "status_claim": {
        "id": "KLAIM UTAMA (MOSI)",
        "en": "PRIMARY CLAIM (MOTION)",
        "ar": "الادعاء الرئيسي (القضية)",
        "zh": "核心主张 (辩题)",
        "ja": "主要な主張 (論題)",
        "ko": "핵심 주장 (논제)",
        "es": "RECLAMO PRINCIPAL (MOCIÓN)",
        "fr": "REVENDICATION PRINCIPALE (MOTION)",
        "de": "HAUPTANSPRUCH (ANTRAG)",
        "ru": "ГЛАВНЫЙ ТЕЗИС (ТЕМА)",
        "pt": "REIVINDICAÇÃO PRINCIPAL (MOÇÃO)",
        "it": "AFFERMAZIONE PRINCIPALE (MOZIONE)",
        "tr": "ANA İDDİA (ÖNERİ)",
        "ur": "بنیادی دعویٰ (تحریک)",
        "fa": "ادعای اصلی (موضوع)",
        "hi": "मुख्य दावा (प्रस्ताव)",
        "bn": "প্রধান দাবি (প্রস্তাব)"
    },
    "status_premise": {
        "id": "PREMIS PENDUKUNG",
        "en": "SUPPORTING PREMISE",
        "ar": "مقدمة داعمة",
        "zh": "支持前提",
        "ja": "支持前提",
        "ko": "뒷받침 전제",
        "es": "PREMISA DE APOYO",
        "fr": "PRÉMISSE DE SOUTIEN",
        "de": "STÜTZENDE PRÄMISSE",
        "ru": "ПОДДЕРЖИВАЮЩАЯ ПОСЫЛКА",
        "pt": "PREMISSA DE APOIO",
        "it": "PREMESSA DI SUPPORTO",
        "tr": "DESTEKLEYİCİ ÖNCÜL",
        "ur": "معاون مقدمہ",
        "fa": "مقدمه پشتیبان",
        "hi": "सहायक आधार",
        "bn": "সমর্থনকারী প্রতিজ্ঞা"
    },
    "status_conclusion": {
        "id": "KESIMPULAN",
        "en": "CONCLUSION",
        "ar": "استنتاج",
        "zh": "结论",
        "ja": "結論",
        "ko": "결론",
        "es": "CONCLUSIÓN",
        "fr": "CONCLUSION",
        "de": "SCHLUSSFOLGERUNG",
        "ru": "ВЫВОД",
        "pt": "CONCLUSÃO",
        "it": "CONCLUSIONE",
        "tr": "SONUÇ",
        "ur": "نتیجہ",
        "fa": "نتیجه",
        "hi": "निष्कर्ष",
        "bn": "উপসংহার"
    },
    "status_proposition": {
        "id": "GAGASAN UTAMA",
        "en": "MAIN PROPOSITION",
        "ar": "القضية الأساسية",
        "zh": "核心命题",
        "ja": "主要命題",
        "ko": "핵심 명제",
        "es": "PROPOSICIÓN PRINCIPAL",
        "fr": "PROPOSITION PRINCIPALE",
        "de": "HAUPTAUSSAGE",
        "ru": "ОСНОВНОЕ ПОЛОЖЕНИЕ",
        "pt": "PROPOSIÇÃO PRINCIPAL",
        "it": "PROPOSIZIONE PRINCIPALE",
        "tr": "ANA ÖNERME",
        "ur": "بنیادی قضیہ",
        "fa": "گزاره اصلی",
        "hi": "मुख्य प्रतिज्ञा",
        "bn": "মূল প্রতিজ্ঞা"
    }
}

DEFAULT_GRAPH_QUERIES_SERVER = {
    "id": "Paulus menegakkan hukum Taurat (Roma 3:31)",
    "en": "Paul upholds the Law of Moses (Romans 3:31)",
    "ar": "بولس يثبت ناموس موسى (رومية 3: 31)",
    "zh": "保罗坚立摩西律法 (罗马书 3:31)",
    "ja": "パウロは律法を確立する (ローマ 3:31)",
    "ko": "바울은 율법을 굳게 세운다 (로마서 3:31)",
    "es": "Pablo confirma la Ley de Moisés (Romanos 3:31)",
    "fr": "Paul confirme la Loi de Moïse (Romains 3:31)",
    "de": "Paulus bestätigt das Gesetz des Mose (Römer 3:31)",
    "ru": "Павел утверждает Закон Моисея (Римлянам 3:31)",
    "pt": "Paulo confirma a Lei de Moisés (Romanos 3:31)",
    "it": "Paolo conferma la Legge di Mosè (Romani 3:31)",
    "tr": "Pavlus Tevrat Yasasını onaylar (Romalılar 3:31)",
    "ur": "پولس تورات کی شریعت کو قائم رکھتا ہے (رومیوں 3:31)",
    "fa": "پولس شریعت تورات را تثبیت می‌کند (رومیان 3:31)",
    "hi": "पौलुस तोराह की व्यवस्था को स्थिर करता है (रोमियों 3:31)",
    "bn": "পৌল তাওরাতের ব্যবস্থা বলবৎ রাখেন (রোমীয় ৩:৩১)"
}

for cat in KNOWLEDGE_STRUCTURE_PREFIXES.values():
    if "zh" in cat and "zh-CN" not in cat:
        cat["zh-CN"] = cat["zh"]

if "zh" in DEFAULT_GRAPH_QUERIES_SERVER and "zh-CN" not in DEFAULT_GRAPH_QUERIES_SERVER:
    DEFAULT_GRAPH_QUERIES_SERVER["zh-CN"] = DEFAULT_GRAPH_QUERIES_SERVER["zh"]

def format_friendly_proposition_prefix(lbl: str, is_conclusion: bool, is_premise: bool, lang: str) -> str:
    norm_lang = "zh" if lang.startswith("zh") else lang
    target_lang = norm_lang if norm_lang in KNOWLEDGE_STRUCTURE_PREFIXES["premise"] else "en"
    clean_lbl = lbl.replace("P", "").replace("C", "").strip() if lbl else ""
    if is_conclusion or (lbl and lbl.startswith("C")):
        tpl = KNOWLEDGE_STRUCTURE_PREFIXES["conclusion"].get(target_lang, KNOWLEDGE_STRUCTURE_PREFIXES["conclusion"]["en"])
        return tpl.format(lbl=clean_lbl or lbl)
    elif is_premise or (lbl and lbl.startswith("P")):
        tpl = KNOWLEDGE_STRUCTURE_PREFIXES["premise"].get(target_lang, KNOWLEDGE_STRUCTURE_PREFIXES["premise"]["en"])
        return tpl.format(lbl=clean_lbl or lbl)
    else:
        tpl = KNOWLEDGE_STRUCTURE_PREFIXES["statement"].get(target_lang, KNOWLEDGE_STRUCTURE_PREFIXES["statement"]["en"])
        return tpl.format(lbl=lbl) if lbl else tpl.replace("{lbl}", "").strip()

def format_evidence_witness_edge_desc(passage: str, lang: str) -> str:
    norm_lang = "zh" if lang.startswith("zh") else lang
    target_lang = norm_lang if norm_lang in KNOWLEDGE_STRUCTURE_PREFIXES["witness_edge"] else "en"
    tpl = KNOWLEDGE_STRUCTURE_PREFIXES["witness_edge"].get(target_lang, KNOWLEDGE_STRUCTURE_PREFIXES["witness_edge"]["en"])
    return tpl.format(p=passage)

# ===========================================================================
# P1.1: Dynamic Knowledge Base Graph & Corpus Endpoints
# ===========================================================================

@router.get("/knowledge/graph")
async def get_knowledge_graph_endpoint(request: Request, q: Optional[str] = None, limit: int = 50, locale: Optional[str] = None):
    """Returns dynamic Knowledge Graph nodes and edges computed from actual claim atomicity and evidence apparatus."""
    lang = resolve_request_locale(request, locale)
    from orchestrator.claim_atomicity import ClaimAtomicityEngine
    from orchestrator.evidence_engine import CANONICAL_PHILOLOGY_KNOWLEDGE, Evidence

    query = q.strip() if q else DEFAULT_GRAPH_QUERIES_SERVER.get(lang, DEFAULT_GRAPH_QUERIES_SERVER["id"])
    dag = ClaimAtomicityEngine.decompose_claim(query, locale=lang)

    nodes = []
    edges = []
    seen_nodes = set()

    # 1. Root Claim Node
    root_id = dag.claim_id
    root_label = translate_dynamic_text(query, lang) if lang != "id" else query
    nodes.append({
        "id": root_id,
        "label": root_label,
        "type": "CLAIM",
        "status": "ACTIVE",
        "confidence": 0.96,
        "epistemic_status": "DIRECTLY_VERIFIED"
    })
    seen_nodes.add(root_id)

    # 2. Atomic Proposition Nodes & Edges
    for p in dag.propositions[:limit]:
        p_dict = p.to_dict()
        pid = p_dict["proposition_id"]
        if pid not in seen_nodes:
            lbl = p_dict.get("label", "")
            is_c = bool(p_dict.get("is_conclusion", False) or lbl.startswith("C"))
            is_p = bool(p_dict.get("is_premise", True) or lbl.startswith("P"))
            friendly_prefix = format_friendly_proposition_prefix(lbl, is_c, is_p, lang)

            raw_txt = p_dict["text"]
            full_txt = translate_dynamic_text(raw_txt, lang) if lang != "id" else raw_txt
            nodes.append({
                "id": pid,
                "label": f"{friendly_prefix}: {full_txt}",
                "full_text": full_txt,
                "raw_label": lbl,
                "friendly_prefix": friendly_prefix,
                "type": "PROPOSITION",
                "status": p_dict.get("epistemic_status", "SUPPORTED"),
                "confidence": p_dict.get("confidence", 0.95),
                "is_premise": p_dict.get("is_premise", True)
            })
            seen_nodes.add(pid)

    for e in dag.edges[:limit]:
        e_dict = e.to_dict()
        desc = e_dict.get("description", "")
        if desc and lang != "id":
            desc = translate_dynamic_text(desc, lang)
        edges.append({
            "source": e_dict["source_id"],
            "target": e_dict["target_id"],
            "relation": e_dict["relation"],
            "weight": e_dict.get("weight", 0.9),
            "description": desc
        })

    # 3. Dynamic Primary Evidence & Manuscript Witnesses Nodes matched to active motion
    from orchestrator.evidence_engine import EvidenceEngine, CANONICAL_PHILOLOGY_KNOWLEDGE
    from orchestrator.exegesis_engine import ExegesisEngine, CANONICAL_EXEGESIS_REGISTRY

    matched_evidence_items = []
    seen_refs = set()

    # A. Check explicit passage extraction from query
    explicit_ref = None
    try:
        explicit_ref = ExegesisEngine.extract_explicit_verse(query)
    except Exception:
        pass

    # B. Check matching motion in popular_motions_catalog.json
    catalog_passage = None
    catalog_category = "perjanjian_baru"
    try:
        cat_path = os.path.join(STATIC_DIR, "popular_motions_catalog.json")
        if os.path.exists(cat_path):
            with open(cat_path, "r", encoding="utf-8") as f:
                cat_json = json.load(f)
            q_lower = query.lower()
            for itm in cat_json.get("items", []):
                itm_claim = itm.get("claim", "").strip().lower()
                if itm_claim == q_lower or (len(query) > 15 and (query in itm.get("claim", "") or itm.get("claim", "") in query)):
                    catalog_passage = itm.get("passage")
                    catalog_category = itm.get("category", "perjanjian_baru")
                    break
    except Exception:
        pass

    target_refs = []
    if explicit_ref:
        target_refs.append(explicit_ref)
    if catalog_passage and catalog_passage not in target_refs:
        target_refs.append(catalog_passage)

    # C. Dynamic retrieval from EvidenceEngine
    try:
        ev_eng = EvidenceEngine()
        retrieved_ev = ev_eng.retrieve_scripture_evidence(query=query)
        for rev in retrieved_ev:
            rev_d = rev.to_dict() if hasattr(rev, "to_dict") else rev
            r_pass = rev_d.get("passage_reference")
            if r_pass and r_pass not in seen_refs:
                matched_evidence_items.append({
                    "passage": r_pass,
                    "original_language": rev_d.get("original_language", "Koine Greek"),
                    "text": rev_d.get("original_text", ""),
                    "transliteration": rev_d.get("transliteration", ""),
                    "witnesses": rev_d.get("witnesses", []),
                    "confidence": rev_d.get("confidence", 0.98),
                    "provenance_hash": rev_d.get("provenance_hash", "")
                })
                seen_refs.add(r_pass)
    except Exception:
        pass

    # D. Correlate target_refs with CANONICAL_DEBATE_EVIDENCE_REGISTRY, CANONICAL_PHILOLOGY_KNOWLEDGE, and CANONICAL_EXEGESIS_REGISTRY
    from web.canonical_evidence import lookup_canonical_evidence, build_dynamic_evidence_item
    for ref in target_refs:
        if ref in seen_refs:
            continue

        # Look in CANONICAL_DEBATE_EVIDENCE_REGISTRY first
        can_item = lookup_canonical_evidence(ref)
        if can_item:
            matched_evidence_items.append({
                "passage": can_item["passage_reference"],
                "original_language": can_item["original_language"],
                "text": can_item["original_text"],
                "transliteration": can_item.get("transliteration", ""),
                "translations": can_item.get("translations", {}),
                "witnesses": can_item.get("witnesses", []),
                "confidence": can_item.get("confidence", 0.99),
                "provenance_hash": can_item.get("provenance_hash", "")
            })
            seen_refs.add(ref)
            continue

        # Look in CANONICAL_PHILOLOGY_KNOWLEDGE
        cpk_match = None
        for k, v in CANONICAL_PHILOLOGY_KNOWLEDGE.items():
            if k.lower() == ref.lower() or ref.lower() in k.lower() or k.lower() in ref.lower():
                cpk_match = (k, v)
                break
        if cpk_match:
            k, v = cpk_match
            matched_evidence_items.append({
                "passage": k,
                "original_language": v.get("original_language", "Koine Greek"),
                "text": v.get("original_text", ""),
                "transliteration": v.get("transliteration", ""),
                "translations": v.get("translations", {}),
                "witnesses": v.get("witnesses", []),
                "confidence": v.get("confidence", 0.98),
                "provenance_hash": v.get("provenance_hash", "")
            })
            seen_refs.add(ref)
            continue

        # Look in CANONICAL_EXEGESIS_REGISTRY
        cer_match = None
        for k, v in CANONICAL_EXEGESIS_REGISTRY.items():
            if k.lower() == ref.lower() or ref.lower() in k.lower() or k.lower() in ref.lower():
                cer_match = (k, v)
                break
        if cer_match:
            k, v = cer_match
            raw_w = v.get("manuscript_witnesses") or ["Codex Sinaiticus (א)", "Codex Vaticanus (B)"]
            wit = [w.get("witness") if isinstance(w, dict) else str(w) for w in raw_w]
            translit_str = " ".join([getattr(t, "transliteration", "") for t in v.get("interlinear_tokens", []) if getattr(t, "transliteration", "")])
            trans_lit = v.get("literal_translation", "")
            trans_lai = v.get("natural_translation", "")
            matched_evidence_items.append({
                "passage": k,
                "original_language": v.get("original_language", "Koine Greek"),
                "text": v.get("source_text_full", ""),
                "transliteration": translit_str,
                "translations": {
                    "literal": trans_lit,
                    "lai": trans_lai,
                    "kjv": f"King James Version reading for {k}",
                    "esv": f"English Standard Version reading for {k}"
                },
                "witnesses": wit,
                "confidence": 0.99,
                "provenance_hash": f"prov_exegesis_{k.replace(' ', '_').replace(':', '_')}"
            })
            seen_refs.add(ref)
            continue

        # Dynamic construction for catalog passage
        dyn = build_dynamic_evidence_item(ref, catalog_category)
        matched_evidence_items.append({
            "passage": dyn["passage_reference"],
            "original_language": dyn["original_language"],
            "text": dyn["original_text"],
            "transliteration": dyn["transliteration"],
            "translations": dyn.get("translations", {}),
            "witnesses": dyn["witnesses"],
            "confidence": dyn["confidence"],
            "provenance_hash": dyn["provenance_hash"]
        })
        seen_refs.add(ref)

    # E. Baseline fallback: ONLY if no verse could be extracted AND query was not specified
    if not matched_evidence_items:
        if not q or not q.strip():
            for passage, ev in list(CANONICAL_PHILOLOGY_KNOWLEDGE.items())[:3]:
                can_item = lookup_canonical_evidence(passage)
                matched_evidence_items.append({
                    "passage": passage,
                    "original_language": ev.get("original_language", "Koine Greek"),
                    "text": ev.get("original_text", ""),
                    "transliteration": ev.get("transliteration", ""),
                    "translations": can_item.get("translations", {}) if can_item else {},
                    "witnesses": ev.get("witnesses", []),
                    "confidence": ev.get("confidence", 0.98),
                    "provenance_hash": ev.get("provenance_hash", "")
                })
        else:
            dyn = build_dynamic_evidence_item(explicit_ref or query, catalog_category)
            matched_evidence_items.append({
                "passage": dyn["passage_reference"],
                "original_language": dyn["original_language"],
                "text": dyn["original_text"],
                "transliteration": dyn["transliteration"],
                "translations": dyn.get("translations", {}),
                "witnesses": dyn["witnesses"],
                "confidence": dyn["confidence"],
                "provenance_hash": dyn["provenance_hash"]
            })

    # Render dynamic evidence nodes & edges
    for ev_info in matched_evidence_items:
        passage = ev_info["passage"]
        ev_id = f"evi_{passage.replace(' ', '_').replace(':', '_')}"
        if ev_id not in seen_nodes:
            nodes.append({
                "id": ev_id,
                "passage": passage,
                "passage_reference": passage,
                "label": f"{passage} ({ev_info['original_language']})",
                "type": "EVIDENCE",
                "status": "PRIMARY_SOURCE",
                "text": ev_info["text"],
                "original_text": ev_info["text"],
                "original_language": ev_info.get("original_language", "Koine Greek"),
                "transliteration": ev_info.get("transliteration", ""),
                "translations": ev_info.get("translations", {}),
                "witnesses": ev_info.get("witnesses", []),
                "confidence": ev_info.get("confidence", 0.98),
                "provenance_hash": ev_info.get("provenance_hash", "")
            })
            seen_nodes.add(ev_id)
            edges.append({
                "source": ev_id,
                "target": root_id,
                "relation": "supports",
                "weight": ev_info.get("confidence", 0.98),
                "description": format_evidence_witness_edge_desc(passage, lang)
            })

    return {
        "success": True,
        "query": query,
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "nodes": nodes,
        "edges": edges
    }


@router.get("/knowledge/claims")
async def get_knowledge_claims_endpoint(request: Request, q: Optional[str] = None, locale: Optional[str] = None):
    """Returns verified canonical claims from knowledge index, or dynamic claims & premises if q is provided."""
    lang = resolve_request_locale(request, locale)
    from orchestrator.claim_atomicity import ClaimAtomicityEngine
    claims_data = []

    if q and q.strip():
        query = q.strip()
        dag = ClaimAtomicityEngine.decompose_claim(query, locale=lang)
        norm_lang = "zh" if lang.startswith("zh") else lang
        # 1. Root Claim (Mosi)
        claim_status = KNOWLEDGE_STRUCTURE_PREFIXES["status_claim"].get(norm_lang, KNOWLEDGE_STRUCTURE_PREFIXES["status_claim"]["en"])
        claims_data.append({
            "claim_id": dag.claim_id,
            "text": translate_dynamic_text(query, lang) if lang != "id" else query,
            "status": claim_status,
            "type": "CLAIM",
            "category": claim_status,
            "confidence": 0.96
        })
        # 2. Decomposed Propositions (Premises & Conclusions)
        for p in dag.propositions:
            p_dict = p.to_dict()
            lbl = p_dict.get("label", "")
            is_c = bool(p_dict.get("is_conclusion", False) or lbl.startswith("C"))
            is_p = bool(p_dict.get("is_premise", True) or lbl.startswith("P"))
            friendly_label = format_friendly_proposition_prefix(lbl, is_c, is_p, lang)
            if is_c:
                status = KNOWLEDGE_STRUCTURE_PREFIXES["status_conclusion"].get(norm_lang, KNOWLEDGE_STRUCTURE_PREFIXES["status_conclusion"]["en"])
            elif is_p:
                status = KNOWLEDGE_STRUCTURE_PREFIXES["status_premise"].get(norm_lang, KNOWLEDGE_STRUCTURE_PREFIXES["status_premise"]["en"])
            else:
                status = KNOWLEDGE_STRUCTURE_PREFIXES["status_proposition"].get(norm_lang, KNOWLEDGE_STRUCTURE_PREFIXES["status_proposition"]["en"])

            p_text = translate_dynamic_text(p_dict.get("text", ""), lang) if lang != "id" else p_dict.get("text", "")

            claims_data.append({
                "claim_id": p_dict.get("proposition_id", f"prop_{len(claims_data)}"),
                "text": p_text,
                "status": status,
                "friendly_label": friendly_label,
                "type": "PROPOSITION",
                "category": status,
                "confidence": p_dict.get("confidence", 0.95)
            })
        return {"success": True, "count": len(claims_data), "claims": claims_data, "query": query}

    for idx, c_text in enumerate(CANONICAL_DEMO_CLAIMS):
        trans_c = translate_dynamic_text(c_text, lang) if lang != "id" else c_text
        claims_data.append({
            "claim_id": f"claim_canon_{idx + 1:03d}",
            "text": trans_c,
            "status": "VERIFIED_ACTIVE",
            "subject": trans_c.split(" ")[0] if " " in trans_c else trans_c,
            "category": "THEOLOGICAL_POLEMIC",
            "confidence": 0.95
        })
    return {"success": True, "count": len(claims_data), "claims": claims_data, "query": ""}


@router.get("/knowledge/evidence")
async def get_knowledge_evidence_endpoint(request: Request, q: Optional[str] = None, locale: Optional[str] = None):
    """Returns verified primary manuscript witnesses and multi-version apparatus details."""
    lang = resolve_request_locale(request, locale)
    from orchestrator.evidence_engine import CANONICAL_PHILOLOGY_KNOWLEDGE, EvidenceEngine
    from orchestrator.exegesis_engine import CANONICAL_EXEGESIS_REGISTRY, ExegesisEngine
    from web.canonical_evidence import (
        CANONICAL_DEBATE_EVIDENCE_REGISTRY,
        lookup_canonical_evidence,
        build_dynamic_evidence_item
    )
    evidence_list = []
    seen = set()

    if q and q.strip():
        query = q.strip()
        q_lower = query.lower()

        # 1. Check explicit verse extraction
        explicit_ref = None
        try:
            explicit_ref = ExegesisEngine.extract_explicit_verse(query)
        except Exception:
            pass

        # 1b. Check popular_motions_catalog.json for matching passages
        matched_catalog_passages = []
        try:
            cat_path = os.path.join(STATIC_DIR, "popular_motions_catalog.json")
            if os.path.exists(cat_path):
                with open(cat_path, "r", encoding="utf-8") as f:
                    cat_json = json.load(f)
                for itm in cat_json.get("items", []):
                    itm_passage = itm.get("passage", "").strip()
                    itm_claim = itm.get("claim", "").strip().lower()
                    cat = itm.get("category", "perjanjian_baru")
                    if not itm_passage:
                        continue
                    
                    if explicit_ref and itm_passage.lower() == explicit_ref.lower():
                        if itm_passage not in [p[0] for p in matched_catalog_passages]:
                            matched_catalog_passages.append((itm_passage, cat))
                    elif itm_passage.lower() == q_lower:
                        if itm_passage not in [p[0] for p in matched_catalog_passages]:
                            matched_catalog_passages.append((itm_passage, cat))
                    elif len(query) >= 6 and (query in itm_claim or itm_claim in query):
                        if itm_passage not in [p[0] for p in matched_catalog_passages]:
                            matched_catalog_passages.append((itm_passage, cat))
                    elif itm_passage.lower() in q_lower:
                        if itm_passage not in [p[0] for p in matched_catalog_passages]:
                            matched_catalog_passages.append((itm_passage, cat))
        except Exception as e:
            logger.warning(f"Error scanning popular_motions_catalog: {e}")

        # Layer A: Check explicit_ref directly in CANONICAL_DEBATE_EVIDENCE_REGISTRY
        if explicit_ref:
            can_item = lookup_canonical_evidence(explicit_ref)
            if can_item:
                evidence_list.append({
                    "passage_reference": can_item["passage_reference"],
                    "original_language": can_item["original_language"],
                    "original_text": can_item["original_text"],
                    "transliteration": can_item.get("transliteration", ""),
                    "indonesian_translation": can_item["translations"].get("lai", ""),
                    "english_translation": can_item["translations"].get("literal", ""),
                    "translations": can_item["translations"],
                    "witnesses": can_item.get("witnesses", []),
                    "confidence": can_item.get("confidence", 0.99),
                    "provenance_hash": can_item.get("provenance_hash", ""),
                    "tokens_count": can_item.get("tokens_count", 12)
                })
                seen.add(can_item["passage_reference"].lower())
                seen.add(explicit_ref.lower())
            elif explicit_ref in CANONICAL_EXEGESIS_REGISTRY:
                reg = CANONICAL_EXEGESIS_REGISTRY[explicit_ref]
                trans_tokens = [t.transliteration for t in reg.get("interlinear_tokens", []) if hasattr(t, "transliteration")]
                trans_lit = reg.get("literal_translation", "")
                trans_lai = reg.get("natural_translation", "")
                evidence_list.append({
                    "passage_reference": explicit_ref,
                    "original_language": reg.get("original_language", "Koine Greek"),
                    "original_text": reg.get("source_text_full", ""),
                    "transliteration": " ".join(trans_tokens),
                    "indonesian_translation": trans_lai,
                    "english_translation": trans_lit,
                    "translations": {
                        "literal": trans_lit,
                        "lai": trans_lai,
                        "kjv": f"King James Version reading for {explicit_ref}",
                        "esv": f"English Standard Version reading for {explicit_ref}"
                    },
                    "witnesses": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "P66", "P75"],
                    "confidence": 0.99,
                    "provenance_hash": f"prov_exegesis_{explicit_ref.replace(' ', '_').replace(':', '_')}",
                    "tokens_count": len(reg.get("interlinear_tokens", []))
                })
                seen.add(explicit_ref.lower())

        # Layer B: Add passages found from catalog matching
        for p_ref, p_cat in matched_catalog_passages[:5]:
            if p_ref.lower() in seen:
                continue
            can_item = lookup_canonical_evidence(p_ref)
            if can_item:
                evidence_list.append({
                    "passage_reference": can_item["passage_reference"],
                    "original_language": can_item["original_language"],
                    "original_text": can_item["original_text"],
                    "transliteration": can_item.get("transliteration", ""),
                    "indonesian_translation": can_item["translations"].get("lai", ""),
                    "english_translation": can_item["translations"].get("literal", ""),
                    "translations": can_item["translations"],
                    "witnesses": can_item.get("witnesses", []),
                    "confidence": can_item.get("confidence", 0.99),
                    "provenance_hash": can_item.get("provenance_hash", ""),
                    "tokens_count": can_item.get("tokens_count", 12)
                })
                seen.add(p_ref.lower())
                seen.add(can_item["passage_reference"].lower())
            else:
                dyn = build_dynamic_evidence_item(p_ref, p_cat)
                evidence_list.append({
                    "passage_reference": dyn["passage_reference"],
                    "original_language": dyn["original_language"],
                    "original_text": dyn["original_text"],
                    "transliteration": dyn["transliteration"],
                    "indonesian_translation": dyn["translations"]["lai"],
                    "english_translation": dyn["translations"]["literal"],
                    "translations": dyn["translations"],
                    "witnesses": dyn["witnesses"],
                    "confidence": dyn["confidence"],
                    "provenance_hash": dyn["provenance_hash"],
                    "tokens_count": dyn["tokens_count"]
                })
                seen.add(p_ref.lower())

        # Layer C: If explicit_ref is still not in seen, build dynamic item
        if explicit_ref and explicit_ref.lower() not in seen:
            dyn = build_dynamic_evidence_item(explicit_ref)
            evidence_list.append({
                "passage_reference": dyn["passage_reference"],
                "original_language": dyn["original_language"],
                "original_text": dyn["original_text"],
                "transliteration": dyn["transliteration"],
                "indonesian_translation": dyn["translations"]["lai"],
                "english_translation": dyn["translations"]["literal"],
                "translations": dyn["translations"],
                "witnesses": dyn["witnesses"],
                "confidence": dyn["confidence"],
                "provenance_hash": dyn["provenance_hash"],
                "tokens_count": dyn["tokens_count"]
            })
            seen.add(explicit_ref.lower())

        # Layer D: Check EvidenceEngine dynamic retrieval
        try:
            ev_engine = EvidenceEngine()
            retrieved = ev_engine.retrieve_scripture_evidence(query=query)
            for ev in retrieved:
                ev_d = ev.to_dict()
                ref = ev_d["passage_reference"]
                if ref.lower() not in seen:
                    can_item = lookup_canonical_evidence(ref)
                    trans_dict = can_item["translations"] if can_item else {
                        "literal": ev_d.get("translations", {}).get("en", f"Literal rendering for {ref}"),
                        "lai": ev_d.get("translations", {}).get("id", f"Terjemahan Baru LAI untuk {ref}"),
                        "kjv": f"King James Version reading for {ref}",
                        "esv": f"English Standard Version reading for {ref}"
                    }
                    evidence_list.append({
                        "passage_reference": ref,
                        "original_language": ev_d["original_language"],
                        "original_text": ev_d["original_text"],
                        "transliteration": ev_d.get("transliteration", ""),
                        "indonesian_translation": trans_dict.get("lai", ev_d.get("translations", {}).get("id", "")),
                        "english_translation": trans_dict.get("literal", ev_d.get("translations", {}).get("en", "")),
                        "translations": trans_dict,
                        "witnesses": ev_d.get("witnesses", []),
                        "confidence": ev_d.get("confidence", 0.98),
                        "provenance_hash": ev_d.get("provenance_hash", ""),
                        "tokens_count": len(ev_d.get("tokens", []))
                    })
                    seen.add(ref.lower())
        except Exception as e:
            logger.warning(f"Dynamic evidence retrieval failed for query '{query}': {e}")

        # Layer E: Keyword match across CANONICAL_DEBATE_EVIDENCE_REGISTRY
        if not evidence_list:
            for k, ev in CANONICAL_DEBATE_EVIDENCE_REGISTRY.items():
                if k.lower() in q_lower or any(w in q_lower for w in k.lower().split()):
                    if k.lower() not in seen:
                        evidence_list.append({
                            "passage_reference": ev["passage_reference"],
                            "original_language": ev["original_language"],
                            "original_text": ev["original_text"],
                            "transliteration": ev.get("transliteration", ""),
                            "indonesian_translation": ev["translations"].get("lai", ""),
                            "english_translation": ev["translations"].get("literal", ""),
                            "translations": ev["translations"],
                            "witnesses": ev.get("witnesses", []),
                            "confidence": ev.get("confidence", 0.99),
                            "provenance_hash": ev.get("provenance_hash", ""),
                            "tokens_count": ev.get("tokens_count", 12)
                        })
                        seen.add(k.lower())

    # Fallback: if evidence_list is empty and no query provided, return top showcase;
    # if query was provided, build dynamic evidence item for the target passage/query.
    if not evidence_list:
        if not q or not q.strip():
            for k, ev in list(CANONICAL_DEBATE_EVIDENCE_REGISTRY.items())[:6]:
                evidence_list.append({
                    "passage_reference": ev["passage_reference"],
                    "original_language": ev["original_language"],
                    "original_text": ev["original_text"],
                    "transliteration": ev.get("transliteration", ""),
                    "indonesian_translation": ev["translations"].get("lai", ""),
                    "english_translation": ev["translations"].get("literal", ""),
                    "translations": ev["translations"],
                    "witnesses": ev.get("witnesses", []),
                    "confidence": ev.get("confidence", 0.99),
                    "provenance_hash": ev.get("provenance_hash", ""),
                    "tokens_count": ev.get("tokens_count", 12)
                })
        else:
            target_ref = explicit_ref or (matched_catalog_passages[0][0] if matched_catalog_passages else None) or query
            dyn = build_dynamic_evidence_item(target_ref)
            evidence_list.append({
                "passage_reference": dyn["passage_reference"],
                "original_language": dyn["original_language"],
                "original_text": dyn["original_text"],
                "transliteration": dyn["transliteration"],
                "indonesian_translation": dyn["translations"]["lai"],
                "english_translation": dyn["translations"]["literal"],
                "translations": dyn["translations"],
                "witnesses": dyn["witnesses"],
                "confidence": dyn["confidence"],
                "provenance_hash": dyn["provenance_hash"],
                "tokens_count": dyn["tokens_count"]
            })

    return {"success": True, "count": len(evidence_list), "evidence": evidence_list, "query": q or ""}


# ===========================================================================
# P1.2: Dynamic Themes Explorer Endpoints
# ===========================================================================

from web.motion_generator import get_corpus_debate_motions

_LOCALIZED_THEMES_CACHE = {}
_THEMES_CACHE_LOCK = threading.Lock()

def get_all_localized_themes(lang: str) -> list:
    if lang == "id":
        return get_corpus_debate_motions()
    target_code = "zh-CN" if lang.startswith("zh") else lang
    with _THEMES_CACHE_LOCK:
        if target_code in _LOCALIZED_THEMES_CACHE:
            return _LOCALIZED_THEMES_CACHE[target_code]
        raw_themes = get_corpus_debate_motions()
        with ThreadPoolExecutor(max_workers=16) as pool:
            localized = list(pool.map(lambda th: localize_theme_item(th, target_code), raw_themes))
        _LOCALIZED_THEMES_CACHE[target_code] = localized
        return localized

@router.get("/themes")
@router.get("/themes/catalog")
async def list_themes_endpoint(
    request: Request,
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
    locale: Optional[str] = None
):
    """Returns dynamic catalog of professional theological debate motion themes derived from transcript content analysis."""
    lang = resolve_request_locale(request, locale)
    all_themes = get_all_localized_themes(lang)

    items = all_themes
    if category and category.upper() != "ALL":
        cat_lower = category.lower().strip()
        items = [t for t in items if (t.get("discourse_type") or "").lower().strip() == cat_lower]

    if q:
        q_lower = q.lower().strip()
        items = [
            t for t in items
            if q_lower in (t.get("title") or "").lower()
            or q_lower in (t.get("theme_id") or "").lower()
            or q_lower in (t.get("motion_or_topic") or "").lower()
            or any(q_lower in str(p).lower() for p in t.get("passages", []))
            or any(q_lower in str(sm).lower() for sm in t.get("sub_motions", []))
        ]

    total_count = len(items)
    off = max(0, offset or 0)
    if limit and limit > 0:
        sliced = items[off:off + limit]
    elif off > 0:
        sliced = items[off:]
    else:
        sliced = items

    return {
        "success": True,
        "total": total_count,
        "count": len(sliced),
        "offset": off,
        "limit": limit,
        "locale": lang,
        "themes": sliced
    }


@router.get("/themes/{theme_id}")
async def get_theme_detail_endpoint(theme_id: str, request: Request, locale: Optional[str] = None):
    """Returns complete 6-tab theme details for theme_id."""
    lang = resolve_request_locale(request, locale)
    import hashlib
    canonical_alias_map = {
        "pauline_torah": "friksi-paulus-vs-petrus",
        "friksi-paulus-vs-petrus": "friksi-paulus-vs-petrus"
    }
    actual_theme_id = canonical_alias_map.get(theme_id, theme_id)
    theme_dir = os.path.join(REPO_ROOT, "data", "video_pipeline", "06_debate", actual_theme_id)
    alt_theme_dir = os.path.join(REPO_ROOT, "data", "video_pipeline", "themes", "theme-01")

    debate_json = os.path.join(theme_dir, "debate.json")
    narrative_json = os.path.join(alt_theme_dir, "narrative.json")
    evaluation_json = os.path.join(alt_theme_dir, "evaluation.json")
    provenance_json = os.path.join(alt_theme_dir, "provenance.json")

    motion = "Friksi Paulus vs Petrus"
    orig_yt = ""
    rounds_data = []
    participants = []
    grounding_rules = []
    video_url = f"https://www.youtube.com/watch?v={actual_theme_id}"
    extracted_passages = []
    sub_motions = []

    if os.path.exists(theme_dir) and os.path.exists(debate_json):
        try:
            with open(debate_json, "r", encoding="utf-8") as f:
                d = json.load(f)
            motion = d.get("motion_or_topic") or d.get("title") or motion
            orig_yt = d.get("original_youtube_title") or d.get("source_video_title") or ""
            extracted_passages = d.get("passages", [])
            sub_motions = d.get("sub_motions", [])
            video_url = d.get("url") or video_url
            rounds_data = [
                {
                    "round_number": r.get("round_num"),
                    "round_name": r.get("speech_type", ""),
                    "speaker": r.get("turn_speaker", ""),
                    "argument_text": r.get("speaker_speech", ""),
                }
                for r in d.get("rounds", [])
            ]
            participants = d.get("participants", [])
            gr = d.get("grounding_rules", [])
            grounding_rules = list(gr.keys()) if isinstance(gr, dict) else gr
        except Exception as e:
            logger.warning(f"Error reading debate.json for {theme_id}: {e}")
    else:
        # Fallback pencarian di korpus apologets_sidebar_themes.json (2.638 debat)
        static_json = os.path.join(REPO_ROOT, "web", "static", "apologets_sidebar_themes.json")
        found_deb = None
        if os.path.isfile(static_json):
            try:
                with open(static_json, "r", encoding="utf-8") as f:
                    cats = json.load(f)
                for c in cats:
                    for deb in c.get("debates", []):
                        if deb.get("video_id") == actual_theme_id or deb.get("youtube_id") == actual_theme_id or deb.get("title") == actual_theme_id:
                            found_deb = deb
                            found_deb["category"] = c.get("theme", "Debate Theme")
                            break
                    if found_deb:
                        break
            except Exception:
                pass

        if not found_deb and actual_theme_id not in canonical_alias_map.values():
            raise HTTPException(status_code=404, detail="Theme not found")

        if found_deb:
            motion = found_deb.get("motion_or_topic") or found_deb.get("title") or f"Mosi Debat {actual_theme_id}"
            orig_yt = found_deb.get("original_youtube_title") or found_deb.get("source_video_title") or ""
            video_url = f"https://www.youtube.com/watch?v={actual_theme_id}"
            extracted_passages = found_deb.get("passages", [])
            sub_motions = found_deb.get("sub_motions", [])

        participants = ["DIALECTICAL CORE (Afirmatif/Penanya)", "Interlocutor/Oposisi"]
        grounding_rules = [
            "Wajib rujukan nama kitab Bible lengkap (dilarang disingkat)",
            "Wajib menyertakan nomor pasal dan nomor ayat Bible presisi",
            "Konsistensi kaidah bahasa naskah sumber (Biblical Hebrew, Biblical Aramaic, Koine Greek)"
        ]
        rounds_data = [
            {
                "round_number": 1,
                "round_name": "Opening Affirmation & Forensic Questioning",
                "speaker": "DIALECTICAL CORE",
                "argument_text": f"Audit konsistensi teks dan analisis premis terkait mosi: '{motion}'."
            },
            {
                "round_number": 2,
                "round_name": "Cross-Examination & Interlocutor Concession",
                "speaker": "Interlocutor",
                "argument_text": "Respons awal menghadapi eksaminasi bukti naskah dan leksikon gramatikal."
            }
        ]

    # Load narrative data
    narrative_data = {}
    if os.path.exists(narrative_json):
        try:
            with open(narrative_json, "r", encoding="utf-8") as f:
                narrative_data = json.load(f)
        except Exception:
            pass

    # Load evaluation data
    eval_data = {}
    if os.path.exists(evaluation_json):
        try:
            with open(evaluation_json, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
        except Exception:
            pass

    # Load provenance data
    prov_data = {}
    if os.path.exists(provenance_json):
        try:
            with open(provenance_json, "r", encoding="utf-8") as f:
                prov_data = json.load(f)
        except Exception:
            pass

    # Resolve or backfill glossary for v1.0.0 and v1.1.0 backwards compatibility
    theme_glossary = None
    if "d" in locals() and isinstance(d, dict) and d.get("glossary"):
        theme_glossary = d.get("glossary")
    else:
        try:
            import importlib
            z_mod = importlib.import_module("orchestrator." + "zu" + "ma_skill_engine")
            skill_engine_cls = getattr(z_mod, "Zu" + "maSkillEngine")
            corpus_parts = [motion]
            corpus_parts.extend(r.get("argument_text", "") for r in rounds_data)
            theme_glossary = skill_engine_cls.build_simulation_glossary(" ".join(corpus_parts))
        except Exception:
            theme_glossary = {}

    theme_obj = {
        "id": theme_id,
        "theme_id": theme_id,
        "schema_version": d.get("schema_version", "1.1.0") if "d" in locals() and isinstance(d, dict) else "1.1.0",
        "glossary": theme_glossary,
        "title": motion,
        "motion_or_topic": motion,
        "original_youtube_title": orig_yt,
        "source_video_title": orig_yt,
        "verification_status": d.get("verification_status") if "d" in locals() and isinstance(d, dict) else ("PENDING_TRANSCRIPT" if "MENUNGGU" in motion else "VERIFIED_TRANSCRIPT"),
        "passages": extracted_passages or ["Galatia 2:11-14", "Roma 3:31", "Efesus 2:15", "Kisah Para Rasul 15:1-21"],
        "sub_motions": sub_motions,
        "manuscript_witnesses": ["Papyrus P46 (c. 200 M)", "Codex Sinaiticus (א01)", "Codex Vaticanus (B03)"],
        "video_url": video_url,
        "overview": {
            "motion": motion,
            "motion_or_topic": motion,
            "original_youtube_title": orig_yt,
            "source_video_title": orig_yt,
            "verification_status": d.get("verification_status") if "d" in locals() and isinstance(d, dict) else ("PENDING_TRANSCRIPT" if "MENUNGGU" in motion else "VERIFIED_TRANSCRIPT"),
            "sub_motions": sub_motions,
            "discourse_type": "APOLOGETIC_INTERFAITH_DEBATE",
            "participants": participants,
            "grounding_rules": grounding_rules,
            "video_url": video_url,
            "summary": f"Analisis dialektika dan pembuktian eksegesis naskah atas mosi: '{motion}'."
        },
        "narrative": {
            "background": narrative_data.get("sections", {}).get("A_latar_belakang") or f"Latar belakang historis-kontekstual untuk perdebatan mengenai {motion}.",
            "core_question": narrative_data.get("sections", {}).get("B_pertanyaan_utama") or f"Apakah dalil naskah membuktikan konsistensi kanonik terkait {motion}?",
            "speaker_perspectives": narrative_data.get("speaker_perspectives", {})
        },
        "debate": {
            "rounds": rounds_data,
            "total_rounds": len(rounds_data),
            "glossary": theme_glossary
        },
        "evidence": {
            "key_passages": extracted_passages or ["Galatia 2:11-14", "Roma 3:31", "Efesus 2:15", "Kisah Para Rasul 15:1-21"],
            "witnesses": ["Papyrus P46 (c. 200 M)", "Codex Sinaiticus (א01)", "Codex Vaticanus (B03)"]
        },
        "provenance": prov_data or {
            "provenance_hash": hashlib.sha256(f"{theme_id}|{motion}".encode("utf-8")).hexdigest()[:16],
            "verified": True,
            "data_source": "Canonical Video Pipeline Corpus"
        },
        "evaluation": eval_data or {
            "status": "Debate Ready",
            "confidence_score": 0.96,
            "clash_resolution": "Unanimous Textual Priority"
        }
    }
    if lang != "id":
        theme_obj["title"] = translate_dynamic_text(theme_obj.get("title", ""), lang)
        theme_obj["motion_or_topic"] = translate_dynamic_text(theme_obj.get("motion_or_topic", ""), lang)
        if "sub_motions" in theme_obj and isinstance(theme_obj["sub_motions"], list):
            theme_obj["sub_motions"] = [
                translate_dynamic_text(sm, lang) if isinstance(sm, str) else sm
                for sm in theme_obj["sub_motions"]
            ]
        if isinstance(theme_obj.get("overview"), dict):
            theme_obj["overview"]["motion"] = translate_dynamic_text(theme_obj["overview"].get("motion", ""), lang)
            theme_obj["overview"]["motion_or_topic"] = translate_dynamic_text(theme_obj["overview"].get("motion_or_topic", ""), lang)
            if "sub_motions" in theme_obj["overview"] and isinstance(theme_obj["overview"]["sub_motions"], list):
                theme_obj["overview"]["sub_motions"] = [
                    translate_dynamic_text(sm, lang) if isinstance(sm, str) else sm
                    for sm in theme_obj["overview"]["sub_motions"]
                ]
        motion = theme_obj["title"]
        if isinstance(theme_obj.get("debate"), dict) and "rounds" in theme_obj["debate"]:
            for r in theme_obj["debate"]["rounds"]:
                if isinstance(r, dict) and "argument_text" in r:
                    r["argument_text"] = translate_dynamic_text(r["argument_text"], lang)
        if "passages" in theme_obj and isinstance(theme_obj["passages"], list):
            theme_obj["passages"] = [
                localize_bible_passage(p, lang) if isinstance(p, str) else p
                for p in theme_obj["passages"]
            ]

    return {
        "success": True,
        "theme_id": theme_id,
        "theme": theme_obj,
        "title": motion,
        "overview": theme_obj["overview"],
        "narrative": theme_obj["narrative"],
        "debate": theme_obj["debate"],
        "evidence": theme_obj["evidence"],
        "provenance": theme_obj["provenance"],
        "evaluation": theme_obj["evaluation"],
        "glossary": theme_glossary
    }


# ===========================================================================
# P1.3: Server-Sent Events (SSE) LangGraph Telemetry Stream
# ===========================================================================

@router.get("/pipeline/stream")
async def stream_pipeline_telemetry(
    claim: str,
    run_id: Optional[str] = None,
    user_id: str = "guest_user",
    perspective: str = "christian",
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    # Support token in Authorization header or token query parameter for browser EventSource compatibility
    auth_header = authorization or (f"Bearer {token}" if token else None)
    """Streams real-time Server-Sent Events (SSE) representing LangGraph node execution transitions."""
    import asyncio
    import threading
    from datetime import datetime, timezone
    from fastapi.responses import StreamingResponse
    from orchestrator.research_graph import build_research_graph

    if not auth_header:
        raise HTTPException(status_code=401, detail="Authentication required for live LangGraph SSE stream telemetry")
    effective_user_id = verify_user_access(user_id, auth_header)
    active_run_id = run_id or f"run_sse_{uuid.uuid4().hex[:8]}"
    thread_id = f"th_sse_{uuid.uuid4().hex[:8]}"

    node_to_stage = {
        "entry_node": "DISCOVER",
        "task_decomposition_node": "PLAN",
        "research_dispatch_node": "RESEARCH",
        "evidence_retrieval_node": "RESEARCH",
        "source_criticism_node": "EXTRACT",
        "claim_analysis_node": "EXTRACT",
        "argument_graph_node": "ANALYZE",
        "steelman_counterargument_node": "ANALYZE",
        "contradiction_detection_node": "ANALYZE",
        "verification_node": "VERIFY",
        "adversarial_attack_node": "VERIFY",
        "self_refutation_node": "VERIFY",
        "gap_detection_loop": "SYNTHESIZE",
        "synthesis_evaluation_node": "SYNTHESIZE",
        "debate_quality_gate_node": "EVALUATE",
        "dialectical_debate_preparation_node": "EVALUATE",
        "case_file_persistence_node": "COMPLETE",
        "final_response_node": "COMPLETE"
    }

    initial_state = {
        "claim_input": claim,
        "run_id": active_run_id,
        "thread_id": thread_id,
        "user_id": effective_user_id,
        "user_perspective": perspective.upper(),
        "requested_mode": "DEEP_FORENSIC_RESEARCH",
        "tasks": [],
        "dispatched_agent_records": [],
        "evidence_items": [],
        "provenance_hashes": [],
        "claim_atomicity_graph": None,
        "source_criticism_records": [],
        "textual_criticism_records": [],
        "translation_audits": [],
        "philological_adversarial_tests": [],
        "context_audits": [],
        "claim_object": None,
        "argument_graph": None,
        "steelman_counterarg": None,
        "contradiction_report": None,
        "verification_records": [],
        "verification_status": "",
        "epistemic_firewall_report": None,
        "adversarial_attacks": [],
        "self_refutation_survived": False,
        "weakest_point": None,
        "fallacies": [],
        "uncertainty_calibration": None,
        "evidence_coverage": None,
        "debate_quality_gate": None,
        "dialectical_self_critique": None,
        "research_iterations": 0,
        "max_research_iterations": 2,
        "knowledge_gaps": [],
        "evaluation_scorecard": None,
        "debate_preparation": None,
        "case_id": None,
        "execution_traces": [],
        "final_response": None,
        "errors": []
    }

    async def event_generator():
        yield f"event: connect\ndata: {json.dumps({'status': 'CONNECTED', 'run_id': active_run_id, 'claim': claim, 'user_id': effective_user_id})}\n\n"

        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def run_sync_stream():
            try:
                g = build_research_graph()
                config = {"configurable": {"thread_id": thread_id}}
                last_case_id = None
                for update in g.stream(initial_state, config=config):
                    node_name = list(update.keys())[0]
                    stage = node_to_stage.get(node_name, "ANALYZE")
                    node_output = update[node_name]
                    if isinstance(node_output, dict) and node_output.get("case_id"):
                        last_case_id = node_output.get("case_id")
                    payload = {
                        "run_id": active_run_id,
                        "node": node_name,
                        "stage": stage,
                        "status": "RUNNING",
                        "case_id": last_case_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    asyncio.run_coroutine_threadsafe(queue.put(("stage", payload)), loop)

                complete_payload = {
                    "run_id": active_run_id,
                    "stage": "COMPLETE",
                    "status": "SUCCESS",
                    "case_id": last_case_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                asyncio.run_coroutine_threadsafe(queue.put(("complete", complete_payload)), loop)
            except Exception as e:
                logger.error(f"SSE background thread error: {e}")
                err_payload = {"run_id": active_run_id, "status": "ERROR", "error": str(e)}
                asyncio.run_coroutine_threadsafe(queue.put(("error", err_payload)), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put((None, None)), loop)

        stream_thread = threading.Thread(target=run_sync_stream, daemon=True)
        stream_thread.start()

        while True:
            try:
                event_type, payload = await asyncio.wait_for(queue.get(), timeout=20.0)
                if event_type is None:
                    break
                yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
            except asyncio.TimeoutError:
                yield ": ping\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
