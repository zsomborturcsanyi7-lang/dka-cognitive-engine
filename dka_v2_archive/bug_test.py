"""
DKA V2 — Hibás kód felismerés teszt
=====================================
1. Betanítunk tiszta kódot
2. Adunk hibás változatokat
3. Ellenőrizzük, hogy a DKA észleli-e:
   - Szintaxis hibákat (parser szinten)
   - Strukturális eltéréseket (pattern matching)
   - Logikai hibákat (pl. végtelen ciklus)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from node_types import NodeType
from grammar_parser import GrammarParser
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from inference_engine_v2 import InferenceEngineV2


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def check_syntax(code, label):
    """Szintaxis ellenőrzés Python AST-val."""
    try:
        compile(code, '<check>', 'exec')
        return True, None
    except SyntaxError as e:
        return False, str(e)


def parse_with_dka(parser, code, label):
    """Megpróbálja a DKA parser-rel feldolgozni a kódot."""
    try:
        nodes = parser.parse(code)
        # Ha a fallback tokenizer használatával lett parse-olva,
        # minden nódus primitív lesz, nincs minta réteg
        pattern_count = sum(1 for n in nodes if hasattr(n, 'type') and 
                          n.type in (
                              NodeType.FUNCTION_DEF, NodeType.FOR_LOOP,
                              NodeType.IF_STATEMENT, NodeType.WHILE_LOOP,
                              NodeType.ASSIGNMENT, NodeType.RETURN_STMT,
                              NodeType.CLASS_DEF, NodeType.BINARY_OP,
                          ))
        return nodes, pattern_count, None
    except Exception as e:
        return [], 0, str(e)


def structural_analysis(engine, graph, code, label, max_matches=3):
    """Elemzi a kód strukturális egyezését a tanult mintákkal."""
    parser = GrammarParser()
    nodes, pattern_count, error = parse_with_dka(parser, code, label)
    
    report = []
    report.append(f"  Parsolt nódusok: {len(nodes)}")
    report.append(f"  Strukturált minták: {pattern_count}")
    
    if error:
        report.append(f"  Parser hiba: {error}")
        return "\n".join(report)
    
    if pattern_count == 0 and len(nodes) > 0:
        report.append(f"  [FIGYELMEZTETES] A kód lapos token-ekre esett szet!")
        report.append(f"  Ez azt jelenti, hogy a GrammarParser nem ismert fel")
        report.append(f"  benne ismert Python strukturakat.")
    
    # Hasonlítsuk össze a tanult mintákkal
    matches = []
    for node in nodes:
        if not hasattr(node, 'type'):
            continue
        for pid, pattern in graph.patterns.items():
            if pattern.type == node.type:
                match = engine.match_pattern(node, pattern)
                if match["match"]:
                    matches.append((node.type.name, match["percentage"]))
    
    if matches:
        report.append(f"  Egyező tanult mintak: {len(matches)}")
        for tname, pct in matches[:max_matches]:
            report.append(f"    - {tname}: {pct}% egyezes")
    else:
        report.append(f"  [FIGYELMEZTETES] Nincs egyezes egyetlen tanult mintaval sem!")
    
    return "\n".join(report)


# ─── 1. FÁZIS: TISZTA KÓD BETANÍTÁSA ────────────────────────────────

print_header("1. FÁZIS: Tiszta kód betanítása")

graph = HypergraphV2()
engine = InferenceEngineV2(graph)
parser = GrammarParser()

clean_codes = {
    "factorial": '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
''',
    "bubble_sort": '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
''',
    "file_read": '''
def read_file(path):
    with open(path) as f:
        return f.read()
''',
    "counter": '''
class Counter:
    def __init__(self):
        self.count = 0
    def increment(self):
        self.count += 1
    def get(self):
        return self.count
'''
}

for name, code in clean_codes.items():
    nodes = parser.parse(code)
    graph.ingest_pattern_tree(nodes, source=name)
    print(f"  Tanultam: {name} ({len(nodes)} node)")


# ─── 2. FÁZIS: HIBÁS KÓD TESZTELÉSE ─────────────────────────────────

print_header("2. FÁZIS: Hibás kód tesztelése")

buggy_cases = [
    # 1. Szintaxis hiba
    ("Szintaxis hiba: hiányzó kettőspont", '''
def hello()
    print("world")
'''),
    # 2. Szintaxis hiba: eltérés
    ("Szintaxis hiba: hiányzó zárójel", '''
def add(a, b:
    return a + b
'''),
    # 3. Logikai hiba: végtelen rekurzió (rossz base case)
    ("Logikai hiba: rossz base case (végtelen rekurzió)", '''
def factorial(n):
    if n < 0:
        return n
    return n * factorial(n - 1)
'''),
    # 4. Logikai hiba: végtelen ciklus
    ("Logikai hiba: végtelen while ciklus", '''
def forever():
    while True:
        pass
    return 0
'''),
    # 5. Helyes kód (kontroll)
    ("HELYES (kontroll): tiszta faktoriális", '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''),
    # 6. Helyes kód variáció (kontroll)
    ("HELYES (kontroll): új függvény, ismert minták", '''
def countdown(n):
    if n <= 0:
        return
    print(n)
    countdown(n - 1)
'''),
    # 7. Névütközés, de struktúra helyes
    ("HELYES (variacio): más név, azonos struktúra", '''
def my_sort(data):
    n = len(data)
    for i in range(n):
        for j in range(n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data
'''),
    # 8. Rossz indentálás
    ("Szintaxis hiba: rossz indentálás", '''
def foo():
    if True:
    print("hi")
'''),
]

for label, buggy_code in buggy_cases:
    print(f"\n--- {label} ---")
    
    # 1. Python compiler szintaxis ellenőrzés
    syntax_ok, syntax_err = check_syntax(buggy_code, label)
    if not syntax_ok:
        print(f"  [Python Syntax Error] {syntax_err}")
    
    # 2. DKA strukturális elemzés
    analysis = structural_analysis(engine, graph, buggy_code, label)
    print(analysis)
    
    # 3. Következtetés
    if not syntax_ok:
        print(f"  -> KOVETKEZTETES: A DKA-nak a koddal kapcsolatban:")
        print(f"     A Python AST parser dobott hibát - a GrammarParser")
        print(f"     token-alapu fallback-re kapcsol, ami elveszti a strukturat.")
    elif "Nincs egyezes" in analysis:
        print(f"  -> KOVETKEZTETES: A DKA strukturális elterest talalt!")
        print(f"     A kod nem egyezik egyetlen tanult mintaval sem.")
    else:
        print(f"  -> KOVETKEZTETES: A DKA ismert mintakat talalt a kodban.")
        print(f"     Strukturalisan helyesnek tunik.")


# ─── 3. FÁZIS: JAVÍTÁSI KÍSÉRLET ────────────────────────────────────

print_header("3. FÁZIS: Javítási kísérlet")

print("""
Ha a DKA hibát talál, megpróbálhatjuk a legközelebbi
tanult minta alapján kijavítani a kódot.

