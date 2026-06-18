# Search API (GitHub CLI)

Specyfikacja API używanego przez `scout_search.py` do wyszukiwania repozytoriów.

## Command

```bash
gh search repos <keyword> --sort stars --limit <n> --language <lang> \
  --json name,owner,stargazersCount,forksCount,description,language,updatedAt,url,license
```

## Parameters

| Parameter    | Typ    | Wartość          | Opis                                    |
| ------------ | ------ | ---------------- | --------------------------------------- |
| `keyword`    | string | z `GAP_KEYWORDS` | Słowa kluczowe do wyszukiwania          |
| `--sort`     | enum   | `stars`          | Sortowanie po popularności              |
| `--limit`    | int    | 5                | Max wyników per keyword                 |
| `--language` | string | optional         | Filtr języka (Python, TypeScript, etc.) |
| `--json`     | flag   | —                | Output w formacie JSON                  |

## Fields (JSON output)

| Field             | Typ    | Opis              | Używane w                |
| ----------------- | ------ | ----------------- | ------------------------ |
| `name`            | string | Nazwa repo        | `repo`, URL              |
| `owner`           | object | `{login: string}` | `repo`, URL              |
| `stargazersCount` | int    | Liczba gwiazdek   | `scorecard` (stars)      |
| `forksCount`      | int    | Liczba forków     | `scorecard` (forks)      |
| `description`     | string | Opis              | `relevance`, `scorecard` |
| `language`        | object | `{name: string}`  | Output language          |
| `updatedAt`       | string | ISO 8601          | `scorecard` (recency)    |
| `url`             | string | GitHub URL        | Output URL               |
| `license`         | object | `{name: string}`  | `scorecard` (license)    |

## Przykładowe wyjście

```json
[
  {
    "name": "pytest",
    "owner": { "login": "pytest-dev" },
    "stargazersCount": 12000,
    "forksCount": 800,
    "description": "pytest: simple powerful testing with Python",
    "language": { "name": "Python" },
    "updatedAt": "2024-01-15T10:00:00Z",
    "url": "https://github.com/pytest-dev/pytest",
    "license": { "name": "MIT License" }
  }
]
```

## Przykładowe zapytanie

```bash
gh search repos "pytest" --sort stars --limit 5 --language Python \
  --json name,owner,stargazersCount,forksCount,description,language,updatedAt,url,license
```

## Obsługa błędów

```python
try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"⚠️ gh search failed: {result.stderr}", file=sys.stderr)
        return []
    repos = json.loads(result.stdout)
    return repos
except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
    print(f"⚠️ Search error: {e}", file=sys.stderr)
    return []
```

| Error              | Reakcja                           |
| ------------------ | --------------------------------- |
| `returncode != 0`  | Pusty wynik, log stderr           |
| `TimeoutExpired`   | Pusty wynik, log error            |
| `JSONDecodeError`  | Pusty wynik, log error            |
| `gh not installed` | ❌ Fatal error, exit with message |

## Rate Limiting

- `gh search repos` ma limit: **10 requests per minute** (unauthenticated)
- Autentykacja: `gh auth login` (zwiększa limit)
- Timeout: 30 sekund per zapytanie
- Brak retry logic — jedna próba, fail fast

## Wymagania

- **GitHub CLI (gh)** zainstalowany
- **Autentykacja** (opcjonalna, ale zalecana)
- **Internet access** (gh wykonuje requesty do GitHub API)

## Instalacja gh CLI

```bash
# Windows
winget install GitHub.cli

# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo apt install gh
```

## Autentykacja

```bash
gh auth login
# Web browser flow lub token
```

## Ograniczenia

- **GitHub only** — brak supportu dla GitLab, Bitbucket, SourceForge
- **Public repos only** — private repos wymagają autentykacji
- **10 req/min** — bez auth, może blokować przy wielu lukach
- **30s timeout** — długie zapytania mogą failować
- **Brak caching** — każde uruchomienie = nowe zapytania

## Alternatywy (przyszłość)

| API                 | Zalety                   | Wady                      |
| ------------------- | ------------------------ | ------------------------- |
| **GitHub REST API** | Więcej fields, paginacja | Wymaga tokena, rate limit |
| **GitHub GraphQL**  | Dokładna selekcja fields | Skomplikowane             |
| **GitLab API**      | GitLab repos             | Inny format               |
| **npm registry**    | JS packages              | Tylko JS                  |
| **PyPI API**        | Python packages          | Tylko Python              |
| **Local index**     | Szybkie, offline         | Wymaga budowania          |

## Rozszerzalność

Aby dodać nowe źródło:

1. Dodaj funkcję `search_<source>()` do `scout_search.py`
2. Dodaj fallback chain: `search_github() -> search_gitlab() -> search_local()`
3. Uaktualnij ten dokument

---

_Wygenerowane z `scout_search.py::search_github()`_
