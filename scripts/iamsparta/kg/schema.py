"""
IAmSparta L1: Knowledge Graph — Schema.

Typy węzłów i krawędzi dla grafu narzędzi środowiska developerskiego.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# --- Enums ---


class Domain(Enum):
    VISUAL = "visual"
    CODE_ANALYSIS = "code-analysis"
    DATA = "data"
    DEV = "dev"
    DEVOPS = "devops"
    AI = "ai"
    VIDEO = "video"
    TESTING = "testing"
    SECURITY = "security"
    OTHER = "other"

    @classmethod
    def from_str(cls, s: str) -> Domain:
        for d in cls:
            if d.value == s:
                return d
        return cls.OTHER


class Priority(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class Status(Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    DEPRECATED = "deprecated"


class ToolType(Enum):
    CLI = "cli"
    PYTHON = "python"
    PLUGIN = "plugin"
    JAR = "jar"
    PYTHON_NOTEBOOK = "python-notebook"
    REPO = "repo"
    UNKNOWN = "unknown"


class RelationshipType(Enum):
    """Typy relacji między węzłami."""

    ALTERNATIVE = "alternative"  # może zastąpić w tej samej kategorii
    DEPENDS_ON = "depends_on"  # wymaga innego narzędzia
    REPLACES = "replaces"  # nowsze zastępuje starsze
    REPLACED_BY = "replaced_by"  # zostało zastąpione
    OVERLAPS_WITH = "overlaps_with"  # częściowo się pokrywa
    INCOMPATIBLE_WITH = "incompatible_with"
    COMPLEMENTARY = "complementary"  # dobrze się uzupełnia
    DEPLOYED_ON = "deployed_on"  # warstwa infrastruktury
    USES = "uses"  # używa innego narzędzia


# --- Węzły ---


@dataclass
class ToolNode:
    """Węzeł reprezentujący narzędzie w ekosystemie."""

    id: str  # unique identifier (np. "Mermaid-CLI")
    name: str
    version: str
    tool_type: ToolType
    domain: Domain
    priority: Priority
    status: Status
    description: str
    location: Optional[str] = None
    run_command: Optional[str] = None
    update_command: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    arch_deprecated_at: Optional[str] = None
    arch_deprecation_reason: Optional[str] = None

    def is_active(self) -> bool:
        """True jeśli narzędzie jest aktywne."""
        return self.status == Status.ACTIVE

    def is_deprecated(self) -> bool:
        """True jeśli narzędzie jest zdeprecjonowane."""
        return self.status == Status.DEPRECATED

    def to_dict(self) -> dict:
        """Serializacja do słownika."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "tool_type": self.tool_type.value
            if isinstance(self.tool_type, ToolType)
            else self.tool_type,
            "domain": self.domain.value
            if isinstance(self.domain, Domain)
            else self.domain,
            "priority": self.priority.value
            if isinstance(self.priority, Priority)
            else self.priority,
            "status": self.status.value
            if isinstance(self.status, Status)
            else self.status,
            "description": self.description,
            "location": self.location,
            "tags": self.tags,
        }


@dataclass
class CapabilityNode:
    """Węzeł reprezentujący zdolność/funkcję."""

    id: str
    name: str
    description: str
    category: str  # np. "diagram-rendering", "code-search"
    tags: List[str] = field(default_factory=list)


@dataclass
class DomainNode:
    """Węzeł reprezentujący domenę."""

    id: str
    name: str
    description: str = ""


# --- Krawędzie ---


@dataclass
class Relationship:
    """Krawędź w grafie."""

    source_id: str
    target_id: str
    rel_type: RelationshipType
    weight: float = 1.0  # 0.0 = weak, 1.0 = strong
    metadata: dict = field(default_factory=dict)

    def reverse(self) -> Relationship:
        """Zwraca odwróconą relację."""
        rev_map = {
            RelationshipType.ALTERNATIVE: RelationshipType.ALTERNATIVE,
            RelationshipType.DEPENDS_ON: RelationshipType.DEPENDS_ON,
            RelationshipType.OVERLAPS_WITH: RelationshipType.OVERLAPS_WITH,
            RelationshipType.COMPLEMENTARY: RelationshipType.COMPLEMENTARY,
            RelationshipType.REPLACED_BY: RelationshipType.REPLACES,
            RelationshipType.REPLACES: RelationshipType.REPLACED_BY,
        }
        return Relationship(
            source_id=self.target_id,
            target_id=self.source_id,
            rel_type=rev_map.get(self.rel_type, self.rel_type),
            weight=self.weight,
        )


# --- Stan grafu ---


@dataclass
class KnowledgeGraphState:
    """Zserializowany stan całego grafu."""

    nodes: dict  # node_id → ToolNode | CapabilityNode | DomainNode
    relationships: List[Relationship]
    built_at: str = ""
    source_files: List[str] = field(default_factory=list)
