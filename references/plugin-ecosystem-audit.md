# Plugin Ecosystem Audit

> Analiza katalogu `plugins/` — co warto zachować jako źródło, co jest duplikatem.
> Data: 2026-06-12

## ✅ WARTE ZACHOWANIA / WARTOŚĆ DODANA

| Element                       | Dlaczego przydatne                                                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Pluginy w `plugins/`          | Źródłowe definicje pluginów (plugin.yaml, requirements, assets, workflows, references) — potrzebne do plugin-manager, instalacji, audytu, aktualizacji |
| ADRs w `documentation/ADRs/`  | 7 ADR-ów (001-007) — polityka architektury pluginów, symlinki, coupling, installer — referencyjne                                                      |
| `docs/superpowers/`           | Specyfikacja test suite vision, TDD, TradingView harness — jeśli robisz TDD/broker automation                                                          |
| `docs/MAF-research-analysis/` | Multi-Agent Framework research — jeśli budujesz agent-systemy                                                                                          |
| `.agent/rules/*.md`           | 5 reguł (coding-conventions, dependency-management, plugin-architecture, self-evolution, TDD) — enforcement layer                                      |
| auditor skill (IAS)           | Decision matrix do oceny narzędzi — jeśli robisz tool adoption reviews                                                                                 |
| heatmap skill (IAS)           | Wizualizacja ekosystemu narzędzi, konflikty portów, pokrycie domen — jeśli zarządzasz tool registry                                                    |

## ❌ NIEPRZYDATNE / DUPLIKATY

| Element                                                                                 | Powód                                                                     |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 127 skilli w `plugins/*/skills/`                                                        | Wszystkie już zainstalowane w `.agents/skills/` — to tylko kopie źródłowe |
| `using-exploration-cycle`                                                               | Nie ma SKILL.md, folder pusty/uszkodzony                                  |
| Pluginy bez plugin.yaml (archive, commands, context-injector, IAS, memory-tiers, spark) | To lokalne pluginy OMO, nie z richfrem — już działają, nie kopiuj         |

## 🎯 REKOMENDACJA

### Zachowaj w `plugins/` (jako źródło):

- spec-kitty-plugin (19 skilli, SDD lifecycle)
- obsidian-wiki-engine (10 skilli, vault/wiki/RLM)
- agent-agentic-os (18 skilli, memory/eval/self-evolution)
- agent-loops (6 skilli, learning loops)
- agent-memory (14 skilli, RLM/vector/memory)
- agent-scaffolders (30 skilli, generators)
- cli-agents (12 skilli, multi-LLM router)
- exploration-cycle-plugin (20 skilli, discovery/prototyping/vibe)
- plugin-manager (3 skilli, install/sync/audit)
- dev-utils (13 skilli, ADR audit, mermaid, context bundler)
- dependency-management (1 skill, pip-compile)

### Dodaj 2 brakujące skille IAS (jeśli chcesz):

- auditor
- heatmap
