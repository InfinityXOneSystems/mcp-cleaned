"""
Domain Taxonomy — Strategic Seed Domain Classification
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md Article V
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class TaxonomyLevel(Enum):
    """Taxonomy hierarchy levels."""
    ROOT = 0
    DOMAIN = 1
    SUBDOMAIN = 2
    TOPIC = 3
    SUBTOPIC = 4


@dataclass
class TaxonomyNode:
    """Node in the domain taxonomy tree."""
    id: str
    name: str
    level: TaxonomyLevel
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level.value,
            "parent_id": self.parent_id,
            "children": self.children,
            "description": self.description,
            "keywords": self.keywords
        }


# ─────────────────────────────────────────────────────────────────────
# STRATEGIC SEED DOMAINS (from VISION_CORTEX_LAW.md Article V)
# ─────────────────────────────────────────────────────────────────────

STRATEGIC_SEED_DOMAINS = {
    "economics": TaxonomyNode(
        id="economics",
        name="Economics",
        level=TaxonomyLevel.DOMAIN,
        description="Economic systems, markets, finance, monetary policy",
        keywords=["market", "finance", "capital", "trade", "inflation", "gdp"],
        children=["macro", "micro", "monetary", "fiscal", "markets"]
    ),
    "ai": TaxonomyNode(
        id="ai",
        name="Artificial Intelligence",
        level=TaxonomyLevel.DOMAIN,
        description="AI/ML systems, compute, algorithms, AGI",
        keywords=["machine learning", "neural", "llm", "compute", "training"],
        children=["ml", "llm", "compute", "robotics", "agi"]
    ),
    "energy": TaxonomyNode(
        id="energy",
        name="Energy",
        level=TaxonomyLevel.DOMAIN,
        description="Energy production, distribution, storage, transition",
        keywords=["power", "renewable", "grid", "oil", "nuclear", "solar"],
        children=["renewable", "fossil", "nuclear", "storage", "grid"]
    ),
    "governance": TaxonomyNode(
        id="governance",
        name="Governance",
        level=TaxonomyLevel.DOMAIN,
        description="Political systems, policy, regulation, institutions",
        keywords=["policy", "regulation", "government", "law", "institution"],
        children=["political", "regulatory", "institutional", "international"]
    ),
    "philosophy": TaxonomyNode(
        id="philosophy",
        name="Philosophy",
        level=TaxonomyLevel.DOMAIN,
        description="Ethics, epistemology, consciousness, meaning",
        keywords=["ethics", "consciousness", "meaning", "truth", "values"],
        children=["ethics", "epistemology", "consciousness", "metaphysics"]
    ),
    "systems": TaxonomyNode(
        id="systems",
        name="Systems",
        level=TaxonomyLevel.DOMAIN,
        description="Complex systems, emergence, collapse, resilience",
        keywords=["complexity", "emergence", "network", "resilience", "collapse"],
        children=["complexity", "networks", "emergence", "resilience"]
    ),
    "technology": TaxonomyNode(
        id="technology",
        name="Technology",
        level=TaxonomyLevel.DOMAIN,
        description="Technology development, adoption, disruption",
        keywords=["innovation", "disruption", "adoption", "infrastructure"],
        children=["infrastructure", "platforms", "hardware", "software"]
    ),
    "culture": TaxonomyNode(
        id="culture",
        name="Culture",
        level=TaxonomyLevel.DOMAIN,
        description="Social dynamics, human behavior, narratives",
        keywords=["social", "narrative", "behavior", "demographics", "trends"],
        children=["social", "behavioral", "narrative", "demographics"]
    )
}


class DomainTaxonomy:
    """
    Manages the strategic seed domain taxonomy.
    
    Used for:
    - Classifying signals, predictions, debates
    - Cross-domain interference detection
    - Thematic clustering
    """
    
    def __init__(self):
        self.nodes: Dict[str, TaxonomyNode] = STRATEGIC_SEED_DOMAINS.copy()
    
    def get_domain(self, domain_id: str) -> Optional[TaxonomyNode]:
        """Get domain by ID."""
        return self.nodes.get(domain_id)
    
    def get_all_domains(self) -> List[TaxonomyNode]:
        """Get all top-level domains."""
        return [n for n in self.nodes.values() if n.level == TaxonomyLevel.DOMAIN]
    
    def classify(self, text: str) -> List[str]:
        """Classify text into domains based on keywords."""
        text_lower = text.lower()
        matches = []
        
        for node in self.nodes.values():
            for keyword in node.keywords:
                if keyword in text_lower:
                    if node.id not in matches:
                        matches.append(node.id)
                    break
        
        return matches
    
    def get_related_domains(self, domain_id: str) -> List[str]:
        """Get domains that commonly co-occur."""
        # Cross-domain relationships (entanglement)
        relationships = {
            "economics": ["ai", "energy", "governance"],
            "ai": ["economics", "energy", "technology", "philosophy"],
            "energy": ["economics", "technology", "governance"],
            "governance": ["economics", "technology", "culture"],
            "philosophy": ["ai", "culture", "systems"],
            "systems": ["ai", "economics", "technology"],
            "technology": ["ai", "economics", "systems"],
            "culture": ["governance", "philosophy", "technology"]
        }
        return relationships.get(domain_id, [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Export taxonomy as dictionary."""
        return {
            "domains": {k: v.to_dict() for k, v in self.nodes.items()},
            "total_domains": len(self.get_all_domains())
        }
