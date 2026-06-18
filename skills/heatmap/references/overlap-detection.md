# Overlap Detection

Wykrywanie nakładania się narzędzi w obrębie domen.

## Metoda

Grupowanie narzędzi po wspólnych alternatywach — narzędzia dzielące te same alternatywy = potencjalne nakładanie.

```python
def detect_overlaps(tools: List[ToolInfo]) -> List[OverlapGroup]:
    overlaps = []
    domain_tools = defaultdict(list)

    for tool in tools:
        domain_tools[tool.domain].append(tool)

    for domain, dt in domain_tools.items():
        # Grupuj po wspólnych alternatywach
        alt_groups = defaultdict(list)
        for tool in dt:
            for alt in tool.alternatives:
                alt_groups[alt].append(tool.id)

        # Wykryj nakładania (≥2 narzędzia dzielące alternatywę)
        for alt, tool_ids in alt_groups.items():
            if len(tool_ids) >= 2:
                overlaps.append(OverlapGroup(
                    domain=domain,
                    tools=tool_ids,
                    common_alternatives=[alt]
                ))

    return overlaps
```

## Przykłady

| Domena        | Narzędzia                       | Wspólne Alternatywy | Ocena                      |
| ------------- | ------------------------------- | ------------------- | -------------------------- |
| visual        | Mermaid, D2, Graphviz, PlantUML | (brak)              | ⚠️ Nakładanie funkcjonalne |
| data          | DuckDB, jq, yq                  | (brak)              | ✅ Różne zastosowania      |
| code-analysis | TreeSitter, Semgrep, cloc       | (brak)              | ✅ Różne zastosowania      |

## Overlap Score

```
overlap_score = overlapping_tools / total_tools
```

Przykład: 4 narzędzia w visual (nakładanie) / 16 total = 0.25 (25%)

## Interpretacja

| Score   | Ocena          | Akcja               |
| ------- | -------------- | ------------------- |
| < 0.1   | 🟢 Niskie      | Brak działań        |
| 0.1-0.3 | 🟡 Umiarkowane | Monitoruj           |
| 0.3-0.5 | 🟠 Wysokie     | Rozważ konsolidację |
| > 0.5   | 🔴 Krytyczne   | Pilna optymalizacja |

## Typy nakładania

| Typ                | Opis                     | Przykład                       |
| ------------------ | ------------------------ | ------------------------------ |
| **Funkcyjne**      | Narzędzia robią to samo  | 4 generatory diagramów         |
| **Technologiczne** | Ta sama technologia      | 2 ORM-y dla tego samego języka |
| **Segmentowe**     | Dla tego samego segmentu | 2 test frameworki              |
