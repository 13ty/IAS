---
name: ias-audit
description: "Audytuje propozycje narzędzi z proposals.csv — ocenia każdą względem gapów, nakładania i wartości."
trigger: /ias-audit
bash: python scripts/proposal_audit.py {{--all}} {{--id}}
argument-hint: "[--all] [--id N]"
allowed-tools:
  - bash
  - read
  - write
  - grep
  - glob
  - webfetch
  - kagi_kagi_extract
---

# Command: /ias-audit

## Description

Audytuje propozycje narzędzi zgromadzone w `data/proposals.csv` — każdą ocenia względem:

- Istniejących luk (gaps z Inventory)
- Nakładania funkcjonalności z obecnymi narzędziami
- Jakości kodu, bezpieczeństwa i społeczności
- Wartości adopcji

## Usage

```
/ias-audit                     # Audytuj wszystkie pending
/ias-audit --all               # Audytuj wszystkie (również już audytowane)
/ias-audit --id 3              # Audytuj konkretną propozycję (ID = wiersz)
```

## Workflow

### Step 1: Load Proposals

Wczytaj `data/proposals.csv` — filtruj po statusie `pending`.

### Step 2: For Each Proposal

1. **Analyzer** — przeanalizuj repo (struktura, architektura, MI)
2. **Tool Registry check** — czy już mamy coś podobnego?
3. **Gap analysis** — czy wypełnia lukę z inventory?
4. **Overlap detection** — czy nakłada się na istniejące?
5. **Ocena końcowa** — skonsoliduj wyniki

### Step 3: Save Results

- Zaktualizuj `proposals.csv` (status → `audited`)
- Zapisz pełną ocenę jako plik .md

### Step 4: Report

Podsumowanie: które propozycje warte adopcji, które odrzucić.

## Output

```
📋 Audyt Propozycji
──────────────────

Propozycja: pytest-dev/pytest (https://github.com/pytest-dev/pytest)
  Status: pending → audited
  Typ: repo | Domena: testing
  Analyzer: Clean Arch 85/100, MI 78/100
  Tool Registry: brak nakładania ✅
  Gap Analysis: wypełnia lukę TESTING (HIGH) ✅
  Net Benefit: 8.2/10 → ZAPROSZENIE DO TAŃCA
  Ocena: data/audits/pytest-dev-pytest.md

Podsumowanie:
  Audytowane: 3/5
  Do adopcji: 2
  Odrzucone: 1
  ⏳ Pozostało: 2
```
