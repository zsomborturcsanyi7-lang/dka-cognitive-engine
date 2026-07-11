"""
DKA Core — Pattern Intelligence Module
========================================
Mélyebb mintaelemzés a kreatív kompozícióhoz.

Képességek:
1. Változó szerep detektálás (mi a loop index, mi a collection, mi a paraméter)
2. Hiányzó inicializáció felismerése (count += 1 → kell count = 0 előtte)
3. Paraméter következtetés (milyen változók jönnek kívülről?)
4. Változó scope követés (mi hova tartozik)
5. Automatikus javaslat: mi hiányzik a kódból?
"""

from __future__ import annotations
from typing import Optional
from collections import Counter

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain, Role,
)


class VariableAnalyzer:
    """
    Változók elemzése egy kódban.
    
    Megmondja egy változóról:
    - Mi a szerepe? (loop_index, collection, counter, result, temp, parameter)
    - Definiálva van-e mielőtt használjuk?
    - Milyen típusú értékeket kap?
    """
    
    ROLES = {
        # Gyakori ciklusváltozók
        "i": "loop_index", "j": "loop_index", "k": "loop_index",
        "idx": "loop_index", "index": "loop_index", "pos": "loop_index",
        "counter": "loop_index", "x": "element", "elem": "element",
        "item": "element", "element": "element", "val": "element",
        "value": "element", "data": "collection", 
        "arr": "collection", "list": "collection", "items": "collection",
        "collection": "collection", "seq": "collection", "sequence": "collection",
        # Számlálók és gyűjtők
        "count": "accumulator", "total": "accumulator", "sum": "accumulator",
        "result": "accumulator", "res": "accumulator", "output": "accumulator",
        "acc": "accumulator",
        # Fájl műveletek
        "f": "file_handle", "file": "file_handle", "fh": "file_handle",
        "fp": "file_handle", "handle": "file_handle",
        "path": "file_path", "filename": "file_path", "fname": "file_path",
        "filepath": "file_path",
        # String műveletek
        "text": "string", "s": "string", "str": "string",
        "msg": "string", "message": "string", "line": "string",
        # Logikai
        "flag": "boolean", "found": "boolean", "done": "boolean",
        "ok": "boolean", "valid": "boolean",
        # API/network
        "url": "url", "response": "response", "resp": "response",
        "req": "request", "request": "request",
        "api_key": "config", "key": "config", "token": "config",
    }
    
    def __init__(self, graph=None):
        self.graph = graph
    
    def analyze_pattern(self, node: BaseNode) -> dict:
        """
        Egy minta változóinak elemzése.
        Visszaadja:
        - variables: {változónév: szerep, használatok_száma, ...}
        - undefined: nincsenek definiálva, de használva
        - parameters: kívülről jövő változók
        - accumulators: gyűjtők amiket inicializálni kell
        """
        analysis = {
            "variables": {},
            "undefined": set(),
            "parameters": set(),
            "accumulators": [],
            "collections": [],
        }
        
        # Változók felderítése
        self._discover_variables(node, analysis, defined=set(), depth=0)
        
        # Paraméterek: amik nincsenek definiálva, de használva vannak
        # ÉS nem szerepelnek assignment targetként
        assignment_targets = self._find_assignment_targets(node)
        analysis["parameters"] = {
            v for v in analysis["undefined"] 
            if v not in assignment_targets
        }
        
        # Gyűjtők: accumulator szerepű változók
        for var_name, info in analysis["variables"].items():
            if info.get("role") == "accumulator":
                analysis["accumulators"].append(var_name)
            if info.get("role") == "collection":
                analysis["collections"].append(var_name)
        
        # undefined → szeparálva paraméterek és tényleg hiányzók
        really_undefined = set()
        for v in analysis["undefined"]:
            info = analysis["variables"].get(v, {})
            # 1 betűsök általában paraméterek
            if len(v) <= 1:
                continue
            # Ha csak 1x használt, valószínűleg paraméter
            if info.get("uses", 0) <= 1:
                continue
            really_undefined.add(v)
        
        analysis["missing_initialization"] = really_undefined
        
        return analysis
    
    def _find_assignment_targets(self, node: BaseNode, targets: set = None) -> set[str]:
        """Assignment target változók gyűjtése."""
        if targets is None:
            targets = set()
        
        if isinstance(node, PatternNode):
            if node.type == NodeType.ASSIGNMENT:
                for role in ("targets", "target"):
                    for child in node.children.get(role, []):
                        if isinstance(child, PrimitiveNode) and child.type == NodeType.VARIABLE:
                            targets.add(child.value)
            
            for children in node.children.values():
                for child in children:
                    self._find_assignment_targets(child, targets)
        
        return targets
    
    def _discover_variables(self, node: BaseNode, analysis: dict,
                            defined: set[str], depth: int = 0):
        """Változók felderítése rekurzívan."""
        if depth > 15:
            return
        
        if isinstance(node, PrimitiveNode):
            if node.type == NodeType.VARIABLE:
                var_name = node.value
                
                # Szerep detektálás
                role = self.ROLES.get(var_name, self._guess_role(var_name))
                
                # Ha paraméter szerepű
                if node.role in ("param", "name"):
                    analysis["parameters"].add(var_name)
                    defined.add(var_name)
                
                if var_name not in analysis["variables"]:
                    analysis["variables"][var_name] = {
                        "role": role,
                        "uses": 0,
                        "defined": var_name in defined,
                        "first_seen": "use",
                    }
                
                analysis["variables"][var_name]["uses"] += 1
                
                # Ha nincs definiálva, jelöljük
                if var_name not in defined and node.role not in ("param", "name"):
                    analysis["undefined"].add(var_name)
        
        elif isinstance(node, PatternNode):
            # Assignment definiálja a target változókat
            if node.type == NodeType.ASSIGNMENT:
                targets = node.children.get("targets", 
                         node.children.get("target", []))
                for t in targets:
                    if isinstance(t, PrimitiveNode) and t.type == NodeType.VARIABLE:
                        defined.add(t.value)
            
            # FOR_LOOP target definiálja a ciklusváltozót
            if node.type == NodeType.FOR_LOOP:
                target = node.children.get("target", [None])[0]
                if target and isinstance(target, PrimitiveNode):
                    if target.type == NodeType.VARIABLE:
                        defined.add(target.value)
            
            # Rekurzív bejárás
            for children in node.children.values():
                for child in children:
                    self._discover_variables(child, analysis, defined.copy(), depth + 1)
    
    def _guess_role(self, var_name: str) -> str:
        """Változónév szerepének kitalálása a név alapján."""
        name_lower = var_name.lower()
        
        if any(name_lower.endswith(s) for s in ["_list", "_array", "_arr", "s", "es"]):
            return "collection"
        if any(name_lower.startswith(p) for p in ["is_", "has_", "should_"]):
            return "boolean"
        if any(name_lower.endswith(s) for s in ["_count", "_num", "_total", "_size"]):
            return "accumulator"
        if any(name_lower.endswith(s) for s in ["_path", "_file", "_dir"]):
            return "file_path"
        if any(name_lower.endswith(s) for s in ["_result", "_res", "_output"]):
            return "accumulator"
        if any(name_lower.startswith(p) for p in ["temp_", "tmp_"]):
            return "temporary"
        
        return "unknown"


