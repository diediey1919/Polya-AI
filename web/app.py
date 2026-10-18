"""FastAPI WebSocket & REST Backend for Polya Dialectical Live Arena.
Supports:
- 6-Slot Multi-Guest Stage (1 Host AI Zuma + 5 Guest Debaters)
- Real-time Viewer Counter & Join Stage Queue
- Live Public Chat with Scripture Citation Highlighting
- Floating Google Sign-In & Profile Wallets
- Multi E-Wallet Donation System (DANA, GoPay, ShopeePay, OVO, QRIS) with 10% Platform Fee / 90% Debater Net
- Live Sawer Banner Alerts & Chimes
- PK Battle Gauge, Evidence HUD Teleprompter, Tap Reactions
- 9router AI Dialectical Engine
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import random
import re
import sqlite3
import time
import uuid
import wave
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import urllib.request
import urllib.error
import requests

# Add runtime directory to sys.path for polya_runtime debate engine
runtime_dir = os.environ.get("POLYA_RUNTIME_DIR", str(Path(__file__).resolve().parent.parent / "runtime"))
sys.path.insert(0, runtime_dir)
from polya_runtime.debate_engine.api import arena_service
from polya_runtime.debate_engine.training_api import DebateTrainingService

training_service = DebateTrainingService.get_instance()


from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, UploadFile, File, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("polya.arena")

DB_PATH = os.environ.get("POLYA_DB_PATH", "/home/ubuntu/.polya/polya_index.db")
NINE_ROUTER_URL = os.environ.get("NINE_ROUTER_URL", "http://localhost:20128/v1/chat/completions")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

# Load GEMINI_API_KEY for Google Gemini Indonesian TTS
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY and os.path.exists("/home/ubuntu/.env.gemini"):
    try:
        with open("/home/ubuntu/.env.gemini") as _f:
            for _line in _f:
                if _line.startswith("GEMINI_API_KEY="):
                    GEMINI_API_KEY = _line.strip().split("=", 1)[1]
                    break
    except Exception as _e:
        logger.warning(f"Error loading .env.gemini: {_e}")

AUDIO_CACHE_DIR = Path(os.environ.get("POLYA_AUDIO_CACHE", "/home/ubuntu/.polya/audio_cache"))
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq Whisper API client initialized successfully.")
    except Exception as e:
        logger.warning(f"Groq client initialization warning: {e}")

WHISPER_HALLUCINATIONS = {
    "terima kasih",
    "terima kasih.",
    "terima kasih sudah menonton",
    "terima kasih sudah menonton.",
    "terima kasih banyak",
    "terima kasih banyak.",
    "terima kasih telah menonton",
    "terimakasih",
    "terimakasih.",
    "thank you",
    "thank you.",
    "thank you for watching",
    "thank you very much",
    "subtitle by",
    "subtitles by",
    "diterjemahkan oleh",
    "you",
    ".",
    "..",
    "...",
    "....",
    "hmm",
    "hmmm",
    "uh",
    "uhm",
    "ah",
    "oh",
    "[musik]",
    "[tepuk tangan]",
    "[suara batuk]",
    "[suara tawa]",
}

def is_whisper_hallucination(text: str) -> bool:
    if not text:
        return True
    cleaned = text.strip().lower().rstrip(".,!?")
    if len(cleaned) < 2:
        return True
    if cleaned in WHISPER_HALLUCINATIONS or text.strip().lower() in WHISPER_HALLUCINATIONS:
        return True
    # Filter repeated single word/char noise hallucinations like "a a a a" or "..."
    words = cleaned.split()
    if len(words) >= 4 and len(set(words)) == 1:
        return True
    return False

async def transcribe_audio_groq(audio_bytes: bytes, filename: str = "voice.webm", language: Optional[str] = None) -> str:
    """Transcribes audio using Groq Whisper API (whisper-large-v3-turbo) with automatic native language detection."""
    if not groq_client:
        return ""
    try:
        file_tuple = (filename, audio_bytes, "audio/webm")
        create_kwargs = {
            "file": file_tuple,
            "model": "whisper-large-v3-turbo",
            "response_format": "json",
            "temperature": 0.0
        }
        # If language is explicitly provided (and not 'auto'/'any'), enforce it; otherwise Whisper will auto-detect native speaker language
        if language and str(language).strip().lower() not in ("auto", "none", "", "all", "detect"):
            create_kwargs["language"] = str(language).strip().lower()

        transcription = groq_client.audio.transcriptions.create(**create_kwargs)
        res_text = transcription.text.strip()
        if is_whisper_hallucination(res_text):
            logger.info(f"Filtered Whisper hallucination/silence noise: '{res_text}'")
            return ""
        return res_text
    except Exception as e:
        logger.error(f"Groq Whisper transcription error: {e}")
        return ""


def wrap_pcm_as_wav(pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Wraps raw 24kHz 16-bit mono PCM bytes into a standard playable WAV RIFF container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


async def generate_gemini_tts(text: str, voice: str = "Kore") -> Optional[str]:
    """Generates natural Indonesian speech using Google Gemini TTS API with SHA-256 disk cache
    and Google Indonesian TTS fallback. Blacklists Microsoft Edge completely."""
    if not text or not text.strip():
        return None

    clean_text = re.sub(r'[*_#`~\[\]\(\)>@]', ' ', text).strip()
    clean_text = re.sub(r'\s+', ' ', clean_text)
    if not clean_text:
        return None
    if len(clean_text) > 350:
        clean_text = clean_text[:350]

    # SHA-256 disk cache check to avoid quota depletion
    cache_key = hashlib.sha256(f"gemini_tts_id:{voice}:{clean_text}".encode("utf-8")).hexdigest()
    cache_file = AUDIO_CACHE_DIR / f"{cache_key}.wav"
    if cache_file.exists() and cache_file.stat().st_size > 100:
        try:
            with open(cache_file, "rb") as f:
                wav_bytes = f.read()
                logger.info(f"Gemini TTS cache HIT: {cache_key[:8]} ({len(wav_bytes)} bytes)")
                return f"data:audio/wav;base64,{base64.b64encode(wav_bytes).decode('utf-8')}"
        except Exception as e:
            logger.warning(f"Error reading TTS cache: {e}")

    prompt = f"Hanya ucapkan TRANSKRIP dengan pelafalan dan intonasi penutur asli Bahasa Indonesia.\n\n#### TRANSCRIPT\n{clean_text}"

    models_to_try = [
        "gemini-3.1-flash-tts-preview",
        "gemini-2.5-flash-preview-tts"
    ]

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice}
                }
            }
        }
    }

    loop = asyncio.get_event_loop()
    def _call_gemini():
        if GEMINI_API_KEY:
            for m in models_to_try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
                try:
                    resp = requests.post(endpoint, json=payload, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        inline = next((p.get("inlineData") or p.get("inline_data") for p in parts if "inlineData" in p or "inline_data" in p), None)
                        if inline and "data" in inline:
                            pcm_data = base64.b64decode(inline["data"])
                            wav_data = wrap_pcm_as_wav(pcm_data, sample_rate=24000)
                            try:
                                with open(cache_file, "wb") as cf:
                                    cf.write(wav_data)
                            except Exception as ce:
                                logger.warning(f"Error writing TTS cache: {ce}")
                            logger.info(f"Gemini TTS generated using {m} ({len(wav_data)} bytes)")
                            return f"data:audio/wav;base64,{base64.b64encode(wav_data).decode('utf-8')}"
                    else:
                        logger.warning(f"Gemini TTS ({m}) error HTTP {resp.status_code}: {resp.text[:120]}")
                except Exception as err:
                    logger.warning(f"Gemini TTS ({m}) exception: {err}")

        # Seamless Fallback to Google Indonesian Voice Engine (gTTS)
        try:
            from gtts import gTTS
            tts = gTTS(text=clean_text, lang='id')
            mp3_buf = io.BytesIO()
            tts.write_to_fp(mp3_buf)
            mp3_bytes = mp3_buf.getvalue()
            logger.info(f"Google Indonesian TTS fallback generated ({len(mp3_bytes)} bytes)")
            return f"data:audio/mp3;base64,{base64.b64encode(mp3_bytes).decode('utf-8')}"
        except Exception as fb_err:
            logger.error(f"Google TTS fallback error: {fb_err}")
            return None

    return await loop.run_in_executor(None, _call_gemini)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence:
    # 1. Existence / directory check
    # 2. Schema check & Auto-healing table creation
    # 3. Indexes & constraints
    logger.info("Initializing Polya database schema via lifespan...")
    try:
        from services import init_foundation_db, verify_foundation_schema, SessionService
        init_foundation_db()
        if not verify_foundation_schema():
            logger.warning("Foundation schema verification incomplete, re-running init...")
            init_foundation_db()
        logger.info("Foundation database self-healing complete and verified.")
    except Exception as e:
        logger.error(f"Failed to auto-heal foundation database: {e}")

    try:
        init_arena_db()
        logger.info("Arena database self-healing complete.")
    except Exception as e:
        logger.error(f"Failed to auto-heal arena database: {e}")

    yield


app = FastAPI(title="Polya Dialectical Live Arena", lifespan=lifespan)

# Mount Foundation API Router (Phase-1 Web Foundation)
try:
    from api_foundation import router as foundation_router, get_current_user_id
    from services import SessionService, GoogleAuthVerifier
    app.include_router(foundation_router)
except Exception:
    try:
        from web.api_foundation import router as foundation_router, get_current_user_id
        from web.services import SessionService, GoogleAuthVerifier
        app.include_router(foundation_router)
    except Exception as e:
        logger.error(f"Failed to mount foundation_router: {e}")

# Ensure static directories exist
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ---------------------------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_arena_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table with E-Wallets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS arena_users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        name TEXT,
        avatar_url TEXT,
        bio TEXT,
        role TEXT DEFAULT 'visitor',
        dana TEXT DEFAULT '',
        gopay TEXT DEFAULT '',
        shopeepay TEXT DEFAULT '',
        ovo TEXT DEFAULT '',
        qris_url TEXT DEFAULT '',
        total_donations_received INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # Donations table with 10% / 90% split
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS arena_donations (
        id TEXT PRIMARY KEY,
        donor_user_id TEXT,
        donor_name TEXT,
        donor_avatar TEXT,
        recipient_user_id TEXT,
        recipient_name TEXT,
        gross_amount INTEGER,
        platform_fee_10pct INTEGER,
        recipient_net_90pct INTEGER,
        payment_method TEXT,
        message TEXT,
        status TEXT DEFAULT 'PAID',
        timestamp TEXT
    )
    """)

    # User Wallet Balances
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS arena_wallet_balances (
        user_id TEXT PRIMARY KEY,
        balance_net INTEGER DEFAULT 0,
        total_withdrawn INTEGER DEFAULT 0,
        updated_at TEXT
    )
    """)

    # Platform Treasury (10% Fee Pool)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS arena_platform_treasury (
        id INTEGER PRIMARY KEY,
        total_fee_collected INTEGER DEFAULT 0,
        updated_at TEXT
    )
    """)
    cursor.execute("INSERT OR IGNORE INTO arena_platform_treasury (id, total_fee_collected, updated_at) VALUES (1, 0, datetime('now'))")

    # Chat Messages History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS arena_chat_messages (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        user_name TEXT,
        user_avatar TEXT,
        message TEXT,
        is_system INTEGER DEFAULT 0,
        timestamp TEXT
    )
    """)

    # Seed AI Host Profile
    cursor.execute("""
    INSERT OR IGNORE INTO arena_users (user_id, email, name, avatar_url, bio, role, dana, gopay, shopeepay, ovo, created_at)
    VALUES (
        'zuma_ai',
        'zuma@polya.ai',
        'Polya ZUMA (AI Core)',
        '/static/avatars/zuma.png',
        'AI Apologetika Forensik — Penguji Konsistensi Dogma & Kanon Teks Bible',
        'host_ai',
        '081299990001',
        '081299990001',
        '081299990001',
        '081299990001',
        datetime('now')
    )
    """)

    # Seed Demo Guest Profiles
    demo_guests = [
        ('user_markus', 'markus@gmail.com', 'Markus_P', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Markus', 'Pengkaji Teologi Perjanjian Baru', '081211112222', '081211112222', '081211112222', '081211112222'),
        ('user_ahmad', 'ahmad@gmail.com', 'Ahmad_Debater', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ahmad', 'Peneliti Manuskrip Ibrani & Yunani', '081388887777', '081388887777', '081388887777', '081388887777'),
        ('user_yohanes', 'yohanes@gmail.com', 'Yohanes_D', 'https://api.dicebear.com/7.x/avataaars/svg?seed=Yohanes', 'Pemerhati Eksegesa Biblika', '081544443333', '081544443333', '081544443333', '081544443333')
    ]
    for uid, email, name, avatar, bio, d, g, sp, ovo in demo_guests:
        cursor.execute("""
        INSERT OR IGNORE INTO arena_users (user_id, email, name, avatar_url, bio, role, dana, gopay, shopeepay, ovo, created_at)
        VALUES (?, ?, ?, ?, ?, 'debater', ?, ?, ?, ?, datetime('now'))
        """, (uid, email, name, avatar, bio, d, g, sp, ovo))
        cursor.execute("""
        INSERT OR IGNORE INTO arena_wallet_balances (user_id, balance_net, total_withdrawn, updated_at)
        VALUES (?, 0, 0, datetime('now'))
        """, (uid,))

    # -----------------------------------------------------------------------
    # Social Media System Tables (Instagram & TikTok Style Feed)
    # -----------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS social_posts (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        user_name TEXT,
        user_avatar TEXT,
        user_badge TEXT DEFAULT 'Debater',
        media_type TEXT, -- 'photo', 'video', 'text', 'audio'
        media_url TEXT,
        caption TEXT,
        music_title TEXT DEFAULT '',
        music_url TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        likes_count INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS social_comments (
        id TEXT PRIMARY KEY,
        post_id TEXT,
        user_id TEXT,
        user_name TEXT,
        user_avatar TEXT,
        comment TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS social_likes (
        user_id TEXT,
        post_id TEXT,
        created_at TEXT,
        PRIMARY KEY (user_id, post_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS social_stories (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        user_name TEXT,
        user_avatar TEXT,
        content TEXT,
        media_url TEXT,
        media_type TEXT DEFAULT 'text',
        bg_gradient TEXT DEFAULT 'from-purple-600 to-indigo-600',
        created_at TEXT
    )
    """)

    # Seed initial rich social feed if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM social_posts")
    post_cnt = cursor.fetchone()["cnt"]
    if post_cnt == 0:
        seed_posts = [
            (
                "post_zuma_1",
                "zuma_ai",
                "Polya ZUMA (AI Core)",
                "https://api.dicebear.com/7.x/bottts/svg?seed=Zuma",
                "👑 Host AI",
                "photo",
                "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=1200&q=80",
                "🔍 Bedah Forensik Yohanes 1:1c: Naskah Codex Sinaiticus (א) dan Codex Vaticanus (B) membuktikan bahwa kata 'θεός' pada akhir klausa tidak berartikel (anarthrous). Dalam kaidah gramatika Yunani Koine, ketiadaan artikel maskulin 'ὁ' menunjukkan sifat kualitatif (predikatif), bukan identitas numerik dengan Bapa (τὸν θεόν di 1:1b). Simak pembuktian lengkapnya di panggung arena debat!",
                "🎵 ZUMA Ambient Dialectics • Suara Nalar",
                "https://actions.google.com/sounds/v1/ambiences/humming_meditation.ogg",
                "#Yohanes1 #CodexSinaiticus #Monoteisme #DialektikaPolya #FilologiYunani",
                248,
                34,
                "2026-09-13 05:30:00"
            ),
            (
                "post_ahmad_2",
                "user_ahmad",
                "Ahmad_Debater",
                "https://api.dicebear.com/7.x/avataaars/svg?seed=Ahmad",
                "🎙️ Debater Tamu",
                "video",
                "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "🔥 Momen tektokan debat panas semalam di panggung Polya Arena! Pembuktian 1 Korintus 8:6 'bagi kita hanya ada satu Allah saja, yaitu Bapa' mematahkan argumen pluralitas ontologis. Simak videonya!",
                "🎵 Epic Middle Eastern Oud • Suara Kebenaran",
                "https://actions.google.com/sounds/v1/science_fiction/deep_pulse_drone.ogg",
                "#1Korintus8 #ArenaDebat #PolyaLive #Tektokan #Monoteisme",
                189,
                21,
                "2026-09-13 04:15:00"
            ),
            (
                "post_markus_3",
                "user_markus",
                "Markus_P",
                "https://api.dicebear.com/7.x/avataaars/svg?seed=Markus",
                "🏛️ Pengkaji Biblika",
                "photo",
                "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?auto=format&fit=crop&w=1200&q=80",
                "📜 Naskah Gulungan Laut Mati (Dead Sea Scrolls 1QIsa): Teks Yesaya 43:10 'Sebelum-Ku tidak ada Allah dibentuk, dan sesudah-Ku tidak akan ada pula'. Penegasan monoteisme mutlak tanpa subordinasi. Bagaimana pandangan rekan-rekan di room debat?",
                "🎵 Ancient Temple Strings • Meditasi Naskah",
                "https://actions.google.com/sounds/v1/ambiences/gentle_rain.ogg",
                "#DeadSeaScrolls #Yesaya43 #MonoteismeMutlak #NaskahKuno",
                132,
                18,
                "2026-09-13 03:00:00"
            )
        ]
        for p in seed_posts:
            cursor.execute("""
            INSERT INTO social_posts (
                id, user_id, user_name, user_avatar, user_badge, media_type, media_url,
                caption, music_title, music_url, tags, likes_count, comments_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, p)

        seed_comments = [
            ("comm_1", "post_zuma_1", "user_ahmad", "Ahmad_Debater", "https://api.dicebear.com/7.x/avataaars/svg?seed=Ahmad", "Analisis yang sangat presisi! Kaidah Colwell sering disalahpahami oleh apologet pemula.", "2026-09-13 05:35:00"),
            ("comm_2", "post_zuma_1", "user_yohanes", "Yohanes_D", "https://api.dicebear.com/7.x/avataaars/svg?seed=Yohanes", "Bagaimana dengan konstruksi Harner (1973) mengenai predikat anarthrous?", "2026-09-13 05:42:00"),
            ("comm_3", "post_ahmad_2", "user_markus", "Markus_P", "https://api.dicebear.com/7.x/avataaars/svg?seed=Markus", "Debat semalam seru sekali, tektokannya sangat cepat dan berbasis nomor ayat.", "2026-09-13 04:30:00")
        ]
        for c in seed_comments:
            cursor.execute("""
            INSERT INTO social_comments (id, post_id, user_id, user_name, user_avatar, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, c)

        seed_stories = [
            ("story_1", "zuma_ai", "Polya ZUMA", "https://api.dicebear.com/7.x/bottts/svg?seed=Zuma", "🔴 Live Panggung Terbuka! Silakan naik ke Kursi 1-5 untuk uji dogma teks.", "", "text", "from-purple-600 via-indigo-600 to-blue-600", "2026-09-13 06:00:00"),
            ("story_2", "user_ahmad", "Ahmad", "https://api.dicebear.com/7.x/avataaars/svg?seed=Ahmad", "📚 Menyiapkan data varian tekstual Markus 1:1 untuk sesi malam ini.", "", "text", "from-amber-500 via-orange-600 to-red-600", "2026-09-13 05:45:00"),
            ("story_3", "user_markus", "Markus", "https://api.dicebear.com/7.x/avataaars/svg?seed=Markus", "💬 Pertanyaan Socratic ZUMA kemarin sangat tajam. Menarik untuk dibedah ulang.", "", "text", "from-emerald-500 via-teal-600 to-cyan-600", "2026-09-13 05:15:00"),
            ("story_4", "user_yohanes", "Yohanes", "https://api.dicebear.com/7.x/avataaars/svg?seed=Yohanes", "🎙️ Standby di antrean panggung open mic!", "", "text", "from-rose-500 via-pink-600 to-purple-600", "2026-09-13 04:50:00")
        ]
        for st in seed_stories:
            cursor.execute("""
            INSERT INTO social_stories (id, user_id, user_name, user_avatar, content, media_url, media_type, bg_gradient, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, st)

    conn.commit()
    conn.close()

init_arena_db()

# ---------------------------------------------------------------------------
# Arena State & Connection Manager
# ---------------------------------------------------------------------------
class ArenaManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.moderator_active: bool = False # Temporarily disabled so human debaters speak without AI interruption

        # Referee & Moderator Entity (Polya System)
        self.referee = {
            "user_id": "polya_referee",
            "name": "Polya (Wasit & Moderator)",
            "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=PolyaReferee",
            "role": "referee_moderator",
            "is_speaking": False,
            "status": "standby_passive",
            "title": "⚖️ Wasit & Moderator (Mendengarkan Diskusi Bebas Tanpa Jeda)"
        }

        # 6 Seats Stage for 3 vs 3:
        # Seats 0..2 = Tim Biru (Team A), Seats 3..5 = Tim Merah (Team B)
        self.seats = [
            # TIM BIRU (Kubu A) - 3 Kursi
            {
                "seat_id": 0,
                "team": "team_a",
                "team_label": "Tim Biru",
                "pos": 1,
                "user_id": None,
                "name": "Kursi 1 (Tim Biru)",
                "avatar": "",
                "role": "debater",
                "is_speaking": False,
                "is_muted": False,
                "time_remaining": 0,
                "status": "empty"
            },
            {
                "seat_id": 1,
                "team": "team_a",
                "team_label": "Tim Biru",
                "pos": 2,
                "user_id": None,
                "name": "Kursi 2 (Tim Biru)",
                "avatar": "",
                "role": "debater",
                "is_speaking": False,
                "is_muted": False,
                "time_remaining": 0,
                "status": "empty"
            },
            {
                "seat_id": 2,
                "team": "team_a",
                "team_label": "Tim Biru",
                "pos": 3,
                "user_id": None,
                "name": "Kursi 3 (Tim Biru)",
                "avatar": "",
                "role": "debater",
                "is_speaking": False,
                "is_muted": False,
                "time_remaining": 0,
                "status": "empty"
            },
            # TIM MERAH (Kubu B) - 3 Kursi
            {
                "seat_id": 3,
                "team": "team_b",
                "team_label": "Tim Merah",
                "pos": 1,
                "user_id": None,
                "name": "Kursi 1 (Tim Merah)",
                "avatar": "",
                "role": "debater",
                "is_speaking": False,
                "is_muted": False,
                "time_remaining": 0,
                "status": "empty"
            },
            {
                "seat_id": 4,
                "team": "team_b",
                "team_label": "Tim Merah",
                "pos": 2,
                "user_id": None,
                "name": "Kursi 2 (Tim Merah)",
                "avatar": "",
                "role": "debater",
                "is_speaking": False,
                "is_muted": False,
                "time_remaining": 0,
                "status": "empty"
            },
            {
                "seat_id": 5,
                "team": "team_b",
                "team_label": "Tim Merah",
                "pos": 3,
                "user_id": None,
                "name": "Kursi 3 (Tim Merah)",
                "avatar": "",
                "role": "debater",
                "is_speaking": False,
                "is_muted": False,
                "time_remaining": 0,
                "status": "empty"
            }
        ]

        self.queue: List[Dict] = []
        self.current_topic = "Debat 3 vs 3: Diskusi Terbuka Bebas Tanpa Jeda Waktu"
        self.pk_state = {
            "active": True,
            "mode": "3vs3",
            "topic": "Debat 3 vs 3: Tim Biru vs Tim Merah",
            "left_seat": 0,
            "left_name": "Tim Biru (3 Debater)",
            "left_score": 1420,
            "left_donations": 350000,
            "right_seat": 3,
            "right_name": "Tim Merah (3 Debater)",
            "right_score": 980,
            "right_donations": 275000,
            "round_seconds": 180,
            "seconds_remaining": 165
        }
        self.current_evidence = {
            "verse": "Yohanes 1:1 & 1 Korintus 8:6",
            "hebrew_greek": "Ἐν ἀρχῇ ἦν ὁ λόγος ... καὶ θεὸς ἦν ὁ λόγος (John 1:1) / εἷς θεὸς ὁ πατήρ (1 Cor 8:6)",
            "manuscripts": "Codex Sinaiticus (א), Codex Vaticanus (B), Papirus 66 (𝔓⁶⁶)",
            "analysis": "Kaidah Gramatika Colwell & Predikat Tanpa Artikel (Anarthrous Predicate Noun)"
        }
        self.simulated_viewers_base = random.randint(12000, 19000)
        self.is_free_mode = True # Default to Free Open Mic Mode (No time limit)

    def toggle_free_mode(self, enabled: Optional[bool] = None) -> bool:
        if enabled is None:
            self.is_free_mode = not self.is_free_mode
        else:
            self.is_free_mode = enabled
        for s in self.seats:
            if self.is_free_mode:
                s["is_muted"] = False
                s["time_remaining"] = 999
        return self.is_free_mode

    async def timer_loop(self):
        """Ticks every second to decrement PK battle round and speaking timers."""
        while True:
            await asyncio.sleep(1)
            try:
                if not self.is_free_mode:
                    # 1. PK Battle Timer Countdown (Only in structured mode)
                    if self.pk_state.get("active", True):
                        current_sec = self.pk_state.get("seconds_remaining", 180) - 1
                        if current_sec <= 0:
                            current_sec = 180 # Reset next round
                        self.pk_state["seconds_remaining"] = current_sec

                    # 2. Speaking Seats Countdown
                    for s in self.seats:
                        if s["status"] == "occupied" and s.get("is_speaking", False):
                            rem = s.get("time_remaining", 90) - 1
                            if rem <= 0:
                                s["is_speaking"] = False
                                s["time_remaining"] = 90
                            else:
                                s["time_remaining"] = rem
                else:
                    # In Free Mode: all occupied seats unmuted, infinite time
                    for s in self.seats:
                        if s["status"] == "occupied":
                            s["is_muted"] = False

                # 3. Broadcast sync every second if viewers are connected
                if self.active_connections:
                    await self.broadcast_state()
            except Exception as e:
                logger.debug(f"Timer tick error: {e}")

    def kick_seat(self, seat_id: int):
        for s in self.seats:
            if s["seat_id"] == seat_id and s["status"] == "occupied":
                kicked_name = s["name"]
                s["user_id"] = None
                s["name"] = f"Kursi {s.get('pos', seat_id + 1)} ({s.get('team_label', 'Debater')})"
                s["avatar"] = ""
                s["role"] = "debater"
                s["is_speaking"] = False
                s["is_muted"] = False
                s["time_remaining"] = 0
                s["status"] = "empty"
                return kicked_name
        return None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Active WS: {len(self.active_connections)}")
        await self.broadcast_state()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Active WS: {len(self.active_connections)}")

    def get_online_viewers(self) -> int:
        delta = random.randint(-12, 12)
        self.simulated_viewers_base = max(12000, min(19000, self.simulated_viewers_base + delta))
        return self.simulated_viewers_base + len(self.active_connections)

    def get_full_state(self) -> Dict:
        return {
            "type": "ARENA_STATE_SYNC",
            "viewers": self.get_online_viewers(),
            "referee": self.referee,
            "seats": self.seats,
            "queue_count": len(self.queue),
            "queue": self.queue,
            "topic": self.current_topic,
            "pk_state": self.pk_state,
            "evidence": self.current_evidence,
            "is_free_mode": self.is_free_mode
        }

    async def broadcast_state(self):
        payload = json.dumps(self.get_full_state())
        await self.broadcast_raw(payload)

    async def broadcast_raw(self, message: str):
        dead_sockets = []
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead_sockets.append(ws)
        for dead in dead_sockets:
            self.disconnect(dead)

    async def broadcast_chat(self, chat_data: Dict):
        payload = json.dumps({
            "type": "NEW_CHAT_MESSAGE",
            "chat": chat_data
        })
        await self.broadcast_raw(payload)

    async def broadcast_donation_alert(self, alert_data: Dict):
        payload = json.dumps({
            "type": "LIVE_DONATION_ALERT",
            "alert": alert_data
        })
        await self.broadcast_raw(payload)

    async def broadcast_tap_reaction(self, reaction_type: str):
        payload = json.dumps({
            "type": "TAP_REACTION",
            "reaction": reaction_type
        })
        await self.broadcast_raw(payload)

    async def broadcast_voice_audio(self, voice_data: Dict, exclude_ws: Optional[WebSocket] = None):
        payload = json.dumps({
            "type": "USER_VOICE_AUDIO",
            "audio": voice_data
        })
        dead_sockets = []
        for ws in self.active_connections:
            if ws != exclude_ws:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_sockets.append(ws)
        for dead in dead_sockets:
            self.disconnect(dead)

    def is_user_on_stage(self, user_id: str) -> bool:
        if not user_id:
            return False
        for s in self.seats:
            if s["status"] == "occupied" and s.get("user_id") == user_id:
                return True
        return False

    def join_queue(self, user: Dict) -> int:
        if not user or not user.get("user_id"):
            return 0
        # If user is already on stage, do not queue them again
        if self.is_user_on_stage(user["user_id"]):
            return 0
        for idx, q in enumerate(self.queue):
            if q.get("user_id") == user["user_id"]:
                return idx + 1
        self.queue.append(user)
        return len(self.queue)

    def leave_queue(self, user_id: str):
        self.queue = [q for q in self.queue if q.get("user_id") != user_id]

    def assign_next_to_seat(self) -> Optional[Dict]:
        for i in range(0, 6):
            if self.seats[i]["status"] == "empty" and self.queue:
                while self.queue:
                    next_user = self.queue.pop(0)
                    if not self.is_user_on_stage(next_user.get("user_id")):
                        team_type = "team_a" if i < 3 else "team_b"
                        team_lbl = "Tim Biru" if i < 3 else "Tim Merah"
                        pos_num = (i % 3) + 1
                        self.seats[i] = {
                            "seat_id": i,
                            "team": team_type,
                            "team_label": team_lbl,
                            "pos": pos_num,
                            "user_id": next_user.get("user_id"),
                            "name": next_user.get("name"),
                            "avatar": next_user.get("avatar_url", ""),
                            "role": "debater",
                            "is_speaking": False,
                            "is_muted": False,
                            "time_remaining": 90,
                            "status": "occupied"
                        }
                        return self.seats[i]
        return None

arena_manager = ArenaManager()

# ---------------------------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------------------------

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None

@app.post("/api/auth/google")
async def google_auth(req: GoogleAuthRequest):
    # Enforce verified Google ID token / provider assertion
    verified = None
    if req.credential:
        verified = GoogleAuthVerifier.verify_credential(req.credential)

    if not verified:
        raise HTTPException(status_code=401, detail="Google authentication failed: invalid or missing ID token credential")

    email = verified["email"]
    name = verified.get("name") or req.name or "Google User"
    avatar = verified.get("avatar_url") or req.avatar_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}"
    google_sub = verified.get("sub", "")

    # Consistent canonical identity mapping across routes anchored to provider subject
    user_id = f"usr_{uuid.uuid5(uuid.NAMESPACE_URL, f'google:{google_sub}').hex[:12]}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM arena_users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        # Check if user with same email exists under older schema, link if found
        cursor.execute("SELECT * FROM arena_users WHERE email = ?", (email,))
        email_row = cursor.fetchone()
        if email_row:
            user_id = email_row["user_id"]
            row = email_row
        else:
            cursor.execute("""
            INSERT INTO arena_users (user_id, email, name, avatar_url, bio, role, created_at)
            VALUES (?, ?, ?, ?, ?, 'visitor', datetime('now'))
            """, (user_id, email, name, avatar, "Pengunjung Dialectical Arena"))
            cursor.execute("""
            INSERT OR IGNORE INTO arena_wallet_balances (user_id, balance_net, total_withdrawn, updated_at)
            VALUES (?, 0, 0, datetime('now'))
            """, (user_id,))
            conn.commit()
            cursor.execute("SELECT * FROM arena_users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
    else:
        # Update user details if email or name updated at provider, preserving user_id and role
        cursor.execute("""
        UPDATE arena_users
        SET email = ?, name = COALESCE(?, name), avatar_url = COALESCE(?, avatar_url)
        WHERE user_id = ?
        """, (email, name, avatar, user_id))
        conn.commit()
        cursor.execute("SELECT * FROM arena_users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

    user_data = dict(row)
    conn.close()

    # Issue signed session token based on server-policy role
    token = SessionService.create_token(user_id, role=user_data.get("role", "visitor"))
    return {"status": "ok", "user": user_data, "session_token": token}


class UpdateProfileRequest(BaseModel):
    user_id: Optional[str] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    dana: Optional[str] = None
    gopay: Optional[str] = None
    shopeepay: Optional[str] = None
    ovo: Optional[str] = None

@app.post("/api/profile/update")
async def update_profile(
    req: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    target_user_id = req.user_id or current_user_id
    if target_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: cannot update another user's profile")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE arena_users
    SET name = COALESCE(?, name),
        bio = COALESCE(?, bio),
        dana = COALESCE(?, dana),
        gopay = COALESCE(?, gopay),
        shopeepay = COALESCE(?, shopeepay),
        ovo = COALESCE(?, ovo)
    WHERE user_id = ?
    """, (req.name, req.bio, req.dana, req.gopay, req.shopeepay, req.ovo, current_user_id))
    conn.commit()
    cursor.execute("SELECT * FROM arena_users WHERE user_id = ?", (current_user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok", "user": dict(row)}


class DonationRequest(BaseModel):
    donor_user_id: Optional[str] = None
    donor_name: Optional[str] = "Debater Supporter"
    donor_avatar: Optional[str] = None
    recipient_user_id: str
    gross_amount: int
    payment_method: str  # DANA, GOPAY, SHOPEEPAY, OVO, QRIS
    message: Optional[str] = ""

@app.post("/api/donate")
async def process_donation(
    req: DonationRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    # Enforce donor authentication: donor cannot forge another user's identity
    effective_donor_user_id = current_user_id
    if req.donor_user_id and req.donor_user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: cannot process donation on behalf of another donor")

    if req.gross_amount <= 0:
        raise HTTPException(status_code=400, detail="Nominal donasi harus lebih besar dari 0")

    # 10% Platform Fee, 90% Debater Net
    platform_fee = int(req.gross_amount * 0.10)
    recipient_net = req.gross_amount - platform_fee
    trx_id = f"TRX-{int(time.time())}-{uuid.uuid4().hex[:4].upper()}"

    conn = get_db()
    cursor = conn.cursor()

    # Check recipient
    cursor.execute("SELECT name FROM arena_users WHERE user_id = ?", (req.recipient_user_id,))
    rec = cursor.fetchone()
    recipient_name = rec["name"] if rec else "Debater"

    # Record transaction with authenticated donor
    cursor.execute("""
    INSERT INTO arena_donations (
        id, donor_user_id, donor_name, donor_avatar, recipient_user_id, recipient_name,
        gross_amount, platform_fee_10pct, recipient_net_90pct, payment_method, message, status, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PAID', datetime('now'))
    """, (
        trx_id, effective_donor_user_id, req.donor_name, req.donor_avatar,
        req.recipient_user_id, recipient_name, req.gross_amount,
        platform_fee, recipient_net, req.payment_method, req.message
    ))

    # Update recipient balance & total received
    cursor.execute("""
    UPDATE arena_users
    SET total_donations_received = total_donations_received + ?
    WHERE user_id = ?
    """, (recipient_net, req.recipient_user_id))

    cursor.execute("""
    UPDATE arena_wallet_balances
    SET balance_net = balance_net + ?, updated_at = datetime('now')
    WHERE user_id = ?
    """, (recipient_net, req.recipient_user_id))

    # Update platform treasury pool (10%)
    cursor.execute("""
    UPDATE arena_platform_treasury
    SET total_fee_collected = total_fee_collected + ?, updated_at = datetime('now')
    WHERE id = 1
    """, (platform_fee,))

    conn.commit()
    conn.close()

    # Accumulate into live debater donation totals for PK HUD
    if req.recipient_user_id == "zuma_ai" or "zuma" in recipient_name.lower():
        arena_manager.pk_state["left_donations"] = arena_manager.pk_state.get("left_donations", 0) + req.gross_amount
    else:
        arena_manager.pk_state["right_donations"] = arena_manager.pk_state.get("right_donations", 0) + req.gross_amount

    # Broadcast Live Sawer Alert to all viewers
    alert_payload = {
        "id": trx_id,
        "donor_name": req.donor_name,
        "donor_avatar": req.donor_avatar or "https://api.dicebear.com/7.x/avataaars/svg?seed=" + req.donor_name,
        "recipient_name": recipient_name,
        "gross_amount": req.gross_amount,
        "recipient_net": recipient_net,
        "payment_method": req.payment_method,
        "message": req.message
    }
    asyncio.create_task(arena_manager.broadcast_donation_alert(alert_payload))

    # Also inject a system highlight message into chat
    system_chat = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "user_id": "system",
        "user_name": "🎉 SAWER ALERT",
        "user_avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=gift",
        "message": f"{req.donor_name} mendonasikan Rp {req.gross_amount:,} ({req.payment_method}) untuk {recipient_name}: \"{req.message}\"",
        "is_system": 1,
        "timestamp": time.strftime("%H:%M")
    }
    asyncio.create_task(arena_manager.broadcast_chat(system_chat))

    return {
        "status": "ok",
        "transaction_id": trx_id,
        "gross_amount": req.gross_amount,
        "platform_fee_10pct": platform_fee,
        "recipient_net_90pct": recipient_net,
        "recipient_name": recipient_name
    }


@app.get("/api/user/{user_id}/wallet")
async def get_user_wallet(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: cannot access another user's wallet")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM arena_users WHERE user_id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("SELECT * FROM arena_wallet_balances WHERE user_id = ?", (user_id,))
    wallet_row = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM arena_donations
    WHERE recipient_user_id = ? OR donor_user_id = ?
    ORDER BY timestamp DESC LIMIT 20
    """, (user_id, user_id))
    trx_rows = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT total_fee_collected FROM arena_platform_treasury WHERE id = 1")
    treasury_row = cursor.fetchone()

    conn.close()

    return {
        "user": dict(user_row),
        "balance_net": wallet_row["balance_net"] if wallet_row else 0,
        "total_withdrawn": wallet_row["total_withdrawn"] if wallet_row else 0,
        "platform_treasury_pool": treasury_row["total_fee_collected"] if treasury_row else 0,
        "transactions": trx_rows
    }


@app.get("/api/corpus/search")
async def search_corpus(q: str):
    corpus_db = os.environ.get("POLYA_INDEX_DB_PATH", "/home/ubuntu/.polya/polya_index.db")
    if not os.path.exists(corpus_db):
        corpus_db = DB_PATH
    conn = sqlite3.connect(corpus_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute("""
        SELECT v.video_id, v.title, v.url, v.primary_theme as speaker, 0 as duration
        FROM youtube_catalog_fts f
        JOIN youtube_catalog v ON f.rowid = v.rowid
        WHERE youtube_catalog_fts MATCH ?
        LIMIT 10
        """, (f"{q}*",))
        results = [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        logger.warning(f"FTS search fallback: {e}")
        cursor.execute("""
        SELECT video_id, title, url, primary_theme as speaker, 0 as duration
        FROM youtube_catalog
        WHERE title LIKE ? OR primary_theme LIKE ?
        LIMIT 10
        """, (f"%{q}%", f"%{q}%"))
        results = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"query": q, "count": len(results), "results": results}


@app.post("/api/voice/transcribe")
async def handle_voice_transcribe(file: UploadFile = File(...), language: Optional[str] = None):
    try:
        content = await file.read()
        transcript = await transcribe_audio_groq(content, filename=file.filename or "voice.webm", language=language)
        return {"success": True, "text": transcript}
    except Exception as e:
        logger.error(f"Voice transcribe error: {e}")
        return {"success": False, "error": str(e), "text": ""}


# ---------------------------------------------------------------------------
# Social Media Feed, Reels & Stories Endpoints (Instagram / TikTok Style)
# ---------------------------------------------------------------------------
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class CreateSocialPostRequest(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    author_name: Optional[str] = None
    user_avatar: Optional[str] = None
    author_avatar: Optional[str] = None
    user_badge: Optional[str] = "Debater"
    author_badge: Optional[str] = "Debater"
    media_type: Optional[str] = "photo"  # photo, video, text, audio
    media_url: Optional[str] = ""
    caption: Optional[str] = ""
    content: Optional[str] = ""
    music_title: Optional[str] = ""
    music_url: Optional[str] = ""
    tags: Optional[str] = ""


class LikePostRequest(BaseModel):
    user_id: str


class CreateSocialCommentRequest(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    author_name: Optional[str] = None
    user_avatar: Optional[str] = None
    author_avatar: Optional[str] = None
    comment: Optional[str] = None
    content: Optional[str] = None


class CreateStoryRequest(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    author_name: Optional[str] = None
    user_avatar: Optional[str] = None
    author_avatar: Optional[str] = None
    content: Optional[str] = ""
    caption: Optional[str] = ""
    media_url: Optional[str] = ""
    media_type: Optional[str] = "text"
    bg_gradient: Optional[str] = "from-purple-600 via-indigo-600 to-blue-600"


@app.post("/api/feed/upload")
async def handle_feed_upload(file: UploadFile = File(...)):
    """Uploads compressed photo, video or audio file for social media feed."""
    try:
        ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
        unique_name = f"up_{uuid.uuid4().hex[:10]}{ext}"
        target_path = os.path.join(UPLOAD_DIR, unique_name)

        with open(target_path, "wb") as f:
            content = await file.read()
            f.write(content)

        url = f"/static/uploads/{unique_name}"

        # Determine media type
        media_type = "photo"
        if ext in [".mp4", ".webm", ".ogg", ".mov"]:
            media_type = "video"
        elif ext in [".mp3", ".wav", ".m4a", ".aac"]:
            media_type = "audio"

        return {
            "success": True,
            "url": url,
            "media_type": media_type,
            "filename": unique_name,
            "size": len(content)
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "detail": str(e)})


@app.get("/api/feed")
async def get_social_feed(tab: str = "all", user_id: Optional[str] = None, limit: int = 25, offset: int = 0):
    """Retrieves social media feed filtered by tab (all, media, video, status)."""
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = []
    if tab == "media":
        where_clauses.append("media_type = 'photo'")
    elif tab == "video":
        where_clauses.append("media_type = 'video'")
    elif tab == "status":
        where_clauses.append("media_type = 'text'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT p.*,
           EXISTS(SELECT 1 FROM social_likes l WHERE l.post_id = p.id AND l.user_id = ?) as has_liked
    FROM social_posts p
    {where_sql}
    ORDER BY p.created_at DESC
    LIMIT ? OFFSET ?
    """
    params = [user_id or "", limit, offset]
    cursor.execute(query, params)
    raw_posts = [dict(r) for r in cursor.fetchall()]

    posts = []
    for post in raw_posts:
        post["has_liked"] = bool(post.get("has_liked", 0))
        # Sync field aliases for frontend compatibility
        post["post_id"] = post["id"]
        post["author_name"] = post["user_name"]
        post["author_avatar"] = post["user_avatar"]
        post["author_badge"] = post["user_badge"]
        post["content"] = post["caption"]
        post["like_count"] = post["likes_count"]
        post["comment_count"] = post["comments_count"]
        post["timestamp"] = post["created_at"]

        cursor.execute("""
        SELECT * FROM social_comments WHERE post_id = ? ORDER BY created_at ASC LIMIT 3
        """, (post["id"],))
        comments_raw = [dict(c) for c in cursor.fetchall()]
        recent_comments = []
        for c in comments_raw:
            c["content"] = c["comment"]
            c["timestamp"] = c["created_at"]
            recent_comments.append(c)
        post["top_comments"] = recent_comments
        post["recent_comments"] = recent_comments
        posts.append(post)

    conn.close()
    return {"status": "ok", "posts": posts}


@app.post("/api/feed/post")
async def create_social_post(req: CreateSocialPostRequest):
    """Creates a new Instagram/TikTok style post with optional compressed photo/video and music track."""
    post_id = f"post_{uuid.uuid4().hex[:8]}"
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")
    name = req.user_name or req.author_name or "Debater"
    avatar = req.user_avatar or req.author_avatar or f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}"
    badge = req.user_badge or req.author_badge or "Debater"
    caption_text = req.caption or req.content or ""

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO social_posts (
        id, user_id, user_name, user_avatar, user_badge, media_type, media_url,
        caption, music_title, music_url, tags, likes_count, comments_count, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
    """, (
        post_id, req.user_id, name, avatar, badge,
        req.media_type or "photo", req.media_url or "", caption_text, req.music_title or "",
        req.music_url or "", req.tags or "", created_at
    ))
    conn.commit()
    cursor.execute("SELECT * FROM social_posts WHERE id = ?", (post_id,))
    row = dict(cursor.fetchone())
    row["has_liked"] = False
    row["post_id"] = row["id"]
    row["author_name"] = row["user_name"]
    row["author_avatar"] = row["user_avatar"]
    row["content"] = row["caption"]
    row["like_count"] = 0
    row["comment_count"] = 0
    row["top_comments"] = []
    row["recent_comments"] = []
    row["timestamp"] = row["created_at"]
    conn.close()

    return {"status": "ok", "success": True, "post": row}


@app.post("/api/feed/like/{post_id}")
async def toggle_post_like(post_id: str, req: LikePostRequest):
    """Toggles like on a post and returns updated count."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM social_likes WHERE user_id = ? AND post_id = ?", (req.user_id, post_id))
    already_liked = cursor.fetchone()

    if already_liked:
        cursor.execute("DELETE FROM social_likes WHERE user_id = ? AND post_id = ?", (req.user_id, post_id))
        cursor.execute("UPDATE social_posts SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (post_id,))
        has_liked = False
        action = "unliked"
    else:
        cursor.execute("INSERT INTO social_likes (user_id, post_id, created_at) VALUES (?, ?, datetime('now'))", (req.user_id, post_id))
        cursor.execute("UPDATE social_posts SET likes_count = likes_count + 1 WHERE id = ?", (post_id,))
        has_liked = True
        action = "liked"

    conn.commit()
    cursor.execute("SELECT likes_count FROM social_posts WHERE id = ?", (post_id,))
    res = cursor.fetchone()
    likes_count = res["likes_count"] if res else 0
    conn.close()

    return {"status": "ok", "success": True, "has_liked": has_liked, "action": action, "like_count": likes_count, "likes_count": likes_count}


@app.get("/api/feed/comments/{post_id}")
async def get_post_comments(post_id: str):
    """Gets all comments for a post in Instagram style."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM social_comments WHERE post_id = ? ORDER BY created_at ASC
    """, (post_id,))
    comments_raw = [dict(r) for r in cursor.fetchall()]
    comments = []
    for c in comments_raw:
        c["content"] = c["comment"]
        c["timestamp"] = c["created_at"]
        comments.append(c)
    conn.close()
    return {"status": "ok", "success": True, "comments": comments}


@app.post("/api/feed/comments/{post_id}")
async def add_post_comment(post_id: str, req: CreateSocialCommentRequest):
    """Adds a comment to a post."""
    comment_id = f"comm_{uuid.uuid4().hex[:8]}"
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")
    name = req.user_name or req.author_name or "Debater"
    avatar = req.user_avatar or req.author_avatar or f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}"
    comment_text = req.comment or req.content or ""

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO social_comments (id, post_id, user_id, user_name, user_avatar, comment, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (comment_id, post_id, req.user_id, name, avatar, comment_text, created_at))

    cursor.execute("UPDATE social_posts SET comments_count = comments_count + 1 WHERE id = ?", (post_id,))
    conn.commit()

    cursor.execute("SELECT * FROM social_comments WHERE id = ?", (comment_id,))
    new_comment = dict(cursor.fetchone())
    new_comment["content"] = new_comment["comment"]
    new_comment["timestamp"] = new_comment["created_at"]
    cursor.execute("SELECT comments_count FROM social_posts WHERE id = ?", (post_id,))
    cnt_row = cursor.fetchone()
    conn.close()

    return {"status": "ok", "success": True, "comment": new_comment, "comment_count": cnt_row["comments_count"] if cnt_row else 1, "comments_count": cnt_row["comments_count"] if cnt_row else 1}


@app.get("/api/feed/stories")
async def get_stories():
    """Gets active stories/status row."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM social_stories ORDER BY created_at DESC LIMIT 20
    """)
    stories_raw = [dict(r) for r in cursor.fetchall()]
    stories = []
    for s in stories_raw:
        s["author_name"] = s["user_name"]
        s["author_avatar"] = s["user_avatar"]
        s["timestamp"] = s["created_at"]
        stories.append(s)
    conn.close()
    return {"status": "ok", "success": True, "stories": stories}


@app.post("/api/feed/stories")
async def create_story(req: CreateStoryRequest):
    """Creates a new status/story."""
    story_id = f"story_{uuid.uuid4().hex[:8]}"
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")
    name = req.user_name or req.author_name or "Debater"
    avatar = req.user_avatar or req.author_avatar or f"https://api.dicebear.com/7.x/avataaars/svg?seed={name}"
    content_text = req.content or req.caption or ""

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO social_stories (id, user_id, user_name, user_avatar, content, media_url, media_type, bg_gradient, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (story_id, req.user_id, name, avatar, content_text, req.media_url or "", req.media_type or "text", req.bg_gradient or "from-purple-600 via-indigo-600 to-blue-600", created_at))
    conn.commit()
    cursor.execute("SELECT * FROM social_stories WHERE id = ?", (story_id,))
    row = dict(cursor.fetchone())
    row["author_name"] = row["user_name"]
    row["author_avatar"] = row["user_avatar"]
    row["timestamp"] = row["created_at"]
    conn.close()

    return {"status": "ok", "success": True, "story": row}


# ---------------------------------------------------------------------------
# WebSocket Arena Connection
# ---------------------------------------------------------------------------
@app.websocket("/ws/arena")
async def websocket_arena(websocket: WebSocket):
    await arena_manager.connect(websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                msg_type = msg.get("type")

                if msg_type == "SEND_CHAT":
                    chat_id = f"msg_{uuid.uuid4().hex[:8]}"
                    timestamp_str = time.strftime("%H:%M")
                    chat_obj = {
                        "id": chat_id,
                        "user_id": msg.get("user_id", "guest"),
                        "user_name": msg.get("user_name", "Visitor"),
                        "user_avatar": msg.get("user_avatar", "https://api.dicebear.com/7.x/avataaars/svg?seed=guest"),
                        "message": msg.get("message", ""),
                        "is_system": 0,
                        "timestamp": timestamp_str
                    }
                    # Save to DB
                    conn = get_db()
                    conn.execute("""
                    INSERT INTO arena_chat_messages (id, user_id, user_name, user_avatar, message, is_system, timestamp)
                    VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
                    """, (chat_id, chat_obj["user_id"], chat_obj["user_name"], chat_obj["user_avatar"], chat_obj["message"]))
                    conn.commit()
                    conn.close()

                    await arena_manager.broadcast_chat(chat_obj)

                    # If moderator is active, Polya AI actively provides ruling; otherwise human debaters speak uninterrupted
                    if arena_manager.moderator_active and chat_obj["user_id"] != "polya_referee" and chat_obj["user_id"] != "zuma_ai" and chat_obj["user_id"] != "system" and chat_obj["message"].strip():
                        asyncio.create_task(generate_ai_rebuttal(chat_obj["message"], chat_obj["user_name"]))

                elif msg_type == "VOICE_PCM_STREAM":
                    pcm_b64 = msg.get("pcm_data", "")
                    sender_id = msg.get("user_id", "debater")
                    sender_name = msg.get("user_name", "Debater")
                    seat_id = msg.get("seat_id", 0)
                    sample_rate = msg.get("sample_rate", 44100)

                    if pcm_b64:
                        payload = json.dumps({
                            "type": "USER_PCM_AUDIO",
                            "user_id": sender_id,
                            "sender_name": sender_name,
                            "seat_id": seat_id,
                            "sample_rate": sample_rate,
                            "pcm_data": pcm_b64
                        })
                        dead_sockets = []
                        for ws in arena_manager.active_connections:
                            if ws != websocket:
                                try:
                                    await ws.send_text(payload)
                                except Exception:
                                    dead_sockets.append(ws)
                        for dead in dead_sockets:
                            arena_manager.disconnect(dead)

                elif msg_type == "VOICE_AUDIO_CHUNK":
                    audio_b64 = msg.get("audio_base64", "")
                    sender_id = msg.get("user_id", "debater")
                    sender_name = msg.get("user_name", "Debater")
                    sender_avatar = msg.get("user_avatar", "https://api.dicebear.com/7.x/avataaars/svg?seed=debater")
                    seat_id = msg.get("seat_id", 1)

                    if audio_b64:
                        # Direct ultra-low latency audio conference pass-through to all debaters & visitors!
                        voice_payload = {
                            "sender_id": sender_id,
                            "sender_name": sender_name,
                            "audio_base64": audio_b64,
                            "seat_id": seat_id
                        }
                        await arena_manager.broadcast_voice_audio(voice_payload, exclude_ws=websocket)

                elif msg_type == "JOIN_QUEUE":
                    user_info = {
                        "user_id": msg.get("user_id"),
                        "name": msg.get("name"),
                        "avatar_url": msg.get("avatar_url")
                    }
                    pos = arena_manager.join_queue(user_info)
                    assigned = arena_manager.assign_next_to_seat()
                    await arena_manager.broadcast_state()

                elif msg_type == "LEAVE_QUEUE":
                    arena_manager.leave_queue(msg.get("user_id"))
                    await arena_manager.broadcast_state()

                elif msg_type == "TAP_REACTION":
                    reaction = msg.get("reaction", "🔥")
                    await arena_manager.broadcast_tap_reaction(reaction)

                elif msg_type == "PK_VOTE":
                    side = msg.get("side") # "left" or "right"
                    if side == "left":
                        arena_manager.pk_state["left_score"] += 10
                    elif side == "right":
                        arena_manager.pk_state["right_score"] += 10
                    await arena_manager.broadcast_state()

                elif msg_type == "TRIGGER_SPEAKING":
                    seat_id = msg.get("seat_id")
                    user_id = msg.get("user_id")
                    is_spk = bool(msg.get("is_speaking", True))
                    if seat_id is not None and seat_id >= 0:
                        for s in arena_manager.seats:
                            if s["seat_id"] == seat_id:
                                s["is_speaking"] = is_spk
                    elif user_id:
                        for s in arena_manager.seats:
                            if s.get("user_id") == user_id:
                                s["is_speaking"] = is_spk
                    await arena_manager.broadcast_state()

                elif msg_type == "KICK_SEAT":
                    seat_id = msg.get("seat_id")
                    if seat_id is not None:
                        kicked = arena_manager.kick_seat(seat_id)
                        if kicked:
                            kick_chat = {
                                "id": f"msg_{uuid.uuid4().hex[:8]}",
                                "user_id": "system",
                                "user_name": "🛡️ Polya Moderator",
                                "user_avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=Mod",
                                "message": f"{kicked} telah diturunkan dari panggung.",
                                "is_system": 1,
                                "timestamp": time.strftime("%H:%M")
                            }
                            await arena_manager.broadcast_chat(kick_chat)
                        await arena_manager.broadcast_state()

                elif msg_type == "TOGGLE_FREE_MODE":
                    is_on = arena_manager.toggle_free_mode(msg.get("enabled"))
                    sys_msg = {
                        "id": f"msg_{uuid.uuid4().hex[:8]}",
                        "user_id": "system",
                        "user_name": "🛡️ Polya Arena",
                        "user_avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=Mod",
                        "message": "🎙️ Mode Sesi Bebas (Open Mic ♾️) DIAKTIFKAN! Semua mic panggung terbuka tanpa batas waktu. Silakan langsung tektokan argumen!" if is_on else "⏱️ Mode Timer Terstruktur DIAKTIFKAN kembali.",
                        "is_system": 1,
                        "timestamp": time.strftime("%H:%M")
                    }
                    await arena_manager.broadcast_chat(sys_msg)
                    await arena_manager.broadcast_state()

            except Exception as parse_err:
                logger.warning(f"Error handling message: {parse_err}")

    except WebSocketDisconnect:
        arena_manager.disconnect(websocket)
        await arena_manager.broadcast_state()


async def generate_ai_rebuttal(user_message: str, user_name: str):
    """Generates a sharp Persona ZUMA Socratic referee & moderator ruling with Bible citations."""
    clean_sender = user_name.replace("🎙️", "").strip()

    # Fallback pre-crafted moderator response
    ai_rebuttal_text = (
        f"@{clean_sender} [PUTUSAN WASIT]: Dalam debat 3 vs 3 ini, kedua tim wajib bersandar murni pada naskah primer Bible. Perhatikan Yohanes 17:3 di mana Yesus menyebut Bapa sebagai 'satu-satunya Allah yang benar' (τὸν μόνον ἀληθινὸν θεόν), diselaraskan dengan 1 Korintus 8:6. Tim lawan dipersilakan merespons klausa anarthrous pada Yohanes 1:1!"
    )

    # Attempt high-speed LLM generation via Groq Qwen
    if groq_client:
        try:
            prompt_system = (
                "Anda adalah POLYA (WASIT & MODERATOR DEBAT 3 vs 3). Anda memimpin debat dialektika antara Tim Biru (3 Debater) dan Tim Merah (3 Debater). "
                "Posture: wasit objektif, netral, berwibawa, tegas, dingin, tajam, presisi, berlandaskan filologi forensik dan manuskrip naskah kuno. "
                "Tugas Anda:\n"
                "1. Menguji argumen pembicara secara forensik langsung ke teks Bible.\n"
                "2. Menegur kesalahan logika (logical fallacy) atau pergeseran terjemahan naskah kuno.\n"
                "3. Memberikan putusan wasit (Moderator Ruling) dan mengarahkan giliran bicara ke tim lawan.\n"
                "ATURAN MUTLAK:\n"
                "1. Nama kitab/surat di Bible WAJIB LENGKAP tanpa disingkat (contoh: Kejadian, Matius, Markus, Lukas, Yohanes, Kisah Para Rasul, Roma, 1 Korintus, Yesaya, dll).\n"
                "2. Wajib menyertakan nomor pasal dan ayat yang presisi (contoh: Yohanes 1:1, 1 Korintus 8:6, Yohanes 17:3, Yesaya 43:10, Matius 24:4-5).\n"
                "3. Wajib selalu menggunakan sebutan 'Bible' (jangan gunakan istilah lain).\n"
                "4. Dilarang mencantumkan tautan atau rujukan web eksternal.\n"
                "5. Berikan putusan wasit dalam 2-3 kalimat lugas, tegas, dan berwibawa."
            )
            response = groq_client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": f"Debater ({clean_sender}) menyampaikan argumen: '{user_message}'. Berikan evaluasi putusan wasit (Moderator Ruling) dan arahkan tim lawan merespons teks Bible!"}
                ],
                max_tokens=220,
                temperature=0.3
            )
            raw_text = response.choices[0].message.content or ""
            import re
            clean_llm = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
            if clean_llm:
                ai_rebuttal_text = f"@{clean_sender} {clean_llm}"
        except Exception as e:
            logger.warning(f"Groq LLM generation error: {e}")

    # Generate Gemini Indonesian TTS Audio for Polya Referee
    gemini_audio = await generate_gemini_tts(ai_rebuttal_text, voice="Kore")

    ai_chat = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "user_id": "polya_referee",
        "user_name": "⚖️ Polya (Wasit & Moderator)",
        "user_avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=PolyaReferee",
        "message": ai_rebuttal_text,
        "audio_base64": gemini_audio or "",
        "is_system": 0,
        "timestamp": time.strftime("%H:%M")
    }

    # Trigger speaking indicator on referee booth
    arena_manager.referee["is_speaking"] = True
    await arena_manager.broadcast_state()
    # Broadcast chat message with Gemini TTS audio attached (Single execution)
    await arena_manager.broadcast_chat(ai_chat)

    # Reset speaking indicator after reading time
    await asyncio.sleep(6)
    arena_manager.referee["is_speaking"] = False
    await arena_manager.broadcast_state()


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "Kore"


