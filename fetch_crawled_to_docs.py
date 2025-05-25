import os
from pathlib import Path
import requests
import json
from typing import List, Dict

DOCS_DIR = Path("docs")
MCP_SERVER_URL = "http://localhost:8000"  # Update if your MCP server is remote
RAG_QUERY_ENDPOINT = f"{MCP_SERVER_URL}/rag/perform_rag_query"

SOURCES = [
    "si.com",
    "olympics.com",
    "bbc.com",
    "bbc.co.uk",
    "verywellmind.com",
    "espn.com",
    "theguardian.com",
    "nytimes.com",
    "psychologytoday.com",
    "ncaa.com",
]

QUERY = "sports psychology OR athlete interview OR mental health"
MATCH_COUNT = 20


def fetch_rag_chunks(source: str) -> List[Dict]:
    """
    Fetch crawled RAG chunks from the MCP server for a given source.

    Args:
        source (str): The source domain to query.

    Returns:
        List[Dict]: List of result dicts with 'content', 'url', and 'metadata'.
    """
    payload = {
        "query": QUERY,
        "source": source,
        "match_count": MATCH_COUNT,
    }
    try:
        resp = requests.post(RAG_QUERY_ENDPOINT, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        print(f"[error] Failed to fetch from {source}: {e}")
        return []


def save_chunk_to_file(content: str, source: str, chunk_index: int, url: str = None):
    """
    Save a chunk of text to a .txt file in /docs with metadata header.

    Args:
        content (str): The text content to save.
        source (str): The source domain.
        chunk_index (int): The chunk index.
        url (str, optional): The original URL.
    """
    DOCS_DIR.mkdir(exist_ok=True)
    safe_source = source.replace(".", "_")
    filename = DOCS_DIR / f"{safe_source}_chunk{chunk_index}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Source: {source}\n")
        if url:
            f.write(f"# URL: {url}\n")
        f.write(f"# Chunk: {chunk_index}\n\n")
        f.write(content.strip())
    print(f"[info] Saved: {filename}")


def main():
    """
    Fetch crawled content from all sources and save to /docs for ingestion.
    """
    for source in SOURCES:
        print(f"[info] Fetching from {source}...")
        results = fetch_rag_chunks(source)
        if not results:
            print(f"[warn] No content found for {source}.")
            continue
        for i, result in enumerate(results):
            content = result.get("content", "")
            url = result.get("url", None)
            if not content.strip():
                continue
            save_chunk_to_file(content, source, i, url)
    print("[done] All available crawled content saved to /docs.")


if __name__ == "__main__":
    main() 