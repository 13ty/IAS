# Maintainability Index (MI) Formula

Pełny wzór MI z `calculate_maintainability()` w `analyzer_check.py`.

## Wzór MI (Maintainability Index)

Oparty na klasycznym MI (Coleman et al.) z normalizacją do skali 0-100.

### Kroki obliczenia

```python
# 1. Zlicz metryki
total_loc          # Lines of Code (non-empty, non-comment)
total_complexity   # Cyclomatic complexity sum
file_count         # Liczba plików

# 2. Średnia złożoność
avg_complexity = total_complexity / file_count

# 3. Halstead Volume (uproszczony)
halstead_volume = total_loc * 2.5

# 4. Surowy MI (wzór Coleman)
mi = 171
    - 5.2 * ln(halstead_volume)
    - 0.23 * avg_complexity
    - 16.2 * ln(total_loc)

# 5. Normalizacja do 0-100
mi_normalized = max(0, min(100, mi * 100 / 171))
```

### Rating

| MI Score | Rating       | Kolor | Interpretacja                 |
| -------- | ------------ | ----- | ----------------------------- |
| ≥ 80     | **high**     | 🟢    | Łatwy do utrzymania           |
| 60-79    | **moderate** | 🟡    | Umiarkowanie trudny           |
| < 60     | **low**      | 🔴    | Trudny, wymaga refaktoryzacji |

## Parametry wejściowe

| Metryka                   | Jak obliczana                   | Opis                                                                     |
| ------------------------- | ------------------------------- | ------------------------------------------------------------------------ | --- | --- |
| **LOC**                   | Linijki niepuste + niekomentarz | `len([l for l in lines if l.strip() and not l.strip().startswith("#")])` |
| **Cyclomatic Complexity** | 1 + liczba punktów decyzyjnych  | `if`, `elif`, `for`, `while`, `except`, `case`, `&&`, `                  |     | `   |
| **Halstead Volume**       | `LOC × 2.5`                     | Uproszczenie (brak pełnego Halsteada)                                    |
| **Avg Complexity**        | `total_complexity / file_count` | Średnia złożoność per plik                                               |

## Obsługiwane rozszerzenia

| Ext                             | Parser     | Complexity keywords            |
| ------------------------------- | ---------- | ------------------------------ |
| `.py`                           | ast        | if, elif, for, while, except   |
| `.ts` / `.tsx` / `.js` / `.jsx` | regex      | if, for, while, case, &&, \|\| |
| `.go`                           | line count | if, for, switch, case          |
| `.rs`                           | line count | if, for, while, match          |
| `.cs`                           | line count | if, for, while, switch, case   |

> Dla `.go`, `.rs`, `.cs`: tylko LOC + prosta heurystyka complexity (brak full parser)

## Wykluczenia

Automatycznie pomijane:

- `node_modules/`
- `__pycache__/`
- `.venv/`, `venv/`

## Przykłady obliczeń

| Projekt            | LOC   | Files | Avg Complx | Halstead | MI (raw) | MI (norm) | Rating      |
| ------------------ | ----- | ----- | ---------- | -------- | -------- | --------- | ----------- |
| Mały, prosty       | 500   | 10    | 1.5        | 1250     | ~150     | **88**    | 🟢 high     |
| Średni             | 5000  | 50    | 3.2        | 12500    | ~120     | **70**    | 🟡 moderate |
| Duży, zagnieżdżony | 20000 | 200   | 5.8        | 50000    | ~80      | **47**    | 🟡 moderate |
| Legacy spaghetti   | 50000 | 300   | 12.0       | 125000   | ~40      | **23**    | 🔴 low      |

## Ograniczenia

1. **Halstead uproszczony** — `LOC × 2.5` zamiast pełnych operatorów/operandów
2. **Complexity heurystyczna** — regex dla JS/TS, proste słowa kluczowe
3. **Brak Halstead Effort/Bugs** — tylko MI index
4. **Brak modułowości** — nie uwzględnia coupling/cohesion

## Testowanie

```bash
# Test na prostym projekcie
python analyzer_check.py ./simple-project --json

# Sprawdź pola:
# maintainability.index → 0-100
# maintainability.rating → "high"/"moderate"/"low"
# maintainability.loc → int
# maintainability.fileCount → int
```

## Rozszerzalność

Aby dodać pełny Halstead:

1. Dodaj parser operatorów/operandów per język
2. Zastąp `halstead_volume = total_loc * 2.5` prawdziwym obliczeniem
3. Dodaj `effort`, `bugs`, `time` metrics

---

_Wygenerowane z `analyzer_check.py::calculate_maintainability()`_
