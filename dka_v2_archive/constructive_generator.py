"""
DKA Core — ConstructiveGenerator
=================================
Nem token-fűző, hanem szintaxis-tudatos kódgenerátor.

A graph-ban tárolt PatternNode-okból építi vissza a Python kódot.
Minden lépésben tudja, hogy mit vár a szintaxis — pl.:
- `if` után `:` kell, aztán egy indentált blokk
- `for` után `in` kell
- `return` után opcionális kifejezés
- stb.

Ha egy szerepkör üres, analógiát keres a gráfban.
"""

from __future__ import annotations
from typing import Optional

from node_types import (
    BaseNode, PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain,
)
from hypergraph_v2 import HypergraphV2


# Operator precedencia tábla
_PRECEDENCE = {
    "**": 80,
    "+": 10, "-": 10,
    "*": 20, "/": 20, "//": 20, "%": 20,
    "<<": 5, ">>": 5,
    "&": 4,
    "^": 3,
    "|": 2,
    "==": 1, "!=": 1, "<": 1, "<=": 1, ">": 1, ">=": 1,
    "and": 0, "or": 0,
}

def _needs_parens(parent_op: str, child_op: str) -> bool:
    """Kell-e zárójel a gyerek köré a szülő operátor miatt?"""
    p_prec = _PRECEDENCE.get(parent_op, 10)
    c_prec = _PRECEDENCE.get(child_op, 10)
    return c_prec < p_prec


