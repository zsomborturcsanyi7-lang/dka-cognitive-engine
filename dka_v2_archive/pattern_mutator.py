"""
DKA Core — Pattern Mutator
============================
A DKA hiányzó képessége: amikor a legközelebbi minta nem elég jó,
MUTÁLJA meg a célnak megfelelően.

Példa:
  goal="sum all numbers" → closest=count_items (mindkettő iterál+akkumulál)
  De a "sum" mást jelent: total += x (nem count += 1)
  → Mutáció: csere count→total, 1→x

Működés:
  1. Goal elemzés: mit kell csinálni? (sum, filter, find, max, min, map)
  2. Legközelebbi minta kiválasztása (a szemantikus indexből)
  3. Különbségek azonosítása: mi a cél és mi a minta között?
  4. Mutáció alkalmazása a mintán
  5. Ellenőrzés: valid Python?
"""

from __future__ import annotations
from typing import Optional, Callable
import re

from node_types import (
    BaseNode, PrimitiveNode, PatternNode,
    NodeType, DataDomain, Role,
)
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from pattern_intel import PatternIntelligence, VariableAnalyzer
from inference_engine_v2 import InferenceEngineV2


class GoalAnalyzer:
    """
    Cél elemző: mit kell csinálni a kódnak?
    
    "sum all numbers in a list"
    → action=accumulate, operation=add, target=numbers, container=list
    
    "filter even numbers"
    → action=filter, condition=even, target=numbers
    
    "find maximum value"
    → action=find, extreme=max, target=value
    """
    
    ACTIONS = {
        "sum": {"action": "accumulate", "op": "add", "init": "0"},
        "total": {"action": "accumulate", "op": "add", "init": "0"},
        "add": {"action": "accumulate", "op": "add", "init": "0"},
        "count": {"action": "accumulate", "op": "increment", "init": "0"},
        "max": {"action": "extreme", "op": "max", "init": "None"},
        "minimum": {"action": "extreme", "op": "min", "init": "float('inf')"},
        "min": {"action": "extreme", "op": "min", "init": "float('inf')"},
        "filter": {"action": "filter", "op": "keep_if"},
        "find": {"action": "search", "op": "first_match"},
        "search": {"action": "search", "op": "first_match"},
        "contain": {"action": "search", "op": "contains"},
        "sort": {"action": "reorder", "op": "ascending"},
        "order": {"action": "reorder", "op": "ascending"},
        "reverse": {"action": "reorder", "op": "reverse"},
        "map": {"action": "transform", "op": "apply"},
        "convert": {"action": "transform", "op": "apply"},
        "transform": {"action": "transform", "op": "apply"},
        "remove": {"action": "filter", "op": "remove_if"},
        "delete": {"action": "filter", "op": "remove_if"},
        "unique": {"action": "filter", "op": "distinct"},
        "group": {"action": "group", "op": "by_key"},
        "flatten": {"action": "transform", "op": "flatten"},
        "join": {"action": "combine", "op": "concatenate"},
        "merge": {"action": "combine", "op": "merge"},
        "split": {"action": "split", "op": "by_delimiter"},
        "parse": {"action": "parse", "op": "from_string"},
        "format": {"action": "format", "op": "to_string"},
        "validate": {"action": "check", "op": "verify"},
        "check": {"action": "check", "op": "verify"},
    }
    
    # Mutációs szabályok: action → mit kell változtatni a mintán
    MUTATION_RULES = {
        "accumulate": {
            "add": {
                # count += 1 → total += x
                "accumulator_name": "total",
                "increment": "x",
                "return_target": "total",
            },
            "increment": {
                "accumulator_name": "count",
                "increment": "1",
                "return_target": "count",
            }
        },
        "extreme": {
            "max": {
                "accumulator_name": "max_val",
                "init": "None",
                "logic": "if x > max_val: max_val = x",
            },
            "min": {
                "accumulator_name": "min_val",
                "init": "float('inf')",
                "logic": "if x < min_val: min_val = x",
            }
        },
        "filter": {
            "keep_if": {
                "accumulator_name": "result",
                "init": "[]",
                "logic": "if condition(x): result.append(x)",
            },
            "remove_if": {
                "accumulator_name": "result",
                "init": "[]",
                "logic": "if not condition(x): result.append(x)",
            }
        },
        "search": {
            "first_match": {
                "accumulator_name": "found",
                "init": "None",
                "logic": "if condition(x): return x",
            }
        }
    }
    
    def __init__(self):
        pass
    
    def analyze(self, goal: str) -> dict:
        """
        Cél elemzése.
        
        Visszaadja:
        - action: mit kell csinálni (accumulate, filter, search, ...)
        - op: hogyan (add, max, keep_if, ...)
        - keywords: a feladat kulcsszavai
        - mutation_rules: mit kell megváltoztatni a mintán
        """
        lower = goal.lower()
        
        # Action detektálás
        action = None
        op = None
        for keyword, info in self.ACTIONS.items():
            if keyword in lower:
                action = info["action"]
                op = info["op"]
                break
        
        if not action:
            # Ha nincs ismert action, próbáljunk következtetni
            if any(w in lower for w in ["each", "every", "all", "list", "array"]):
                action = "iterate"
        
        # Mutációs szabályok
        mutation = None
        if action and op:
            action_rules = self.MUTATION_RULES.get(action, {})
            mutation = action_rules.get(op)
        
        # Kulcsszavak
        words = set(re.findall(r'[a-zA-Z_]\w*', lower))
        
        return {
            "action": action,
            "op": op,
            "keywords": words,
            "mutation": mutation,
            "goal": goal,
        }


