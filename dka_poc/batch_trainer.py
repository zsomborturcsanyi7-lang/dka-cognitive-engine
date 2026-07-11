import os
import json
from receptor import Receptor
from hypergraph import Hypergraph
from bridge import FileProcessor
from bridge_transformer import TransformerBridge

def batch_train():
    print("=== DKA BATCH TRAINING: Programozási Minták Tanulása ===")
    
    receptor = Receptor()
    graph = Hypergraph(context_size=3) # Higher context for better code structure
    processor = FileProcessor(receptor, graph)
    
    # 1. Tanítási forrásfájlok kijelölése
    training_files = [
        "dka_poc/training_samples.txt",
        "dka_poc/legacy_sort.py",
        "dka_poc/legacy_encrypt.py",
        "dka_poc/game_logic.py"
    ]
    
    print("\n[1] Fájlok beolvasása és neurális integráció...")
    for file_path in training_files:
        if os.path.exists(file_path):
            print(f"  Tanulás: {file_path}...")
            success = processor.process_file(file_path)
            if success:
                print(f"    [OK] {file_path} integrálva.")
        else:
            print(f"  [!] Fájl nem található: {file_path}")

    print(f"\n[2] Tanítás befejezve. Gráf mérete: {len(graph.nodes)} nódus.")
    
    # 3. Tudás perzisztencia (Mentés JSON-be)
    graph_data = graph.to_json()
    with open("dka_poc/dka_graph.json", "w") as f:
        f.write(graph_data)
    print("  A DKA tudása elmentve: dka_poc/dka_graph.json")

    # 4. Tesztelés a friss tudásbázissal
    print("\n[3] Tesztelés a frissen szerzett tudással...")
    bridge = TransformerBridge(graph)
    
    # Olyan kérdés, ami a tanult fájlokra épít
    test_query = "Készíts egy buborékos rendezést (sort) a listára!"
    print(f"  Kérdés: '{test_query}'")
    
    result = bridge.process_query(test_query)
    print(f"\n[DKA Válasza]\n{result}")

if __name__ == "__main__":
    batch_train()
