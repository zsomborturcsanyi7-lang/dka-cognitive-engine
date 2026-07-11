from receptor import Receptor
from hypergraph import Hypergraph
from engine import LogicEngine
from inference_engine import InferenceEngine
from bridge import CodeGenerator

class TransformerBridge:
    """
    Acts as the interface between a natural language model (Transformer)
    and the Deterministic Cognitive Architecture (DKA).
    """
    def __init__(self, graph):
        self.graph = graph
        self.engine = LogicEngine(graph)
        self.inference = InferenceEngine(graph, self.engine)
        self.generator = CodeGenerator(self.engine)

    def process_query(self, natural_language_query):
        """
        Simulates the Transformer's role: translating NL to DKA Constraints.
        In a production environment, this would call a real LLM.
        """
        print(f"\n[Transformer] Fordítás: '{natural_language_query}'")
        
        # Simulated NLP Extraction
        # For this PoC, we map keywords to existing graph concepts
        extracted_goals = []
        words = natural_language_query.lower().replace("!", "").replace(".", "").split()
        
        # Fuzzy keyword matching
        query_lower = natural_language_query.lower()
        
        mapping = {
            "rendez": ["def", "sort", "for", "if", "data", "return"],
            "titkos": ["def", "encrypt", "text", "result", "return"],
            "ciklus": ["for", "range", "in"],
            "adat": ["data", "input_data", "clean_data"],
            "ment": ["save_to_db", "log_event"]
        }

        for key, targets in mapping.items():
            if key in query_lower:
                extracted_goals.extend(targets)

        # Also look for exact node values in the query
        for node in self.graph.nodes.values():
            if len(node.value) > 2 and node.value.lower() in query_lower:
                extracted_goals.append(node.value)

        # Deduplicate and maintain logical order
        unique_goals = []
        for g in extracted_goals:
            if g not in unique_goals: unique_goals.append(g)

        if not unique_goals:
            return "Sajnálom, nem találtam ismert logikai fogalmat a kérésben."

        print(f"[Transformer] Kinyert logikai célok: {unique_goals}")
        
        # Hand over to DKA for deterministic reasoning
        return self._dka_reasoning(unique_goals)

    def _dka_reasoning(self, goals):
        """
        The DKA core performs the actual logical synthesis.
        """
        print("[DKA] Determinisztikus következtetés megkezdése...")
        
        # Start from the first goal or a default start node
        start_val = goals[0]
        full_path, success = self.inference.solve_with_constraints(start_val, goals)
        
        if success:
            # Generate actual Python-like code from the logic
            code = self.generator.detokenize(full_path)
            return code
        else:
            return "A DKA nem tudott hibátlan logikai láncot építeni a kért elemek között."

def main():
    print("=== DKA HIBRID TRANSFORMER-DKA RENDSZER SZIMULÁCIÓ ===")
    
    # Initialize the "Brain"
    receptor = Receptor()
    graph = Hypergraph(context_size=2)
    bridge = TransformerBridge(graph)
    
    # Knowledge Ingestion (Continuous Stream)
    print("\n[Tanulás] Folytonos tudásfolyam rögzítése...")
    knowledge_stream = (
        "input_data = get_user_input ( ) ; "
        "clean_data = [ x for x in input_data if x != None ] ; "
        "save_to_db ( clean_data ) ; "
        "log_event ( 'Operation successful' ) ;"
    )
    graph.learn(receptor.process(knowledge_stream))
    
    # Define a high-level skill
    skill_tokens = receptor.process("clean_data = [ x for x in input_data if x != None ] ; save_to_db ( clean_data ) ;")
    skill_ids = [graph.get_or_create_node(t).id for t in skill_tokens]
    graph.create_metanode("CLEAN_AND_SAVE_SKILL", skill_ids)
    print("  'CLEAN_AND_SAVE_SKILL' MetaNode rögzítve.")
    
    # Interaction
    queries = [
        "Kérj be adatot és mentsd el!",
        "Tisztítsd meg az inputot és naplózd az eseményt!",
        "Mentsd el a tisztított listát!"
    ]
    
    for q in queries:
        result = bridge.process_query(q)
        print(f"[Válasz]\n{result}")
        print("-" * 50)

if __name__ == "__main__":
    main()
