#!/usr/bin/env python3
"""
Polya MCP Server & Knowledge Retrieval Hub
Exposes Polya's FTS5 Knowledge Base, Zuma Video Corpus, and TaskObserver Queue
via Model Context Protocol (MCP) and Command Line Interface (CLI).
"""

import os
import sys
import json
import sqlite3
import argparse
from typing import Dict, Any, List

DB_PATH = "/home/ubuntu/.polya/polya_index.db"
CORPUS_DIR = "/home/ubuntu/skills/debate/zuma/corpus"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_corpus(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search videos and transcripts by keyword/theme in FTS5 index."""
    conn = get_db()
    cur = conn.cursor()
    try:
        sanitized_query = "".join(c for c in query if c.isalnum() or c in " *\"_-").strip()
        if not sanitized_query:
            sanitized_query = query
            
        cur.execute("""
            SELECT video_id, video_number, url, title, primary_theme, rank
            FROM youtube_catalog_fts
            WHERE youtube_catalog_fts MATCH ?
            ORDER BY rank
            LIMIT ?;
        """, (sanitized_query, limit))
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            v_num = int(r["video_number"])
            seg_path = os.path.join(CORPUS_DIR, f"video-{v_num:03d}", "segmented_transcript.json")
            has_corpus = os.path.exists(seg_path)
            results.append({
                "video_number": v_num,
                "video_id": r["video_id"],
                "title": r["title"],
                "url": r["url"],
                "primary_theme": r["primary_theme"],
                "has_segmented_corpus": has_corpus
            })
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return [{"error": str(e)}]

def get_transcript(video_number: int, max_segments: int = 20) -> Dict[str, Any]:
    """Retrieve full metadata and top dialogue segments for a video."""
    v_dir = os.path.join(CORPUS_DIR, f"video-{video_number:03d}")
    meta_path = os.path.join(v_dir, "metadata.json")
    seg_path = os.path.join(v_dir, "segmented_transcript.json")
    
    if not os.path.exists(v_dir):
        return {"error": f"Video #{video_number} directory not found in corpus."}
        
    res = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            res["metadata"] = json.load(f)
            
    if os.path.exists(seg_path):
        with open(seg_path, "r", encoding="utf-8") as f:
            seg_data = json.load(f)
            res["total_segments"] = seg_data.get("total_segments", 0)
            res["sample_segments"] = seg_data.get("segments", [])[:max_segments]
    else:
        res["sample_segments"] = []
        res["note"] = "Segmented transcript pending worker extraction."
        
    return res

def search_exegesis(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search academic knowledge, exegesis, and patristic records."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, title, category, tradition, step, snippet(knowledge_fts, 6, '[<b>', '</b>]', '...', 15) as snippet
            FROM knowledge_fts
            WHERE knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT ?;
        """, (query, limit))
        rows = cur.fetchall()
        results = [dict(r) for r in rows]
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return [{"error": str(e)}]

def queue_status() -> Dict[str, Any]:
    """Get live TaskObserver queue telemetry."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status, count(*) as count FROM task_queue GROUP BY status;")
    rows = cur.fetchall()
    conn.close()
    
    breakdown = {r['status']: r['count'] for r in rows}
    total = sum(breakdown.values())
    completed = breakdown.get("COMPLETED", 0)
    
    return {
        "total_videos": total,
        "completed": completed,
        "queued": breakdown.get("QUEUED", 0),
        "failed": breakdown.get("FAILED", 0),
        "rate_limited": breakdown.get("RATE_LIMITED", 0),
        "progress_percentage": round((completed / total * 100) if total else 0, 2)
    }

# Setup MCP Server
try:
    from mcp.server.mcpserver import MCPServer
    mcp_app = MCPServer("polya-mcp")

    @mcp_app.tool()
    def mcp_search_corpus(query: str, limit: int = 5) -> str:
        """Search videos and transcripts by keyword or theological theme in Polya's FTS5 catalog."""
        return json.dumps(search_corpus(query, limit), indent=2)

    @mcp_app.tool()
    def mcp_get_transcript(video_number: int, max_segments: int = 20) -> str:
        """Retrieve full metadata and timed dialogue segments for a video in the Zuma corpus."""
        return json.dumps(get_transcript(video_number, max_segments), indent=2)

    @mcp_app.tool()
    def mcp_search_exegesis(query: str, limit: int = 5) -> str:
        """Search academic knowledge, patristics, textual variants, and exegesis records."""
        return json.dumps(search_exegesis(query, limit), indent=2)

    @mcp_app.tool()
    def mcp_queue_status() -> str:
        """Get live telemetry and progress metrics for the TaskObserver video ingestion queue."""
        return json.dumps(queue_status(), indent=2)

except ImportError:
    mcp_app = None

def main():
    parser = argparse.ArgumentParser(description="Polya MCP Knowledge Server CLI")
    parser.add_argument("--search-corpus", type=str, help="Search video debate corpus")
    parser.add_argument("--get-transcript", type=int, help="Get transcript by video number")
    parser.add_argument("--search-exegesis", type=str, help="Search theological exegesis knowledge")
    parser.add_argument("--status", action="store_true", help="Get queue status")
    parser.add_argument("--stdio", action="store_true", help="Run as stdio MCP server")
    
    args, unknown = parser.parse_known_args()
    
    if args.status:
        print(json.dumps(queue_status(), indent=2))
    elif args.search_corpus:
        print(json.dumps(search_corpus(args.search_corpus), indent=2))
    elif args.get_transcript:
        print(json.dumps(get_transcript(args.get_transcript), indent=2))
    elif args.search_exegesis:
        print(json.dumps(search_exegesis(args.search_exegesis), indent=2))
    else:
        # Default behavior when run by MCP client (Claude, Codex, Hermes, AGY)
        if mcp_app is not None:
            mcp_app.run(transport="stdio")
        else:
            print("Error: MCP package not installed in environment.", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
