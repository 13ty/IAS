#!/usr/bin/env python3
"""
init_project.py — Bootstrap IAS project structure.

Creates required directories and default files that are excluded from
version control (.gitignore). Run once after cloning the repo.

Usage:
    python scripts/init_project.py
"""

import json
import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_data_structure():
    """Create data/ directory with empty defaults."""
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Empty tool registry template
    registry_file = data_dir / "tool_registry.json"
    if not registry_file.exists():
        registry_file.write_text(
            json.dumps(
                {
                    "version": "2.0.0",
                    "last_updated": "not initialized",
                    "tools": {},
                    "domains": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  + {registry_file.relative_to(PROJECT_ROOT)}")

    # Empty taxonomy mapping
    taxonomy_file = data_dir / "taxonomy_mapping.json"
    if not taxonomy_file.exists():
        taxonomy_file.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "last_updated": "not initialized",
                    "mappings": {},
                    "axes": {
                        "layer": "A0-A8: Physical Storage → Application",
                        "function": "B0-B6: Ingest → Visualization",
                        "domain": "C0-C9: System/Infra → AI/ML",
                        "pattern": "D0-D12: CLI → Notebook",
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  + {taxonomy_file.relative_to(PROJECT_ROOT)}")

    # Empty proposals CSV with headers
    proposals_file = data_dir / "proposals.csv"
    if not proposals_file.exists():
        proposals_file.write_text(
            "timestamp,url,source,type,notes,status\n", encoding="utf-8"
        )
        print(f"  + {proposals_file.relative_to(PROJECT_ROOT)}")

    # audits/ directory (empty)
    audits_dir = data_dir / "audits"
    audits_dir.mkdir(exist_ok=True)
    print(f"  + {audits_dir.relative_to(PROJECT_ROOT)}/")

    # repo-cards/ directory (empty)
    repo_cards_dir = data_dir / "repo-cards"
    repo_cards_dir.mkdir(exist_ok=True)
    print(f"  + {repo_cards_dir.relative_to(PROJECT_ROOT)}/")

    return data_dir


def create_state_structure():
    """Create state/ directory with schema."""
    state_dir = PROJECT_ROOT / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Copy schema.json from references if it exists there, or create default
    schema_file = state_dir / "schema.json"
    if not schema_file.exists():
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "IAS Tech Stack Oracle State",
            "description": "Shared state file for IAS plugin ecosystem",
            "type": "object",
            "required": ["version", "lastUpdated", "currentPhase"],
            "properties": {
                "version": {
                    "type": "string",
                    "description": "Schema version",
                    "const": "1.0.0",
                },
                "lastUpdated": {
                    "type": "string",
                    "format": "date-time",
                    "description": "ISO 8601 timestamp",
                },
                "currentPhase": {
                    "type": "string",
                    "enum": ["IDLE", "INVENTORY", "ANALYZER", "SCOUT", "COMPLETE"],
                    "description": "Current pipeline phase",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Path to analyzed project",
                },
                "inventory": {
                    "type": "object",
                    "description": "Inventory scan results",
                },
                "analysis": {"type": "object", "description": "Analysis results"},
                "scout": {"type": "object", "description": "Scout results"},
                "decisions": {"type": "array", "description": "Pipeline decisions"},
                "history": {"type": "array", "description": "Pipeline run history"},
            },
        }
        schema_file.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(f"  + {schema_file.relative_to(PROJECT_ROOT)}")

    return state_dir


def create_envy_template():
    """Create backend/.envy template with placeholders."""
    envy_file = PROJECT_ROOT / "backend" / ".envy"
    backend_dir = PROJECT_ROOT / "backend"
    backend_dir.mkdir(parents=True, exist_ok=True)

    if not envy_file.exists():
        envy_file.write_text(
            "# IAS - Machine Configuration\n"
            "# Copy this template and fill in your paths.\n"
            "# This file is in .gitignore — it will NOT be committed.\n"
            "\n"
            "_meta:\n"
            "  machine: YOUR_PC_NAME\n"
            "  os: win32\n"
            "  generated: 2026-01-01\n"
            "\n"
            "runtime:\n"
            "  python: python\n"
            "  gh: gh\n"
            "\n"
            "paths:\n"
            "  ias_root: C:\\Users\\YOU\\.config\\opencode\\plugins\\IAS\n"
            "  vaults: C:\\Users\\YOU\\.config\\opencode\\Vaults\n"
            "  opencode_config: C:\\Users\\YOU\\.config\\opencode\n"
            "\n"
            "services:\n"
            "  lmstudio: http://localhost:1234\n"
            "\n"
            "ai_providers:\n"
            "  lmstudio_api_url: http://localhost:1234/v1\n"
            "  embedding_model: text-embedding-mxbai-embed-large-v1\n",
            encoding="utf-8",
        )
        print(f"  + {envy_file.relative_to(PROJECT_ROOT)}")
    return envy_file


def create_logs_dir():
    """Create logs/ directory."""
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    print(f"  + {logs_dir.relative_to(PROJECT_ROOT)}/")


def main():
    print("IAS — Initializing project structure\n")

    print("[data/]")
    create_data_structure()

    print("\n[state/]")
    create_state_structure()

    print("\n[backend/]")
    create_envy_template()

    print("\n[logs/]")
    create_logs_dir()

    print("\n--- Done ---")
    print("Next steps:")
    print("  1. Edit backend/.envy with your machine paths")
    print("  2. Create a Python venv: python -m venv .venv")
    print("  3. Install deps: pip install pyyaml mcp")


if __name__ == "__main__":
    main()
