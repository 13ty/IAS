# Health Score Formula

Wzór obliczania zdrowia projektu w `calculate_health()`.

## Wzór główny

```
Health Coverage = max(0, 100 - (high_gaps × 20 + medium_gaps × 10))
```

## Parametry

| Zmienna       | Źródło                         | Waga           |
| ------------- | ------------------------------ | -------------- |
| `high_gaps`   | Liczba luk o severity="high"   | ×20            |
| `medium_gaps` | Liczba luk o severity="medium" | ×10            |
| `low_gaps`    | Liczba luk o severity="low"    | 0 (tylko info) |

## Składowe wyniku

```python
return {
    "coverage": coverage,              # 0-100%
    "totalComponents": total,          # Liczba wszystkich komponentów
    "securityRisks": high_gaps,        # = high_gaps
    "staleDependencies": stale_count,  # Zawsze 0 (nieimplementowane)
    "gapCount": len(gaps),             # Łączna liczba luk
}
```

## Przykłady obliczeń

| High | Medium | Low | Coverage | Status           |
| ---- | ------ | --- | -------- | ---------------- |
| 0    | 0      | 0   | 100%     | 🟢 Idealny       |
| 0    | 1      | 0   | 90%      | 🟢 Bardzo dobry  |
| 1    | 0      | 0   | 80%      | 🔵 Dobry         |
| 0    | 2      | 0   | 80%      | 🔵 Dobry         |
| 1    | 1      | 0   | 70%      | 🟡 Średni        |
| 2    | 0      | 0   | 60%      | 🟡 Średni        |
| 1    | 3      | 0   | 50%      | 🟠 Słaby         |
| 3    | 0      | 0   | 40%      | 🔴 Krytyczny     |
| 5    | 5      | 0   | 0% (min) | 🔴 Brak pokrycia |

## Interpretacja

| Coverage | Label            | Akcja                      |
| -------- | ---------------- | -------------------------- |
| 90-100%  | 🟢 **Excellent** | Tylko monitoring           |
| 70-89%   | 🔵 **Good**      | Planuj poprawki medium     |
| 50-69%   | 🟡 **Fair**      | Priorytet: high gaps       |
| 30-49%   | 🟠 **Poor**      | Natychmiast: high + medium |
| 0-29%    | 🔴 **Critical**  | Blokuje release            |

## Stale Dependencies ( nieużywane )

Pole `"staleDependencies": 0` — placeholder na przyszłość:

- Możliwość: porównanie wersji z najnowszymi na npm/PyPI
- Wymaga: API calls do registry (rate limits)
- Można dodać jako opcjonalne `--check-stale`

## Testowanie

```bash
# 0 gaps → 100%
python inventory_scan.py ./test-projects/perfect --json

# 1 high (Testing) → 80%
python inventory_scan.py ./test-projects/no-tests --json

# 2 medium (Doc, License) → 80%
python inventory_scan.py ./test-projects/no-docs --json
```

---

_Wygenerowane z `inventory_scan.py::calculate_health()`_
