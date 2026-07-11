"""
DKA V2 — Nagyobb kódbázis betanítása
======================================
Megtanítjuk a DKA-t az asztalon található Python kódokkal.
Cél: lássuk, mit tanul egy valós kódbázisból, mennyire skálázható.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from node_types import NodeType
from dka import DKA


def learn_file(dka, path):
    """Egy Python fájl betanítása, hiba esetén skip."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        if len(code) < 10:
            return 0, "túl rövid"
        count = dka.learn(code, source=path)
        return count, None
    except Exception as e:
        return 0, str(e)[:80]


print("DKA V2 — Nagy kódbázis betanítás")
print("=" * 60)

dka = DKA()

# 1. Forrás: Drug Repurposing src/
src_dirs = [
    "C:/Users/iga/Desktop/AI Drug Repurposing/src/",
    "C:/Users/iga/Desktop/DTK model/dka_poc/",
    "C:/Users/iga/Desktop/DTK model/dka_core/",
]

total_files = 0
total_pie_before = 0
errors = []

for src_dir in src_dirs:
    if not os.path.exists(src_dir):
        print(f"\n[Nem talalhato] {src_dir}")
        continue
    
    print(f"\n[Bejaras] {src_dir}")
    
    files = [f for f in os.listdir(src_dir) if f.endswith('.py') and f != '__init__.py']
    
    for fname in sorted(files):
        fpath = os.path.join(src_dir, fname)
        count, error = learn_file(dka, fpath)
        total_files += 1
        
        if error:
            msg = f"  [ERR] {fname}: {error}"
            print(msg)
            errors.append(msg)
        elif count > 0:
            print(f"  [OK]  {fname}: +{count} PIE")
        else:
            print(f"  [--]  {fname}: 0 PIE (mar minden benne volt)")

# Statisztika
print("\n" + "=" * 60)
print("BETANITAS VEGE")
print("=" * 60)

stats = dka.stats()
print(f"\nFajlok: {total_files}")
print(f"Hibak: {len(errors)}")
print(f"\nOsszes PIE: {stats['total_pie']}")
print(f"  1. reteg (Primitiv):  {stats['primitives']}")
print(f"  2. reteg (Minta):     {stats['patterns']}")
print(f"  3. reteg (Sema):      {stats['schemas']}")

# Minta típusok eloszlása
type_counts = {}
for pattern in dka.graph.patterns.values():
    tname = pattern.type.name
    type_counts[tname] = type_counts.get(tname, 0) + 1

print(f"\nMinta tipusok eloszlasa:")
for tname, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    bar = "#" * min(count, 40)
    print(f"  {tname:20s} {count:4d} {bar}")

# Strukturális mélység
max_depth = max(
    (dka.graph.calculate_depth(pid) for pid in list(dka.graph.patterns.keys())[:500]),
    default=0
)
print(f"\nMax strukturalis melyseg: {max_depth} szint")
print(f"Osszes graf meret: {stats['total_pie']} PIE")

# Minta/primitív arány (tömörítés)
ratio = stats['patterns'] / stats['primitives'] if stats['primitives'] > 0 else 0
print(f"Tomoritesi rata (minta/primitiv): {ratio:.2f}")

# Sémák
if dka.graph.schemas:
    print(f"\nSema nevek:")
    for s in dka.graph.schemas.values():
        print(f"  {s.name} ({len(s.pattern_ids)} minta)")

print()
print("=" * 60)
print("TESZT: ismert minta tipusok felismerese")
print("=" * 60)

# Ellenőrizzük, hogy felismer-e alap mintákat
test_patterns = [
    ("FOR_LOOP", NodeType.FOR_LOOP),
    ("IF_STATEMENT", NodeType.IF_STATEMENT),
    ("WHILE_LOOP", NodeType.WHILE_LOOP),
    ("FUNCTION_DEF", NodeType.FUNCTION_DEF),
    ("CLASS_DEF", NodeType.CLASS_DEF),
    ("ASSIGNMENT", NodeType.ASSIGNMENT),
    ("FUNCTION_CALL", NodeType.FUNCTION_CALL),
    ("RETURN_STMT", NodeType.RETURN_STMT),
    ("IMPORT", NodeType.IMPORT),
    ("BINARY_OP", NodeType.BINARY_OP),
    ("ATTRIBUTE_ACCESS", NodeType.ATTRIBUTE_ACCESS),
    ("BLOCK", NodeType.BLOCK),
]

for name, ntype in test_patterns:
    count = len(dka.graph.find_by_type(ntype))
    status = "OK" if count > 0 else "NINCS"
    print(f"  {name:20s}: {count} db [{status}]")

# Mentés
dka.save("dka_trained.json")
print(f"\nGraf elmentve: dka_trained.json ({stats['total_pie']} PIE)")
