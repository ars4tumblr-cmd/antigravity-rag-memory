# Hybrid Local-Cloud AI Assistant — Інсайти та Рішення

**Проект:** c:\Users\Mr. Schaslivij\.gemini\antigravity\scratch\Hybrid_Local_Cloud_AI_Assistant
**Дата:** 2026-02-01
**Фаза:** Завершено Phase 1-7

---

## 🏗️ Архітектурні Рішення

### 1. Privacy-First Routing

**Проблема:** Як забезпечити що Cloud LLM ніколи не бачить сирий PII?

**Рішення:** Трирівнева класифікація:
- `LOCAL` — обробка тільки локально (Ollama)
- `CLOUD_SANITIZE` — cloud отримує тільки санітизований текст з placeholders
- `CLOUD_SAFE` — жодних PII, можна відправити raw text

**Код:** `orchestrator/router/classifier.py`

### 2. Session-Scoped PIIRegistry

**Проблема:** Як відновити оригінальні імена у відповіді від Cloud?

**Рішення:** PIIRegistry зберігає mapping `placeholder → original` на рівні сесії:
```python
registry.register("Олександр", "PERSON")  # → [PERSON_1]
registry.desanitize("[PERSON_1] says hello")  # → "Олександр says hello"
```

---

## 🛡️ ADEN v2.3: Adaptive Decision Engine & Privacy Filter

**Фаза:** Phase 5-7 (ADEN Core + Privacy Filter)
**Дата:** 2026-02-01

### 1. Judge-Consultant Architecture

**Проблема:** Як використати інтелект Local LLM для оцінки складності, не довіряючи їй безпеку?

**Рішення:**
- **Consultant (Local LLM):** Генерує `intent_hint` (наприклад, "complex_analysis").
- **Judge (ADEN Core):** Приймає рішення. Якщо Consultant каже "Cloud", а Privacy Policy каже "Paranoid" — ADEN ветує хмару.

### 2. Court Registry Sanitization (Privacy Filter)

**Проблема:** Як отримати якісну відповідь хмари на PII-дані, не порушуючи приватність?

**Рішення:** Reversible Anonymization.
1. **Input:** "Мене звати Іванов"
2. **Registry:** Створює пару `{ "[PERSON_1]": "Іванов" }` (In-Memory, Session-Scoped).
3. **Cloud:** Отримує "Мене звати [PERSON_1]".
4. **Output:** Відповідь "Привіт [PERSON_1]" де-санітизується назад в "Привіт Іванов".

**Код:** `src/privacy_filter/sanitizer.py`

### 3. Economy-First Routing

**Принцип:** Не витрачати токени хмари на "Привіт".
- **Simple Query** -> `LOCAL` (безкоштовно).
- **Complex Query** -> `CLOUD_SANITIZE` (платимо за інтелект, але ховаємо дані).
- **Paranoid Mode** -> `LOCAL` (безпека понад усе).

### 4. "Safe" (PIIRegistry) Security

**Вимоги:** "Сейф" має бути неприступним.
- **In-Memory Only:** Жодних дисків.
- **Auto-Wipe:** Метод `registry.clear()` знищує дані.
- **Isolation:** Registry не передається в LLM.

---

**Tags:** #python #fastapi #privacy #pii #ner #spacy #mcp #ollama #claude #testing #async #aden #privacy-filter
