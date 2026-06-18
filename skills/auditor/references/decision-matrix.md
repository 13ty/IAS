# Decision Matrix

Metoda oceny propozycji narzędzi używana przez auditora.

## Kryteria i wagi

| Kryterium           | Waga | Opis                                               | Skala            |
| ------------------- | ---- | -------------------------------------------------- | ---------------- |
| **Gap Fit**         | 0.30 | Jak dobrze wypełnia istniejącą lukę                | 1-10             |
| **Quality**         | 0.25 | Jakość kodu, architektura, bezpieczeństwo          | 1-10             |
| **Team Fit**        | 0.30 | Jak dobrze pasuje do stacka i umiejętności zespołu | 1-10             |
| **Adoption Effort** | 0.15 | Koszt wdrożenia, migracji, nauki                   | 1-10 (odwrócone) |

## Wzór

```python
net_benefit = (
    gap_fit * 0.30
    + quality * 0.25
    + team_fit * 0.30
    + (10 - adoption_effort) * 0.15
)
```

> **Adoption Effort jest odwrócone**: niższy wysiłek = wyższy benefit.
> Przykład: effort=2 → (10-2)=8 → 8×0.15=1.2

## Przykłady obliczeń

| Gap Fit | Quality | Team Fit | Effort | Net Benefit | Verdict                 |
| ------- | ------- | -------- | ------ | ----------- | ----------------------- |
| 9       | 8       | 9        | 3      | **8.55**    | 🎉 ZAPROSZENIE DO TAŃCA |
| 7       | 6       | 7        | 5      | **6.65**    | 🧪 PILOT                |
| 4       | 5       | 4        | 8      | **4.05**    | 🧪 PILOT                |
| 3       | 4       | 3        | 9      | **3.30**    | 📚 LEKCJA               |
| 8       | 7       | 8        | 6      | **7.15**    | 🎉 ZAPROSZENIE DO TAŃCA |

## Progi decyzyjne

| Net Benefit | Verdict                     | Akcja                          |
| ----------- | --------------------------- | ------------------------------ |
| > 7.0       | 🎉 **ZAPROSZENIE DO TAŃCA** | Pełna adopcja                  |
| > 4.0       | 🧪 **PILOT**                | Trial w ograniczonym zakresie  |
| ≤ 4.0       | 📚 **LEKCJA**               | Uczymy się, ale nie adoptujemy |

## Skalowanie wag

```python
weights = {
    "gap_fit": 0.30,
    "quality": 0.25,
    "team_fit": 0.30,
    "adoption_effort": 0.15,
}
```

- Suma wag = 1.0 (100%)
- Team Fit + Gap Fit = 60% (najważniejsze)
- Quality = 25% (jakość techniczna)
- Adoption Effort = 15% (koszt, najmniej ważny)

## Override rules

| Sytuacja               | Modyfikacja          |
| ---------------------- | -------------------- |
| **Overlap detected**   | Gap Fit -= 3 (min 1) |
| **Brak licencji**      | Quality -= 2         |
| **Stars > 1000**       | Quality += 1         |
| **Critical CVE**       | Quality = 1          |
| **Team already uses**  | Team Fit += 2        |
| **Requires new stack** | Team Fit -= 2        |

## Wartości domyślne (symulacja)

```python
gap_fit = 7      # Zakładamy że user nie proponuje czegoś co już mamy
quality = 6      # Domyślna ocena wstępna
team_fit = 5     # Domyślna - wymaga analizy stacka
adoption_effort = 5  # Domyślna
```

## Output

```json
{
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

## Ograniczenia

- **Wartości domyślne** — Symulacja bez rzeczywistej analizy
- **Subiektywne scoringi** — Wymaga eksperta do oceny
- **Brak cost modeling** — Effort = heurystyka, nie rzeczywisty koszt
- **Binary thresholds** — Może przegapić edge cases

## Rozszerzalność (przyszłość)

| Nowe kryterium    | Waga | Opis                          |
| ----------------- | ---- | ----------------------------- |
| **Security**      | 0.15 | CVE count, scorecard, license |
| **Community**     | 0.10 | Contributors, issues, PRs     |
| **Maturity**      | 0.10 | Version history, releases     |
| **Performance**   | 0.10 | Benchmarks, load tests        |
| **Documentation** | 0.10 | Completeness, examples        |

---

_Wygenerowane z `skills/auditor/SKILL.md` oraz `scripts/proposal_audit.py`_
