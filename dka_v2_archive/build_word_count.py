"""
DKA V2 — Word Frequency Program
=================================
Egy valódi, használható program: szógyakoriság számláló fájlból.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from struct_compose import SimplePatternFactory, SlotFiller, ProgramScaffold

g = HypergraphV2.from_json_file("dka_trained_500.json")
sem = SemanticIndex(g)
sem.index_all()
gen = ConstructiveGenerator(g)
factory = SimplePatternFactory()
filler = SlotFiller(g, sem)

# ===== SCAFFOLD ÉPÍTÉS KÉZZEL =====
# word_frequency(path): read → split → count → return

read_val = PatternNode("ASSIGNMENT")
read_val.children["targets"] = [Node("VARIABLE", value="text")]
read_val.children["value"] = [PatternNode("FUNCTION_CALL")]

split_val = PatternNode("ASSIGNMENT")
split_val.children["targets"] = [Node("VARIABLE", value="words")]
split_val.children["value"] = [PatternNode("FUNCTION_CALL")]

loop = PatternNode("FOR_LOOP")
loop.children["target"] = [Node("VARIABLE", value="word")]
loop.children["iter"] = [Node("VARIABLE", value="words")]
loop_body = PatternNode("BLOCK")
loop.children["body"] = [loop_body]
count_assign = PatternNode("ASSIGNMENT")
count_assign.children["targets"] = [PatternNode("INDEX_ACCESS")]
loop_body.children["statements"] = [count_assign]

ret = PatternNode("RETURN_STMT")
ret.children["value"] = []

body = PatternNode("BLOCK")
body.children["statements"] = [read_val, split_val, loop, ret]

func = PatternNode("FUNCTION_DEF")
func.children["name"] = [Node("VARIABLE", value="word_frequency")]
func.children["params"] = [Node("VARIABLE", value="path", role="param")]
func.children["body"] = [body]

# Kitöltés
filled = filler.fill(func, "count word frequency in a file")
code = gen.generate(filled)
print(code)
valid = False
try:
    compile(code, "<test>", "exec")
    valid = True
    print("  [OK] Valid Python!")
except SyntaxError as e:
    print(f"  [HIBA] {e.lineno}: {e.msg}")

# Ha valid, mentsük ki
if valid:
    with open("word_frequency.py", "w") as f:
        f.write(code)
    print("  Mentve: word_frequency.py")
