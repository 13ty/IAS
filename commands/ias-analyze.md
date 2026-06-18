---
name: ias-analyze
description: "Uruchamia skill Analyzer — ocenia repozytorium pod kątem Clean Architecture, utrzymywalności i wartości upgrade'u."
trigger: /ias-analyze
bash: python scripts/analyzer_check.py {{repo_url_or_path}} {{--compare-with}}
argument-hint: repo_url_or_path
allowed-tools:
  - bash
  - read
  - write
  - grep
  - glob
---

# Command: /ias-analyze

## Description

Uruchamia tylko skill Analyzer — ocenia repozytorium pod kątem Clean Architecture, utrzymywalności i wartości upgrade'u.

## Usage

```
/ias-analyze <repo_url_or_path> [--compare-with local_path]
```

## Arguments

| Argument         | Required | Description                                   |
| ---------------- | -------- | --------------------------------------------- |
| repo_url_or_path | Tak      | URL repozytorium GitHub lub lokalna ścieżka   |
| --compare-with   | Nie      | Lokalna ścieżka do porównania (upgrade value) |

## Workflow

1. Przygotuj repozytorium (clone lub direct)
2. Buduj graf zależności
3. Wykryj warstwy Clean Architecture
4. Waliduj kierunek zależności
5. Wylicz Maintainability Index
6. Oszacuj Upgrade Value (jeśli --compare-with)
7. Zapisz do state

## Output

```
🔍 Analysis Report

Repository: fastapi/fastapi
URL: https://github.com/fastapi/fastapi

🏛️ Clean Architecture: 82/100
├── Entities: ✅ Detected (fastapi/dependencies.py)
├── Use Cases: ✅ Detected (fastapi/routing.py)
├── Adapters: ✅ Detected (fastapi/middleware/)
├── Drivers: ✅ Detected (fastapi/encoders.py)
└── Violations: 1 (medium)
    └── applications.py → imports starlette (should be abstracted)

📈 Maintainability Index: 75/100
├── Lines of Code: 24,500
├── Cyclomatic Complexity: 8.2
└── Rating: Moderate

⬆️ Upgrade Value: 0.65 (compared to Django 3.2)
├── Effort: HIGH (full rewrite)
├── Benefit: async, 10x speed, modern patterns
├── Risk: Breaking changes in authentication layer
└── Recommendation: Consider for new microservices only
```
