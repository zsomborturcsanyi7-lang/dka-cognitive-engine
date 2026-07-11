"""
DKA Core — Hypergraph V2
=========================
3 rétegű hipergráf: Primitív Réteg → Minta Réteg → Séma Réteg.

Nem lineáris token tárolás, hanem strukturális kapcsolatok.
A kontextus mérése: Strukturális Egység (SE) — minden aktív nódus 1 SE.
"""

from __future__ import annotations
import json
import uuid
from collections import defaultdict
from typing import Optional

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain,
    NodeSerializer,
)


class HypergraphV2:
    """
    Háromrétegű hipergráf.
    
    1. réteg: Primitív Réteg (lapos nódusok)
    2. réteg: Minta Réteg (strukturált kapcsolatok) 
    3. réteg: Séma Réteg (fogalmi absztrakció)
    
    Minden réteg tud keresztbe hivatkozni a többire.
    """
    
    def __init__(self):
        # ─── 3 réteg ──────────────────────────────────────────────
        self.primitives: dict[str, PrimitiveNode] = {}      # id → PrimitiveNode
        self.patterns: dict[str, PatternNode] = {}          # id → PatternNode
        self.schemas: dict[str, SchemaNode] = {}            # id → SchemaNode
        
        # ─── Indexek ──────────────────────────────────────────────
        # Érték → nódus ID-k (gyors kereséshez)
        self.value_index: dict[str, list[str]] = defaultdict(list)
        # Típus → nódus ID-k
        self.type_index: dict[str, list[str]] = defaultdict(list)
        # Domain → nódus ID-k
        self.domain_index: dict[str, list[str]] = defaultdict(list)
        
        # Fingerprint index: adott fingerprint → nódus ID-k
        self.fingerprint_index: dict[str, set[str]] = defaultdict(set)
        
        # Forrás → nódus ID-k
        self.source_index: dict[str, list[str]] = defaultdict(list)
        
        # ─── Statisztika ──────────────────────────────────────────
        self.total_pies = 0  # Primitív Információs Egységek száma
        
        # Következő ID
        self._next_num_id = 0
    
    def _generate_id(self, prefix: str = "N") -> str:
        self._next_num_id += 1
        return f"{prefix}_{self._next_num_id}"
    
    def _index_node(self, node: BaseNode):
        """Regisztrál egy nódust az indexekbe."""
        nid = node.id
        self.value_index[node.value].append(nid)
        self.type_index[node.type.name].append(nid)
        self.domain_index[node.domain.name].append(nid)
        
        for fp in node.fingerprints:
            self.fingerprint_index[fp].add(nid)
        
        if node.source:
            self.source_index[node.source].append(nid)
    
    # ─── Nódus felvétel ────────────────────────────────────────────
    
    def add_primitive(self, node: PrimitiveNode) -> str:
        """Primitív nódus hozzáadása az 1. réteghez."""
        if not node.id:
            node.id = self._generate_id("P")
        self.primitives[node.id] = node
        self._index_node(node)
        self.total_pies += 1
        return node.id
    
    def add_pattern(self, node: PatternNode) -> str:
        """Minta nódus hozzáadása a 2. réteghez."""
        if not node.id:
            node.id = self._generate_id("M")
        
        # Gyerek nódusok automatikus regisztrációja
        for role, children in node.children.items():
            for child in children:
                if isinstance(child, PrimitiveNode) and child.id not in self.primitives:
                    self.add_primitive(child)
                elif isinstance(child, PatternNode) and child.id not in self.patterns:
                    self.add_pattern(child)
        
        self.patterns[node.id] = node
        self._index_node(node)
        self.total_pies += 1
        return node.id
    
    def add_schema(self, node: SchemaNode) -> str:
        """Séma nódus hozzáadása a 3. réteghez."""
        if not node.id:
            node.id = self._generate_id("S")
        self.schemas[node.id] = node
        self._index_node(node)
        self.total_pies += 1
        return node.id
    
    # ─── Tömeges betöltés ──────────────────────────────────────────
    
    def ingest_pattern_tree(self, nodes: list, domain: DataDomain = DataDomain.GENERAL,
                            source: str = "") -> list[str]:
        """
        GrammarParser kimenetének betöltése a hipergráfba.
        Visszaadja a legfelső szintű nódusok ID-it.
        """
        top_ids = []
        for node in nodes:
            if isinstance(node, PatternNode):
                nid = self.add_pattern(node)
                top_ids.append(nid)
            elif isinstance(node, PrimitiveNode):
                nid = self.add_primitive(node)
                top_ids.append(nid)
        return top_ids
    
    def learn_from_code(self, code: str, domain: DataDomain = DataDomain.GENERAL,
                        source: str = "") -> list[str]:
        """Python kód közvetlen betöltése."""
        from grammar_parser import GrammarParser
        parser = GrammarParser()
        nodes = parser.parse(code, domain=domain, source=source)
        return self.ingest_pattern_tree(nodes, domain=domain, source=source)
    
    # ─── Keresés ───────────────────────────────────────────────────
    
    def find_by_value(self, value: str) -> list[BaseNode]:
        """Keresés érték alapján (minden rétegben)."""
        ids = self.value_index.get(value, [])
        result = []
        for nid in ids:
            node = self.get_node(nid)
            if node:
                result.append(node)
        return result
    
    def find_by_type(self, ntype: NodeType) -> list[BaseNode]:
        """Keresés típus alapján."""
        ids = self.type_index.get(ntype.name, [])
        result = []
        for nid in ids:
            node = self.get_node(nid)
            if node:
                result.append(node)
        return result
    
    def find_by_fingerprint(self, fp: str) -> list[BaseNode]:
        """Keresés fingerprint alapján."""
        ids = self.fingerprint_index.get(fp, set())
        return [self.get_node(nid) for nid in ids if self.get_node(nid)]
    
    def get_node(self, nid: str) -> Optional[BaseNode]:
        """Nódus lekérése ID alapján (bármely rétegből)."""
        if nid in self.primitives:
            return self.primitives[nid]
        if nid in self.patterns:
            return self.patterns[nid]
        if nid in self.schemas:
            return self.schemas[nid]
        return None
    
    def get_all_nodes(self) -> list[BaseNode]:
        """Összes nódus listája."""
        nodes = []
        nodes.extend(self.primitives.values())
        nodes.extend(self.patterns.values())
        nodes.extend(self.schemas.values())
        return nodes
    
    # ─── Strukturális mérések ──────────────────────────────────────
    
    def calculate_depth(self, nid: str, visited: set[str] = None) -> int:
        """Strukturális mélység kiszámítása."""
        if visited is None:
            visited = set()
        if nid in visited:
            return 0
        
        visited.add(nid)
        node = self.get_node(nid)
        if not node:
            return 0
        
        max_depth = 0
        if isinstance(node, PatternNode) and node.children:
            for children in node.children.values():
                for child in children:
                    child_depth = self.calculate_depth(child.id, visited)
                    if child_depth > max_depth:
                        max_depth = child_depth
                    visited.add(child.id)
        
        return max_depth + 1
    
    def get_structural_distance(self, nid_a: str, nid_b: str, max_depth: int = 20) -> Optional[int]:
        """
        Strukturális Relevancia Távolság (SRT) két nódus között.
        Visszaadja, hogy hány él távolságra vannak egymástól a gráfban.
        None = nincs kapcsolat.
        """
        if nid_a == nid_b:
            return 0
        
        # BFS mindkét irányból
        from collections import deque
        
        def bfs(start_id, target_id, max_d):
            queue = deque([(start_id, 0)])
            visited = {start_id}
            while queue:
                current, dist = queue.popleft()
                if dist >= max_d:
                    continue
                
                node = self.get_node(current)
                if not node:
                    continue
                
                # Szomszédok: gyerekek + szülők
                neighbors = set()
                
                # 1. Gyerekek (PatternNode esetén)
                if isinstance(node, PatternNode):
                    for children in node.children.values():
                        for child in children:
                            neighbors.add(child.id)
                
                # 2. Szülők (mely PatternNode-ok gyereke ez a nódus)
                for pnode in self.patterns.values():
                    for children in pnode.children.values():
                        for child in children:
                            if child.id == current:
                                neighbors.add(pnode.id)
                
                # 3. Séma kapcsolatok
                for schema in self.schemas.values():
                    if current in schema.pattern_ids:
                        neighbors.add(schema.id)
                    if current == schema.id:
                        neighbors.update(schema.pattern_ids)
                
                for nid in neighbors:
                    if nid == target_id:
                        return dist + 1
                    if nid not in visited:
                        visited.add(nid)
                        queue.append((nid, dist + 1))
            
            return None
        
        return bfs(nid_a, nid_b, max_depth)
    
    def get_context_scope(self, focus_nid: str, max_se: int = 50) -> dict:
        """
        Aktív Scope lekérése.
        Visszaadja a fókuszált nódus körüli strukturális környezetet SE-ben mérve.
        
        Visszatérés:
        {
            "focus": BaseNode,
            "children": [...],  # közvetlen gyerekek (1 SE / db)
            "parents": [...],   # közvetlen szülők (1 SE / db)  
            "siblings": [...],  # testvérek (1 SE / db)
            "associations": [...],  # asszociált sémák (1 SE / db)
            "total_se": int
        }
        """
        scope = {
            "focus": self.get_node(focus_nid),
            "children": [],
            "parents": [],
            "siblings": [],
            "associations": [],
            "total_se": 0,
        }
        
        used = {focus_nid}
        
        # Gyerekek (PatternNode esetén)
        focus_node = scope["focus"]
        if isinstance(focus_node, PatternNode):
            for role, children in focus_node.children.items():
                for child in children:
                    if child.id not in used:
                        scope["children"].append({"role": role, "node": child})
                        used.add(child.id)
        
        # Szülők
        for pnode in self.patterns.values():
            for role, children in pnode.children.items():
                for child in children:
                    if child.id == focus_nid and pnode.id not in used:
                        scope["parents"].append({"role": role, "node": pnode})
                        used.add(pnode.id)
        
        # Testvérek (azonos szülő alatt)
        for pnode in self.patterns.values():
            for children in pnode.children.values():
                for child in children:
                    if child.id == focus_nid:
                        # Ez a szülő — testvérek az összes gyereke
                        for role2, children2 in pnode.children.items():
                            for sibling in children2:
                                if sibling.id != focus_nid and sibling.id not in used:
                                    scope["siblings"].append({"role": role2, "node": sibling})
                                    used.add(sibling.id)
        
        # Asszociált sémák
        for schema in self.schemas.values():
            if focus_nid in schema.pattern_ids and schema.id not in used:
                scope["associations"].append({"node": schema, "strength": schema.associations.get(schema.id, 1.0)})
                used.add(schema.id)
        
        scope["total_se"] = len(scope["children"]) + len(scope["parents"]) + len(scope["siblings"]) + len(scope["associations"]) + 1  # +1 a focus
        
        return scope
    
    # ─── Pattern Discovery ─────────────────────────────────────────
    
    def discover_patterns(self, min_instances: int = 2) -> list[dict]:
        """
        Automatikus mintafelfedezés.
        Megkeresi azokat a struktúra-kombinációkat, amik többször előfordulnak.
        
        Visszaadja a gyakori mintákat a gyakoriságukkal.
        """
        # Csoportosítás típus + szerepkör kombinációk szerint
        signature_counts = defaultdict(list)
        
        for pattern in self.patterns.values():
            # Készítsünk egy "ujjlenyomatot" a minta szerkezetéről
            sig_parts = [pattern.type.name]
            for role, children in pattern.children.items():
                child_types = sorted(set(c.type.name for c in children))
                sig_parts.append(f"{role}:{','.join(child_types)}")
            signature = "|".join(sig_parts)
            
            signature_counts[signature].append(pattern.id)
        
        # Gyakori minták
        discoveries = []
        for signature, ids in signature_counts.items():
            if len(ids) >= min_instances:
                discoveries.append({
                    "signature": signature,
                    "count": len(ids),
                    "pattern_ids": ids,
                    "examples": [
                        {"id": pid, "type": self.patterns[pid].type.name}
                        for pid in ids[:3]
                    ]
                })
        
        return sorted(discoveries, key=lambda d: d["count"], reverse=True)
    
    # ─── Séma építés ───────────────────────────────────────────────
    
    def build_schema(self, name: str, pattern_ids: list[str],
                     domain: DataDomain = DataDomain.GENERAL) -> Optional[SchemaNode]:
        """
        Új séma létrehozása meglévő mintákból.
        Automatikusan kiszámolja az asszociációkat.
        """
        valid_ids = [pid for pid in pattern_ids if pid in self.patterns]
        if len(valid_ids) < 2:
            return None
        
        schema = SchemaNode(
            name=name,
            type=NodeType.SCHEMA,
            pattern_ids=set(valid_ids),
            domain=domain,
        )
        
        # Asszociációk: a séma mintái között meglévő kapcsolatok
        for pid in valid_ids:
            pattern = self.patterns[pid]
            
            # Keressünk olyan sémákat, amik ezt a mintát is tartalmazzák
            for existing_schema in self.schemas.values():
                if pid in existing_schema.pattern_ids and existing_schema.id != schema.id:
                    strength = len(existing_schema.pattern_ids & set(valid_ids)) / len(set(valid_ids))
                    schema.associations[existing_schema.id] = max(
                        schema.associations.get(existing_schema.id, 0),
                        strength
                    )
        
        self.add_schema(schema)
        return schema
    
    # ─── Statisztika ───────────────────────────────────────────────
    
    def stats(self) -> dict:
        """Hipergráf statisztika."""
        return {
            "total_pie": self.total_pies,
            "primitives": len(self.primitives),
            "patterns": len(self.patterns),
            "schemas": len(self.schemas),
            "fingerprints": len(self.fingerprint_index),
            "sources": len(self.source_index),
            "depth": max([self.calculate_depth(nid) for nid in list(self.primitives.keys())[:100]] or [0]),
        }
    
    # ─── Serializáció ──────────────────────────────────────────────
    
    def to_json(self) -> str:
        data = {
            "primitives": {nid: NodeSerializer.to_dict(node) for nid, node in self.primitives.items()},
            "patterns": {nid: NodeSerializer.to_dict(node) for nid, node in self.patterns.items()},
            "schemas": {nid: NodeSerializer.to_dict(node) for nid, node in self.schemas.items()},
            "stats": self.stats(),
        }
        return json.dumps(data, indent=2)
    
    @staticmethod
    def from_json(json_str: str) -> HypergraphV2:
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        
        graph = HypergraphV2()
        
        # Először az összes nódust betöltjük
        all_nodes: dict[str, BaseNode] = {}
        
        for nid, ndata in data.get("primitives", {}).items():
            node = NodeSerializer.from_dict(ndata)
            all_nodes[nid] = node
            graph.primitives[nid] = node
        
        for nid, ndata in data.get("patterns", {}).items():
            node = NodeSerializer.from_dict(ndata, all_nodes)
            all_nodes[nid] = node
            graph.patterns[nid] = node
        
        for nid, ndata in data.get("schemas", {}).items():
            node = NodeSerializer.from_dict(ndata)
            all_nodes[nid] = node
            graph.schemas[nid] = node
        
        # Indexek újraépítése
        for node in all_nodes.values():
            graph._index_node(node)
            graph.total_pies += 1
        
        graph._next_num_id = len(all_nodes)
        
        return graph
    
    def to_json_file(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @staticmethod
    def from_json_file(path: str) -> HypergraphV2:
        with open(path, 'r', encoding='utf-8') as f:
            return HypergraphV2.from_json(f.read())
