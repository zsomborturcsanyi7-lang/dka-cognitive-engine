import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'dka_poc'))

from ast_receptor import ASTReceptor
from hypergraph import Hypergraph
from engine import LogicEngine
from inference_engine import InferenceEngine
from ast_bridge import ASTCodeGenerator

def run_abstraction_test():
    print("=== DKA Változó-Absztrakciós (Sablonosító) Teszt ===")
    
    receptor = ASTReceptor()
    graph = Hypergraph(context_size=2)
    logic_engine = LogicEngine(graph)
    inference = InferenceEngine(graph, logic_engine)
    generator = ASTCodeGenerator(logic_engine)
    
    print("\n[1] Tanulás két különböző kód alapján...")
    
    # Kód 1: Webshop fizetés (változók: cart, total)
    code_web = """
def process_order(cart):
    if cart.is_valid():
        save_db(cart.total)
        return True
    """
    
    # Kód 2: Felhasználó hitelesítés (változók: user, session)
    # A struktúra ugyanaz: egy IF, ami meghív egy .is_valid()-ot, majd egy mentés, majd return True.
    code_auth = """
def verify_login(user):
    if user.is_valid():
        log_session(user.session)
        return True
    """
    
    tokens_web = receptor.process(code_web)
    print("Webshop Tokens:", tokens_web)
    graph.learn(tokens_web, domain="general", source="web.py")
    
    tokens_auth = receptor.process(code_auth)
    print("Auth Tokens:", tokens_auth)
    graph.learn(tokens_auth, domain="general", source="auth.py")
    
    print(f"\nGráf csomópontok száma: {len(graph.nodes)}")
    print("Mivel a struktúra azonos volt, a csomópontok számának nagyon kicsinek kell lennie (nem duplikálódott a gráf)!")
    
    print("\n[2] Kód Generálás a Sablonok alapján...")
    
    # Generáltassuk le a sikeres ágat
    constraints = ["FUNC:VAR_1(VAR_2)", "IF:VAR_2.is_valid()", "RETURN:True"]
    sequence, success = inference.solve_with_constraints(constraints[0], constraints[1:])
    
    print("\n[3] Generált Sablon Kód (Készen áll az LLM általi kitöltésre):")
    code_output = generator.detokenize(sequence)
    print("----------------------------------------")
    print(code_output)
    print("----------------------------------------")

if __name__ == "__main__":
    run_abstraction_test()
