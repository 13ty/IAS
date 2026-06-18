---
name: ias-scout
description: "Uruchamia skill Scout — szuka repozytoriów na GitHub pasujących do wykrytych braków technologicznych."
trigger: /ias-scout
bash: python scripts/scout_search.py {{--gaps}} {{--max-results}}
argument-hint: "--gaps category1,category2 --max-results 10"
allowed-tools:
  - bash
  - read
  - write
  - grep
  - glob
---

# Command: /ias-scout

## Description

Uruchamia tylko skill Scout — szuka repozytoriów na GitHub pasujących do wykrytych braków.

## Usage

```
/ias-scout [--gaps "category1,category2"] [--max-results 10]
```

## Arguments

| Argument      | Required | Description                                      |
| ------------- | -------- | ------------------------------------------------ |
| --gaps        | Nie      | Kategorie do wyszukania. Domyślnie: z state file |
| --max-results | Nie      | Maksymalna liczba wyników. Domyślnie: 10         |

## Workflow

1. Wyodrębnij luki (z flagi --gaps lub z state)
2. Mapuj luki na słowa kluczowe
3. Przeszukaj GitHub (gh CLI)
4. Filtruj i deduplikuj
5. Oceń bezpieczeństwo (scorecard/estymacja)
6. Oblicz relevance
7. Priorytetyzuj wyniki

## Output

```
🔎 Scout Report

Gaps Addressed: Testing, Security, Documentation

Top 10 Repositories:

1. pytest-dev/pytest (⭐ 12,000)
   Score: 0.91 | Coverage: Testing | Effort: LOW
   "The pytest framework makes it easy to write small tests"

2. pyupio/safety (⭐ 2,500)
   Score: 0.87 | Coverage: Security | Effort: LOW
   "Safety checks Python dependencies for known security vulnerabilities"

3. mkdocs/mkdocs (⭐ 19,000)
   Score: 0.85 | Coverage: Documentation | Effort: MEDIUM
   "Project documentation with Markdown"

... (7 more)

📊 Summary
├── Total scanned: 250 repos
├── Matched: 10 repos
├── Gaps addressed: 3/4
└── Gaps remaining: CI/CD (no good match found)
```
