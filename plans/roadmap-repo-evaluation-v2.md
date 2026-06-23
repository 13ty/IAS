# Roadmap: Repo Evaluation v2 — Od rankingu do mapy narzędziowej

> **Cel**: Przeprojektowanie systemu oceny repozytoriów w IAS. Nie pytamy "czy to dobry projekt?" tylko "czy to wartościowe dla nas w sposób który ma znaczenie?"
>
> **Filozofia**: Repo != kategoria. Każde narzędzie może mieć wiele capability, a capability to pierwszo klasowy byt.
>
> **Stan**: Koncept uzgodniony, gotowy do implementacji.

---

## Faza 0: Fundament danych (3 schematy + 1 taksonomia)

Podstawa wszystkiego — definicje strukturalne które są SSOT dla całego pipeline'u.

| Element                              | Opis                                                                                   | Status         |
| ------------------------------------ | -------------------------------------------------------------------------------------- | -------------- |
| `state/scoring_criteria.schema.json` | Definicja kryteriów oceny — wagi, wymiary, progi decyzyjne                             | Koncept gotowy |
| `state/capability_taxonomy.json`     | Słownik capability — kontrolowane kategorie (50-100) do wypełniania przy deep research | Koncept gotowy |
| `state/repo_queue.schema.json`       | Kolejka URL-i do oceny — lekka, walidowana, z dedup                                    | Koncept gotowy |
| `state/repo_card.schema.json`        | Główna karta repo — zawsze wypełniana dla każdego wpisu                                | Koncept gotowy |
| `state/capability_map.schema.json`   | Mapa capability — opcjonalna, tylko dla deep research                                  | Koncept gotowy |

**Kryterium sukcesu**: Każdy plik `.schema.json` przechodzi walidację JSON Schema. Schematy są spójne między sobą (odwołują się po `$ref` tam gdzie to ma sens).

---

## Faza 1: Pipeline zbierania (queue → knowledge)

Transformacja obecnego `proposals.csv` w zarządzaną kolejkę, i obecnych plików `.md` w ustrukturyzowane karty.

| Zadanie                                | Opis                                                                                   | Priorytet |
| -------------------------------------- | -------------------------------------------------------------------------------------- | --------- |
| `state/repo_queue.json` + walidacja    | Zastępuje `proposals.csv`. JSON z statusami (pending → enriched → evaluated → decided) | P1        |
| `state/repo_knowledge.json`            | Indeks wszystkich ocenionych repo — szybkie query, nie pełne dane                      | P1        |
| `state/repos/{repo_id}/repo_card.json` | Karta oceny — generowana dla każdego repo                                              | P1        |
| `state/repos/{repo_id}/timeline.json`  | Historia ocen — data, verdict, capability_map_version                                  | P1        |
| Deduplikacja URL                       | Zanim URL trafi do queue, sprawdza knowledge + queue                                   | P1        |
| Walidacja URL                          | Sprawdzanie czy URL jest poprawnym GitHub (lub innym) repo                             | P1        |
| `proposal_collect.py` → v2             | Zapis do `repo_queue.json` zamiast `proposals.csv`                                     | P1        |
| `proposal_audit.py` → v2               | Zapis do `repos/{repo_id}/` zamiast `data/audits/*.md`                                 | P2        |
| `scout_search.py` → v2                 | Wyniki scouta lądują w queue (do potwierdzenia), nie tylko stdout                      | P2        |

**Kryterium sukcesu**: Nowe repo trafia do queue → automatycznie enriched → ręcznie/kont ekstem evaluated → ląduje w knowledge z repo_card.

---

## Faza 2: Głęboka ocena (capability map + investigation log)

Dla repo które mają potencjał (serendipity >= medium lub manualne oznaczenie) — dogłębny research z użyciem codebase-memory.

