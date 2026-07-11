import os
import time
from receptor import Receptor
from hypergraph import Hypergraph
from bridge import FileProcessor
from bridge_transformer import TransformerBridge

def massive_training_run():
    print("=== DKA MASSIVE TRAINING WITH DOMAIN FILTERING ===")
    
    receptor = Receptor()
    graph = Hypergraph(context_size=4)
    processor = FileProcessor(receptor, graph)
    
    # Domain Mapping
    sources = {
        "general_programming": [
            "dka_poc/programming_corpus.txt",
            "dka_poc/training_samples.txt",
            "dka_poc/legacy_sort.py",
            "dka_poc/legacy_encrypt.py"
        ],
        "internal_logic": [
            "dka_poc/engine.py",
            "dka_poc/hypergraph.py",
            "dka_poc/inference_engine.py",
            "dka_poc/receptor.py"
        ]
    }
    
    print("\n[STEP 1] Ingesting code corpus with domain tags...")
    for domain, files in sources.items():
        print(f"  Tanulás Domén: '{domain}'")
        for file_path in files:
            if os.path.exists(file_path):
                print(f"    Fájl: {file_path}...")
                processor.process_file(file_path, domain=domain)
    
    # 2. Complex Evaluation with Domain Restriction
    print("\n[STEP 2] Restricted Multi-Domain Logic Synthesis Test...")
    bridge = TransformerBridge(graph)
    
    # SET DOMAIN FILTER: Only use general programming knowledge for code generation
    bridge.inference.allowed_domains = {"general_programming"}
    
    complex_query = "Készíts egy programot, ami beolvas egy fájlt, gyorsrendezéssel (quicksort) lerendezi az adatokat, és az eredményt elküldi egy API-nak!"
    
    print(f"  Complex Query: '{complex_query}'")
    print(f"  [Security] Domén-szűrő AKTÍV: {bridge.inference.allowed_domains}")
    
    result = bridge.process_query(complex_query)
    
    print(f"\n[DKA CLEAN RESPONSE (No Internal Leakage)]\n{result}")

if __name__ == "__main__":
    massive_training_run()
