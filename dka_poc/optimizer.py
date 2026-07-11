from hypergraph import Edge

class Optimizer:
    """
    Asynchronous-ready optimization core for the DKA Hypergraph.
    Handles path compression (shortcuts) and selective forgetting (decay).
    """
    def __init__(self, graph):
        self.graph = graph

    def define_abstraction(self, pattern_values, meta_label):
        """
        Encapsulates a frequent pattern into a MetaNode.
        Connects existing nodes to the new MetaNode.
        """
        # Convert values to existing node IDs
        sequence_ids = []
        for val in pattern_values:
            node = self.graph.get_node_by_value(val)
            if not node: return None # Pattern contains unknown nodes
            sequence_ids.append(node.id)

        # Create MetaNode
        meta = self.graph.create_metanode(meta_label, sequence_ids)
        
        # Link previous nodes of the pattern to the MetaNode
        start_node_id = sequence_ids[0]
        for node in self.graph.nodes.values():
            if node.id == meta.id: continue
            for (target_id, ctx), edge in list(node.edges_out.items()):
                if target_id == start_node_id:
                    # Add a transition to the abstraction
                    # BOOST the counter to ensure it's preferred
                    node.add_or_increment_edge(meta.id, context=ctx)
                    meta_key = (meta.id, ctx)
                    node.edges_out[meta_key].counter = edge.counter + 10.0
        
        # MetaNode should point to the node following the pattern sequence
        # To keep it simple, the MetaNode's outgoing edges will be copied from 
        # the last node in the sequence.
        last_node_id = sequence_ids[-1]
        last_node = self.graph.nodes[last_node_id]
        meta.edges_out = last_node.edges_out.copy()

        return meta

    def apply_decay(self, decay_rate=0.1):
        """
        Reduces the strength of all edges. Removes edges with counter <= 0.
        This implements the selective forgetting mechanism.
        """
        edges_removed = 0
        for node in self.graph.nodes.values():
            keys_to_remove = []
            for key, edge in node.edges_out.items():
                edge.decay(decay_rate)
                if edge.counter <= 0:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del node.edges_out[key]
                edges_removed += 1
        return edges_removed

    def compute_topological_signature(self, node_id):
        """
        Computes a unique signature for a node based on its neighborhood.
        The signature is context-aware but replaces local variable IDs with placeholders.
        """
        node = self.graph.nodes[node_id]
        
        # In a real DKA, this would be a deep recursive hash.
        # For PoC, we look at the values of immediate neighbors.
        incoming = []
        for n in self.graph.nodes.values():
            for (tid, ctx), edge in n.edges_out.items():
                if tid == node_id:
                    # We store the value of the preceding node
                    incoming.append(n.value)
        
        outgoing = [self.graph.nodes[tid].value for (tid, ctx) in node.edges_out.keys()]
        
        return (tuple(sorted(incoming)), tuple(sorted(outgoing)))

    def detect_semantic_associations(self, role_label="LOOP_INDEX", pattern_values=None):
        """
        Identifies nodes that appear in the same logical pattern.
        Example: nodes that appear in 'for ( ? = 0 ;'
        """
        if not pattern_values: return 0
        
        associations_made = 0
        matching_nodes = set()
        
        # A very simple pattern matcher: find nodes that occupy the '?' position
        # if the pattern is ['for', '(', '?', '=', '0', ';']
        placeholder_idx = pattern_values.index("?")
        pattern_len = len(pattern_values)
        
        # In a real DKA, we'd scan the graph paths. 
        # Here we just use a heuristic: nodes with similar signatures.
        signatures = {}
        for node in self.graph.nodes.values():
            if node.is_meta: continue
            sig = self.compute_topological_signature(node.id)
            signatures[node.id] = sig
            
        # Group nodes by signature
        from collections import defaultdict
        groups = {}
        for nid, sig in signatures.items():
            if sig not in groups: groups[sig] = []
            groups[sig].append(nid)
            
        for sig, nids in groups.items():
            if len(nids) > 1:
                # If multiple nodes have the exact same topology, they are synonyms
                base_node = self.graph.nodes[nids[0]]
                base_node.role = role_label
                for other_id in nids[1:]:
                    other_node = self.graph.nodes[other_id]
                    other_node.role = role_label
                    base_node.add_association(other_id, role_label)
                    other_node.add_association(base_node.id, role_label)
                    associations_made += 1
                    
        return associations_made
