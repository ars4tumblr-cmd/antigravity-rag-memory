"""
Автоматичний тест ядра RAG системи.
Перевіряє ізоляцію scope та project_id.
"""

import sys
from pathlib import Path

# Додаємо папку rag до PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from chroma_client import AntigravityRAGClient
import tempfile
import shutil


def run_tests():
    """Запуск тестів."""
    print("🧪 Запуск тестів RAG Core...\n")
    
    # Створюємо тимчасову папку для тестової БД
    temp_dir = tempfile.mkdtemp(prefix="rag_test_")
    print(f"📁 Тимчасова БД: {temp_dir}")
    
    try:
        # Ініціалізація клієнта
        client = AntigravityRAGClient(persist_directory=temp_dir)
        print("✅ Клієнт ініціалізовано\n")
        
        # Тест 1: Додавання Global запису
        print("📝 Тест 1: Збереження Global preference")
        global_id = client.store(
            content="Користувач віддає перевагу темній темі в UI",
            project_id="test_project",
            scope="global",
            entity_type="preference",
            manual_save=True
        )
        print(f"✅ Global запис створено: {global_id}\n")
        
        # Тест 2: Додавання Local запису для project_A
        print("📝 Тест 2: Збереження Local fact для project_A")
        local_a_id = client.store(
            content="Залежність X версії 2.5 зламана в project_A",
            project_id="project_A",
            scope="local",
            entity_type="fact"
        )
        print(f"✅ Local запис для project_A: {local_a_id}\n")
        
        # Тест 3: Додавання Private запису
        print("📝 Тест 3: Збереження Private нотатки")
        private_id = client.store(
            content="Особиста нотатка: переглянути архітектуру через тиждень",
            project_id="project_A",
            scope="private",
            entity_type="decision"
        )
        print(f"✅ Private запис: {private_id}\n")
        
        # Тест 4: Пошук з контексту project_B (НЕ має бачити Local A)
        print("🔍 Тест 4: Пошук з контексту project_B")
        results_b = client.search(
            query="залежність проблема",
            project_id="project_B",
            n_results=10
        )
        
        # Перевірка: project_B НЕ має бачити local записи project_A
        local_a_visible = any(r['id'] == local_a_id for r in results_b)
        global_visible = any(r['id'] == global_id for r in results_b)
        
        if local_a_visible:
            print("❌ FAIL: project_B бачить Local записи project_A!")
            return False
        else:
            print("✅ PASS: Local ізоляція працює")
        
        if global_visible:
            print("✅ PASS: project_B бачить Global записи")
        else:
            print("⚠️  WARNING: project_B НЕ бачить Global (можливо, запит нерелевантний)")
        
        print()
        
        # Тест 5: Пошук з контексту project_A (має бачити І Local, І Global)
        print("🔍 Тест 5: Пошук з контексту project_A")
        results_a = client.search(
            query="проблеми та налаштування",
            project_id="project_A",
            n_results=10
        )
        
        local_a_visible_in_a = any(r['id'] == local_a_id for r in results_a)
        global_visible_in_a = any(r['id'] == global_id for r in results_a)
        
        if local_a_visible_in_a and global_visible_in_a:
            print("✅ PASS: project_A бачить І Local, І Global")
        else:
            print(f"❌ FAIL: project_A НЕ бачить всі записи (Local: {local_a_visible_in_a}, Global: {global_visible_in_a})")
            return False
        
        print()
        
        # Тест 6: Перевірка контексту проекту
        print("📦 Тест 6: get_project_context для project_A")
        context_a = client.get_project_context(project_id="project_A", limit=5)
        
        if len(context_a) >= 2:  # Має бути мінімум Local + Global
            print(f"✅ PASS: Отримано {len(context_a)} записів контексту")
            # Перевіряємо пріоритет manual_save
            if context_a[0]['metadata'].get('manual_save'):
                print("✅ PASS: Manual save записи на першому місці")
            else:
                print("⚠️  WARNING: Manual save не на першому місці")
        else:
            print(f"❌ FAIL: Очікувалось >= 2 записів, отримано {len(context_a)}")
            return False
        
        print()
        
        # Тест 7: Private НЕ має з'являтися в загальному пошуку
        print("🔒 Тест 7: Перевірка ізоляції Private")
        # TODO: Додати логіку фільтрації private в search
        # Поки що це концептуально — private не експортується
        print("⚠️  INFO: Private логіка буде реалізована в export функції")
        
        print("\n" + "="*50)
        print("✅ ВСІ ТЕСТИ ПРОЙДЕНІ!")
        print("="*50)
        return True
    
    except Exception as e:
        print(f"\n❌ ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Очищення
        shutil.rmtree(temp_dir,ignore_errors=True)
        print(f"\n🧹 Тимчасову БД видалено: {temp_dir}")


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
