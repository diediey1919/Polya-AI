#!/usr/bin/env python3
"""
Polya AI - Interactive Terminal Dialectical Interface
Powered by Persona ZUMA and Polya MCP Knowledge Engine.
"""

import sys
import os
import readline

# Add path for polya_mcp_server
sys.path.insert(0, "/home/ubuntu/.polya")
try:
    import polya_mcp_server
except ImportError:
    pass

BANNER = """
================================================================================
           POLYA APOLOGETIKA - PERSONA ZUMA INTERACTIVE DIALECTICAL CLI         
================================================================================
  Status: STANDALONE AAS RUNTIME (Zero Hermes Dependency)
  Knowledge Engine: FTS5 SQLite (.polya/polya_index.db)
  Video Corpus: 2,638 Catalog Records | 10 Baseline Datasets
  Protocols: Strict Bible Citations | Ilzam al-Khasm | Socratic Pressure
================================================================================
Type your opponent argument or theological claim to debate.
Commands:
  :status    - Show TaskObserver video ingestion progress
  :search <q>- Search video debate corpus
  :exegesis <q> - Search theological research database
  :quit      - Exit CLI
================================================================================
"""

def handle_query(query: str):
    query = query.strip()
    if not query:
        return
        
    if query == ":quit" or query == ":exit":
        print("\nSelesai. Dialektika ditutup.\n")
        sys.exit(0)
        
    if query == ":status":
        st = polya_mcp_server.queue_status()
        print(f"\n[TaskObserver Telemetry]")
        print(f"  • Total Videos    : {st['total_videos']}")
        print(f"  • Completed       : {st['completed']}")
        print(f"  • In Queue        : {st['queued']}")
        print(f"  • Progress        : {st['progress_percentage']}%\n")
        return

    if query.startswith(":search "):
        term = query[8:].strip()
        res = polya_mcp_server.search_corpus(term, limit=3)
        print(f"\n[Hasil Pencarian Korpus: '{term}']")
        for r in res:
            print(f"  • Video #{r.get('video_number')}: {r.get('title')} ({r.get('url')})")
        print()
        return

    if query.startswith(":exegesis "):
        term = query[10:].strip()
        res = polya_mcp_server.search_exegesis(term, limit=3)
        print(f"\n[Hasil Pencarian Eksegesa: '{term}']")
        for r in res:
            print(f"  • [{r.get('id')}] {r.get('title')}")
            print(f"    Snippet: {r.get('snippet')}")
        print()
        return

    # Normal debate argument input
    print("\n--- [POLYA AI (PERSONA ZUMA)] ---")
    print(f"Menanggapi klaim: \"{query}\"\n")
    
    # Auto-retrieval MCP
    corpus_matches = polya_mcp_server.search_corpus(query, limit=2)
    exegesis_matches = polya_mcp_server.search_exegesis(query, limit=2)
    
    if corpus_matches and "error" not in corpus_matches[0]:
        print("[RAG Evidence - Korpus Video Zuma]:")
        for c in corpus_matches:
            print(f"  - Ref Video #{c.get('video_number')}: {c.get('title')}")
        print()

    if exegesis_matches and "error" not in exegesis_matches[0]:
        print("[RAG Evidence - Naskah & Eksegesa]:")
        for e in exegesis_matches:
            print(f"  - Ref Naskah: {e.get('title')} ({e.get('step', '')})")
        print()

    print("[Socratic Dialectical Response]:")
    print("Buka teks kanonikal Anda dan jangan mengalihkan premis.")
    print("Setiap klaim dogmatis wajib dibuktikan dengan ayat eksplisit dari Bible (Lengkap Nama Kitab, Pasal, dan Ayat).")
    print("--------------------------------------------------------------------------------\n")

def main():
    print(BANNER)
    while True:
        try:
            inp = input("OPPONENT > ")
            handle_query(inp)
        except (KeyboardInterrupt, EOFError):
            print("\nKeluar dari Polya CLI.")
            break

if __name__ == "__main__":
    main()
