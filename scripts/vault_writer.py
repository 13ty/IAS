#!/usr/bin/env python3
"""
vault_writer.py — Kwatermistrz: Zapis ocen do Obsidian vault.

Generuje pliki analizy zgodne z template v3 (Poznaj → Zrozum → Zdecyduj).
Zapisuje do Vaults/tool-registry/analyses/ z poprawnym frontmatter YAML.

Użycie:
  python vault_writer.py --repo https://github.com/user/repo --output analyses/
  python vault_writer.py --tool-data data/tool_registry.json --tool-name Mermaid-CLI
  python vault_writer.py --audit data/audits/20260607_pytest.md
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Domyślna ścieżka vaultu (nadpisywana przez --vault-path)
VAULT_PATH = Path(__file__).parent.parent.parent.parent / "Vaults" / "tool-registry"
ANALYSES_DIR = VAULT_PATH / "analyses"


def slugify(text: str) -> str:
    """Konwertuje nazwę na bezpieczny filename."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "unknown"


def generate_repo_analysis(data: Dict) -> str:
    """
    Generuje pełną analizę repozytorium wg template v3.

    data wymagane:
    - repo_full_name, repo_url, primary_language, stars, license, last_updated
    - mission (jedno zdanie)
    - personality (opis osobowości)
    - feature_matrix (lista dict: cecha, nasz_swiat, ich_swiat, roznica)
    - unique_points (lista 3)
    - not_what (czego nie są)
    - strengths (lista dict: nazwa, dlaczego)
    - challenges (lista dict: nazwa, dlaczego)
    - inspiration (iskry)
    - adoption_effort (dict: czas_nauki, migracja, testy, wsparcie - każdy 1-10)
    - value_score (dict: nowe_funkcje, jakosc_vs_nasze, integracje, wydajnosc - każdy 1-10)
    - net_benefit (float)
    - verdict (ZAPROSZENIE DO TAŃCA / PILOT / LEKCJA)
    - team_acceptance (dict: kto_uzywa, radość_frustracja, sprzeciw, ryzyko_buntu)
    - learning_value (dict: wzorzec, inspiracja, anti_wzorzec, architektura)
    - notes (opcjonalnie)
    """
    ae = data.get("adoption_effort", {})
    vs = data.get("value_score", {})

    # Oblicz sumy ważone
    ae_total = (
        ae.get("czas_nauki", 5) * 0.30
        + ae.get("migracja", 5) * 0.30
        + ae.get("testy", 5) * 0.20
        + ae.get("wsparcie", 5) * 0.20
    )
    vs_total = (
        vs.get("nowe_funkcje", 5) * 0.40
        + vs.get("jakosc_vs_nasze", 5) * 0.30
        + vs.get("integracje", 5) * 0.20
        + vs.get("wydajnosc", 5) * 0.10
    )

    tags = data.get("tags", ["@analysis", "@benchmark"])
    tag_lines = "\n".join(f"  - {t}" for t in tags)

    # Feature matrix
    feature_rows = ""
    for f in data.get("feature_matrix", []):
        feature_rows += f"| {f.get('cecha', '')} | {f.get('nasz_swiat', '')} | {f.get('ich_swiat', '')} | {f.get('roznica', '')} |\n"

    # Strengths
    strengths = ""
    for i, s in enumerate(data.get("strengths", []), 1):
        strengths += f"{i}. **{s.get('nazwa', '')}** – {s.get('dlaczego', '')}\n"

    # Challenges
    challenges = ""
    for i, c in enumerate(data.get("challenges", []), 1):
        challenges += f"{i}. **{c.get('nazwa', '')}** – {c.get('dlaczego', '')}\n"

    # Verdict checkbox
    verdict = data.get("verdict", "LEKCJA")
    verdict_checks = {
        "ZAPROSZENIE DO TAŃCA": "- [x] ✅ **ZAPROSZENIE DO TAŃCA** – Zmieniamy kierunek\n- [ ] 🟡 **PILOT** – Przetestujmy najpierw  \n- [ ] 📚 **LEKCJA** – Idziemy osobno, ale uczymy się\n- [ ] ❌ **NIE TERAZ** – Może kiedyś w przyszłości",
        "PILOT": "- [ ] ✅ **ZAPROSZENIE DO TAŃCA** – Zmieniamy kierunek\n- [x] 🟡 **PILOT** – Przetestujmy najpierw  \n- [ ] 📚 **LEKCJA** – Idziemy osobno, ale uczymy się\n- [ ] ❌ **NIE TERAZ** – Może kiedyś w przyszłości",
        "LEKCJA": "- [ ] ✅ **ZAPROSZENIE DO TAŃCA** – Zmieniamy kierunek\n- [ ] 🟡 **PILOT** – Przetestujmy najpierw  \n- [x] 📚 **LEKCJA** – Idziemy osobno, ale uczymy się\n- [ ] ❌ **NIE TERAZ** – Może kiedyś w przyszłości",
        "NIE TERAZ": "- [ ] ✅ **ZAPROSZENIE DO TAŃCA** – Zmieniamy kierunek\n- [ ] 🟡 **PILOT** – Przetestujmy najpierw  \n- [ ] 📚 **LEKCJA** – Idziemy osobno, ale uczymy się\n- [x] ❌ **NIE TERAZ** – Może kiedyś w przyszłości",
    }

    ta = data.get("team_acceptance", {})
    radość = (
        "🟢 Więcej radości"
        if ta.get("radość_frustracja", "radość") == "radość"
        else "🔴 Więcej frustracji"
    )

    lv = data.get("learning_value", {})

    content = f"""---
type: repo-analysis
version: 3.0.0
created: {datetime.now().strftime("%Y-%m-%d")}
category: skill-2-benchmark
subcategory: repository-evaluation
tags:
{tag_lines}
optimized_for: rag
---

# 🔬 Analiza Repozytorium: {data.get("repo_full_name", "Unknown")}

> *{data.get("mission", "Analiza w toku")}*

---

## 📍 1. Poznaj – Pierwsze spotkanie

### 🪪 Tożsamość
```
Nazwa: {data.get("repo_full_name", "Unknown")}
URL: {data.get("repo_url", "")}
Główna mowa: {data.get("primary_language", "Unknown")}
Gwiazdki: {data.get("stars", 0)} ⭐
Licencja: {data.get("license", "Unknown")}
Ostatnia aktualizacja: {data.get("last_updated", "Unknown")}
```

### 🎯 Misja (w jednym zdaniu)
> *"{data.get("mission", "")}"*

### 👥 Kto to jest?
> *{data.get("personality", "")}*

---

## 🔍 2. Zrozum – Głęboka rozmowa

### ⚖️ Różnice które mają znaczenie

#### Porównanie z naszym światem
| Cecha | Nasz świat | Ich świat | Różnica |
|-------|------------|-----------|---------|
{feature_rows}

#### Co je czyni wyjątkowymi?
{chr(10).join(f"> {p}" for p in data.get("unique_points", []))}

#### Czego NIE są?
> *{data.get("not_what", "")}*

### 💪 Ich mocne strony (co możemy się nauczyć)
{strengths}

### 😟 Ich wyzwania (czego możemy się nauczyć czego NIE robić)
{challenges}

### 💡 Iskry inspiracji
> *{data.get("inspiration", "")}*

---

## ⚖️ 3. Zdecyduj – Czy warto iść dalej razem?

### 📊 Rachunek zysków i strat

#### Koszt przyjęcia (Adoption Effort)

| Element | Ocena (1-10) | Waga | Wynik |
|---------|--------------|------|-------|
| Czas nauki | {ae.get("czas_nauki", 5)}/10 | 0.30 | {ae.get("czas_nauki", 5) * 0.30:.1f} |
| Migracja | {ae.get("migracja", 5)}/10 | 0.30 | {ae.get("migracja", 5) * 0.30:.1f} |
| Testy | {ae.get("testy", 5)}/10 | 0.20 | {ae.get("testy", 5) * 0.20:.1f} |
| Wsparcie | {ae.get("wsparcie", 5)}/10 | 0.20 | {ae.get("wsparcie", 5) * 0.20:.1f} |
| **SUMA** | | | **{ae_total:.1f}/10** |

#### Wartość (Value Score)

| Element | Ocena (1-10) | Waga | Wynik |
|---------|--------------|------|-------|
| Nowe funkcje | {vs.get("nowe_funkcje", 5)}/10 | 0.40 | {vs.get("nowe_funkcje", 5) * 0.40:.1f} |
| Jakość vs nasze | {vs.get("jakosc_vs_nasze", 5)}/10 | 0.30 | {vs.get("jakosc_vs_nasze", 5) * 0.30:.1f} |
| Integracje | {vs.get("integracje", 5)}/10 | 0.20 | {vs.get("integracje", 5) * 0.20:.1f} |
| Wydajność | {vs.get("wydajnosc", 5)}/10 | 0.10 | {vs.get("wydajnosc", 5) * 0.10:.1f} |
| **SUMA** | | | **{vs_total:.1f}/10** |

### 🎯 Ostateczna decyzja
```
Net Benefit = {vs_total:.1f} - ({ae_total:.1f} × 0.5) = {data.get("net_benefit", 0):.2f}
```

#### Interpretacja wyniku:
- **> 5.0** → ✅ **ZAPROSZENIE DO TAŃCA** – Warto zmienić kierunek
- **> 0.0** → 🟡 **PILOT** – Warto przetestować na małą skalę  
- **≤ 0.0** → 📚 **LEKCJA** – Nie idziemy razem, ale możemy się nauczyć

### 🤝 Akceptacja przez zespołu

| Pytanie | Odpowiedź |
|---------|-----------|
| Kto głównie będzie tego używał? | {ta.get("kto_uzywa", "")} |
| Czy agenci będą mieli więcej radości czy frustracji? | {radość} |
| Czy są grupy które mogą się sprzeciwić? | {ta.get("sprzeciw", "")} |
| Jak duże jest ryzyko buntu? | {ta.get("ryzyko_buntu", 5)}/10 |

> ⚠️ *"Nie zabieraj agentom ich ulubionego narzędzia – to jak zabrać dziecku ulubioną zabawkę."*

### 🎓 Wartość nauki (bez względu na decyzję)

| Kategoria | Co warto zapamiętać? |
|-----------|----------------------|
| **Wzorzec** | {lv.get("wzorzec", "")} |
| **Inspiracja** | {lv.get("inspiracja", "")} |
| **Anti-Wzorzec** | {lv.get("anti_wzorzec", "")} |
| **Architektura** | {lv.get("architektura", "")} |

---

## 📝 Notatki z podróży
> *{data.get("notes", "Brak dodatkowych notatek")}*

---

## ✅ Podsumowanie decyzji

{verdict_checks.get(verdict, verdict_checks["LEKCJA"])}

**Moje uzasadnienie:**
> *{data.get("justification", "")}*

---

*Stworzono podczas analizy {data.get("repo_full_name", "Unknown")}*
*Szablon v3.0 – gdzie analiza staje się przygodą*
"""
    return content


