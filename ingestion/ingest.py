import os
import sys
import glob
import json
import argparse
from typing import List, Dict, Any

from ingestion.chunker import chunk_transcript
from backend.app.retrieval.vector_store import vector_store

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_raw_episodes() -> List[Dict[str, Any]]:
    """Load all transcript JSON files from ingestion/data/."""
    files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    episodes = []
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            episodes.append(data)
    return episodes


def run_ingestion(refresh: bool = False):
    """Run chunking and indexing pipeline."""
    print(f"[*] Starting Lenny Podcast Transcript Ingestion Pipeline...")
    if refresh:
        print("[-] Refresh flag detected: clearing existing index...")
        vector_store.clear()

    episodes = load_raw_episodes()
    print(f"[+] Loaded {len(episodes)} podcast episodes from '{DATA_DIR}'.")

    all_chunks = []
    for ep in episodes:
        chunks = chunk_transcript(ep, max_chars=1200, overlap_chars=200)
        print(f"  • '{ep.get('title')}' -> {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"[+] Total chunks to index: {len(all_chunks)}")
    vector_store.add_documents(all_chunks)
    print(f"[✓] Successfully indexed {len(vector_store.documents)} chunks into vector store.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Lenny Podcast Transcripts")
    parser.add_argument("--refresh", action="store_true", help="Clear and re-index all documents")
    args = parser.parse_args()

    run_ingestion(refresh=args.refresh)
