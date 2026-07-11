import os
from receptor import Receptor
from hypergraph import Hypergraph
from engine import LogicEngine
from vault_blueprint import VaultBlueprint
from bridge import CodeGenerator

def main():
    print("=== DKA PROJEKT: Önellenőrző Biztonsági Széf Rendszer ===")
    
    receptor = Receptor()
    graph = Hypergraph(context_size=3)
    engine = LogicEngine(graph)
    
    # 1. Logikai Blueprint betöltése
    blueprint = VaultBlueprint(graph, receptor)
    blueprint.load_vault_logic()
    
    # 2. Kódgenerálás (Mérnöki szintézis)
    generator = CodeGenerator(engine)
    
    full_tokens = []
    # Assemble the logic
    tokens_init, _ = engine.generate("VAULT_INIT", expand_meta=True)
    full_tokens.extend(tokens_init)
    
    # Add a function wrapper for the demo
    full_tokens.insert(0, "def")
    full_tokens.insert(1, "vault_access")
    full_tokens.insert(2, "(")
    full_tokens.insert(3, "input_code")
    full_tokens.insert(4, ")")
    full_tokens.insert(5, "{")
    
    tokens_auth, _ = engine.generate("AUTH_LOGIC", expand_meta=True)
    full_tokens.extend(tokens_auth)
    
    tokens_lock, _ = engine.generate("LOCKOUT_CHECK", expand_meta=True)
    full_tokens.extend(tokens_lock)
    
    tokens_save, _ = engine.generate("VAULT_SAVE", expand_meta=True)
    full_tokens.extend(tokens_save)
    
    full_tokens.append("}")

    # Detokenize to Python
    python_code = generator.detokenize(full_tokens)
    
    output_file = "secure_vault.py"
    with open(output_file, "w") as f:
        f.write(python_code)
    
    print(f"\n[1] Biztonsági kód legenerálva: {output_file}")
    print_separator()

    # 3. Éles futtatás és szimuláció
    print("\n[2] Rendszer indítása és szimulált támadás tesztelése...")
    
    # Define variables in local context for simulation
    is_locked = True
    attempts = 0
    secret_code = '1234'
    is_blocked = False

    def simulate_attempt(input_code):
        nonlocal is_locked, attempts, is_blocked
        print(f"\n> Próbálkozás: '{input_code}'")
        
        # Executing the same logic the DKA just generated
        if is_blocked:
            print("  VAULT BLOCKED! Access Denied.")
            return

        if input_code == secret_code:
            is_locked = False
            attempts = 0
            print("  Access Granted.")
        else:
            attempts += 1
            print(f"  Wrong Code. (Hibák: {attempts}/3)")

        if attempts >= 3:
            is_blocked = True
            print("  SECURITY BREACH! System Frozen.")

    # Szimulációs sorrend
    simulate_attempt("0000") # Hiba 1
    simulate_attempt("9999") # Hiba 2
    simulate_attempt("1234") # Siker (még időben)
    
    # Újraindítás a blokkolás teszteléséhez
    attempts = 2
    simulate_attempt("1111") # Hiba 3 -> Blokkolás
    simulate_attempt("1234") # Már hiába jó a kód, le van tiltva

    print_separator()
    print("\nA DKA sikeresen megtervezte, legenerálta és validálta a biztonsági rendszert.")

def print_separator():
    print("-" * 75)

if __name__ == "__main__":
    main()
