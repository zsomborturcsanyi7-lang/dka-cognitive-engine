"""Hiányzó minták betanítása + word_counter teszt."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dka import DKA
from struct_compose import ProgramScaffold, SlotFiller, StructuredComposer
from constructive_generator import ConstructiveGenerator

# 1. Graph betöltése
dka = DKA()
dka.load('dka_trained_500.json')
print(f"Betöltve: PIE={dka.stats()['total_pie']}, Patterns={len(dka.graph.patterns)}")

# 2. Hiányzó függvények betanítása
uj_fuggvenyek = {
    "read_file": '''
def read_file(path):
    with open(path, 'r') as f:
        content = f.read()
    return content
''',
    "split_words": '''
def split_words(text):
    return text.split()
''',
    "count_words": '''
def count_words(words):
    counts = {}
    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1
    return counts
''',
    "word_frequency": '''
def word_frequency(path):
    text = open(path).read()
    words = text.split()
    freq = {}
    for w in words:
        if w in freq:
            freq[w] += 1
        else:
            freq[w] = 1
    return freq
''',
    "file_read_text": '''
def file_read_text(path):
    f = open(path, 'r')
    content = f.read()
    f.close()
    return content
''',
    "split_by_whitespace": '''
def split_by_whitespace(text):
    return [w for w in text.split() if w]
''',
}

for name, code in uj_fuggvenyek.items():
    cnt = dka.learn(code, source=name)
    print(f"  [+] {name}: +{cnt} PIE")

# 3. Mentés
dka.save('dka_trained_500.json')
print(f"\nMentve. PIE={dka.stats()['total_pie']}, Patterns={len(dka.graph.patterns)}")

# 4. Word_counter scaffold teszt
print("\n" + "="*50)
print("WORD_COUNTER TESZT")
print("="*50)

filler = SlotFiller(dka.graph, dka.semantics)
gen = ConstructiveGenerator(dka.graph)

scaffold = ProgramScaffold.word_counter()
filled = filler.fill(scaffold, 'count word frequency')
code = gen.generate(filled)
print("Eredmény:")
print(code)
try:
    compile(code, '<test>', 'exec')
    print("  [OK] Valid Python!")
    
    # Ellenőrizzük a tartalmat
    has_open_or_read = 'open(' in code or 'read(' in code or 'with open' in code
    has_split = 'split()' in code or 'split' in code
    has_dict_or_count = '{' in code or 'count' in code
    has_return = 'return ' in code
    
    checks = [
        ("fájl olvasás", has_open_or_read),
        ("szétvágás", has_split),
        ("számlálás", has_dict_or_count),
        ("visszatérés", has_return),
    ]
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    
    all_pass = all(ok for _, ok in checks)
    print(f"\n  Összesen: {'MIND PASS' if all_pass else 'VAN FAIL'}")
except SyntaxError as e:
    print(f"  [HIBA] line {e.lineno}: {e.msg}")

# 5. Teszt: filter even + más alap algoritmusok
print("\n" + "="*50)
print("ALAP ALGORITMUS TESZTEK")
print("="*50)

tesztek = [
    "filter even numbers",
    "sort array",
    "sum all numbers",
    "binary search",
    "is prime",
    "reverse string",
    "word frequency count",
]
for goal in tesztek:
    code = dka.generate(goal=goal)
    if code:
        first = code.split('\\n')[0][:70]
        valid = False
        try:
            compile(code, '<test>', 'exec')
            valid = True
        except SyntaxError:
            pass
        print(f"  {'OK' if valid else 'H'} '{goal}' → {first}")
    else:
        print(f"  -  '{goal}' → (nincs válasz)")
