#!/usr/bin/env python3
"""
Pre-warming script: завантажує модель в cache ПЕРЕД першим використанням.
Запускається автоматично при старті Antigravity.
"""

import sys
from pathlib import Path

# Додаємо папку rag до PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

print("🔥 RAG Pre-warming: Завантаження моделі в cache...")

try:
    from sentence_transformers import SentenceTransformer
    
    # Завантажуємо модель (це створить cache)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Тестовий embedding для прогріву
    _ = model.encode(["warmup"], show_progress_bar=False)
    
    print("✅ Модель завантажена і готова!")
    print(f"   Кеш: {Path.home() / '.cache' / 'huggingface'}")
    
except Exception as e:
    print(f"❌ Помилка: {e}")
    print("⚠️  RAG працюватиме, але перший запит буде повільним")
    sys.exit(1)
