# Violation Types (Clean Architecture)

Definicje naruszeń Clean Architecture wykrywanych przez `check_violations()`.

## Typy naruszeń

| Typ                      | Opis                              | Severity | Przykład                        |
| ------------------------ | --------------------------------- | -------- | ------------------------------- |
| **dependency_inversion** | Inner layer importuje outer layer | 🔴 high  | `entities` importuje `adapters` |

## Logika wykrywania

```python
LAYER_ORDER = ["entities", "usecases", "adapters", "drivers"]

for file_path, imports in graph.items():
    source_layer = detect_layer(file_path)
    source_idx = LAYER_ORDER.index(source_layer)

    for imp in imports:
        target_layer = detect_layer(target_file)
        target_idx = LAYER_ORDER.index(target_layer)

        if target_idx > source_idx:  # outer imports inner
            violations.append(Violation(
                type="dependency_inversion",
                source=file_path,
                target=target_file,
                severity="high",
                detail=f"{source_layer} imports {target_layer}"
            ))
```

## Matrix Dependency Rule

| Source \ Target | entities | usecases | adapters | drivers |
| --------------- | -------- | -------- | -------- | ------- |
| **entities**    | ✅       | ❌       | ❌       | ❌      |
| **usecases**    | ✅       | ✅       | ❌       | ❌      |
| **adapters**    | ✅       | ✅       | ✅       | ❌      |
| **drivers**     | ✅       | ✅       | ✅       | ✅      |

- ✅ = dozwolone (same layer lub inner → outer)
- ❌ = **VIOLATION** (outer → inner)

## Przykłady naruszeń

| Source (plik)                   | Target (import)                            | Source Layer | Target Layer | Violation              |
| ------------------------------- | ------------------------------------------ | ------------ | ------------ | ---------------------- |
| `domain/user.py`                | `from adapters import UserRepo`            | entities     | adapters     | ❌ entities → adapters |
| `services/create_user.py`       | `from infrastructure.db import PostgresDB` | usecases     | drivers      | ❌ usecases → drivers  |
| `controllers/user_ctrl.py`      | `from domain import User`                  | adapters     | entities     | ✅ dozwolone           |
| `infrastructure/db/postgres.py` | `from services import UserService`         | drivers      | usecases     | ❌ drivers → usecases  |

## Violation Object

```python
@dataclass
class Violation:
    type: str              # "dependency_inversion"
    source: str            # source file path (relative)
    target: str            # target file path (relative)
    severity: str          # "high"
    detail: str            # "{source_layer} imports {target_layer}"
```

## Output w wyniku

```json
{
  "clean_architecture": {
    "score": 85,
    "layers": {...},
    "violations": [
      {
        "type": "dependency_inversion",
        "source": "domain/user.py",
        "target": "adapters/user_repo.py",
        "severity": "high",
        "detail": "entities imports adapters"
      }
    ],
    "violationCount": 3
  }
}
```

## Score Impact

```
clean_arch_score = (detected_layers / 4) * 100 - (violations * 5)
```

| Violations | Penalty | Przykład (4 layers detected) |
| ---------- | ------- | ---------------------------- |
| 0          | 0       | 100                          |
| 1          | -5      | 95                           |
| 2          | -10     | 90                           |
| 5          | -25     | 75                           |
| 10         | -50     | 50                           |

## Rozszerzalność (przyszłość)

| Nowy typ              | Kiedy dodać                                 | Logika                        |
| --------------------- | ------------------------------------------- | ----------------------------- |
| `circular_dependency` | Wykrywanie cykli w grafie                   | Tarjan/ Kosaraju na grafie    |
| `layer_skip`          | Pomijanie warstwy (entities → adapters)     | `target_idx - source_idx > 1` |
| `god_class`           | Wykrywanie klas z zbyt dużą liczbą importów | Threshold na `len(imports)`   |

---

_Wygenerowane z `analyzer_check.py::check_violations()`_
