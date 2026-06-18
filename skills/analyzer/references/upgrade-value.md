# Upgrade Value Calculation

Metoda oceny wartości migracji/aktualizacji w `calculate_upgrade_value()`.

## Wzór

```python
def calculate_upgrade_value(current_path: str, target_path: str) -> Dict:
    current_mi = calculate_maintainability(current_path)
    target_mi = calculate_maintainability(target_path)

    mi_diff = target_mi["index"] - current_mi["index"]
    loc_ratio = target_mi["loc"] / max(1, current_mi["loc"])

    # Benefit
    if mi_diff > 10:
        benefit = "Higher maintainability"
    elif mi_diff > 0:
        benefit = "Slightly better maintainability"
    else:
        benefit = "Similar or lower maintainability"

    # Effort / Risk
    if loc_ratio > 2:
        effort = "high"
        risk = "Significant codebase size difference"
    elif loc_ratio > 1.5:
        effort = "medium"
        risk = "Moderate codebase size difference"
    else:
        effort = "low"
        risk = "Similar codebase size"

    # Score 0-1
    score = max(0, min(1, (mi_diff + 50) / 100))
```

## Tabela decyzyjna

### Maintainability Diff (mi_diff)

| mi_diff | Benefit                            | Interpretacja                     |
| ------- | ---------------------------------- | --------------------------------- |
| > 10    | "Higher maintainability"           | Znacząca poprawa - warto migrować |
| 1-10    | "Slightly better maintainability"  | Lekka poprawa - opcjonalne        |
| ≤ 0     | "Similar or lower maintainability" | Brak korzyści / pogorszenie       |

### LOC Ratio (target/current)

| loc_ratio | Effort     | Risk                                   |
| --------- | ---------- | -------------------------------------- |
| > 2.0     | **high**   | "Significant codebase size difference" |
| 1.5 - 2.0 | **medium** | "Moderate codebase size difference"    |
| ≤ 1.5     | **low**    | "Similar codebase size"                |

### Score (0-1)

```
score = clamp((mi_diff + 50) / 100, 0, 1)
```

| mi_diff | Score | Interpretacja        |
| ------- | ----- | -------------------- |
| -50     | 0.0   | Pogorszenie o 50 pkt |
| 0       | 0.5   | Neutralne            |
| +10     | 0.6   | Lekka poprawa        |
| +25     | 0.75  | Umiarkowana poprawa  |
| +50     | 1.0   | Maksymalna korzyść   |

## Przykłady

| Current MI | Target MI | mi_diff | loc_ratio | Score | Effort   | Benefit  | Verdict        |
| ---------- | --------- | ------- | --------- | ----- | -------- | -------- | -------------- |
| 45         | 75        | +30     | 1.2       | 0.80  | low      | Higher   | ✅ **Migruj**  |
| 60         | 68        | +8      | 1.1       | 0.58  | low      | Slightly | ⚠️ Opcjonalnie |
| 70         | 65        | -5      | 0.9       | 0.45  | low      | Similar  | ❌ Nie         |
| 50         | 85        | +35     | 2.5       | 0.85  | **high** | Higher   | ⚠️ Ryzyko      |

## Integracja z CLI

```bash
python analyzer_check.py ./current --compare-with ./target --json
```

Output:

```json
{
  "upgrade_value": {
    "current": { "path": "./current", "maintainability": 55.2 },
    "target": { "path": "./target", "maintainability": 82.1 },
    "score": 0.77,
    "effort": "low",
    "benefit": "Higher maintainability",
    "risk": "Similar codebase size"
  }
}
```

## Rekomendacje generowane

W `analyze_repository()` na podstawie upgrade_value + violations + MI:

```python
recommendations = []
if not layer_scores["entities"]["detected"]:
    recommendations.append("Consider adding a domain/entities layer")
if not layer_scores["usecases"]["detected"]:
    recommendations.append("Consider adding a usecases/services layer")
if violations:
    recommendations.append(f"Fix {len(violations)} dependency violations")
if maintainability["rating"] == "low":
    recommendations.append("Refactor to improve maintainability")
```

## Ograniczenia

1. **Tylko MI + LOC** — brak analizy: test coverage, security, performance, team familiarity
2. **Binary score** — nie uwzględnia częściowej adopcji
3. **Brak cost modeling** — effort = tylko LOC ratio, nie uwzględnia: breaking changes, learning curve, tooling

## Rozszerzalność (przyszłość)

| Nowa metryka           | Co doda               | Jak                                 |
| ---------------------- | --------------------- | ----------------------------------- |
| **Test coverage diff** | Porównanie % pokrycia | `coverage.py` / `jest --coverage`   |
| **Security diff**      | Luki CVE w deps       | `pip-audit` / `npm audit`           |
| **Breaking changes**   | API compatibility     | `git diff` + semantic versioning    |
| **Team effort**        | Szacunek person-dni   | Heurystyka: LOC × complexity factor |
| **Migration path**     | Automatyczne kroki    | Codemod / AST transforms            |

---

_Wygenerowane z `analyzer_check.py::calculate_upgrade_value()`_
