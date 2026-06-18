---
name: heatmap
description: >
  Generuje wizualizację mapy ciepła ekosystemu narzędzi IAS.
  Analizuje pokrycie domen, nakładania się, priorytety, konflikty portów,
  oraz mocne i słabe strony zestawu narzędzi.

trigger_words:
  - mapa ciepła
  - heat map
  - wizualizacja ekosystemu
  - nakładanie narzędzi
  - konflikty portów
  - mocne strony
  - słabe strony
  - wąskie gardła
  - pokrycie domen

examples:
  - "Pokaż mapę ciepła ekosystemu"
  - "Wykryj nakładania się narzędzi"
  - "Sprawdź konflikty portów"
  - "Jakie domeny są słabo pokryte?"
  - "Generuj raport JSON"

negatives:
  - Do NOT use for inventory (use inventory)
  - Do NOT use for analyzing single repos (use analyzer)
  - Do NOT use for GitHub search (use scout)
---

# Skill: Heat Map

## Purpose

Generowanie wizualizacji mapy ciepła ekosystemu narzędzi — analiza pokrycia domen, nakładania się, priorytetów, konfliktów portów oraz mocnych i słabych stron.

## Metodologia

- **Domain Coverage**: liczenie narzędzi per domena, wykrywanie luk
- **Overlap Detection**: grupowanie narzędzi po wspólnych alternatywach
- **Priority Distribution**: analiza hot/warm/cold
- **Port Conflict Detection**: parsowanie run_command + porównanie z .envy
- **Strength/Weakness Analysis**: identyfikacja mocnych i słabych stron
- **Bottleneck Detection**: single points of failure

## Workflow

### Step 1: Load Data

1. Wczytaj `data/tool_registry.json`
2. Wczytaj `.envy` z `Vaults/3Pillars/.envy`
3. Wyodrębnij informacje o portach

### Step 2: Domain Analysis

1. Policz narzędzia per domena
2. Zidentyfikuj dobrze pokryte domeny (≥3 narzędzi)
3. Zidentyfikuj luki (0-1 narzędzi)
4. Oblicz coverage score

### Step 3: Overlap Detection

1. Pogrupuj narzędzia po wspólnych alternatywach
2. Wykryj nakładania się w obrębie domeny
3. Oblicz overlap score

### Step 4: Port Conflict Detection

1. Sparsuj `run_command` regexem `[:\s](\d{4,5})`
2. Porównaj z portami z `.envy`
3. Wykryj konflikty (ten sam port = wiele narzędzi)

### Step 5: Strength/Weakness Analysis

1. **Mocne strony**: domeny z wieloma hot narzędziami
2. **Słabe strony**: domeny z małą liczbą narzędzi, zimne priorytety
3. **Wąskie gardła**: single points of failure w krytycznych domenach

### Step 6: Generate Output

1. **ASCII Table** (domyślnie) — czytelna tabela z wykresami słupkowymi
2. **Mermaid Diagram** (--mermaid) — diagram z podziałem na subgraphs
3. **JSON** (--json) — strukturyzowane dane do dalszego przetwarzania

## Output Contract

```json
{
  "timestamp": "2024-01-15T10:00:00",
  "domains": {
    "visual": {
      "total": 4,
      "hot": 3,
      "warm": 1,
      "cold": 0,
      "tools": ["Mermaid-CLI", "D2", "Graphviz", "PlantUML"]
    }
  },
  "overlaps": [
    {
      "domain": "visual",
      "tools": ["Mermaid-CLI", "D2", "Graphviz", "PlantUML"],
      "common_alternatives": []
    }
  ],
  "port_conflicts": [],
  "strengths": ["visual: 4 narzędzia, 3 hot"],
  "weaknesses": ["devops: tylko 1 narzędzie (actionlint)"],
  "bottlenecks": [
    "devops: actionlint jest jedynym narzędziem w krytycznej domenie"
  ],
  "coverage_score": 0.67,
  "overlap_score": 0.24,
  "priority_distribution": { "hot": 16, "warm": 1, "cold": 0 }
}
```

## Error Handling

| Error                     | Action                                    |
| ------------------------- | ----------------------------------------- |
| Brak tool_registry.json   | ❌ Fatal: "Brak rejestru narzędzi"        |
| Brak .envy                | ⚠️ Warning: "Pomijam analizę portów"      |
| Nieprawidłowy JSON        | ❌ Fatal: "Nieprawidłowy format rejestru" |
| Brak portów w run_command | ℹ️ Info: "Brak portów do analizy"         |
