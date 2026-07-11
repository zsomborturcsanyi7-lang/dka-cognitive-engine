from hypergraph import Hypergraph

class DomainBridge:
    """
    Connects multiple domain-specific graphs (Code, Config, etc.) 
    via cross-domain BridgeEdges.
    """
    def __init__(self):
        self.domains = {} # domain_name -> Hypergraph
        self.bridge_edges = [] # List of (source_domain, node_id, target_domain, node_id)

    def register_domain(self, name, graph):
        self.domains[name] = graph

    def create_bridge(self, dom_a, val_a, dom_b, val_b):
        """
        Creates a semantic link between two nodes in different domains.
        """
        node_a = self.domains[dom_a].get_node_by_value(val_a)
        node_b = self.domains[dom_b].get_node_by_value(val_b)
        
        if node_a and node_b:
            self.bridge_edges.append((dom_a, node_a.id, dom_b, node_b.id))
            print(f"[DomainBridge] BridgeCreated: {dom_a}:'{val_a}' <-> {dom_b}:'{val_b}'")
            return True
        return False

class RippleEffectEngine:
    """
    Propagates logical changes across domain boundaries.
    """
    def __init__(self, bridge):
        self.bridge = bridge

    def analyze_impact(self, source_domain, old_value, new_value):
        """
        Detects nodes affected by a value change in a specific domain.
        """
        print(f"[RippleEffect] Elemzés: {source_domain} változás: '{old_value}' -> '{new_value}'")
        
        graph_s = self.bridge.domains[source_domain]
        node_s = graph_s.get_node_by_value(new_value) # Target the NEW node
        if not node_s: return []

        impacts = []
        for (da, id_a, db, id_b) in self.bridge.bridge_edges:
            if da == source_domain and id_a == graph_s.value_to_id.get(old_value):
                # We found a bridge from the OLD node. Propagate to the other domain.
                target_node = self.bridge.domains[db].nodes[id_b]
                impacts.append((db, target_node.value))
                print(f"  [!] Hatás észlelve a(z) '{db}' doménben: '{target_node.value}' frissítése javasolt.")
        
        return impacts
