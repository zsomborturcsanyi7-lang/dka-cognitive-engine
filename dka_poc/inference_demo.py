from receptor import Receptor
from hypergraph import Hypergraph
from engine import LogicEngine
from inference_engine import InferenceEngine

def run_inference_demo():
    print("=== DKA LOGIKAI KÖVETKEZTETÉS ÉS TRANSFORMER BRIDGE DEMÓ ===")
    
    receptor = Receptor()
    graph = Hypergraph(context_size=2)
    engine = LogicEngine(graph)
    infer = InferenceEngine(graph, engine)

    # 1. Tanulási fázis (A rendszer "tapasztalatokat" gyűjt)
    print("\n[1] Tanulási fázis: Elemi összefüggések rögzítése...")
    
    # Tapasztalat A: Hogyan kell adatot kérni és tárolni
    graph.learn(receptor.process("input_data = get_user_input ( ) ;"))
    
    # Tapasztalat B: Hogyan kell listát tisztítani
    graph.learn(receptor.process("clean_data = [ x for x in input_data if x != None ] ;"))
    
    # Tapasztalat C: Hogyan kell eredményt menteni
    graph.learn(receptor.process("save_to_db ( clean_data ) ;"))

    print(f"  Gráf mérete: {len(graph.nodes)} nódus.")

    # 2. Szimulált Transformer Interfész
    # A Transformer lefordítja a kérdést ("Kérj adatot és mentsd el!") logikai kényszerekké (Constraints).
    print("\n[2] Szimulált Transformer fordítás:")
    user_query = "Kérj adatot a felhasználótól és mentsd el a tisztított listát az adatbázisba!"
    
    # A Transformer kimenete (logikai mérföldkövek):
    constraints = ["input_data", "clean_data", "save_to_db"]
    print(f"  Kérdés: '{user_query}'")
    print(f"  DKA logikai célpontok: {constraints}")

    # 3. Determinisztikus Következtetés
    print("\n[3] DKA Logikai következtetés (Inference Engine) futtatása...")
    
    # A rendszer megpróbálja összekötni a pontokat transzitivitás alapján
    # Bár sosem látta az "input_data" és a "save_to_db" kapcsolatát közvetlenül egy sorban,
    # a "clean_data" nóduszon keresztül képes a dedukcióra.
    
    full_logic, success = infer.solve_with_constraints("input_data", constraints)
    
    if success:
        print("\n[4] Generált megoldás (Logikailag hibátlan):")
        # Detokenize (egyszerűsített megjelenítés)
        print("  " + " ".join(full_logic))
    else:
        print("\n[!] A DKA nem tudott logikai kapcsolatot teremteni a kért fogalmak között.")

if __name__ == "__main__":
    run_inference_demo()
