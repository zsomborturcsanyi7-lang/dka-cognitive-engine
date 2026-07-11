"""
DKA Core — Szimbolikus Nódus Rendszer
=======================================
Nem token-ek, hanem típusos, hierarchikus nódusok.
3 réteg: Primitív → Minta → Séma

Minden nódus egy Primitív Információs Egység (PIE).
Az "értelme" nem a string value-ben van, hanem a típusban + kapcsolatokban.
"""

from __future__ import annotations
import uuid
import json
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional


# ─── Típusok ─────────────────────────────────────────────────────────

class NodeType(Enum):
    # Primitív réteg
    VARIABLE = auto()
    KEYWORD = auto()
    OPERATOR = auto()
    LITERAL = auto()
    DELIMITER = auto()
    
    # Minta réteg
    ASSIGNMENT = auto()
    FOR_LOOP = auto()
    WHILE_LOOP = auto()
    IF_STATEMENT = auto()
    FUNCTION_CALL = auto()
    FUNCTION_DEF = auto()
    LAMBDA = auto()
    CLASS_DEF = auto()
    RETURN_STMT = auto()
    IMPORT = auto()
    EXPRESSION = auto()
    BLOCK = auto()
    COMPARISON = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    ATTRIBUTE_ACCESS = auto()
    INDEX_ACCESS = auto()
    LIST_COMP = auto()
    
    # Séma réteg
    PATTERN = auto()
    SCHEMA = auto()
    ANALOGY = auto()
    
    # Speciális
    ROOT = auto()
    UNKNOWN = auto()


class DataDomain(Enum):
    """Milyen domain-be tartozik a nódus."""
    GENERAL = auto()
    WEB = auto()
    MATH = auto()
    IO = auto()
    SECURITY = auto()
    ALGORITHM = auto()
    DATA_STRUCTURE = auto()
    NETWORK = auto()
    CONFIG = auto()


# ─── Szerepkörök ─────────────────────────────────────────────────────

@dataclass
class Role:
    """Mit csinál ez a nódus a szülő mintában."""
    name: str  # pl. "loop_index", "condition", "body", "target", "value"
    
    # A szerepkörhöz tartozó típus-megszorítások
    # Pl. egy "target" role csak VARIABLE típusú gyerek lehet
    allowed_types: list[NodeType] = field(default_factory=list)
    
    # Hány gyerek töltheti be ezt a szerepkört (None = bármennyi)
    cardinality: Optional[tuple[int, int]] = None  # (min, max)


# ─── Nódusok ─────────────────────────────────────────────────────────