@app.post("/api/tts/gemini")
async def handle_gemini_tts_endpoint(req: TTSRequest):
    """Generates natural Indonesian speech via Gemini API Key."""
    audio_b64 = await generate_gemini_tts(req.text, voice=req.voice or "Kore")
    if audio_b64:
        return {"success": True, "audio_base64": audio_b64}
    return {"success": False, "error": "Gemini TTS generation failed or rate limited"}


@app.post("/api/zuma/speak")
async def trigger_zuma_direct_speak(request: Request):
    data = {}
    try:
        data = await request.json()
    except Exception:
        pass
    prompt = data.get("prompt", "Buka sesi arena debat 3 vs 3 ini sebagai wasit dan moderator objektif berlandaskan Yesaya 43:10 dan 1 Korintus 8:6.")
    asyncio.create_task(generate_ai_rebuttal(prompt, "Host"))
    return {"status": "ok", "message": "Polya Moderator speaking triggered"}


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(arena_manager.timer_loop())

# ---------------------------------------------------------------------------
# Debate Arena 3-vs-3 Master Event UI & REST/WebSocket Endpoints (Prompt 12)
# ---------------------------------------------------------------------------
debate_ws_clients: Set[WebSocket] = set()

async def broadcast_arena_event(event_type: str, data: Dict[str, Any]):
    dead_clients = set()
    message = json.dumps({"type": event_type, "data": data})
    for client in list(debate_ws_clients):
        try:
            await client.send_text(message)
        except Exception:
            dead_clients.add(client)
    for dc in dead_clients:
        debate_ws_clients.discard(dc)