| Zadanie                                      | Opis                                                                               | Priorytet |
| -------------------------------------------- | ---------------------------------------------------------------------------------- | --------- |
| `state/repos/{repo_id}/capability_map.json`  | Mapa capability — lista capability z jakością i opisem "jak to odkryliśmy"         | P2        |
| `state/repos/{repo_id}/investigation_log.md` | Co odkryliśmy, co było zaskoczeniem, co warte zapamiętania                         | P2        |
| codebase-memory integration                  | Użycie codebase-memory do analizy kodu repo przy deep research                     | P2        |
| Serendipity detection                        | Mechanizm oznaczania repo jako "potencjalnie wartościowe poza oczywistą kategorią" | P2        |
| Capability dedup / merge                     | Gdy dwa repo mają tę samą capability — możliwość porównania jakości                | P3        |

**Kryterium sukcesu**: Dla dowolnego repo capability_map pozwala odpowiedzieć "co to robi czego nie robi nic innego" i "jakie capability pokrywa".

---

## Faza 3: Przebudowa skryptów + integracja

Dopasowanie istniejących skryptów do nowych schematów. To dużo zmian w kodzie — każdy skrypt wymaga przepisania logiki I/O.

| Skrypt                | Zmiana                                                              | Priorytet |
| --------------------- | ------------------------------------------------------------------- | --------- |
| `proposal_collect.py` | Zamiast CSV → `repo_queue.json`. Nowa komenda w plugin.json         | P1        |
| `proposal_audit.py`   | Zamiast `data/audits/*.md` → `state/repos/{repo_id}/repo_card.json` | P2        |
| `scout_search.py`     | Wyniki do `repo_queue.json` z source="scout"                        | P2        |
| `orchestrator.py`     | Nowe checkpointy zgodne z schematami                                | P2        |
| `vault_writer.py`     | Template na bazie repo_card zamiast ad-hoc analizy                  | P3        |

**Kryterium sukcesu**: `ias-scan` / `ias-audit` / `ias-scout` działają z nowym modelem danych.

---

## Faza 4: Query i użycie

Narzędzia do korzystania z zebranej wiedzy — capability search, porównania, mapa narzędziowa.

| Zadanie               | Opis                                                         | Priorytet |
| --------------------- | ------------------------------------------------------------ | --------- |
| `/ias-repo-search`    | Szukaj w knowledge po capability, języku, verdict            | P3        |
| Capability comparison | Dla capability X pokaż wszystkie repo które ją mają + jakość | P3        |
| Tag system            | @repo, @python, @testing — tagi dla łatwego filtrowania      | P3        |
| Knowledge graph sync  | Repozytoria z knowledge jako węzły w codebase-memory         | P4        |

**Kryterium sukcesu**: Można zapytać "pokaż wszystkie repo z capability `property-based-testing`" i dostać listę z porównaniem.

---

## Struktura docelowa `state/`

```
state/
├── capability_taxonomy.json        # Faza 0 — słownik capability
├── scoring_criteria.json           # Faza 0 — jak oceniamy
├── repo_queue.json                 # Faza 1 — inbox do oceny
├── repo_knowledge.json             # Faza 1 — indeks wszystkich repo
└── repos/
    └── {repo_id}/
        ├── repo_card.json          # Faza 1 — karta oceny (zawsze)
        ├── timeline.json           # Faza 1 — historia ocen
        ├── capability_map.json     # Faza 2 — opcjonalna, deep research
        └── investigation_log.md    # Faza 2 — opcjonalna, odkrycia
```

---

## Notatki

- **Fazy realizujemy sekwencyjnie** — Faza 0 musi być gotowa przed Faza 1, Faza 1 przed Faza 2 itd.
- **Każde repo = folder** — nawet "is-even". Małe repo też mają wartość jako kontekst.
- **Brak auto re-evaluation** — repo czeka w bazie aż podejmiemy decyzję o zmianie kategorii w stacku.
- **Capability map = opcjonalna** — próg: `serendipity_potential >= medium` lub manualne oznaczenie.
- **Software zmienia się co 6 miesięcy o rząd wielkości** — capability map nie jest raz-na-zawsze. timeline.json notuje datę oceny.