class InsertMutation:
    """Egy INSERT utasítás beszúrása a kódba (inicializáció)."""
    def __init__(self, var_name, init_value, position="start"):
        self.type = "insert"
        self.var_name = var_name
        self.init_value = init_value
        self.position = position
    
    def apply(self, body_stmts: list) -> list:
        init = PatternNode(type=NodeType.ASSIGNMENT,
            roles={"targets": Role("targets"), "value": Role("value")})
        init.children["targets"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=self.var_name)]
        init.children["value"] = [
            PrimitiveNode(type=NodeType.LITERAL, value=str(self.init_value))]
        
        new_stmts = list(body_stmts)
        if self.position == "start":
            new_stmts.insert(0, init)
        else:
            new_stmts.append(init)
        return new_stmts


class ReplaceMutation:
    """Egy változónév lecserélése a mintában."""
    def __init__(self, old_name, new_name):
        self.type = "replace"
        self.old_name = old_name
        self.new_name = new_name
    
    def apply(self, node: BaseNode):
        if isinstance(node, PrimitiveNode):
            if node.type == NodeType.VARIABLE and node.value == self.old_name:
                node.value = self.new_name
        elif isinstance(node, PatternNode):
            for children in node.children.values():
                for child in children:
                    self.apply(child)


class PatternMutator:
    """
    Minták mutálása a cél alapján.
    
    Ha a "sum all numbers" → count_items a legközelebbi,
    de a count_items "count += 1"-et használ, nem "total += x"-et.
    A mutátor kicseréli az akkumulátor logikát.
    """
    
    def __init__(self, graph: HypergraphV2, generator: ConstructiveGenerator,
                 semantics: SemanticIndex):
        self.graph = graph
        self.generator = generator
        self.semantics = semantics
        self.analyzer = GoalAnalyzer()
        self.pattern_intel = PatternIntelligence(graph)
        self.engine = InferenceEngineV2(graph)
    
    def mutate_for_goal(self, goal: str) -> Optional[str]:
        """
        Cél → mutáció → új kód.
        
        1. Goal elemzés
        2. Keresés akkumulátor mintára (type alapján, nem szemantikusan)
        3. Mutáció alkalmazása
        """
        analysis = self.analyzer.analyze(goal)
        
        if not analysis["action"]:
            return None
        
        # Rekurzív kereső függvények
        def _has_type(node, target_type, visited=None):
            if visited is None:
                visited = set()
            if node.id in visited:
                return False
            visited.add(node.id)
            if isinstance(node, PatternNode):
                if node.type == target_type:
                    return True
                for children in node.children.values():
                    for child in children:
                        if _has_type(child, target_type, visited):
                            return True
            return False
        
        def _find_accumulator(node, visited=None):
            if visited is None:
                visited = set()
            if node.id in visited:
                return False
            visited.add(node.id)
            if isinstance(node, PatternNode):
                if node.type == NodeType.ASSIGNMENT:
                    for role in ("targets", "target"):
                        for t in node.children.get(role, []):
                            if isinstance(t, PrimitiveNode):
                                info = VariableAnalyzer.ROLES.get(t.value, "")
                                if info == "accumulator" or t.value in ("count", "total", "result", "sum"):
                                    return True
                for children in node.children.values():
                    for child in children:
                        if _find_accumulator(child, visited):
                            return True
            return False
        
        # Keressünk FUNCTION_DEF mintákat
        best_func = None
        
        for pid, pattern in self.graph.patterns.items():
            if pattern.type != NodeType.FUNCTION_DEF:
                continue
            
            has_loop = _has_type(pattern, NodeType.FOR_LOOP)
            has_accumulator = _find_accumulator(pattern)
            has_return = _has_type(pattern, NodeType.RETURN_STMT)
            has_if = _has_type(pattern, NodeType.IF_STATEMENT)
            has_append = False
            # Ellenőrizzük a .append hívást
            for children in pattern.children.values():
                for child in children:
                    if isinstance(child, PatternNode) and child.type == NodeType.BLOCK:
                        for stmt in child.children.get("statements", []):
                            if isinstance(stmt, PatternNode):
                                if stmt.type == NodeType.FUNCTION_CALL:
                                    func = stmt.children.get("func", [None])[0]
                                    if func and isinstance(func, PatternNode):
                                        if func.type == NodeType.ATTRIBUTE_ACCESS:
                                            attr = func.children.get("attribute", [None])[0]
                                            if attr and hasattr(attr, 'value') and attr.value == "append":
                                                has_append = True
            
            # STRUCTURE-based match: accumulator pattern
            if analysis["action"] == "accumulate":
                if has_loop and has_accumulator and has_return:
                    best_func = pattern
                    break
            
            # FILTER pattern: loop + if + append
            if analysis["action"] == "filter":
                if has_loop and has_if and has_append and has_return:
                    best_func = pattern
                    break
            
            # SEARCH pattern: loop + if + return
            if analysis["action"] == "search":
                if has_loop and has_if and has_return and not has_append:
                    best_func = pattern
                    break
        
        if not best_func:
            # Fallback: egyszerű szemantikus keresés
            sem_results = self.semantics.search_by_text(goal, top_k=3)
            for r in sem_results:
                if r['type'] == 'FUNCTION_DEF':
                    pattern = self.graph.patterns.get(r['id'])
                    if pattern:
                        best_func = pattern
                        break
                    
        # EXTREME action: keressünk COMPARISON + RETURN mintát
        if not best_func and analysis["action"] == "extreme":
            for pid, pattern in self.graph.patterns.items():
                if pattern.type == NodeType.FUNCTION_DEF:
                    has_comparison = _has_type(pattern, NodeType.COMPARISON)
                    has_if = _has_type(pattern, NodeType.IF_STATEMENT)
                    has_ret = _has_type(pattern, NodeType.RETURN_STMT)
                    if has_comparison and has_if and has_ret:
                        best_func = pattern
                        break
        
        if not best_func:
            return None
        
        # Klónozás
        clone = self.engine._clone_pattern(best_func)
        
        # Mutáció alkalmazása
        mutation = analysis.get("mutation")
        if mutation:
            clone = self._apply_mutation(clone, mutation, analysis)
        
        # Függvény wrapper ha kell
        return self.generator.generate(clone)
    
    def _apply_mutation(self, func_node: PatternNode,
                        mutation: dict, analysis: dict) -> PatternNode:
        """Mutáció alkalmazása a függvény klónján."""
        body = func_node.children.get("body", [None])[0]
        if not body or not isinstance(body, PatternNode):
            return func_node
        
        body_stmts = body.children.get("statements", [])
        if not body_stmts:
            return func_node
        
        # Akkumulátor név csere
        acc_name = mutation.get("accumulator_name", "result")
        
        # Keressük a meglévő akkumulátort
        existing_acc = None
        for stmt in body_stmts:
            if isinstance(stmt, PatternNode) and stmt.type == NodeType.ASSIGNMENT:
                targets = stmt.children.get("targets", stmt.children.get("target", []))
                for t in targets:
                    if isinstance(t, PrimitiveNode) and t.type == NodeType.VARIABLE:
                        info = self.pattern_intel.analyzer.ROLES.get(t.value, "")
                        if info == "accumulator" or t.value in ("count", "total", "result"):
                            existing_acc = t.value
                            break
        
        # Ha van akkumulátor, cseréljük le
        if existing_acc and existing_acc != acc_name:
            for stmt in body_stmts:
                if isinstance(stmt, PatternNode):
                    for children in stmt.children.values():
                        for child in children:
                            self._rename_var(child, existing_acc, acc_name)
        
        # Return target csere
        return_target = mutation.get("return_target")
        if return_target and existing_acc:
            for stmt in body_stmts:
                if isinstance(stmt, PatternNode) and stmt.type == NodeType.RETURN_STMT:
                    val = stmt.children.get("value", [None])[0]
                    if val and isinstance(val, PrimitiveNode) and val.type == NodeType.VARIABLE:
                        if val.value == existing_acc:
                            val.value = return_target
        
        # Init csere
        init_val = mutation.get("init")
        if init_val and existing_acc:
            for stmt in body_stmts:
                if isinstance(stmt, PatternNode) and stmt.type == NodeType.ASSIGNMENT:
                    targets = stmt.children.get("targets", stmt.children.get("target", []))
                    for t in targets:
                        if isinstance(t, PrimitiveNode) and t.value == existing_acc:
                            # Cseréljük az init értéket
                            vals = stmt.children.get("value", [])
                            if vals:
                                vals[0] = PrimitiveNode(
                                    type=NodeType.LITERAL,
                                    value=str(init_val))
        
        body.children["statements"] = body_stmts
        return func_node
    
    def _rename_var(self, node: BaseNode, old: str, new: str):
        """Változónév átírása."""
        if isinstance(node, PrimitiveNode) and node.type == NodeType.VARIABLE:
            if node.value == old:
                node.value = new
        elif isinstance(node, PatternNode):
            for children in node.children.values():
                for child in children:
                    self._rename_var(child, old, new)


