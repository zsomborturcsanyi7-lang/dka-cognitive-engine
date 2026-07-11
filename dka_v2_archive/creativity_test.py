"""DKA V2 — Komplex kreatív tesztek"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from struct_compose import StructuredComposer, ProgramScaffold, SlotFiller

g = HypergraphV2.from_json_file("dka_trained_500.json")
sem = SemanticIndex(g)
sem.index_all()
gen = ConstructiveGenerator(g)
composer = StructuredComposer(g, gen, sem)
filler = SlotFiller(g, sem)

tests = [
    # 1. Guess game (újra - bizonyíték)
    ("guess the number", "scaffold"),
    # 2. Data processing
    ("process csv file", "scaffold"),
    # 3. Sort
    ("sort array", "normal"),
    # 4. Search
    ("find item in list", "normal"),
    # 5. Filter
    ("filter even numbers", "normal"),
    # 6. Scaffold: guess más néven
    ("number guessing game", "scaffold"),
]

print("=" * 70)
print("  DKA V2 — KREATÍV GENERÁLÁS TESZT")
print("=" * 70)

passed = 0
total = 0

for goal, test_type in tests:
    total += 1
    print(f"\n  {total}. '{goal}' [{test_type}]")
    print(f"  {'-'*60}")
    
    code = None
    if test_type == "scaffold":
        # Közvetlen scaffold teszt (biztosabb)
        if "guess" in goal or "number" in goal:
            scaffold = ProgramScaffold.guess_game
        elif "csv" in goal or "file" in goal:
            scaffold = ProgramScaffold.data_processor
        else:
            scaffold = ProgramScaffold.simple_function
        
        name = goal.replace(" ", "_")[:15]
        s = scaffold(name)
        filled = filler.fill(s, goal)
        code = gen.generate(filled)
    
    if not code:
        code = composer.compose([], goal)
    
    if code:
        # 4 space indent a kiíráshoz
        for line in code.split("\n"):
            print(f"    {line}")
        
        try:
            compile(code, "<test>", "exec")
            print(f"\n  >>> [OK] VALID PYTHON")
            passed += 1
        except SyntaxError as e:
            print(f"\n  >>> [HIBA] {e.lineno}: {e.msg[:60]}")
    else:
        print("    (ures)")
        print(f"\n  >>> [URES]")

print(f"\n{'='*70}")
print(f"  EREDMÉNY: {passed}/{total} VALID PYTHON")
print(f"{'='*70}")
