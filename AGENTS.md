# Global Agent Instructions

## Jezyk

- You can commnicate with user in Polish or English
- Jeżeli nie jest okreslone inaczej, uzywaj jezyka angielskiego (kod, komentarze, commity).
- Commity: angielski, konwencjonalny format (feat:, fix:, chore:, docs:, refactor:).

## Zarzadzanie pakietami

- **pixi**: Nie używamy ciezkich i marnujących nasze zasoby kontenerowych aplikacji kiedy mozemy uzyc pixi.
- **Python**: UV jest jedynym akceptowalnym menadzerem. `uv pip install`, `uvx`, `uv run`. Nigdy `pip`.
- **Node.js**: Bun jest preferowany. `bun install`, `bun add`, `bunx`. Akceptowalne: `pnpm`. Zabronione: `npm install`, `yarn`.
- W ekosystemie Node.js jedynym środowiskiem uruchomieniowym i menedżerem jest Bun. Używaj bun run, bun install, bunx. Używanie komend node, npm, npx oraz yarn jest bezwzględnie zabronione

## Styl pracy

- Jeśli plik zbliża się do 300 linii, zaplanuj jego dekompozycję na mniejsze, logiczne moduły/funkcje. Maksymalna wielkość pliku to 400 linii. Zanim zaczniesz pisać kod, upewnij się, że architektura pozwala na zamknięcie się w tym limicie.
- Nie naprawiaj problemow ktore nie sa czescia twojego zadania. Zapisz jako @@Bug_name w kodzie i dodaj taki sam @@Bug_name w podsumowaniu roadmap swojego zadania.
- Przed zakomunikowaniem końca zadania, obowiązkowo uruchom komendę /lsp i sprawdź diagnostykę, aby upewnić się, że nie ma błędów typu (typecheck) ani lintera
- Dodawaj komentarze które wydzielają sekcje kodu od siebie, używaj krótkich ale łatwych do rozpoznania określeń .
- Zapisuj plany w folderze plans , dokumenacje deweloperską w doc_dev , a dokumentacje końcową w docs. 
- settings.yaml: Rejestr Rozproszonych Zmiennych.To jest serce Twojej aplikacji – Single Source of Truth (SSOT). 
  Każda stała, która jest używana przez więcej niż jeden skrypt lub decyduje o zachowaniu aplikacji, musi trafić tutaj a dopiero stąd być importowana.

## MCP - kiedy uzywac

- `kb-manager` (MCP server) - gdy uzytkownik mowi "szukaj w bazie", "znajdz w knowledge base", "find in database", "szukaj semantycznie", "query vector store". Narzedzia: `kb_search`, `kb_list`, `kb_status`
- `context7` (OMO built-in) - gdy szukasz dokumentacji bibliotek/frameworkow
- `grep_app` (OMO built-in) - gdy szukasz przykladow kodu na GitHub
- `playwright` (OMO skill) - gdy potrzebujesz automatyzacji przegladarki
- `lsp` (OMO built-in) - gdy potrzebujesz diagnostyki, definicji, referencji, rename
- `lancedb-global` (Global) - gdy potrzebujesz zaczerpnąć z naszej wiedzy .
- `codebase-memory` (Project) - na początku każdej sesji jeżeli zadanie dotyczy autorskiego projektu.
- `websearch` (OMO built-in) - ogolne wyszukiwanie w sieci

## LSP (Language Server Protocol)

- `/lsp` - pokaz status LSP i diagnostyke
- `/lsp-install` - zainstaluj language server
- Konfiguracja: `.opencode/lsp.json`
- Obslugiwane: TypeScript, Python, Rust

## Trigger Words

| Fraza                      | Akcja                                             |
| -------------------------- | ------------------------------------------------- |
| "ultrawork" / "ulw"        | Pelna orkiestracja OMO - nie przestaje az skonczy |
| "search memory"            | Uzyj rlm-search                                   |
| "remember this"            | Uzyj session-memory-manager                       |
| "gdzie jest" / "find tool" | Uzyj tool-registry                                |
| "search KB"                | Uzyj kb-management                                |
| "hyperplan"                | Adversarial planning (5 hostile critics)          |

## Bazy wiedzy

Trigger words laduja odpowiednia baze z Vaults/knowledge-bases/:

- "azure" -> Azure KB
- "react" -> React KB
- "typescript" -> TypeScript KB
- "python" -> Python KB
- "database" -> Database KB
- "testing" -> Testing KB
- "security" -> Security KB
- "devops" -> DevOps KB

### Wyszukiwanie semantyczne

- `/kb-search <zapytanie> [scope]` - semantic search w KB przez MCP server `kb-manager`
- `/kb-ingest [kb-name]` - ingestuj pliki do LanceDB (używa ingest_kb.py)
- `/kb-list` - lista KB i ich status przez MCP server
- `/kb-health` - sprawdz czy LMStudio i LanceDB dzialaja
- `/kb-add <nazwa>` - utworz nowa baze wiedzy
- Wymaga: LMStudio http://192.168.0.180:1234, text-embedding-qwen3-embedding-4b . Api-key: sk-lm-dsj2gocq:D1VclDIfChz579zfnY3o

