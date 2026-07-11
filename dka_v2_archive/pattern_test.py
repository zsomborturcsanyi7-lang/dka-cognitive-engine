from pattern_intel import PatternIntelligence
from grammar_parser import GrammarParser
from hypergraph_v2 import HypergraphV2
from node_types import NodeType

parser = GrammarParser()
graph = HypergraphV2()

pi = PatternIntelligence(graph)

codes = {
    "count": "def count_items(items):\n    count = 0\n    for item in items:\n        count += 1\n    return count",
    "check": "def check_value(x, threshold):\n    if x > threshold:\n        return True\n    return False",
}

for name, code in codes.items():
    nodes = parser.parse(code)
    graph.ingest_pattern_tree(nodes)
    for node in nodes:
        if hasattr(node, "type") and node.type == NodeType.FUNCTION_DEF:
            a = pi.analyze(node)
            print(f"=== {name} ===")
            print(f"  Params: {a['parameters']}")
            print(f"  Akkum: {a['needs_init']}")

print()
print("=== Kompatibilitas ===")
funcs = [n for n in graph.patterns.values() if n.type == NodeType.FUNCTION_DEF]
for i in range(len(funcs)):
    for j in range(i+1, len(funcs)):
        comp = pi.compare_patterns(funcs[i], funcs[j])
        print(f"  vs: common={comp['common_vars']}, compatible={comp['compatible']}")
