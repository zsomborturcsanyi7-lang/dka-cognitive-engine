from hypergraph import MetaNode

class VaultBlueprint:
    """
    Architectural templates for a high-security state machine.
    """
    def __init__(self, graph, receptor):
        self.graph = graph
        self.receptor = receptor

    def load_vault_logic(self):
        # 1. State Initialization
        self._add("VAULT_INIT", 
            "is_locked = True ; attempts = 0 ; secret_code = '1234' ; is_blocked = False ;")

        # 2. Authentication Logic
        self._add("AUTH_LOGIC", 
            "if ( is_blocked ) : print ( 'VAULT BLOCKED! Access Denied.' ) ; return ; "
            "if ( input_code == secret_code ) : is_locked = False ; attempts = 0 ; print ( 'Access Granted.' ) ; "
            "else : attempts += 1 ; print ( 'Wrong Code.' ) ;")

        # 3. Security Lockout (Integrity Rule)
        self._add("LOCKOUT_CHECK", 
            "if ( attempts >= 3 ) : is_blocked = True ; print ( 'SECURITY BREACH! System Frozen.' ) ;")

        # 4. Persistence Simulation
        self._add("VAULT_SAVE", "status = { 'locked' : is_locked , 'blocked' : is_blocked } ; print ( 'State Saved.' ) ;")

    def _add(self, label, template):
        tokens = self.receptor.process(template)
        self.graph.create_metanode(label, [self.graph.get_or_create_node(t).id for t in tokens])
