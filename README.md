# IAS — Kwatermistrz

> **I**nventory → **A**nalyzer → **S**cout  
> Centralny system logistyczny środowiska developerskiego.

Plugin do OpenCode, który wie jakie narzędzia masz, gdzie są, i czego brakuje.

## Komendy

| Komenda                 | Opis                                         |
| ----------------------- | -------------------------------------------- |
| `/ias-scan <path>`      | Pełny pipeline: Inventory → Analyzer → Scout |
| `/ias-inventory <path>` | Skan projektu: SBOM, Technology Radar, luki  |
| `/ias-analyze <path>`   | Analiza architektury: Clean Architecture, MI |
| `/ias-scout --gaps`     | Szukaj narzędzi na GitHub                    |
| `/ias-audit`            | Audyt propozycji narzędzi                    |
| `/ias-heatmap`          | Mapa ciepła ekosystemu narzędzi              |
| `/tool-use <path>`      | Rejestruj nowe narzędzie                     |

## Pierwsze uruchomienie

Po sklonowaniu repozytorium uruchom skrypt bootstrap:

```bash
python scripts/init_project.py
```

Utworzy lokalne katalogi i pliki konfiguracyjne (wymagane, ale wykluczone z Gita).

Następnie edytuj `backend/.envy` — ustaw swoje ścieżki maszynowe.

## Wymagania

- Python 3.10+
- OpenCode
- Opcjonalnie: `gh` CLI, `cdxgen`, `grype`

## Struktura

```
IAS/
├── plugin.json          # Manifest
├── SKILL.md             # Główny skill OpenCode
├── commands/            # Komendy
├── skills/              # Umiejętności agenta
├── agents/              # Agent orchestrator
├── scripts/             # Kod Python
├── references/          # Dokumentacja architektury
├── hooks/               # Event hooks
├── backend/
│   ├── .planCS          # Mapa rusztowania
│   ├── .envy            # Konfiguracja lokalna (gitignored)
│   └── settings.yaml    # Ustawienia pipeline'u
├── data/                # Dane (gitignored — init skrypt)
└── state/               # Stan pipeline'u (gitignored — init skrypt)
```

## Licencja

MIT
