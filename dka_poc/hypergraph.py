import json

class Edge:
    """
    Represents a deterministic connection between two nodes with context.
    """
    def __init__(self, source_id, target_id, context=None, is_shortcut=False):
        self.source_id = source_id
        self.target_id = target_id
        self.context = context  # Tuple of node IDs
        self.counter = 1.0      # Float for decay compatibility
        self.is_shortcut = is_shortcut
        self.origin_sources = set() # Set of source identifiers (filenames, etc.)

    def increment(self, amount=1.0, source=None):
        self.counter += amount
        if source:
            self.origin_sources.add(source)

    def decay(self, rate):
        self.counter -= rate
        if self.counter < 0:
            self.counter = 0

    def to_dict(self):
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "context": self.context,
            "counter": self.counter,
            "is_shortcut": self.is_shortcut
        }

    @staticmethod
    def from_dict(data):
        edge = Edge(data["source_id"], data["target_id"], context=tuple(data["context"]) if data["context"] else None, is_shortcut=data["is_shortcut"])
        edge.counter = data["counter"]
        return edge

    def __repr__(self):
        ctx_str = f", ctx={self.context}" if self.context else ""
        return f"Edge({self.source_id}->{self.target_id}{ctx_str}, count={self.counter:.2f})"


class AssociativeEdge:
    """
    A semantic link between two nodes that play the same logical role.
    """
    def __init__(self, source_id, target_id, role_label):
        self.source_id = source_id
        self.target_id = target_id
        self.role_label = role_label

    def __repr__(self):
        return f"AssocEdge({self.source_id}<->{self.target_id}, role='{self.role_label}')"


class Node:
    """
    A discrete symbolic unit in the cognitive architecture.
    """
    def __init__(self, node_id, value):
        self.id = node_id
        self.value = value
        # Mapping: (target_id, context_tuple) -> Edge object
        self.edges_out = {}
        self.associations = {} # target_id -> AssociativeEdge
        self.role = None
        self.is_meta = False
        self.domains = set() # Set of domain labels

    def add_or_increment_edge(self, target_id, context=None, source=None):
        key = (target_id, context)
        if key in self.edges_out:
            self.edges_out[key].increment(source=source)
        else:
            edge = Edge(self.id, target_id, context=context)
            edge.increment(amount=0.0, source=source) # Initialize source set
            self.edges_out[key] = edge

    def add_association(self, target_id, role_label):
        if target_id not in self.associations:
            self.associations[target_id] = AssociativeEdge(self.id, target_id, role_label)

    def to_dict(self):
        return {
            "id": self.id,
            "value": self.value,
            "is_meta": self.is_meta,
            "role": self.role,
            "edges": [e.to_dict() for e in self.edges_out.values()]
        }

    def __repr__(self):
        type_str = "Meta" if self.is_meta else "Std"
        role_str = f", role='{self.role}'" if self.role else ""
        return f"Node[{type_str}](id={self.id}, val='{self.value}'{role_str}, edges={len(self.edges_out)})"


class MetaNode(Node):
    """
    A hierarchical node that encapsulates a sequence of other nodes.
    Acts as an abstraction of complex logic patterns.
    """
    def __init__(self, node_id, value, sequence_ids):
        super().__init__(node_id, value)
        self.sequence_ids = sequence_ids  # List of node IDs this MetaNode represents
        self.is_meta = True

    def to_dict(self):
        data = super().to_dict()
        data["sequence_ids"] = self.sequence_ids
        return data

    def __repr__(self):
        return f"MetaNode(id={self.id}, val='{self.value}', seq_len={len(self.sequence_ids)})"


class Hypergraph:
    """
    Knowledge base with context-aware directed edges, hierarchical MetaNodes, and semantic roles.
    """
    def __init__(self, context_size=2):
        self.nodes = {}  # node_id -> Node/MetaNode
        self.value_to_id = {} # value -> node_id
        self._next_id = 0
        self.context_size = context_size

    def to_json(self):
        data = {
            "context_size": self.context_size,
            "next_id": self._next_id,
            "nodes": [n.to_dict() for n in self.nodes.values()]
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        graph = Hypergraph(context_size=data["context_size"])
        graph._next_id = data["next_id"]
        
        # First pass: Create nodes
        for n_data in data["nodes"]:
            if n_data["is_meta"]:
                node = MetaNode(n_data["id"], n_data["value"], n_data["sequence_ids"])
            else:
                node = Node(n_data["id"], n_data["value"])
            node.role = n_data.get("role")
            graph.nodes[node.id] = node
            graph.value_to_id[node.value] = node.id
            
        # Second pass: Restore edges
        for n_data in data["nodes"]:
            node = graph.nodes[n_data["id"]]
            for e_data in n_data["edges"]:
                edge = Edge.from_dict(e_data)
                key = (edge.target_id, edge.context)
                node.edges_out[key] = edge
                
        return graph

    def get_or_create_node(self, value):
        if value in self.value_to_id:
            return self.nodes[self.value_to_id[value]]
        
        node_id = self._next_id
        self._next_id += 1
        
        new_node = Node(node_id, value)
        self.nodes[node_id] = new_node
        self.value_to_id[value] = node_id
        return new_node

    def create_metanode(self, value, sequence_ids):
        """
        Creates a new MetaNode representing an abstraction.
        """
        node_id = self._next_id
        self._next_id += 1
        
        meta = MetaNode(node_id, value, sequence_ids)
        self.nodes[node_id] = meta
        self.value_to_id[value] = node_id
        return meta

    def learn(self, sequence, domain="general", source=None):
        """
        Learns from a sequence, incorporating context windows, domains and sources.
        """
        if not sequence:
            return

        node_sequence = []
        for val in sequence:
            node = self.get_or_create_node(val)
            node.domains.add(domain)
            node_sequence.append(node)

        # 1. Sequential Learning
        for i in range(len(node_sequence) - 1):
            current_node = node_sequence[i]
            next_node = node_sequence[i+1]
            
            start_idx = max(0, i - self.context_size)
            context = tuple(n.id for n in node_sequence[start_idx:i])
            current_node.add_or_increment_edge(next_node.id, context=context, source=source)
            
            if context:
                current_node.add_or_increment_edge(next_node.id, context=None, source=source)

        # 2. Associative Learning
        for i in range(len(node_sequence)):
            node_a = node_sequence[i]
            for j in range(len(node_sequence)):
                if i == j: continue
                node_b = node_sequence[j]
                node_a.add_association(node_b.id, "CO_OCCURRENCE")

    def get_node_by_value(self, value):
        node_id = self.value_to_id.get(value)
        if node_id is not None:
            return self.nodes[node_id]
        return None

    def __repr__(self):
        return f"Hypergraph(nodes={len(self.nodes)})"


    def __repr__(self):
        return f"Hypergraph(nodes={len(self.nodes)})"
