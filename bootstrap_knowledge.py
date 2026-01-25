#!/usr/bin/env python3
"""
BOOTSTRAP KNOWLEDGE SCRIPT
Run this on a new PC (e.g., PC1) to instantly inject core knowledge that was extracted on PC2.
"""

import os
import sys
import uuid
from datetime import datetime
import chromadb

# Configuration
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
PROJECT_ID = "antigravity-rag-memory"

# Knowledge to be injected
KNOWLEDGE = [
    {
        "content": "Orchestrator Agent uses 'bd' (beads) for task management. Run 'bd onboard' to start. Commands: bd ready, bd show, bd update.",
        "entity_type": "fact",
        "project_id": "Orchestrator_Agent",
        "scope": "local"
    },
    {
        "content": "Language Rule for RAG: Usage of English for storage and Ukrainian for output is mandatory. 'Global' scope for general facts, 'Local' for project specifics.",
        "entity_type": "preference",
        "project_id": "antigravity-rag-memory",
        "scope": "global"
    },
    {
        "content": "Mandatory workflow for ending sessions: 1. File issues. 2. Quality gates. 3. Update status. 4. PUSH TO REMOTE (git pull --rebase && bd sync && git push).",
        "entity_type": "decision",
        "project_id": "Orchestrator_Agent",
        "scope": "global"
    },
    {
        "content": "Work session always starts with 'git pull', then 'bd ready' to find tasks, and ends with mandatory 'git push'. No offline work or forgotten pushes allowed.",
        "entity_type": "preference",
        "project_id": "antigravity-rag-memory",
        "scope": "global"
    },
    {
        "content": "ROBO_AUTO_SYNC Logic: Scripts consolidate files from backup sources (HaasBackup*.zip signature) to 'D:\\ROBO'. Files are organized by Month/Year. Newer files overwrite older ones; duplicates are removed.",
        "entity_type": "fact",
        "project_id": "ROBO_AUTO_SYNC",
        "scope": "local"
    },
    {
        "content": "ROBO_AUTO_SYNC Scripts: Consolidate-Robo.ps1 (main logic), JobTracker.psm1 (status tracking). Target root is D:\\ROBO by default.",
        "entity_type": "fact",
        "project_id": "ROBO_AUTO_SYNC",
        "scope": "local"
    },
    {
        "content": "Problem: Git synchronization fails on Windows PCs with auth errors. Solution: Run 'git config --global credential.helper manager'.",
        "entity_type": "decision",
        "project_id": "windows_administration",
        "scope": "global"
    },
    {
        "content": "PC1 Sync Issue: If Git CLI fails on PC1, enable credential manager globaly. This is a known stored fix.",
        "entity_type": "fact",
        "project_id": "windows_administration",
        "scope": "global"
    },
    {
        "content": "Language Stability Rule: If Ukrainian language causes stability issues (encoding, crashes), use Latin Transliteration instead. Do not break the system for the sake of language.",
        "entity_type": "preference",
        "project_id": "antigravity-rag-memory",
        "scope": "global"
    }
]

def get_chroma_client():
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        client.heartbeat()
        return client
    except Exception as e:
        print(f"[ERROR] Cannot connect to ChromaDB: {e}")
        sys.exit(1)

def inject_knowledge():
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="knowledge_store")
    
    print(f"Завантаження {len(KNOWLEDGE)} фактів...")
    
    for item in KNOWLEDGE:
        # Generate stable ID based on content to prevent duplicates
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item["content"]))
        
        # Check if exists
        existing = collection.get(ids=[doc_id])
        if existing["ids"]:
            print(f"[-] Пропущено (існує): {item['content'][:50]}...")
            continue
            
        # Add timestamp
        metadata = {
            "entity_type": item["entity_type"],
            "project_id": item["project_id"],
            "scope": item["scope"],
            "timestamp": datetime.now().isoformat(),
            "source": "bootstrap_script"
        }
        
        collection.add(
            documents=[item["content"]],
            metadatas=[metadata],
            ids=[doc_id]
        )
        print(f"[+] Додано: {item['content'][:50]}...")

    print("\nГОТОВО! Знання завантажено.")

if __name__ == "__main__":
    inject_knowledge()
