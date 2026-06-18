# Ecosystem Markers

Lista plików markerowych używanych przez `detect_ecosystems()` do wykrywania ekosystemów w projekcie.

## Tabela markerów

| Ecosystem  | Pliki markerowe    | Opis                               |
| ---------- | ------------------ | ---------------------------------- |
| **node**   | `package.json`     | Standardowy manifest npm/yarn/pnpm |
| **python** | `requirements.txt` | Legacy Python dependencies         |
|            | `pyproject.toml`   | Modern Python packaging (PEP 621)  |
|            | `setup.py`         | Legacy setuptools                  |
|            | `Pipfile`          | Pipenv dependencies                |
| **dotnet** | `*.csproj`         | C# project files                   |
|            | `*.sln`            | Visual Studio solution             |
| **go**     | `go.mod`           | Go modules                         |
| **rust**   | `Cargo.toml`       | Rust Cargo manifest                |
| **java**   | `pom.xml`          | Maven build                        |
|            | `build.gradle`     | Gradle build                       |

## Logika wykrywania

```python
for ecosystem, files in markers.items():
    for pattern in files:
        if list(root.glob(pattern)):
            ecosystems.append(ecosystem)
            break
```

- Pierwszy znaleziony marker dla ekosystemu dodaje go do listy
- `break` zapobiega dodawaniu duplikatów
- Wykrywane są wszystkie ekosystemy obecne w projekcie (może być polyglot)

## Rozszerzalność

Aby dodać nowy ekosystem:

1. Dodaj wpis do słownika `markers` w `detect_ecosystems()`
2. Zaimplementuj parser w nowej funkcji `parse_<ecosystem>()`
3. Dodaj wpisy do `known_good` / `known_outdated` w `classify_radar()`
4. Zaktualizuj tę dokumentację

## Przykłady

| Projekt                        | Wykryte ekosystemy     |
| ------------------------------ | ---------------------- |
| React + FastAPI                | `node`, `python`       |
| .NET API + React frontend      | `dotnet`, `node`       |
| Go microservice                | `go`                   |
| Mono-repo (Node + Python + Go) | `node`, `python`, `go` |

---

_Wygenerowane z `inventory_scan.py::detect_ecosystems()`_
