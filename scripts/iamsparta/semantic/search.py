"""
IAmSparta L2: Semantic Layer — Search API.

Semantic search po capability embeddings w LanceDB.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from .embeddings import (
    connect_lancedb,
    generate_query_embedding,
    get_or_create_table,
)


class SemanticSearch:
    """Semantic search nad capability embeddings."""

    def __init__(self, table_name: str = "iamsparta_capabilities") -> None:
        self._table_name = table_name
        self._db = None
        self._table = None

    def _ensure_connected(self) -> Any:
        if self._table is None:
            self._db = connect_lancedb()
            self._table = get_or_create_table(self._db, self._table_name)
        return self._table

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Semantic search: znajdź narzędzia podobne do zapytania.

        Args:
            query: Opis capability, np. "diagram rendering UML"
            limit: Maksymalna liczba wyników

        Returns:
            Lista narzędzi z score podobieństwa
        """
        table = self._ensure_connected()
        query_embedding = generate_query_embedding(query)
        results = table.search(query_embedding).limit(limit).to_list()
        return results

    def search_by_domain(self, query: str, domain: str, limit: int = 10) -> List[Dict]:
        """Semantic search z filtrem domeny."""
        results = self.search(query, limit=limit * 3)  # więcej dla filtra
        return [r for r in results if r.get("domain") == domain][:limit]

    def find_similar(self, tool_id: str, limit: int = 5) -> List[Dict]:
        """Znajdź narzędzia podobne do danego (po embeddingu)."""
        table = self._ensure_connected()

        # Pobierz embedding istniejącego narzędzia
        try:
            existing = table.search().where(f"tool_id = '{tool_id}'").limit(1).to_list()
        except Exception:
            existing = []

        if not existing:
            return []

        # Użyj embeddingu jako query
        query_embedding = existing[0].get("embedding")
        if not query_embedding:
            return []

        results = table.search(query_embedding).limit(limit + 1).to_list()
        # Usuń siebie z wyników
        return [r for r in results if r.get("tool_id") != tool_id][:limit]

    def count(self) -> int:
        """Liczba zaindeksowanych narzędzi."""
        table = self._ensure_connected()
        return len(table.to_list())

    def list_all(self) -> List[Dict]:
        """Lista wszystkich zaindeksowanych narzędzi."""
        table = self._ensure_connected()
        return table.to_list()


# --- CLI ---


def main():
    import argparse

    parser = argparse.ArgumentParser(description="IAmSparta L2: Semantic Search")
    parser.add_argument("--search", type=str, help="Zapytanie semantic search")
    parser.add_argument("--domain", type=str, help="Filtruj po domenie")
    parser.add_argument("--similar", type=str, help="Znajdź podobne do tool_id")
    parser.add_argument("--count", action="store_true", help="Policz indeksy")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    ss = SemanticSearch()

    if args.search:
        if args.domain:
            results = ss.search_by_domain(args.search, args.domain, args.limit)
        else:
            results = ss.search(args.search, args.limit)
        print(f"🔎 Wyniki dla: '{args.search}'")
        for r in results:
            print(f"  • {r.get('tool_name', '?')} ({r.get('domain', '?')})")
            print(f"    {r.get('description', '')[:100]}")

    elif args.similar:
        results = ss.find_similar(args.similar, args.limit)
        print(f"🔎 Podobne do: '{args.similar}'")
        for r in results:
            print(f"  • {r.get('tool_name', '?')} ({r.get('domain', '?')})")

    elif args.count:
        print(f"📊 Indeksów: {ss.count()}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
