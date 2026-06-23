"""
Template Rendering Engine for IAS Pipeline.

Uses Mustache (via pystache) for template rendering.
All templates in templates/ directory.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import pystache


class TemplateRenderer:
    """Renders Mustache templates with provided context."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self._cache: Dict[str, pystache.Template] = {}

    def _load_template(self, name: str) -> pystache.Template:
        """Load and compile template (cached)."""
        if name not in self._cache:
            template_path = self.templates_dir / f"{name}.mustache"
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            with open(template_path, "r", encoding="utf-8") as f:
                self._cache[name] = pystache.parse(f.read())
        return self._cache[name]

    def render(self, name: str, context: Dict[str, Any]) -> str:
        """Render template with context."""
        template = self._load_template(name)
        renderer = pystache.Renderer()
        return renderer.render(template, context)

    def render_to_file(
        self, name: str, context: Dict[str, Any], output_path: Path
    ) -> None:
        """Render template and write to file."""
        output = self.render(name, context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)


def load_context_from_json(json_path: Path) -> Dict[str, Any]:
    """Load rendering context from JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_context_to_json(context: Dict[str, Any], json_path: Path) -> None:
    """Save rendering context to JSON file."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)


# Default context builders
def build_repo_context(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build context for repo_card template from repo data."""
    from datetime import datetime

    now = datetime.now().isoformat()

    context = {
        "repo_id": repo_data.get("repo_id", ""),
        "repo_name": repo_data.get("name", repo_data.get("repo_name", "")),
        "repo_url": repo_data.get("url", repo_data.get("repo_url", "")),
        "project_type": repo_data.get("type", repo_data.get("project_type", "unknown")),
        "category": repo_data.get("category", "uncategorized"),
        "status": repo_data.get("status", "pending"),
        "created_at": repo_data.get("created_at", now),
        "updated_at": now,
        "description": repo_data.get("description", ""),
        "stars": repo_data.get("stars", 0),
        "forks": repo_data.get("forks", 0),
        "watchers": repo_data.get("watchers", 0),
        "open_issues": repo_data.get("open_issues", 0),
        "license": repo_data.get("license", "Unknown"),
        "language": repo_data.get("language", "Unknown"),
        "size_kb": repo_data.get("size_kb", 0),
        "topics": repo_data.get("topics", []),
        "scoring": repo_data.get("scoring", {}),
        "verdict": repo_data.get("verdict", "NOT_EVALUATED"),
        "adoption_probability": repo_data.get("adoption_probability", "unknown"),
        "capabilities": repo_data.get("capabilities", []),
        "serendipity_potential": repo_data.get("serendipity_potential", "none"),
        "serendipity_notes": repo_data.get("serendipity_notes", ""),
        "pipeline_version": "1.0.0",
        "timestamp": now,
    }

    # Normalize topics for template
    if isinstance(context["topics"], str):
        context["topics"] = [
            t.strip() for t in context["topics"].split(",") if t.strip()
        ]

    return context


def build_capability_context(
    repo_data: Dict[str, Any], mcp_memory_path: str
) -> Dict[str, Any]:
    """Build context for capability_map template."""
    from datetime import datetime
    from collections import defaultdict

    now = datetime.now().isoformat()
    capabilities = repo_data.get("capabilities", [])

    # Group by category
    categories = defaultdict(list)
    for cap in capabilities:
        categories[cap.get("category", "other")].append(cap)

    category_list = [
        {"category": cat, "count": len(items), "items": items}
        for cat, items in categories.items()
    ]

    return {
        "repo_id": repo_data.get("repo_id", ""),
        "repo_name": repo_data.get("name", repo_data.get("repo_name", "")),
        "analysis_date": now,
        "capability_map_version": repo_data.get("capability_map_version", "1.0"),
        "capabilities": capabilities,
        "categories": category_list,
        "missing_capabilities": repo_data.get("missing_capabilities", []),
        "mcp_memory_path": mcp_memory_path,
    }


def build_investigation_context(
    repo_data: Dict[str, Any], analyst: str = "pipeline"
) -> Dict[str, Any]:
    """Build context for investigation_log template."""
    from datetime import datetime

    now = datetime.now().isoformat()

    return {
        "repo_id": repo_data.get("repo_id", ""),
        "repo_name": repo_data.get("name", repo_data.get("repo_name", "")),
        "started_at": now,
        "analyst": analyst,
        "investigation_goal": repo_data.get(
            "investigation_goal", "Automated evaluation via pipeline"
        ),
        "structure_findings": repo_data.get("structure_findings", []),
        "semantic_findings": repo_data.get("semantic_findings", []),
        "capability_findings": repo_data.get("capability_findings", []),
        "surprises": repo_data.get("surprises", []),
        "agent_judgments": repo_data.get("agent_judgments", []),
        "conclusions": repo_data.get("conclusions", "Pending agent review"),
        "recommendations": repo_data.get("recommendations", []),
    }


def build_timeline_context(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build context for timeline template."""
    from datetime import datetime

    now = datetime.now().isoformat()
    events = repo_data.get("timeline_events", [])

    # Add current event if not present
    if not events or events[0].get("timestamp") != now:
        events.insert(
            0,
            {
                "timestamp": now,
                "event_type": "PIPELINE_RUN",
                "details": [
                    "Pipeline executed",
                    f"Version: {repo_data.get('pipeline_version', '1.0.0')}",
                ],
                "capability_map_version": repo_data.get(
                    "capability_map_version", "1.0"
                ),
                "verdict": repo_data.get("verdict", "PENDING"),
                "agent": "pipeline",
            },
        )

    return {
        "repo_id": repo_data.get("repo_id", ""),
        "repo_name": repo_data.get("name", repo_data.get("repo_name", "")),
        "last_updated": now,
        "events": events,
    }
