"""
DKA V2 — Alap algoritmusok betanítása
========================================
A DKA legnagyobb hiányossága: nincsenek alap algoritmus mintái.
"filter even numbers" → bubble_sort, mert a "filter" ismeretlen.

Megoldás: betanítjuk a 10 legalapvetőbb algoritmust.
Így a szintézis, a mutáció és a szemantikus keresés is 
tud velük dolgozni.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dka import DKA
from semantic_layer import SemanticExtractor

# A 10 legalapvetőbb algoritmus, amit minden fejlesztő ismer
ALAP_ALGORITMUSOK = {
    "sum_list": '''
def sum_list(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
''',
    "filter_even": '''
def filter_even(numbers):
    result = []
    for num in numbers:
        if num % 2 == 0:
            result.append(num)
    return result
''',
    "find_max": '''
def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val
''',
    "find_min": '''
def find_min(numbers):
    if not numbers:
        return None
    min_val = numbers[0]
    for num in numbers:
        if num < min_val:
            min_val = num
    return min_val
''',
    "contains": '''
def contains(items, target):
    for item in items:
        if item == target:
            return True
    return False
''',
    "reverse_list": '''
def reverse_list(items):
    result = []
    for i in range(len(items) - 1, -1, -1):
        result.append(items[i])
    return result
''',
    "count_occurrences": '''
def count_occurrences(items, target):
    count = 0
    for item in items:
        if item == target:
            count += 1
    return count
''',
    "are_all_positive": '''
def are_all_positive(numbers):
    for num in numbers:
        if num <= 0:
            return False
    return True
''',
    "get_first_n": '''
def get_first_n(items, n):
    return items[:n]
''',
    "merge_sorted": '''
def merge_sorted(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result
''',
}

def train_alap(dka=None):
    if dka is None:
        dka = DKA()
    
    for name, code in ALAP_ALGORITMUSOK.items():
        count = dka.learn(code, source=name)
        print(f"  [+] {name}: +{count} PIE")
    
    # Bővítsük a szemantikus indexet közvetlenül az ismert szavakkal
    extractor = SemanticExtractor()
    
    # Minden KNOWN_PATTERNS kulcsszó legyen fogalom
    for keyword, tags in extractor.KNOWN_PATTERNS.items():
        # Keressünk olyan mintákat, amik használják ezt a kulcsszót
        for pid, pattern in dka.graph.patterns.items():
            pattern_str = str(pattern)
            clean_keyword = keyword.replace(".", "_")
            if clean_keyword in pattern_str or keyword in pattern_str:
                for tag in tags:
                    dka.semantics.concept_index[tag].add(pid)
                    dka.semantics.pattern_semantics[pid].add(tag)
    
    # Minden NAME_PREFIXES kulcsszó is legyen fogalom
    for prefix, tags in extractor.NAME_PREFIXES.items():
        for pid, pattern in dka.graph.patterns.items():
            pattern_str = str(pattern)
            if prefix in pattern_str.lower():
                for tag in tags:
                    dka.semantics.concept_index[tag].add(pid)
                    dka.semantics.pattern_semantics[pid].add(tag)
    
    stats = dka.stats()
    print(f"\n  Gráf: {stats['total_pie']} PIE, {stats['patterns']} minta, {stats['schemas']} séma")
    print(f"  Szemantikus: {dka.semantics.stats()['total_concepts']} fogalom")
    
    return dka


if __name__ == "__main__":
    print("Alap algoritmusok betanítása...")
    dka = train_alap()
    
    # TESZT: most már tudnia kell a filter, sum, max fogalmakat
    print("\n=== TESZTEK ===")
    for goal in ["sum all numbers", "filter even numbers", "find maximum", 
                  "count occurrences", "reverse list", "contains value"]:
        code = dka.generate(goal=goal)
        if code:
            first_line = code.split('\\n')[0]
            print(f"  '{goal}' → {first_line}")
            try:
                compile(code, '<test>', 'exec')
                print(f"    [OK]")
            except SyntaxError as e:
                print(f"    [HIBA] {e}")
        else:
            print(f"  '{goal}' → (nincs válasz)")
