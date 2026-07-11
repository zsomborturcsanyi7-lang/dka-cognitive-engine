import re

class Receptor:
    """
    Translates structured text into discrete symbolic sequences for the Hypergraph.
    Uses a deterministic regex-based tokenizer.
    """
    def __init__(self):
        # Correctly formatted raw string for regex including +=
        self.token_pattern = re.compile(r"'[^']*'|[a-zA-Z_]\w*|[0-9]+|(?:>=|<=|==|!=|\+=|\+\+|--)|[\+\-\*/=;(){}<>!&|\[\]\.\?\,,:]|\s+")

    def tokenize(self, text):
        """
        Converts input text into a sequence of non-whitespace tokens.
        """
        tokens = self.token_pattern.findall(text)
        # Filter out whitespace-only tokens to focus on logic
        return [t for t in tokens if not t.isspace()]

    def process(self, text):
        """
        Directly provides the sequence for the Hypergraph.
        """
        return self.tokenize(text)
