#!/usr/bin/env python3
"""
Тестовий скрипт для демонстрації циклу УКР→АНГ→Збереження→УКР.
"""

import sys
from pathlib import Path

# Додаємо папку rag до PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from chroma_client import AntigravityRAGClient

# Ініціалізація клієнта (використовує реальну БД в .rag/chroma_db/)
client = AntigravityRAGClient()

# КРОК 1: Переклад УКР→АНГ (виконує агент)
user_input_uk = "абабгаламага це видавництво"
translated_en = "Abahalamaxa is a publishing house"

print("🔄 Переклад:")
print(f"   УКР: {user_input_uk}")
print(f"   АНГ: {translated_en}\n")

# КРОК 2: Збереження в RAG (англійською)
doc_id = client.store(
    content=translated_en,
    project_id="antigravity",
    scope="global",
    entity_type="fact",
    manual_save=True  # Ручний тригер через remember_now
)

print("✅ Збережено в RAG:")
print(f"   ID: {doc_id}")
print(f"   Scope: global")
print(f"   Manual save: True\n")

# КРОК 3: Підтвердження користувачу (українською)
confirmation_uk = f"🔥 ЗАПАМ'ЯТАНО: {user_input_uk}"
print(confirmation_uk)
print()

# КРОК 4: Тест пошуку
print("🔍 Тест пошуку (запит українською):")
search_query_uk = "що таке абабгаламага"
search_query_en = "what is Abahalamaxa"

print(f"   Запит УКР: {search_query_uk}")
print(f"   Переклад АНГ: {search_query_en}\n")

results = client.search(query=search_query_en, n_results=1)

if results:
    print("📦 Знайдено:")
    result = results[0]
    found_en = result['content']
    found_uk = "абабгаламага це видавництво"  # Переклад назад
    
    print(f"   АНГ (з БД): {found_en}")
    print(f"   УКР (показ): {found_uk}")
    print(f"   Scope: {result['metadata']['scope']}")
    print(f"   Manual save: {result['metadata']['manual_save']}")
else:
    print("❌ Нічого не знайдено")

print("\n" + "="*60)
print("✅ Повний цикл УКР→АНГ→Збереження→Пошук→УКР завершено!")
print("="*60)
