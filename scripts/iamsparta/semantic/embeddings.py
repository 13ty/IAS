"""
IAmSparta L2: Semantic Layer — Capability Embeddings.

Generuje embeddingi dla narzędzi i capability description przez LMStudio API.
Zapisuje do LanceDB dla semantic search.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Ścieżki
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENVY_PATH = PLUGIN_ROOT / "backend" / ".envy"

# Domyślne
DEFAULT_LMSTUDIO_URL = "http://localhost:1234/v1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-mxbai-embed-large-v1"
DEFAULT_API_KEY = os.environ.get("LMSTUDIO_API_KEY", "")


def _parse_envy(path: Path) -> Dict[str, str]:
    """Parsuje .envy (INI-like) do dict."""
    config = {}
    current_section = ""
    if not path.exists():
        return config
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].lower()
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            config[f"{current_section}.{key.strip().lower()}"] = val.strip()
    return config


def get_lmstudio_config() -> Dict[str, str]:
    envy = _parse_envy(ENVY_PATH)
    return {
        "url": envy.get("ai_providers.lmstudio_api_url", DEFAULT_LMSTUDIO_URL),
        "embedding_model": envy.get(
            "ai_providers.embedding_model", DEFAULT_EMBEDDING_MODEL
        ),
        "api_key": DEFAULT_API_KEY,
    }


def generate_embedding(
    text: str, config: Optional[Dict[str, str]] = None
) -> List[float]:
    """Generuje embedding przez LMStudio /embeddings endpoint."""
    cfg = config or get_lmstudio_config()
    url = f"{cfg['url'].rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg["embedding_model"],
        "input": text,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


def generate_capability_embedding(
    tool_name: str,
    description: str,
    domain: str,
    config: Optional[Dict[str, str]] = None,
) -> List[float]:
    """Generuje embedding dla capability narzędzia."""
    text = f"Tool: {tool_name}\nDomain: {domain}\nDescription: {description}"
    return generate_embedding(text, config)


def generate_query_embedding(query: str) -> List[float]:
    """Generuje embedding dla zapytania."""
    return generate_embedding(query)


# --- LanceDB operations ---


def connect_lancedb() -> Any:
    """Łączy się z LanceDB (remote → in-process fallback)."""
    import lancedb

    envy = _parse_envy(ENVY_PATH)
    port = int(envy.get("external_dependencies.lancedb_port", "6542"))

    try:
        return lancedb.connect(f"http://localhost:{port}")
    except Exception:
        pass

    vector_dir = envy.get("storage.vector_store_dir", "./lancedb-store")
    return lancedb.connect(str(Path(vector_dir).resolve()))


def get_or_create_table(db: Any, table_name: str = "iamsparta_capabilities"):
    """Pobiera lub tworzy tabelę capability embeddings."""
    import pyarrow as pa

    schema = pa.schema(
        [
            pa.field("tool_id", pa.string()),
            pa.field("tool_name", pa.string()),
            pa.field("domain", pa.string()),
            pa.field("description", pa.string()),
            pa.field("priority", pa.string()),
            pa.field("status", pa.string()),
            pa.field("embedding", pa.list_(pa.float32(), 1024)),
        ]
    )

    if table_name in db.table_names():
        return db.open_table(table_name)
    return db.create_table(table_name, schema=schema)


def upsert_capability(
    tool_id: str,
    tool_name: str,
    domain: str,
    description: str,
    priority: str = "warm",
    status: str = "active",
) -> bool:
    """Generuje embedding i upsertuje do LanceDB."""
    try:
        config = get_lmstudio_config()
        db = connect_lancedb()
        table = get_or_create_table(db)

        embedding = generate_capability_embedding(
            tool_name, description, domain, config
        )

        record = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "domain": domain,
            "description": description,
            "priority": priority,
            "status": status,
            "embedding": embedding,
        }

        try:
            table.delete(f"tool_id = '{tool_id}'")
        except Exception:
            pass
        table.add([record])
        return True
    except Exception as e:
        print(f"❌ LanceDB upsert error: {e}", file=sys.stderr)
        return False


def batch_upsert(tools_data: List[Dict[str, str]]) -> Dict[str, bool]:
    """Batch upsert wielu narzędzi."""
    results = {}
    for t in tools_data:
        ok = upsert_capability(
            tool_id=t.get("tool_id", t.get("id", "unknown")),
            tool_name=t.get("name", "unknown"),
            domain=t.get("domain", "other"),
            description=t.get("description", ""),
            priority=t.get("priority", "warm"),
            status=t.get("status", "active"),
        )
        results[t.get("tool_id", "unknown")] = ok
    return results
