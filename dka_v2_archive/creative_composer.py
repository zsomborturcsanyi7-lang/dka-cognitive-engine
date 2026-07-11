"""
DKA Core — Creative Composer
==============================
Új kód generálása meglévő minták kreatív kombinálásával.

Probléma: a DKA tud bubble_sort-ot (ciklus + összehasonlítás + csere)
és read_config-ot (fájl I/O + JSON). De nem tud belőlük "fájlkeresőt" csinálni.

Megoldás: Pattern → Analógia → Adaptáció → Generálás

1. Template kiválasztása (pl. FOR_LOOP struktúra)
2. Tartalom kiválasztása (pl. IF_STATEMENT + FILE_READ)
3. Változónevek összehangolása
4. Generálás

A kulcs: nem az egész függvényt klónozzuk, hanem a SZEREPEKET.
"""

from __future__ import annotations
from typing import Optional
from collections import Counter
import re

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain, Role,
)
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from pattern_intel import PatternIntelligence


class VariableMapper:
    """
    Változónév összehangoló.
    
    Ha a template "arr"-t használ, a content meg "data"-t,
    akkor ezt feloldja: mindkettő ugyanazt a változót jelenti.
    """
    
    def __init__(self):
        self.known_synonyms = {
            "arr": ["data", "list", "items", "array", "seq", "sequence"],
            "data": ["arr", "list", "items", "array", "seq", "content"],
            "list": ["data", "arr", "items", "array", "seq"],
            "items": ["data", "arr", "list", "array"],
            "n": ["len", "size", "length", "count", "num"],
            "i": ["j", "k", "idx", "index", "pos", "counter"],
            "j": ["i", "k", "idx", "index"],
            "x": ["elem", "item", "val", "value", "element"],
            "elem": ["x", "item", "val", "value", "element"],
            "item": ["x", "elem", "val", "value"],
            "val": ["x", "elem", "item", "value"],
            "result": ["res", "output", "ret", "out"],
            "res": ["result", "output", "ret"],
            "path": ["filepath", "filename", "fname", "p"],
            "text": ["str", "s", "content", "data"],
            "s": ["text", "str", "content", "data"],
            "key": ["k", "keyword", "query"],
            "k": ["key", "keyword"],
            "f": ["file", "fh", "fp", "handle"],
            "file": ["f", "fh", "fp"],
        }
        
        self._mapped_vars: dict[str, str] = {}
    
    def map_variable(self, template_var: str, content_var: str) -> str:
        """Két változónév összehangolása. Visszaadja a közös nevet."""
        # Ha ugyanaz, nincs dolgunk
        if template_var == content_var:
            return template_var
        
        # Ismert szinonima?
        if content_var in self.known_synonyms.get(template_var, []):
            return template_var
        
        if template_var in self.known_synonyms.get(content_var, []):
            return content_var
        
        # Ha a template változó rövidebb, általában azt használjuk
        if len(template_var) <= len(content_var):
            return template_var
        return content_var
    
    def adapt_pattern(self, node: BaseNode, var_map: dict[str, str]) -> BaseNode:
        """Változónevek átírása egy mintában a var_map alapján."""
        if isinstance(node, PrimitiveNode):
            if node.type == NodeType.VARIABLE and node.value in var_map:
                node.value = var_map[node.value]
                node.fingerprints.add("adapted")
            return node
        
        elif isinstance(node, PatternNode):
            for role, children in node.children.items():
                node.children[role] = [
                    self.adapt_pattern(child, var_map) for child in children
                ]
            return node
        
        return node


class TemplateLibrary:
    """
    Ismert kód "sablonok" — nem a teljes függvény, hanem a STRUKTÚRA.
    
    Minden sablon leírja:
    - Milyen szerepkörökből áll
    - Milyen változókat használ
    - Mit vár a környezetétől
    """
    
    def __init__(self, graph: HypergraphV2):
        self.graph = graph
    
    def get_template(self, ntype: NodeType, pattern_id: str = None) -> Optional[dict]:
        """
        Egy minta "sablonjának" lekérése.
        A sablon tartalmazza a struktúrát, de a konkrét változónevek nélkül.
        """
        if pattern_id:
            pattern = self.graph.patterns.get(pattern_id)
        else:
            patterns = self.graph.find_by_type(ntype)
            pattern = patterns[0] if patterns else None
        
        if not pattern or not isinstance(pattern, PatternNode):
            return None
        
        # Változók kinyerése
        variables = self._extract_variables(pattern)
        
        # Struktúra fingerprint
        structure = self._get_structure_fingerprint(pattern)
        
        return {
            "pattern": pattern,
            "type": ntype.name,
            "variables": variables,
            "structure": structure,
        }
    
    def _extract_variables(self, node: BaseNode, depth: int = 0) -> set[str]:
        """Változónevek kinyerése egy mintából."""
        if depth > 10:
            return set()
        
        vars_found = set()
        
        if isinstance(node, PrimitiveNode):
            if node.type == NodeType.VARIABLE and node.role != "name":
                vars_found.add(node.value)
        
        elif isinstance(node, PatternNode):
            for children in node.children.values():
                for child in children:
                    vars_found.update(self._extract_variables(child, depth + 1))
        
        return vars_found


