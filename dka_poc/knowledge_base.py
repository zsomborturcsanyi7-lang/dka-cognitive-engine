from hypergraph import MetaNode

class LogicLibrary:
    """
    A foundational library of optimized logical primitives pre-loaded into the DKA.
    These MetaNodes represent universal programming constructs.
    """
    def __init__(self, graph, receptor):
        self.graph = graph
        self.receptor = receptor
        self.primitives = {} # label -> MetaNode

    def load_primitives(self):
        """
        Populates the Hypergraph with core programming structures.
        """
        # 1. Iteration Primitives
        self._add_primitive("FOR_LOOP_STRUCTURE", "for ( ? = 0 ; ? < ? ; ? ++ ) { ? }")
        self._add_primitive("WHILE_LOOP_STRUCTURE", "while ( ? ) { ? }")
        
        # 2. Conditional Primitives
        self._add_primitive("IF_ELSE_STRUCTURE", "if ( ? ) { ? } else { ? }")
        
        # 3. Data Structure Primitives
        self._add_primitive("LIST_ACCESS", "? [ ? ]")
        self._add_primitive("MAP_ASSIGN", "? [ ? ] = ? ;")
        
        # 4. Error Handling
        self._add_primitive("TRY_CATCH_STRUCTURE", "try { ? } catch ( ? ) { ? }")
        
        # 5. High-level Algorithms
        self._add_primitive("SORT_PRIMITIVE", 
            "for ( i = 0 ; i < n ; i ++ ) { for ( j = 0 ; j < n - i - 1 ; j ++ ) { if ( ? [ j ] > ? [ j + 1 ] ) { ? } } }")

        print(f"[LogicLibrary] {len(self.primitives)} alapvető logikai primitív betöltve.")

    def _add_primitive(self, label, template):
        """
        Converts a template string into a MetaNode.
        The '?' characters are treated as variable placeholders (roles).
        """
        tokens = self.receptor.process(template)
        # In a real DKA, we'd handle placeholders as semantic roles.
        # For PoC, we store the token sequence.
        meta = self.graph.create_metanode(label, [self.graph.get_or_create_node(t).id for t in tokens])
        self.primitives[label] = meta
        return meta