@app.websocket("/api/arena/ws")
async def debate_arena_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    debate_ws_clients.add(websocket)
    try:
        # Send initial state immediately
        await websocket.send_text(json.dumps({
            "type": "STATE_UPDATE",
            "data": arena_service.get_full_state()
        }))
        while True:
            raw_msg = await websocket.receive_text()
            try:
                msg_data = json.loads(raw_msg)
                action = msg_data.get("action")
                if action:
                    ok, resp_msg, state = arena_service.execute_operator_action(msg_data)
                    await broadcast_arena_event("STATE_UPDATE", state)
            except Exception as e:
                logger.warning(f"Error handling debate websocket message: {e}")
    except WebSocketDisconnect:
        debate_ws_clients.discard(websocket)
    except Exception as e:
        logger.warning(f"Debate websocket error: {e}")
        debate_ws_clients.discard(websocket)

@app.get("/api/arena/state")
async def get_debate_arena_state():
    """Returns authoritative 100% engine state for UI visualization."""
    return JSONResponse(arena_service.get_full_state())

@app.post("/api/arena/action")
async def execute_debate_arena_action(request: Request):
    """Executes a debate action through referee and state machine."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    ok, msg, state = arena_service.execute_operator_action(body)
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": ok, "message": msg, "state": state})

@app.post("/api/arena/golden_match")
async def load_golden_match_endpoint():
    """Loads Golden Match 001 fixture through the engine."""
    state = arena_service.load_golden_match()
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": True, "message": "Golden match loaded successfully", "state": state})

@app.post("/api/arena/golden_live_match")
async def load_golden_live_match_endpoint():
    """Executes DEBATE_ARENA_LIVE_GOLDEN_001 with 6 human debaters and concurrency validation."""
    state = arena_service.run_golden_live_match_001()
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": True, "message": "Golden live match executed successfully", "state": state})

@app.post("/api/arena/lobby/join")
async def join_lobby_endpoint(request: Request):
    """Assigns human participant to seat with team verification."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    name = body.get("name", "Debater")
    spk_str = body.get("speaker_id", "P1")
    team_str = body.get("team", "PROPOSITION")
    sess_id = body.get("session_id")
    try:
        from polya_runtime.debate_engine.models import SpeakerId, TeamSide
        spk = SpeakerId(spk_str)
        team = TeamSide(team_str)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Invalid speaker or team: {e}"}, status_code=400)

    ok, msg, sess_data = arena_service.join_lobby(name, spk, team, sess_id)
    state = arena_service.get_full_state()
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": ok, "message": msg, "session": sess_data, "state": state})