class CreativeComposer:
    """
    Kreatív kompozíció: két vagy több minta összeolvasztása új kóddá.
    
    Folyamat:
    1. Template kiválasztása (FOR_LOOP struktúra)
    2. Tartalom hozzáadása (IF_STATEMENT a body-ba)
    3. Változónevek összehangolása
    4. Generálás
    
    Példa: bubble_sort FOR_LOOP + read_config OPEN
    → új függvény: for line in file: if keyword in line: ...
    """
    
    def __init__(self, graph: HypergraphV2, generator: ConstructiveGenerator,
                 semantics: SemanticIndex):
        self.graph = graph
        self.generator = generator
        self.semantics = semantics
        self.mapper = VariableMapper()
        self.templates = TemplateLibrary(graph)
        self.pattern_intel = PatternIntelligence(graph)
    
    def compose(self, goal: str, 
                template_type: NodeType = None,
                content_types: list[NodeType] = None) -> Optional[str]:
        """
        Kreatív kompozíció egy cél leírásból.
        
        goal: "search in file" vagy "count words" stb.
        template_type: a fő struktúra típusa (pl. FOR_LOOP)
        content_types: a body-ban használt minták típusai
        """
        # 1. Szemantikus keresés a legjobb template-hez
        template, content_patterns = self._find_patterns(goal, template_type, content_types)
        
        if not template:
            return None
        
        # 2. Ha van sablon és tartalom, próbáljuk meg összeolvasztani
        if content_patterns and isinstance(template, PatternNode):
            return self._merge_into_template(template, content_patterns, goal)
        
        # 3. Ha nincs tartalom, csak a template-et generáljuk
        return self.generator.generate(template)
    
    def _find_patterns(self, goal: str, 
                       template_type: NodeType,
                       content_types: list[NodeType]) -> tuple:
        """Megkeresi a legjobb template és tartalom mintákat."""
        template = None
        contents = []
        
        # Szemantikus keresés
        sem_results = self.semantics.search_by_text(goal, top_k=5)
        
        # Template keresés
        if template_type:
            templates = self.graph.find_by_type(template_type)
            if templates:
                template = templates[0]
        
        # Ha nincs explicit template, a legjobb FUNCTION_DEF-et használjuk
        if not template:
            for sr in sem_results:
                if sr['type'] == 'FUNCTION_DEF':
                    pattern = self.graph.patterns.get(sr['id'])
                    if pattern:
                        template = pattern
                        break
        
        # Tartalom minták
        if content_types:
            for ct in content_types:
                candidates = self.graph.find_by_type(ct)
                if candidates:
                    contents.append(candidates[0])
        
        # Ha nincs content_types, a szemantikus keresésből szedünk
        if not contents:
            for sr in sem_results:
                if sr['type'] != 'FUNCTION_DEF' and sr['id'] not in [id for id in [p.id if hasattr(p, 'id') else None for p in [template]]]:
                    pattern = self.graph.patterns.get(sr['id'])
                    if pattern:
                        contents.append(pattern)
        
        return template, contents
    
    def _has_return(self, node: BaseNode) -> bool:
        """Ellenőrzi, hogy egy nódus tartalmaz-e RETURN_STMT-et."""
        if isinstance(node, PatternNode):
            if node.type == NodeType.RETURN_STMT:
                return True
            for children in node.children.values():
                for child in children:
                    if self._has_return(child):
                        return True
        return False
    
    def _merge_into_template(self, template: PatternNode,
                             content_patterns: list[PatternNode],
                             goal: str) -> str:
        """
        Tartalom minták beillesztése a template-be.
        Ha a template nem FUNCTION_DEF és van return, becsomagolja.
        """
        from inference_engine_v2 import InferenceEngineV2
        engine = InferenceEngineV2(self.graph)
        
        # Ellenőrizzük, hogy kell-e FUNCTION_DEF wrapper
        needs_wrapper = False
        has_return = False
        for content in content_patterns:
            if isinstance(content, PatternNode) and content.type == NodeType.RETURN_STMT:
                has_return = True
            # Rekurzív keresés return-ra
            if self._has_return(content):
                has_return = True
        
        if has_return and not isinstance(template, PatternNode) or (
            isinstance(template, PatternNode) and template.type != NodeType.FUNCTION_DEF):
            needs_wrapper = True
    
        # Klónozzuk a template-et
        clone = engine._clone_pattern(template)
        
        # Ha kell wrapper, hozzunk létre egy FUNCTION_DEF-et
        if needs_wrapper:
            func_wrapper = PatternNode(
                type=NodeType.FUNCTION_DEF,
                domain=template.domain if hasattr(template, 'domain') else DataDomain.GENERAL,
                roles={
                    "name": Role("name", cardinality=(1, 1)),
                    "params": Role("params", cardinality=(0, None)),
                    "body": Role("body", cardinality=(1, 1)),
                }
            )
            
            # Paraméterek kinyerése az elemzésből
            all_params = set()
            all_targets = set()
            for c in [template] + content_patterns:
                analysis = self.pattern_intel.analyze(c)
                all_params.update(analysis["parameters"])
                # Assignment target-eket ne tegyük paraméterré
                all_targets.update(
                    self.pattern_intel.analyzer._find_assignment_targets(c)
                )
            
            # Tényleges paraméterek: undefined változók, amik NEM assignment target-ek
            actual_params = all_params - all_targets
            
            func_wrapper.children["name"] = [
                PrimitiveNode(type=NodeType.VARIABLE, value="process", role="name")
            ]
            func_wrapper.children["params"] = [
                PrimitiveNode(type=NodeType.VARIABLE, value=p, role="param")
                for p in sorted(actual_params)
            ]
            
            body_block = PatternNode(
                type=NodeType.BLOCK,
                roles={"statements": Role("statements", cardinality=(0, None))}
            )
            
            body_statements = []
            
            # Akkumulátorok inicializálása
            all_accumulators = set()
            for c in [template] + content_patterns:
                analysis = self.pattern_intel.analyze(c)
                for acc in analysis.get("needs_init", []):
                    if acc not in all_params:
                        init_node = PatternNode(
                            type=NodeType.ASSIGNMENT,
                            roles={
                                "targets": Role("targets", cardinality=(1, None)),
                                "value": Role("value", cardinality=(1, 1)),
                            }
                        )
                        init_node.children["targets"] = [
                            PrimitiveNode(type=NodeType.VARIABLE, value=acc, role="target")
                        ]
                        init_node.children["value"] = [
                            PrimitiveNode(type=NodeType.LITERAL, value="0")
                        ]
                        body_statements.append(init_node)
                        all_accumulators.add(acc)
            
            body_statements.append(clone)
            for content in content_patterns:
                body_statements.append(engine._clone_pattern(content))
            
            body_block.children["statements"] = body_statements
            func_wrapper.children["body"] = [body_block]
            clone = func_wrapper
            return self.generator.generate(clone)
        
        # Keressük a body blokkot
        body_roles = ["body", "body", "statements"]
        target_body = None
        for role in body_roles:
            bodies = clone.children.get(role, [])
            if bodies and isinstance(bodies[0], PatternNode):
                target_body = bodies[0]
                break
        
        if not target_body:
            return self.generator.generate(clone)
        
        # Ha a body-nak van "statements" szerepköre, oda tesszük
        stmts = target_body.children.get("statements", [])
        
        # Tartalom hozzáadása (klónozva)
        for content in content_patterns:
            cloned_content = engine._clone_pattern(content)
            
            # Változók összehangolása — csak azonos szerepkörben
            template_vars = self.templates._extract_variables(template)
            content_vars = self.templates._extract_variables(content)
            
            var_map = {}
            for cv in content_vars:
                if cv in template_vars:
                    continue  # Már ugyanaz a név, nincs dolgunk
                
                # Keressük a legjobb template változót
                best_match = None
                for tv in template_vars:
                    # Csak akkor térképezünk, ha értelmes a kapcsolat
                    if cv != tv and len(cv) > 1 and len(tv) > 1:
                        # Pl. "data" → "arr" ha szinonimák
                        mapped = self.mapper.map_variable(tv, cv)
                        if mapped == tv:
                            best_match = tv
                        elif mapped == cv:
                            best_match = cv
                
                if best_match and best_match != cv:
                    var_map[cv] = best_match
            
            if var_map:
                cloned_content = self.mapper.adapt_pattern(cloned_content, var_map)
            
            stmts.append(cloned_content)
        
        target_body.children["statements"] = stmts
        
        return self.generator.generate(clone)
    
    def creative_synthesize(self, goal: str) -> str:
        """
        Teljes kreatív szintézis: cél → új kód.
        Képes meglévő mintákból új kombinációkat létrehozni.
        """
        # 1. Cél elemzése: milyen típusú template kell?
        goal_lower = goal.lower()
        
        # Template típus detektálás
        template_type = None
        if any(w in goal_lower for w in ["loop", "iterate", "each", "every", "for"]):
            template_type = NodeType.FOR_LOOP
        elif any(w in goal_lower for w in ["while", "until"]):
            template_type = NodeType.WHILE_LOOP
        elif any(w in goal_lower for w in ["if", "check", "condition", "when"]):
            template_type = NodeType.IF_STATEMENT
        
        # Ha nincs explicit template, szemantikus keresés a függvényre
        if not template_type:
            sem_results = self.semantics.search_by_text(goal, top_k=3)
            for sr in sem_results:
                if sr['type'] == 'FUNCTION_DEF':
                    pattern = self.graph.patterns.get(sr['id'])
                    if pattern:
                        return self.generator.generate(pattern)
        
        # Tartalom típusok detektálás
        content_types = []
        if any(w in goal_lower for w in ["file", "read", "open"]):
            content_types.append(NodeType.FUNCTION_CALL)
        if any(w in goal_lower for w in ["compare", "search", "find", "check", "filter"]):
            content_types.append(NodeType.COMPARISON)
        if any(w in goal_lower for w in ["return"]):
            content_types.append(NodeType.RETURN_STMT)
        
        # 2. Kompozíció
        result = self.compose(goal, template_type, content_types if content_types else None)
        
        if result:
            return result
        
        # 3. Fallback: ha nincs kreatív találat, sima szintézis
        return None


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from dka import DKA
    
    dka = DKA()
    
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
    
    dka.learn('''
def count_items(items):
    count = 0
    for item in items:
        count += 1
    return count
''', source='count_items')
    
    composer = CreativeComposer(dka.graph, dka.generator, dka.semantics)
    
    print("=== KREATÍV KOMPOZÍCIÓ TESZT ===")
    
    # 1. Keressünk FOR_LOOP-ot és adjunk hozzá IF_STATEMENT-et
    print("\n--- FOR_LOOP + IF_STATEMENT ---")
    for_loops = dka.graph.find_by_type(NodeType.FOR_LOOP)
    if_stmt = dka.graph.find_by_type(NodeType.IF_STATEMENT)
    
    if for_loops and if_stmt:
        result = composer._merge_into_template(for_loops[0], [if_stmt[0]], "loop with condition")
        print(result)
        if result:
            try:
                compile(result, '<test>', 'exec')
                print("  [OK] Valid Python!")
            except SyntaxError as e:
                print(f"  [HIBA] {e}")
    
    # 2. Kreatív szintézis: "search in file"
    print("\n--- creative_synthesize('search in file') ---")
    result = composer.creative_synthesize("search in file")
    if result:
        print(result)
        try:
            compile(result, '<test>', 'exec')
            print("  [OK] Valid Python!")
        except SyntaxError as e:
            print(f"  [HIBA] {e}")
    else:
        print("  (nincs kreatív találat)")
    
    # 3. Kreatív szintézis: "check each item"
    print("\n--- creative_synthesize('check each item') ---")
    result = composer.creative_synthesize("check each item")
    if result:
        print(result)
        try:
            compile(result, '<test>', 'exec')
            print("  [OK] Valid Python!")
        except SyntaxError as e:
            print(f"  [HIBA] {e}")
    else:
        print("  (nincs kreatív találat)")
    
    # 4. Kreatív szintézis: "loop through and count"
    print("\n--- creative_synthesize('loop through and count') ---")
    result = composer.creative_synthesize("loop through and count")
    if result:
        print(result)
        try:
            compile(result, '<test>', 'exec')
            print("  [OK] Valid Python!")
        except SyntaxError as e:
            print(f"  [HIBA] {e}")
    else:
        print("  (nincs kreatív találat)")
