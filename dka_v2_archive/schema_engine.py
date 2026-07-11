"""
DKA Core — Schema Engine
=========================
A 3. réteg (Séma) motorja.

Cél: a strukturális minták fölé szemantikus tudást építeni.

Egy séma nem csak annyit tud, hogy "ez egy FOR ciklus",
hanem azt is, hogy:
- "ez egy TIPIKUS faktorialis: base case n <= 1, rekurziv hivas n-1-gyel"
- "ez egy BUBBLE SORT: nested for, comparison, swap pattern"
- "ez egy API hivas: requests.get(), status_code check, json return"

A sémák ezért képesek:
  - Validalni: "ez a faktorialis gyanus, mert a base case n < 0, nem n <= 1"
  - Javitani: "a helyes base case n <= 1 lenne"
  - Generalni: "ide egy FOR ciklus kell, ilyen paraméterekkel"
"""

from __future__ import annotations
from typing import Optional, Any
from collections import Counter
import json

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain,
)
from hypergraph_v2 import HypergraphV2


class SchemaConstraint:
    """
    Egy séma megszorítása egy adott szerepkörre.
    
    Pl. a faktorialis sémában:
      role="condition", type=COMPARISON
      -> left_type=VARIABLE, op=LtE, right_value="1"
    
    Ha egy új kódban a condition right_value != "1", az gyanús.
    """
    
    def __init__(self, role_path: str, constraints: dict[str, Any],
                 importance: float = 1.0):
        """
        role_path: melyik szerepkörre vonatkozik (pl. "body.statements.0.condition")
        constraints: mik az elvárások (pl. {"op": "LtE", "right_value": "1"})
        importance: mennyire fontos (0-1). 1 = kötelező, 0 = opcionális
        """
        self.role_path = role_path
        self.constraints = constraints
        self.importance = importance
    
    def check(self, node: BaseNode, graph: HypergraphV2) -> dict:
        """
        Ellenőrzi, hogy egy nódus megfelel-e a megszorításnak.
        
        Returns: {"passed": bool, "violations": [str], "score": float}
        """
        violations = []
        passed_checks = 0
        total_checks = len(self.constraints)
        
        for key, expected_value in self.constraints.items():
            # Rekurzív role_path követése
            current = node
            for role in self.role_path.split("."):
                if role.isdigit():
                    # Index elérés
                    idx = int(role)
                    if isinstance(current, list) and idx < len(current):
                        current = current[idx]
                    else:
                        violations.append(f"Path {self.role_path}: cannot access [{idx}]")
                        break
                elif hasattr(current, 'children') and role in current.children:
                    children = current.children[role]
                    current = children[0] if children else None
                elif hasattr(current, role):
                    current = getattr(current, role)
                else:
                    violations.append(f"Path {self.role_path}: role '{role}' not found")
                    current = None
                    break
            
            if current is None:
                continue
            
            # Ellenőrizzük a megszorítást a jelenlegi nóduson
            if key == "type":
                if hasattr(current, 'type') and current.type.name == expected_value:
                    passed_checks += 1
                else:
                    violations.append(f"Expected type={expected_value}, got {getattr(current, 'type', '?')}")
            
            elif key == "value":
                if hasattr(current, 'value') and str(current.value) == str(expected_value):
                    passed_checks += 1
                else:
                    violations.append(f"Expected value={expected_value}, got {getattr(current, 'value', '?')}")
            
            elif key.startswith("child_"):
                # Gyerek nódus tulajdonságának ellenőrzése
                child_role = key[6:]  # "child_type" → "type"
                if hasattr(current, 'children'):
                    for children_list in current.children.values():
                        for child in children_list:
                            if hasattr(child, child_role) and str(getattr(child, child_role)) == str(expected_value):
                                passed_checks += 1
                                break
                        else:
                            continue
                        break
                    else:
                        violations.append(f"No child with {child_role}={expected_value}")
                else:
                    violations.append(f"Node has no children")
            
            else:
                # Általános attribútum ellenőrzés
                if hasattr(current, key) and str(getattr(current, key)) == str(expected_value):
                    passed_checks += 1
                else:
                    violations.append(f"Expected {key}={expected_value}, got {getattr(current, key, '?')}")
        
        score = passed_checks / max(total_checks, 1) * self.importance
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "score": score,
        }


