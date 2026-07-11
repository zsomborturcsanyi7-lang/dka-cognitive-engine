"""
DKA Core — GrammarParser
=========================
Nem tokenizál, hanem strukturált mintákká alakítja a Python kódot.

Kimenet: PatternNode-ok fája, ahol minden ágnak jelentése van.
Nem ['def', 'foo', '(', ...] sorozat, hanem:
  FunctionDef
    ├── name: "foo"
    ├── params: [...]
    └── body: Block [...]

Minden amit a parser lát, az rögzítve van a PatternNode roles-ában.
"""

from __future__ import annotations
import ast
import builtins
from typing import Optional

from node_types import (
    PrimitiveNode, PatternNode, SchemaNode,
    NodeType, DataDomain, Role,
    BaseNode,
)


class GrammarParser:
    """
    Python kód → Strukturált PatternNode fa.
    Nem token sorozat, hanem típusos, hierarchikus nódusok.
    """
    
    def __init__(self):
        self.ignore_names = set(dir(builtins)) | {'self', 'cls', 'True', 'False', 'None'}
        self._next_abstract_id = 1
    
    def parse(self, code: str, domain: DataDomain = DataDomain.GENERAL, 
              source: str = "") -> list[PatternNode | PrimitiveNode]:
        """
        Fő belépési pont. Python kód → PatternNode fák listája.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # Ha nem tiszta Python, próbáljuk hibajavítva
            print(f"[GrammarParser] SyntaxError: {e}")
            return self._parse_as_fallback(code, domain, source)
        
        return self._parse_module(tree, domain, source)
    
    def _parse_module(self, tree: ast.Module, domain: DataDomain, 
                      source: str) -> list:
        nodes = []
        for stmt in tree.body:
            node = self._parse_statement(stmt, domain, source)
            if node:
                nodes.append(node)
        return nodes
    
    def _parse_statement(self, stmt: ast.stmt, domain: DataDomain,
                         source: str) -> Optional[BaseNode]:
        """Dispatch different statement types."""
        handler_map = {
            ast.FunctionDef: self._parse_function_def,
            ast.AsyncFunctionDef: self._parse_function_def,
            ast.ClassDef: self._parse_class_def,
            ast.Assign: self._parse_assign,
            ast.AugAssign: self._parse_aug_assign,
            ast.AnnAssign: self._parse_ann_assign,
            ast.For: self._parse_for,
            ast.AsyncFor: self._parse_for,
            ast.While: self._parse_while,
            ast.If: self._parse_if,
            ast.With: self._parse_with,
            ast.Return: self._parse_return,
            ast.Expr: self._parse_expr_stmt,
            ast.Import: self._parse_import,
            ast.ImportFrom: self._parse_import_from,
            ast.Try: self._parse_try,
            ast.Raise: self._parse_raise,
            ast.Break: lambda *a: PrimitiveNode(type=NodeType.KEYWORD, value="break", domain=domain),
            ast.Continue: lambda *a: PrimitiveNode(type=NodeType.KEYWORD, value="continue", domain=domain),
            ast.Pass: lambda *a: PrimitiveNode(type=NodeType.KEYWORD, value="pass", domain=domain),
            ast.Delete: self._parse_delete,
            ast.Global: lambda *a: PrimitiveNode(type=NodeType.KEYWORD, value="global", domain=domain),
            ast.Nonlocal: lambda *a: PrimitiveNode(type=NodeType.KEYWORD, value="nonlocal", domain=domain),
            ast.Assert: self._parse_assert,
        }
        
        handler = handler_map.get(type(stmt))
        if handler:
            return handler(stmt, domain, source)
        
        return PrimitiveNode(
            type=NodeType.UNKNOWN,
            value=f"<{type(stmt).__name__}>",
            domain=domain, source=source
        )
    
    def _parse_function_def(self, stmt: ast.FunctionDef | ast.AsyncFunctionDef,
                           domain: DataDomain, source: str) -> PatternNode:
        """def name(params): body → FunctionDef pattern"""
        is_async = isinstance(stmt, ast.AsyncFunctionDef)
        
        func_node = PatternNode(
            type=NodeType.FUNCTION_DEF,
            domain=domain, source=source,
            roles={
                "name": Role("name", cardinality=(1, 1)),
                "params": Role("params", cardinality=(0, None)),
                "body": Role("body", cardinality=(1, 1)),
                "decorators": Role("decorators", cardinality=(0, None)),
                "returns": Role("returns", cardinality=(0, 1)),
            }
        )
        
        # Név
        name_node = PrimitiveNode(
            type=NodeType.VARIABLE,
            value=stmt.name,
            role="name",
            domain=domain, source=source
        )
        func_node.children["name"] = [name_node]
        
        # Paraméterek
        params = self._parse_arguments(stmt.args, domain, source)
        func_node.children["params"] = params
        
        # Decoratorok
        if stmt.decorator_list:
            func_node.children["decorators"] = [
                self._parse_expression(d, domain, source)
                for d in stmt.decorator_list
            ]
        
        # Return annotation
        if stmt.returns:
            func_node.children["returns"] = [
                self._parse_expression(stmt.returns, domain, source)
            ]
        
        # Body
        body_block = self._make_block(stmt.body, domain, source)
        func_node.children["body"] = [body_block]
        
        return func_node
    
    def _parse_class_def(self, stmt: ast.ClassDef, domain: DataDomain,
                         source: str) -> PatternNode:
        class_node = PatternNode(
            type=NodeType.CLASS_DEF,
            domain=domain, source=source,
            roles={
                "name": Role("name", cardinality=(1, 1)),
                "bases": Role("bases", cardinality=(0, None)),
                "body": Role("body", cardinality=(1, 1)),
                "decorators": Role("decorators", cardinality=(0, None)),
            }
        )
        
        class_node.children["name"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=stmt.name, 
                         role="name", domain=domain, source=source)
        ]
        
        if stmt.bases:
            class_node.children["bases"] = [
                self._parse_expression(b, domain, source) 
                for b in stmt.bases
            ]
        
        if stmt.decorator_list:
            class_node.children["decorators"] = [
                self._parse_expression(d, domain, source)
                for d in stmt.decorator_list
            ]
        
        class_node.children["body"] = [
            self._make_block(stmt.body, domain, source)
        ]
        
        return class_node
    
    def _parse_assign(self, stmt: ast.Assign, domain: DataDomain,
                      source: str) -> PatternNode:
        """target = value → Assignment pattern"""
        assign_node = PatternNode(
            type=NodeType.ASSIGNMENT,
            domain=domain, source=source,
            roles={
                "targets": Role("targets", cardinality=(1, None)),
                "value": Role("value", cardinality=(1, 1)),
            }
        )
        
        assign_node.children["targets"] = [
            self._parse_expression(t, domain, source)
            for t in stmt.targets
        ]
        assign_node.children["value"] = [
            self._parse_expression(stmt.value, domain, source)
        ]
        
        return assign_node
    
    def _parse_aug_assign(self, stmt: ast.AugAssign, domain: DataDomain,
                          source: str) -> PatternNode:
        """target += value → Assignment with operator"""
        assign_node = PatternNode(
            type=NodeType.ASSIGNMENT,
            domain=domain, source=source,
            roles={
                "target": Role("target", cardinality=(1, 1)),
                "operator": Role("operator", cardinality=(1, 1)),
                "value": Role("value", cardinality=(1, 1)),
            }
        )
        
        assign_node.children["target"] = [
            self._parse_expression(stmt.target, domain, source)
        ]
        assign_node.children["operator"] = [
            PrimitiveNode(type=NodeType.OPERATOR, value=type(stmt.op).__name__,
                         role="operator", domain=domain)
        ]
        assign_node.children["value"] = [
            self._parse_expression(stmt.value, domain, source)
        ]
        
        return assign_node
    
    def _parse_ann_assign(self, stmt: ast.AnnAssign, domain: DataDomain,
                          source: str) -> PatternNode:
        assign_node = PatternNode(
            type=NodeType.ASSIGNMENT,
            domain=domain, source=source,
            roles={
                "target": Role("target", cardinality=(1, 1)),
                "annotation": Role("annotation", cardinality=(1, 1)),
                "value": Role("value", cardinality=(0, 1)),
            }
        )
        
        assign_node.children["target"] = [
            self._parse_expression(stmt.target, domain, source)
        ]
        assign_node.children["annotation"] = [
            self._parse_expression(stmt.annotation, domain, source)
        ]
        if stmt.value:
            assign_node.children["value"] = [
                self._parse_expression(stmt.value, domain, source)
            ]
        
        return assign_node
    
    def _parse_for(self, stmt: ast.For | ast.AsyncFor, domain: DataDomain,
                   source: str) -> PatternNode:
        """for target in iter: body → ForLoop pattern"""
        for_node = PatternNode(
            type=NodeType.FOR_LOOP,
            domain=domain, source=source,
            roles={
                "target": Role("target", cardinality=(1, 1)),
                "iter": Role("iter", cardinality=(1, 1)),
                "body": Role("body", cardinality=(1, 1)),
                "orelse": Role("orelse", cardinality=(0, 1)),
            }
        )
        
        for_node.children["target"] = [
            self._parse_expression(stmt.target, domain, source)
        ]
        for_node.children["iter"] = [
            self._parse_expression(stmt.iter, domain, source)
        ]
        for_node.children["body"] = [
            self._make_block(stmt.body, domain, source)
        ]
        if stmt.orelse:
            for_node.children["orelse"] = [
                self._make_block(stmt.orelse, domain, source)
            ]
        
        return for_node
    
    def _parse_while(self, stmt: ast.While, domain: DataDomain,
                     source: str) -> PatternNode:
        while_node = PatternNode(
            type=NodeType.WHILE_LOOP,
            domain=domain, source=source,
            roles={
                "condition": Role("condition", cardinality=(1, 1)),
                "body": Role("body", cardinality=(1, 1)),
                "orelse": Role("orelse", cardinality=(0, 1)),
            }
        )
        
        while_node.children["condition"] = [
            self._parse_expression(stmt.test, domain, source)
        ]
        while_node.children["body"] = [
            self._make_block(stmt.body, domain, source)
        ]
        if stmt.orelse:
            while_node.children["orelse"] = [
                self._make_block(stmt.orelse, domain, source)
            ]
        
        return while_node
    
    def _parse_if(self, stmt: ast.If, domain: DataDomain,
                  source: str) -> PatternNode:
        """if condition: body [else: orelse] → IfStatement pattern"""
        if_node = PatternNode(
            type=NodeType.IF_STATEMENT,
            domain=domain, source=source,
            roles={
                "condition": Role("condition", cardinality=(1, 1)),
                "body": Role("body", cardinality=(1, 1)),
                "orelse": Role("orelse", cardinality=(0, 1)),
            }
        )
        
        if_node.children["condition"] = [
            self._parse_expression(stmt.test, domain, source)
        ]
        if_node.children["body"] = [
            self._make_block(stmt.body, domain, source)
        ]
        if stmt.orelse:
            if_node.children["orelse"] = [
                self._parse_statement_or_block(stmt.orelse, domain, source)
            ]
        
        return if_node
    
    def _parse_with(self, stmt: ast.With, domain: DataDomain,
                    source: str) -> PatternNode:
        with_node = PatternNode(
            type=NodeType.BLOCK,
            domain=domain, source=source,
            roles={
                "context": Role("context", cardinality=(1, None)),
                "body": Role("body", cardinality=(1, 1)),
            }
        )
        
        with_node.children["context"] = [
            self._parse_withitem(item, domain, source)
            for item in stmt.items
        ]
        with_node.children["body"] = [
            self._make_block(stmt.body, domain, source)
        ]
        
        return with_node
    
    def _parse_withitem(self, item: ast.withitem, domain: DataDomain,
                        source: str) -> PatternNode:
        context_expr = self._parse_expression(item.context_expr, domain, source)
        if item.optional_vars:
            assign = PatternNode(
                type=NodeType.ASSIGNMENT,
                roles={
                    "target": Role("target", cardinality=(1, 1)),
                    "value": Role("value", cardinality=(1, 1)),
                }
            )
            assign.children["target"] = [
                self._parse_expression(item.optional_vars, domain, source)
            ]
            assign.children["value"] = [context_expr]
            return assign
        return context_expr
    
    def _parse_return(self, stmt: ast.Return, domain: DataDomain,
                      source: str) -> PatternNode:
        ret_node = PatternNode(
            type=NodeType.RETURN_STMT,
            domain=domain, source=source,
            roles={
                "value": Role("value", cardinality=(0, 1)),
            }
        )
        
        if stmt.value:
            ret_node.children["value"] = [
                self._parse_expression(stmt.value, domain, source)
            ]
        
        return ret_node
    
    def _parse_try(self, stmt: ast.Try, domain: DataDomain,
                   source: str) -> PatternNode:
        try_node = PatternNode(
            type=NodeType.BLOCK,  # Try blokk mint special block
            domain=domain, source=source,
            roles={
                "body": Role("body", cardinality=(1, 1)),
                "handlers": Role("handlers", cardinality=(0, None)),
                "orelse": Role("orelse", cardinality=(0, 1)),
                "finalbody": Role("finalbody", cardinality=(0, 1)),
            }
        )
        
        try_node.children["body"] = [
            self._make_block(stmt.body, domain, source)
        ]
        
        if stmt.handlers:
            handlers = []
            for h in stmt.handlers:
                handler = PatternNode(
                    type=NodeType.IF_STATEMENT,
                    domain=domain, source=source,
                    roles={
                        "type": Role("type", cardinality=(0, 1)),
                        "name": Role("name", cardinality=(0, 1)),
                        "body": Role("body", cardinality=(1, 1)),
                    }
                )
                if h.type:
                    handler.children["type"] = [
                        self._parse_expression(h.type, domain, source)
                    ]
                if h.name:
                    handler.children["name"] = [
                        PrimitiveNode(type=NodeType.VARIABLE, value=h.name,
                                     role="name", domain=domain, source=source)
                    ]
                handler.children["body"] = [
                    self._make_block(h.body, domain, source)
                ]
                handlers.append(handler)
            try_node.children["handlers"] = handlers
        
        if stmt.orelse:
            try_node.children["orelse"] = [
                self._make_block(stmt.orelse, domain, source)
            ]
        if stmt.finalbody:
            try_node.children["finalbody"] = [
                self._make_block(stmt.finalbody, domain, source)
            ]
        
        return try_node
    
    def _parse_raise(self, stmt: ast.Raise, domain: DataDomain,
                     source: str) -> PrimitiveNode:
        val = ast.unparse(stmt) if stmt.exc else "raise"
        return PrimitiveNode(type=NodeType.KEYWORD, value=val, domain=domain, source=source)
    
    def _parse_delete(self, stmt: ast.Delete, domain: DataDomain,
                      source: str) -> PrimitiveNode:
        val = ast.unparse(stmt)
        return PrimitiveNode(type=NodeType.EXPRESSION, value=val, domain=domain, source=source)
    
    def _parse_assert(self, stmt: ast.Assert, domain: DataDomain,
                      source: str) -> PrimitiveNode:
        val = ast.unparse(stmt)
        return PrimitiveNode(type=NodeType.EXPRESSION, value=val, domain=domain, source=source)
    
    def _parse_expr_stmt(self, stmt: ast.Expr, domain: DataDomain,
                         source: str) -> BaseNode:
        """Egy kifejezés mint utasítás (pl. függvényhívás önálló sorban)."""
        return self._parse_expression(stmt.value, domain, source)
    
    def _parse_import(self, stmt: ast.Import, domain: DataDomain,
                      source: str) -> PatternNode:
        imp = PatternNode(type=NodeType.IMPORT, domain=domain, source=source,
                          roles={"names": Role("names", cardinality=(1, None))})
        imp.children["names"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=a.name, domain=domain, source=source)
            for a in stmt.names
        ]
        return imp
    
    def _parse_import_from(self, stmt: ast.ImportFrom, domain: DataDomain,
                           source: str) -> PatternNode:
        imp = PatternNode(type=NodeType.IMPORT, domain=domain, source=source,
                          roles={"module": Role("module", cardinality=(1, 1)),
                                 "names": Role("names", cardinality=(1, None))})
        imp.children["module"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=stmt.module or "",
                         role="module", domain=domain, source=source)
        ]
        imp.children["names"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=a.name, domain=domain, source=source)
            for a in stmt.names
        ]
        return imp
    
    # ─── Expression parsing ──────────────────────────────────────
    
    def _parse_expression(self, expr: ast.expr, domain: DataDomain,
                          source: str) -> BaseNode:
        """Dispatch AST expression nodes."""
        handler_map = {
            ast.Name: self._parse_name,
            ast.Constant: self._parse_constant,
            ast.BinOp: self._parse_binop,
            ast.UnaryOp: self._parse_unaryop,
            ast.Call: self._parse_call,
            ast.Attribute: self._parse_attribute,
            ast.Subscript: self._parse_subscript,
            ast.List: lambda e, d, s: self._make_list_literal(e, d, s),
            ast.Dict: self._parse_dict,
            ast.Tuple: self._parse_tuple,
            ast.Set: self._parse_set,
            ast.Slice: self._parse_slice,
            ast.Compare: self._parse_compare,
            ast.BoolOp: self._parse_boolop,
            ast.IfExp: self._parse_if_exp,
            ast.Lambda: self._parse_lambda,
            ast.ListComp: self._parse_list_comp,
            ast.SetComp: self._parse_set_comp,
            ast.DictComp: self._parse_dict_comp,
            ast.GeneratorExp: self._parse_generator,
            ast.Starred: self._parse_starred,
            ast.FormattedValue: self._parse_formatted,
            ast.JoinedStr: self._parse_joined_str,
            ast.Await: self._parse_await,
            ast.Yield: self._parse_yield,
            ast.YieldFrom: self._parse_yield_from,
        }
        
        handler = handler_map.get(type(expr))
        if handler:
            return handler(expr, domain, source)
        
        return PrimitiveNode(
            type=NodeType.EXPRESSION,
            value=f"<{type(expr).__name__}>",
            domain=domain, source=source
        )
    
    def _parse_name(self, expr: ast.Name, domain: DataDomain,
                    source: str) -> PrimitiveNode:
        return PrimitiveNode(
            type=NodeType.VARIABLE,
            value=expr.id,
            domain=domain, source=source,
            fingerprints={"name_ref"}
        )
    
    def _parse_constant(self, expr: ast.Constant, domain: DataDomain,
                        source: str) -> PrimitiveNode:
        val = expr.value
        if isinstance(val, str):
            ntype = NodeType.LITERAL
            label = f'"{val}"'
        elif isinstance(val, (int, float)):
            ntype = NodeType.LITERAL
            label = str(val)
        elif isinstance(val, bool):
            ntype = NodeType.KEYWORD
            label = "True" if val else "False"
        elif val is None:
            ntype = NodeType.KEYWORD
            label = "None"
        else:
            ntype = NodeType.LITERAL
            label = str(val)
        
        return PrimitiveNode(type=ntype, value=label, domain=domain, source=source)
    
    def _parse_binop(self, expr: ast.BinOp, domain: DataDomain,
                     source: str) -> PatternNode:
        """left + right → BinaryOp pattern"""
        op_node = PatternNode(
            type=NodeType.BINARY_OP,
            domain=domain, source=source,
            roles={
                "left": Role("left", cardinality=(1, 1)),
                "operator": Role("operator", cardinality=(1, 1)),
                "right": Role("right", cardinality=(1, 1)),
            }
        )
        
        op_node.children["left"] = [
            self._parse_expression(expr.left, domain, source)
        ]
        op_node.children["operator"] = [
            PrimitiveNode(type=NodeType.OPERATOR,
                         value=type(expr.op).__name__,
                         role="operator", domain=domain)
        ]
        op_node.children["right"] = [
            self._parse_expression(expr.right, domain, source)
        ]
        
        return op_node
    
    def _parse_unaryop(self, expr: ast.UnaryOp, domain: DataDomain,
                       source: str) -> PatternNode:
        op_node = PatternNode(
            type=NodeType.UNARY_OP,
            domain=domain, source=source,
            roles={
                "operator": Role("operator", cardinality=(1, 1)),
                "operand": Role("operand", cardinality=(1, 1)),
            }
        )
        
        op_node.children["operator"] = [
            PrimitiveNode(type=NodeType.OPERATOR,
                         value=type(expr.op).__name__,
                         role="operator", domain=domain)
        ]
        op_node.children["operand"] = [
            self._parse_expression(expr.operand, domain, source)
        ]
        
        return op_node
    
    def _parse_call(self, expr: ast.Call, domain: DataDomain,
                    source: str) -> PatternNode:
        """func(args) → FunctionCall pattern"""
        call_node = PatternNode(
            type=NodeType.FUNCTION_CALL,
            domain=domain, source=source,
            roles={
                "func": Role("func", cardinality=(1, 1)),
                "args": Role("args", cardinality=(0, None)),
                "kwargs": Role("kwargs", cardinality=(0, None)),
            }
        )
        
        call_node.children["func"] = [
            self._parse_expression(expr.func, domain, source)
        ]
        
        if expr.args:
            call_node.children["args"] = [
                self._parse_expression(a, domain, source)
                for a in expr.args
            ]
        
        if expr.keywords:
            kwargs = []
            for kw in expr.keywords:
                kw_node = PatternNode(
                    type=NodeType.ASSIGNMENT,
                    roles={
                        "target": Role("target", cardinality=(1, 1)),
                        "value": Role("value", cardinality=(1, 1)),
                    }
                )
                kw_node.children["target"] = [
                    PrimitiveNode(type=NodeType.VARIABLE, value=kw.arg or "",
                                 role="name", domain=domain, source=source)
                ]
                kw_node.children["value"] = [
                    self._parse_expression(kw.value, domain, source)
                ]
                kwargs.append(kw_node)
            call_node.children["kwargs"] = kwargs
        
        return call_node
    
    def _parse_attribute(self, expr: ast.Attribute, domain: DataDomain,
                         source: str) -> PatternNode:
        """obj.attr → AttributeAccess pattern"""
        attr_node = PatternNode(
            type=NodeType.ATTRIBUTE_ACCESS,
            domain=domain, source=source,
            roles={
                "object": Role("object", cardinality=(1, 1)),
                "attribute": Role("attribute", cardinality=(1, 1)),
            }
        )
        
        attr_node.children["object"] = [
            self._parse_expression(expr.value, domain, source)
        ]
        attr_node.children["attribute"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=expr.attr,
                         role="attribute", domain=domain, source=source)
        ]
        
        return attr_node
    
    def _parse_subscript(self, expr: ast.Subscript, domain: DataDomain,
                         source: str) -> PatternNode:
        """obj[index] → IndexAccess pattern"""
        idx_node = PatternNode(
            type=NodeType.INDEX_ACCESS,
            domain=domain, source=source,
            roles={
                "object": Role("object", cardinality=(1, 1)),
                "index": Role("index", cardinality=(1, 1)),
            }
        )
        
        idx_node.children["object"] = [
            self._parse_expression(expr.value, domain, source)
        ]
        idx_node.children["index"] = [
            self._parse_expression(expr.slice, domain, source)
        ]
        
        return idx_node
    
    def _parse_compare(self, expr: ast.Compare, domain: DataDomain,
                       source: str) -> PatternNode:
        """left op right → Comparison pattern"""
        comp_node = PatternNode(
            type=NodeType.COMPARISON,
            domain=domain, source=source,
            roles={
                "left": Role("left", cardinality=(1, 1)),
                "ops": Role("ops", cardinality=(1, None)),
                "comparators": Role("comparators", cardinality=(1, None)),
            }
        )
        
        comp_node.children["left"] = [
            self._parse_expression(expr.left, domain, source)
        ]
        comp_node.children["ops"] = [
            PrimitiveNode(type=NodeType.OPERATOR,
                         value=type(op).__name__,
                         role="operator", domain=domain)
            for op in expr.ops
        ]
        comp_node.children["comparators"] = [
            self._parse_expression(c, domain, source)
            for c in expr.comparators
        ]
        
        return comp_node
    
    def _parse_boolop(self, expr: ast.BoolOp, domain: DataDomain,
                      source: str) -> PatternNode:
        """a and b / a or b"""
        op_name = type(expr.op).__name__
        bool_node = PatternNode(
            type=NodeType.BINARY_OP,
            domain=domain, source=source,
            roles={
                "operator": Role("operator", cardinality=(1, 1)),
                "values": Role("values", cardinality=(1, None)),
            }
        )
        bool_node.children["operator"] = [
            PrimitiveNode(type=NodeType.OPERATOR, value=op_name,
                         role="operator", domain=domain)
        ]
        bool_node.children["values"] = [
            self._parse_expression(v, domain, source)
            for v in expr.values
        ]
        return bool_node
    
    def _parse_if_exp(self, expr: ast.IfExp, domain: DataDomain,
                      source: str) -> PatternNode:
        """a if cond else b"""
        if_node = PatternNode(
            type=NodeType.IF_STATEMENT,
            domain=domain, source=source,
            roles={
                "condition": Role("condition", cardinality=(1, 1)),
                "body": Role("body", cardinality=(1, 1)),
                "orelse": Role("orelse", cardinality=(1, 1)),
            }
        )
        if_node.children["condition"] = [
            self._parse_expression(expr.test, domain, source)
        ]
        if_node.children["body"] = [
            self._parse_expression(expr.body, domain, source)
        ]
        if_node.children["orelse"] = [
            self._parse_expression(expr.orelse, domain, source)
        ]
        return if_node
    
    def _parse_lambda(self, expr: ast.Lambda, domain: DataDomain,
                      source: str) -> PatternNode:
        func_node = PatternNode(
            type=NodeType.LAMBDA,
            domain=domain, source=source,
            roles={
                "params": Role("params", cardinality=(0, None)),
                "body": Role("body", cardinality=(1, 1)),
            }
        )
        func_node.children["params"] = self._parse_arguments(expr.args, domain, source)
        func_node.children["body"] = [
            self._parse_expression(expr.body, domain, source)
        ]
        return func_node
    
    def _parse_list_comp(self, expr: ast.ListComp, domain: DataDomain,
                         source: str) -> PatternNode:
        lc = PatternNode(
            type=NodeType.LIST_COMP,
            domain=domain, source=source,
            roles={
                "elt": Role("elt", cardinality=(1, 1)),
                "generators": Role("generators", cardinality=(1, None)),
            }
        )
        lc.children["elt"] = [
            self._parse_expression(expr.elt, domain, source)
        ]
        lc.children["generators"] = self._parse_comprehension_generators(
            expr.generators, domain, source
        )
        return lc
    
    def _parse_set_comp(self, expr, domain, source):
        return self._parse_list_comp(expr, domain, source)
    
    def _parse_dict_comp(self, expr, domain, source):
        dc = PatternNode(
            type=NodeType.LIST_COMP,
            domain=domain, source=source,
            roles={
                "key": Role("key", cardinality=(1, 1)),
                "value": Role("value", cardinality=(1, 1)),
                "generators": Role("generators", cardinality=(1, None)),
            }
        )
        dc.children["key"] = [
            self._parse_expression(expr.key, domain, source)
        ]
        dc.children["value"] = [
            self._parse_expression(expr.value, domain, source)
        ]
        dc.children["generators"] = self._parse_comprehension_generators(
            expr.generators, domain, source
        )
        return dc
    
    def _parse_generator(self, expr, domain, source):
        return self._parse_list_comp(expr, domain, source)
    
    def _parse_comprehension_generators(self, generators, domain, source):
        gens = []
        for gen in generators:
            for_node = PatternNode(
                type=NodeType.FOR_LOOP,
                roles={
                    "target": Role("target", cardinality=(1, 1)),
                    "iter": Role("iter", cardinality=(1, 1)),
                    "ifs": Role("ifs", cardinality=(0, None)),
                }
            )
            for_node.children["target"] = [
                self._parse_expression(gen.target, domain, source)
            ]
            for_node.children["iter"] = [
                self._parse_expression(gen.iter, domain, source)
            ]
            if gen.ifs:
                for_node.children["ifs"] = [
                    self._parse_expression(if_clause, domain, source)
                    for if_clause in gen.ifs
                ]
            gens.append(for_node)
        return gens
    
    def _parse_starred(self, expr: ast.Starred, domain, source):
        return self._parse_expression(expr.value, domain, source)
    
    def _parse_formatted(self, expr, domain, source):
        val = ast.unparse(expr)
        return PrimitiveNode(type=NodeType.LITERAL, value=val, domain=domain, source=source)
    
    def _parse_joined_str(self, expr, domain, source):
        val = ast.unparse(expr)
        return PrimitiveNode(type=NodeType.LITERAL, value=val, domain=domain, source=source)
    
    def _parse_await(self, expr, domain, source):
        return self._parse_expression(expr.value, domain, source)
    
    def _parse_yield(self, expr, domain, source):
        val = ast.unparse(expr)
        return PrimitiveNode(type=NodeType.KEYWORD, value=val, domain=domain, source=source)
    
    def _parse_yield_from(self, expr, domain, source):
        val = ast.unparse(expr)
        return PrimitiveNode(type=NodeType.KEYWORD, value=val, domain=domain, source=source)
    
    # ─── Helpers ──────────────────────────────────────────────────
    
    def _parse_arguments(self, args: ast.arguments, domain: DataDomain,
                         source: str) -> list:
        params = []
        for arg in args.args:
            params.append(
                PrimitiveNode(type=NodeType.VARIABLE, value=arg.arg,
                             role="param", domain=domain, source=source)
            )
        if args.vararg:
            params.append(
                PrimitiveNode(type=NodeType.VARIABLE, value=f"*{args.vararg.arg}",
                             role="vararg", domain=domain, source=source)
            )
        for arg in args.kwonlyargs:
            params.append(
                PrimitiveNode(type=NodeType.VARIABLE, value=arg.arg,
                             role="kwarg", domain=domain, source=source)
            )
        if args.kwarg:
            params.append(
                PrimitiveNode(type=NodeType.VARIABLE, value=f"**{args.kwarg.arg}",
                             role="kwarg", domain=domain, source=source)
            )
        return params
    
    def _make_block(self, stmts: list[ast.stmt], domain: DataDomain,
                    source: str) -> PatternNode:
        """Egy blokk (függvény törzs, ciklus törzs, stb.) PatternNode-ként."""
        block = PatternNode(
            type=NodeType.BLOCK,
            domain=domain, source=source,
            roles={"statements": Role("statements", cardinality=(0, None))}
        )
        block.children["statements"] = [
            self._parse_statement(s, domain, source)
            for s in stmts
        ]
        return block
    
    def _parse_statement_or_block(self, stmts: list, domain, source):
        """Ha több utasítás van, blokkba teszi."""
        if len(stmts) == 1:
            return self._parse_statement(stmts[0], domain, source)
        return self._make_block(stmts, domain, source)
    
    def _make_list_literal(self, expr: ast.List, domain, source) -> PatternNode:
        elems = [self._parse_expression(e, domain, source) for e in expr.elts]
        list_node = PatternNode(
            type=NodeType.EXPRESSION,
            domain=domain, source=source,
            roles={"elements": Role("elements", cardinality=(0, None))}
        )
        list_node.children["elements"] = elems
        return list_node
    
    def _parse_dict(self, expr: ast.Dict, domain, source) -> PatternNode:
        d = PatternNode(
            type=NodeType.EXPRESSION,
            domain=domain, source=source,
            roles={"keys": Role("keys"), "values": Role("values")}
        )
        d.children["keys"] = [
            self._parse_expression(k, domain, source) if k else PrimitiveNode(type=NodeType.KEYWORD, value="**")
            for k in expr.keys
        ]
        d.children["values"] = [
            self._parse_expression(v, domain, source) for v in expr.values
        ]
        return d
    
    def _parse_tuple(self, expr: ast.Tuple, domain, source) -> PatternNode:
        return self._make_list_literal(expr, domain, source)
    
    def _parse_set(self, expr: ast.Set, domain, source) -> PatternNode:
        return self._make_list_literal(expr, domain, source)
    
    def _parse_slice(self, expr: ast.Slice, domain, source) -> PatternNode:
        return PrimitiveNode(type=NodeType.EXPRESSION, value=ast.unparse(expr),
                            domain=domain, source=source)
    
    def _parse_as_fallback(self, code: str, domain, source) -> list:
        """Ha nem tiszta Python, token-alapon próbálkozik."""
        import re
        tokens = re.findall(r"[a-zA-Z_]\w*|[0-9]+|==|!=|<=|>=|[-+*/=;(){}<>!&|,.\[\]:]", code)
        nodes = []
        for t in tokens:
            if t in ('if', 'else', 'for', 'while', 'def', 'class', 'return', 'import', 'from',
                     'try', 'except', 'finally', 'with', 'raise', 'pass', 'break', 'continue',
                     'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda', 'yield',
                     'global', 'nonlocal', 'assert', 'del', 'as'):
                nodes.append(PrimitiveNode(type=NodeType.KEYWORD, value=t, domain=domain, source=source))
            elif t in ('+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=', '+=', '-=', '*=', '/='):
                nodes.append(PrimitiveNode(type=NodeType.OPERATOR, value=t, domain=domain, source=source))
            elif t in ('(', ')', '{', '}', '[', ']', ';', ':', ',', '.'):
                nodes.append(PrimitiveNode(type=NodeType.DELIMITER, value=t, domain=domain, source=source))
            elif t.isdigit():
                nodes.append(PrimitiveNode(type=NodeType.LITERAL, value=t, domain=domain, source=source))
            else:
                nodes.append(PrimitiveNode(type=NodeType.VARIABLE, value=t, domain=domain, source=source))
        return nodes


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = GrammarParser()
    
    test_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def main():
    for i in range(10):
        print(fibonacci(i))
'''
    
    nodes = parser.parse(test_code)
    
    def print_tree(node, indent=0):
        prefix = "  " * indent
        if hasattr(node, 'type') and hasattr(node, 'value'):
            print(f"{prefix}{node.type.name}: {node.value[:40]}")
        elif hasattr(node, 'type'):
            print(f"{prefix}{node.type.name}")
        else:
            print(f"{prefix}{type(node).__name__}")
        
        if hasattr(node, 'children') and node.children:
            for role, children in node.children.items():
                print(f"{prefix}  [{role}]:")
                for child in children:
                    print_tree(child, indent + 2)
    
    for n in nodes:
        print_tree(n)
        print("---")
