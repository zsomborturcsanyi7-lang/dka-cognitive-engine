"""
DKA Core — Synthesis Engine V2
================================
Cél: új kód előállítása meglévő minták kombinációjából.

Architektúra:
1. Cél lebontása (Goal Decomposition) → részcélok
2. Minta keresés (Pattern Retrieval) → minden részcélhoz
3. Kompozíció (Composition) → részek összeillesztése
4. Generálás → valid Python kód

Példa: "írj egy fájlkereső függvényt"
1. Cél lebontás: FUNCTION_DEF + FILE_IO + SEARCH_LOGIC
2. Minta keresés: read_config (file io) + bubble_sort (comparison loop)
3. Kompozíció: read_config struktúrája + bubble_sort logikája
4. Eredmény: def search_file(path, keyword): ...

A kompozíció a kulcs: hogyan lehet két független mintát
összeolvasztani egy új, működő programmá.
"""

from __future__ import annotations
from typing import Optional
from collections import Counter
import re

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain,
    make_pattern_node,
)
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex


class GoalDecomposer:
    """
    1. lépés: Cél lebontása részmintákra.
    
    "sort numbers" → [FUNCTION_DEF, FOR_LOOP, COMPARISON, SWAP]
    "read file"   → [FUNCTION_DEF, FILE_OPEN, DATA_READ, RETURN]
    "api fetch"   → [FUNCTION_DEF, HTTP_REQUEST, JSON_PARSE, RETURN]
    """
    
    # Ismert cél → részminták térkép
    KNOWN_GOALS = {
        # Rendezési minták
        "sort": ["FUNCTION_DEF", "FOR_LOOP", "FOR_LOOP", "COMPARISON", "ASSIGNMENT", "RETURN_STMT"],
        "order": ["FUNCTION_DEF", "FOR_LOOP", "COMPARISON", "ASSIGNMENT", "RETURN_STMT"],
        "bubble": ["FUNCTION_DEF", "FOR_LOOP", "FOR_LOOP", "COMPARISON", "ASSIGNMENT", "RETURN_STMT"],
        
        # Matematikai minták
        "factorial": ["FUNCTION_DEF", "IF_STATEMENT", "COMPARISON", "RETURN_STMT", "FUNCTION_CALL", "BINARY_OP"],
        "fibonacci": ["FUNCTION_DEF", "IF_STATEMENT", "COMPARISON", "RETURN_STMT", "FUNCTION_CALL", "BINARY_OP"],
        "math": ["FUNCTION_DEF", "IF_STATEMENT", "RETURN_STMT", "FUNCTION_CALL", "BINARY_OP"],
        
        # Fájl műveletek
        "file": ["FUNCTION_DEF", "FUNCTION_CALL", "FUNCTION_CALL", "RETURN_STMT"],
        "read": ["FUNCTION_DEF", "FUNCTION_CALL", "FUNCTION_CALL", "RETURN_STMT"],
        "write": ["FUNCTION_DEF", "FUNCTION_CALL", "RETURN_STMT"],
        "config": ["FUNCTION_DEF", "FUNCTION_CALL", "FUNCTION_CALL", "RETURN_STMT"],
        
        # API minták
        "api": ["FUNCTION_DEF", "FUNCTION_CALL", "ATTRIBUTE_ACCESS", "IF_STATEMENT", "RETURN_STMT"],
        "fetch": ["FUNCTION_DEF", "FUNCTION_CALL", "IF_STATEMENT", "RETURN_STMT"],
        "request": ["FUNCTION_DEF", "FUNCTION_CALL", "ATTRIBUTE_ACCESS", "IF_STATEMENT", "RETURN_STMT"],
        "get": ["FUNCTION_DEF", "FUNCTION_CALL", "IF_STATEMENT", "RETURN_STMT"],
        
        # Adat struktúrák
        "list": ["FUNCTION_DEF", "FOR_LOOP", "FUNCTION_CALL", "RETURN_STMT"],
        "search": ["FUNCTION_DEF", "FOR_LOOP", "IF_STATEMENT", "COMPARISON", "RETURN_STMT"],
        "find": ["FUNCTION_DEF", "FOR_LOOP", "IF_STATEMENT", "RETURN_STMT"],
        "filter": ["FUNCTION_DEF", "FOR_LOOP", "IF_STATEMENT", "FUNCTION_CALL", "RETURN_STMT"],
        "count": ["FUNCTION_DEF", "FOR_LOOP", "IF_STATEMENT", "ASSIGNMENT", "RETURN_STMT"],
        
        # Algoritmus minták
        "loop": ["FOR_LOOP", "BLOCK"],
        "iterate": ["FOR_LOOP", "BLOCK"],
        "check": ["IF_STATEMENT", "COMPARISON", "BLOCK"],
        "compare": ["COMPARISON", "IF_STATEMENT"],
        "return": ["RETURN_STMT"],
        "convert": ["FUNCTION_DEF", "FUNCTION_CALL", "RETURN_STMT"],
        "parse": ["FUNCTION_DEF", "FUNCTION_CALL", "RETURN_STMT"],
    }
    
    def __init__(self, graph: HypergraphV2, semantics: SemanticIndex):
        self.graph = graph
        self.semantics = semantics
    
    def decompose(self, goal: str) -> list[str]:
        """
        Cél lebontása részminták listájára.
        Prioritás: pontosabb kulcsszó egyezés > általános.
        """
        goal_lower = goal.lower()
        words = set(re.findall(r'[a-zA-Z_]\w*', goal_lower))
        
        needed_types = []
        best_score = 0
        best_types = None
        
        # 1. Ismert célok pontozása: mennyire illeszkedik a célhoz
        for keyword, types in self.KNOWN_GOALS.items():
            score = 0
            # Teljes szó egyezés
            if keyword in words:
                score += 10
            # Részleges egyezés
            elif keyword in goal_lower:
                score += 5
            
            # Szemantikus egyezés: a szótár kulcsszavak a szövegben
            keyword_parts = set(re.findall(r'[a-zA-Z]+', keyword))
            word_overlap = len(keyword_parts & words)
            if word_overlap > 0:
                score += word_overlap * 3
            
            if score > best_score:
                best_score = score
                best_types = types
        
        # 2. Ha találtunk ismert célt, használjuk
        if best_types and best_score >= 3:
            return best_types
        
        # 3. Különben: szemantikus keresés + típus következtetés
        sem_results = self.semantics.search_by_text(goal, top_k=3)
        found_types = set()
        for r in sem_results:
            found_types.add(r['type'])
            # Keressük a minta típusát a gráfban
            pattern = self.graph.patterns.get(r['id'])
            if pattern:
                # Adjuk hozzá a minta gyerekeinek típusait is
                for children in pattern.children.values():
                    for child in children:
                        if isinstance(child, PatternNode):
                            found_types.add(child.type.name)
        
        if found_types:
            # Rendezzük: FUNCTION_DEF előre
            ordered = []
            if "FUNCTION_DEF" in found_types:
                ordered.append("FUNCTION_DEF")
                found_types.discard("FUNCTION_DEF")
            ordered.extend(sorted(found_types, key=lambda t: -len(t)))
            return ordered
        
        # 4. Alapértelmezett: keresés a szemantikus indexben
        related = self.semantics.search_by_text(goal, top_k=1)
        if related:
            pattern = self.graph.patterns.get(related[0]['id'])
            if pattern:
                # Vegyük a minta típusát + gyerekeit
                types = [pattern.type.name]
                for children in pattern.children.values():
                    for child in children:
                        if isinstance(child, PatternNode):
                            types.append(child.type.name)
                return types
        
        return ["FUNCTION_DEF", "RETURN_STMT"]


