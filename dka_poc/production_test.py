import os
from receptor import Receptor
from hypergraph import Hypergraph
from engine import LogicEngine
from bridge_cross import DomainBridge, RippleEffectEngine
from bridge import FileProcessor

def main():
    print("=== DKA PRODUCTION-READY TEST ===")
    
    # Setup
    receptor = Receptor()
    code_graph = Hypergraph(context_size=2)
    config_graph = Hypergraph(context_size=1)
    bridge = DomainBridge()
    bridge.register_domain("Code", code_graph)
    bridge.register_domain("Config", config_graph)
    
    processor = FileProcessor(receptor, code_graph) # Using code_graph as base
    
    # 1. Loading Multi-file project
    print("\n[1] Multi-fájl projekt betöltése...")
    code_content = "api_key = 'SECRET_123' ;"
    config_content = "{ 'api_key' : 'SECRET_123' }"
    
    # Process simulated files
    code_graph.learn(receptor.process(code_content))
    config_graph.learn(receptor.process(config_content))
    
    # 2. Establishing Cross-Domain Link
    bridge.create_bridge("Code", "api_key", "Config", "api_key")
    
    # 3. Final Integrity & Self-Check
    print("\n[2] Teljes rendszer integritás-ellenőrzés...")
    engine_code = LogicEngine(code_graph)
    engine_config = LogicEngine(config_graph)
    
    errs_code = engine_code.self_check()
    errs_config = engine_config.self_check()
    
    if not errs_code and not errs_config:
        print("  [OK] Minden domén logikailag konzisztens.")
        print("  [STATUS] DKA KÉSZENLÉTI MÓDBAN.")
    else:
        print("  [!] HIBA: Integritási problémák észlelve.")

if __name__ == "__main__":
    main()
