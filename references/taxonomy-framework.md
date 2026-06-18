# Taxonomy Framework — Wielowymiarowa Klasyfikacja Narzędzi

> Projekt frameworku kategoryzacji narzędzi dla heatmapy i analizy ekosystemu.
> Celem jest zastąpienie płaskich kategorii ("knowledge", "database") macierzą 4-wymiarową,
> która pozwoli wykrywać prawdziwe luki, nakładania i relacje między narzędziami.

---

## Spis treści

1. [Problem: Płaskie kategorie kłamią](#1-problem-płaskie-kategorie-kłamią)
2. [Model 4-wymiarowy](#2-model-4-wymiarowy)
3. [Wymiar A: Warstwa Techniczna](#3-wymiar-a-warstwa-techniczna-stack-level)
4. [Wymiar B: Funkcja](#4-wymiar-b-funkcja-co-narzędzie-robi)
5. [Wymiar C: Domena Aplikacyjna](#5-wymiar-c-domena-aplikacyjna-kontekst-użycia)
6. [Wymiar D: Wzorzec Architektoniczny](#6-wymiar-d-wzorzec-architektoniczny-jak-działa)
7. [Mapowanie Narzędzi — Przykłady](#7-mapowanie-narzędzi--przykłady)
8. [Heatmapa 4D — Jak Działa](#8-heatmapa-4d--jak-działa)
9. [Metryki Jakości w Wielowymiarze](#9-metryki-jakości-w-wielowymiarze)
10. [Implementacja w Analyzer](#10-implementacja-w-analyzer)
11. [Odpowiedzi na Kluczowe Pytania](#11-odpowiedzi-na-kluczowe-pytania)

---

## 1. Problem: Płaskie kategorie kłamią

### Stary model (płaska lista)

```
Kategorie: [Database, Knowledge, Search, Agent, ...]
```

Każde narzędzie dostaje jedną etykietę. Prowadzi do:

- **Fałszywych porównań**: "Calibre score 7 vs Obsidian score 8" — porównujesz e-book reader z notatnikiem grafowym
- **Ukrytych nakładań**: Dwa narzędzia w kategorii "Database" mogą być na różnych poziomach (Embedding vs SQL)
- **Niewidzialnych luk**: Brakuje Ci Search Engine, ale kategoria "Search" jest pusta, a "Database" pełna — myślisz że "masz pokrycie"
- **Płaskiego scoringu**: Wszystkie narzędzia w kategorii dostają tę samą wagę, niezależnie od warstwy

### Nowy model (4-wymiarowa macierz)

Każde narzędzie jest opisane przez krotkę `(Warstwa, Funkcja, Domena, Wzorzec)`.
Porównujesz narzędzia tylko w obrębie wspólnych wymiarów — lub tworzysz widoki przekrojowe.

---

## 2. Model 4-wymiarowy

```
Narzędzie: ChromaDB
  ┌─ Warstwa:  Vector Database
  ├─ Funkcja:  Store + Retrieve
  ├─ Domena:   Data Science / AI
  └─ Wzorzec:  Vector Search + RAG
```

### Dlaczego 4 wymiary?

| Wymiar  | Pyta                  | Odpowiada na                 |
| ------- | --------------------- | ---------------------------- |
| Warstwa | "Na czym to stoi?"    | Stack level, infrastruktura  |
| Funkcja | "Co to robi?"         | Use case, capability         |
| Domena  | "W jakim kontekście?" | Ekosystem, user persona      |
| Wzorzec | "Jak to działa?"      | Architektura, design pattern |

Każdy wymiar ma własną hierarchię — kategorie mogą być rodzicami i dziećmi.

---

## 3. Wymiar A: Warstwa Techniczna (Stack Level)

Hierarchia warstw od najniższej do najwyższej:

```
A0  Physical           [NAS, SSD, FS, S3, Dropbox]
  │
A1  Data Store         [SQLite, PostgreSQL, MySQL, MongoDB, Redis]
  │
A2  Vector Store       [ChromaDB, Qdrant, Pinecone, Weaviate]
  │
A3  Search Engine      [Elasticsearch, Meilisearch, Typesense, Algolia]
  │
A4  Index / Cache      [Redis, Memcached, SQLite FTS]
  │
A5  Embedding / ML     [Ollama, OpenAI Embeddings, sentence-transformers]
  │
A6  RAG Framework      [LangChain, LlamaIndex, Haystack]
  │
A7  Agent Framework    [LangGraph, CrewAI, AutoGen, Mem0]
  │
A8  Application        [Obsidian, Calibre, Notion, VS Code]
```

### Zasady

1. **Warstwy niższe są fundamentem dla wyższych** — ChromaDB (A2) jest poniżej LangChain (A6)
2. **Narzędzie może działać na wielu warstwach** — Redis to A1 (store) i A4 (cache)
3. **Luka na niższej warstwie blokuje wyższe** — brak Vector Store (A2) = nie zrobisz RAG (A6)
4. **A8 (Application) = warstwa użytkownika końcowego** — tutaj lądują narzędzia GUI

### Kategoryzacja narzędzi

| Narzędzie     | Warstwa | Uzasadnienie                                |
| ------------- | ------- | ------------------------------------------- |
| SQLite        | A1      | Relacyjna baza embedded                     |
| ChromaDB      | A2      | Vector DB, dedykowana do embeddingów        |
| Qdrant        | A2      | Vector DB, produkcyjna, lepsza skalowalność |
| Elasticsearch | A3      | Full-text search + aggregacje               |
| Meilisearch   | A3      | Lekki full-text search                      |
| Redis         | A1, A4  | Store (A1) + Cache (A4)                     |
| Ollama        | A5      | Lokalne embeddingi / LLM                    |
| LangChain     | A6      | Orchestracja RAG pipelines                  |
| LangGraph     | A7      | Agent memory + multi-agent                  |
| Obsidian      | A8      | Aplikacja notatek                           |
| Calibre       | A8      | Aplikacja e-book                            |
| VS Code       | A8      | Edytor kodu                                 |

### Score na warstwie

Ocena narzędzia na jego warstwie — nie porównuj A2 z A8.
Ale możesz ocenić "pokrycie warstwy": czy masz coś na A2, A3, A4?

---

## 4. Wymiar B: Funkcja (Co narzędzie robi)

Funkcje ułożone w flow od początku do końca cyklu życia danych:

```
B0  Capture           → Import, Scrape, Sync, Record, Webhook
  │
B1  Organize          → Tag, Link, Classify, Schema, Metadata
  │
B2  Store             → DB, Blob, Cache, Archive
  │
B3  Retrieve          → Search, Query, Recommend, Browse
  │
B4  Analyze           → ETL, Transform, Aggregate, Visualize
  │
B5  Publish           → Export, Render, Report, Notify
  │
B6  Collaborate       → Real-time, Async, Review, Comment
```

### Narzędzie może pełnić wiele funkcji

| Narzędzie     | Funkcja(e)                                                    | Główna |
| ------------- | ------------------------------------------------------------- | ------ |
| Obsidian      | B0 (Capture), B1 (Organize), B3 (Retrieve)                    | B0+B1  |
| Calibre       | B1 (Organize — metadata), B2 (Store — e-booki), B3 (Retrieve) | B1+B2  |
| ChromaDB      | B2 (Store), B3 (Retrieve — similarity search)                 | B2+B3  |
| Elasticsearch | B2 (Store — index), B3 (Retrieve — search)                    | B3     |
| Ollama        | B4 (Analyze — embedding), B3 (Retrieve)                       | B4     |

### Scoring funkcji

Nie "czy narzędzie ma funkcję X?", ale "jak dobrze wykonuje funkcję Y?".

- Obsidian w B1 (Organize) = 9/10 (linki, tagi, grafy)
- Calibre w B1 (Organize) = 7/10 (metadata, seria, tagi, ale brak linków między książkami)

---

## 5. Wymiar C: Domena Aplikacyjna (Kontekst użycia)

```
C0  System / Infra         [Docker, Terraform, K8s, GitHub Actions]
C1  Development            [VS Code, Git, npm, Python]
C2  Data / Analytics       [Jupyter, Metabase, Grafana, dbt]
C3  AI / ML                [Ollama, LangChain, ChromaDB, HuggingFace]
C4  PKM                    [Obsidian, Notion, Roam, Logseq]
C5  Reading / Research     [Calibre, Zotero, Readwise, Pocket]
C6  Design / Creative      [Figma, Blender, Photoshop]
C7  Project Management     [Linear, Jira, Trello, Notion]
C8  Content Management     [WordPress, Strapi, Ghost]
C9  Communication          [Slack, Discord, Email]
```

### Zasady

1. **Domena to kontekst, nie własność** — ChromaDB jest w C3 (AI/ML), ale może być też w C0 (infra)
2. **Priorytet kontekstu** — narzędzie ma PRIMARY domain (gdzie jest najczęściej używane) i SECONDARY (inne konteksty)
3. **Domeny mogą się nakładać** — Notion jest w C4 (PKM) i C7 (Project Management)

### Kluczowe rozróżnienie

Calibre i Obsidian są w RÓŻNYCH domenach:

- Calibre → C5 (Reading/Research) — organizacja kolekcji książek, konwersja formatów, metadata
- Obsidian → C4 (PKM) — tworzenie grafów wiedzy, linkowanie notatek, knowledge management

**Porównywanie ich score'ów w tej samej domenie nie ma sensu.**
Porównanie ma sens dopiero gdy nałożymy wszystkie wymiary:

- Ta sama warstwa? Calibre=A8, Obsidian=A8 → TAK (oba aplikacje)
- Ta sama funkcja? Calibre=B1+B2, Obsidian=B0+B1 → CZĘŚCIOWO (obie organizują)
- Ta sama domena? Calibre=C5, Obsidian=C4 → NIE

---

## 6. Wymiar D: Wzorzec Architektoniczny (Jak działa)

```
D0  Document Store         [KVS, blob storage, pliki]
D1  Relational DB          [SQL, schemas, ACID]
D2  Full-text Search       [Inverted index, tokenizacja]
D3  Vector Search          [Embedding similarity, ANN]
D4  Knowledge Graph        [Nodes, edges, trawersal]
D5  RAG                    [Retrieve → Augment → Generate]
D6  Agent Memory           [Conversation history, state, tools]
D7  Event Sourcing         [Event log, CQRS, stream processing]
D8  ETL / Pipeline         [Extract → Transform → Load]
D9  Pub / Sub              [Message queue, events, broadcast]
```

### Dystynkcje

| Wzorzec               | Mechanizm            | Przykład użycia                                        |
| --------------------- | -------------------- | ------------------------------------------------------ |
| Full-text Search (D2) | TF-IDF, BM25         | Szukasz "Kwatermistrz" w dokumentach                   |
| Vector Search (D3)    | Embedding cosine sim | Szukasz "narzędzie do zarządzania wiedzą" semantycznie |
| Knowledge Graph (D4)  | RDF, Property Graph  | "Pokaż wszystkie narzędzia połączone z ChromaDB"       |
| RAG (D5)              | Retriever + LLM      | "Podsumuj dokumenty o wektorowych bazach"              |

### Dlaczego to ważne?

Dwa narzędzia mogą być w tej samej warstwie i domenie, ale działać inaczej:

- Elasticsearch (D2) vs ChromaDB (D3) — obie A3/A2, obie C3, ale zupełnie inny mechanizm wyszukiwania
- Obsidian (D4 — local graph) vs Neo4j (D4 — proper graph DB) — obie D4, ale różne warstwy

---

## 7. Mapowanie Narzędzi — Przykłady

### Pełna klasyfikacja

| Narzędzie         | Warstwa (A)                 | Funkcja (B)                                         | Domena (C)              | Wzorzec (D)                   |
| ----------------- | --------------------------- | --------------------------------------------------- | ----------------------- | ----------------------------- |
| **ChromaDB**      | A2 (Vector Store)           | B2 Store, B3 Retrieve                               | C3 AI/ML                | D3 Vector Search, D5 RAG      |
| **Qdrant**        | A2 (Vector Store)           | B2 Store, B3 Retrieve                               | C3 AI/ML                | D3 Vector Search              |
| **Elasticsearch** | A3 (Search Engine)          | B2 Store, B3 Retrieve                               | C0 Infra, C3 AI/ML      | D2 Full-text Search           |
| **Redis**         | A1 (Data Store), A4 (Cache) | B2 Store                                            | C0 Infra                | D0 Document Store, D9 Pub/Sub |
| **Obsidian**      | A8 (Application)            | B0 Capture, B1 Organize, B3 Retrieve                | C4 PKM                  | D4 Knowledge Graph (local)    |
| **Calibre**       | A8 (Application)            | B1 Organize, B2 Store                               | C5 Reading              | D0 Document Store             |
| **Ollama**        | A5 (Embedding/ML)           | B4 Analyze                                          | C3 AI/ML                | D5 RAG (LLM provider)         |
| **LangChain**     | A6 (RAG Framework)          | B3 Retrieve, B4 Analyze                             | C3 AI/ML                | D5 RAG, D6 Agent Memory       |
| **LangGraph**     | A7 (Agent Framework)        | B4 Analyze                                          | C3 AI/ML                | D6 Agent Memory               |
| **Neo4j**         | A1 (Data Store)             | B2 Store, B3 Retrieve                               | C3 AI/ML                | D4 Knowledge Graph (DB)       |
| **PostgreSQL**    | A1 (Data Store)             | B2 Store, B3 Retrieve                               | C0 Infra                | D1 Relational DB              |
| **SQLite**        | A1 (Data Store)             | B2 Store, B3 Retrieve                               | C0 Infra                | D1 Relational DB              |
| **Meilisearch**   | A3 (Search Engine)          | B3 Retrieve                                         | C0 Infra                | D2 Full-text Search           |
| **Notion**        | A8 (Application)            | B0 Capture, B1 Organize, B5 Publish, B6 Collaborate | C4 PKM, C7 Project Mgmt | D0 Document Store             |
| **Zotero**        | A8 (Application)            | B0 Capture, B1 Organize                             | C5 Reading/Research     | D0 Document Store (biblio)    |

### Nakładania widoczne od razu

- **ChromaDB ↔ Qdrant**: A2=B2+B3, C3, D3 → PRAWDZIWE NAKŁADANIE (oba robią to samo)
- **Obsidian ↔ Notion**: A8, B0+B1, C4 → CZĘŚCIOWE NAKŁADANIE (oba PKM, ale Notion też C7 i B6)
- **Obsidian ↔ Calibre**: A8, B1 → TYLKO WSPÓLNA APLIKACYJNOŚĆ (różne domeny, różne wzorce)
- **Elasticsearch ↔ ChromaDB**: A3 vs A2, D2 vs D3 → KOMPLEMENTARNE (nie nakładanie)

---

## 8. Heatmapa 4D — Jak Działa

### Widoki

Zamiast jednej mapy — kilka przełączalnych widoków:

| Widok                | Osie                        | Mówi                                                  |
| -------------------- | --------------------------- | ----------------------------------------------------- |
| **Stack Coverage**   | A (Warstwa) × C (Domena)    | Które warstwy są pokryte w której domenie             |
| **Functional Gaps**  | B (Funkcja) × C (Domena)    | Których funkcji brakuje w której domenie              |
| **Overlap Matrix**   | A (Warstwa) × D (Wzorzec)   | Gdzie narzędzia się dublują                           |
| **Integration View** | A (Warstwa) × A (sąsiednie) | Czy narzędzia na sąsiednich warstwach są kompatybilne |

### Przykład: Stack Coverage dla C3 (AI/ML)

```
Warstwa        Narzędzia                    Score
────────────────────────────────────────────────────
A2 Vector      ■■■ ChromaDB  ■□□ Qdrant     8/10
A3 Search      □□□                           0/10 ← GAP
A5 Embedding   ■■■ Ollama                    7/10
A6 RAG         ■■□ LangChain                 6/10
A7 Agent       ■□□ LangGraph                 4/10
A8 App         □□□                           0/10
```

### Przykład: Overlap Matrix dla A2 (Vector Store)

```
              ChromaDB   Qdrant   Pinecone   Weaviate
ChromaDB        ●        ●●■       □          □
Qdrant          ●●■       ●        □          □
Pinecone        □         □        ●          □
Weaviate        □         □        □          ●
```

- ● = same warstwa + funkcja + domena (pełne nakładanie)
- ●■ = to samo + różni się domeną (częściowe)
- □ = różna warstwa/funkcja (brak nakładania)

---

## 9. Metryki Jakości w Wielowymiarze

### Problem: "Calibre score 7 vs Obsidian score 8"

W starym modelu: kategoria "Knowledge" → oba dostają score → Obsidian "wygrywa".
W nowym modelu: **porównuj tylko w obrębie współdzielonych wymiarów**.

### Macierz porównania Calibre vs Obsidian

| Wymiar      | Calibre           | Obsidian           | Wspólny?     | Porównanie                    |
| ----------- | ----------------- | ------------------ | ------------ | ----------------------------- |
| A (Warstwa) | A8 App            | A8 App             | ✅ TAK       | Oba aplikacje, ten sam poziom |
| B (Funkcja) | B1+B2             | B0+B1+B3           | ⚠️ Częściowo | Wspólne tylko B1 (Organize)   |
| C (Domena)  | C5 Reading        | C4 PKM             | ❌ NIE       | Różne konteksty               |
| D (Wzorzec) | D0 Document Store | D4 Knowledge Graph | ❌ NIE       | Różne architektury            |

**Wniosek**: Można porównać B1 (jak dobrze organizują), ale reszta to kategoria error.

### Poprawne pytania

| Pytanie                                          | Ma sens?                                    |
| ------------------------------------------------ | ------------------------------------------- |
| "Które narzędzie lepiej organizuje w C4 PKM?"    | ✅ TAK — porównujesz B1 w tej samej domenie |
| "Czy Calibre jest lepsze od Obsidian?"           | ❌ NIE — różne domeny i wzorce              |
| "Jaka jest luka w A2 dla C4?"                    | ✅ TAK — brak vector DB dla PKM             |
| "Czy nakładanie ChromaDB/Qdrant jest problemem?" | ✅ TAK — pełne nakładanie w A2/C3/D3        |

### Skalowanie scoringu

Zamiast jednego score — macierz score'ów per wymiar:

```python
{
    "tool": "ChromaDB",
    "scores": {
        "by_layer": {
            "A2": {"fitness": 0.85, "maturity": 0.75, "integration": 0.60}
        },
        "by_function": {
            "B2": {"fitness": 0.80, "maturity": 0.75},
            "B3": {"fitness": 0.85, "maturity": 0.75}
        },
        "by_domain": {
            "C3": {"relevance": 0.90, "adoption": 0.80}
        },
        "by_pattern": {
            "D3": {"fitness": 0.90, "maturity": 0.80},
            "D5": {"fitness": 0.70, "maturity": 0.60}
        }
    }
}
```

---

## 10. Implementacja w Analyzer

### Klasyfikator narzędzi

Analyzer_check.py przy skanowaniu repozytorium klasyfikuje je w 4 wymiary:

```python
def classify_tool(repo_data: dict) -> Taxonomy:
    return Taxonomy(
        layer=detect_layer(repo_data),        # A0-A8
        functions=detect_functions(repo_data), # lista B0-B6
        domain=detect_domain(repo_data),       # C0-C9
        pattern=detect_pattern(repo_data),      # D0-D9
    )
```

### Detekcja (heurystyki)

| Wymiar      | Heurystyka                                                             |
| ----------- | ---------------------------------------------------------------------- |
| A (Warstwa) | Zależności: `chromadb` → A2, `elasticsearch` → A3, `langchain` → A6    |
| B (Funkcja) | README: słowa kluczowe "search" → B3, "store" → B2, "analyze" → B4     |
| C (Domena)  | Tematyka repo, tagi GitHub, sekcja "About"                             |
| D (Wzorzec) | Architektura: `vectorstore` → D3, `agent` → D6, `knowledge graph` → D4 |

### Scores w 4 wymiarach

Nie ma "ogólnego score". Są scores per wymiar:

- **Layer fitness**: Jak dobrze narzędzie spełnia swoją rolę na swojej warstwie
- **Function quality**: Jakość implementacji funkcji (np. B3 Retrieve)
- **Domain relevance**: Jak bardzo narzędzie pasuje do domeny
- **Pattern maturity**: Jak dojrzały jest wzorzec architektoniczny

---

## 11. Odpowiedzi na Kluczowe Pytania

### "Czy Calibre score powinien być lepszy niż Obsidian?"

**Nie ma jednego score.** Porównanie ma sens tylko w obrębie współdzielonego wymiaru:

- **Funkcja B1 (Organize)**: Obsidian = 9/10 (linki, tagi, grafy), Calibre = 7/10 (metadata, seria). Obsidian wygrywa w organizacji.
- **Funkcja B2 (Store)**: Calibre = 8/10 (formaty, konwersja, metadata embedded), Obsidian = 6/10 (plain markdown). Calibre wygrywa w przechowywaniu.
- **Domena C4 PKM vs C5 Reading**: Nieporównywalne — różne konteksty, różne potrzeby.

W nowej heatmapie te porównania są EXPLICIT — widać które wymiary są wspólne, a które nie.

### "Czy nasz analyzer da nam klarowność?"

Tak, **jeśli** zbudujemy go na 4 wymiarach. Wtedy analyzer:

1. Klasyfikuje narzędzie w 4D → widać gdzie pasuje
2. Wykrywa nakładania tylko gdy wszystkie 4 wymiary się pokrywają
3. Pokazuje luki per wymiar — nie "brak narzędzi w DB", ale "brak narzędzia A3 Full-text Search w domenie C3 AI/ML"
4. Pozwala na sensowne porównania — tylko w obrębie wspólnych wymiarów

### "Czy to nie jest przekombinowane?"

To tyle wymiarów ile potrzeby, żeby heatmapa mówiła prawdę. Jeśli narzędzia mają być "same ... in some form or not" — potrzebujemy frameworku który to rozstrzyga, a nie ukrywa pod jednym scorem.

Płaski score to oszustwo. 4D to pierwszy krok w stronę uczciwej analizy.

---

## Podsumowanie

| Stary model                       | Nowy model                                  |
| --------------------------------- | ------------------------------------------- |
| Płaska lista kategorii            | 4-wymiarowa macierz                         |
| Jeden score na narzędzie          | Scores per (A,B,C,D)                        |
| "Calibre > Obsidian"              | "Calibre lepszy w B2, Obsidian lepszy w B1" |
| Heatmap: kolorowane karty         | Heatmap: macierz przekrojowa                |
| Nakładanie: po słowach kluczowych | Nakładanie: po wspólnych wymiarach          |
| Luki: "brak w kategorii X"        | Luki: "brak w (A=3, C=AI, D=Search)"        |

---

_Framework projektowy — wersja 0.1 (konceptualna)._
_Następny krok: implementacja klasyfikatora w analyzer_check.py._
