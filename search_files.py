#!/usr/bin/env python3
"""
Search files across all PC collections in ChromaDB.
Finds relevant files based on semantic similarity.
"""

import os
import sys
import chromadb
from typing import List, Dict

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))


def get_chroma_client():
    """Connect to ChromaDB server."""
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        client.heartbeat()
        return client
    except Exception as e:
        print(f"[ERROR] Cannot connect to ChromaDB: {e}")
        sys.exit(1)


def search_all_collections(client, query: str, n_results: int = 10) -> List[Dict]:
    """Search across all file collections."""
    results = []
    
    # Get all collections that start with "files_"
    collections = client.list_collections()
    file_collections = [c for c in collections if c.name.startswith("files_")]
    
    if not file_collections:
        print("No file collections found. Run index_files.py first.")
        return []
    
    for collection in file_collections:
        try:
            # Query this collection
            query_result = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count()),
                include=["metadatas", "distances", "documents"]
            )
            
            # Process results
            if query_result["ids"] and query_result["ids"][0]:
                for i, doc_id in enumerate(query_result["ids"][0]):
                    metadata = query_result["metadatas"][0][i] if query_result["metadatas"] else {}
                    distance = query_result["distances"][0][i] if query_result["distances"] else 0
                    
                    results.append({
                        "id": doc_id,
                        "pc_name": metadata.get("pc_name", "unknown"),
                        "project": metadata.get("project", "unknown"),
                        "filename": metadata.get("filename", doc_id),
                        "relative_path": metadata.get("relative_path", doc_id),
                        "path": metadata.get("path", ""),
                        "distance": distance,
                        "relevance": round((1 - distance) * 100, 1) if distance < 1 else 0,
                    })
        except Exception as e:
            print(f"[WARN] Error querying {collection.name}: {e}")
    
    # Sort by relevance (lower distance = more relevant)
    results.sort(key=lambda x: x["distance"])
    
    return results[:n_results]


def main():
    if len(sys.argv) < 2:
        print("Usage: python search_files.py <query>")
        print("Example: python search_files.py 'backup script'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    print(f"\n=== SEARCHING: '{query}' ===\n")
    
    client = get_chroma_client()
    results = search_all_collections(client, query)
    
    if not results:
        print("No results found.")
        return
    
    print(f"Found {len(results)} result(s):\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['pc_name']}] {result['relative_path']}")
        print(f"   Project: {result['project']}")
        print(f"   Relevance: {result['relevance']}%")
        print()


if __name__ == "__main__":
    main()