@app.post("/api/arena/lobby/ready")
async def ready_lobby_endpoint(request: Request):
    """Sets readiness for human debater seat."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    spk_str = body.get("speaker_id", "P1")
    ready = body.get("ready", True)
    try:
        from polya_runtime.debate_engine.models import SpeakerId
        spk = SpeakerId(spk_str)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Invalid speaker_id: {e}"}, status_code=400)

    ok, msg = arena_service.set_participant_ready(spk, ready)
    state = arena_service.get_full_state()
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": ok, "message": msg, "state": state})

@app.post("/api/arena/lobby/reconnect")
async def reconnect_lobby_endpoint(request: Request):
    """Handles participant reconnecting to authoritative state."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    spk_str = body.get("speaker_id", "P1")
    sess_id = body.get("session_id")
    try:
        from polya_runtime.debate_engine.models import SpeakerId
        spk = SpeakerId(spk_str)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Invalid speaker_id: {e}"}, status_code=400)

    ok, msg, state = arena_service.reconnect_participant(spk, sess_id)
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": ok, "message": msg, "state": state})

@app.post("/api/arena/reset")
async def reset_debate_arena_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    topic = body.get("topic", "Regulasi Forensik Kecerdasan Buatan dan Pertanggungjawaban Algoritmik")
    desc = body.get("description", "Uji Forensik Standar Pertanggungjawaban Algoritma Otonom 3-vs-3")
    state = arena_service.reset_match(topic, desc)
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": True, "message": "Match reset successfully", "state": state})

