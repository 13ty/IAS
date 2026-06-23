# TOREFINE — IAS: Reset i Refinement

> **Problem**: IAS ma ~17 skryptów, 3 schematy myślowe (Repo Evaluation, IASparta KG, Tool Registry), i żaden z nich nie jest właściwym rdzeniem. Repo Evaluation v2 zaczęło żyć własnym życiem i przysłoniło prawdziwą wartość.

---

## 1. Core Identity (co NIE może się zmienić)

**IAS = semantyczna wyszukiwarka + rejestr całego środowiska deweloperskiego.**

Nie dla projektów. Dla **maszyny dewelopera**. Pyta się po ludzku, dostaje narzędzie + ścieżkę + komendę. W 500ms.

| Pytanie         | Powinien odpowiedzieć                                                            |
| --------------- | -------------------------------------------------------------------------------- |
| "mp3 flaw"      | `ffmpeg.exe` → `R:\Dev\Tools\ffmpeg\bin\ffmpeg.exe` + `ffmpeg -i in.mp3 out.wav` |
| "diagram code"  | `mermaid-cli`, `plantuml.jar`, `structurizr` — ścieżki, komendy, porty           |
| "test api rest" | `httpie`, `restish`, `curl`, `bruno` — gdzie są, jak odpalić, config             |

To **`locate` + `which` + `apropos` × embeddingi × graf wiedzy**. Nic więcej, nic mniej.

---

Musi być jasne aby oddzielić to co MAMY od tego co WIEMY , CO PROPONUJEMY, od tego co NAM BRAKUJE. KWATERMISTRZ wie co MAMY , HEATMAPA opiera sie na tym co mamy a czego NAM BRAKUJE , oceny odbywaja sie na podstawie tego co PROPONUJEMY aby zamienić to w to co WIEMY. Na podstawie tego co WIEMY i czego NAM BRAKUJE sprawić ze stanie sie coś tym co MAMY. 

---

## 2. Co mamy — separacja core vs noise

### 🟢 CORE — to jest wartościowe, to chronić

| Element                                    | Co robi                                                          | Wartość                                                            |
| ------------------------------------------ | ---------------------------------------------------------------- | ------------------------------------------------------------------ |
| `scripts/iamsparta/kg/graph.py`            | In-memory knowledge graph: Tool → Capability → Domain            | Fundament. Węzły, krawędzie, indeksy, serializacja — wszystko jest |
| `scripts/iamsparta/kg/schema.py`           | Typy: `ToolNode`, `CapabilityNode`, `DomainNode`, `Relationship` | Silne typowanie, brak surowych dictów                              |
| `scripts/iamsparta/kg/builder.py`          | Buduje graf z `tool_registry.json` + auto-relacje                | Gotowy pipeline                                                    |
| `scripts/iamsparta/semantic/search.py`     | Semantic search: `search("diagram")` → LanceDB → wyniki          | Najbliżej prawdziwego IAS                                          |
| `scripts/iamsparta/semantic/embeddings.py` | Generuje embeddingi przez LMStudio → LanceDB                     | Kręgosłup semantic search                                          |
| `scripts/tool_register.py`                 | Auto-detekcja toola: typ, wersja, opis, domena, run_command      | Port wejściowy dla ~2000 tooli                                     |
| `scripts/lancedb_upsert.py`                | Upsert embeddingów narzędzi do LanceDB                           | Persystencja                                                       |
| `scripts/mcp_server.py`                    | Wystawia narzędzia IAS jako MCP (audit, inventory, search)       | Interfejs dla agenta                                               |

### 🟡 NOISE / ROZPRASZACZE — użyteczne ale nie core

| Element                  | Problem                                                                      | Decyzja                                         |
| ------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------- |
| `repo_batch_init.py`     | Init pending repo z kolejki — dotyczy **repo evaluation**, nie tool registry | Zostawić jako feature, nie mieszać do core flow |
| `capability_mapper.py`   | Mapuje repo_card → capability_map przez substring — **repo evaluation**      | Jw. Użyteczne w swoim kontekście                |
| `timeline_manager.py`    | Zarządzanie timeline dla repo — **repo evaluation**                          | Jw.                                             |
| `proposal_audit.py` v2   | Audyt propozycji → repo_card                                                 | Część pipeline'u, ale nie pierwszego kontaktu   |
| `proposal_collect.py` v2 | Kolejka URL-i                                                                | Jw.                                             |
| `scout_search.py` v2     | Szukanie repo na GitHub                                                      | Jw.                                             |
| `analyzer_check.py`      | Clean Architecture violations                                                | Osobna domena (analiza projektów)               |
| `inventory_scan.py`      | SBOM projektu                                                                | Osobna domena                                   |
| `heatmap.py`             | Mapa ciepła tool_registry                                                    | Hybryda — dotyczy tooli, ale nie jest search    |

### 🔴 MARTWE / DO USUNIĘCIA

