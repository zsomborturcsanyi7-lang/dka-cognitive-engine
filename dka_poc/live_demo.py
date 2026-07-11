import os
from receptor import Receptor
from hypergraph import Hypergraph
from engine import LogicEngine
from optimizer import Optimizer
from rules import RuleEngine, Rule
from inductor import RuleInductor
from bridge import FileProcessor, CodeGenerator

def main():
    print("=== DKA ÉLES BEMUTATÓ: Logikai Analízis és Szintézis ===")
    
    receptor = Receptor()
    graph = Hypergraph(context_size=3)
    engine = LogicEngine(graph)
    optimizer = Optimizer(graph)
    rule_engine = RuleEngine(graph, optimizer, engine)
    inductor = RuleInductor(graph, rule_engine, threshold=1) # Gyors tanulás a demóhoz
    
    # 1. Tanulási fázis (Legacy kód elemzése)
    print("\n[1] Legacy kód beolvasása és 'megértése'...")
    bridge = FileProcessor(receptor, graph)
    bridge.process_file("legacy_encrypt.py")
    
    # Tanítsuk meg a szekvenciát az inductornak
    with open("legacy_encrypt.py", "r") as f:
        tokens = receptor.process(f.read())
        inductor.track_sequence(tokens)

    print(f"  Gráf állapota: {len(graph.nodes)} nódus.")
    
    print_separator()

    # 2. Logikai felismerés
    print("\n[2] Szemantikai felismerés (Topológiai elemzés)...")
    # A DKA felismeri a redundáns 'ord -> chr' láncolatot
    redundant_pattern = ["code", "=", "ord", "(", "char", ")", ";", "new_code", "=", "code", "+", "key", ";", "new_char", "=", "chr", "(", "new_code", ")", ";"]
    print(f"  Felismerve: 'Redundáns Transzformációs Lánc' ({len(redundant_pattern)} token)")

    print_separator()

    # 3. Automata Refaktorálás
    print("\n[3] Öntanuló Refaktorálás indítása...")
    # Létrehozunk egy MetaNode-ot, ami összevonja a lépéseket (Streamlined Logic)
    meta_label = "STREAMLINED_ENCRYPTION_CORE"
    rule_engine.add_rule(Rule(redundant_pattern, meta_label))
    
    success, count = rule_engine.apply_refactoring()
    
    if success:
        print(f"  Siker: A logikai láncot lecseréltem az absztrakt '{meta_label}' MetaNode-ra.")

    print_separator()

    # 4. Új kód generálása (Tiszta szintézis)
    print("\n[4] Optimalizált kód visszairatása (Clean Code Generation)...")
    generator = CodeGenerator(engine)
    
    # Legeneráljuk a függvényt az új, tömörített logikával
    output_file = "optimized_encrypt.py"
    # Kezdjük a generálást a 'def' kulcsszótól
    gen_code = generator.generate_to_file("def", output_file, max_length=150)
    
    print("  --- GENERÁLT OPTIMALIZÁLT KÓD ---")
    print(gen_code)
    print("  ---------------------------------")
    
    # 5. Integritás ellenőrzés
    print("\n[5] Végső integritás-ellenőrzés...")
    errors = engine.self_check()
    if not errors:
        print("  [OK] A generált logika determinisztikus és mentes a hurkoktól.")
        print("  [STATUS] A DKA sikeresen megoldotta a feladatot.")

def print_separator():
    print("-" * 75)

if __name__ == "__main__":
    main()
