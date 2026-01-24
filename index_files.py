#!/usr/bin/env python3
"""
File Indexer for Antigravity RAG System.
Indexes all project files into ChromaDB for semantic search.

Each PC has its own collection (files_PC1, files_PC2, etc.)
This prevents conflicts when syncing via Git.
"""

import os
import sys
import hashlib
import socket
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

# Configuration
WORKSPACE = Path(os.environ.get("WORKSPACE", r"C:\Users\Mr. Schaslivij\.gemini\antigravity\scratch"))
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
PC_NAME = socket.gethostname()

# File extensions to index
INDEXABLE_EXTENSIONS = {".md", ".ps1", ".py", ".json", ".txt", ".yaml", ".yml"}

# Folders to skip
SKIP_FOLDERS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}


def get_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of file content."""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def read_file_content(filepath: Path) -> Optional[str]:
    """Read file content, handling encoding issues."""
    encodings = ["utf-8", "utf-8-sig", "cp1251", "latin-1"]
    for encoding in encodings:
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def get_project_name(filepath: Path, workspace: Path) -> str:
    """Extract project name from file path."""
    try:
        relative = filepath.relative_to(workspace)
        parts = relative.parts
        if len(parts) > 0:
            return parts[0]
    except ValueError:
        pass
    return "unknown"


def scan_files(workspace: Path) -> List[Dict]:
    """Scan workspace for indexable files."""
    files = []
    
    for root, dirs, filenames in os.walk(workspace):
        # Skip unwanted folders
        dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS]
        
        for filename in filenames:
            filepath = Path(root) / filename
            
            # Check extension
            if filepath.suffix.lower() not in INDEXABLE_EXTENSIONS:
                continue
            
            # Skip very large files (>1MB)
            try:
                if filepath.stat().st_size > 1_000_000:
                    continue
            except OSError:
                continue
            
            content = read_file_content(filepath)
            if content is None:
                continue
            
            files.append({
                "path": str(filepath),
                "relative_path": str(filepath.relative_to(workspace)),
                "project": get_project_name(filepath, workspace),
                "content": content,
                "hash": get_file_hash(filepath),
                "extension": filepath.suffix.lower(),
                "filename": filepath.name,
            })
    
    return files


def get_chroma_client():
    """Connect to ChromaDB server."""
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        client.heartbeat()
        print(f"[OK] Connected to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
        return client
    except Exception as e:
        print(f"[ERROR] Cannot connect to ChromaDB: {e}")
        print("Make sure ChromaDB server is running (start_chroma_server.ps1)")
        sys.exit(1)


def index_files(client, files: List[Dict], pc_name: str):
    """Index files into ChromaDB collection for this PC."""
    collection_name = f"files_{pc_name}"
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": f"File index for {pc_name}"}
    )
    
    # Get existing documents
    existing = collection.get()
    existing_ids = set(existing["ids"]) if existing["ids"] else set()
    existing_hashes = {}
    if existing["metadatas"]:
        for i, meta in enumerate(existing["metadatas"]):
            if meta and "hash" in meta:
                existing_hashes[existing["ids"][i]] = meta["hash"]
    
    # Prepare documents to add/update
    to_add = {"ids": [], "documents": [], "metadatas": []}
    to_update = {"ids": [], "documents": [], "metadatas": []}
    current_ids = set()
    
    for file_info in files:
        doc_id = file_info["relative_path"].replace("\\", "/")
        current_ids.add(doc_id)
        
        metadata = {
            "path": file_info["path"],
            "relative_path": file_info["relative_path"],
            "project": file_info["project"],
            "hash": file_info["hash"],
            "extension": file_info["extension"],
            "filename": file_info["filename"],
            "pc_name": pc_name,
        }
        
        if doc_id not in existing_ids:
            # New file
            to_add["ids"].append(doc_id)
            to_add["documents"].append(file_info["content"])
            to_add["metadatas"].append(metadata)
        elif existing_hashes.get(doc_id) != file_info["hash"]:
            # File changed
            to_update["ids"].append(doc_id)
            to_update["documents"].append(file_info["content"])
            to_update["metadatas"].append(metadata)
    
    # Find deleted files
    deleted_ids = existing_ids - current_ids
    
    # Apply changes
    if to_add["ids"]:
        collection.add(**to_add)
        print(f"[+] Added {len(to_add['ids'])} new files")
    
    if to_update["ids"]:
        collection.update(**to_update)
        print(f"[~] Updated {len(to_update['ids'])} changed files")
    
    if deleted_ids:
        collection.delete(ids=list(deleted_ids))
        print(f"[-] Removed {len(deleted_ids)} deleted files")
    
    if not to_add["ids"] and not to_update["ids"] and not deleted_ids:
        print("[=] No changes detected")
    
    total = collection.count()
    print(f"[i] Total files in index: {total}")


def main():
    print(f"\n=== FILE INDEXER ({PC_NAME}) ===\n")
    print(f"Workspace: {WORKSPACE}")
    print(f"Collection: files_{PC_NAME}\n")
    
    # Scan files
    print("Scanning files...")
    files = scan_files(WORKSPACE)
    print(f"Found {len(files)} indexable files\n")
    
    if not files:
        print("No files to index.")
        return
    
    # Connect to ChromaDB
    client = get_chroma_client()
    
    # Index files
    print("\nIndexing...")
    index_files(client, files, PC_NAME)
    
    print("\n=== DONE ===\n")


if __name__ == "__main__":
    main()
