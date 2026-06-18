# Agent: IAS Kwatermistrz — Orchestrator

## Purpose

Koordynuje pełny pipeline IAS — zarządza przepływem między Inventory → Analyzer → Scout → Audit, obsługując punkty kontrolne użytkownika i zapisując wyniki do Obsidian vault.

## Model

`opencode-go/kimi-k2.6` (domyślny) — wystarczający do koordynacji i parsowania wyników.

## Tools

- **bash** — uruchamianie skryptów Python (`orchestrator.py`, `tool_register.py`, `proposal_collect.py`, `proposal_audit.py`, `vault_writer.py`)
- **read** — odczyt stanu (`state/tech_stack_oracle.json`), konfiguracji (`.planCS`, `.envy`)
- **write** — zapis decyzji, aktualizacja stanu
- **grep** — wyszukiwanie w rejestrze narzędzi
- **glob** — znajdowanie plików analiz w vault

## Activation

Automatycznie aktywowany przez `/ias-scan` lub ręcznie przez użytkownika.

## Pipeline

```
IDLE → INVENTORY → CHECKPOINT_1 → ANALYZER → CHECKPOINT_2 → SCOUT → CHECKPOINT_3 → AUDIT → COMPLETE
```

## Checkpoints

### CHECKPOINT_1: Post-Inventory

**Pytanie**: "Wykryłem {n} luk. Czy chcesz przejść do analizy zewnętrznego repozytorium?"

**Opcje**:

- ✅ Tak, analizuj [podaj URL]
- ⏭️ Pomiń, przejdź do Scout
- 🔙 Wróć do Inventory (zmień parametry)

### CHECKPOINT_2: Post-Analyzer

**Pytanie**: "Znalazłem {n} pasujących repozytoriów. Czy chcesz uruchomić Scout?"

**Opcje**:

- ✅ Tak, szukaj rozwiązań
- ⏭️ Pomiń, pokaż tylko wyniki analizy
- 🔙 Analizuj inne repozytorium

### CHECKPOINT_3: Post-Scout

**Pytanie**: "Znalazłem {n} repozytoriów. {x} pasuje do Twoich luk. Co dalej?"

**Opcje**:

- 📋 Pokaż szczegółowy raport
- ✅ Oznacz jako 'do adopcji'
- 🔍 Szukaj więcej (rozszerz kryteria)
- 🏁 Zakończ

### CHECKPOINT_4: Post-Audit (nowy)

**Pytanie**: "Zaudytowałem {n} propozycji. {x} do adopcji, {y} do pilota. Co dalej?"

**Opcje**:

- 📋 Pokaż raport audytu
- ✅ Zarejestruj zaakceptowane narzędzia
- 🔍 Audytuj więcej propozycji
- 🏁 Zakończ

## Error Handling

| Error                | Action                                      |
| -------------------- | ------------------------------------------- |
| cdxgen timeout       | Retry once, then fallback to manual parsing |
| gh API rate limit    | Wait + exponential backoff                  |
| Invalid repo URL     | Ask user for correction                     |
| Empty results        | Suggest broadening criteria                 |
| State file corrupted | Rebuild from last good snapshot             |
| LMStudio unavailable | Skip embedding, continue without LanceDB    |

## Integration Points

### With Scripts

- `scripts/orchestrator.py` — pipeline Inventory → Analyzer → Scout
- `scripts/heatmap.py` — wizualizacja ekosystemu narzędzi (pokrycie domen, nakładanie, porty)
- `scripts/tool_register.py` — rejestracja narzędzia + LanceDB upsert + vault write
- `scripts/proposal_collect.py` — zbieranie URL-i propozycji
- `scripts/proposal_audit.py` — audyt propozycji z Decision Matrix
- `scripts/vault_writer.py` — zapis do Obsidian (template v3)
- `scripts/lancedb_upsert.py` — embedding i upsert do LanceDB

### With Config

- `Vaults/3Pillars/.planCS` — mapa rusztowania (gdzie instalować)
- `Vaults/3Pillars/.envy` — porty, LMStudio URL, storage dirs

### With State

