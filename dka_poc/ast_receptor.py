import ast
import builtins

class VariableAbstractor(ast.NodeTransformer):
    """
    Replaces concrete variable and function names with generic placeholders (VAR_1, VAR_2).
    Ignores built-in names like 'print', 'int', etc.
    """
    def __init__(self):
        self.var_map = {}
        self.var_counter = 1
        self.ignore_names = set(dir(builtins)) | {'self', 'True', 'False', 'None'}

    def get_abstract_name(self, name):
        if name in self.ignore_names:
            return name
        if name not in self.var_map:
            self.var_map[name] = f"VAR_{self.var_counter}"
            self.var_counter += 1
        return self.var_map[name]

    def visit_Name(self, node):
        node.id = self.get_abstract_name(node.id)
        return self.generic_visit(node)
        
    def visit_arg(self, node):
        node.arg = self.get_abstract_name(node.arg)
        return self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        node.name = self.get_abstract_name(node.name)
        return self.generic_visit(node)

class ASTReceptor:
    """
    Translates Python code into discrete logical blocks using the Abstract Syntax Tree (AST).
    With the VariableAbstractor, it learns patterns instead of hardcoded variable names.
    """
    def __init__(self):
        pass

    def process(self, text):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []
            
        # Abstract variables BEFORE tokenization
        abstractor = VariableAbstractor()
        tree = abstractor.visit(tree)
        ast.fix_missing_locations(tree)
        
        tokens = []
        
        class TokenVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                args = ast.unparse(node.args)
                tokens.append(f"FUNC:{node.name}({args})")
                for stmt in node.body:
                    self.visit(stmt)
                tokens.append("END_BLOCK")
                
            def visit_If(self, node):
                test_src = ast.unparse(node.test)
                tokens.append(f"IF:{test_src}")
                for stmt in node.body:
                    self.visit(stmt)
                if node.orelse:
                    tokens.append("ELSE")
                    for stmt in node.orelse:
                        self.visit(stmt)
                tokens.append("END_BLOCK")
                
            def visit_Expr(self, node):
                tokens.append(f"STMT:{ast.unparse(node.value)}")
                
            def visit_Return(self, node):
                val = ast.unparse(node.value) if node.value else ""
                tokens.append(f"RETURN:{val}")

            def visit_Assign(self, node):
                tokens.append(f"ASSIGN:{ast.unparse(node)}")
                
            def generic_visit(self, node):
                # Fallback for other statements
                if isinstance(node, ast.stmt) and not isinstance(node, (ast.FunctionDef, ast.If, ast.Expr, ast.Return, ast.Assign)):
                    tokens.append(f"STMT:{ast.unparse(node)}")
                super().generic_visit(node)
                
        visitor = TokenVisitor()
        for stmt in tree.body:
            visitor.visit(stmt)
            
        return tokens

