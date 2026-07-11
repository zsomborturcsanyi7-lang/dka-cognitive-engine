import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'dka_poc'))

from ast_receptor import ASTReceptor
from hypergraph import Hypergraph
from engine import LogicEngine
from inference_engine import InferenceEngine
from ast_bridge import ASTCodeGenerator

def run_game_test():
    print("=== DKA Játékfejlesztés Teszt ===")
    
    receptor = ASTReceptor()
    graph = Hypergraph(context_size=2)
    logic_engine = LogicEngine(graph)
    inference = InferenceEngine(graph, logic_engine)
    generator = ASTCodeGenerator(logic_engine)
    
    print("\n[1] A 'Világtudás' betöltése...")
    # A DKA "üres lappal" indul. Ahhoz, hogy játékot írjon, előbb látnia kell játék-logikát.
    # Betáplálunk neki egy egyszerű Számkitaláló (Guess the number) játék struktúrát.
    game_corpus = """
def play_guessing_game(target):
    guess = int(input("Tippelj: "))
    if guess == target:
        print("Nyertél!")
        return True
    else:
        print("Nem talált!")
        return False
    """
    
    graph.learn(receptor.process(game_corpus), domain="games", source="guess_game.py")
    print("Játék logika megtanulva az AST gráfba.")
    
    print("\n[2] Játék Generálása (Útvonal kényszerítéssel)...")
    print("Megkérjük a DKA-t, hogy rakjon össze egy játékmenetet, ami a győzelemmel ér véget.")
    inference.allowed_domains = {"games"}
    
    # Itt mondjuk meg neki, hogy mik a fő "mérföldkövek" (Kezdés -> Feltétel -> Nyerés)
    constraints = ["FUNC:play_guessing_game(target)", "IF:guess == target", "RETURN:True"]
    
    sequence, success = inference.solve_with_constraints(constraints[0], constraints[1:])
    
    print("\n[3] Generált Python Kód:")
    code_output = generator.detokenize(sequence)
    print("----------------------------------------")
    print(code_output)
    print("----------------------------------------")

if __name__ == "__main__":
    run_game_test()
