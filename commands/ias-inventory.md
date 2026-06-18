---
name: ias-inventory
description: "Uruchamia skill Inventory — generuje SBOM, klasyfikuje na Technology Radar, wykrywa luki w projekcie."
trigger: /ias-inventory
bash: python scripts/inventory_scan.py {{path}}
argument-hint: path
allowed-tools:
  - bash
  - read
  - write
  - grep
  - glob
---

# Command: /ias-inventory

## Description

Uruchamia tylko skill Inventory — generuje SBOM, klasyfikuje na Radar, wykrywa luki.

## Usage

```
/ias-inventory [path]
```

## Arguments

| Argument | Required | Description                                                     |
| -------- | -------- | --------------------------------------------------------------- |
| path     | No       | Ścieżka do projektu. Jeśli pominięte, używa bieżącego katalogu. |

## Workflow

1. Wykryj typ projektu
2. Generuj SBOM (cdxgen)
3. Skanuj luki (grype)
4. Klasyfikuj na Radar
5. Wykryj luki
6. Zapisz do state

## Output

```
📊 Inventory Report

Project: MyProject
Path: R:\Dev\MyProject

📦 Dependencies (45 components)
├── Python 3.11 ✅
├── FastAPI 0.104.0 ✅
├── SQLAlchemy 1.4.0 ⚠️
└── ... (42 more)

🔴 Vulnerabilities (2 found)
├── CVE-2024-1234 (HIGH) - package@1.0.0
└── CVE-2024-5678 (MEDIUM) - other@2.0.0

📡 Technology Radar
├── Adopt: Python 3.11, FastAPI, PostgreSQL
├── Trial: Ruff, uv
├── Assess: SQLAlchemy 2.0
└── Hold: Python 3.8

🔍 Gaps Detected (3)
├── [HIGH] No test framework
├── [MEDIUM] Missing SECURITY.md
└── [LOW] No linting config
```
