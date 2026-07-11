"""
DKA Core — Inference Engine V2
================================
Strukturális következtető motor.

Nem statisztikai súlyok, hanem:
- Strukturális Relevancia Távolság (SRT)
- Aktív Scope (SE-ben mérve)
- Pattern Illesztés (struktúra egyezés)
- Analógiás következtetés (Séma rétegből)

Cél: adott probléma → gráfban meglévő minták → új struktúra építés.
"""

from __future__ import annotations
from typing import Optional
from collections import deque

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain,
)
from hypergraph_v2 import HypergraphV2


class InferenceEngineV2:
    """
    DKA következtető motor.
    
    Két fő képesség:
    1. Pattern Matching — meglévő minták felismerése új kódban
    2. Constructive Reasoning — új struktúra építése analógiák alapján
    
    Minden mérés SE-ben (Strukturális Egység) történik.
    """
    
    def __init__(self, graph: HypergraphV2):
        self.graph = graph
        self.max_search_depth = 50  # SE
        self.analogy_threshold = 0.6  # Hasonlósági küszöb
    
    # ─── Pattern Matching ─────────────────────────────────────────
    
    def match_pattern(self, node_a: PatternNode, node_b: PatternNode) -> dict:
        """
        Két PatternNode összehasonlítása.
        Visszaadja a hasonlósági pontszámot és a különbségeket.
        
        Pontozás:
        - Típus egyezés: 30 pont
        - Role-ok egyezése: 30 pont  
        - Gyerek nódusok típus egyezés: 40 pont
        """
        score = 0
        max_score = 100
        details = []
        
        # 1. Típus egyezés
        if node_a.type == node_b.type:
            score += 30
            details.append(f"type_match:{node_a.type.name}")
        else:
            details.append(f"type_mismatch:{node_a.type.name}!={node_b.type.name}")
        
        # 2. Role-ok egyezése
        roles_a = set(node_a.roles.keys()) if hasattr(node_a, 'roles') else set(node_a.children.keys())
        roles_b = set(node_b.roles.keys()) if hasattr(node_b, 'roles') else set(node_b.children.keys())
        
        common_roles = roles_a & roles_b
        total_roles = roles_a | roles_b
        
        if total_roles:
            role_score = (len(common_roles) / len(total_roles)) * 30
            score += role_score
            if common_roles:
                details.append(f"roles:{len(common_roles)}/{len(total_roles)}")
        
        # 3. Gyerekek típusának egyezése közös role-okban
        child_match_total = 0
        child_match_count = 0
        
        for role in common_roles:
            children_a = node_a.children.get(role, [])
            children_b = node_b.children.get(role, [])
            
            for ca, cb in zip(children_a, children_b):
                child_match_total += 1
                if ca.type == cb.type:
                    child_match_count += 1
                # Rekurzív összehasonlítás PatternNode-okra
                elif isinstance(ca, PatternNode) and isinstance(cb, PatternNode):
                    sub_match = self.match_pattern(ca, cb)
                    if sub_match["score"] >= 60:
                        child_match_count += 1
        
        if child_match_total > 0:
            child_score = (child_match_count / child_match_total) * 40
            score += child_score
            details.append(f"children:{child_match_count}/{child_match_total}")
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": round(score / max_score * 100, 1),
            "details": details,
            "match": score >= 70,
        }
    
    # ─── Analogy Finder ───────────────────────────────────────────
    
    def find_analogies(self, query: PatternNode, max_results: int = 5) -> list[dict]:
        """
        Hasonló minták keresése a gráfban.
        SE-ben méri a távolságot, struktúrában a hasonlóságot.
        """
        results = []
        
        for pid, candidate in self.graph.patterns.items():
            if candidate.id == query.id:
                continue
            
            # Pattern egyezés
            match_result = self.match_pattern(query, candidate)
            
            # Csak akkor vesszük, ha elég hasonló
            if match_result["percentage"] >= self.analogy_threshold * 100:
                # SRT számítás (ha van kapcsolat)
                srt = None
                if query.id and candidate.id:
                    srt = self.graph.get_structural_distance(query.id, candidate.id)
                
                results.append({
                    "pattern_id": pid,
                    "pattern": candidate,
                    "similarity": match_result["percentage"],
                    "structural_distance_se": srt,
                    "match_details": match_result["details"],
                })
        
        # Rendezés hasonlóság szerint
        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:max_results]
    
    # ─── Constructive Reasoning ───────────────────────────────────
    
    def solve_with_patterns(self, goal_type: NodeType, constraints: dict = None) -> Optional[PatternNode]:
        """
        Cél: létrehozni egy PatternNode-ot adott típusból,
        a gráfban található analógiák alapján.
        
        constraints: {"role_name": {"type": NodeType, "value": str, ...}}
        
        Példa:
          solve_with_patterns(FOR_LOOP, {"iter": {"value": "range"}})
          → for x in range(n):
        """
        # 1. Keressünk összes ilyen típusú mintát
        candidates = self.graph.find_by_type(goal_type)
        if not candidates:
            return None
        
        # 2. Szűkítsük a megszorítások alapján
        if constraints:
            filtered = []
            for candidate in candidates:
                if isinstance(candidate, PatternNode):
                    if self._check_constraints(candidate, constraints):
                        filtered.append(candidate)
            if filtered:
                candidates = filtered
        
        if not candidates:
            return None
        
        # 3. Vegyük a legjobban illeszkedőt és klónozzuk
        best = candidates[0]
        return self._clone_pattern(best)
    
    def _check_constraints(self, pattern: PatternNode, constraints: dict) -> bool:
        """Ellenőrzi, hogy egy PatternNode megfelel-e a megszorításoknak."""
        for role, constraint in constraints.items():
            children = pattern.children.get(role, [])
            if not children:
                return False
            
            child = children[0]
            constraint_type = constraint.get("type")
            constraint_value = constraint.get("value")
            
            if constraint_type and child.type != constraint_type:
                return False
            if constraint_value and child.value != constraint_value:
                return False
        
        return True
    
    def _clone_pattern(self, pattern: PatternNode) -> PatternNode:
        """PatternNode klónozása (új ID-val)."""
        clone = PatternNode(
            type=pattern.type,
            value=pattern.value,
            role=pattern.role,
            domain=pattern.domain,
            source=pattern.source,
            roles=pattern.roles.copy() if pattern.roles else {},
            confidence=1.0,
        )
        
        # Gyerekek másolása (rekurzívan)
        for role, children in pattern.children.items():
            cloned_children = []
            for child in children:
                if isinstance(child, PatternNode):
                    cloned_children.append(self._clone_pattern(child))
                elif isinstance(child, PrimitiveNode):
                    cloned_child = PrimitiveNode(
                        type=child.type,
                        value=child.value,
                        role=child.role,
                        domain=child.domain,
                        source=child.source,
                        fingerprints=child.fingerprints.copy(),
                    )
                    cloned_children.append(cloned_child)
            clone.children[role] = cloned_children
        
        return clone
    
    # ─── Gap Filling ─────────────────────────────────────────────
    
    def fill_gap(self, context_sequence: list[PatternNode], 
                 target_type: NodeType) -> Optional[PatternNode]:
        """
        Hiányzó lépés kitöltése a kontextus alapján.
        
        Példa: [FunctionDef, ...] → "mi kell ide, hogy működjön?"
        A kontextus alapján analógiát keres, és a legvalószínűbb 
        PatternNode-ot adja vissza.
        """
        if not context_sequence:
            return None
        
        # 1. Utolsó nódus kontextusa
        last_node = context_sequence[-1]
        
        # 2. Keressünk hasonló kontextust a gráfban
        #    (olyan mintákat, ahol az utolsó nódus után target_type következik)
        for pid, pattern in self.graph.patterns.items():
            if pattern.type == target_type:
                # Ellenőrizzük, hogy a kontextusban lévő minta 
                # előzménye hasonló-e
                match = self.match_pattern(last_node, pattern)
                if match["match"]:
                    return self._clone_pattern(pattern)
        
        # 3. Ha nincs pontos egyezés, próbáljunk sémákat
        for schema in self.graph.schemas.values():
            for pid in schema.pattern_ids:
                pattern = self.graph.patterns.get(pid)
                if pattern and pattern.type == target_type:
                    return self._clone_pattern(pattern)
        
        return None
    
    # ─── Program Synthesis ────────────────────────────────────────
    
    def synthesize(self, goal_description: str, 
                   available_types: list[NodeType] = None) -> list[PatternNode]:
        """
        Cél leírás → program szintézis.
        
        goal_description: pl. "sort an array" vagy "fetch data from api"
        available_types: milyen típusú mintákból építkezhet
        
        Ez a legmagasabb szintű belépési pont.
        """
        print(f"[Inference] Cél: '{goal_description}'")
        print(f"[Inference] Elérhető típusok: {[t.name for t in (available_types or [])]}")
        
        result = []
        
        # 1. Kulcsszavak kinyerése a leírásból
        keywords = goal_description.lower().split()
        
        # 2. Próbáljunk sémákat találni a kulcsszavak alapján
        matched_schemas = []
        for schema in self.graph.schemas.values():
            schema_words = schema.name.lower().split("_")
            if any(kw in schema_words or any(kw in sname for sname in schema_words) 
                   for kw in keywords):
                matched_schemas.append(schema)
        
        if matched_schemas:
            print(f"[Inference] Talált sémák: {[s.name for s in matched_schemas]}")
            for schema in matched_schemas[:2]:
                for pid in schema.pattern_ids:
                    pattern = self.graph.patterns.get(pid)
                    if pattern and (not available_types or pattern.type in available_types):
                        result.append(self._clone_pattern(pattern))
        
        # 3. Ha nincs séma, próbáljunk típus alapú keresést
        if not result and available_types:
            for atype in available_types:
                candidates = self.graph.find_by_type(atype)
                if candidates:
                    best = candidates[0]
                    if isinstance(best, PatternNode):
                        result.append(self._clone_pattern(best))
        
        # 4. Gap filling: ha van result, nézzük meg mi hiányzik
        if result and available_types:
            used_types = set(p.type for p in result)
            missing_types = [t for t in available_types if t not in used_types]
            
            for mtype in missing_types:
                gap_fill = self.fill_gap(result, mtype)
                if gap_fill:
                    result.append(gap_fill)
        
        return result


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from grammar_parser import GrammarParser
    from constructive_generator import ConstructiveGenerator
    
    parser = GrammarParser()
    graph = HypergraphV2()
    gen = ConstructiveGenerator(graph)
    engine = InferenceEngineV2(graph)
    
    # Tanító kód
    training_code = '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''
    
    nodes = parser.parse(training_code)
    graph.ingest_pattern_tree(nodes)
    
    print("=== GRÁF STATISZTIKA ===")
    stats = graph.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print()
    print("=== PATTERN DISCOVERY ===")
    patterns = graph.discover_patterns()
    for p in patterns:
        print(f"  {p['signature'][:60]}... x{p['count']}")
    
    print()
    print("=== PATTERN MATCHING TESZT ===")
    all_fors = graph.find_by_type(NodeType.FOR_LOOP)
    if len(all_fors) >= 2:
        match = engine.match_pattern(all_fors[0], all_fors[1])
        print(f"  Két FOR ciklus hasonlósága: {match['percentage']}% (match={match['match']})")
    
    all_ifs = graph.find_by_type(NodeType.IF_STATEMENT)
    if len(all_ifs) >= 2:
        match = engine.match_pattern(all_ifs[0], all_ifs[1])
        print(f"  Két IF hasonlósága: {match['percentage']}% (match={match['match']})")
    
    # Klónozás teszt
    print()
    print("=== SZINTÉZIS TESZT ===")
    synthesized = engine.synthesize("sort", [NodeType.FOR_LOOP, NodeType.IF_STATEMENT, NodeType.RETURN_STMT])
    if synthesized:
        print(f"  Generált {len(synthesized)} nódus")
        code = gen.generate(synthesized[0])
        print(f"  Kód: {code[:100]}...")
    
    print()
    print("=== GRÁF MENTÉS ===")
    graph.to_json_file("dka_test_graph.json")
    print(f"  Elmentve: dka_test_graph.json ({graph.stats()['total_pie']} PIE)")
