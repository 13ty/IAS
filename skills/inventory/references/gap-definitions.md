# Gap Definitions

Definicje luk wykrywanych przez `detect_gaps()` z severity mapping.

## Kategorie luk

| Kategoria         | Severity  | Warunek wykrycia                                                                                                            | Sugerowana akcja                                 |
| ----------------- | --------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **Testing**       | 🔴 high   | Brak folderu `tests/` / `test/` / `__tests__` / `spec/` ORAZ brak plików `test_*.py`, `*_test.py`, `*.test.ts`, `*.spec.ts` | Dodaj test framework (pytest, vitest, jest) + CI |
| **Documentation** | 🟡 medium | Brak `README.md` w root projekcie                                                                                           | Stwórz README z opisem, instalacją, użyciem      |
| **License**       | 🟡 medium | Brak `LICENSE` ani `LICENSE.md`                                                                                             | Dodaj licencję (MIT, Apache-2.0, BSD-3)          |
| **Security**      | ⚪ low    | Brak `SECURITY.md`                                                                                                          | Dodaj politykę zgłaszania luk                    |
| **CI/CD**         | 🟡 medium | Brak `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`                                                                  | Skonfiguruj CI (GitHub Actions, GitLab CI)       |
| **Linting**       | ⚪ low    | Brak configu: `.eslintrc*`, `pyproject.toml`, `.flake8`, `ruff.toml`                                                        | Dodaj linting (eslint, ruff, flake8)             |

## Logika wykrywania

```python
# Testing
test_dirs = ["tests", "test", "__tests__", "spec"]
has_tests = any((root / d).exists() for d in test_dirs)
if not has_tests:
    py_test_files = list(root.rglob("test_*.py")) + list(root.rglob("*_test.py"))
    js_test_files = list(root.rglob("*.test.ts")) + list(root.rglob("*.spec.ts"))
    if not py_test_files and not js_test_files:
        gaps.append(Gap("Testing", "high", "No test framework or test files detected"))

# Documentation
if not (root / "README.md").exists():
    gaps.append(Gap("Documentation", "medium", "Missing README.md"))

# License
if not (root / "LICENSE").exists() and not (root / "LICENSE.md").exists():
    gaps.append(Gap("License", "medium", "Missing LICENSE file"))

# Security
if not (root / "SECURITY.md").exists():
    gaps.append(Gap("Security", "low", "Missing SECURITY.md"))

# CI/CD
ci_dirs = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"]
has_ci = any((root / d).exists() for d in ci_dirs)
if not has_ci:
    gaps.append(Gap("CI/CD", "medium", "No CI/CD configuration detected"))

# Linting
lint_configs = [
    ".eslintrc", ".eslintrc.js", ".eslintrc.json",
    "pyproject.toml", ".flake8", "ruff.toml"
]
has_lint = any((root / c).exists() for c in lint_configs)
if not has_lint:
    gaps.append(Gap("Linting", "low", "No linting configuration detected"))
```

## Severity Matrix

| Severity   | Waga w Health Score | Priorytet naprawy            |
| ---------- | ------------------- | ---------------------------- |
| **high**   | 20 pkt              | Natychmiast — ryzyko jakości |
| **medium** | 10 pkt              | W najbliższym sprincie       |
| **low**    | 0 pkt (tylko info)  | Gdy czas pozwala             |

> Health coverage = max(0, 100 - (high_gaps × 20 + medium_gaps × 10))

## Rozszerzalność

Aby dodać nową kategorię:

1. Dodaj warunek w `detect_gaps()` z odpowiednim severity
2. Zaktualizuj tę tabelę
3. Opcjonalnie: dodaj w `references/scout-gap-keywords.md` słowa kluczowe dla Scou-ta

## Przykłady

| Projekt                                        | Wykryte luki                                                                                            |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Pusty folder                                   | Testing (high), Documentation (medium), License (medium), Security (low), CI/CD (medium), Linting (low) |
| Tylko README                                   | Testing (high), License (medium), Security (low), CI/CD (medium), Linting (low)                         |
| Pełny setup (tests, CI, lint, license, README) | _brak luk_                                                                                              |

---

_Wygenerowane z `inventory_scan.py::detect_gaps()`_