@app.post("/api/arena/degraded")
async def toggle_degraded_state_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    component = body.get("component", "analytics")
    enabled = body.get("enabled", True)
    arena_service.set_degraded_state(component, enabled)
    state = arena_service.get_full_state()
    await broadcast_arena_event("STATE_UPDATE", state)
    return JSONResponse({"success": True, "component": component, "enabled": enabled, "state": state})

@app.get("/api/arena/replay")
async def get_debate_replay_endpoint():
    """Returns replay timeline, causal battle graph, and turning points."""
    replay_engine = arena_service.engine.get_replay_engine()
    analytics_engine = arena_service.engine.get_analytics_engine()
    return JSONResponse({
        "timeline": [
            {
                "event_id": e.event_id,
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "round_name": e.round_name,
                "speaker_id": e.speaker_id,
                "summary": e.summary
            }
            for e in replay_engine.timeline.events
        ],
        "turning_points": [
            {
                "id": tp.item_id,
                "score": tp.impact_score,
                "round": tp.round_name,
                "summary": tp.summary
            }
            for tp in analytics_engine.turning_point_engine.turning_points
        ],
        "state": arena_service.get_full_state()
    })

@app.get("/api/arena/forensics")
async def get_debate_forensics_endpoint():
    """Returns full forensic metrics, claim registry, and ZUMA persona analysis."""
    state = arena_service.get_full_state()
    return JSONResponse({
        "forensics": state.get("forensics"),
        "zuma_persona": state.get("forensics", {}).get("zuma_persona"),
        "quality_index": state.get("forensics", {}).get("quality_index", 8.98),
        "authoritative": True
    })