@dataclass
class BaseNode:
    """Minden nódus alapja — egy Primitív Információs Egység (PIE)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    type: NodeType = NodeType.UNKNOWN
    value: str = ""
    role: Optional[str] = None
    domain: DataDomain = DataDomain.GENERAL
    source: str = ""  # Melyik fájlból/mondatból jött
    
    # Fingerprint — hash-ek arról, hogy milyen mintákban szerepel
    fingerprints: set[str] = field(default_factory=set)
    
    # SRT méréshez: strukturális távolság cache
    _structural_depth: int = 0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.name,
            "value": self.value,
            "role": self.role,
            "domain": self.domain.name,
            "source": self.source,
            "fingerprints": list(self.fingerprints),
        }
    
    @staticmethod
    def from_dict(d: dict) -> BaseNode:
        return BaseNode(
            id=d["id"],
            type=NodeType[d["type"]],
            value=d.get("value", ""),
            role=d.get("role"),
            domain=DataDomain[d.get("domain", "GENERAL")],
            source=d.get("source", ""),
            fingerprints=set(d.get("fingerprints", [])),
        )


@dataclass
class PrimitiveNode(BaseNode):
    """
    1. réteg: Primitív nódus.
    A legkisebb építőkő — változó, operátor, kulcsszó, literál.
    """
    # Konkrét pozíció az eredeti forrásban (debug/bizonyíték)
    source_pos: Optional[tuple[int, int]] = None  # (sor, oszlop)


@dataclass
class PatternNode(BaseNode):
    """
    2. réteg: Minta nódus.
    Strukturált kapcsolat — assignment, for loop, if, function call.
    A gyerekek role-al vannak címkézve, nem sorszámmal.
    """
    type: NodeType = NodeType.PATTERN
    children: dict[str, list['PatternNode | PrimitiveNode']] = field(default_factory=dict)
    # children: {"target": [node1], "operator": [node2], "value": [node3]}
    
    # Constraints: milyen típusú gyerekeket vár
    roles: dict[str, Role] = field(default_factory=dict)
    
    # Hányszor láttuk ezt a mintát (tanulási erősség)
    confidence: float = 1.0
    
    def get_by_role(self, role_name: str) -> list:
        return self.children.get(role_name, [])
    
    def get_first_by_role(self, role_name: str) -> Optional:
        kids = self.children.get(role_name, [])
        return kids[0] if kids else None
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d["children"] = {
            role: [c.id for c in children]
            for role, children in self.children.items()
        }
        d["roles"] = {
            name: {"allowed_types": [t.name for t in r.allowed_types]}
            for name, r in self.roles.items()
        }
        d["confidence"] = self.confidence
        return d


@dataclass
class SchemaNode(BaseNode):
    """
    3. réteg: Séma nódus.
    Magas szintű fogalmi absztrakció.
    Összeköt több PatternNode-ot egy fogalommá.
    """
    type: NodeType = NodeType.SCHEMA
    name: str = ""
    
    # A sémát alkotó minták
    pattern_ids: set[str] = field(default_factory=set)
    
    # Általánosítások — magasabb szintű séma
    generalizations: dict[str, str] = field(default_factory=dict)
    # {"enumeráció": "gyűjtemény_bejárás"}
    
    # Variációk — alacsonyabb szintű megvalósítások
    variations: dict[str, str] = field(default_factory=dict)
    # {"tömb": "for_i_in_range", "lista": "for_elem_in_list"}
    
    # Asszociációk más sémákhoz (szemantikus kapcsolat)
    associations: dict[str, float] = field(default_factory=dict)
    # {"error_handling": 0.85}
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        d["name"] = self.name
        d["pattern_ids"] = list(self.pattern_ids)
        d["generalizations"] = self.generalizations
        d["variations"] = self.variations
        d["associations"] = self.associations
        return d


# ─── Utility ─────────────────────────────────────────────────────────

def make_pattern_node(ptype: NodeType, roles: dict[str, Role] = None) -> PatternNode:
    """Gyors PatternNode gyártás."""
    return PatternNode(
        type=ptype,
        roles=roles or {},
    )


# ─── Serializáció ────────────────────────────────────────────────────

class NodeSerializer:
    """Tudja, hogy melyik nódus melyik réteghez tartozik."""
    
    @staticmethod
    def to_dict(node: BaseNode) -> dict:
        if isinstance(node, SchemaNode):
            return node.to_dict()
        elif isinstance(node, PatternNode):
            return node.to_dict()
        else:
            return node.to_dict()
    
    @staticmethod
    def from_dict(d: dict, all_nodes: dict[str, BaseNode] = None) -> BaseNode:
        ntype = NodeType[d.get("type", "UNKNOWN")]
        
        # Séma réteg
        if "pattern_ids" in d:
            return SchemaNode(
                id=d["id"],
                type=ntype,
                value=d.get("value", ""),
                name=d.get("name", ""),
                pattern_ids=set(d.get("pattern_ids", [])),
                generalizations=d.get("generalizations", {}),
                variations=d.get("variations", {}),
                associations={k: float(v) for k, v in d.get("associations", {}).items()},
                role=d.get("role"),
                domain=DataDomain[d.get("domain", "GENERAL")],
                source=d.get("source", ""),
            )
        
        # Minta réteg
        if "children" in d:
            children = {}
            for role_name, child_ids in d.get("children", {}).items():
                children[role_name] = [
                    all_nodes[cid] if all_nodes and cid in all_nodes else BaseNode(id=cid)
                    for cid in child_ids
                ]
            
            roles = {}
            for name, rdata in d.get("roles", {}).items():
                roles[name] = Role(
                    name=name,
                    allowed_types=[NodeType[t] for t in rdata.get("allowed_types", [])]
                )
            
            return PatternNode(
                id=d["id"],
                type=ntype,
                value=d.get("value", ""),
                children=children,
                roles=roles,
                confidence=float(d.get("confidence", 1.0)),
                role=d.get("role"),
                domain=DataDomain[d.get("domain", "GENERAL")],
                source=d.get("source", ""),
            )
        
        # Primitív réteg
        return PrimitiveNode(
            id=d["id"],
            type=ntype,
            value=d.get("value", ""),
            role=d.get("role"),
            domain=DataDomain[d.get("domain", "GENERAL")],
            source=d.get("source", ""),
            fingerprints=set(d.get("fingerprints", [])),
        )
