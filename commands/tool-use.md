---
name: tool-use
description: "Rejestruje nowe narzędzie przy pierwszym użyciu — auto-detekcja metadanych, opcjonalnie analiza jakości i szukanie alternatyw."
trigger: /tool-use
bash: python scripts/tool_register.py {{path}} --quick
argument-hint: path [--quick] [--analyze] [--compare] [--list]
allowed-tools:
  - bash
  - read
  - write
  - grep
  - glob
  - lsp_diagnostics
examples:
  - "/tool-use R:\\Dev\\Tools\\Remotion"
  - "/tool-use --list"
  - "/tool-use --list --domain video"
  - "/tool-use --list --priority hot"
  - "/tool-use R:\\Dev\\Tools\\processor --quick" # Rejestracja z wpisem do data/research/tools.csv
---

# Command: /tool-use

## Description

Użyj narzędzia po raz pierwszy — automatycznie rejestruje je w systemie. Opcjonalnie analizuje jakość i szuka alternatyw.

## Usage

```
/tool-use <path>                # Interaktywna rejestracja
/tool-use <path> --quick        # Szybka rejestracja (bez pytań)
/tool-use <path> --analyze      # Rejestracja + analiza jakości
/tool-use <path> --compare      # Rejestracja + szukanie alternatyw
/tool-use <path> --analyze --compare  # Pełny pakiet
/tool-use --list                # Lista zarejestrowanych
/tool-use --list --domain video # Filtruj po domenie
/tool-use --list --priority hot # Filtruj po priorytecie
```

## Arguments

| Argument   | Required               | Description                                  |
| ---------- | ---------------------- | -------------------------------------------- |
| path       | Tak (jeśli nie --list) | Ścieżka do narzędzia                         |
| --quick    | Nie                    | Rejestruj bez interaktywnych pytań           |
| --analyze  | Nie                    | Uruchom analizę jakości                      |
| --compare  | Nie                    | Szukaj alternatyw (Scout)                    |
| --list     | Nie                    | Pokaż zarejestrowane narzędzia               |
| --domain   | Nie                    | Filtr: video, databases, ai_ml, devops, etc. |
| --priority | Nie                    | Filtr: hot, warm, cold                       |
| --status   | Nie                    | Filtr: adopt, trial, assess, hold            |
| --json     | Nie                    | Wynik jako JSON                              |

## Workflow

### First Use (nowe narzędzie)

1. Auto-detect (package.json, pyproject.toml, etc.)
2. Jeśli --analyze: Clean Architecture check
3. Jeśli --compare: Scout szuka alternatyw
4. Interaktywne pytania: domain? priority? status?
5. Register w tool_inventory.json
6. Upsert do ChromaDB
7. Generuj quick_start/\*.md
8. Uruchom / Pokaż jak użyć

### Already Registered

1. Update use_count
2. Pokaż istniejący wpis
3. Jeśli --analyze: pokaż istniejącą analizę

## Output Example

```
🔍 Wykryto: Remotion 4.0.15 (node)
   Opis: Video creation in React
   Uruchomienie: npx remotion studio

📋 Pytania:
   Domena [video/databases/ai_ml/...] (default: video): video
   Priorytet [hot/warm/cold] (default: hot): hot
   Status [adopt/trial/assess/hold] (default: trial): adopt
   Opis (enter = auto): Programmatic video creation in React

✅ Zarejestrowano: Remotion
   Domena: video
   Priorytet: hot
   Status: adopt
   Uruchom: npx remotion studio
   Quick Start: quick_start/remotion.md
```

## Integration

- **ChromaDB**: Auto-upsert na rejestracji
- **Research Database**: Dodaje wpis do `data/research/tools.csv` przy rejestracji nowego narzędzia
- **IAS Analyzer**: Jeśli --analyze
- **IAS Scout**: Jeśli --compare
- **Obsidian**: Generuje quick_start/\*.md
