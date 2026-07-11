import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'dka_poc'))

from ast_receptor import ASTReceptor
from hypergraph import Hypergraph
from engine import LogicEngine
from inference_engine import InferenceEngine
from ast_bridge import ASTCodeGenerator
from bridge import FileProcessor

def run_ast_tests():
    print("=== DKA AST (Abstract Syntax Tree) Evolúciós Teszt ===")
    
    receptor = ASTReceptor()
    graph = Hypergraph(context_size=2)
    logic_engine = LogicEngine(graph)
    inference = InferenceEngine(graph, logic_engine)
    processor = FileProcessor(receptor, graph)
    generator = ASTCodeGenerator(logic_engine)
    
    print("\n[1] AST Tudásbázis felépítése (Tökéletes Szintaktikai Blokkok)...")
    
    code_web = """
def handle_request(req):
    if req.is_valid():
        db.save(req.data)
        return Response(200)
    else:
        return Response(400)
    """
    
    # AST feldolgozás
    tokens = receptor.process(code_web)
    print("AST Szimbólumok:", tokens)
    
    graph.learn(tokens, domain="web", source="web_module.py")
    
    print(f"Gráf csomópontok száma (AST alapokon): {len(graph.nodes)}")
    
    print("\n[2] Kényszerített Útkeresés (Constraint Solving az AST-ben)...")
    print("Cél: Webes folyamat rekonstrukciója (FUNC -> STMT -> RETURN)")
    
    inference.allowed_domains = {"web"}
    
    # Ebben az új rendszerben a csomópontok komplett kódrészletek
    constraints = ["FUNC:handle_request(req)", "IF:req.is_valid()", "RETURN:Response(200)"]
    sequence, success = inference.solve_with_constraints(constraints[0], constraints[1:])
    print(f"Logikai sorrend: {' -> '.join(sequence)}")
    
    print("\n[3] Determinisztikus Visszaalakítás (Tökéletes Python kód)...")
    code_output = generator.detokenize(sequence)
    print("Generált szintaktika:\n")
    print("----------------------------------------")
    print(code_output)
    print("----------------------------------------")
    print("\n=== TESZT VÉGE ===")

if __name__ == "__main__":
    run_ast_tests()
