from receptor import Receptor
from hypergraph import Hypergraph
from engine import LogicEngine
import time
import os

class FileProcessor:
    """
    Reads external source files and integrates their logic.
    Now includes a 'watchdog' mode for directory monitoring.
    """
    def __init__(self, receptor, graph):
        self.receptor = receptor
        self.graph = graph
        self.processed_files = set()

    def process_file(self, file_path, domain="general", source=None):
        if not os.path.exists(file_path):
            return False
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tokens = self.receptor.process(content)
        # Use file_path as default source if none provided
        effective_source = source if source else file_path
        self.graph.learn(tokens, domain=domain, source=effective_source)
        return True

    def start_watchdog(self, directory, interval=2):
        """
        Monitors a directory and automatically ingests new or modified files.
        """
        print(f"[Watchdog] Megfigyelés indítva: {directory}")
        try:
            while True:
                for filename in os.listdir(directory):
                    if filename.endswith(('.py', '.json', '.txt')):
                        path = os.path.join(directory, filename)
                        mtime = os.path.getmtime(path)
                        file_key = (path, mtime)
                        
                        if file_key not in self.processed_files:
                            print(f"[Watchdog] Új/Módosult fájl: {filename}")
                            self.process_file(path)
                            self.processed_files.add(file_key)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("[Watchdog] Leállítva.")

class CodeGenerator:
    """
    Converts graph structures back into syntactically correct Python code.
    Translates logical markers ({, }, ;) into Pythonic indentation and colons.
    """
    def __init__(self, engine):
        self.engine = engine

    def detokenize(self, tokens):
        """
        Converts a list of tokens into a formatted Python string.
        """
        code = ""
        indent_level = 0
        
        for i, token in enumerate(tokens):
            if token == '{':
                code = code.rstrip() + ":\n"
                indent_level += 1
                code += "    " * indent_level
            elif token == '}':
                indent_level -= 1
                code = code.rstrip() + "\n" + "    " * indent_level
            elif token == ';':
                code = code.rstrip() + "\n" + "    " * indent_level
            else:
                # Basic token spacing
                # Symbols that should NOT have a space before them
                if token in ('.', ',', ':', ')', ']', ';'):
                    code = code.rstrip() + token + " "
                # Symbols that should NOT have a space after them
                elif token in ('(', '['):
                    code += token
                else:
                    code += token + " "
                    
        return code.strip()

    def generate_to_file(self, start_token, output_path, max_length=500):
        generated_tokens, _ = self.engine.generate(start_token, max_length=max_length, expand_meta=True)
        code = self.detokenize(generated_tokens)
                
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return code
