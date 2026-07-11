import sys
import os

from receptor import Receptor
from hypergraph import Hypergraph
from engine import LogicEngine
from inference_engine import InferenceEngine
from bridge import FileProcessor, CodeGenerator

def run_tests():
    print("=== DKA (Deterministic Knowledge Architecture) Összefogó Teszt ===")
    
    receptor = Receptor()
    graph = Hypergraph(context_size=2)
    logic_engine = LogicEngine(graph)
    inference = InferenceEngine(graph, logic_engine)
    processor = FileProcessor(receptor, graph)
    generator = CodeGenerator(logic_engine)
    
    print("\n[1] Tudásbázis felépítése (Különböző domének és források)...")
    
    # Készítünk néhány fiktív "forrás" kódot
    code_web = """
def handle_request(req):
    if req.is_valid():
        db.save(req.data)
        return Response(200)
    else:
        return Response(400)
    """
    
    code_math = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)
    """
    
    code_secret = """
def internal_auth_logic(user):
    secret_key = "12345"
    if user.key == secret_key:
        grant_access()
    """
    
    # Betanítás a graph.learn segítségével, közvetítve tokeneket
    graph.learn(receptor.process(code_web), domain="web", source="web_module.py")
    graph.learn(receptor.process(code_math), domain="math", source="math_module.py")
    graph.learn(receptor.process(code_secret), domain="internal", source="auth_module.py")
    
    print(f"Gráf csomópontok száma: {len(graph.nodes)}")
    
    print("\n[2] Logikai Fókusz (Logical Focus) Teszt...")
    print("Cél: A rendszernek egyértelmű logikai útvonalat kell találnia forráson belül.")
    inference.allowed_domains = {"math", "web", "internal"}
    path, msg = inference.deduce_path("def", "calculate_fibonacci")
    print(f"Út keresése (def -> calculate_fibonacci): {' -> '.join(path) if path else msg}")
    
    print("\n[3] Domén-szűrés (Domain Filtering) Teszt...")
    print("Cél: 'web' doménre korlátozva nem érheti el a belső titkos logikát (internal_auth_logic).")
    inference.allowed_domains = {"web"}
    path, msg = inference.deduce_path("def", "internal_auth_logic")
    print(f"Keresés tiltott doménbe (def -> internal_auth_logic): {msg}")
    
    print("\n[4] Kényszerített Útkeresés (Constraint Solving)...")
    print("Cél: Készítsen egy folyamatot 'def' ponttól 'Response'-ig a web doménen belül.")
    inference.allowed_domains = {"web"}
    constraints = ["def", "req", "if", "return", "Response"]
    sequence, success = inference.solve_with_constraints(constraints[0], constraints[1:])
    print(f"Logikai sorrend: {' '.join(sequence)}")
    
    print("\n[5] Determinisztikus Visszaalakítás Kóddá...")
    code_output = generator.detokenize(sequence)
    print("Generált szintaktika:\n")
    print(code_output)

    print("\n=== TESZT VÉGE ===")

if __name__ == "__main__":
    run_tests()