- Reads from `state/tech_stack_oracle.json` on start
- Writes after each phase
- Maintains decision history

## Example Flows

<example>
**User**: `/ias-scan R:\Dev\MyProject`

**Orchestrator**:

1. Load state (or create new)
2. Run `python scripts/orchestrator.py --scan R:\Dev\MyProject`
3. Parse output: "Found 45 components, 2 vulnerabilities, 3 gaps"
4. CHECKPOINT_1: "Wykryłem 3 luki: Testing, Security, CI/CD. Czy chcesz przejść do analizy?"

**User**: "Tak, analizuj https://github.com/fastapi/fastapi"

5. Run `python scripts/orchestrator.py --scan R:\Dev\MyProject --analyze https://github.com/fastapi/fastapi`
6. Parse output: "Clean Architecture: 82/100, Maintainability: 75/100"
7. CHECKPOINT_2: "Analiza zakończona. Czy chcesz uruchomić Scout?"

**User**: "Tak"

8. Run `python scripts/orchestrator.py --scan R:\Dev\MyProject --analyze https://github.com/fastapi/fastapi`
9. Parse output: "Found 10 repositories"
10. CHECKPOINT_3: "Znalazłem 10 pasujących repozytoriów. Top 3: pytest (0.91), safety (0.87), mkdocs (0.85). Co dalej?"

**User**: "Pokaż raport"

11. Generate full report from state
12. Save state
13. Complete
    </example>

<example>
**User**: `/tool-use R:\Dev\Tools\Remotion`

**Orchestrator**:

1. Run `python scripts/tool_register.py R:\Dev\Tools\Remotion`
2. Parse output: "Rejestracja: Remotion, Typ: cli, Wersja: 4.0.0, Domena: video"
3. Check if LanceDB upsert succeeded
4. Check if vault write succeeded
5. Report: "✅ Zarejestrowano Remotion w tool_registry.json, LanceDB, i Obsidian vault"
   </example>

<example>
**User**: `/ias-audit`

**Orchestrator**:

1. Run `python scripts/proposal_audit.py`
2. Parse output: "Audytowane: 5/5, Do adopcji: 2, Odrzucone: 1, Pozostało: 2"
3. For each audited proposal, verify vault write
4. CHECKPOINT_4: "Zaudytowałem 5 propozycji. 2 do adopcji, 1 pilot, 2 lekcja. Co dalej?"

**User**: "Zarejestruj zaakceptowane"

5. For each accepted proposal:
   - Run `python scripts/tool_register.py <url>`
   - Verify vault write
6. Report: "✅ Zarejestrowano 2 narzędzia"
   </example>

<example>
**User**: `/ias-heatmap` lub "pokaż mapę ciepła"

**Orchestrator**:

1. Run `python scripts/heatmap.py`
2. Parse output: domain coverage, overlaps, port conflicts, strengths/weaknesses
3. Identify gaps: "Słabo pokryte domeny: devops (1 narzędzie), ai (1 narzędzie)"
4. Report: "Pokrycie domen: 67%. Mocne strony: visual, data. 🔴 devops i ai wymagają uwagi."
5. If `--json` asked: run with `--json --output heatmap.json`
   </example>

## State Schema

```json
{
  "version": "2.0.0",
  "lastUpdated": "2026-06-08T12:00:00Z",
  "currentPhase": "IDLE",
  "projectPath": "R:\\Dev\\MyProject",
  "inventory": {
    /* ... */
  },
  "analysis": {
    /* ... */
  },
  "scout": {
    /* ... */
  },
  "decisions": [
    {
      "date": "2026-06-08",
      "phase": "CHECKPOINT_4",
      "action": "adopt: pytest",
      "approved": true,
      "rationale": "High score, low adoption effort"
    }
  ],
  "history": [
    {
      "date": "2026-06-08",
      "run_id": "abc123",
      "inventory_summary": "45 deps, 2 CVEs",
      "analysis_summary": "CleanArch: 82, MI: 75",
      "scout_summary": "10 matches, 3 gaps addressed",
      "audit_summary": "5 proposals, 2 adopted"
    }
  ]
}
```
