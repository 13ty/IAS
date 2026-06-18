# Strength/Weakness Analysis

Analiza mocnych i słabych stron ekosystemu narzędzi.

## Metoda

### Mocne Strony (Strengths)

```python
def find_strengths(domains: Dict[str, DomainStats]) -> List[str]:
    strengths = []
    for name, stats in domains.items():
        if stats.is_well_covered and stats.hot_count >= 2:
            strengths.append(f"{name}: {stats.total} narzędzi, {stats.hot_count} hot")
    return strengths
```

**Kryteria:**

- Domena dobrze pokryta (≥3 narzędzi)
- Większość hot (≥2)

### Słabe Strony (Weaknesses)

```python
def find_weaknesses(domains: Dict[str, DomainStats]) -> List[str]:
    weaknesses = []
    for name, stats in domains.items():
        if stats.is_gap:
            weaknesses.append(f"{name}: tylko {stats.total} narzędzie ({stats.tools[0].name})")
    return weaknesses
```

**Kryteria:**

- Domena z luką (≤1 narzędzia)
- Niski priorytet (cold > hot)

### Wąskie Gardła (Bottlenecks)

```python
def find_bottlenecks(domains: Dict[str, DomainStats]) -> List[str]:
    bottlenecks = []
    critical_domains = {"devops", "security", "ai", "data"}

    for name, stats in domains.items():
        if name in critical_domains and stats.total <= 1:
            bottlenecks.append(f"{name}: {stats.tools[0].name} jest jedynym narzędziem w krytycznej domenie")
    return bottlenecks
```

**Kryteria:**

- Krytyczna domena (devops, security, ai, data)
- Single point of failure (1 narzędzie)

## Przykłady

| Kategoria     | Domena | Ocena              | Opis                    |
| ------------- | ------ | ------------------ | ----------------------- |
| ✅ Strength   | visual | 4 narzędzia, 3 hot | Dobrze pokryta          |
| ✅ Strength   | data   | 4 narzędzia, 4 hot | Świetnie pokryta        |
| ❌ Weakness   | devops | 1 narzędzie        | GAP                     |
| ❌ Weakness   | ai     | 1 narzędzie        | GAP                     |
| ⚠️ Bottleneck | devops | actionlint         | Single point of failure |
| ⚠️ Bottleneck | ai     | PromptLab          | Single point of failure |

## Score

```
health_score = (strengths - weaknesses - bottlenecks) / total_domains
```

| Score    | Ocena        | Akcja               |
| -------- | ------------ | ------------------- |
| ≥ 0.8    | 🟢 Excellent | Brak działań        |
| 0.6-0.79 | 🟡 Good      | Drobne ulepszenia   |
| 0.4-0.59 | 🟠 Fair      | Wymagane inwestycje |
| < 0.4    | 🔴 Poor      | Pilne działania     |

## Rekomendacje

| Typ            | Akcja                     | Priorytet |
| -------------- | ------------------------- | --------- |
| **Gap**        | Dodaj narzędzie do domeny | HIGH      |
| **Bottleneck** | Dodaj alternatywę         | CRITICAL  |
| **Overlap**    | Rozważ konsolidację       | MEDIUM    |
| **Cold**       | Zaktualizuj priorytet     | LOW       |