class SchemaEngine:
    """
    Séma motor: sémák létrehozása, validálás, tanulás.
    """
    
    def __init__(self, graph: HypergraphV2):
        self.graph = graph
        self.constraints: dict[str, list[SchemaConstraint]] = {}
    
    # ─── Séma létrehozás értelmes névvel ─────────────────────────
    
    def create_schema(self, name: str, pattern_ids: list[str],
                      description: str = "",
                      domain: DataDomain = DataDomain.GENERAL) -> SchemaNode:
        """
        Séma létrehozása értelmes névvel.
        Automatikusan kiszámolja a megszorításokat a mintákból.
        """
        valid_ids = [pid for pid in pattern_ids if pid in self.graph.patterns]
        if len(valid_ids) < 1:
            return None
        
        schema = SchemaNode(
            name=name,
            type=NodeType.SCHEMA,
            pattern_ids=set(valid_ids),
            domain=domain,
            value=description,
        )
        
        # Számoljuk ki az asszociációkat más sémákhoz
        for pid in valid_ids:
            pattern = self.graph.patterns[pid]
            for other_schema in self.graph.schemas.values():
                if pid in other_schema.pattern_ids and other_schema.id != schema.id:
                    overlap = len(other_schema.pattern_ids & set(valid_ids))
                    strength = overlap / max(len(set(valid_ids) | other_schema.pattern_ids), 1)
                    schema.associations[other_schema.id] = max(
                        schema.associations.get(other_schema.id, 0),
                        strength
                    )
        
        # Tanuljunk megszorításokat a mintákból
        self._learn_constraints(schema, valid_ids)
        
        self.graph.add_schema(schema)
        return schema
    
    def _learn_constraints(self, schema: SchemaNode, pattern_ids: list[str]):
        """
        Megszorítások tanulása: egyszerű, értelmes tulajdonságok kinyerése.
        """
        if not pattern_ids:
            return
        
        all_traits = []
        for pid in pattern_ids:
            pattern = self.graph.patterns.get(pid)
            if not pattern:
                continue
            
            # Rekurzív trait extraction
            traits = self._collect_traits(pattern)
            all_traits.append(traits)
        
        # Keressük a gyakori jellemzőket a minták között
        common = self._find_common_traits(all_traits, len(pattern_ids))
        
        constraints = []
        for trait in common:
            c = SchemaConstraint(
                role_path=trait["path"],
                constraints={trait["key"]: trait["value"]},
                importance=trait["frequency"],
            )
            constraints.append(c)
        
        self.constraints[schema.id] = constraints
    
    def _collect_traits(self, node: BaseNode, path: str = "",
                        depth: int = 0) -> list[dict]:
        """
        Értelmes jellemzők gyűjtése egy nódusból.
        Csak a fontos, általánosítható tulajdonságokat gyűjti.
        """
        if depth > 8:
            return []
        
        traits = []
        
        if isinstance(node, PatternNode):
            traits.append({
                "path": path,
                "key": "pattern_type",
                "value": node.type.name
            })
            
            for role, children in node.children.items():
                for i, child in enumerate(children):
                    child_path = f"{path}.{role}" if path else role
                    child_traits = self._collect_traits(child, child_path, depth + 1)
                    traits.extend(child_traits)
        
        elif isinstance(node, PrimitiveNode):
            if node.type in (NodeType.LITERAL,):
                traits.append({
                    "path": path,
                    "key": "literal_type",
                    "value": node.type.name,
                })
            
            if node.type == NodeType.VARIABLE and node.role in ("param", "name"):
                traits.append({
                    "path": path,
                    "key": "role",
                    "value": node.role,
                })
            
            if node.type == NodeType.OPERATOR:
                traits.append({
                    "path": path,
                    "key": "operator",
                    "value": node.value,
                })
        
        return traits
    
    def _find_common_traits(self, all_traits: list[list[dict]],
                           total_patterns: int) -> list[dict]:
        """Gyakori jellemzők keresése az összes minta között."""
        if not all_traits:
            return []
        
        from collections import Counter
        
        # Minden trait-et egy kulcsra képezünk
        trait_counts = Counter()
        for traits in all_traits:
            seen = set()
            for t in traits:
                key = (t["path"], t["key"], str(t["value"]))
                if key not in seen:
                    trait_counts[key] += 1
                    seen.add(key)
        
        threshold = max(2, total_patterns * 0.4)
        common = []
        
        for (path, key, value), count in trait_counts.items():
            if count >= threshold and count >= 2:
                common.append({
                    "path": path,
                    "key": key,
                    "value": value,
                    "frequency": count / total_patterns,
                })
        
        return common
    
    def validate(self, node: BaseNode, schema_id: str = None) -> dict:
        """
        Validálás: összehasonlítja a nódus trait-jeit a séma elvárásaival.
        """
        if not self.constraints:
            return {}
        
        node_traits = self._collect_traits(node)
        # Path-független trait halmaz: csak (key, value) pár
        node_trait_set = set(
            (t["key"], str(t["value"]))
            for t in node_traits
        )
        
        results = {}
        schemas_to_check = []
        
        if schema_id:
            if schema_id in self.graph.schemas:
                schemas_to_check.append(schema_id)
        else:
            schemas_to_check = list(self.graph.schemas.keys())
        
        for sid in schemas_to_check:
            schema = self.graph.schemas.get(sid)
            constraints = self.constraints.get(sid, [])
            
            if not schema or not constraints:
                continue
            
            violations = []
            passed = 0
            total = len(constraints)
            
            for c in constraints:
                trait_key = (list(c.constraints.keys())[0] if c.constraints else "", 
                            str(list(c.constraints.values())[0]) if c.constraints else "")
                
                if trait_key in node_trait_set:
                    passed += 1
                else:
                    constraint_desc = f"{c.role_path}: {c.constraints}"
                    violations.append(f"Missing: {constraint_desc}")
            
            score = passed / max(total, 1)
            
            results[schema.name] = {
                "passed": score >= 0.7,
                "violations": violations[:5],
                "score": score,
                "matched": passed,
                "total": total,
                "schema_id": sid,
            }
        
        return results
    
    # ─── Statisztika ─────────────────────────────────────────────
    
    def stats(self) -> dict:
        """Séma motor statisztika."""
        total_constraints = sum(len(c) for c in self.constraints.values())
        return {
            "schemas": len(self.graph.schemas),
            "total_constraints": total_constraints,
            "avg_constraints_per_schema": total_constraints / max(len(self.graph.schemas), 1),
        }


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from grammar_parser import GrammarParser
    
    parser = GrammarParser()
    graph = HypergraphV2()
    engine = SchemaEngine(graph)
    
    # Tanító kód
    training = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''
    
    nodes = parser.parse(training)
    nids = graph.ingest_pattern_tree(nodes)
    
    # Keressük a FUNCTION_DEF mintákat
    funcs = graph.find_by_type(NodeType.FUNCTION_DEF)
    
    if len(funcs) >= 2:
        # Hozzunk létre értelmes sémákat
        schema1 = engine.create_schema(
            name="recursive_math_function",
            pattern_ids=[funcs[0].id, funcs[1].id],
            description="Rekurzív matematikai függvény base case-szel és rekurzív hívással"
        )
        
        if schema1:
            print(f"Letrehozva: {schema1.name}")
            print(f"  Mintak: {len(schema1.pattern_ids)}")
            print(f"  Assoc: {len(schema1.associations)}")
            
            # Megszorítások
            constraints = engine.constraints.get(schema1.id, [])
            print(f"  Megszoritasok: {len(constraints)}")
            for c in constraints[:5]:
                print(f"    {c.role_path}: {c.constraints} (fontossag: {c.importance:.2f})")
        
        # Teszt: validáljunk egy helyes faktoriálist
        print("\n--- Validacio: helyes faktorialis ---")
        valid_code = "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"
        valid_nodes = parser.parse(valid_code)
        for vn in valid_nodes:
            if isinstance(vn, PatternNode) and vn.type == NodeType.FUNCTION_DEF:
                results = engine.validate(vn)
                if results:
                    for name, r in results.items():
                        print(f"  {name}: score={r['score']:.2f}, passed={r['passed']}")
                break
        
        # Teszt: validáljunk egy hibás faktoriálist
        print("\n--- Validacio: HIBAS faktorialis (rossz base case) ---")
        buggy_code = "def factorial(n):\n    if n < 0:\n        return n\n    return n * factorial(n - 1)"
        buggy_nodes = parser.parse(buggy_code)
        for bn in buggy_nodes:
            if isinstance(bn, PatternNode) and bn.type == NodeType.FUNCTION_DEF:
                results = engine.validate(bn)
                if results:
                    for name, r in results.items():
                        print(f"  {name}: score={r['score']:.2f}, passed={r['passed']}")
                        if r['violations']:
                            print(f"  Violations ({len(r['violations'])}):")
                            for v in r['violations'][:3]:
                                print(f"    - {v}")
                break
    
    print(f"\nSchemaEngine stats: {engine.stats()}")