class PatternRetriever:
    """
    2. lépés: Minden részcélhoz megkeresi a legjobb mintát.
    """
    
    def __init__(self, graph: HypergraphV2, semantics: SemanticIndex):
        self.graph = graph
        self.semantics = semantics
    
    def retrieve(self, needed_types: list[str], goal: str = "") -> list[dict]:
        """
        Minden típushoz megkeresi a legjobb mintát.
        Ha van goal, a szemantikus keresést használja a legjobb
        FUNCTION_DEF kiválasztásához.
        """
        results = []
        used_ids = set()
        
        # Ha van goal és kell FUNCTION_DEF, először szemantikusan keresünk
        has_func = False
        if goal and "FUNCTION_DEF" in needed_types:
            sem_results = self.semantics.search_by_text(goal, top_k=3)
            for sr in sem_results:
                if sr['type'] == 'FUNCTION_DEF' and sr['id'] not in used_ids:
                    pattern = self.graph.patterns.get(sr['id'])
                    if pattern:
                        results.append({
                            "type": "FUNCTION_DEF",
                            "pattern_id": sr['id'],
                            "pattern": pattern,
                            "source": sr.get('name', ''),
                            "relevance": sr.get('relevance', 1),
                        })
                        used_ids.add(sr['id'])
                        has_func = True
                        break
        
        type_map = {t.name: t for t in NodeType}
        
        for ntype_name in needed_types:
            if ntype_name not in type_map:
                continue
            
            # Ha már van FUNCTION_DEF, a többit ne adjuk hozzá
            if ntype_name == "FUNCTION_DEF" and has_func:
                continue
            
            ntype = type_map[ntype_name]
            candidates = self.graph.find_by_type(ntype)
            
            if not candidates:
                continue
            
            # Válasszuk a legjobbat: preferáljuk a már használttól különbözőt
            best = None
            for c in candidates:
                if c.id not in used_ids:
                    best = c
                    break
            
            if best is None and candidates:
                best = candidates[0]
            
            if best:
                # Keressük a forrást
                source = ""
                if isinstance(best, PatternNode):
                    for pid2, p2 in self.graph.patterns.items():
                        for children in p2.children.values():
                            for child in children:
                                if isinstance(child, PatternNode) and child.id == best.id:
                                    name_node = p2.children.get("name", [None])[0]
                                    if name_node:
                                        source = name_node.value
                
                results.append({
                    "type": ntype_name,
                    "pattern_id": best.id,
                    "pattern": best,
                    "source": source,
                })
                used_ids.add(best.id)
        
        return results


