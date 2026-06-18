---
description: >
  This skill should be used when the user asks to "analyze repository", "check architecture",
  "evaluate code quality", "compare with my stack", or "what's the cost of migration".
  
  Use this skill even when the user doesn't explicitly say "analyzer" --
  mentions of Clean Architecture, maintainability, or upgrade value should also trigger this.

examples:
  - "Przeanalizuj to repozytorium"
  - "Oceń architekturę projektu"
  - "Porównaj z moim stackiem"
  - "Jaki jest koszt migracji?"
  - "Clean Architecture check"

negatives:
  - Do NOT use this for local inventory (use inventory)
  - Do NOT use this for finding new tools (use scout)
---

# Skill: Analyzer

## Purpose
Głęboka analiza techniczna repozytoriów — ocenia Clean Architecture compliance, wylicza Maintainability Index, szacuje Upgrade Value.

## Methodology Sources
- **Robert C. Martin**: Clean Architecture 4-layer model
- **SEI/CMU**: Maintainability Index formula
- **Martin Fowler**: Architecture Decision Records

## Workflow

### Step 1: Prepare Repository
Jeśli URL → sklonuj do temp katalogu:
```bash
git clone --depth 1 {repo_url} /tmp/ias-analysis
```
Jeśli lokalna ścieżka → użyj bezpośrednio.

### Step 2: Build Dependency Graph
Dla każdego obsługiwanego języka parsuj import statements.

### Step 3: Detect Layers
Heurystyka katalogowa:

| Pattern | Layer |
|---------|-------|
| `domain/`, `entities/`, `models/`, `core/` | Entities |
| `usecases/`, `services/`, `interactors/` | Use Cases |
| `adapters/`, `controllers/`, `gateways/` | Adapters |
| `infrastructure/`, `infra/`, `drivers/` | Drivers |

### Step 4: Validate Dependency Direction
Rule: Inner layers CANNOT import outer layers.

### Step 5: Calculate Maintainability Index
SEI formula: `MI = 171 - 5.2*ln(V) - 0.23*G - 16.2*ln(LOC)`

### Step 6: Calculate Upgrade Value
Porównaj obecny stack z target repo.

### Step 7: Generate Analysis Report
Zapisz do state.

## Output Contract

```json
{
  "cleanArchitecture": { "score": 0-100, "layers": {...}, "violations": [...] },
  "maintainability": { "index": 0-100, "rating": "low|moderate|high" },
  "upgradeValue": { "score": 0-1, "effort": "low|medium|high" }
}
```

## Quality Criteria
- Violations detected ≥75% accuracy
- Maintainability Index ±10% of actual
- Upgrade Value human approval ≥70%

## Error Handling
| Error | Action |
|-------|--------|
| Cannot clone repo | Report error, ask for local path |
| Unknown language | Skip architecture check |
| No layers detected | Report "No Clean Architecture patterns found" |
