# Layer Patterns (Clean Architecture)

Definicja 4 warstw Clean Architecture używanych przez `detect_layer()` i `detect_layers()`.

## LAYER_PATTERNS

Słownik mapujący nazwę warstwy na listę wzorców nazw folderów.

```python
LAYER_PATTERNS = {
    "entities": ["domain", "entities", "models", "core", "entity"],
    "usecases": [
        "usecases",
        "use_cases",
        "services",
        "interactors",
        "application",
        "app",
    ],
    "adapters": [
        "adapters",
        "controllers",
        "gateways",
        "interfaces",
        "handlers",
        "api",
    ],
    "drivers": [
        "infrastructure",
        "infra",
        "drivers",
        "frameworks",
        "external",
        "persistence",
    ],
}
```

## Tabela warstw

| Warstwa      | Wzorce folderów                                                               | Odpowiedzialność                                | Przykłady                                               |
| ------------ | ----------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------- |
| **entities** | `domain`, `entities`, `models`, `core`, `entity`                              | Business logic, domain models, enterprise rules | `domain/`, `models/`, `core/user.py`                    |
| **usecases** | `usecases`, `use_cases`, `services`, `interactors`, `application`, `app`      | Application business rules, orchestration       | `services/`, `application/`, `use_cases/create_user.py` |
| **adapters** | `adapters`, `controllers`, `gateways`, `interfaces`, `handlers`, `api`        | Interface adapters, controllers, presenters     | `controllers/`, `api/`, `handlers/`, `gateways/`        |
| **drivers**  | `infrastructure`, `infra`, `drivers`, `frameworks`, `external`, `persistence` | Frameworks, DB, UI, external systems            | `infrastructure/`, `persistence/`, `frameworks/django/` |

## Zasada Dependency Rule (Dependency Inversion)

```
entities ← usecases ← adapters ← drivers
```

- **Inner layers nie mogą importować outer layers**
- entities: zero zależności od innych warstw
- usecases: może importować entities
- adapters: może importować usecases + entities
- drivers: może importować wszystko

## Logika wykrywania

```python
def detect_layer(file_path: str, root_path: str) -> Optional[str]:
    rel_path = Path(file_path).relative_to(root_path).as_posix()
    parts = rel_path.lower().split("/")

    for layer, patterns in LAYER_PATTERNS.items():
        for part in parts:
            if part in patterns:
                return layer
    return None
```

- Sprawdza każdy segment ścieżki (case-insensitive)
- Pierwsze dopasowanie wygrywa
- `None` = folder nie należy do Clean Architecture (np. `tests/`, `docs/`, `scripts/`)

## Dependency Graph Building

```python
extensions = {
    ".py": parse_python_imports,      # ast.parse -> Import, ImportFrom
    ".ts": parse_typescript_imports,  # regex: import ... from, require()
    ".tsx": parse_typescript_imports,
    ".js": parse_typescript_imports,
    ".jsx": parse_typescript_imports,
}
```

- Pomija: `node_modules`, `__pycache__`, `.venv`, `venv`
- Zwraca graf: `{source_file: [imported_modules]}`

## Violation Detection

```python
if target_idx > source_idx:  # outer imports inner = VIOLATION
    violations.append(Violation(...))
```

- `target_idx > source_idx` = inner layer imports outer layer = **violation**
- `severity="high"` dla dependency_inversion

## Przykłady

| Ścieżka                          | Warstwa  | Dopasowanie                |
| -------------------------------- | -------- | -------------------------- |
| `domain/user.py`                 | entities | `domain` ∈ entities        |
| `services/create_user.py`        | usecases | `services` ∈ usecases      |
| `controllers/user_controller.py` | adapters | `controllers` ∈ adapters   |
| `infrastructure/db/postgres.py`  | drivers  | `infrastructure` ∈ drivers |
| `tests/test_user.py`             | None     | brak dopasowania           |
| `docs/architecture.md`           | None     | brak dopasowania           |

## Rozszerzalność

Aby dodać/zmienić wzorce:

1. Edytuj `LAYER_PATTERNS` w `analyzer_check.py`
2. Zaktualizuj tę tabelę
3. Uruchom testy na znanych projektach Clean Architecture

## Clean Architecture Score

```
detected_count = liczba wykrytych warstw (0-4)
violation_penalty = violations × 5
score = max(0, min(100, (detected_count / 4) * 100 - violation_penalty))
```

| Detected Layers | Base Score | - Violations       | Final |
| --------------- | ---------- | ------------------ | ----- |
| 4/4             | 100        | -10 (2 violations) | 90    |
| 3/4             | 75         | -5 (1 violation)   | 70    |
| 2/4             | 50         | 0                  | 50    |
| 1/4             | 25         | 0                  | 25    |
| 0/4             | 0          | 0                  | 0     |

---

_Wygenerowane z `analyzer_check.py::LAYER_PATTERNS`_