Ez a funkció még fejlesztés alatt áll. Jelenleg:
- A pattern matching megmondja, MELYIK minta hasonlít
- A constructive generator ki tudja generálni a helyes változatot
- A gap-filling még nem tud kreatívan új kódot írni a hibás helyére

Példa: ha a "factorial(n - 1)" helyett "factorial(n" van,
a pattern matching alacsony pontszámot ad, de a legközelebbi
illeszkedő mintát ki tudja generálni.
""")

# Próbáljuk ki: mi a legközelebbi tanult minta a rossz faktoriálishoz?
print("Legkozelebbi tanult minta a hibas factorial-hoz:")
buggy_fact = '''
def factorial(n):
    if n < 0:
        return n
    return n * factorial(n - 1)
'''

nodes, _, _ = parse_with_dka(parser, buggy_fact, "buggy_fact")
for node in nodes:
    if hasattr(node, 'type') and node.type == NodeType.FUNCTION_DEF:
        analogies = engine.find_analogies(node, max_results=2)
        for a in analogies:
            name_node = a["pattern"].children.get("name", [None])[0] if a["pattern"].children.get("name") else None
            pname = name_node.value if name_node else "?"
            print(f"  Hasonlo minta: {a['pattern'].type.name} ({pname}) - {a['similarity']}%")
        
        # Generáljuk a helyes változatot
        from constructive_generator import ConstructiveGenerator
        gen = ConstructiveGenerator(graph)
        correct = gen.generate(node)
        
        print(f"\n  Helyes változat (a legkozelebbi analogia alapjan):")
        print(f"  {correct[:120]}...")
        break

print()
print_header("TESZT VÉGE")
print("""
ÖSSZEGZÉS:
  - Syntax error: a Python AST parser dobja, a GrammarParser fallback-re kapcsol
  - Strukturális eltérés: a pattern matching alacsony pontszámot ad
  - A DKA V2 jelenleg: felismeri a hibát, de nem tudja kijavítani
  - Következő lépés: javító motor (error-correcting synthesis)
""")
