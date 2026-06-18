# Overlap Detection

Metoda wykrywania nakładania narzędzi używana przez auditora.

## Cel

Wykryć czy proponowane narzędzie dubluje funkcjonalność istniejących narzędzi w stacku.

## Algorytm

```python
def detect_overlap(proposal, registry):
    overlap_tools = []
    notes = proposal.get("notes", "").lower()

    for tool_name, tool_data in registry["tools"].items():
        desc = tool_data.get("description", "").lower()
        domain = tool_data.get("domain", "").lower()

        # Keyword matching w notes vs description
        if any(kw in desc for kw in notes.split() if kw):
            overlap_tools.append(tool_name)

    has_overlap = len(overlap_tools) > 0
    return {"has_overlap": has_overlap, "existing_tools": overlap_tools}
```

## Logika

1. **Wczytaj** `tool_registry.json` (istniejące narzędzia)
2. **Porównaj** notatki propozycji z opisami istniejących narzędzi
3. **Keyword matching** — case-insensitive, per word
4. **Zwróć** listę narzędzi z nakładaniem

## Przykłady

| Propozycja   | Notes                | Existing Tool | Description               | Overlap?                     |
| ------------ | -------------------- | ------------- | ------------------------- | ---------------------------- |
| pytest-xdist | "parallel testing"   | pytest        | "testing framework"       | ✅ Tak ("testing" w notes)   |
| bandit       | "security scanner"   | sonarqube     | "security scanner"        | ✅ Tak ("security scanner")  |
| docusaurus   | "documentation"      | mkdocs        | "documentation generator" | ✅ Tak ("documentation")     |
| react        | "frontend framework" | vue           | "frontend framework"      | ✅ Tak ("frontend")          |
| ffmpeg       | "video processing"   | pytest        | "testing framework"       | ❌ Nie (brak wspólnych słów) |

## Impact na Decision Matrix

```python
if has_overlap:
    gap_fit = max(1, gap_fit - 3)  # Kara za nakładanie
```

| Scenariusz              | Gap Fit | Impact  | Verdict                   |
| ----------------------- | ------- | ------- | ------------------------- |
| **Brak overlap**        | 7       | Neutral | Zależy od reszty          |
| **Overlap + lepsze**    | 4       | Kara -3 | 🧪 Pilot (może migrować)  |
| **Overlap + gorsze**    | 4       | Kara -3 | 📚 Lesson (keep existing) |
| **Overlap + neutralne** | 4       | Kara -3 | 🧪 Pilot (porównaj)       |

## Workflow

```
Wykryto overlap:
├── TAK
│   ├── Porównaj feature-by-feature
│   │   ├── Nowe jest lepsze → Rekomenduj migrację
│   │   ├── Istniejące jest lepsze → Odrzuć
│   │   └── Porównywalne → Pilot (A/B test)
│   └── Zaktualizuj overlap w raporcie
└── NIE
    ├── Brak nakładania ✅
    └── Kontynuuj normalny audyt
```

## Output

```json
{
  "overlap": {
    "has_overlap": true,
    "existing_tools": ["pytest", "pytest-cov"],
    "recommendation": "migrate"
  }
}
```

## Ograniczenia

- **Keyword matching only** — Brak semantycznego porównania
- **Brak feature-by-feature** — Tylko keyword overlap, nie feature overlap
- **Binary (Tak/Nie)** — Brak "częściowego" nakładania
- **Brak cost comparison** — Nie uwzględnia kosztu migracji

## Rozszerzalność (przyszłość)

| Ulepszenie              | Co doda                      | Jak                     |
| ----------------------- | ---------------------------- | ----------------------- |
| **Feature overlap**     | Porównanie cech              | Checklist comparison    |
| **Semantic similarity** | Embedding similarity         | `sentence-transformers` |
| **Cost comparison**     | TCO migracji vs keep         | Cost calculator         |
| **Usage overlap**       | Ile % użytkowników używa obu | Analytics               |
| **Migration path**      | Automatyczny codemod         | AST transforms          |

## Przykłady z życia

| Stack       | Proposition  | Overlap         | Decyzja                            |
| ----------- | ------------ | --------------- | ---------------------------------- |
| React + Vue | React        | Vue istnieje    | 📚 Lesson (nie dodawaj)            |
| pytest      | pytest-xdist | pytest istnieje | 🧪 Pilot (parallel = nowa feature) |
| mkdocs      | docusaurus   | docs istnieją   | 🧪 Pilot (lepsze UX, nowy stack)   |
| None        | bandit       | None            | 🎉 Adopt (brak overlap)            |
| SQLAlchemy  | django-orm   | ORM istnieje    | 📚 Lesson (redundantne)            |

---

_Wygenerowane z `scripts/proposal_audit.py` oraz `skills/auditor/SKILL.md`_
