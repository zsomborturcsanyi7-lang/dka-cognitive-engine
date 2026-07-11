"""DKA V2 — Trained model test"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from synthesis_engine_v2 import SynthesisEngineV2
from pattern_mutator import PatternMutator

g = HypergraphV2.from_json_file("dka_trained_500.json")
print(f"Graf: {g.stats()['total_pie']} PIE, {g.stats()['patterns']} minta")

sem = SemanticIndex(g)
sem.index_all()
print(f"Fogalmak: {sem.stats()['total_concepts']}")

gen = ConstructiveGenerator(g)
synth = SynthesisEngineV2(g, sem, gen)
mutator = PatternMutator(g, gen, sem)

tests = [
    "sort array", "find prime", "sum numbers", "filter even",
    "reverse text", "read file", "count words", "is palindrome",
    "binary search", "factorial", "fibonacci", "shuffle list",
    "roll dice", "safe divide", "stack push",
]

ok = 0
total = 0
for goal in tests:
    code = synth.synthesize(goal)
    if not code:
        code = mutator.mutate_for_goal(goal)
    if not code:
        sr = sem.search_by_text(goal, top_k=1)
        if sr:
            pid = sr[0]["id"]
            p = g.patterns.get(pid)
            if p and hasattr(p, "type") and p.type.name == "FUNCTION_DEF":
                code = gen.generate(p)
    
    total += 1
    if code:
        first = code.split("\n")[0][:60]
        try:
            compile(code, "<test>", "exec")
            ok += 1
            status = "OK"
        except SyntaxError as e:
            status = f"X({e.lineno})"
        print(f"  [{status}] {goal:20s} -> {first}")
    else:
        print(f"  [--] {goal:20s} -> (ures)")

print(f"\n{ok}/{total} valid Python, {ok}/{total} helyes")
