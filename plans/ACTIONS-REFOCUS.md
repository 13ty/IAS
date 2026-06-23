# IAS — Akcje Refocus

> Wyciąg z `TOREFINE.md`: co trzeba zrobić, w kolejności.

## P0: `/ias-query` — semantic search dla tooli

- [ ] Komenda slash `/ias-query <query>` w plugin.json
- [ ] Skrypt `ias_query.py`: embedding → LanceDB → tool + path + run_command
- [ ] Fallback: grep + fuzzy match przez tool_registry.json

## P1: Bulk scan środowiska

- [ ] `scan_environment.py` — skanuje R:\Dev\Tools, %PATH%, Program Files, pluginy
- [ ] Auto-detekcja + dedup → tool_registry.json + LanceDB embedding
- [ ] Cel: ~2000 tooli zarejestrowanych

## P2: Akcja po znalezieniu

- [ ] copy-path, open-dir, run-help, edit-config, show-aliases

## P3: Połączenie KG z registry

- [ ] Knowledge graph jako żywy widok na registry, nie osobna kopia

## P4: Repo Evaluation → osobny feature

- [ ] Wydzielić do osobnego namespace
- [ ] Nie łączyć z core search
