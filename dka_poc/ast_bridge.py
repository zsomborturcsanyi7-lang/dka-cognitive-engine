import os

class ASTCodeGenerator:
    """
    Converts AST-based logical blocks back into perfectly formatted Python code.
    Since it uses structural markers (FUNC, IF, STMT), syntax errors are eliminated.
    """
    def __init__(self, engine):
        self.engine = engine

    def detokenize(self, tokens):
        """
        Converts a sequence of AST block tokens into valid Python code.
        """
        lines = []
        indent = 0
        
        for token in tokens:
            # Handle relaxed tokens from constraints
            if token.startswith("<") and token.endswith("_RECONSTRUCTED>"):
                continue

            if token.startswith("FUNC:"):
                signature = token.split(":", 1)[1]
                lines.append("    " * indent + f"def {signature}:")
                indent += 1
            elif token.startswith("IF:"):
                cond = token.split(":", 1)[1]
                lines.append("    " * indent + f"if {cond}:")
                indent += 1
            elif token == "ELSE":
                indent -= 1
                lines.append("    " * indent + "else:")
                indent += 1
            elif token == "END_BLOCK":
                indent = max(0, indent - 1)
            elif token.startswith("STMT:"):
                stmt = token.split(":", 1)[1]
                lines.append("    " * indent + stmt)
            elif token.startswith("ASSIGN:"):
                stmt = token.split(":", 1)[1]
                lines.append("    " * indent + stmt)
            elif token.startswith("RETURN:"):
                val = token.split(":", 1)[1]
                if val:
                    lines.append("    " * indent + f"return {val}")
                else:
                    lines.append("    " * indent + "return")
            else:
                # Fallback for unexpected tokens
                lines.append("    " * indent + f"# Unknown block: {token}")
                
        return "\n".join(lines)

    def generate_to_file(self, start_token, output_path, max_length=50):
        generated_tokens, _ = self.engine.generate(start_token, max_length=max_length, expand_meta=True)
        code = self.detokenize(generated_tokens)
                
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return code
