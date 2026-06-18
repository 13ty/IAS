# Gap Analysis

Metoda analizy luk technologicznych używana przez auditora.

## Typy luk

| Typ                 | Opis                                       | Przykład                    |
| ------------------- | ------------------------------------------ | --------------------------- |
| **Feature Gap**     | Brak funkcjonalności w stacku              | Brak test automation        |
| **Quality Gap**     | Istniejące narzędzie jest niskiej jakości  | Stary framework z błędami   |
| **Integration Gap** | Trudność integracji z istniejącym stackiem | Brak API dla naszego języka |
| **Performance Gap** | Istniejące rozwiązanie za wolne            | ORM z N+1 queries           |

## Workflow

### Step 1: Load Gap

```python
# Wczytaj z Inventory lub bezpośrednio
# Inventory → radar classification, health formula, gap definitions
```

### Step 2: Feature Gap Analysis

```
Czy propozycja robi coś czego nie mamy?
├── TAK → Gap Fit = 8-10
│   └── Sprawdź czy można to zrobić istniejącymi narzędziami
│       ├── TAK → Gap Fit = 5-7 (można workaround)
│       └── NIE → Gap Fit = 8-10 (unikalne)
└── NIE → Gap Fit = 1-4 (redundantne)
```

### Step 3: Quality Gap Analysis

```
Czy propozycja jest lepsza od tego co mamy?
├── TAK
│   ├── O ile lepsza?
│   │   ├── Znacząco (10x lepsza MI) → Quality = 9-10
│   │   ├── Umiarkowanie (2x lepsza MI) → Quality = 7-8
│   │   └── Lekko → Quality = 5-6
│   └── Czy warto migrować?
│       ├── TAK (upgrade_value > 0.7) → Adopt
│       └── NIE → Keep existing
└── NIE → Quality = 1-4
```

### Step 4: Integration Gap Analysis

```
Czy łatwo zintegrować z naszym stackiem?
├── TAK (natywna integracja) → Team Fit = 8-10
│   └── Przykład: React library w React projekcie
├── CZĘŚCIOWO (wymaga adaptera) → Team Fit = 5-7
│   └── Przykład: Python tool w Node.js projekcie
└── NIE (trudna integracja) → Team Fit = 1-4
    └── Przykład: C++ library w Python projekcie
```

## Scoring

| Gap Type        | Score | Waga w Decision Matrix |
| --------------- | ----- | ---------------------- |
| Feature Gap     | 1-10  | → Gap Fit              |
| Quality Gap     | 1-10  | → Quality              |
| Integration Gap | 1-10  | → Team Fit             |
| Performance Gap | 1-10  | → Quality (subset)     |

## Output

```json
{
  "gap_analysis": {
    "fills_gap": true,
    "gap_category": "Testing",
    "gap_severity": "high",
    "gap_type": "feature",
    "existing_alternatives": ["manual testing", "basic pytest"],
    "unique_value": "parallel execution + coverage"
  }
}
```

## Przykłady

| Gap            | Existing       | Proposition  | Analysis                          | Verdict   |
| -------------- | -------------- | ------------ | --------------------------------- | --------- |
| **Testing**    | pytest (basic) | pytest-xdist | Feature: parallel execution       | 🎉 Adopt  |
| **Security**   | none           | bandit       | Feature: SAST                     | 🎉 Adopt  |
| **Docs**       | mkdocs         | docusaurus   | Quality: better UX, but new stack | 🧪 Pilot  |
| **Monitoring** | prometheus     | datadog      | Feature: managed, but $$$         | 🧪 Pilot  |
| **ORM**        | SQLAlchemy     | django-orm   | Redundant, different stack        | 📚 Lesson |

## Ograniczenia

- **Binary scoring** — Brak granularności (1-10)
- **Subiektywne oceny** — Wymaga eksperta
- **Brak cost analysis** — Nie uwzględnia TCO
- **Static analysis** — Nie śledzi zmian w czasie

## Rozszerzalność (przyszłość)

| Nowy typ           | Co mierzy      | Jak                  |
| ------------------ | -------------- | -------------------- |
| **Security Gap**   | CVE coverage   | `security_check.py`  |
| **Compliance Gap** | GDPR, SOC2     | Checklist audit      |
| **Team Skill Gap** | Learning curve | Survey, skill matrix |
| **Cost Gap**       | TCO comparison | Cost calculator      |

---

_Wygenerowane z `skills/auditor/SKILL.md`_
