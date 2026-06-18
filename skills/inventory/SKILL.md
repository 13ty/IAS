---
description: >
  Inventory — skanuje lokalny ekosystem programistyczny. Generuje SBOM, klasyfikuje technologie
  wg Thoughtworks Technology Radar, wykrywa luki bezpieczeństwa i narzędziowe.
  Używany przez pipeline IAS: Inventory → Analyzer → Scout.

trigger_words:
  - zeskanuj mój projekt
  - co mam zainstalowane
  - inventory mojego stacka
  - SBOM dla mojego projektu
  - sprawdź dependencies
  - radar technologiczny
  - jakie mam narzędzia
  - czego mi brakuje
  - scan my project
  - what do I have installed
  - project inventory
  - dependency check
  - SBOM generator
  - tech radar

examples:
  - "Zeskanuj mój projekt i powiedz czego mi brakuje"
  - "Wygeneruj SBOM dla bieżącego katalogu"
  - "Pokaż Technology Radar dla mojego stacka"
  - "Sprawdź czy mam wszystkie narzędzia do Python developmentu"
  - "Inventory mojego projektu z wykryciem luk"

negatives:
  - Do NOT use for analyzing single repositories (use analyzer)
  - Do NOT use for finding alternatives on GitHub (use scout)
  - Do NOT use for heatmap visualization (use heatmap)
---

# Skill: Inventory

## Purpose

Mapuje lokalny ekosystem programistyczny — generuje SBOM, klasyfikuje technologie wg Technology Radar, wykrywa luki.

## Trigger

Aktywuj gdy użytkownik mówi:

- "Zeskanuj mój projekt"
- "Co mam zainstalowane?"
- "Inventory mojego stacka"
- "SBOM dla mojego projektu"
- "Sprawdź dependencies"

## Methodology Sources

- **OWASP CycloneDX**: SBOM standard (format wyjściowy)
- **Thoughtworks Technology Radar**: Klasyfikacja Adopt/Trial/Assess/Hold

## Workflow

### Step 1: Detect Project Type

Skanuj katalog główny w poszukiwaniu plików manifestów:

- `package.json` → Node.js
- `requirements.txt` / `pyproject.toml` → Python
- `*.csproj` / `*.sln` → .NET
- `go.mod` → Go
- `Cargo.toml` → Rust
- `pom.xml` / `build.gradle` → Java

### Step 2: Generate SBOM

Wywołaj `cdxgen` dla wykrytych ekosystemów:

```bash
cdxgen -t {ecosystem} -o sbom.json {project_path}
```

Jeśli cdxgen nie jest zainstalowany:

1. Informuj użytkownika
2. Fallback: parsuj pliki manifestów ręcznie

### Step 3: Scan Vulnerabilities

Wywołaj `grype` na wygenerowanym SBOM:

```bash
grype sbom.json -o json > vulnerabilities.json
```

### Step 4: Classify on Radar

Zastosuj reguły klasyfikacji:

| Ring       | Criteria                                                    |
| ---------- | ----------------------------------------------------------- |
| **Adopt**  | Version matches latest stable, no CVEs, actively maintained |
| **Trial**  | Newer version available, minor CVEs, good community         |
| **Assess** | Outdated (1-2 major versions), some CVEs                    |
| **Hold**   | EOL, critical CVEs, abandoned                               |

### Step 5: Detect Gaps

Sprawdź:

- [ ] Test coverage (look for test directories, test files)
- [ ] Documentation (README, docs/)
- [ ] License file
- [ ] SECURITY.md
- [ ] CI/CD configuration
- [ ] Linting/formatting config

### Step 6: Generate TechProfile

Zapisz wynik do `state/tech_stack_oracle.json`:

```json
{
  "timestamp": "2026-03-31T12:00:00Z",
  "project": "MyProject",
  "inventory": {
    "sbom": { "format": "CycloneDX-1.5", "components": [...] },
    "radar": {
      "adopt": ["Python 3.11", "FastAPI"],
      "trial": ["Ruff"],
      "assess": ["SQLAlchemy 1.x"],
      "hold": ["Python 3.8"]
    },
    "vulnerabilities": [...],
    "gaps": [
      { "category": "Testing", "severity": "high", "detail": "No test framework" },
      { "category": "Security", "severity": "medium", "detail": "Missing SECURITY.md" }
    ]
  }
}
```

## Output Contract

```json
{
  "sbom": { "format": "...", "components": [...] },
  "radar": { "adopt": [...], "trial": [...], "assess": [...], "hold": [...] },
  "vulnerabilities": [...],
  "gaps": [...],
  "health": {
    "coverage": 0.85,
    "staleDepCount": 3,
    "securityRisks": 2
  }
}
```

## Quality Criteria

- SBOM coverage ≥95% of actual dependencies
- Radar classification accuracy ≥90%
- Gap detection precision ≥80%

## Error Handling

| Error                        | Action                                  |
| ---------------------------- | --------------------------------------- |
| cdxgen not installed         | Fallback to manual parsing              |
| grype not installed          | Skip vulnerability scan, note in output |
| Multiple ecosystems detected | Scan each, merge results                |
| Empty project                | Report "No dependencies found"          |