class PatternIntelligence:
    """
    Minták intelligens elemzése.
    
    Képességek:
    - Mit csinál ez a minta? (változó-elemzés alapján)
    - Mi hiányzik belőle? (undefined változók, inicializálatlan gyűjtők)
    - Hogyan lehet más mintákkal kombinálni? (szerep-illesztés)
    """
    
    def __init__(self, graph=None):
        self.graph = graph
        self.analyzer = VariableAnalyzer(graph)
    
    def analyze(self, node: BaseNode) -> dict:
        """
        Teljes elemzés: változók + szerkezet + hiányzó részek.
        """
        var_analysis = self.analyzer.analyze_pattern(node)
        
        elemzés = {
            "type": node.type.name if hasattr(node, 'type') else "?",
            "variables": var_analysis["variables"],
            "parameters": var_analysis["parameters"],
            "undefined": var_analysis["missing_initialization"],
            "needs_init": var_analysis["accumulators"],
            "collections": var_analysis["collections"],
        }
        
        # Ajánlások generálása
        elemzés["recommendations"] = self._generate_recommendations(elemzés)
        
        return elemzés
    
    def _generate_recommendations(self, elemzés: dict) -> list[str]:
        """Ajánlások generálása az elemzés alapján."""
        recs = []
        
        for acc in elemzés["needs_init"]:
            if acc not in elemzés["parameters"]:
                recs.append(f"{acc} = 0  (inicializálás szükséges)")
        
        for undef in elemzés["undefined"]:
            if undef not in elemzés["parameters"] and undef not in elemzés["needs_init"]:
                recs.append(f"{undef} = ...  (definiáld a változót)")
        
        if elemzés["collections"] and elemzés["type"] == "FUNCTION_DEF":
            for c in elemzés["collections"]:
                if c not in elemzés["parameters"]:
                    recs.append(f"Add paraméter: {c}")
        
        if elemzés["parameters"]:
            recs.append(f"Függvény paraméterek: {', '.join(elemzés['parameters'])}")
        
        return recs
    
    def compare_patterns(self, node_a: BaseNode, node_b: BaseNode) -> dict:
        """
        Két minta összehasonlítása a változók szintjén.
        Megmondja, hogyan lehet őket összeolvasztani.
        """
        analysis_a = self.analyze(node_a)
        analysis_b = self.analyze(node_b) if hasattr(node_b, 'type') else {}
        # Use analyze method
        analysis_b = self.analyze(node_b)
        
        vars_a = set(analysis_a["variables"].keys())
        vars_b = set(analysis_b["variables"].keys())
        
        return {
            "common_vars": vars_a & vars_b,
            "unique_a": vars_a - vars_b,
            "unique_b": vars_b - vars_a,
            "params_a": analysis_a["parameters"],
            "params_b": analysis_b["parameters"],
            "compatible": len(vars_a & vars_b) > 0,
        }


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from grammar_parser import GrammarParser
    from hypergraph_v2 import HypergraphV2
    
    parser = GrammarParser()
    graph = HypergraphV2()
    
    code = '''
def count_items(items):
    count = 0
    for item in items:
        count += 1
    return count
'''
    
    nodes = parser.parse(code)
    graph.ingest_pattern_tree(nodes)
    
    pi = PatternIntelligence(graph)
    
    for node in nodes:
        if hasattr(node, 'type') and node.type == NodeType.FUNCTION_DEF:
            analysis = pi.analyze(node)
            print("=== FÜGGVÉNY ELEMZÉS ===")
            print(f"Típus: {analysis['type']}")
            print(f"Változók:")
            for vname, info in analysis['variables'].items():
                if info['uses'] > 0:
                    print(f"  {vname}: role={info['role']}, uses={info['uses']}")
            print(f"Paraméterek: {analysis['parameters']}")
            print(f"Hiányzó inicializáció: {analysis['undefined']}")
            print(f"Akkumulátorok: {analysis['needs_init']}")
            print(f"Ajánlások:")
            for r in analysis['recommendations']:
                print(f"  - {r}")
