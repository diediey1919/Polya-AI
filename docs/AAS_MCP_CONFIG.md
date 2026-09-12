# Polya AI - AAS Agent & MCP Builder Specification

## Overview
Polya AI operates on a standalone, multi-agent architecture using the AAS (Autonomous Agent System) Agent & MCP Builder framework within Antigravity.

---

## 1. Registered Specialized Agents (Agen Turunan)

| Agent Name | Role | Primary Capabilities | Guardrails & Rules |
| :--- | :--- | :--- | :--- |
| **`polya_zuma`** | Master Dialectical Debater | Socratic Cross-Examination, Concession Extraction, Ilzam al-Khasm, Dilemma Locking | Strict Bible citation (full book names, chapters, verses), Zero open-web sources, Cold analytical tone |
| **`polya_filologi`** | Forensic Exegesis Specialist | Root word analysis (Hebrew/Greek), Lexicon lookup (BDB, BDAG, HALOT), Textual variants (Codex Sinaiticus, Vaticanus, DSS) | Academic philological precision, translational distortion audit |
| **`polya_ingestion`**| TaskObserver & Worker Agent| Background batch ingestion of 2,500+ videos, telemetry, circuit breaker management | 20–40s jitter delay, auto rate-limit protection |

---

## 2. Integrated MCP Server (`polya-mcp`)
* **Location**: `/home/ubuntu/.polya/polya_mcp_server.py`
* **Protocol Interface**: Model Context Protocol (MCP) & Python Direct Integration

### Available MCP Tools:
1. `search_corpus(query: str, limit: int)`: Full-text search across 2,638 video transcripts and catalog.
2. `get_transcript(video_number: int)`: Retrieve timed dialog segments and metadata for a specific video.
3. `search_exegesis(query: str, limit: int)`: Query 189 academic records on theology, patristics, and textual variants.
4. `queue_status()`: Real-time telemetry on the 2,500+ video background ingestion queue.

---

## 3. Knowledge & RAG Retrieval Engine
* **Database**: `/home/ubuntu/.polya/polya_index.db`
* **Virtual Tables**: `knowledge_fts` (FTS5), `youtube_catalog_fts` (FTS5)
* **Task Queue**: `task_queue` (SQLite table with state machine: `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `RATE_LIMITED`)

---

## 4. Background Ingestion & TaskObserver
* **Worker Daemon**: `/home/ubuntu/.polya/polya_batch_worker.py`
* **Cron Schedule**: `0 * * * *` (10 videos/hour $\approx$ 240–250 videos/day)
* **Corpus Storage**: `/home/ubuntu/skills/debate/zuma/corpus/video-{NNN}/`