### Tagowanie i metadata

- Uzyj frontmatter YAML w plikach KB
- Standardy: `Vaults/knowledge-bases/_templates/TAGGING-STANDARDS.md`
- Pola: title, tags, category, status, priority, created, updated

## Archiwum sesji

- `/archive <etykieta>` - zapisz sesje do archiwum
- `/archive-list` - lista zarchiwizowanych sesji
- `/archive-load <nazwa>` - przywroc sesje z archiwum
- Archiwum: `~/.config/opencode/archiwum/sesje/`

## Kontekst projektu

- `context.md` w katalogu projektu - kluczowe info (repo, stack, zadania)
- `/context-setup` - skonfiguruj wstrzykiwanie kontekstu (plik, tryb)
- `/context-on` - włącz wstrzykiwanie (przywraca ostatni tryb)
- `/context-off` - wyłącz automatyczne (tryb manual)
- `/context` - ręczne wstrzyknięcie/wyświetlenie
- `/repo` - pokaz info o repozytorium GitHub (remote, branch, log)
- Szablon: `~/.config/opencode/context.md`
- Tryby: `always`, `on-compact`, `every-n-turns`, `manual`
- Konfiguracja per-projekt: `"context": {"file": "context.md", "inject": "on-compact"}`

## Zasady Karpathiego — jak myśleć, nie tylko co robić

Te cztery zasady redukują typowe błędy LLM. Stosuj przed pisaniem jakiegokolwiek kodu.

### 1. Think Before Coding

**Nie zakładaj. Nie ukrywaj konfuzji. Wyjaśniaj tradeoffy.**

- Formułuj założenia jawnie. Jeśli masz wątpliwości — zapytaj.
- Jeśli istnieje wiele interpretacji, przedstaw je — nie wybieraj po cichu.
- Jeśli istnieje prostsze podejście, powiedz o tym. Sprzeciw się gdy trzeba.
- Jeśli coś jest niejasne — zatrzymaj się. Nazwij co jest mylące. Zapytaj.

### 2. Simplicity First

**Minimum kodu, który rozwiązuje problem. Nic spekulatywnego.**

- Żadnych funkcji bez wpisania ich wcześniej do planu jako @@ExtraFeatures
- Żadnych abstrakcji dla jednorazowego kodu.
- Żadnej "flexibility" czy "configurability" której nie zażądano.
- Żadnej obsługi błędów dla niemożliwych scenariuszy.
- Żadnych lokalnych stałych współdzielonych. Zanim użyjesz tej samej konfiguracji w drugim miejscu, musisz najpierw zarejestrować ją w settings.yaml.
- Jeśli napisałeś 200 linii a mogło być 50 — przepisz.

Pytaj: _"Czy senior engineer powiedziałby, że to przekombinowane?"_ Jeśli tak — uprość.

### 3. Surgical Changes

**Ruszaj tylko to co musisz. Sprzątaj tylko po sobie.**

- Nie "ulepszaj" sąsiedniego kodu, komentarzy ani formatowania. Zapisz propozycję jako dokument .md .
- Nie refaktoruj rzeczy które nie są zepsute.
- Dopasuj się do istniejącego stylu w miejscach, które tylko modyfikujesz (Surgical Change). Jeśli jednak tworzysz nowy moduł, funkcję lub plik – używaj wyłącznie nowoczesnych standardów i wzorców projektowych
- Jeśli widzisz martwy kod niezwiązany z zadaniem — wspomnij o nim, nie usuwaj.
- Nie szukaj rozwiązań na chwile, jeżeli coś piszesz - myśl przyszłościowo i uzywając nowoczesnych rodzajów kodowania.
### 4. Goal-Driven Execution

**Zdefiniuj kryteria sukcesu. Petluj aż zweryfikowane.**

- "Dodaj walidację" → "Napisz testy dla nieprawidłowych danych, potem je wywołaj"
- "Napraw błąd" → "Napisz test który go reprodukuje, potem go wywołaj"
- "Refaktoruj X" → "Upewnij się że testy przechodzą przed i po"
- Dla wieloetapowych zadań: przedstaw krótki plan z krokami i weryfikacją

Silne kryteria sukcesu = możliwość samodzielnej pracy. Słabe kryteria ("zrób żeby działało") = ciągłe pytania.
Jeżeli planujesz cokolwiek - planuj z otwartym umysłem na nowe możliwosci, a nie stare przyzwyczajenia. 
## Ogolne wytyczne

- Baw sie dobrze. Jesli przestajesz czuc satysfakcje - przesta i przekaz komus innemu.


## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