---

## @@TODO: Wzbogacanie danych — GitHub PAT / clone / Actions

**Problem**: `repo_batch_init.py` tworzy karty z domyślnymi wartościami (stars=0, language=Unknown, topics=[]). `proposal_audit.py --non-interactive` daje all-5. capability_mapper nie ma czym mapować. Pipeline działa mechanicznie, ale jakość jest marna.

**Potrzeba**: Skrypt `enrich_repo_data.py` który bierze zainicjalizowane repo z queue i wzbogaca `repo_card.json` o realne dane.

**Rozważane podejścia** (do wyboru):

| Podejście                          | Zalety                                                             | Wady                                                    |
| ---------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------- |
| **A: GitHub PAT + PyGithub**       | Lekkie, tylko API call, szybko                                     | Limit API (5000/h), PAT wymaga configu, tylko GitHub    |
| **B: Git clone do temp + analiza** | Najpełniejsze dane — readme, structure, config files, license file | Ciężkie, długie, wymaga cleanup, ale user uważa że best |
| **C: GitHub Actions**              | Bez lokalnego zużycia, automatyka                                  | Narzut infra, niepotrzebne dla <100 repo                |

**Rekomendacja wstępna**: Podejście B (clone do temp) daje najwięcej — można wyciągnąć README, strukturę plików, wykryć język z actual files, zobaczyć configi. Potem `shutil.rmtree`.

**Co powinien robić `enrich_repo_data.py`**:

- [ ] Przyjmuje repo_id (lub URL)
- [ ] Klonuje do temp na dysk (`tempfile.TemporaryDirectory`)
- [ ] Wyciąga: README → description, strukturę katalogów → języki, package.json/pyproject.toml → zależności, licencję
- [ ] Aktualizuje `repo_card.json`: enriched.stars, enriched.language, enriched.topics, enriched.license, enriched.description
- [ ] Usuwa temp
- [ ] Opcjonalnie: może też fetchować GitHub API (PyGithub) dla statystyk (stars, forks, issues)
- [ ] Aktualizuje timeline

**Zależność**: Może być uruchamiany przed `proposal_audit` (bo audit potrzebuje realnych danych do scoringu) lub jako osobny krok między batch_init a auditem.

**Status**: 🔲 Do zrobienia. Decyzja o podejściu otwarta.

## Decyzje architektoniczne

### ADR-001: ArcticDB jako warstwa query (2026-06-22)

**Status**: Rozważone, odłożone (ang. "someday, maybe — ale uwzględnione w każdym kolejnym etapie").

**Kont tekst**: System oceny repo zapisuje dane w płaskich JSON-ach (`state/`). Przy skali < 100 rekordów to w pełni wystarcza. Pojawiło się pytanie o bazę danych i backup.

**Odrzucone**: SQLite — narzut ORM, schematy, migracje. Nie chcemy tego.

**Rozważone**: [ArcticDB](https://arcticdb.io/) — kolumnowa baza danych od Man Group (używana w produkcji przez hedge fundy).

- JSON-native ingest — wrzucamy `repo_card.json` wprost, bez transformacji
- Versioning wbudowany — każda zmiana to snapshot, `list_versions()` = backup
- Query przez DataFrame — filter po capability, group by verdict
- Zero schematów, zero migracji

**Konsekwencja**: ArcticDB jest zarejestrowane w `data/tool_registry.json` (priority: cold, status: assess). Każda przyszła zmiana w modelu danych (`state/`) powinna uwzględniać, że docelowo dane mogą być syncowane do ArcticDB. Nie blokuje to żadnej z faz — doklejamy jako osobny skrypt `repo_to_arctic.py` kiedy (i jeśli) faktycznie zajdzie potrzeba.
