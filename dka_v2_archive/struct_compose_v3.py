"""
DKA Core — Structure Composition Engine V3
===========================================
A ReasoningEngine hiányzó része: hogyan rakjunk össze egy programot,
amire nincs közvetlen tanult minta.

Új architektúra: Python kód string → GrammarParser → PatternNode.
Nem kell kézzel építeni a nódusokat.

Folyamat:
1. Scaffold kiválasztása a goal alapján (keyword matching)
2. A scaffold kódját a GrammarParser feldolgozza → PatternNode fa
3. A fa adaptálása: függvénynév, paraméterek, visszatérési érték
4. Generálás a ConstructiveGenerator-ral
"""

from __future__ import annotations
from typing import Optional
from node_types import PatternNode, NodeType, Role, PrimitiveNode
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from grammar_parser import GrammarParser


class ProgramScaffoldV3:
    """
    Python kód string → PatternNode scaffold-ok.
    Minden scaffold egy komplett, működő Python függvény,
    amit aztán a goal-hoz igazítunk (variable renaming + parameter adapt).
    """

    # Scaffold-ok: kulcsszavak → (kód, leírás)
    SCAFFOLDS = {}

    @staticmethod
    def _register(keywords: list[str], code: str, description: str = ""):
        """Egy scaffold regisztrálása kulcsszavakkal."""
        for kw in keywords:
            ProgramScaffoldV3.SCAFFOLDS[kw] = (code, description)

    @staticmethod
    def select(goal: str) -> Optional[str]:
        """
        Kiválasztja a legmegfelelőbb scaffold-ot a goal alapján.
        Kulcsszó matching: hány scaffold-kulcsszó szerepel a goal-ban.
        """
        goal_lower = goal.lower()
        goal_words = set(goal_lower.split())

        best_match = None
        best_count = 0

        for keyword, (code, desc) in ProgramScaffoldV3.SCAFFOLDS.items():
            kw_words = set(keyword.split())
            overlap = len(goal_words & kw_words)
            # Szubstring matching is
            for kw in kw_words:
                for gw in goal_words:
                    if kw in gw or gw in kw:
                        overlap += 0.5
            if overlap > best_count:
                best_count = overlap
                best_match = (code, desc)

        if best_count >= 1.0:
            return best_match[0]
        return None


# ─── SCAFFOLD DEFINÍCIÓK ────────────────────────────────────────

ProgramScaffoldV3._register(
    keywords=["guess", "number", "game"],
    description="Számkitalálós játék: random + while + input + if/elif/else",
    code="""
def guess_game():
    import random
    target = random.randint(1, 100)
    while True:
        guess = int(input("Tipp: "))
        if guess == target:
            print("Helyes!")
            break
        elif guess < target:
            print("Tippelj nagyobbat")
        else:
            print("Tippelj kisebbet")
""")

ProgramScaffoldV3._register(
    keywords=["word", "count", "frequency", "counter", "file"],
    description="Szógyakoriság számláló: open → split → dict → return",
    code="""
def word_frequency(path):
    text = open(path).read()
    words = text.split()
    freq = {}
    for w in words:
        if w in freq:
            freq[w] += 1
        else:
            freq[w] = 1
    return freq
""")

ProgramScaffoldV3._register(
    keywords=["csv", "file", "read", "process", "data"],
    description="CSV feldolgozó: open → read → process → return",
    code="""
def process_csv(path):
    data = []
    with open(path, 'r') as f:
        for line in f:
            row = line.strip().split(',')
            data.append(row)
    return data
""")

ProgramScaffoldV3._register(
    keywords=["calculator", "calc", "compute", "math", "operation"],
    description="Egyszerű számológép: input → compute → output",
    code="""
def calculator(a, op, b):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        return a / b
    else:
        return None
""")

ProgramScaffoldV3._register(
    keywords=["search", "find", "lookup", "filter"],
    description="Lista kereső: iter → condition → return",
    code="""
def search_list(items, target):
    result = []
    for item in items:
        if item == target:
            result.append(item)
    return result
""")


class StructuredComposerV3:
    """
    Összetett kompozíció: scaffold kiválasztása → parser → adaptáció → generálás.
    """

    def __init__(self, graph: HypergraphV2, semantics: SemanticIndex):
        self.graph = graph
        self.semantics = semantics
        self.parser = GrammarParser()
        self.generator = ConstructiveGenerator(graph)

    def _extract_function_name(self, goal: str) -> str:
        """Goal-ból értelmes függvénynév generálása."""
        import re
        words = re.findall(r'[a-zA-Z]\w*', goal.lower())
        # Szűrjünk gyakori szavakat
        stop_words = {'a', 'an', 'the', 'in', 'of', 'for', 'to', 'and', 'or',
                      'by', 'with', 'from', 'at', 'is', 'are', 'be', 'was',
                      'all', 'some', 'any', 'each', 'every', 'this', 'that'}
        meaningful = [w for w in words if w not in stop_words and len(w) > 1]
        if not meaningful:
            return "process"
        return "_".join(meaningful[:4])

    def compose(self, goal: str) -> Optional[str]:
        """
        Main entry point: goal → scaffold → kód.
        """
        code_template = ProgramScaffoldV3.select(goal)
        if not code_template:
            return None

        # 1. Parser: kód → PatternNode fa
        nodes = self.parser.parse(code_template)

        # 2. Keressük a FUNCTION_DEF-et
        func_node = None
        for node in nodes:
            if isinstance(node, PatternNode) and node.type == NodeType.FUNCTION_DEF:
                func_node = node
                break

        if not func_node:
            return None

        # 3. Adaptáció: függvénynév a goal alapján
        new_name = self._extract_function_name(goal)
        name_nodes = func_node.children.get("name", [])
        if name_nodes:
            name_nodes[0].value = new_name

        # 4. Generálás
        code = self.generator.generate(func_node)

        # 5. Validálás
        try:
            compile(code, '<dka_scaffold>', 'exec')
            return code
        except SyntaxError as e:
            return None
