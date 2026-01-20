"""
ChromaDB Client для глобальної RAG пам'яті Antigravity.
Підтримує багатомовні embeddings (українська + англійська).

ARCHITECTURE: Client-Server mode
- ChromaDB runs as a separate server on localhost:8000
- This client connects via HTTP (no file locking issues)
"""

import chromadb
from chromadb.config import Settings
from chromadb import EmbeddingFunction
# NOTE: embedding_functions imported lazily to avoid slow SentenceTransformer load
from typing import List, Dict, Optional
from pathlib import Path
import os
import requests

# ChromaDB Server configuration
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))

# Embedding Server configuration  
EMBED_HOST = os.environ.get("EMBED_HOST", "localhost")
EMBED_PORT = int(os.environ.get("EMBED_PORT", "8001"))


class HttpEmbeddingFunction(EmbeddingFunction):
    """Embedding function that calls our HTTP embedding server."""
    
    def __init__(self, host: str = EMBED_HOST, port: int = EMBED_PORT):
        self.url = f"http://{host}:{port}/embed"
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        try:
            response = requests.post(self.url, json={"texts": input}, timeout=30)
            response.raise_for_status()
            return response.json()["embeddings"]
        except Exception as e:
            raise RuntimeError(f"Embedding server error: {e}")


class AntigravityRAGClient:
    """Клієнт для роботи з векторним сховищем знань."""
    
    def __init__(self, persist_directory: str = None):
        """
        Ініціалізація клієнта ChromaDB.
        
        Connects to ChromaDB server running on localhost:8000.
        If server is not available, falls back to PersistentClient (for testing).
        """
        self.embedding_function = None
        
        # Try HTTP client first (production mode)
        try:
            self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            self.client.heartbeat()  # Test connection
            self._mode = "http"
            # Use our HTTP embedding server
            self.embedding_function = HttpEmbeddingFunction()
        except Exception as e:
            # Fallback to persistent client (for local testing)
            if persist_directory is None:
                home = Path.home()
                persist_directory = str(home / ".gemini" / "antigravity" / ".rag" / "chroma_db")
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_directory)
            self._mode = "persistent"
            # Load local embedding function for persistent mode
            from chromadb.utils import embedding_functions  # Lazy import
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        
        # Get or create collection
        # In HTTP mode: don't pass embedding_function to avoid slow loading
        # We'll generate embeddings ourselves via HttpEmbeddingFunction
        if self._mode == "http":
            self.collection = self.client.get_or_create_collection(
                name="antigravity_global_knowledge",
                embedding_function=None,  # Don't load default embedder!
                metadata={"description": "Global RAG memory for all Antigravity projects"}
            )
        else:
            self.collection = self.client.get_or_create_collection(
                name="antigravity_global_knowledge",
                embedding_function=self.embedding_function,
                metadata={"description": "Global RAG memory for all Antigravity projects"}
            )
    
    def store(
        self,
        content: str,
        project_id: str,
        scope: str = "local",
        entity_type: str = "fact",
        source_session: str = "",
        manual_save: bool = False,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Зберегти знання в RAG.
        
        Args:
            content: Текст для збереження
            project_id: ID проекту (наприклад, 'orchestrator_agent')
            scope: 'global', 'local', або 'private'
            entity_type: Тип: 'preference', 'fact', 'decision', 'code_snippet'
            source_session: UUID сесії
            manual_save: Чи збережено вручну (пріоритет)
            metadata: Додаткові метадані
        
        Returns:
            ID збереженого документа
        """
        import uuid
        from datetime import datetime
        
        doc_id = str(uuid.uuid4())
        
        # Базові метадані
        meta = {
            "project_id": project_id,
            "scope": scope,
            "entity_type": entity_type,
            "source_session": source_session,
            "timestamp": datetime.utcnow().isoformat(),
            "manual_save": manual_save
        }
        
        if metadata:
            meta.update(metadata)
            
        # Generate embedding if needed
        embeddings = None
        if self._mode == "http" and self.embedding_function:
            embeddings = self.embedding_function([content])
        
        # Додаємо в колекцію
        self.collection.add(
            documents=[content],
            metadatas=[meta],
            ids=[doc_id],
            embeddings=embeddings # Pass generated embeddings if any
        )
        
        return doc_id
    
    def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Пошук знань по семантичному запиту.
        
        Args:
            query: Текст запиту
            project_id: Фільтр по проекту (якщо None — тільки global)
            n_results: Кількість результатів
            filters: Додаткові фільтри
        
        Returns:
            Список знайдених документів з метаданими
        """
        # Формуємо where-умову для фільтрації
        where_clause = {}
        
        # Generate query embedding if needed
        query_embeddings = None
        if self._mode == "http" and self.embedding_function:
            query_embeddings = self.embedding_function([query])

        if project_id == "*":
            # "God Mode": шукаємо по всіх записах без обмежень скопу
            results = self.collection.query(
                query_texts=[query] if not query_embeddings else None,
                query_embeddings=query_embeddings,
                n_results=n_results
            )
            return self._format_results(results)
            
        elif project_id:
            # Шукаємо: (project_id == X AND scope == local) OR (scope == global)
            # ChromaDB не підтримує OR напряму, тому робимо два запити і об'єднуємо
            
            # Запит 1: Local записи для цього проекту
            local_results = self.collection.query(
                query_texts=[query] if not query_embeddings else None,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where={
                    "$and": [
                        {"project_id": project_id},
                        {"scope": "local"}
                    ]
                }
            )
            
            # Запит 2: Global записи
            global_results = self.collection.query(
                query_texts=[query] if not query_embeddings else None,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where={"scope": "global"}
            )
            
            # Об'єднуємо результати (дедуплікація по ID)
            all_docs = []
            seen_ids = set()
            
            for result_set in [local_results, global_results]:
                if result_set['documents']:
                    for i, doc_id in enumerate(result_set['ids'][0]):
                        if doc_id not in seen_ids:
                            all_docs.append({
                                "id": doc_id,
                                "content": result_set['documents'][0][i],
                                "metadata": result_set['metadatas'][0][i],
                                "distance": result_set['distances'][0][i] if 'distances' in result_set else None
                            })
                            seen_ids.add(doc_id)
            
            # Сортуємо по distance (менше = краще)
            all_docs.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
            
            return all_docs[:n_results]
        
        else:
            # Якщо project_id не вказано — тільки global
            where_clause["scope"] = "global"
        
        if filters:
            where_clause.update(filters)
        
        results = self.collection.query(
            query_texts=[query] if not query_embeddings else None,
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        
        return self._format_results(results)
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """Format ChromaDB results into a clean list of dictionaries."""
        formatted = []
        if results and results.get('documents'):
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    "id": doc_id,
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        return formatted

    def get_project_context(self, project_id: str, limit: int = 10) -> List[Dict]:
        """
        Отримати найрелевантніші записи для проекту (для початку сесії).
        
        Args:
            project_id: ID проекту
            limit: Максимальна кількість записів
        
        Returns:
            Список записів, відсортованих по пріоритету
        """
        # Отримуємо local записи для цього проекту
        local_results = self.collection.get(
            where={
                "$and": [
                    {"project_id": project_id},
                    {"scope": "local"}
                ]
            },
            limit=limit
        )
        
        # Отримуємо global записи
        global_results = self.collection.get(
            where={"scope": "global"},
            limit=limit
        )
        
        # Об'єднуємо результати
        formatted = []
        seen_ids = set()
        
        for results_set in [local_results, global_results]:
            if results_set['documents']:
                for i, doc_id in enumerate(results_set['ids']):
                    if doc_id not in seen_ids:
                        formatted.append({
                            "id": doc_id,
                            "content": results_set['documents'][i],
                            "metadata": results_set['metadatas'][i]
                        })
                        seen_ids.add(doc_id)
        
        # Сортуємо: manual_save = True першими
        formatted.sort(key=lambda x: (not x['metadata'].get('manual_save', False)))
        
        return formatted[:limit]
