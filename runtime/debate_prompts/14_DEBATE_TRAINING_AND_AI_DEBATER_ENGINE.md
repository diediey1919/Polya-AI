# DEBATE ARENA — PROMPT 14
## DEBATE TRAINING & AI DEBATER ARCHITECTURE SPECIFICATION

### 1. CONSTITUTIONAL BOUNDARY & MODE ISOLATION

Sistem membedakan secara absolut antara dua konteks eksekusi (**`ExecutionContext`**):

```
                    DEBATE PLATFORM
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
     OFFICIAL ARENA                DEBATE TRAINING
        HUMAN 3v3                    HUMAN vs AI
            │                             │
            ▼                             ▼
     OFFICIAL ENGINE              TRAINING ENGINE
            │                             │
            ▼                             ▼
      AI EVENT CONTROL             AI DEBATE AGENT
            │                             │
    ┌───────┼────────┐             ┌──────┼─────────┐
    ▼       ▼        ▼             ▼      ▼         ▼
 Moderator Referee Judges       Opponent Examiner Coach
    │       │        │             │      │         │
    └───────┴────────┘             └──────┴─────────┘
            │                             │
            ▼                             ▼
     OFFICIAL RECORD               TRAINING RECORD
```

#### Constitutional Contract:
1. **OFFICIAL_ARENA**:
   - `AI participant = STRICTLY FORBIDDEN`
   - AI hanya berfungsi sebagai *Event Intelligence* (Host, Moderator, Referee, Timekeeper, Fact Checker, Judges, Commentary, Analytics).
   - Roster terdiri dari tepat 6 debater manusia (`P1`, `P2`, `P3`, `C1`, `C2`, `C3`).
   - Setiap upaya menyuntikkan ID training (`AI_TRAINING_DEBATER`, `USER_DEBATER`) atau score training ke arena resmi akan ditolak dengan galat pelanggaran keamanan (*Security Violation*).

2. **TRAINING_MODE**:
   - `AI participant = ALLOWED`
   - AI dapat berfungsi aktif sebagai *Debate Opponent*, *Cross-Examiner*, *Rebuttal Opponent*, *Evidence Challenger*, *Rapid-Fire Opponent*, *Mock Debate Partner*, dan *Debate Coach*.
   - Identitas speaker: `USER_DEBATER`, `AI_TRAINING_DEBATER`, `TRAINING_COACH`, `TRAINING_EXAMINER`, `TRAINING_MODERATOR`.
   - Skor bersifat diagnostik (*Training Score*) dan tidak pernah dihitung ke dalam leaderboard/ELO resmi.

---

### 2. DATA MODELS & NAMESPACE ISOLATION

| Entitas | Official Arena | Debate Training | Keterangan Isolasi |
| :--- | :--- | :--- | :--- |
| **Argument ID** | `ARG-xxxx` | `USER-ARG-xxxx` / `AI-ARG-xxxx` | Namespace terpisah mutlak |
| **Claim ID** | `CLM-xxxx` | `TRAIN-CLAIM-xxxx` | Namespace terpisah mutlak |
| **Evidence ID** | `EVD-xxxx` | `TRAIN-EVD-xxxx` | Namespace terpisah mutlak |
| **Clash ID** | `CLASH-xxxx` | `TRAIN-CLASH-xxxx` | Namespace terpisah mutlak |
| **Event Log ID** | `EVT-xxxx` | `TRAIN-EVT-xxxx` | Log tersimpan dalam arsip terisolasi |
| **Timer Engine** | `TimerEngine` | `TrainingTimer` | Timer independen tanpa mutable state bersama |
| **State Machine** | `DebateStateMachine` | `TrainingStateMachine` | Siklus hidup terisolasi |

---

### 3. TRAINING TYPES & CURRICULUM

1. **PRACTICE DEBATE**: Latihan debat penuh Human vs AI Debater.
2. **CROSS-EXAMINATION TRAINING**: AI menjadi Examiner yang menguji premis, asumsi tersembunyi, konsistensi teks, dan kausalitas.
3. **REBUTTAL TRAINING**: Latihan membongkar klaim lawan $\rightarrow$ identifikasi kelemahan $\rightarrow$ serangan logika $\rightarrow$ counterargument $\rightarrow$ impak.
4. **EVIDENCE CHALLENGE**: AI menantang sumber, integritas sitasi (aturan penamaan kitab lengkap tanpa singkatan, contoh: *1 Korintus 12:27*), dan konteks naskah primer.
5. **RAPID-FIRE DEBATE**: Respons cepat dengan timer pendek (45 detik) untuk melatih ketenangan dan presisi.
6. **FULL MOCK DEBATE**: Simulasi 10 fase formal penuh melawan AI Debater.
7. **COACH MODE**: Analisis pasca sesi menghasilkan umpan balik terstruktur 9 poin.

---

### 4. 9-POINT STRUCTURED COACHING FEEDBACK

Setiap sesi latihan menghasilkan diagnosa komprehensif:
1. `WHAT YOU DID WELL`
2. `WEAK ARGUMENTS`
3. `MISSED REBUTTALS`
4. `UNANSWERED QUESTIONS`
5. `EVIDENCE PROBLEMS`
6. `LOGICAL WEAKNESSES`
7. `BEST MOMENT`
8. `TURNING POINT`
9. `WHAT TO IMPROVE`

---

### 5. PROMPT HIERARCHY FOR TRAINING AI

Sesuai Pasal 39:
1. **SYSTEM SAFETY & FAIRNESS**: Tanpa fabrikasi sitasi; penandaan argumen hipotetis.
2. **TRAINING MODE CONTRACT**: Otorisasi partisipasi dalam `TRAINING_MODE`.
3. **TRAINING STATE**: Sesi, topik, posisi, sisa waktu.
4. **ROUND RULES**: Protokol fase aktif.
5. **OPPONENT ROLE**: Instruksi tugas AI (Debater / Examiner / Coach).
6. **STRATEGY & ADAPTIVE PROFILE**: Target kelemahan user dan riwayat argumen.
7. **PERSONA**: `ZUMA_STYLE`, `SOCRATIC`, `SKEPTICAL`, `ACADEMIC`, `ADVERSARIAL`, dll.
8. **STYLE**: Pola dialektika, eksegesis leksikal, dan tekanan sokratik.
