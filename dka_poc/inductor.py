from rules import Rule

class RuleInductor:
    """
    Analyzes the Hypergraph and learning history to induce new refactoring rules.
    Implements a basic form of Inductive Logic Programming (ILP).
    """
    def __init__(self, graph, rule_engine, threshold=3):
        self.graph = graph
        self.rule_engine = rule_engine
        self.threshold = threshold
        self.pattern_registry = {} # tuple(tokens) -> frequency count

    def track_sequence(self, sequence):
        if len(sequence) < 3: return
        for length in range(3, min(11, len(sequence) + 1)):
            for i in range(len(sequence) - length + 1):
                sub_seq = tuple(sequence[i:i+length])
                self.pattern_registry[sub_seq] = self.pattern_registry.get(sub_seq, 0) + 1
                if self.pattern_registry[sub_seq] == self.threshold:
                    self.induce_rule(sub_seq)

    def induce_rule(self, pattern_tuple):
        pattern_list = list(pattern_tuple)
        meta_label = f"AUTO_META_{len(self.rule_engine.rules) + 1}"
        for existing_rule in self.rule_engine.rules:
            if existing_rule.pattern_values == pattern_list: return
        new_rule = Rule(pattern_list, meta_label)
        self.rule_engine.add_rule(new_rule)
        print(f"[RuleInductor] RuleGenerated: {pattern_list} -> [{meta_label}] (Freq >= {self.threshold})")

    def consolidate_rules(self):
        if not self.rule_engine.rules: return
        sorted_rules = sorted(self.rule_engine.rules, key=lambda r: len(r.pattern_values), reverse=True)
        unique_rules = []
        for i, rule in enumerate(sorted_rules):
            is_subpattern = False
            for other in sorted_rules:
                if rule is other: continue
                p_str = " ".join(rule.pattern_values)
                o_str = " ".join(other.pattern_values)
                if p_str in o_str:
                    is_subpattern = True
                    break
            if not is_subpattern: unique_rules.append(rule)
        for i, rule in enumerate(unique_rules):
            rule.meta_label = f"OPTIMIZED_BLOCK_{i+1}"
        self.rule_engine.rules = unique_rules
        print(f"[RuleInductor] Consolidation complete. Kept {len(self.rule_engine.rules)} specific rules.")

class SuggestionEngine:
    """
    Identifies verbose or non-optimal code patterns and suggests library-based refactorings.
    Uses a similarity threshold (default 80%) for pattern matching.
    """
    def __init__(self, graph, logic_library):
        self.graph = graph
        self.library = logic_library

    def analyze_sequence(self, tokens, threshold=0.8):
        """
        Compares a sequence of tokens against known primitives using a sliding window.
        """
        suggestions = []
        token_seq = list(tokens)
        
        for label, meta in self.library.primitives.items():
            # Get primitive tokens
            primitive_tokens = [self.graph.nodes[nid].value for nid in meta.sequence_ids]
            p_len = len(primitive_tokens)
            
            if len(token_seq) < p_len:
                continue
                
            # Sliding window over the input tokens
            max_score = 0
            for start in range(len(token_seq) - p_len + 1):
                window = token_seq[start:start+p_len]
                score = self._calculate_similarity(window, primitive_tokens)
                max_score = max(max_score, score)
            
            if max_score >= threshold:
                suggestions.append({
                    "pattern": label,
                    "score": max_score
                })
                print(f"[SuggestionEngine] PatternMatched: [VERBOSE_CODE] -> [{label}] (Similarity: {max_score:.2f})")
                
        return suggestions

    def _calculate_similarity(self, seq_a, seq_b):
        """
        Calculates similarity ratio between two token sequences.
        '?' in seq_b matches anything in seq_a.
        """
        # Very simple alignment check for PoC
        matches = 0
        min_len = min(len(seq_a), len(seq_b))
        if min_len == 0: return 0
        
        for i in range(min_len):
            if seq_b[i] == "?" or seq_a[i] == seq_b[i]:
                matches += 1
                
        return matches / len(seq_b)
