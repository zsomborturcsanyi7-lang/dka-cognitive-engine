"""
DKA V3 — Concept Graph
=======================
A fogalmi tudásbázis szíve. Nem Python függvényeket tárol,
hanem ABSZTRAKT FOGALMAKAT és azok kapcsolatait.

Egy "lista" fogalom itt nem a Python listát jelenti,
hanem az absztrakt "elemek sorozata" fogalmat.
Hogy ezt Pythonban hogy írjuk, az a Generator dolga.

Minden fogalom:
  - definíció (embereknek)
  - tulajdonságok (gépnek)
  - kapcsolatok más fogalmakhoz
  - műveletek amiket támogat
  - példák
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto


class RelationType(Enum):
    """Kapcsolattípusok fogalmak között."""
    IS_A = auto()           # "kutya" IS_A "állat"
    HAS_PROPERTY = auto()   # "lista" HAS_PROPERTY "sorrend"
    HAS_OPERATION = auto()  # "lista" HAS_OPERATION "szűrés"
    PRODUCES = auto()       # "szűrés" PRODUCES "lista"
    REQUIRES = auto()       # "szűrés" REQUIRES "feltétel"
    OPPOSITE = auto()       # "páros" OPPOSITE "páratlan"
    EXAMPLE = auto()        # "páros" EXAMPLE "2, 4, 6"
    PART_OF = auto()        # "input" PART_OF "form"
    SAME_AS = auto()        # "array" SAME_AS "lista(tömb)"


@dataclass
class ConceptRelation:
    """Egy kapcsolat két fogalom között."""
    type: RelationType
    target_name: str        # cél fogalom neve
    strength: float = 1.0   # 0.0 - 1.0 (mennyire erős a kapcsolat)
    description: str = ""


@dataclass
class Operation:
    """Egy művelet, amit egy fogalom támogat."""
    name: str
    description: str
    inputs: list[str] = field(default_factory=list)      # bemenő fogalmak
    outputs: list[str] = field(default_factory=list)     # kimenő fogalmak
    constraints: list[str] = field(default_factory=list) # előfeltételek
    examples: list[str] = field(default_factory=list)    # szöveges példák


@dataclass
class Property:
    """Egy tulajdonság, amivel egy fogalom rendelkezhet."""
    name: str
    value_type: str          # "szám", "szöveg", "logikai", "fogalom"
    description: str = ""
    possible_values: list = field(default_factory=list)


@dataclass
class Concept:
    """Egy fogalom. Ez a DKA V3 alapegysége."""
    name: str
    description: str = ""
    
    # Tulajdonságok
    properties: list[Property] = field(default_factory=list)
    
    # Műveletek amiket ez a fogalom támogat
    operations: list[Operation] = field(default_factory=list)
    
    # Kapcsolatok más fogalmakhoz
    relations: list[ConceptRelation] = field(default_factory=list)
    
    # Nyelvi reprezentációk (hogyan jelenik meg különböző nyelvekben)
    # Pl. "lista" = Python: "list", HTML: "ul/ol", JS: "Array"
    language_mappings: dict[str, str] = field(default_factory=dict)
    
    # Példák
    examples: list[str] = field(default_factory=list)
    
    # Meta
    created_by: str = "system"
    confidence: float = 1.0  # mennyire biztos a fogalom


class ConceptGraph:
    """
    A fogalmi tudásbázis.
    
    Nem Python specifikus! Itt "lista" = elemek sorozata,
    függetlenül attól, hogy Pythonban list, JS-ben Array,
    HTML-ben ul/ol.
    """
    
    def __init__(self):
        self.concepts: dict[str, Concept] = {}
    
    def add(self, concept: Concept) -> Concept:
        """Fogalom hozzáadása vagy frissítése."""
        self.concepts[concept.name] = concept
        return concept
    
    def get(self, name: str) -> Optional[Concept]:
        """Fogalom lekérése név alapján."""
        return self.concepts.get(name)
    
    def get_or_create(self, name: str, description: str = "") -> Concept:
        """Fogalom lekérése vagy létrehozása ha nem létezik."""
        existing = self.get(name)
        if existing:
            return existing
        concept = Concept(name=name, description=description)
        self.add(concept)
        return concept
    
    def relate(self, source: str, target: str, 
               rel_type: RelationType, strength: float = 1.0,
               description: str = "") -> None:
        """Kapcsolat létrehozása két fogalom között."""
        source_c = self.get_or_create(source)
        target_c = self.get_or_create(target)
        
        # Meglévő kapcsolat erősítése
        for rel in source_c.relations:
            if rel.target_name == target and rel.type == rel_type:
                rel.strength = max(rel.strength, strength)
                if description:
                    rel.description = description
                return
        
        # Új kapcsolat
        source_c.relations.append(ConceptRelation(
            type=rel_type, target_name=target,
            strength=strength, description=description
        ))
    
    def find_by_operation(self, operation: str) -> list[Concept]:
        """Minden fogalom megkeresése, ami támogat egy műveletet."""
        results = []
        for concept in self.concepts.values():
            for op in concept.operations:
                if operation in op.name.lower():
                    results.append(concept)
                    break
        return results
    
    def find_by_property(self, property_name: str) -> list[Concept]:
        """Minden fogalom megkeresése, ami rendelkezik egy tulajdonsággal."""
        results = []
        for concept in self.concepts.values():
            for prop in concept.properties:
                if property_name in prop.name.lower():
                    results.append(concept)
                    break
        return results
    
    def get_related(self, name: str, rel_type: Optional[RelationType] = None) -> list[ConceptRelation]:
        """Egy fogalom kapcsolatainak lekérése."""
        concept = self.get(name)
        if not concept:
            return []
        if rel_type:
            return [r for r in concept.relations if r.type == rel_type]
        return concept.relations
    
    def shortest_path(self, from_name: str, to_name: str) -> list[str]:
        """Legrövidebb út két fogalom között (BFS)."""
        if from_name == to_name:
            return [from_name]
        
        visited = {from_name}
        queue = [[from_name]]
        
        while queue:
            path = queue.pop(0)
            last = path[-1]
            concept = self.get(last)
            if not concept:
                continue
            for rel in concept.relations:
                if rel.target_name not in visited:
                    new_path = path + [rel.target_name]
                    if rel.target_name == to_name:
                        return new_path
                    visited.add(rel.target_name)
                    queue.append(new_path)
        return []
    
    def infer(self, concept_name: str) -> list[str]:
        """Következtetés: mi IGAZ egy fogalomra a kapcsolatok alapján."""
        results = []
        concept = self.get(concept_name)
        if not concept:
            return results
        
        # IS_A lánc követése
        for rel in concept.relations:
            if rel.type == RelationType.IS_A:
                results.append(f"{concept_name} egy {rel.target_name}")
                results.extend(self.infer(rel.target_name))
        
        # Tulajdonságok
        for prop in concept.properties:
            results.append(f"{concept_name} rendelkezik: {prop.name} ({prop.description})")
        
        # Műveletek
        for op in concept.operations:
            results.append(f"{concept_name} tud: {op.name} ({op.description})")
        
        return results
    
    def stats(self) -> dict:
        """Statisztika a tudásbázisról."""
        total_relations = sum(len(c.relations) for c in self.concepts.values())
        total_operations = sum(len(c.operations) for c in self.concepts.values())
        return {
            "concepts": len(self.concepts),
            "relations": total_relations,
            "operations": total_operations,
        }
