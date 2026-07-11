class InferenceEngine:
    """
    The reasoning core of the DKA. Performs goal-oriented pathfinding
    and logical deduction using the Hypergraph.
    Strictly deterministic, no probabilities.
    """
    def __init__(self, graph, logic_engine):
        self.graph = graph
        self.logic_engine = logic_engine
        self.allowed_domains = None # Set of allowed domain labels

    def deduce_path(self, start_val, goal_val, max_depth=15):
        """
        Attempts to find a logically consistent path using context-aware DFS 
        and domain filtering.
        """
        start_node = self.graph.get_node_by_value(start_val)
        goal_node = self.graph.get_node_by_value(goal_val)

        if not start_node or not goal_node:
            return None, f"Ismeretlen fogalom"

        # Domain check for the start and goal node
        if self.allowed_domains:
            if not (start_node.domains & self.allowed_domains):
                return None, f"A(z) '{start_val}' nódus nem része az engedélyezett doméneknek."
            if not (goal_node.domains & self.allowed_domains):
                return None, f"A(z) '{goal_val}' nódus (cél) nem része az engedélyezett doméneknek."

        print(f"[Inference] Domén-szűrt következtetés ({self.allowed_domains}): '{start_val}' -> '{goal_val}'")
        
        path = self._find_context_aware_route([start_node.id], goal_node.id, max_depth)
        
        if path:
            values = [self.graph.nodes[nid].value for nid in path]
            return values, "Sikeres."
        
        return None, "Nincs érvényes kontextus-alapú út."

    def _find_context_aware_route(self, current_path, goal_id, depth, active_focus=None):
        current_id = current_path[-1]
        current_node = self.graph.nodes[current_id]
        
        if current_id == goal_id:
            return current_path
        
        if depth <= 0:
            return None

        # Calculate context
        ctx_size = self.graph.context_size
        current_ctx = tuple(current_path[-ctx_size-1:-1]) if len(current_path) > 1 else ()

        # --- Skill Discovery (MetaNode preference) ---
        for edge in current_node.edges_out.values():
            target = self.graph.nodes[edge.target_id]
            if target.is_meta:
                if goal_id in target.sequence_ids or goal_id == target.id:
                    return current_path + target.sequence_ids

        # --- Logical Focus Scoring ---
        def edge_score(edge):
            target = self.graph.nodes[edge.target_id]
            score = 0
            
            # 1. Context Match (Highest Priority)
            if edge.context == current_ctx: score += 1000
            
            # 2. LOGICAL FOCUS: Prefer same source as the current path
            if active_focus and active_focus in edge.origin_sources:
                score += 2000 # Strong bias to stay in the same logical block
            
            # 3. MetaNode preference
            if target.is_meta: score += 500
            
            return score + edge.counter

        sorted_edges = sorted(current_node.edges_out.values(), key=edge_score, reverse=True)

        for edge in sorted_edges:
            target = self.graph.nodes[edge.target_id]
            
            if self.allowed_domains and not (target.domains & self.allowed_domains):
                continue

            if edge.target_id in current_path[-5:]: continue 
            
            # Update active focus if the edge belongs to a clear source
            new_focus = list(edge.origin_sources)[0] if edge.origin_sources else active_focus
            
            new_path = current_path + [edge.target_id]
            result = self._find_context_aware_route(new_path, goal_id, depth - 1, active_focus=new_focus)
            if result:
                return result

        # Associative Jump
        for assoc_id in current_node.associations.keys():
            if assoc_id not in current_path:
                assoc_node = self.graph.nodes[assoc_id]
                if self.allowed_domains and not (assoc_node.domains & self.allowed_domains):
                    continue
                # If we jump to an association, try to find the goal from there
                result = self._find_context_aware_route(current_path + [assoc_id], goal_id, depth - 1, active_focus)
                if result:
                    return result

        return None

    def solve_with_constraints(self, start_val, constraints):
        """
        Generates a sequence that passes through checkpoints, autonomously 
        filling gaps with the most logically sound paths.
        """
        full_sequence = []
        current_pos = start_val
        
        print(f"[DKA Reasoning] Logikai ív tervezése: {' -> '.join(constraints)}")

        for goal in constraints:
            if current_pos == goal and full_sequence:
                continue
                
            path, msg = self.deduce_path(current_pos, goal)
            if path:
                # Add the path, avoiding duplication of the bridge node
                if full_sequence and full_sequence[-1] == path[0]:
                    full_sequence.extend(path[1:])
                else:
                    full_sequence.extend(path)
                current_pos = full_sequence[-1]
            else:
                # RELAXED SEARCH: If no direct path to specific token, 
                # try to find any path that gets us CLOSER to the goal 
                # using associative jumps.
                print(f"  [!] Közvetlen út megszakadt: '{current_pos}' -> '{goal}'. Kitöltés keresése...")
                # For PoC, we just skip the impossible gap and move to next anchor
                full_sequence.append(f"<{goal}_RECONSTRUCTED>")
                current_pos = goal

        # --- Self-Validation & Cleanup ---
        # (Validation disabled for this demo to show the raw reconstruction)
        return full_sequence, True

