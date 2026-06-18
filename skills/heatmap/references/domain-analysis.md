# Domain Coverage Analysis

Analiza pokrycia domen narzędziowych w ekosystemie.

## Definicje

| Termin             | Definicja                                 | Próg                         |
| ------------------ | ----------------------------------------- | ---------------------------- |
| **Well-covered**   | Domena z wystarczającą liczbą narzędzi    | ≥ 3 narzędzia                |
| **Gap**            | Domena z niewystarczającą liczbą narzędzi | ≤ 1 narzędzie                |
| **Coverage Score** | Odsetek dobrze pokrytych domen            | well_covered / total_domains |

## Metoda analizy

```python
def analyze_domains(tools: List[ToolInfo]) -> Dict[str, DomainStats]:
    domains = {}
    for tool in tools:
        if tool.domain not in domains:
            domains[tool.domain] = DomainStats(name=tool.domain)
        domains[tool.domain].tools.append(tool)

        # Zlicz priorytety
        if tool.priority == "hot":
            domains[tool.domain].hot_count += 1
        elif tool.priority == "warm":
            domains[tool.domain].warm_count += 1
        else:
            domains[tool.domain].cold_count += 1

    return domains
```

## Przykłady

| Domena        | Narzędzia | Hot | Warm | Cold | Status          |
| ------------- | --------- | --- | ---- | ---- | --------------- |
| visual        | 4         | 3   | 1    | 0    | ✅ Well-covered |
| code-analysis | 3         | 3   | 0    | 0    | ✅ Well-covered |
| data          | 4         | 4   | 0    | 0    | ✅ Well-covered |
| dev           | 4         | 4   | 0    | 0    | ✅ Well-covered |
| devops        | 1         | 1   | 0    | 0    | ⚠️ GAP          |
| ai            | 1         | 1   | 0    | 0    | ⚠️ GAP          |

## Coverage Score

```
coverage_score = well_covered_domains / total_domains
```

Przykład: 4 well-covered / 6 total = 0.67 (67%)

## Interpretacja

| Score    | Ocena        | Akcja               |
| -------- | ------------ | ------------------- |
| ≥ 0.8    | 🟢 Excellent | Brak działań        |
| 0.6-0.79 | 🟡 Good      | Drobne ulepszenia   |
| 0.4-0.59 | 🟠 Fair      | Wymagane inwestycje |
| < 0.4    | 🔴 Poor      | Pilne działania     |

## Rozszerzalność

| Nowa metryka      | Co mierzy                          | Jak                         |
| ----------------- | ---------------------------------- | --------------------------- |
| **Depth Score**   | Średnia liczba narzędzi per domena | total_tools / total_domains |
| **Balance Score** | Równomierność pokrycia             | stddev(tools_per_domain)    |
| **Critical Gap**  | Luki w krytycznych domenach        | Manualna ocena              |
