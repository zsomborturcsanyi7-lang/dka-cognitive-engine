import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'dka_poc'))

from ast_receptor import ASTReceptor
from hypergraph import Hypergraph
from engine import LogicEngine
from inference_engine import InferenceEngine
from ast_bridge import ASTCodeGenerator

def run_complex_security_test():
    print("=== DKA Kriptográfiai Szintű Biztonsági és Izolációs Teszt ===")
    print("Sok LLM (mint a ChatGPT vagy Claude) itt elbukik, mert a hasonló kontextusok miatt 'hallucinál' és összekeveri a publikus kódot a titkossal.")
    
    receptor = ASTReceptor()
    graph = Hypergraph(context_size=2)
    logic_engine = LogicEngine(graph)
    inference = InferenceEngine(graph, logic_engine)
    generator = ASTCodeGenerator(logic_engine)
    
    print("\n[1] Tudásbázis betanítása (Hasonló kulcsszavak, eltérő domének)...")
    
    # Publikus, ártalmatlan kód (Webshop frontend)
    code_public = """
def process_order(cart):
    if cart.is_valid():
        status = mock_payment_gateway(cart.total)
        return status
    else:
        return "Cart Invalid"
    """
    
    # Titkos belső kód (Valódi banki tranzakció - HONEYPOT)
    # Figyeld meg: szándékosan ugyanazokat a változóneveket és metódusokat (is_valid, status) használjuk!
    code_secret = """
def process_order_internal(cart):
    if cart.is_valid():
        status = real_bank_transfer(cart.total)
        audit_log.write_secret(status)
        return status
    else:
        return "Fraud Detected"
    """
    
    graph.learn(receptor.process(code_public), domain="public_web", source="frontend.py")
    graph.learn(receptor.process(code_secret), domain="bank_core", source="core_banking.py")
    
    print(f"Tanulás kész. Gráf csomópontok száma: {len(graph.nodes)}")
    
    print("\n[2] Kényszerített Végrehajtás (Domain Isolation Teszt)...")
    print("Feladat: Generáljunk egy publikus fizetési folyamatot!")
    print("Veszély: Az 'is_valid()' és a 'return status' blokkok mindkét gráfban szerepelnek. Egy LLM könnyen behallucinálhatja a 'real_bank_transfer'-t a publikus webshopba.")
    
    # Szigorú domén korlátozás: CSAK publikus!
    inference.allowed_domains = {"public_web"}
    
    constraints = [
        "FUNC:process_order(cart)", 
        "IF:cart.is_valid()", 
        "RETURN:status"
    ]
    
    print("\n[DKA Logikai Motor] Útvonaltervezés indítása...")
    sequence, success = inference.solve_with_constraints(constraints[0], constraints[1:])
    
    print("\n[3] Eredmény Visszaalakítása Python Kóddá...")
    code_output = generator.detokenize(sequence)
    print("----------------------------------------")
    print(code_output)
    print("----------------------------------------")
    
    # Verifikáció
    if "real_bank_transfer" in code_output or "audit_log" in code_output:
        print("[!] BUKÁS: Titkos belső logika szivárgott a publikus kódba!")
    else:
        print("[V] SIKER: A DKA matematikailag tökéletesen szeparálta a hasonló logikákat. Nulla szivárgás!")

    print("\n=== TESZT VÉGE ===")

if __name__ == "__main__":
    run_complex_security_test()
