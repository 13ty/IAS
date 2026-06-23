#!/usr/bin/env python3
"""
repo_utils.py — Kwatermistrz: Współdzielone narzędzia do zarządzania repozytoriami.

Moduł fundament dla systemu oceny repozytoriów v2.
Obsługuje: walidację URL, deduplikację, queue/knowledge I/O, capability taxonomy.

Użycie (przez inne skrypty):
    from repo_utils import add_to_queue, validate_github_url, ...
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

# --- Ścieżki ---
IAS_ROOT = os.path.dirname(os.path.dirname(__file__))
STATE_DIR = os.path.join(IAS_ROOT, "state")
REPOS_DIR = os.path.join(STATE_DIR, "repos")

QUEUE_PATH = os.path.join(STATE_DIR, "repo_queue.json")
KNOWLEDGE_PATH = os.path.join(STATE_DIR, "repo_knowledge.json")
TAXONOMY_PATH = os.path.join(STATE_DIR, "capability_taxonomy.json")
SCORING_PATH = os.path.join(STATE_DIR, "scoring_criteria.json")

# --- Walidacja i normalizacja URL-i ---

GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/?$"
)


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Parsuje URL GitHub, zwraca (owner, repo) lub None."""
    url = url.strip().rstrip("/")
    match = GITHUB_URL_PATTERN.match(url)
    if match:
        return match.group(1), match.group(2)
    return None


def normalize_github_url(url: str) -> str | None:
    """Normalizuje URL GitHub, zwraca kanoniczną formę lub None."""
    parsed = parse_github_url(url)
    if not parsed:
        return None
    owner, repo = parsed
    return f"https://github.com/{owner}/{repo}"


def validate_github_url(url: str) -> tuple[bool, str | None]:
    """Waliduje URL GitHub. Zwraca (is_valid, error_message)."""
    url = url.strip()
    if not url:
        return False, "URL is empty"
    if "github.com" not in url:
        return False, "Only GitHub URLs are supported"
    normalized = normalize_github_url(url)
    if not normalized:
        return (
            False,
            "Invalid GitHub URL format. Expected: https://github.com/owner/repo",
        )
    return True, normalized


# --- UUID ---
def generate_repo_id() -> str:
    """Generuje UUID v4 dla repozytorium."""
    return str(uuid.uuid4())


# --- Queue I/O (state/repo_queue.json) ---


def load_queue() -> dict:
    """Wczytuje kolejkę URL-i do oceny."""
    if not os.path.exists(QUEUE_PATH):
        return {"version": "1.0.0", "items": [], "last_updated": _now()}
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue: dict) -> None:
    """Zapisuje kolejkę URL-i."""
    queue["last_updated"] = _now()
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def is_url_in_queue(url: str) -> bool:
    """Sprawdza czy URL już istnieje w kolejce (dedup)."""
    normalized = normalize_github_url(url)
    if not normalized:
        return False
    queue = load_queue()
    for item in queue["items"]:
        if normalize_github_url(item["url"]) == normalized:
            return True
    return False


def add_to_queue(
    url: str,
    source: str = "user",
    priority: str = "medium",
    gap_category: str | None = None,
    notes: str = "",
) -> dict | None:
    """Dodaje URL do kolejki. Zwraca wpis lub None jeśli URL nieprawidłowy/duplikat."""
    is_valid, result = validate_github_url(url)
    if not is_valid:
        print(f"❌ {result}")
        return None

    normalized_url = result  # type: ignore

    # Dedup: sprawdź queue + knowledge
    if is_url_in_queue(normalized_url):
        print(f"⚠️  URL już istnieje w kolejce: {normalized_url}")
        return None

    if is_url_in_knowledge(normalized_url):
        print(f"⚠️  URL już oceniony (repo_knowledge): {normalized_url}")
        return None

    entry = {
        "id": generate_repo_id(),
        "url": normalized_url,
        "source": source,
        "discovered_at": _now(),
        "status": "pending",
        "priority": priority,
        "notes": notes,
    }
    if gap_category:
        entry["gap_category"] = gap_category

    queue = load_queue()
    queue["items"].append(entry)
    save_queue(queue)

    print(f"✅ Dodano do kolejki: {normalized_url} (id: {entry['id']})")
    return entry


def remove_from_queue(url_or_id: str) -> bool:
    """Usuwa wpis z kolejki po URL lub ID."""
    queue = load_queue()
    normalized = normalize_github_url(url_or_id)
    before = len(queue["items"])
    queue["items"] = [
        item
        for item in queue["items"]
        if not (
            item["id"] == url_or_id
            or (normalized and normalize_github_url(item["url"]) == normalized)
        )
    ]
    if len(queue["items"]) < before:
        save_queue(queue)
        print(f"✅ Usunięto z kolejki: {url_or_id}")
        return True
    print(f"⚠️  Nie znaleziono w kolejce: {url_or_id}")
    return False


def list_queue(status: str | None = None) -> list[dict]:
    """Zwraca wpisy z kolejki, opcjonalnie filtrowane po statusie."""
    queue = load_queue()
    items = queue["items"]
    if status:
        items = [item for item in items if item["status"] == status]
    return items


