#!/usr/bin/env python3
"""
lancedb_upsert.py — LanceDB helper dla IAS.

Upsertuje embeddingi narzędzi do LanceDB (localhost:6542).
Generuje embeddingi przez LMStudio (text-embedding-mxbai-embed-large-v1).
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional

# Konfiguracja z Vaults/3Pillars
ENVY_PATH = Path(__file__).parent.parent / "backend" / ".envy"

# Domyślne wartości (fallback — nadpisywane przez .envy lub zmienne środowiskowe)
DEFAULT_LMSTUDIO_URL = "http://localhost:1234/v1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-mxbai-embed-large-v1"
DEFAULT_API_KEY = os.environ.get("LMSTUDIO_API_KEY", "")


def parse_envy(path: Path) -> Dict[str, str]:
    """Parsuje prosty .envy (INI-like) do dict."""
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
    """Zwraca konfigurację LMStudio z .envy lub defaulty."""
    envy = parse_envy(ENVY_PATH)
    return {
        "url": envy.get("ai_providers.lmstudio_api_url", DEFAULT_LMSTUDIO_URL),
        "embedding_model": envy.get(
            "ai_providers.embedding_model", DEFAULT_EMBEDDING_MODEL
        ),
        "api_key": DEFAULT_API_KEY,
    }


def generate_embedding(text: str, config: Dict[str, str]) -> List[float]:
    """Generuje embedding przez LMStudio /embeddings endpoint."""
    url = f"{config['url'].rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["embedding_model"],
        "input": text,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


def connect_lancedb() -> "lancedb.DBConnection":
    """Łączy się z LanceDB (fallback: in-process → remote)."""
    import lancedb

    envy = parse_envy(ENVY_PATH)
    vector_dir = envy.get("storage.vector_store_dir", "./lancedb-store")
    port = int(envy.get("external_dependencies.lancedb_port", "6542"))

    # Spróbuj remote (table server)
    try:
        return lancedb.connect(f"http://localhost:{port}")
    except Exception:
        pass

    # Fallback: in-process (lokalny katalog)
    return lancedb.connect(str(Path(vector_dir).resolve()))


def get_or_create_table(db: "lancedb.DBConnection", table_name: str = "tool_registry"):
    """Pobiera lub tworzy tabelę tool_registry ze schematem."""
    import lancedb
    import pyarrow as pa

    schema = pa.schema(
        [
            pa.field("tool_id", pa.string()),
            pa.field("name", pa.string()),
            pa.field("version", pa.string()),
            pa.field("type", pa.string()),
            pa.field("domain", pa.string()),
            pa.field("priority", pa.string()),
            pa.field("status", pa.string()),
            pa.field("location", pa.string()),
            pa.field("run_command", pa.string()),
            pa.field("update_command", pa.string()),
            pa.field("description", pa.string()),
            pa.field(
                "embedding", pa.list_(pa.float32(), 1024)
            ),  # mxbai-embed-large = 1024 dims
        ]
    )

    if table_name in db.table_names():
        return db.open_table(table_name)
    return db.create_table(table_name, schema=schema)


def upsert_tool(tool_data: Dict, table_name: str = "tool_registry") -> bool:
    """
    Upsert pojedynczego narzędzia do LanceDB.

    tool_data wymagane klucze: tool_id, name, version, type, domain, priority,
    status, location, run_command, update_command, description
    """
    try:
        config = get_lmstudio_config()
        db = connect_lancedb()
        table = get_or_create_table(db, table_name)

        # Generuj embedding z opisu + nazwy
        text_for_embedding = f"{tool_data['name']}: {tool_data['description']}"
        embedding = generate_embedding(text_for_embedding, config)

        # Przygotuj rekord
        record = {**tool_data, "embedding": embedding}

        # Upsert (delete + insert - LanceDB nie ma natywnego upsert)
        try:
            table.delete(f"tool_id = '{tool_data['tool_id']}'")
        except Exception:
            pass
        table.add([record])
        return True
    except Exception as e:
        print(f"❌ LanceDB upsert error: {e}", file=sys.stderr)
        return False


def search_tools(
    query: str, limit: int = 10, table_name: str = "tool_registry"
) -> List[Dict]:
    """Semantic search narzędzi."""
    try:
        config = get_lmstudio_config()
        db = connect_lancedb()
        if table_name not in db.table_names():
            return []
        table = db.open_table(table_name)
        query_embedding = generate_embedding(query, config)
        results = table.search(query_embedding).limit(limit).to_list()
        return results
    except Exception as e:
        print(f"❌ LanceDB search error: {e}", file=sys.stderr)
        return []


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LanceDB upsert/search dla IAS")
    parser.add_argument("--upsert", type=str, help="Ścieżka do JSON z danymi narzędzia")
    parser.add_argument("--search", type=str, help="Zapytanie semantic search")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--table", type=str, default="tool_registry")
    args = parser.parse_args()

    if args.upsert:
        with open(args.upsert, encoding="utf-8") as f:
            tool_data = json.load(f)
        ok = upsert_tool(tool_data, args.table)
        print("✅ Upsert OK" if ok else "❌ Upsert failed")
    elif args.search:
        results = search_tools(args.search, args.limit, args.table)
        for r in results:
            print(f"  {r['tool_id']} ({r['domain']}) - {r['description'][:80]}...")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
