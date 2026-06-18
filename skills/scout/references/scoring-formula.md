# Scoring Formulas (Scout)

Formuły scoringu używane przez `scout_search.py` do rankingu repozytoriów.

## Relevance Score

```python
def calculate_relevance(repo: Dict, gap_keywords: List[str]) -> float:
    text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()

    matches = 0
    for keyword in gap_keywords:
        if keyword.lower() in text:
            matches += 1

    return min(1.0, matches / max(1, len(gap_keywords)))
```

### Logika

- Sprawdza czy keyword występuje w nazwie lub opisie repo
- Case-insensitive
- Relevance = matches / total_keywords (capped at 1.0)

### Przykłady

| Keywords                      | Nazwa          | Opis                     | Matches | Relevance |
| ----------------------------- | -------------- | ------------------------ | ------- | --------- |
| ["pytest", "jest"]            | "pytest-xdist" | "Pytest plugin"          | 2       | 1.0       |
| ["security", "vulnerability"] | "bandit"       | "Python security linter" | 1       | 0.5       |
| ["react", "vue"]              | "angular"      | "Framework"              | 0       | 0.0       |

## Scorecard (Quality Score)

```python
def estimate_scorecard(repo: Dict) -> float:
    score = 0

    # 1. Description present (+0.1)
    if repo.get("description"):
        score += 0.1

    # 2. Stars popularity (+0.1-0.2)
    stars = repo.get("stargazersCount", 0)
    if stars > 1000:      score += 0.2
    elif stars > 100:     score += 0.15
    elif stars > 10:      score += 0.1

    # 3. Forks activity (+0.1-0.15)
    forks = repo.get("forksCount", 0)
    if forks > 100:       score += 0.15
    elif forks > 10:      score += 0.1

    # 4. Recency (+0.1-0.2)
    updated = repo.get("updatedAt", "")
    if updated:
        days_since = (now - update_date).days
        if days_since < 30:   score += 0.2
        elif days_since < 90: score += 0.15
        elif days_since < 180: score += 0.1

    # 5. License (+0.15)
    if repo.get("licenseInfo"):
        score += 0.15

    return min(1.0, score)
```

### Scorecard Breakdown

| Metric          | Threshold  | Points | Max      |
| --------------- | ---------- | ------ | -------- |
| **Description** | present    | +0.1   | 0.1      |
| **Stars**       | > 1000     | +0.2   | 0.2      |
|                 | > 100      | +0.15  |          |
|                 | > 10       | +0.1   |          |
| **Forks**       | > 100      | +0.15  | 0.15     |
|                 | > 10       | +0.1   |          |
| **Recency**     | < 30 days  | +0.2   | 0.2      |
|                 | < 90 days  | +0.15  |          |
|                 | < 180 days | +0.1   |          |
| **License**     | present    | +0.15  | 0.15     |
| **TOTAL**       |            |        | **0.85** |

> Maksymalny scorecard = 0.85 (bez bonusu). W praktyce ~0.6-0.8 dla dobrych repo.

## Final Score

```python
final_score = relevance * 0.5 + scorecard * 0.5
```

| Component     | Weight | Opis                          |
| ------------- | ------ | ----------------------------- |
| **Relevance** | 0.5    | Jak dobrze repo pasuje do luk |
| **Scorecard** | 0.5    | Jakość / popularność repo     |

### Przykłady final_score

| Repo        | Stars | Forks | Updated | License | Relevance | Scorecard | Final    |
| ----------- | ----- | ----- | ------- | ------- | --------- | --------- | -------- |
| pytest      | 12k   | 800   | 5d      | MIT     | 1.0       | 0.85      | **0.93** |
| jest        | 45k   | 5k    | 10d     | MIT     | 0.5       | 0.85      | **0.68** |
| random-tool | 50    | 5     | 200d    | None    | 0.0       | 0.2       | **0.10** |

## Ranking

```python
results.sort(key=lambda r: r.final_score, reverse=True)
return results[:max_results]
```

- Sortowanie malejące po final_score
- Zwraca top N (domyślnie 10)

## Gap Coverage

```python
gap_coverage[repo_key].add(gap)  # Deduplikacja per gap
```

- Repo może pokrywać wiele luk
- `gap_coverage` = lista unikalnych luk
- Używane w summary: `gaps_covered`, `gaps_missing`

## Output Fields

```json
{
  "repo": "owner/name",
  "url": "https://github.com/owner/name",
  "description": "...",
  "stars": 12000,
  "forks": 800,
  "language": "Python",
  "updated_at": "2024-01-15T10:00:00Z",
  "license": "MIT",
  "relevance_score": 1.0,
  "estimated_scorecard": 0.85,
  "final_score": 0.93,
  "gap_coverage": ["testing"]
}
```

## Ograniczenia

- **Relevance = binary keyword matching** — brak semantycznego searchu
- **Scorecard = heurystyczny** — nie uwzględnia: test coverage, security, maintainability
- **Stars bias** — popularne != najlepsze
- **Recency bias** — nowe repo mogą być lepsze niż stare
- **Brak cost estimate** — nie uwzględnia effort adopcji

## Rozszerzalność (przyszłość)

| Nowa metryka              | Co doda                     | Jak                                               |
| ------------------------- | --------------------------- | ------------------------------------------------- |
| **Semantic relevance**    | Embedding similarity        | `sentence-transformers` + repo desc               |
| **Activity score**        | Commits per month           | `gh api repos/{owner}/{repo}/commits`             |
| **Contributor diversity** | Bus factor                  | `gh api repos/{owner}/{repo}/contributors`        |
| **Security score**        | OpenSSF Scorecard           | `gh api repos/{owner}/{repo}/security-advisories` |
| **Adoption effort**       | LOC, deps, breaking changes | `analyzer_check.py` on repo                       |
| **Maturity**              | Version history, releases   | `gh api repos/{owner}/{repo}/releases`            |

---

_Wygenerowane z `scout_search.py::calculate_relevance()` + `estimate_scorecard()`_