class PatternComposer:
    """
    3. lépés: A kiválasztott minták összeillesztése egy koherens programmá.
    """
    
    def __init__(self, graph: HypergraphV2, generator: ConstructiveGenerator):
        self.graph = graph
        self.generator = generator
    
    def compose(self, patterns: list[dict], goal: str = "") -> Optional[str]:
        """
        Minták összeillesztése.
        
        Ha van szemantikusan talált FUNCTION_DEF, csak azt adjuk vissza.
        A többi pattern csak akkor kell, ha nincs teljes függvény.
        """
        if not patterns:
            return ""
        
        # 1. Van-e szemantikus kereséssel talált FUNCTION_DEF?
        func_pattern = None
        body_patterns = []
        for p in patterns:
            if p["type"] == "FUNCTION_DEF" and isinstance(p["pattern"], PatternNode):
                if func_pattern is None:
                    func_pattern = p
                else:
                    body_patterns.append(p)
            elif func_pattern is None:
                # Csak akkor gyűjtünk body mintákat, ha nincs FUNCTION_DEF
                body_patterns.append(p)
        
        if func_pattern:
            # Ha van FUNCTION_DEF, generáljuk és adjuk vissza
            code = self.generator.generate(func_pattern["pattern"])
            
            # Ha több FUNCTION_DEF is van, a másodikat is hozzáfűzhetjük
            if len(body_patterns) >= 1:
                extra = []
                for p in body_patterns[:2]:
                    extra.append(self.generator.generate(p["pattern"]))
                if extra:
                    code = code + "\n\n" + "\n\n".join(extra)
            
            return code
        
        # 2. Ha nincs FUNCTION_DEF, a body mintákból építünk
        return self._compose_flat(patterns)
    
    def _compose_with_function_text(self, func_pattern: dict,
                                    other_patterns: list[dict]) -> str:
        """Függvény + extra minták szöveg szintű összefűzése."""
        # Generáljuk a teljes függvényt
        func_code = self.generator.generate(func_pattern["pattern"])
        
        if not other_patterns:
            return func_code
        
        # Generáljuk a kiegészítő minták kódját
        extra_codes = []
        for p in other_patterns:
            code = self.generator.generate(p["pattern"])
            if code and code.strip():
                # 4 space indent hozzáadása
                indented = "    " + code.replace("\n", "\n    ")
                extra_codes.append(indented)
        
        if not extra_codes:
            return func_code
        
        # Keressük meg a függvény body végét (az utolsó return utáni sort)
        lines = func_code.split("\n")
        
        # Ha a függvény utolsó sora egy return, előtte szúrjuk be
        insert_pos = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith("#"):
                # Az utolsó nem-üres sor után szúrjuk be
                insert_pos = i + 1
                break
        
        # Beszúrás
        extra_block = "\n".join(extra_codes)
        result_lines = lines[:insert_pos] + [extra_block] + lines[insert_pos:]
        
        return "\n".join(result_lines)
    
    def _compose_flat(self, patterns: list[dict]) -> str:
        """Minták sorba rendezése (ha nincs FUNCTION_DEF keret)."""
        parts = []
        for p in patterns:
            code = self.generator.generate(p["pattern"])
            if code:
                parts.append(code)
        return "\n".join(parts)


