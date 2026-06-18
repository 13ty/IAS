---
name: ias-scan
description: "Uruchamia pełny pipeline IAS: Inventory → Analyzer → Scout — skanuje projekt, analizuje repo, szuka rozwiązań."
trigger: /ias-scan
bash: python scripts/orchestrator.py --scan {{path_or_url}}
argument-hint: path_or_url
allowed-tools:
  - bash
  - read
  - write
  - grep
  - glob
---

# Command: /ias-scan

## Description

Uruchamia pełny pipeline IAS: Inventory → Analyzer → Scout

## Usage

```
/ias-scan [path_or_url]
```

## Arguments

| Argument    | Required | Description                                                                  |
| ----------- | -------- | ---------------------------------------------------------------------------- |
| path_or_url | No       | Ścieżka do projektu lub URL repo. Jeśli pominięte, używa bieżącego katalogu. |

## Workflow

### Phase 1: Inventory

1. Wykryj typ projektu (package.json, requirements.txt, etc.)
2. Uruchom cdxgen → generuj SBOM
3. Uruchom grype → skanuj luki
4. Klasyfikuj na Technology Radar
5. Wykryj luki (gaps)
6. Zapisz do state

### Phase 2: Analyzer (jeśli podano URL)

1. Sklonuj repozytorium
2. Buduj graf zależności
3. Wykryj warstwy Clean Architecture
4. Waliduj kierunek zależności
5. Wylicz Maintainability Index
6. Oszacuj Upgrade Value
7. Zapisz do state

### Phase 3: Scout

1. Wyodrębnij luki z Inventory i Analyzer
2. Mapuj luki na słowa kluczowe
3. Przeszukaj GitHub
4. Oceń bezpieczeństwo (Scorecard)
5. Oblicz relevance
6. Priorytetyzuj wyniki
7. Zapisz do state

## Output

Generuje raport z:

- Inventory summary (SBOM, Radar, Health)
- Analysis summary (Clean Arch, Maintainability, Upgrade Value)
- Scout results (top 10 matching repos)
- Recommendations

## Example

```
/ias-scan R:\Dev\MyPythonProject

# Output:
# ✅ Inventory: 45 components, 2 vulnerabilities, 3 gaps
# ✅ Analyzer: Clean Arch score 78/100, Maintainability 82/100
# ✅ Scout: Found 8 repos matching your gaps
# 📋 Recommendations: [list]
```