@app.get("/arena")
async def get_debate_arena_ui():
    """Serves the Professional 3-vs-3 Live Debate Arena UI."""
    arena_file = os.path.join(STATIC_DIR, "arena.html")
    if os.path.exists(arena_file):
        with open(arena_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Debate Arena UI Loading...</h1>")

# ---------------------------------------------------------------------------
# Debate Training API Endpoints (Prompt 14)
# ---------------------------------------------------------------------------

@app.post("/api/training/session/create")
async def create_training_session_endpoint(request: Request):
    """Creates an isolated Human vs AI Debate Training session."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    user_id = body.get("user_id", "user-default")
    topic = body.get("topic", "Uji Konsistensi Ontologis dan Integritas Leksikal Teks Kuno")
    desc = body.get("description", "Sesi latihan dialektika dan pembuktian forensik melawan AI Debater")

    from polya_runtime.debate_engine.models import TeamSide
    from polya_runtime.debate_engine.training_models import TrainingType, TrainingDifficulty, TrainingPersona

    user_pos = TeamSide(body.get("user_position", "PROPOSITION"))
    t_type = TrainingType(body.get("training_type", "PRACTICE_DEBATE"))
    diff = TrainingDifficulty(body.get("difficulty", "NORMAL"))
    persona = TrainingPersona(body.get("persona", "ZUMA_STYLE"))

    res = training_service.create_session(
        user_id=user_id,
        topic=topic,
        topic_description=desc,
        user_position=user_pos,
        training_type=t_type,
        difficulty=diff,
        persona=persona
    )
    # Automatically advance session to CONSTRUCTIVE state for immediate sparring readiness
    sid = res.get("training_session_id")
    if sid:
        from polya_runtime.debate_engine.training_models import TrainingState
        training_service.transition_state(sid, TrainingState.CONSTRUCTIVE)
        res["current_state"] = "CONSTRUCTIVE"
        res["status"] = "ACTIVE"
    return JSONResponse(res)

@app.get("/api/training/session/{session_id}")
async def get_training_session_endpoint(session_id: str):
    """Returns authoritative snapshot of training session state."""
    state = training_service.get_session_state(session_id)
    if not state:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return JSONResponse(state)

@app.post("/api/training/session/argument")
async def submit_training_argument_endpoint(request: Request):
    """Submits user argument in a training session."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    sid = body.get("training_session_id")
    claim = body.get("claim", "")
    premises = body.get("premises", [])
    reasoning = body.get("reasoning", "")
    impact = body.get("impact", "")
    target = body.get("target_argument_id")
    is_hypo = body.get("is_hypothetical", False)

    ok, res = training_service.submit_user_argument(
        session_id=sid,
        claim=claim,
        premises=premises,
        reasoning=reasoning,
        impact=impact,
        target_argument_id=target,
        is_hypothetical=is_hypo
    )
    return JSONResponse({"success": ok, "result": res})

@app.post("/api/training/session/evidence")
async def submit_training_evidence_endpoint(request: Request):
    """Submits user evidence in a training session."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    sid = body.get("training_session_id")
    citation = body.get("source_citation", "")
    source_type = body.get("source_type", "ACADEMIC_SOURCE")
    passage = body.get("verse_or_passage")
    is_hypo = body.get("is_hypothetical", False)

    ok, res = training_service.submit_user_evidence(
        session_id=sid,
        source_citation=citation,
        source_type=source_type,
        verse_or_passage=passage,
        is_hypothetical=is_hypo
    )
    return JSONResponse({"success": ok, "result": res})

@app.post("/api/training/session/cross_exam")
async def submit_training_cross_exam_endpoint(request: Request):
    """Submits question or answer for cross-examination training."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    sid = body.get("training_session_id")
    action = body.get("action", "QUESTION")
    text = body.get("text", "")

    if action == "QUESTION":
        ok, res = training_service.submit_cross_exam_question(sid, text)
    else:
        ok, res = training_service.submit_cross_exam_answer(sid, text)
    return JSONResponse({"success": ok, "result": res})

@app.post("/api/training/session/ai_turn")
async def generate_training_ai_turn_endpoint(request: Request):
    """Triggers AI Debater opponent response."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    sid = body.get("training_session_id")
    sim_error = body.get("simulate_error", False)
    ok, res = training_service.generate_ai_turn(session_id=sid, simulate_error=sim_error)
    return JSONResponse({"success": ok, "ai_turn": res})

@app.post("/api/training/session/evaluate")
async def evaluate_training_session_endpoint(request: Request):
    """Concludes session and generates 9-point coaching feedback & diagnostic score."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    sid = body.get("training_session_id") or body.get("session_id")
    state = training_service.get_session_state(sid) if sid else None
    if not state:
        return JSONResponse({"error": "Session not found", "detail": "Training session not found"}, status_code=404)
    ok, res = training_service.evaluate_and_coach(session_id=sid)
    if not ok:
        return JSONResponse({"error": "Evaluation failed", "result": res}, status_code=400)
    return JSONResponse({
        "success": True,
        "session_id": sid,
        "overall_score": res.get("score", {}).get("overall_score", 85),
        "evaluation": res
    })

@app.get("/api/training/session/{session_id}/replay")
async def get_training_replay_endpoint(session_id: str):
    """Returns deterministic replay for the training session."""
    replay = training_service.get_training_replay(session_id)
    if not replay:
        return JSONResponse({"error": "Replay not found"}, status_code=404)
    return JSONResponse(replay)

@app.get("/api/training/user/{user_id}/history")
async def get_user_training_history_endpoint(user_id: str):
    history = training_service.get_user_training_history(user_id)
    return JSONResponse({"user_id": user_id, "history": history})

@app.get("/api/training/user/{user_id}/stats")
async def get_user_training_stats_endpoint(user_id: str):
    stats = training_service.get_user_training_stats(user_id)
    return JSONResponse({"user_id": user_id, "stats": stats})


# ---------------------------------------------------------------------------
# Serve Main Frontend HTML
# ---------------------------------------------------------------------------
@app.get("/")
@app.get("/login")
@app.get("/checkout")
@app.get("/checkout/success")
@app.get("/checkout/pending")
@app.get("/checkout/failed")
@app.get("/dashboard")
@app.get("/calculator")
@app.get("/themes")
@app.get("/themes/{theme_id:path}")
@app.get("/knowledge")
@app.get("/knowledge/{subpath:path}")
@app.get("/persona")
@app.get("/persona/{subpath:path}")
@app.get("/pipeline")
@app.get("/pipeline/{subpath:path}")
@app.get("/search")
@app.get("/settings")
@app.get("/account")
@app.get("/account/{subpath:path}")
@app.get("/audit")
@app.get("/report")
async def get_index():
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), headers=headers)
    arena_file = os.path.join(STATIC_DIR, "arena.html")
    if os.path.exists(arena_file):
        with open(arena_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), headers=headers)
    return HTMLResponse("<h1>Polya Arena Loading...</h1>", headers=headers)

@app.get("/calculator-report.txt")
@app.get("/report.txt")
async def get_calculator_report():
    txt_file = os.path.join(STATIC_DIR, "calculator-end-to-end-repair-report.txt")
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="utf-8") as f:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=f.read())
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("Report not found", status_code=404)

@app.get("/p1-report.txt")
@app.get("/p1.txt")
async def get_p1_report():
    txt_file = os.path.join(os.path.dirname(__file__), "..", "docs", "audits", "p1-implementation-report.txt")
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="utf-8") as f:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=f.read())
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("Report not found", status_code=404)

@app.get("/p0-report.txt")
@app.get("/p0.txt")
async def get_p0_report():
    txt_file = os.path.join(STATIC_DIR, "p0-implementation-report.txt")
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="utf-8") as f:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=f.read())
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("Report not found", status_code=404)

@app.get("/audit.txt")
@app.get("/report.txt")
@app.get("/website-integration-audit.txt")
async def get_audit_report():
    txt_file = os.path.join(STATIC_DIR, "website-integration-audit.txt")
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="utf-8") as f:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=f.read())
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("Report not found", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