class SynthesisEngineV2:
    """
    Teljes szintézis folyamat:
    1. Decompose → 2. Retrieve → 3. Compose → 4. Generate
    """
    
    def __init__(self, graph: HypergraphV2, semantics: SemanticIndex,
                 generator: ConstructiveGenerator):
        self.graph = graph
        self.semantics = semantics
        self.generator = generator
        
        self.decomposer = GoalDecomposer(graph, semantics)
        self.retriever = PatternRetriever(graph, semantics)
        self.composer = PatternComposer(graph, generator)
    
    def synthesize(self, goal: str, verbose: bool = False) -> str:
        """
        Teljes szintézis: cél → kód.
        
        1. Cél lebontása részmintákra
        2. Minták keresése
        3. Kompozíció
        4. Generálás
        """
        if verbose:
            print(f"[Synthesis] Cel: '{goal}'")
        
        # 1. Decompose
        needed_types = self.decomposer.decompose(goal)
        if verbose:
            print(f"[Synthesis] Szukseges tipusok: {needed_types}")
        
        # 1.5 Szemantikus keresés a FUNCION_DEF-re (pontosabb, mint a típus alapú)
        best_func_via_semantics = None
        if needed_types and "FUNCTION_DEF" in needed_types:
            sem_results = self.semantics.search_by_text(goal, top_k=5)
            for sr in sem_results:
                if sr['type'] == 'FUNCTION_DEF':
                    pattern = self.graph.patterns.get(sr['id'])
                    if pattern:
                        best_func_via_semantics = pattern
                        break
        
        # 2. Retrieve
        patterns = self.retriever.retrieve(needed_types, goal)
        if verbose:
            print(f"[Synthesis] Talalt mintak: {len(patterns)}")
            for p in patterns:
                src = f" (forras: {p['source']})" if p['source'] else ""
                print(f"  - {p['type']}: {p['pattern_id'][:8]}{src}")
        
        if not patterns:
            if verbose:
                print(f"[Synthesis] Nincs talalat.")
            return ""
        
        # 3. Compose — használjuk a szemantikus találatot, ha van
        if best_func_via_semantics:
            composed = self.generator.generate(best_func_via_semantics)
        else:
            composed = self.composer.compose(patterns, goal)
        
        # 4. Validálás
        try:
            compile(composed, '<synthesis>', 'exec')
            if verbose:
                print(f"[Synthesis] Valid Python!")
        except SyntaxError as e:
            if verbose:
                print(f"[Synthesis] Szintaxis hiba: {e}")
        
        return composed


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from dka import DKA
    
    dka = DKA()
    
    # Tanító kódok
    dka.learn('''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
''', source='bubble_sort')
    
    dka.learn('''
def fetch_user(user_id):
    import requests
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
''', source='fetch_user')
    
    dka.learn('''
def read_config(path):
    import json
    with open(path) as f:
        data = json.load(f)
    return data
''', source='read_config')
    
    dka.learn('''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
''', source='factorial')
    
    # Synthesis Engine
    engine = SynthesisEngineV2(dka.graph, dka.semantics, dka.generator)
    
    print("=== SZINTEZIS TESZTEK ===")
    print()
    
    tests = [
        "sort",
        "factorial",
        "read file",
        "api fetch",
        "search",
        "filter list",
        "count items",
    ]
    
    for test_goal in tests:
        print(f"--- '{test_goal}' ---")
        result = engine.synthesize(test_goal, verbose=True)
        print()
        if result:
            print(result[:200])
        else:
            print("  (nincs eredmeny)")
        print()