def write_to_vault(content: str, filename: str, subdir: str = "analyses") -> Path:
    """Zapisuje plik do vaultu."""
    target_dir = VAULT_PATH / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def write_repo_analysis(data: Dict, filename: Optional[str] = None) -> Path:
    """Pełna funkcja: generuje + zapisuje analizę repozytorium."""
    if not filename:
        repo_name = data.get("repo_full_name", "unknown").replace("/", "-")
        date_prefix = datetime.now().strftime("%Y%m%d")
        filename = f"{date_prefix}_{slugify(repo_name)}.md"

    content = generate_repo_analysis(data)
    filepath = write_to_vault(content, filename)
    print(f"✅ Zapisano analizę: {filepath}")
    return filepath


def write_tool_registration(tool_data: Dict) -> Path:
    """Zapisuje prostą analizę rejestracji narzędzia (uproszczony template)."""
    name = tool_data.get("name", "unknown")
    date_prefix = datetime.now().strftime("%Y%m%d")
    filename = f"{date_prefix}_{slugify(name)}-registration.md"

    content = f"""---
type: tool-registration
version: 1.0.0
created: {datetime.now().strftime("%Y-%m-%d")}
category: tool-registry
tags:
  - "@tool"
  - "@registration"
  - "@{tool_data.get("domain", "unknown")}"
optimized_for: rag
---

# 📦 Rejestracja Narzędzia: {name}

## 🪪 Tożsamość
```
Nazwa: {name}
Wersja: {tool_data.get("version", "unknown")}
Typ: {tool_data.get("type", "unknown")}
Domena: {tool_data.get("domain", "unknown")}
Lokalizacja: {tool_data.get("location", "")}
```

## 🎯 Opis
> *{tool_data.get("description", "")}*

## 🚀 Uruchomienie
```bash
{tool_data.get("run_command", "")}
```

## 🔄 Aktualizacja
```bash
{tool_data.get("update_command", "Brak komendy aktualizacji")}
```

## 📊 Alternatywy
{", ".join(tool_data.get("alternatives", ["brak"]))}

---

*Zarejestrowano przez IAS Kwatermistrz ({datetime.now().strftime("%Y-%m-%d %H:%M")})*
"""
    filepath = write_to_vault(content, filename, subdir="analyses")
    print(f"✅ Zapisano rejestrację: {filepath}")
    return filepath


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Vault Writer – zapis ocen do Obsidian"
    )
    parser.add_argument("--repo", type=str, help="URL repozytorium")
    parser.add_argument(
        "--tool-data", type=str, help="Ścieżka do JSON z danymi narzędzia"
    )
    parser.add_argument("--tool-name", type=str, help="Nazwa narzędzia do filtrowania")
    parser.add_argument(
        "--audit", type=str, help="Ścieżka do pliku audytu do konwersji"
    )
    parser.add_argument("--output", type=str, help="Niestandardowa ścieżka wyjściowa")
    args = parser.parse_args()

    if args.tool_data:
        with open(args.tool_data, encoding="utf-8") as f:
            tool_data = json.load(f)
        if args.tool_name:
            tool_data = tool_data.get("tools", {}).get(args.tool_name, tool_data)
        write_tool_registration(tool_data)
    elif args.repo:
        # Prosta analiza z URL
        repo_name = args.repo.rstrip("/").split("/")[-2:]
        repo_full = "/".join(repo_name)
        data = {
            "repo_full_name": repo_full,
            "repo_url": args.repo,
            "primary_language": "Unknown",
            "stars": 0,
            "license": "Unknown",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "mission": f"Analiza repozytorium {repo_full}",
            "personality": "W toku – wymaga głębszej analizy",
            "feature_matrix": [],
            "unique_points": [],
            "not_what": "",
            "strengths": [],
            "challenges": [],
            "inspiration": "",
            "adoption_effort": {
                "czas_nauki": 5,
                "migracja": 5,
                "testy": 5,
                "wsparcie": 5,
            },
            "value_score": {
                "nowe_funkcje": 5,
                "jakosc_vs_nasze": 5,
                "integracje": 5,
                "wydajnosc": 5,
            },
            "net_benefit": 2.5,
            "verdict": "PILOT",
            "team_acceptance": {
                "kto_uzywa": "Wszyscy agenci",
                "radość_frustracja": "radość",
                "sprzeciw": "brak",
                "ryzyko_buntu": 2,
            },
            "learning_value": {
                "wzorzec": "",
                "inspiracja": "",
                "anti_wzorzec": "",
                "architektura": "",
            },
            "notes": "",
            "justification": "Wstępna analiza – wymaga uzupełnienia",
        }
        write_repo_analysis(data)
    elif args.audit:
        # Konwersja istniejącego audytu
        with open(args.audit, encoding="utf-8") as f:
            audit_data = (
                json.load(f) if args.audit.endswith(".json") else {"raw": f.read()}
            )
        print(f"📋 Konwersja audytu: {args.audit}")
        # TODO: pełna konwersja
        print("⚠️  Konwersja audytu w toku – użyj --repo lub --tool-data")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
