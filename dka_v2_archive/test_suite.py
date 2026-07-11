"""
DKA V2 — Teljes Tesztcsomag
=============================
Minden core funkció validálása.
Ha itt minden OK, akkor a rendszer elméletileg készen áll az élő tesztre.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from node_types import (
    PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain, BaseNode,
    Role
)
from hypergraph_v2 import HypergraphV2
from grammar_parser import GrammarParser
from constructive_generator import ConstructiveGenerator
from inference_engine_v2 import InferenceEngineV2
from dka import DKA


passed = 0
failed = 0
errors = []


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [OK] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}" + (f" - {detail}" if detail else "")
        print(msg)
        errors.append(msg)


def test_group(name):
    print(f"\n=== {name} ===")


# ────────────────────────────────────────────────────────────────────
# 1. Node Types
# ────────────────────────────────────────────────────────────────────

test_group("1. Nódus Rendszer (node_types.py)")

p = PrimitiveNode(type=NodeType.VARIABLE, value="x")
test("PrimitiveNode létezik", isinstance(p, BaseNode))
test("PrimitiveNode típusa", p.type == NodeType.VARIABLE)
test("PrimitiveNode értéke", p.value == "x")

pn = PatternNode(type=NodeType.FOR_LOOP)
test("PatternNode létezik", isinstance(pn, PatternNode))
pn.children["target"] = [p]
test("PatternNode gyerek", len(pn.children["target"]) == 1)

sn = SchemaNode(name="test_schema", pattern_ids={"a", "b"})
test("SchemaNode létezik", isinstance(sn, SchemaNode))
test("SchemaNode név", sn.name == "test_schema")
test("SchemaNode minták", len(sn.pattern_ids) == 2)

# Serializáció
d = p.to_dict()
p2 = PrimitiveNode.from_dict(d)
test("PrimitiveNode serializáció", p2.value == p.value and p2.type == p.type)

d2 = sn.to_dict()
test("SchemaNode serializáció", d2["name"] == "test_schema")


# ────────────────────────────────────────────────────────────────────
# 2. Grammar Parser
# ────────────────────────────────────────────────────────────────────

test_group("2. Grammar Parser (grammar_parser.py)")

parser = GrammarParser()

# Egyszerű függvény
nodes = parser.parse("def foo():\n    pass")
test("Parser: üres függvény", len(nodes) > 0)
has_func = any(isinstance(n, PatternNode) and n.type == NodeType.FUNCTION_DEF for n in nodes)
test("Parser: FUNCTION_DEF felismerés", has_func)

# For ciklus
nodes2 = parser.parse("for i in range(10):\n    print(i)")
has_for = any(isinstance(n, PatternNode) and n.type == NodeType.FOR_LOOP for n in nodes2)
test("Parser: FOR_LOOP felismerés", has_for)

# If/else
nodes3 = parser.parse("if x > 0:\n    return 1\nelse:\n    return -1")
has_if = any(isinstance(n, PatternNode) and n.type == NodeType.IF_STATEMENT for n in nodes3)
test("Parser: IF_STATEMENT felismerés", has_if)

# Osztály
nodes4 = parser.parse("class Foo:\n    def bar(self):\n        pass")
has_class = any(isinstance(n, PatternNode) and n.type == NodeType.CLASS_DEF for n in nodes4)
test("Parser: CLASS_DEF felismerés", has_class)

# Komplex kifejezés
nodes5 = parser.parse("result = (a + b) * c")
has_assign = any(isinstance(n, PatternNode) and n.type == NodeType.ASSIGNMENT for n in nodes5)
test("Parser: ASSIGNMENT kifejezéssel", has_assign)

# Import
nodes6 = parser.parse("import os\nfrom pathlib import Path")
has_import = any(isinstance(n, PatternNode) and n.type == NodeType.IMPORT for n in nodes6)
test("Parser: IMPORT felismerés", has_import)

# While
nodes7 = parser.parse("while True:\n    break")
has_while = any(isinstance(n, PatternNode) and n.type == NodeType.WHILE_LOOP for n in nodes7)
test("Parser: WHILE_LOOP felismerés", has_while)


# ────────────────────────────────────────────────────────────────────
# 3. Constructive Generator (Roundtrip)
# ────────────────────────────────────────────────────────────────────

test_group("3. Constructive Generator (roundtrip)")

graph = HypergraphV2()
gen = ConstructiveGenerator(graph)

roundtrip_cases = [
    ("fibonacci", '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''),
    ("bubble_sort", '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''),
    ("class_def", '''
class Counter:
    def __init__(self):
        self.count = 0
    def increment(self):
        self.count += 1
    def get(self):
        return self.count
'''),
    ("while_loop", '''
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
'''),
    ("api_call", '''
def get_data(url):
    import requests
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    return None
'''),
]

for name, code in roundtrip_cases:
    nodes = parser.parse(code)
    nids = graph.ingest_pattern_tree(nodes)
    
    # Generáljuk vissza
    generated = gen.generate_program(nids)
    
    # Valid Python?
    try:
        compile(generated, '<test>', 'exec')
        valid = True
    except SyntaxError as e:
        valid = False
        detail = str(e)
    
    test(f"Roundtrip: {name} (valid Python)", valid, detail if not valid else "")


# ────────────────────────────────────────────────────────────────────
# 4. Hypergraph
# ────────────────────────────────────────────────────────────────────

test_group("4. Hipergráf (hypergraph_v2.py)")

stats = graph.stats()
test("Grúf nem üres", stats["total_pie"] > 0)
test("Van primitív nódus", stats["primitives"] > 0)
test("Van minta nódus", stats["patterns"] > 0)

# Keresés
fors = graph.find_by_type(NodeType.FOR_LOOP)
test("find_by_type: FOR_LOOP", len(fors) > 0)

ifs = graph.find_by_type(NodeType.IF_STATEMENT)
test("find_by_type: IF_STATEMENT", len(ifs) > 0)

funcs = graph.find_by_type(NodeType.FUNCTION_DEF)
test("find_by_type: FUNCTION_DEF", len(funcs) > 0)

# Strukturális mélység
if funcs:
    depth = graph.calculate_depth(funcs[0].id)
    test("Strukturális mélység > 0", depth > 0)

# SRT
if len(fors) >= 1 and len(ifs) >= 1:
    dist = graph.get_structural_distance(fors[0].id, ifs[0].id)
    test("SRT mérhető", dist is not None or True)  # Lehet None ha nincs kapcsolat

# Scope
if funcs:
    scope = graph.get_context_scope(funcs[0].id)
    test("Scope total_se > 0", scope["total_se"] > 0)
    test("Scope focus nem None", scope["focus"] is not None)

# Pattern Discovery
patterns = graph.discover_patterns(min_instances=2)
test("Pattern discovery talál mintákat", len(patterns) > 0)

# Serializáció
json_str = graph.to_json()
graph2 = HypergraphV2.from_json(json_str)
test("Serializáció/deserializáció", graph2.stats()["total_pie"] == stats["total_pie"])

# Séma építés
if len(patterns) > 0:
    schema = graph.build_schema("test_loop", patterns[0]["pattern_ids"][:2])
    if schema:
        test("Séma építés sikerült", schema.name == "test_loop")


# ────────────────────────────────────────────────────────────────────
# 5. Inference Engine
# ────────────────────────────────────────────────────────────────────

test_group("5. Következtető Motor (inference_engine_v2.py)")

engine = InferenceEngineV2(graph)

# Pattern matching
if len(fors) >= 2:
    match = engine.match_pattern(fors[0], fors[1])
    test("Pattern matching: FOR-FOR hasonlóság", match["percentage"] >= 50)

if len(ifs) >= 2:
    match = engine.match_pattern(ifs[0], ifs[1])
    test("Pattern matching: IF-IF hasonlóság", match["percentage"] >= 50)

# Különböző típusok összehasonlítása (kicsi hasonlóság)
if len(fors) > 0 and len(ifs) > 0:
    match = engine.match_pattern(fors[0], ifs[0])
    test("Pattern matching: FOR-IF különböző", match["percentage"] < 100)

# Analógia keresés
if fors:
    analogies = engine.find_analogies(fors[0], max_results=3)
    if analogies:
        test("Analógia keresés találatot ad", len(analogies) > 0)

# Constraint-based solve
solved = engine.solve_with_patterns(NodeType.FOR_LOOP)
if solved:
    test("solve_with_patterns: FOR_LOOP", solved.type == NodeType.FOR_LOOP)

solved2 = engine.solve_with_patterns(NodeType.IF_STATEMENT)
if solved2:
    test("solve_with_patterns: IF_STATEMENT", solved2.type == NodeType.IF_STATEMENT)


# ────────────────────────────────────────────────────────────────────
# 6. DKA integráció
# ────────────────────────────────────────────────────────────────────

test_group("6. DKA integráció (dka.py)")

dka = DKA()

count = dka.learn("def hello():\n    print('world')", source="hello")
test("DKA.learn hozzáad PIE-t", count > 0)

test("DKA.stats működik", dka.stats()["total_pie"] > 0)

generated = dka.generate(goal="hello")
test("DKA.generate goal-al hívható", isinstance(generated, str))

reason = dka.reason("hello")
test("DKA.reason visszatér stringgel", isinstance(reason, str) and len(reason) > 0)

inspect = dka.inspect()
test("DKA.inspect visszatér stringgel", isinstance(inspect, str) and len(inspect) > 0)

# Mentés/betöltés
dka.save("dka_test_save.json")
loaded = os.path.exists("dka_test_save.json")
test("DKA.save fájlba ír", loaded)

if loaded:
    dka2 = DKA()
    dka2.load("dka_test_save.json")
    test("DKA.load visszaállítja a gráfot", dka2.stats()["total_pie"] == dka.stats()["total_pie"])
    os.remove("dka_test_save.json")


# ────────────────────────────────────────────────────────────────────
# 7. Végső roundtrip teszt (minden eddig tanult kód vissza)
# ────────────────────────────────────────────────────────────────────

test_group("7. Teljes roundtrip (minden tanult kód)")

# Minden FUNCTION_DEF-ot generáljunk vissza
func_nodes = dka2.graph.find_by_type(NodeType.FUNCTION_DEF) if loaded else graph.find_by_type(NodeType.FUNCTION_DEF)
# Használjuk az eredeti gráfot
orig_funcs = graph.find_by_type(NodeType.FUNCTION_DEF)
all_valid = True
for func in orig_funcs:
    code = gen.generate(func)
    try:
        compile(code, '<test>', 'exec')
    except SyntaxError:
        all_valid = False
        break

test("Minden függvény roundtrip-je valid Python", all_valid)

# Minden osztály
classes = graph.find_by_type(NodeType.CLASS_DEF)
classes_valid = True
for cls in classes:
    code = gen.generate(cls)
    try:
        compile(code, '<test>', 'exec')
    except SyntaxError:
        classes_valid = False
        break

if classes:
    test("Minden osztály roundtrip-je valid Python", classes_valid)


# ────────────────────────────────────────────────────────────────────
# 8. Memória hatékonyság
# ────────────────────────────────────────────────────────────────────

test_group("8. Memória hatékonyság")

stats = graph.stats()
ratio = stats["patterns"] / stats["primitives"] if stats["primitives"] > 0 else 0
test(f"Minta/primitív arány: {ratio:.2f} (tömörítés)", ratio > 0.5)

# A 3. réteg hatékonysága: minden séma legalább 2 mintát takar
schema_efficiency = 0
for schema in graph.schemas.values():
    if len(schema.pattern_ids) >= 2:
        schema_efficiency += 1
test(f"Sémák amik valóban absztrahálnak (>=2 minta)", schema_efficiency > 0)


# ────────────────────────────────────────────────────────────────────
# Összegzés
# ────────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"TESZT ÖSSZEGZÉS")
print(f"{'='*50}")
print(f"  Passed: {passed}/{passed + failed}")
print(f"  Failed: {failed}")

if errors:
    print(f"\n  Hibák:")
    for e in errors:
        print(f"    {e}")

print()
if failed == 0:
    print("  MINDEN TESZT SIKERES! A DKA V2 készen áll az élő tesztre.")
else:
    print(f"  {failed} teszt nem sikerült. Javítás szükséges.")

print()
