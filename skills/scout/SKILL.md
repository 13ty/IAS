---
description: >
  This skill should be used when the user asks to "find alternatives", "search GitHub",
  "discover repositories", "what's popular in X", or "find tools for my gaps".
  
  Use this skill even when the user doesn't explicitly say "scout" --
  mentions of GitHub discovery, OSS evaluation, or gap filling should also trigger this.

examples:
  - "Znajdź alternatywę dla..."
  - "Szukam biblioteki do..."
  - "Co jest popularne w dziedzinie...?"
  - "Odkryj repo dla moich braków"

negatives:
  - Do NOT use this for local inventory (use inventory)
  - Do NOT use this for analyzing existing repos (use analyzer)
---

# Skill: Scout

## Purpose
Masowe przeszukiwanie GitHub w celu znalezienia repozytoriów pasujących do braków wykrytych przez Inventory i Analyzer.

## Methodology Sources
- **OpenSSF**: Scorecard (security 0-10)
- **OpenSSF**: Criticality Score (importance 0-1)
- **Linux Foundation**: OSS Due Diligence

## Workflow

### Step 1: Extract Gaps from State
Wczytaj `state/tech_stack_oracle.json`.

### Step 2: Build Search Queries
Mapuj gaps na słowa kluczowe:

| Gap | Keywords |
|-----|----------|
| Testing | "pytest", "jest", "testing framework" |
| Security | "security scanner", "sast" |
| Documentation | "documentation generator" |
| CI/CD | "github actions", "pipeline" |

### Step 3: Search GitHub
```bash
gh search repos "{keyword}" --stars ">100" --sort stars --limit 20
```

### Step 4: Filter & Deduplicate
- Min 50 stars, 10 forks
- Active (commit <90 days)
- Compatible license

### Step 5: Score with OpenSSF
Use scorecard CLI or estimate from metadata.

### Step 6: Calculate Relevance
Keyword matching + severity weighting.

### Step 7: Prioritize Results
`final_score = scorecard * 0.3 + criticality * 0.3 + relevance * 0.4`

### Step 8: Generate Scout Report
Zapisz do state.

## Output Contract

```json
{
  "results": [{ "repo": "...", "scorecard": 0-1, "relevance": 0-1, "final_score": 0-1 }],
  "summary": { "total_scanned": N, "matched": N, "gaps_addressed": N }
}
```

## Quality Criteria
- Match Precision ≥80%
- Diversity ≥3 per gap
- Availability ≥95%

## Error Handling
| Error | Action |
|-------|--------|
| Rate limit | Exponential backoff |
| No gaps | Ask user what to search |
| No results | Broaden criteria |