class ConstructiveGenerator:
    """
    PatternNode fa → Python kód.
    
    Minden NodeType-hoz tartozik egy generátor függvény,
    ami tudja a szintaktikai szabályokat.
    """
    
    def __init__(self, graph: HypergraphV2 = None):
        self.graph = graph
        self.indent_size = 4
        self._indent_level = 0
    
    def set_graph(self, graph: HypergraphV2):
        self.graph = graph
    
    def _indent(self) -> str:
        return " " * (self._indent_level * self.indent_size)
    
    def generate(self, node: BaseNode) -> str:
        """
        Bármely nódusból kódot generál.
        A nódus típusa alapján dispatch-el.
        """
        if isinstance(node, PrimitiveNode):
            return self._generate_primitive(node)
        elif isinstance(node, PatternNode):
            return self._generate_pattern(node)
        elif isinstance(node, SchemaNode):
            # Séma: válassza ki a legjobb variációt
            return self._generate_schema(node)
        return ""
    
    def _generate_primitive(self, node: PrimitiveNode) -> str:
        """Primitív nódus → string."""
        value = node.value
        
        if node.type == NodeType.LITERAL:
            # String literálok: idézőjelek
            if value.startswith('"') or value.startswith("'"):
                return value
            # Ha szám
            try:
                float(value)
                return value
            except ValueError:
                pass
            return f'"{value}"' if ' ' in value else value
        
        if node.type == NodeType.VARIABLE:
            if node.value.startswith("*"):
                return node.value
            if node.value.startswith("**"):
                return node.value
            return node.value
        
        if node.type == NodeType.OPERATOR:
            # Python operátor nevek → szimbólum
            op_map = {
                "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
                "FloorDiv": "//", "Mod": "%", "Pow": "**",
                "LShift": "<<", "RShift": ">>", "BitOr": "|",
                "BitXor": "^", "BitAnd": "&",
                "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=",
                "Gt": ">", "GtE": ">=", "Is": "is", "IsNot": "is not",
                "In": "in", "NotIn": "not in",
                "And": "and", "Or": "or", "Not": "not",
                "UAdd": "+", "USub": "-", "Invert": "~",
            }
            return op_map.get(value, value)
        
        if node.type == NodeType.KEYWORD:
            return value
        
        if node.type == NodeType.DELIMITER:
            return value
        
        return str(value)
    
    def _generate_pattern(self, node: PatternNode) -> str:
        """PatternNode → kód, a típus alapján."""
        handler = {
            NodeType.FUNCTION_DEF: self._gen_function_def,
            NodeType.CLASS_DEF: self._gen_class_def,
            NodeType.ASSIGNMENT: self._gen_assignment,
            NodeType.FOR_LOOP: self._gen_for_loop,
            NodeType.WHILE_LOOP: self._gen_while_loop,
            NodeType.IF_STATEMENT: self._gen_if_statement,
            NodeType.RETURN_STMT: self._gen_return,
            NodeType.FUNCTION_CALL: self._gen_function_call,
            NodeType.ATTRIBUTE_ACCESS: self._gen_attribute_access,
            NodeType.INDEX_ACCESS: self._gen_index_access,
            NodeType.BINARY_OP: self._gen_binary_op,
            NodeType.UNARY_OP: self._gen_unary_op,
            NodeType.COMPARISON: self._gen_comparison,
            NodeType.BLOCK: self._gen_block,
            NodeType.IMPORT: self._gen_import,
            NodeType.LIST_COMP: self._gen_list_comp,
            NodeType.LAMBDA: self._gen_lambda,
            NodeType.EXPRESSION: self._gen_expression,
        }
        
        handler_fn = handler.get(node.type)
        if handler_fn:
            return handler_fn(node)
        
        # Fallback: próbáljuk értelmezni a gyerekekből
        return self._gen_fallback(node)
    
    def _get_child(self, node: PatternNode, role: str, index: int = 0) -> Optional[BaseNode]:
        """Biztonságos gyerek lekérés."""
        children = node.children.get(role, [])
        if index < len(children):
            return children[index]
        return None
    
    def _generate_children(self, children: list[BaseNode], separator: str = ", ") -> str:
        """Több gyerek generálása."""
        parts = [self.generate(c) for c in children]
        return separator.join(parts)
    
    # ─── Specific generators ───────────────────────────────────────
    
    def _gen_function_def(self, node: PatternNode) -> str:
        name = self._get_child(node, "name")
        params = node.children.get("params", [])
        body = self._get_child(node, "body")
        decorators = node.children.get("decorators", [])
        returns = self._get_child(node, "returns")
        
        lines = []
        
        # Decoratorok
        for dec in decorators:
            dec_code = self.generate(dec)
            lines.append(f"{self._indent()}@{dec_code}")
        
        # Fejléc
        header = f"{self._indent()}def {self.generate(name)}("
        param_strs = [self.generate(p) for p in params]
        header += ", ".join(param_strs) + "):"
        lines.append(header)
        
        # Body
        if body:
            old_indent = self._indent_level
            self._indent_level += 1
            body_code = self.generate(body)
            lines.append(body_code)
            self._indent_level = old_indent
        else:
            lines.append(f"{self._indent()}{' ' * self.indent_size}pass")
        
        return "\n".join(lines)
    
    def _gen_class_def(self, node: PatternNode) -> str:
        name = self._get_child(node, "name")
        bases = node.children.get("bases", [])
        body = self._get_child(node, "body")
        decorators = node.children.get("decorators", [])
        
        lines = []
        
        for dec in decorators:
            dec_code = self.generate(dec)
            lines.append(f"{self._indent()}@{dec_code}")
        
        header = f"{self._indent()}class {self.generate(name)}"
        if bases:
            header += "(" + ", ".join(self.generate(b) for b in bases) + ")"
        header += ":"
        lines.append(header)
        
        if body:
            old_indent = self._indent_level
            self._indent_level += 1
            body_code = self.generate(body)
            lines.append(body_code)
            self._indent_level = old_indent
        else:
            lines.append(f"{self._indent()}{' ' * self.indent_size}pass")
        
        return "\n".join(lines)
    
    def _gen_assignment(self, node: PatternNode) -> str:
        targets = node.children.get("targets", node.children.get("target", []))
        value = self._get_child(node, "value")
        operator_node = self._get_child(node, "operator")
        
        # Ellenorizzuk, hogy tuple/tomb-e a target (tuple unpacking)
        target_strs = []
        for t in targets:
            if isinstance(t, PatternNode) and t.type == NodeType.EXPRESSION:
                elements = t.children.get("elements", t.children.get("values", []))
                if elements:
                    # Tuple unpacking: a, b = ... (ne [a, b] = ...)
                    target_strs.append(", ".join(self.generate(e) for e in elements))
                else:
                    target_strs.append(self.generate(t))
            elif isinstance(t, PatternNode) and t.type == NodeType.INDEX_ACCESS:
                target_strs.append(self.generate(t))
            else:
                target_strs.append(self.generate(t))
        
        # Tuple/unpacking esetén a value-t is máshogy kell
        value_str = ""
        if value:
            # Ha a value is EXPRESSION elements-szel, az tuple lehet
            if isinstance(value, PatternNode) and value.type == NodeType.EXPRESSION:
                elements = value.children.get("elements", value.children.get("values", []))
                if elements:
                    value_str = ", ".join(self.generate(e) for e in elements)
                else:
                    value_str = self.generate(value)
            else:
                value_str = self.generate(value)
        
        target_str = ", ".join(target_strs)
        
        if operator_node:
            op = self.generate(operator_node)
            # value_str mar definialva van fentebb
            return f"{self._indent()}{target_str} {op}= {value_str}"
        
        annotation = self._get_child(node, "annotation")
        if annotation and not value:
            return f"{self._indent()}{target_str}: {self.generate(annotation)}"
        elif annotation:
            return f"{self._indent()}{target_str}: {self.generate(annotation)} = {value_str}"
        
        if value:
            return f"{self._indent()}{target_str} = {value_str}"
        
        return f"{self._indent()}{target_str} = ..."
    
    def _gen_for_loop(self, node: PatternNode) -> str:
        target = self._get_child(node, "target")
        iter_node = self._get_child(node, "iter")
        body = self._get_child(node, "body")
        orelse = node.children.get("orelse", [])
        
        target_str = self.generate(target) if target else "?"
        iter_str = self.generate(iter_node) if iter_node else "?"
        
        lines = [f"{self._indent()}for {target_str} in {iter_str}:"]
        
        if body:
            old_indent = self._indent_level
            self._indent_level += 1
            body_code = self.generate(body)
            lines.append(body_code)
            self._indent_level = old_indent
        else:
            lines.append(f"{self._indent()}{' ' * self.indent_size}pass")
        
        if orelse:
            old_indent = self._indent_level
            self._indent_level += 1
            lines.append(f"{self._indent()* 0}else:")
            for o in orelse:
                lines.append(self.generate(o))
            self._indent_level = old_indent
        
        return "\n".join(lines)
    
    def _gen_while_loop(self, node: PatternNode) -> str:
        condition = self._get_child(node, "condition")
        body = self._get_child(node, "body")
        
        cond_str = self.generate(condition) if condition else "True"
        
        lines = [f"{self._indent()}while {cond_str}:"]
        
        if body:
            old_indent = self._indent_level
            self._indent_level += 1
            body_code = self.generate(body)
            lines.append(body_code)
            self._indent_level = old_indent
        else:
            lines.append(f"{self._indent()}{' ' * self.indent_size}pass")
        
        return "\n".join(lines)
    
    def _gen_if_statement(self, node: PatternNode) -> str:
        condition = self._get_child(node, "condition")
        body = self._get_child(node, "body")
        
        cond_str = self.generate(condition) if condition else "True"
        
        lines = [f"{self._indent()}if {cond_str}:"]
        
        if body:
            old_indent = self._indent_level
            self._indent_level += 1
            body_code = self.generate(body)
            lines.append(body_code)
            self._indent_level = old_indent
        else:
            lines.append(f"{self._indent()}{' ' * self.indent_size}pass")
        
        # Else/elif lánc — REKURZÍVAN, mindig a SZÜLŐ indent szintjén
        self._gen_elif_chain(node, lines)
        
        return "\n".join(lines)
    
    def _gen_elif_chain(self, node: PatternNode, lines: list):
        """If/elif/else lánc generálása (rekurzív, szülő indent szinten)."""
        orelse = node.children.get("orelse", [])
        if not orelse:
            return
        
        first_orelse = orelse[0]
        if isinstance(first_orelse, PatternNode) and first_orelse.type == NodeType.IF_STATEMENT:
            # ELIF: ugyanazon indent szinten, mint a szülő if
            cond = self._get_child(first_orelse, "condition")
            cond_str = self.generate(cond) if cond else "True"
            lines.append(f"{self._indent()}elif {cond_str}:")
            
            elif_body = self._get_child(first_orelse, "body")
            if elif_body:
                old = self._indent_level
                self._indent_level += 1
                lines.append(self.generate(elif_body))
                self._indent_level = old
            else:
                lines.append(f"{self._indent()}{' ' * self.indent_size}pass")
            
            # Rekurzív: elif-nek is lehet orelse-je (újabb elif vagy else)
            self._gen_elif_chain(first_orelse, lines)
        else:
            # ELSE
            lines.append(f"{self._indent()}else:")
            old = self._indent_level
            self._indent_level += 1
            for o in orelse:
                o_code = self.generate(o)
                if o_code:
                    # Ha nincs már indentálva, adjunk hozzá
                    if not o_code.startswith(' '):
                        lines.append(f"{self._indent()}{o_code}")
                    else:
                        lines.append(o_code)
            self._indent_level = old
    
    def _gen_return(self, node: PatternNode) -> str:
        value = self._get_child(node, "value")
        if value:
            return f"{self._indent()}return {self.generate(value)}"
        return f"{self._indent()}return"
    
    def _gen_function_call(self, node: PatternNode) -> str:
        func = self._get_child(node, "func")
        args = node.children.get("args", [])
        kwargs = node.children.get("kwargs", [])
        
        func_str = self.generate(func) if func else "?"
        
        arg_parts = [self.generate(a) for a in args]
        for kw in kwargs:
            if isinstance(kw, PatternNode) and kw.type == NodeType.ASSIGNMENT:
                target = self._get_child(kw, "target", 0)
                value = self._get_child(kw, "value", 0)
                arg_parts.append(f"{self.generate(target)}={self.generate(value)}")
        
        return f"{func_str}({', '.join(arg_parts)})"
    
    def _gen_attribute_access(self, node: PatternNode) -> str:
        obj = self._get_child(node, "object")
        attr = self._get_child(node, "attribute")
        
        obj_str = self.generate(obj) if obj else "?"
        attr_str = self.generate(attr) if attr else "?"
        
        return f"{obj_str}.{attr_str}"
    
    def _gen_index_access(self, node: PatternNode) -> str:
        obj = self._get_child(node, "object")
        index = self._get_child(node, "index")
        
        obj_str = self.generate(obj) if obj else "?"
        idx_str = self.generate(index) if index else "?"
        
        return f"{obj_str}[{idx_str}]"
    
    def _gen_binary_op(self, node: PatternNode) -> str:
        left = self._get_child(node, "left")
        operator = self._get_child(node, "operator")
        right = self._get_child(node, "right")
        values = node.children.get("values", [])
        
        if operator:
            op_str = " " + self.generate(operator) + " "
            
            left_str = self.generate(left) if left else ""
            right_str = self.generate(right) if right else ""
            
            if left_str and right_str:
                # Operator precedence: csak akkor kell zarojel, ha a gyerek
                # operátorának alacsonyabb a precedenciája
                parent_op = self.generate(operator) if operator else ""
                
                needs_parens = False
                for child, child_str in [(left, left_str), (right, right_str)]:
                    if child and isinstance(child, PatternNode) and child.type == NodeType.BINARY_OP:
                        child_op_node = child.children.get("operator", [None])[0]
                        child_op = self.generate(child_op_node) if child_op_node else ""
                        if _needs_parens(parent_op, child_op):
                            needs_parens = True
                    elif child and isinstance(child, PatternNode) and child.type == NodeType.COMPARISON:
                        needs_parens = True
                
                if needs_parens:
                    return f"({left_str}{op_str}{right_str})"
                return f"{left_str}{op_str}{right_str}"
            
            # Ha több érték (BoolOp)
            return op_str.join(self.generate(v) for v in values)
        
        return "?"
    
    def _gen_unary_op(self, node: PatternNode) -> str:
        operator = self._get_child(node, "operator")
        operand = self._get_child(node, "operand")
        
        op_str = self.generate(operator) if operator else ""
        operand_str = self.generate(operand) if operand else "?"
        
        return f"{op_str}{operand_str}"

    def _gen_comparison(self, node: PatternNode) -> str:
        left = self._get_child(node, "left")
        ops = node.children.get("ops", [])
        comparators = node.children.get("comparators", [])
        
        left_str = self.generate(left) if left else "?"
        result = left_str
        
        for i, op_node in enumerate(ops):
            op_str = self.generate(op_node)
            comp_str = self.generate(comparators[i]) if i < len(comparators) else "?"
            result += f" {op_str} {comp_str}"
        
        return result
    
    def _gen_block(self, node: PatternNode) -> str:
        """Blokk generálása (indentált utasítások)."""
        stmts = node.children.get("statements", node.children.get("body", []))
        indent = self._indent()
        lines = []
        for stmt in stmts:
            code = self.generate(stmt)
            if code:
                # Csak akkor adunk indent-et, ha a statement még nem tartalmazza
                if not code.startswith(" " * self.indent_size):
                    lines.append(f"{indent}{code}")
                else:
                    lines.append(code)
        return "\n".join(lines)
    
    def _gen_import(self, node: PatternNode) -> str:
        module = self._get_child(node, "module")
        names = node.children.get("names", [])
        
        if module:
            mod_str = self.generate(module)
            name_strs = ", ".join(self.generate(n) for n in names)
            return f"{self._indent()}from {mod_str} import {name_strs}"
        else:
            name_strs = ", ".join(self.generate(n) for n in names)
            return f"{self._indent()}import {name_strs}"
    
    def _gen_list_comp(self, node: PatternNode) -> str:
        elt = self._get_child(node, "elt")
        key = self._get_child(node, "key")
        val = self._get_child(node, "value")
        generators = node.children.get("generators", [])
        
        elt_str = self.generate(key) + ": " + self.generate(val) if key and val else self.generate(elt) if elt else "?"
        
        gen_strs = []
        for gen in generators:
            if isinstance(gen, PatternNode):
                gen_strs.append(self.generate(gen))
        
        return f"[{elt_str} {' '.join(gen_strs)}]"
    
    def _gen_lambda(self, node: PatternNode) -> str:
        """lambda x: x + 1"""
        params = node.children.get("params", [])
        body = self._get_child(node, "body")
        param_str = ", ".join(self.generate(p) for p in params)
        body_str = self.generate(body) if body else "None"
        return f"lambda {param_str}: {body_str}"
    
    def _gen_expression(self, node: PatternNode) -> str:
        """Általános kifejezés — próbáljuk a gyerekekből."""
        elements = node.children.get("elements", [])
        if elements is not None:
            if elements:
                items = [self.generate(e) for e in elements]
                return "[" + ", ".join(items) + "]"
            else:
                # Üres lista []
                return "[]"
        
        keys = node.children.get("keys", [])
        vals = node.children.get("values", [])
        if keys and vals:
            items = [f"{self.generate(k)}: {self.generate(v)}" for k, v in zip(keys, vals)]
            return "{" + ", ".join(items) + "}"
        
        return "?"
    
    def _gen_fallback(self, node: PatternNode) -> str:
        """Ha nincs specifikus generátor, próbáljuk értelmezni a gyerekekből."""
        if not node.children:
            return ""
        
        # Próbáljuk a body-t generálni
        body = node.children.get("body", [])
        if body:
            return "\n".join(self.generate(b) for b in body)
        
        # Próbáljuk az összes gyereket szekvenciálisan
        parts = []
        for role, children in node.children.items():
            for child in children:
                code = self.generate(child)
                if code:
                    parts.append(code)
        
        return " ".join(parts)
    
    def _gen_schema(self, node: SchemaNode) -> str:
        """Séma: válassza ki a legjobb mintát és generálja azt."""
        if not node.pattern_ids:
            return ""
        
        # Első minta generálása
        first_pid = next(iter(node.pattern_ids))
        pattern = self.graph.patterns.get(first_pid) if self.graph else None
        if pattern:
            return self.generate(pattern)
        
        return f"<Schema:{node.name}>"
    
    def generate_from_ids(self, nid: str) -> str:
        """Nódus ID alapján generál."""
        node = self.graph.get_node(nid) if self.graph else None
        if node:
            return self.generate(node)
        return ""
    
    def generate_program(self, nids: list[str]) -> str:
        """Több nódusból teljes program generálása."""
        parts = []
        for nid in nids:
            code = self.generate_from_ids(nid)
            if code:
                parts.append(code)
        return "\n\n".join(parts)


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    from grammar_parser import GrammarParser
    
    parser = GrammarParser()
    graph = HypergraphV2()
    gen = ConstructiveGenerator(graph)
    
    test_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''
    
    nodes = parser.parse(test_code)
    nids = graph.ingest_pattern_tree(nodes)
    
    print("=== EREDETI KÓD ===")
    print(test_code.strip())
    
    print("\n=== GENERÁLT KÓD ===")
    generated = gen.generate_program(nids)
    print(generated)
    
    print("\n=== GRÁF STATISZTIKA ===")
    stats = graph.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # Próbáljuk ki az SRT-t
    if nids:
        first_nid = nids[0]
        scope = graph.get_context_scope(first_nid)
        print(f"\n=== AKTÍV SCOPE (focus={first_nid[:8]}...) ===")
        print(f"  Total SE: {scope['total_se']}")
        print(f"  Gyerekek: {len(scope['children'])}")
        print(f"  Szülők: {len(scope['parents'])}")
        print(f"  Testvérek: {len(scope['siblings'])}")