class AdaptedSynthesis:
    """
    Adaptált szintézis: a DKA utolsó hiányzó képessége.
    
    1. Próbál pontos egyezést (synthesis_engine_v2)
    2. Ha nincs, próbál kreatív kompozíciót (creative_composer)
    3. Ha az sem jó, próbál mutációt (pattern_mutator)
    4. Ha minden más: visszaadja a legközelebbi matchinget
    """
    
    def __init__(self, graph: HypergraphV2, generator: ConstructiveGenerator,
                 semantics: SemanticIndex):
        self.graph = graph
        self.generator = generator
        self.semantics = semantics
        self.mutator = PatternMutator(graph, generator, semantics)
    
    def synthesize(self, goal: str) -> str:
        """Teljes adaptált szintézis."""
        # 1. Mutáció próbálkozás (új)
        result = self.mutator.mutate_for_goal(goal)
        if result:
            return result
        
        # 2. Egyszerű generálás (meglévő)
        from dka import DKA
        return ""


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from dka import DKA
    
    dka = DKA()
    
    dka.learn('''
def count_items(items):
    count = 0
    for item in items:
        count += 1
    return count
''', source='count')
    
    dka.learn('''
def check_value(x, threshold):
    if x > threshold:
        return True
    return False
''', source='check')
    
    mutator = PatternMutator(dka.graph, dka.generator, dka.semantics)
    
    print("=== MUTÁCIÓS TESZT ===")
    for goal in ["sum all numbers", "count items", "find max"]:
        print(f"\n--- '{goal}' ---")
        result = mutator.mutate_for_goal(goal)
        if result:
            print(result)
            try:
                compile(result, '<test>', 'exec')
                print("  [OK] Valid Python!")
            except SyntaxError as e:
                print(f"  [HIBA] {e}")
        else:
            print("  (nincs mutáció)")
