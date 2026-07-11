"""
DKA Core — Semantic Layer (4. réteg)
======================================
A kód "jelentésének" rétege.

Probléma: a DKA látja a struktúrát (FOR_LOOP + COMPARISON + SWAP),
de nem tudja, hogy ez "buborék rendezés".

Megoldás: minden mintához hozzárendelünk szemantikus címkéket,
amik leírják, hogy MIT CSINÁL a kód, nem csak hogyan néz ki.

A szemantikus réteg:
1. Kivonatolja a kód "jelentését" (függvény neve, kommentek, pattern fingerprint)
2. Összeköti a fogalmakat a mintákkal ("sort" -> bubble_sort, quicksort)
3. Kereséskor a jelentés alapján talál mintákat (ne csak típus alapján)
4. Használat közben tanul: ha a "sort" keresés bubble_sort-ot ad, megerősíti a kapcsolatot
"""

from __future__ import annotations
import re
import json
from collections import defaultdict, Counter
from typing import Optional

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType,
)
from hypergraph_v2 import HypergraphV2


class SemanticExtractor:
    """
    Jelentés kivonatolása a kódból.
    
    Források:
    - Függvény nevek (camelCase, snake_case → fogalmakra bontás)
    - Változó nevek
    - Kommentek, docstring-ek
    - Ismert API minták (requests.get, json.load, etc.)
    - Pattern struktúra fingerprint
    """
    
    # Ismert API és könyvtár minták → szemantikus címkék
    KNOWN_PATTERNS = {
        "requests.get": ["api_call", "http_get", "data_fetching"],
        "requests.post": ["api_call", "http_post", "data_submission"],
        "json.load": ["serialization", "data_parsing"],
        "json.dump": ["serialization", "data_writing"],
        "open": ["file_io", "file_read", "file_write"],
        "print": ["output", "logging"],
        "range": ["iteration", "sequence_generation"],
        "len": ["size_check", "length"],
        "sorted": ["sorting", "ordering"],
        "max": ["maximum", "aggregation"],
        "min": ["minimum", "aggregation"],
        "sum": ["summation", "aggregation"],
        ".append": ["list_operation", "mutation"],
        ".pop": ["list_operation", "removal"],
        ".sort": ["sorting", "inplace_sort"],
        ".join": ["string_operation", "concatenation"],
        ".split": ["string_operation", "splitting"],
        ".strip": ["string_operation", "cleaning"],
        ".upper": ["string_operation", "case_conversion"],
        ".lower": ["string_operation", "case_conversion"],
        ".get": ["dict_access", "safe_access"],
    }
    
    # Gyakori függvény név előtagok → szemantikus címkék
    NAME_PREFIXES = {
        "get": ["access", "retrieval", "query"],
        "set": ["mutation", "configuration", "update"],
        "is": ["check", "validation", "boolean_query"],
        "has": ["check", "ownership", "existence"],
        "find": ["search", "lookup", "discovery"],
        "search": ["search", "lookup"],
        "create": ["creation", "instantiation", "factory"],
        "make": ["creation", "construction", "factory"],
        "build": ["creation", "construction"],
        "delete": ["deletion", "removal", "destruction"],
        "remove": ["deletion", "removal"],
        "update": ["mutation", "update", "modification"],
        "save": ["persistence", "storage", "serialization"],
        "load": ["loading", "deserialization", "retrieval"],
        "read": ["loading", "file_read", "input"],
        "write": ["persistence", "file_write", "output"],
        "parse": ["parsing", "interpretation", "analysis"],
        "convert": ["conversion", "transformation"],
        "transform": ["transformation", "conversion"],
        "validate": ["validation", "checking"],
        "check": ["checking", "validation"],
        "compute": ["computation", "calculation"],
        "calculate": ["computation", "calculation"],
        "sort": ["sorting", "ordering"],
        "filter": ["filtering", "selection"],
        "map": ["transformation", "mapping"],
        "reduce": ["reduction", "aggregation"],
        "init": ["initialization", "construction"],
        "reset": ["reset", "initialization"],
        "format": ["formatting", "transformation"],
        "encode": ["encoding", "serialization"],
        "decode": ["decoding", "deserialization"],
        "generate": ["generation", "creation"],
        "process": ["processing", "handling"],
        "handle": ["handling", "processing"],
        "render": ["rendering", "presentation"],
        "connect": ["connection", "networking"],
        "disconnect": ["disconnection"],
        "login": ["authentication", "access"],
        "logout": ["authentication", "signout"],
        "register": ["registration", "creation"],
        "notify": ["notification", "messaging"],
        "send": ["messaging", "transmission"],
        "receive": ["messaging", "reception"],
        "fetch": ["retrieval", "api_call", "data_fetching"],
        "upload": ["upload", "transmission"],
        "download": ["download", "retrieval"],
        "merge": ["merging", "combination"],
        "split": ["splitting", "division"],
        "count": ["counting", "aggregation"],
        "list": ["listing", "enumeration"],
        "print": ["printing", "output"],
        "display": ["display", "presentation"],
        "show": ["display", "presentation"],
        "run": ["execution", "invocation"],
        "execute": ["execution", "invocation"],
        "start": ["startup", "initialization"],
        "stop": ["shutdown", "termination"],
        "close": ["shutdown", "closure"],
        "clean": ["cleaning", "sanitization"],
        "sanitize": ["sanitization", "cleaning"],
        "escape": ["escaping", "sanitization"],
    }
    
    # Típus-alapú szemantikus címkék
    TYPE_SEMANTICS = {
        NodeType.FUNCTION_CALL: ["invocation", "call"],
        NodeType.FOR_LOOP: ["iteration", "loop", "repetition"],
        NodeType.WHILE_LOOP: ["iteration", "conditional_loop", "repetition"],
        NodeType.IF_STATEMENT: ["conditional", "branching", "decision"],
        NodeType.RETURN_STMT: ["return", "output", "exit"],
        NodeType.ASSIGNMENT: ["assignment", "storage"],
        NodeType.COMPARISON: ["comparison", "checking"],
        NodeType.BINARY_OP: ["arithmetic", "operation"],
        NodeType.IMPORT: ["import", "dependency", "module_loading"],
        NodeType.FUNCTION_DEF: ["function_definition", "declaration"],
        NodeType.CLASS_DEF: ["class_definition", "declaration", "object_oriented"],
        NodeType.ATTRIBUTE_ACCESS: ["attribute_access", "property_access"],
        NodeType.INDEX_ACCESS: ["index_access", "collection_access"],
        NodeType.LIST_COMP: ["list_comprehension", "functional", "transformation"],
    }
    
    def __init__(self):
        pass
    
    def extract_semantics(self, node: BaseNode) -> list[str]:
        """
        Egy nódus szemantikus címkéinek kinyerése.
        Visszaad egy listát a kapcsolódó fogalmakról.
        """
        tags = []
        
        if isinstance(node, PatternNode):
            # Típus alapú címkék
            tags.extend(self.TYPE_SEMANTICS.get(node.type, []))
            
            # Gyerekek vizsgálata
            tags.extend(self._analyze_children(node))
        
        elif isinstance(node, PrimitiveNode):
            if node.type == NodeType.VARIABLE:
                # Változónév → fogalmak
                tags.extend(self._parse_name(node.value))
        
        return list(set(tags))  # Egyedi címkék
    
    def extract_function_semantics(self, func_node: PatternNode) -> dict:
        """
        Teljes függvény szemantikus elemzése.
        Visszaadja:
        - tags: a függvény fogalmi címkéi
        - patterns: a függvényt alkotó fontosabb minták
        - name_meaning: a függvénynév jelentése
        - complexity_budget: mennyire komplex (minta mélység alapján)
        """
        if func_node.type != NodeType.FUNCTION_DEF:
            return {"tags": [], "patterns": [], "name_meaning": "", "complexity": 0}
        
        tags = []
        patterns_found = []
        
        # 1. Függvénynév elemzése
        name_node = func_node.children.get("name", [None])[0]
        if name_node:
            name_tags = self._parse_name(name_node.value)
            tags.extend(name_tags)
        
        # 2. Paraméterek elemzése
        params = func_node.children.get("params", [])
        for p in params:
            param_tags = self._parse_name(p.value)
            tags.extend([f"param_{t}" for t in param_tags])
        
        # 3. Test-ben lévő minták elemzése
        body = func_node.children.get("body", [])
        for block in body:
            if isinstance(block, PatternNode):
                patterns_found.append(block.type.name)
                tags.extend(self._analyze_pattern_deep(block))
        
        # 4. Gyakori kombinációk felismerése
        pattern_types = Counter(patterns_found)
        
        # Rekurzió detektálása
        if self._detect_recursion(func_node):
            tags.append("recursive")
        
        # IO műveletek
        if "open" in str(func_node):
            tags.append("file_operation")
        
        # API hívások
        if "requests.get" in str(func_node) or "requests.post" in str(func_node):
            tags.append("api_call")
        
        return {
            "tags": list(set(tags)),
            "patterns": dict(pattern_types),
            "complexity": len(patterns_found),
        }
    
    def _analyze_children(self, node: PatternNode) -> list[str]:
        """Gyerek nódusokból szemantikus címkék."""
        tags = []
        for role, children in node.children.items():
            for child in children:
                if isinstance(child, PatternNode):
                    tags.extend(self.TYPE_SEMANTICS.get(child.type, []))
                elif isinstance(child, PrimitiveNode):
                    if child.type == NodeType.VARIABLE:
                        # Ismert API/pattern név?
                        if child.value in self.KNOWN_PATTERNS:
                            tags.extend(self.KNOWN_PATTERNS[child.value])
        return tags
    
    def _analyze_pattern_deep(self, node: BaseNode, depth: int = 0) -> list[str]:
        """Rekurzív minta elemzés (mélyebbre is néz)."""
        if depth > 5:
            return []
        
        tags = []
        
        if isinstance(node, PatternNode):
            tags.extend(self.TYPE_SEMANTICS.get(node.type, []))
            for children in node.children.values():
                for child in children:
                    tags.extend(self._analyze_pattern_deep(child, depth + 1))
        
        elif isinstance(node, PrimitiveNode):
            if node.type == NodeType.VARIABLE:
                if node.value in self.KNOWN_PATTERNS:
                    tags.extend(self.KNOWN_PATTERNS[node.value])
                # Parse variable names for concepts
                tags.extend(self._parse_name(node.value))
                # Metódus hívások (pl. .append, .sort)
                if node.value.startswith("."):
                    method = node.value
                    if method in self.KNOWN_PATTERNS:
                        tags.extend(self.KNOWN_PATTERNS[method])
        
        return tags
    
    def _parse_name(self, name: str) -> list[str]:
        """Függvény/változónév → fogalmi címkék."""
        tags = []
        
        # snake_case bontás
        parts = name.split("_")
        for part in parts:
            # camelCase bontás
            sub_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', part)
            for sub in sub_parts:
                sub_lower = sub.lower()
                tags.append(sub_lower)
                # Ismert előtag?
                if sub_lower in self.NAME_PREFIXES:
                    tags.extend(self.NAME_PREFIXES[sub_lower])
        
        # Rövidítések felismerése
        name_lower = name.lower()
        known = {
            "fib": ["fibonacci", "recursive", "mathematical"],
            "fact": ["factorial", "recursive", "mathematical"],
            "gcd": ["mathematical", "divisor"],
            "lcm": ["mathematical", "multiple"],
            "arr": ["array", "collection"],
            "str": ["string"],
            "int": ["integer"],
            "val": ["value"],
            "obj": ["object"],
            "ctx": ["context"],
            "req": ["request"],
            "resp": ["response"],
            "calc": ["calculation"],
            "config": ["configuration"],
            "conf": ["configuration"],
            "temp": ["temporary"],
            "tmp": ["temporary"],
            "max": ["maximum"],
            "min": ["minimum"],
            "avg": ["average"],
            "init": ["initialization"],
            "prev": ["previous"],
            "next": ["next"],
            "curr": ["current"],
            "idx": ["index"],
            "msg": ["message"],
            "db": ["database"],
            "api": ["api"],
            "url": ["url", "web"],
            "html": ["html", "web"],
            "csv": ["csv", "tabular"],
            "json": ["json", "serialized"],
            "xml": ["xml", "serialized"],
            "auth": ["authentication"],
        }
        
        if name_lower in known:
            tags.extend(known[name_lower])
        
        return list(set(tags))
    
    def _detect_recursion(self, func_node: PatternNode) -> bool:
        """Rekurzió detektálása: a függvény meghívja saját magát?"""
        name_node = func_node.children.get("name", [None])[0]
        if not name_node:
            return False
        
        func_name = name_node.value
        
        # Keressünk FUNCTION_CALL-okat a body-ban
        body = func_node.children.get("body", [])
        return self._search_for_call(body, func_name)
    
    def _search_for_call(self, nodes: list, target_name: str) -> bool:
        for node in nodes:
            if isinstance(node, PatternNode):
                if node.type == NodeType.FUNCTION_CALL:
                    func = node.children.get("func", [None])[0]
                    if func and hasattr(func, 'value') and func.value == target_name:
                        return True
                # Rekurzív keresés a gyerekekben
                for children in node.children.values():
                    if self._search_for_call(children, target_name):
                        return True
        return False


