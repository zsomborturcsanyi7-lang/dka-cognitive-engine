class LogicEngine:
    """
    Deterministic inference and validation engine.
    Uses graph traversal to generate code and detect logical errors.
    """
    def __init__(self, graph):
        self.graph = graph

    def generate(self, start_value, max_length=50, expand_meta=True):
        """
        Generates a sequence, recursively expanding MetaNodes if requested.
        Tracks 'traversal_steps' to demonstrate efficiency.
        """
        current_node = self.graph.get_node_by_value(start_value)
        if not current_node:
            return [f"<Unknown:{start_value}>"], 0

        result = []
        result_ids = []
        traversal_steps = 0

        def add_node_to_result(node):
            nonlocal traversal_steps
            traversal_steps += 1
            if node.is_meta and expand_meta:
                # Recursive expansion of the MetaNode
                for sub_id in node.sequence_ids:
                    sub_node = self.graph.nodes[sub_id]
                    add_node_to_result(sub_node)
            else:
                result.append(node.value)
                result_ids.append(node.id)

        add_node_to_result(current_node)
        
        for _ in range(max_length - 1):
            if not current_node.edges_out:
                break
            
            ctx_size = self.graph.context_size
            search_ctx = tuple(result_ids[-ctx_size-1:-1]) if len(result_ids) > 1 else ()
            
            def get_score(edge):
                context_match = 1.0 if edge.context == search_ctx else 0.0
                return (context_match, edge.counter)

            candidates = sorted(current_node.edges_out.values(), 
                               key=get_score, 
                               reverse=True)
            
            # Semantic Jump: if no good direct candidate, check associations
            if not candidates or (candidates[0].counter < 1.0 and current_node.associations):
                for assoc_id in current_node.associations.keys():
                    assoc_node = self.graph.nodes[assoc_id]
                    if assoc_node.edges_out:
                        # Jump to synonym and take its best edge
                        assoc_candidates = sorted(assoc_node.edges_out.values(), 
                                                key=get_score, 
                                                reverse=True)
                        if assoc_candidates:
                            # print(f"DEBUG: Semantic Jump '{current_node.value}' -> '{assoc_node.value}'")
                            next_edge = assoc_candidates[0]
                            current_node = self.graph.nodes[next_edge.target_id]
                            break
                else:
                    if not candidates: break
                    next_edge = candidates[0]
                    current_node = self.graph.nodes[next_edge.target_id]
            else:
                next_edge = candidates[0]
                current_node = self.graph.nodes[next_edge.target_id]
            
            # Recursive expansion of the MetaNode
            if current_node.is_meta and not expand_meta:
                result.append(f"[{current_node.value}]")
                result_ids.append(current_node.id)
                traversal_steps += 1
            else:
                add_node_to_result(current_node)
            
            # Remove the early ';' exit to allow multi-line/complex blocks
            # if result[-1] == ';':
            #     break
                
        return result, traversal_steps

    def self_check(self):
        """
        Performs internal consistency checks on the hypergraph.
        Detects orphaned edges, logical loops (circularity), and MetaNode validity.
        """
        errors = []
        
        # 1. Orphaned Edges & Target Consistency
        for node in self.graph.nodes.values():
            for key, edge in node.edges_out.items():
                if edge.target_id not in self.graph.nodes:
                    errors.append(f"OrphanedEdge: Node {node.id} ('{node.value}') points to non-existent ID {edge.target_id}")

        # 2. MetaNode Consistency
        for node in self.graph.nodes.values():
            if node.is_meta:
                for sub_id in node.sequence_ids:
                    if sub_id not in self.graph.nodes:
                        errors.append(f"MetaNodeInconsistency: MetaNode {node.id} ('{node.value}') contains non-existent sub-node ID {sub_id}")

        # 3. Circularity Detection (Logical Loops)
        # DFS with recursion stack to detect back-edges.
        visited = set()
        stack = set()
        
        def find_cycles(node_id, path):
            if node_id in stack:
                cycle_path = path[path.index(node_id):] + [node_id]
                cycle_values = []
                for nid in cycle_path:
                    val = self.graph.nodes[nid].value
                    cycle_values.append(val)
                errors.append(f"LogicalLoopDetected: {' -> '.join(cycle_values)}")
                return True
            
            if node_id in visited:
                return False

            visited.add(node_id)
            stack.add(node_id)
            path.append(node_id)
            
            node = self.graph.nodes[node_id]
            found = False
            for edge in node.edges_out.values():
                if find_cycles(edge.target_id, path):
                    found = True
                    break # Stop at first cycle for this path
            
            path.pop()
            stack.remove(node_id)
            return found

        # Only run on non-MetaNodes for base logic check, 
        # or include MetaNodes if they are part of the flow.
        for node_id in list(self.graph.nodes.keys()):
            if node_id not in visited:
                find_cycles(node_id, [])

        return errors

    def validate(self, sequence):
        """
        Validates sequence with contextual back-off.
        """
        if not sequence:
            return True, -1, "Empty sequence"

        node_ids = []
        for val in sequence:
            node = self.graph.get_node_by_value(val)
            if not node:
                return False, sequence.index(val), f"Unknown token: '{val}'"
            node_ids.append(node.id)

        for i in range(len(node_ids) - 1):
            curr_node = self.graph.nodes[node_ids[i]]
            next_id = node_ids[i+1]
            
            # 1. Try full context
            start_idx = max(0, i - self.graph.context_size)
            full_ctx = tuple(node_ids[start_idx:i])
            
            if (next_id, full_ctx) in curr_node.edges_out:
                continue
            
            # 2. Back-off: Try generic context (None)
            if (next_id, None) in curr_node.edges_out:
                # print(f"  [Validation] Back-off used for '{sequence[i]}' -> '{sequence[i+1]}'")
                continue
                
            return False, i + 1, f"Invalid logical transition: '{sequence[i]}' -> '{sequence[i+1]}'"

        return True, -1, "Sequence is logically consistent"
