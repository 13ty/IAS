# Gap Keywords Mapping

Mapowanie kategorii luk na słowa kluczowe używane przez `scout_search.py`.

## GAP_KEYWORDS

```python
GAP_KEYWORDS = {
    "testing": ["pytest", "jest", "testing framework", "unit test", "test automation"],
    "security": ["security scanner", "vulnerability", "sast", "dast", "owasp"],
    "documentation": ["documentation generator", "docs", "api reference", "mkdocs"],
    "cicd": ["github actions", "pipeline", "cicd", "jenkins", "gitlab ci"],
    "monitoring": ["observability", "logging", "metrics", "tracing", "prometheus"],
    "performance": ["profiling", "benchmark", "optimization", "load testing"],
    "database": ["orm", "database", "sql", "nosql", "migration"],
    "ai": ["machine learning", "llm", "ai agent", "rag", "embedding"],
    "video": ["video processing", "animation", "motion graphics", "ffmpeg"],
    "frontend": ["react", "vue", "svelte", "component library", "ui framework"],
}
```

## Domains (10 kategorii)

| Category          | Keywords                                                    | Primary Focus                               |
| ----------------- | ----------------------------------------------------------- | ------------------------------------------- |
| **testing**       | pytest, jest, testing framework, unit test, test automation | Test automation frameworks                  |
| **security**      | security scanner, vulnerability, sast, dast, owasp          | Security scanning & vulnerability detection |
| **documentation** | documentation generator, docs, api reference, mkdocs        | Documentation generation tools              |
| **cicd**          | github actions, pipeline, cicd, jenkins, gitlab ci          | CI/CD pipelines & automation                |
| **monitoring**    | observability, logging, metrics, tracing, prometheus        | Observability & monitoring stacks           |
| **performance**   | profiling, benchmark, optimization, load testing            | Performance testing & optimization          |
| **database**      | orm, database, sql, nosql, migration                        | Database tools & ORMs                       |
| **ai**            | machine learning, llm, ai agent, rag, embedding             | AI/ML tooling & frameworks                  |
| **video**         | video processing, animation, motion graphics, ffmpeg        | Video processing & animation                |
| **frontend**      | react, vue, svelte, component library, ui framework         | Frontend frameworks & UI libraries          |

## Fallback Behavior

```python
gap_lower = gap.lower()
keywords = GAP_KEYWORDS.get(gap_lower, [gap])
```

- Jeśli gap nie istnieje w mapie → używa samej nazwy jako keyword
- Przykład: `GAP_KEYWORDS.get("devops", ["devops"])` → `["devops"]`

## Search Strategy

```python
for keyword in keywords[:2]:  # Tylko 2 pierwsze keywords per gap
    repos = search_github(keyword, max_results=5, language=language)
```

- Dla każdej luki: wyszukuje max 2 pierwsze keywords
- Każdy keyword: max 5 wyników
- Deduplikacja po `owner/repo`
- Merge coverage: repo może pokrywać wiele luk

## Przykład użycia

```bash
# Gap: testing
python scout_search.py --gaps "testing"
# Wyszukuje: "pytest", "jest" (pierwsze 2 z listy)

# Gap: security
python scout_search.py --gaps "security"
# Wyszukuje: "security scanner", "vulnerability"

# Multiple gaps
python scout_search.py --gaps "testing,security,monitoring"
# Wyszukuje 2 keywords per gap = 6 zapytań
```

## Output Coverage

```json
{
  "gaps": ["testing", "security"],
  "summary": {
    "gaps_covered": ["testing", "security"],
    "gaps_missing": []
  }
}
```

- `gaps_covered`: luki pokryte przez co najmniej 1 repo
- `gaps_missing`: luki bez wyników

## Rozszerzalność

Aby dodać nową kategorię:

1. Dodaj do `GAP_KEYWORDS` w `scout_search.py`
2. Zaktualizuj tę tabelę
3. Testuj z `--gaps "new_category"`

## Ograniczenia

- **Tylko 10 kategorii** — nowe luki wymagają ręcznego dodania
- **Hardcoded keywords** — brak dynamicznego rozszerzania
- **Tylko 2 keywords per gap** — może przegapić repozytoria
- **GitHub only** — brak supportu dla GitLab, Bitbucket, etc.

---

_Wygenerowane z `scout_search.py::GAP_KEYWORDS`_