| Element                      | Problem                                                                                                                |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `orchestrator.py`            | Splątany ze starym `data/`, nie używa `state/`, nie używa KG. Trudno refaktorować — łatwiej przepisać                  |
| `vault_writer.py`            | Ad-hoc template, nieczytelny output                                                                                    |
| `scripts/iamsparta/council/` | Council orchestrator (wieloagentowy audyt) — koncepcyjnie ciekawy, ale obecnie nieużywany i oderwany od rzeczywistości |

---

## 3. Co trzeba zrobić — priorytety

### P0: Prosty query interface

**Cel**: `/ias-query "mp3 convert"` → ffmpeg.exe + ścieżka + komenda. Działa offline, <500ms.

**Brak**: Nie ma komendy `/ias-query`. Jest `search.py --search` ale nie ma interfejsu dla użytkownika/agenta.

**Co zrobić**:

- Komenda `/ias-query <query>` w `plugin.json` / `commands/`
- Nowy skrypt `ias_query.py` który: query → embedding → LanceDB → top-K → format (tool, path, run_command)
- Opcjonalnie fallback: grep + fuzzy przez tool_registry.json gdy embedding nie dostępny

### P1: Bulk scan środowiska

**Cel**: Zarejestrować tools które już są na maszynie.

**Brak**: Rejestr jest pusty. `tool_register.py` działa per-ścieżka — nikt nie przebiegnie 2000 razy.

**Co zrobić**:

- Skrypt `scan_environment.py` który przeszukuje:
  - `R:\Dev\Tools\` — wszystkie podfoldery z package.json/pyproject.toml/.git
  - `%PATH%` — binary dostępne z konsoli
  - `C:\Program Files\` — zainstalowane aplikacje
  - Zarejestrowane pluginy OpenCode
- Auto-detekcja + dedup → tool_registry.json + LanceDB embedding

### P2: Akcja po znalezieniu

**Cel**: Znalazłeś tool → możesz coś z nim zrobić, nie tylko przeczytać. Powinnismy mieć dla kazdego tool gotowy zestaw instrukcji (najlepie w formie jednego pliku .exe albo skryptu) do tego aby : 

- Wyświetlić lokalizację narzędzia i opis jeżeli wymagane.
- Zaktualizować repozytorium
- Zaktualizowac zaleznosci
- Stworzyć backup konfiguracji
- Zainstalowac repozytorium/zalezności
- Uruchomic narzędzie 
- Wyswietlić instrukcję

Taka gotowa lista powinna być dostępna dla każdego narzędzia z poziomu kwatermitrza lub komendy IAS . 

**Brak**: Search zwraca nazwę i tyle.

**Co zrobić**:

- `copy-path` — skopiuj ścieżkę
- `open-dir` — otwórz folder w explorerze
- `run-help` — uruchom `tool --help`
- `edit-config` — otwórz config toola
- `show-aliases` — pokaż aliasy i skróty

coś jeszcze ? 

### P3: Połączenie KG z registry

**Cel**: Knowledge graph IASparta (`iamsparta/kg/`) i tool registry (`tool_registry.json`) to jedno.

**Brak**: KG buduje się z `tool_registry.json` przez `builder.py`, ale to jednokierunkowe. Zmiana w registry → przebudowa KG. Żadnego sprzężenia zwrotnego.

**Co zrobić**:

- KG powinien być _żywym widokiem_ na registry, nie osobną kopią
- Albo: KG jako primary store, registry jako serializacja
- Albo: builder jako serwis a nie skrypt jednorazowy

### P4: Repo Evaluation jako moduł, nie misja

**Cel**: Repo Evaluation (queue → audit → batch_init → capability_map) działa, ale jako **feature**, nie centrum.

**Brak**: Zajęło 3 sesje i przysłoniło core.

**Co zrobić**:

- Zostawić jako pipeline w `scripts/` pod osobny namespace
- Nie łączyć z core search — to narzędzie do podejmowania decyzji "czy zainstalować nowy tool", nie do znajdowania co już jest
- Komenda `/ias-repo-search` → oddzielna

---

## 4. Czego NIE robić

- ❌ ArcticDB – dopóki nie ma >100 rekordów. JSON wystarcza. Potem jednak dobrze wprowadzić baze Arctic.
- ❌ Council orchestracji – dopóki podstawowy search nie działa
- ❌ Automatycznej re-evaluation – narzędzia nie zmieniają się codziennie
- ❌ Web UI – CLI + MCP + slash command w OpenCode to wystarczający interfejs

---

## 5. Mapa decyzyjna

```
Jesteś tu?
│
├─ "gdzie jest X?" → to robi /ias-query (P0) ← JESTEŚMY TU
│
├─ "czego mi brakuje?" → to robi Scout + Repo Evaluation (feature)
│
├─ "co jest na mojej maszynie?" → to robi scan_environment (P1)
│
├─ "pokaż narzędzia do Y" → to robi semantic search + domain filter (P0+P2)
│
└─ "co jest lepsze, X czy Y?" → to robi porównanie capability (P4 feature)
```

---

_Utworzono: 2026-06-23. Punkt refocusu po dryfie w Repo Evaluation v2._