class SemanticIndex:
    """
    Szemantikus Index.
    
    Összeköti a fogalmakat (pl. "sort", "recursive", "api") 
    a gráfban lévő mintákkal.
    
    Kétirányú index:
    - concept → pattern_ids (mely minták kapcsolódnak egy fogalomhoz)
    - pattern_id → concepts (milyen fogalmak kapcsolódnak egy mintához)
    """
    
    def __init__(self, graph: HypergraphV2):
        self.graph = graph
        self.extractor = SemanticExtractor()
        
        # concept → set(pattern_id)
        self.concept_index: dict[str, set[str]] = defaultdict(set)
        # pattern_id → set(concept)
        self.pattern_semantics: dict[str, set[str]] = defaultdict(set)
        
        # Használati statisztika: concept → hányszor használtuk
        self.concept_usage: Counter = Counter()
        
        # Keresési előzmény: concept → pattern_id → sikeresség
        self.search_history: dict[str, Counter] = defaultdict(Counter)
    
    def index_pattern(self, pid: str):
        """Egy minta indexelése a szemantikus rétegbe."""
        pattern = self.graph.patterns.get(pid)
        if not pattern:
            return
        
        concepts = set()
        
        # Alap címkék
        concepts.update(self.extractor.extract_semantics(pattern))
        
        # Ha FUNCTION_DEF, extra elemezés
        if pattern.type == NodeType.FUNCTION_DEF:
            semantics = self.extractor.extract_function_semantics(pattern)
            concepts.update(semantics["tags"])
        
        # Tárolás
        self.pattern_semantics[pid] = concepts
        for concept in concepts:
            self.concept_index[concept].add(pid)
    
    def index_all(self):
        """Összes minta indexelése."""
        for pid in list(self.graph.patterns.keys()):
            self.index_pattern(pid)
    
    def index_new(self):
        """Csak az új, még nem indexelt minták indexelése."""
        for pid in list(self.graph.patterns.keys()):
            if pid not in self.pattern_semantics:
                self.index_pattern(pid)
    
    def search(self, concept: str, top_k: int = 5) -> list[dict]:
        """
        Keresés fogalom alapján.
        
        concept: "sort", "recursive", "api", "file_io", stb.
        Visszaadja a kapcsolódó mintákat relevancia sorrendben.
        """
        self.concept_usage[concept] += 1
        
        # Pontos fogalom keresés
        results = []
        direct_ids = self.concept_index.get(concept, set())
        
        for pid in direct_ids:
            pattern = self.graph.patterns.get(pid)
            if not pattern:
                continue
            
            # Név lekérése (ha FUNCTION_DEF)
            name = ""
            if pattern.type == NodeType.FUNCTION_DEF:
                name_node = pattern.children.get("name", [None])[0]
                if name_node:
                    name = name_node.value
            
            # Relevancia: hányszor használtuk ezt a találatot korábban
            relevance = self.search_history[concept].get(pid, 0) + 1
            
            results.append({
                "id": pid,
                "type": pattern.type.name,
                "name": name,
                "concepts": list(self.pattern_semantics.get(pid, set())),
                "relevance": relevance,
            })
        
        # Rendezés relevancia szerint
        results.sort(key=lambda r: r["relevance"], reverse=True)
        
        # Előzmény rögzítése
        for r in results:
            self.search_history[concept][r["id"]] += 1
        
        return results[:top_k]
    
    def search_by_text(self, text: str, top_k: int = 5) -> list[dict]:
        """
        Szabad szöveges keresés.
        A szöveget fogalmakra bontja, majd az összes fogalom alapján keres.
        Pontozás: minél több fogalom egyezik, annál magasabb a pont.
        """
        concepts = set()
        text_lower = text.lower()
        words = re.findall(r'[a-zA-Z_]\w*', text_lower)
        
        for word in words:
            concepts.update(self.extractor._parse_name(word))
            if word in self.concept_index:
                concepts.add(word)
        
        if not concepts:
            return []
        
        # Pontozás: minden mintára számoljuk, hány fogalom egyezik
        pattern_scores: dict[str, float] = {}
        for concept in concepts:
            for pid in self.concept_index.get(concept, set()):
                pattern_scores[pid] = pattern_scores.get(pid, 0) + 1.0
        
        if not pattern_scores:
            return []
        
        # Relatív pontszám: egyező fogalmak / összes fogalom
        total_concepts = len(concepts)
        
        results = []
        for pid, score in pattern_scores.items():
            pattern = self.graph.patterns.get(pid)
            if not pattern:
                continue
            
            # Pont: egyező fogalmak / összes fogalom (mennyire fedi le a keresést)
            coverage = score / total_concepts
            
            # Bónusz: a minta saját fogalmainak hány %-a egyezik
            own_concepts = self.pattern_semantics.get(pid, set())
            if own_concepts:
                overlap = len(set(concepts) & own_concepts)
                precision = overlap / len(own_concepts)
            else:
                precision = 0
            
            # Kombinált pont: coverage + precision
            combined = coverage * 0.6 + precision * 0.4
            
            name = ""
            if pattern.type == NodeType.FUNCTION_DEF:
                name_node = pattern.children.get("name", [None])[0]
                if name_node:
                    name = name_node.value
            
            # === NÉVEGYEZÉS BÓNUSZ ===
            # Ha a függvénynév szavai substring-ként szerepelnek a goal-ban
            name_bonus = 0.0
            if name:
                name_words = name.lower().split('_')
                for nw in name_words:
                    for gw in words:
                        if nw in gw or gw in nw:
                            name_bonus += 0.1
                            break
                # Extra bónusz teljes név egyezésre
                goal_set = set(words)
                name_set = set(name_words)
                exact_overlap = len(goal_set & name_set)
                if exact_overlap >= 2 and exact_overlap == len(name_words):
                    name_bonus += 0.2
                elif exact_overlap >= 2 or (exact_overlap == len(name_words) and exact_overlap > 0):
                    name_bonus += 0.1
            
            # Használati előzmény bónusz
            history_bonus = sum(
                self.search_history.get(c, {}).get(pid, 0) * 0.1
                for c in concepts
            )
            
            relevance = combined + history_bonus + name_bonus
            
            results.append({
                "id": pid,
                "type": pattern.type.name,
                "name": name,
                "concepts": list(self.pattern_semantics.get(pid, set())),
                "relevance": round(relevance, 3),
            })
        
        results.sort(key=lambda r: r["relevance"], reverse=True)
        
        # Előzmény rögzítése
        for r in results[:top_k]:
            for concept in concepts:
                self.search_history[concept][r["id"]] += 1
        
        return results[:top_k]
    
    def learn_from_feedback(self, query: str, pattern_id: str, success: bool):
        """
        Tanulás a felhasználói visszajelzésből.
        Ha a keresés sikeres volt, erősíti a kapcsolatot.
        """
        if success:
            self.search_history[query][pattern_id] += 2  # Extra pont
        else:
            self.search_history[query][pattern_id] -= 1  # Gyengítés
    
    def get_concept_cloud(self, top_k: int = 20) -> list[tuple[str, int]]:
        """Leggyakoribb fogalmak listája."""
        concepts = self.concept_usage.most_common(top_k)
        if not concepts:
            # Ha még nincs használat, a legtöbb mintához kapcsolódó fogalmak
            concept_counts = [(c, len(ids)) for c, ids in self.concept_index.items()]
            concept_counts.sort(key=lambda x: -x[1])
            concepts = concept_counts[:top_k]
        return concepts
    
    def stats(self) -> dict:
        return {
            "total_concepts": len(self.concept_index),
            "total_indexed_patterns": len(self.pattern_semantics),
            "total_searches": sum(self.concept_usage.values()),
            "total_history_entries": len(self.search_history),
        }


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from grammar_parser import GrammarParser
    from hypergraph_v2 import HypergraphV2
    
    parser = GrammarParser()
    graph = HypergraphV2()
    
    # Tanító kód
    samples = '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def fetch_user(user_id):
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
    
    nodes = parser.parse(samples)
    graph.ingest_pattern_tree(nodes)
    
    # Szemantikus index építés
    sidx = SemanticIndex(graph)
    sidx.index_all()
    
    print("=== SZEMANTIKUS INDEX ===")
    stats = sidx.stats()
    print(f"  Fogalmak: {stats['total_concepts']}")
    print(f"  Indexelt mintak: {stats['total_indexed_patterns']}")
    
    print("\n=== LEGGYAKORIBB FOGALMAK ===")
    for concept, count in sidx.get_concept_cloud(10):
        print(f"  {concept}: {count}")
    
    print("\n=== KERESES: 'sort' ===")
    results = sidx.search("sort")
    for r in results:
        print(f"  {r['type']}: {r['name']} (relevance: {r['relevance']})")
    
    print("\n=== KERESES: 'api' ===")
    results = sidx.search("api")
    for r in results:
        print(f"  {r['type']}: {r['name']} (relevance: {r['relevance']})")
    
    print("\n=== KERESES: 'recursive' ===")
    results = sidx.search("recursive")
    for r in results:
        print(f"  {r['type']}: {r['name']} (relevance: {r['relevance']})")
    
    print("\n=== SZABAD SZOVEGES KERESES: 'sort numbers' ===")
    results = sidx.search_by_text("sort numbers")
    for r in results:
        print(f"  {r['type']}: {r['name']} (relevance: {r['relevance']})")
    
    print("\n=== SZABAD SZOVEGES KERESES: 'read data from url' ===")
    results = sidx.search_by_text("read data from url")
    for r in results:
        print(f"  {r['type']}: {r['name']} (relevance: {r['relevance']})")
    
    print("\n=== SZABAD SZOVEGES KERESES: 'calculate factorial' ===")
    results = sidx.search_by_text("calculate factorial")
    for r in results:
        print(f"  {r['type']}: {r['name']} (relevance: {r['relevance']})")
