---
name: ias
description: >
  IAS — Kwatermistrz środowiska developerskiego. Inventory, Analyzer, Scout.
  Centralny rejestr narzędzi, audyt propozycji, mapa rusztowania.
  Odpowiada na pytania: co mamy, gdzie to jest, jak użyć, czego brakuje.

trigger_words:
  - IAS
  - kwatermistrz
  - tech stack
  - inventory
  - SBOM
  - analyze repo
  - scout alternatives
  - tool registration
  - tool registry
  - rejestr narzędzi
  - audyt propozycji
  - mapa narzędzi
  - co mam zainstalowane
  - czego mi brakuje
  - znajdź narzędzie
  - oceń repozytorium
  - skanuj projekt
  - propozycja narzędzia
  - zarejestruj narzędzie

examples:
  - "Zeskanuj mój projekt i powiedz czego mi brakuje"
  - "Zarejestruj nowe narzędzie pod ścieżką R:\\Dev\\Tools\\Remotion"
  - "Przeanalizuj repozytorium fastapi/fastapi"
  - "Znajdź alternatywę dla pytest"
  - "Oceń propozycję narzędzia https://github.com/user/repo"
  - "Pokaż rejestr narzędzi w domenie video"
  - "Gdzie powinienem zainstalować to narzędzie?"

negatives:
  - Do NOT use this for writing code (use coding skills)
  - Do NOT use this for git operations (use git skill)
  - Do NOT use this for deployment (use devops skill)

version: 2.0.0
author: 13ty
created: 2026-06-06
updated: 2026-06-07
---

# IAS — Kwatermistrz (Smart Tech-Stack Oracle)

> **I**nventory → **A**nalyzer → **S**cout  
> Centralny system logistyczny środowiska developerskiego.

## Rola

IAS to **Kwatermistrz** — wie dokładnie co, gdzie i jak jest skonfigurowane oraz dostarcza tę wiedzę agentom na żądanie.

**Kluczowe pytania:**

- Gdzie jest narzędzie X? → ścieżka, typ, uruchomienie
- Jak zaktualizować Y? → komenda, źródło, dokumentacja
- Gdzie instalować nowe narzędzie? → reguła z `.planCS`
- Czy to repo jest dla nas wartościowe? → audyt + ocena w Vault
- Co nam brakuje? → gap analysis z Inventory

## Komendy

| Komenda          | Opis                                                       |
| ---------------- | ---------------------------------------------------------- |
| `/ias-scan`      | Pełny pipeline: Inventory → Analyzer → Scout               |
| `/ias-inventory` | Skanuj projekt: SBOM, Vulnerability scan, Technology Radar |
| `/ias-analyze`   | Analizuj repozytorium: Clean Architecture, Maintainability |
| `/ias-scout`     | Szukaj repozytoriów na GitHub pasujących do braków         |
| `/ias-audit`     | Audytuj propozycje narzędzi (z proposals.csv)              |
| `/ias-heatmap`   | Generuj mapę ciepła ekosystemu narzędzi                    |
| `/tool-use`      | Rejestruj nowe narzędzie przy pierwszym użyciu             |

## Umiejętności (Skill)

Plugin dostarcza 10 umiejętności:

| Skill                    | Opis                                                           |
| ------------------------ | -------------------------------------------------------------- |
| **inventory**            | Mapowanie lokalnego ekosystemu (SBOM, Technology Radar, Gaps)  |
| **analyzer**             | Ocena repozytoriów (Clean Architecture, Upgrade Value)         |
| **scout**                | Odkrywanie repozytoriów na GitHub i ocena bezpieczeństwa       |
| **auditor**              | Audyt propozycji narzędzi względem gapów i istniejącego stacka |
| **heatmap**              | Wizualizacja ekosystemu narzędzi (pokrycie, nakładanie, porty) |
| **iamsparta-graph**      | Knowledge Graph — relacje między narzędziami, capability map   |
| **iamsparta-core**       | Orchestrator IAmSparta — routing L1/L2/L3, synteza decyzji     |
| **iamsparta-comparison** | Silnik porównawczy — feature matrix, gap analysis              |
| **iamsparta-strategist** | Agent Strateg — ocena strategiczna TAKE/WAIT/BUILD/SKIP        |
| **iamsparta-feedback**   | Pętla feedbacku — uczenie się z decyzji, kalibracja confidence |

## Integracje

- **Tool Registry** — rejestr narzędzi (`data/tool_registry.json`)
- **Obsidian Vault** — przechowywanie ocen narzędzi (template v3)
- **Backend (.planCS)** — mapa rusztowania (gdzie co ląduje)
- **Backend (.envy)** — konfiguracja środowiska i portów
- **ChromaDB** — semantic search dla narzędzi (opcjonalnie)

## Struktura

```
IAS/
├── plugin.json              # Manifest pluginu
├── SKILL.md                 # Ten plik
├── package.json             # npm package
├── VISION.md                # Wizja i architektura
├── PLAN.md                  # Plan implementacji
├── README.md                # Dokumentacja
├── commands/                # Komendy (7)
├── skills/                  # Umiejętności (5)
├── agents/                  # Agent (orchestrator)
├── scripts/                 # Skrypty Python (6)
├── data/                    # Dane (tool_registry.json, proposals.csv)
├── references/              # Dokumentacja metodologii
├── state/                   # Stan pipeline'u
├── backend/                 # Backend (.planCS, .envy)
└── hooks/                   # Hooks
```