# --- Knowledge I/O (state/repo_knowledge.json) ---


def load_knowledge() -> dict:
    """Wczytuje indeks ocenionych repozytoriów."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return {"version": "1.0.0", "repositories": [], "last_updated": _now()}
    with open(KNOWLEDGE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_knowledge(knowledge: dict) -> None:
    """Zapisuje indeks ocenionych repozytoriów."""
    knowledge["last_updated"] = _now()
    with open(KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, indent=2, ensure_ascii=False)


def is_url_in_knowledge(url: str) -> bool:
    """Sprawdza czy URL jest już w indeksie ocenionych."""
    normalized = normalize_github_url(url)
    if not normalized:
        return False
    knowledge = load_knowledge()
    for repo in knowledge["repositories"]:
        if normalize_github_url(repo["url"]) == normalized:
            return True
    return False


def add_to_knowledge_index(repo_entry: dict) -> None:
    """Dodaje wpis do indeksu repo_knowledge.json (po ocenie)."""
    knowledge = load_knowledge()
    # Dedup
    for i, existing in enumerate(knowledge["repositories"]):
        if existing["id"] == repo_entry["id"]:
            knowledge["repositories"][i] = repo_entry
            save_knowledge(knowledge)
            return
    knowledge["repositories"].append(repo_entry)
    save_knowledge(knowledge)


# --- Repo Card I/O (state/repos/{repo_id}/repo_card.json) ---


def ensure_repo_dir(repo_id: str) -> str:
    """Tworzy katalog dla repo jeśli nie istnieje. Zwraca ścieżkę."""
    path = os.path.join(REPOS_DIR, repo_id)
    os.makedirs(path, exist_ok=True)
    return path


def save_repo_card(card: dict) -> str:
    """Zapisuje repo_card.json do state/repos/{repo_id}/."""
    repo_id = card["id"]
    repo_dir = ensure_repo_dir(repo_id)
    path = os.path.join(repo_dir, "repo_card.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
    return path


def load_repo_card(repo_id: str) -> dict | None:
    """Wczytuje repo_card.json dla danego repo."""
    path = os.path.join(REPOS_DIR, repo_id, "repo_card.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_timeline(timeline: dict) -> str:
    """Zapisuje timeline.json do state/repos/{repo_id}/."""
    repo_id = timeline["repo_id"]
    repo_dir = ensure_repo_dir(repo_id)
    path = os.path.join(repo_dir, "timeline.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)
    return path


def save_capability_map(cap_map: dict) -> str:
    """Zapisuje capability_map.json do state/repos/{repo_id}/."""
    repo_id = cap_map["repo_id"]
    repo_dir = ensure_repo_dir(repo_id)
    path = os.path.join(repo_dir, "capability_map.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cap_map, f, indent=2, ensure_ascii=False)
    return path


# --- Taxonomy / Scoring loaders ---


def load_taxonomy() -> dict | None:
    """Wczytuje capability_taxonomy.json."""
    if not os.path.exists(TAXONOMY_PATH):
        print("⚠️  capability_taxonomy.json not found")
        return None
    with open(TAXONOMY_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_scoring_criteria() -> dict | None:
    """Wczytuje scoring_criteria.json."""
    if not os.path.exists(SCORING_PATH):
        print("⚠️  scoring_criteria.json not found")
        return None
    with open(SCORING_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_capability_id(name: str) -> str | None:
    """Znajduje capability_id po nazwie (fuzzy)."""
    taxonomy = load_taxonomy()
    if not taxonomy:
        return None
    name_lower = name.lower().strip()
    for domain in taxonomy.get("domains", []):
        for cap in domain.get("capabilities", []):
            if cap["name"].lower() == name_lower or cap["id"] == name_lower:
                return cap["id"]
    return None


def list_capability_ids() -> list[str]:
    """Zwraca wszystkie dostępne capability ID z taksonomii."""
    taxonomy = load_taxonomy()
    if not taxonomy:
        return []
    ids = []
    for domain in taxonomy.get("domains", []):
        for cap in domain.get("capabilities", []):
            ids.append(cap["id"])
    return ids


# --- Pomocnicze ---


def _now() -> str:
    """Zwraca bieżący timestamp ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def compute_verdict(overall_score: float) -> str:
    """Określa verdict na podstawie overall_score zgodnie ze scoring_criteria."""
    # Wbudowane progi — można nadpisać ładując scoring_criteria.json
    if overall_score >= 7.0:
        return "ADOPT"
    elif overall_score >= 4.5:
        return "PILOT"
    elif overall_score >= 2.0:
        return "LEARN"
    return "NOT_NOW"


def queue_stats() -> dict:
    """Statystyki kolejki: liczba per status."""
    queue = load_queue()
    stats = {"total": len(queue["items"])}
    for item in queue["items"]:
        s = item["status"]
        stats[s] = stats.get(s, 0) + 1
    return stats


def knowledge_stats() -> dict:
    """Statystyki wiedzy: liczba per verdict."""
    knowledge = load_knowledge()
    stats = {"total": len(knowledge["repositories"])}
    for repo in knowledge["repositories"]:
        v = repo.get("verdict", "unknown")
        stats[v] = stats.get(v, 0) + 1
    return stats
