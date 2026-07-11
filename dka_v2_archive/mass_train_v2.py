"""
DKA V2 — Gyorsított tömeges tanítás
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from node_types import NodeType, DataDomain
from grammar_parser import GrammarParser
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from inference_engine_v2 import InferenceEngineV2


class FastDKA:
    """DKA pattern discovery nélkül — gyors tömeges tanításhoz."""
    def __init__(self):
        self.graph = HypergraphV2()
        self.parser = GrammarParser()
    
    def learn(self, code, source=""):
        old = self.graph.total_pies
        nodes = self.parser.parse(code, domain=DataDomain.GENERAL, source=source)
        self.graph.ingest_pattern_tree(nodes, domain=DataDomain.GENERAL, source=source)
        return self.graph.total_pies - old


def generate_all():
    """400+ függvény generálása."""
    
    def templ(template, name):
        return template.replace("{0}", name)
    
    codes = []
    
    # === 1. RENDEZÉSEK (25) ===
    for name in ["bubble_sort", "selection_sort", "insertion_sort", "merge_sort", "quick_sort"]:
        for sfx in ["", "_v2", "_alt", "_fast", "_simple"]:
            n = name + sfx
            if name == "bubble_sort":
                codes.append((n, templ('''
def {0}(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
''', n)))
            elif name == "selection_sort":
                codes.append((n, templ('''
def {0}(arr):
    n = len(arr)
    for i in range(n):
        m = i
        for j in range(i + 1, n):
            if arr[j] < arr[m]:
                m = j
        arr[i], arr[m] = arr[m], arr[i]
    return arr
''', n)))
            elif name == "insertion_sort":
                codes.append((n, templ('''
def {0}(arr):
    for i in range(1, len(arr)):
        k = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > k:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = k
    return arr
''', n)))
            elif name == "merge_sort":
                codes.append((n, templ('''
def {0}(arr):
    if len(arr) <= 1:
        return arr
    m = len(arr) // 2
    l = {0}(arr[:m])
    r = {0}(arr[m:])
    return merge_{0}(l, r)
def merge_{0}(a, b):
    r = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            r.append(a[i]); i += 1
        else:
            r.append(b[j]); j += 1
    r.extend(a[i:]); r.extend(b[j:])
    return r
''', n)))
            elif name == "quick_sort":
                codes.append((n, templ('''
def {0}(arr):
    if len(arr) <= 1:
        return arr
    p = arr[-1]
    l = [x for x in arr[:-1] if x <= p]
    r = [x for x in arr[:-1] if x > p]
    return {0}(l) + [p] + {0}(r)
''', n)))
    
    # === 2. KERESÉSEK (25) ===
    for sfx in ["", "_v2", "_alt", "_fast", "_simple"]:
        n = f"linear_search{sfx}"
        codes.append((n, templ('''
def {0}(items, target):
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1
''', n)))
        n = f"binary_search{sfx}"
        codes.append((n, templ('''
def {0}(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        m = (lo + hi) // 2
        if arr[m] == target:
            return m
        if arr[m] < target:
            lo = m + 1
        else:
            hi = m - 1
    return -1
''', n)))
        n = f"find_all{sfx}"
        codes.append((n, templ('''
def {0}(items, target):
    r = []
    for i, item in enumerate(items):
        if item == target:
            r.append(i)
    return r
''', n)))
        n = f"contains_element{sfx}"
        codes.append((n, templ('''
def {0}(items, target):
    for item in items:
        if item == target:
            return True
    return False
''', n)))
        n = f"count_element{sfx}"
        codes.append((n, templ('''
def {0}(items, target):
    c = 0
    for item in items:
        if item == target:
            c += 1
    return c
''', n)))
    
    # === 3. SZÁMELMÉLET (25) ===
    for sfx in ["", "_v2", "_alt", "_fast", "_simple"]:
        n = f"is_prime{sfx}"
        codes.append((n, templ('''
def {0}(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
''', n)))
        n = f"factorial{sfx}"
        codes.append((n, templ('''
def {0}(n):
    if n <= 1:
        return 1
    return n * {0}(n - 1)
''', n)))
        n = f"fibonacci{sfx}"
        codes.append((n, templ('''
def {0}(n):
    if n <= 1:
        return n
    return {0}(n - 1) + {0}(n - 2)
''', n)))
        n = f"gcd{sfx}"
        codes.append((n, templ('''
def {0}(a, b):
    while b:
        a, b = b, a % b
    return a
''', n)))
        n = f"lcm{sfx}"
        codes.append((n, templ('''
def {0}(a, b):
    return a * b // gcd(a, b)
''', n)))
    
    # === 4. LISTA MŰVELETEK (50) ===
    list_ops = [
        ("sum_list", 'total', '+='),
        ("max_value", 'max_val', 'if x > max_val: max_val = x'),
        ("min_value", 'min_val', 'if x < min_val: min_val = x'),
        ("filter_even", 'result', 'if x % 2 == 0: result.append(x)'),
        ("filter_odd", 'result', 'if x % 2 != 0: result.append(x)'),
        ("remove_duplicates", 'seen', 'if x not in seen: seen.append(x)'),
        ("square_all", 'result', 'result.append(x * x)'),
        ("double_all", 'result', 'result.append(x * 2)'),
        ("absolute_all", 'result', 'result.append(abs(x))'),
        ("increment_all", 'result', 'result.append(x + 1)'),
    ]
    templates = ["", "_v2", "_alt", "_fast", "_simple"]
    for base_name, acc, logic in list_ops:
        for sfx in templates:
            n = base_name + sfx
            codes.append((n, templ(f'''
def {n}(items):
    {acc} = []
    for x in items:
        {logic}
    return {acc}
''', n)))
    
    # === 5. SZÖVEG (25) ===
    for sfx in templates:
        n = f"reverse_string{sfx}"
        codes.append((n, templ('''
def {0}(s):
    return s[::-1]
''', n)))
        n = f"is_palindrome{sfx}"
        codes.append((n, templ('''
def {0}(s):
    return s == s[::-1]
''', n)))
        n = f"count_vowels{sfx}"
        codes.append((n, templ('''
def {0}(s):
    c = 0
    for ch in s:
        if ch in 'aeiouAEIOU':
            c += 1
    return c
''', n)))
        n = f"count_words{sfx}"
        codes.append((n, templ('''
def {0}(text):
    return len(text.split())
''', n)))
        n = f"to_lowercase{sfx}"
        codes.append((n, templ('''
def {0}(s):
    r = ''
    for ch in s:
        if 'A' <= ch <= 'Z':
            r += chr(ord(ch) + 32)
        else:
            r += ch
    return r
''', n)))
    
    # === 6. FÁJL (25) ===
    for sfx in templates:
        n = f"read_file{sfx}"
        codes.append((n, templ('''
def {0}(path):
    with open(path) as f:
        return f.read()
''', n)))
        n = f"write_file{sfx}"
        codes.append((n, templ('''
def {0}(path, data):
    with open(path, 'w') as f:
        f.write(data)
''', n)))
        n = f"read_lines{sfx}"
        codes.append((n, templ('''
def {0}(path):
    with open(path) as f:
        return [l.rstrip() for l in f]
''', n)))
        n = f"file_exists{sfx}"
        codes.append((n, templ('''
def {0}(path):
    try:
        with open(path):
            return True
    except FileNotFoundError:
        return False
''', n)))
        n = f"count_lines{sfx}"
        codes.append((n, templ('''
def {0}(path):
    with open(path) as f:
        return sum(1 for _ in f)
''', n)))
    
    # === 7. MATEMATIKA (25) ===
    for sfx in templates:
        n = f"is_even{sfx}"
        codes.append((n, f"def {n}(n):\n    return n % 2 == 0\n"))
        n = f"is_positive{sfx}"
        codes.append((n, f"def {n}(n):\n    return n > 0\n"))
        n = f"absolute_value{sfx}"
        codes.append((n, f"def {n}(n):\n    return n if n >= 0 else -n\n"))
        n = f"power{sfx}"
        codes.append((n, f"def {n}(base, exp):\n    r = 1\n    for _ in range(exp):\n        r *= base\n    return r\n"))
        n = f"digit_sum{sfx}"
        codes.append((n, templ('''
def {0}(n):
    s = 0
    n = abs(n)
    while n:
        s += n % 10
        n //= 10
    return s
''', n)))
    
    # === 8. HIBAKEZELÉS (15) ===
    for sfx in templates[:3]:
        n = f"safe_divide{sfx}"
        codes.append((n, templ('''
def {0}(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
''', n)))
        n = f"parse_int{sfx}"
        codes.append((n, templ('''
def {0}(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None
''', n)))
        n = f"safe_get{sfx}"
        codes.append((n, templ('''
def {0}(d, key, default=None):
    try:
        return d[key]
    except (KeyError, TypeError):
        return default
''', n)))
    
    # === 9. ADAT STRUKTÚRA (15) ===
    for sfx in templates[:3]:
        n = f"stack_push{sfx}"
        codes.append((n, templ('''
def {0}(stack, item):
    stack.append(item)
    return stack
''', n)))
        n = f"stack_pop{sfx}"
        codes.append((n, templ('''
def {0}(stack):
    if not stack:
        return None
    return stack.pop()
''', n)))
        n = f"queue_push{sfx}"
        codes.append((n, templ('''
def {0}(queue, item):
    queue.append(item)
    return queue
''', n)))
        n = f"queue_pop{sfx}"
        codes.append((n, templ('''
def {0}(queue):
    if not queue:
        return None
    return queue.pop(0)
''', n)))
        n = f"list_length{sfx}"
        codes.append((n, f"def {n}(items):\n    c = 0\n    for _ in items:\n        c += 1\n    return c\n"))
    
    # === 10. JÁTÉK (20) ===
    for sfx in templates:
        n = f"roll_dice{sfx}"
        codes.append((n, templ('''
def {0}():
    import random
    return random.randint(1, 6)
''', n)))
        n = f"shuffle_items{sfx}"
        codes.append((n, templ('''
def {0}(items):
    import random
    r = items[:]
    for i in range(len(r) - 1, 0, -1):
        j = random.randint(0, i)
        r[i], r[j] = r[j], r[i]
    return r
''', n)))
        n = f"random_pick{sfx}"
        codes.append((n, templ('''
def {0}(items):
    import random
    if not items:
        return None
    return random.choice(items)
''', n)))
        n = f"random_range{sfx}"
        codes.append((n, templ('''
def {0}(lo, hi):
    import random
    return random.randint(lo, hi)
''', n)))
    
    return codes


print("Függvények generálása...")
all_codes = generate_all()
print(f"  Generálva: {len(all_codes)} függvény")

print("\nDKA tanítása...")
t0 = time.time()
dka = FastDKA()
trained = 0
errors = 0
for name, code in all_codes:
    try:
        c = dka.learn(code, source=name)
        if c > 0:
            trained += 1
    except Exception:
        errors += 1
dt = time.time() - t0

stats = dka.graph.stats()
print(f"\n=== EREDMÉNY ===")
print(f"  Idő: {dt:.1f}s")
print(f"  Betanult: {trained}/{len(all_codes)}")
print(f"  Hiba: {errors}")
print(f"  PIE: {stats['total_pie']}")
print(f"  Primitív: {stats['primitives']}")
print(f"  Minta: {stats['patterns']}")

# Pattern discovery egyszer a végén
print("\nPattern discovery...")
t1 = time.time()
patterns = dka.graph.discover_patterns(min_instances=3)
dt2 = time.time() - t1
print(f"  Idő: {dt2:.1f}s")
print(f"  Talált minták: {len(patterns)}")

print("\nMentés...")
dka.graph.to_json_file("dka_trained_500.json")
import os
fsize = os.path.getsize("dka_trained_500.json") / 1024
print(f"  dka_trained_500.json ({fsize:.0f} KB)")

# Szemantikus index
print("\nSzemantikus index...")
from semantic_layer import SemanticIndex
sem = SemanticIndex(dka.graph)
sem.index_all()
sstats = sem.stats()
print(f"  Fogalmak: {sstats['total_concepts']}")
print(f"  Indexelt: {sstats['total_indexed_patterns']}")
