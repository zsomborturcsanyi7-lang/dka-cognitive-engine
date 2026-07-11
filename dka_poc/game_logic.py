from hypergraph import MetaNode

class GameLogicLibrary:
    """
    Extends the LogicLibrary with game-specific abstractions.
    """
    def __init__(self, graph, receptor):
        self.graph = graph
        self.receptor = receptor

    def load_snake_primitives(self):
        """
        Defines the logical blocks for a grid-based Snake game.
        """
        # 1. SNAKE_STATE: [x, y, body, direction]
        self._add_meta("SNAKE_STATE_INIT", "snake_body = [ ( 5 , 5 ) , ( 4 , 5 ) , ( 3 , 5 ) ] ; direction = ( 1 , 0 ) ; score = 0 ;")
        
        # 2. INPUT_HANDLER: WASD to Direction
        self._add_meta("INPUT_HANDLER", 
            "if ( key == 'w' ) { direction = ( 0 , -1 ) ; } "
            "if ( key == 's' ) { direction = ( 0 , 1 ) ; } "
            "if ( key == 'a' ) { direction = ( -1 , 0 ) ; } "
            "if ( key == 'd' ) { direction = ( 1 , 0 ) ; }")

        # 3. SNAKE_MOVE: Head update and tail removal
        self._add_meta("SNAKE_MOVE", 
            "head = snake_body [ 0 ] ; "
            "new_head = ( head [ 0 ] + direction [ 0 ] , head [ 1 ] + direction [ 1 ] ) ; "
            "snake_body.insert ( 0 , new_head ) ; "
            "snake_body.pop ( ) ;")

        # 4. COLLISION_ENGINE: Wall and self collision
        self._add_meta("COLLISION_ENGINE", 
            "if ( new_head [ 0 ] < 0 or new_head [ 0 ] >= 20 or new_head [ 1 ] < 0 or new_head [ 1 ] >= 20 ) { game_over = True ; } "
            "if ( new_head in snake_body [ 1 : ] ) { game_over = True ; }")

        # 5. GAME_LOOP: The main orchestration
        self._add_meta("GAME_LOOP", 
            "while ( not game_over ) { [INPUT_HANDLER] [SNAKE_MOVE] [COLLISION_ENGINE] }")

        print("[GameLogicLibrary] Snake-specifikus MetaNode-ok definiálva.")

    def _add_meta(self, label, template):
        tokens = self.receptor.process(template)
        # Store MetaNode in graph
        self.graph.create_metanode(label, [self.graph.get_or_create_node(t).id for t in tokens])
