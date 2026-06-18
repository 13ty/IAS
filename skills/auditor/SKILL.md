---
name: auditor
description: >
  Audyt propozycji narzędzi. Ocenia każde proponowane narzędzie względem
  istniejących luk technologicznych, nakładania funkcjonalności,
  jakości kodu i wartości adopcji. Używa template'ów z tool-registry vault.

trigger_words:
  - audyt propozycji
  - oceń to narzędzie
  - czy to narzędzie jest dla nas
  - propozycja narzędzia
  - analiza porównawcza
  - czy warto adoptować
  - decision matrix
  - net benefit
  - gap analysis
  - overlap detection

examples:
  - "Oceń propozycję https://github.com/pytest-dev/pytest"
  - "Czy to narzędzie jest dla nas wartościowe?"
  - "Przeanalizuj propozycje w proposals.csv"
  - "Porównaj to narzędzie z tym co już mamy"
  - "Wypełnij decision matrix dla nowego narzędzia"

negatives:
  - Do NOT use this for local inventory (use inventory)
  - Do NOT use this for analyzing existing repos without proposal context
  - Do NOT use this for GitHub search (use scout)
---

# Skill: Auditor

## Purpose

Systematyczna ocena propozycji narzędzi — od kolekcji przez analizę po decyzję adopcyjną.

## Metodologia

- **Decision Matrix**: 4 kryteria × wagi → Net Benefit
- **Gap Analysis**: Feature/Quality/Integration/Performance Gap
- **Overlap Detection**: czy nowe narzędzie dubluje istniejące
- **Risk Assessment**: Team Acceptance jako kluczowy czynnik (waga 0.3)

## Workflow

### Step 1: Load Proposal

Wczytaj propozycję z `data/proposals.csv` lub bezpośredniego URL.

### Step 2: Initial Scan

1. Określ typ (repo/python-package/npm/vscode-extension/other)
2. Jeśli repo GitHub → zbierz podstawowe metadane (stars, forks, last commit)
3. Jeśli package → sprawdź wersję, zależności, popularność

### Step 3: Deep Analysis

Dla repozytoriów:

1. **Analyzer check** — struktura, Clean Arch, MI
2. **Security check** — license, CVEs, scorecard
3. **Community health** — contributors, issues, PRs

Dla package'ów:

1. **Dependency check** — czy pasuje do naszego stacka
2. **Version compatibility** — wymagane wersje
3. **Alternative check** — czy mamy już podobne

### Step 4: Gap & Overlap Analysis

1. **Gap analysis**: czy wypełnia lukę z Inventory?
   - Feature Gap: czy robi coś czego nie mamy?
   - Quality Gap: czy jest lepsze od tego co mamy?
   - Integration Gap: czy łatwo zintegrować?
2. **Overlap detection**: czy nakłada się na istniejące?
   - Jeśli tak → porównaj feature-by-feature
   - Jeśli nowe jest lepsze → rekomenduj migrację
   - Jeśli istniejące jest lepsze → odrzuć

### Step 5: Decision Matrix

| Kryterium       | Waga | Opis                                               |
| --------------- | ---- | -------------------------------------------------- |
| Gap Fit         | 0.30 | Jak dobrze wypełnia istniejącą lukę                |
| Quality         | 0.25 | Jakość kodu, architektura, bezpieczeństwo          |
| Team Fit        | 0.30 | Jak dobrze pasuje do stacka i umiejętności zespołu |
| Adoption Effort | 0.15 | Koszt wdrożenia, migracji, nauki                   |

**Skala 1-10 dla każdego kryterium.**
**Net Benefit = Σ(kryterium × waga)**

Progi decyzyjne:

- `> 7.0` → **ZAPROSZENIE DO TAŃCA** (adopt)
- `> 4.0` → **PILOT** (trial w ograniczonym zakresie)
- `<= 4.0` → **LEKCJA** (uczymy się, ale nie adoptujemy)

### Step 6: Generate Report

1. Zapisz pełną ocenę do `data/audits/{slug}.md`
2. Zaktualizuj `proposals.csv` (status → `audited`)
3. Jeśli adopt → dodaj do `tool_registry.json`

## Output Contract

```json
{
  "proposal": { "url": "...", "type": "repo", "status": "audited" },
  "analysis": {
    "clean_arch": { "score": 0-100, "violations": [...] },
    "maintainability": { "index": 0-100, "rating": "..." },
    "security": { "license": "...", "scorecard": 0-10 }
  },
  "gap_analysis": {
    "fills_gap": true,
    "gap_category": "Testing",
    "gap_severity": "high"
  },
  "overlap": {
    "has_overlap": false,
    "existing_tools": []
  },
  "decision_matrix": {
    "gap_fit": 8,
    "quality": 7,
    "team_fit": 9,
    "adoption_effort": 6,
    "net_benefit": 7.8,
    "verdict": "ZAPROSZENIE DO TAŃCA"
  }
}
```

## Error Handling

| Error                 | Action                              |
| --------------------- | ----------------------------------- |
| Nieznany typ URL      | Zapytaj użytkownika o typ           |
| Repo nie istnieje     | Oznacz jako invalid w proposals.csv |
| Brak propozycji w CSV | Poinformuj użytkownika              |
| Rate limit GitHub     | Użyj estymacji z dostępnych danych  |
