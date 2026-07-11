class Rule:
    """
    Represents a refactoring rule: a pattern to find and a MetaNode to replace it with.
    """
    def __init__(self, pattern_values, meta_label):
        self.pattern_values = pattern_values
        self.meta_label = meta_label

class RuleEngine:
    """
    Applies logic rules to the Hypergraph to transform and optimize its structure.
    """
    def __init__(self, graph, optimizer, engine):
        self.graph = graph
        self.optimizer = optimizer
        self.engine = engine
        self.rules = []

    def add_rule(self, rule):
        self.rules.append(rule)

    def apply_refactoring(self):
        """
        Executes all rules. Uses a snapshot/rollback mechanism for safety.
        """
        print("[RuleEngine] Refaktorálás megkezdése...")
        
        # Snapshot for rollback
        snapshot = self.graph.to_json()
        
        applied_count = 0
        try:
            for rule in self.rules:
                # Find and define abstraction (this links incoming edges to the new MetaNode)
                meta = self.optimizer.define_abstraction(rule.pattern_values, rule.meta_label)
                if meta:
                    print(f"  Szabály alkalmazva: '{rule.meta_label}'")
                    applied_count += 1
                
            # Integrity Check
            errors = self.engine.self_check()
            if errors:
                print(f"  HIBA: A refaktorálás megsértette az integritást! Rollback...")
                for err in errors:
                    print(f"    - {err}")
                self.rollback(snapshot)
                return False, 0
            
            print(f"  Sikeres refaktorálás. Alkalmazott szabályok: {applied_count}")
            return True, applied_count
            
        except Exception as e:
            print(f"  KRITIKUS HIBA a refaktorálás során: {e}. Rollback...")
            self.rollback(snapshot)
            return False, 0

    def rollback(self, snapshot_json):
        """
        Restores the graph to a previous state from a JSON snapshot.
        """
        from hypergraph import Hypergraph
        restored_graph = Hypergraph.from_json(snapshot_json)
        # Update current graph references (shallow copy of internals)
        self.graph.nodes = restored_graph.nodes
        self.graph.value_to_id = restored_graph.value_to_id
        self.graph._next_id = restored_graph._next_id
        self.graph.context_size = restored_graph.context_size
        print("  A gráf állapota visszaállítva.")
