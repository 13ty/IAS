---
title: "IAS & Spartanin — short overview"
description: "Brief, non-technical overview for external readers"
version: 1.0.0
---

# IAS & Spartanin — Jak to działa?

## IAS — Kwatermistrz

**Co to jest?**  
Narzędzie, które wie dokładnie **co masz zainstalowane** i **co Ci brakuje** w środowisku deweloperskim.

**Jak działa?**

```
Ty mówisz: "Przeskanuj mój projekt"
         ↓
IAS skanuje → widzi jakie narzędzia używasz
         ↓
Porównuje z "idealnym" stackiem
         ↓
Mówi Ci: "Masz to ✅, tego brakuje ❌, a to możesz wymienić 🔄"
```

**Co robi?**

| Komenda          | Co robi                                                 |
| ---------------- | ------------------------------------------------------- |
| `/ias-scan`      | Pełny skan: co masz, czego brakuje, co poleca           |
| `/ias-inventory` | Lista narzędzi w projekcie                              |
| `/ias-analyze`   | Ocena jakości kodu (Clean Architecture, utrzymywalność) |
| `/ias-scout`     | Szuka alternatyw na GitHubie                            |
| `/ias-audit`     | Ocenia czy nowe narzędzie jest warte instalacji         |
| `/ias-heatmap`   | Mapa ciepła — co jest mocne, co słabe                   |

**Przykład:**

```
Ty: "Przeskanuj R:\Dev\MojaAplikacja"
IAS:
  ✅ Masz: Python 3.11, FastAPI, pytest
  ❌ Brakuje: CI/CD, Docker, linter
  🔄 pytest jest OK, ale unittest2 jest lepszy dla Twojego przypadku
```

**Dla kogo?**

- Deweloperzy, którzy chcą wiedzieć "co jeszcze potrzebuję?"
- Zespoły, które chcą uporządkować narzędzia
- Ktoś, kto zaczyna nowy projekt i nie wie od czego zacząć

---

## Spartanin (IAmSparta)

**Co to jest?**  
Plan strategiczny dla IAS — **jak rozwijać system工具** w dłuższej perspektywie.

**Na czym polega?**  
Zamiast losowo dodawać narzędzia, Spartanin pomaga:

1. **Zrozumieć** — co naprawdę potrzebujesz (analiza luk)
2. **Zaplanować** — priorytety, kolejność adopcji
3. **Wdrożyć** — krok po kroku, z testowaniem
4. **Zmierzyć** — czy nowe narzędzia faktycznie pomagają?

**Przykład:**

```
Ty: "Chcę dodać narzędzia AI do mojego stacka"
Spartanin:
  1. Analizuje: masz 1 narzędzie AI (PromptLab), brakuje 5 innych
  2. Planuje: zacznij od wektorowej bazy danych (Potrzebna do RAG)
  3. Wdraża: dodaj Qdrant → przetestuj → dodaj embedding → przetestuj
  4. Mierzy: czy szybkość odpowiedzi wzrosła? Czy jakość się poprawiła?
```

**Dla kogo?**

- Ktoś, kto chce **strategicznie** rozwijać swój stack
- Zespoły planujące migrację lub modernizację
- Ktoś, kto nie chce "kupować wszystkiego po kolei"

---

## Podsumowanie

|              | IAS                        | Spartanin                           |
| ------------ | -------------------------- | ----------------------------------- |
| **Co?**      | Skaner + doradca           | Strateg + planista                  |
| **Kiedy?**   | "Co mam teraz?"            | "Co będę mieć za 3 miesiące?"       |
| **Jak?**     | Szybki skan, od razu wynik | Analiza → plan → wdrożenie → pomiar |
| **Przykład** | "Brakuje CI/CD"            | "Dodaj GitHub Actions w 3 etapach"  |

---

## Technicznie (bardzo krótko)

- **IAS**: Python skrypty + JSON/CSV dane + MCP server (dla agentów AI)
- **Spartanin**: Warstwa strategiczna nad IAS (planowanie, priorytety, metryki)
- **Dane**: `tool_registry.json` (16 narzędzi), `proposals.csv` (kolejka audytów)
- **Integracje**: Obsidian Vault (zapis), LanceDB (semantic search), GitHub (odkrywanie)

---

_Napisano dla kogoś, kto nie zna projektu. Bez żargonu technicznego._
