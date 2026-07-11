"""
DKA V2 — Gyorsított batch tanítás időkorláttal
"""

import sys, os, signal, json
sys.path.insert(0, os.path.dirname(__file__))

from dka import DKA
from node_types import NodeType


def learn_file_safe(dka, path):
    """Egy fájl betanítása timeout-al."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        if len(code) < 10:
            return 0, "too short"
        count = dka.learn(code, source=path)
        return count, None
    except SyntaxError as e:
        return 0, f"SYNTAX: {e.msg[:60]}"
    except Exception as e:
        return 0, str(e)[:80]


dka = DKA()

src_dirs = {
    "drug_repurposing": "C:/Users/iga/Desktop/AI Drug Repurposing/src/",
    "dka_poc": "C:/Users/iga/Desktop/DTK model/dka_poc/",
    "dka_core": "C:/Users/iga/Desktop/DTK model/dka_core/",
}

total_files = 0
total_ok = 0
total_pie = 0
errors = []

for label, src_dir in src_dirs.items():
    if not os.path.exists(src_dir):
        print(f"[SKIP] {label}")
        continue
    
    files = sorted([f for f in os.listdir(src_dir) if f.endswith('.py') and f != '__init__.py'])
    print(f"\n=== {label} ({len(files)} file) ===")
    
    for fname in files:
        fpath = os.path.join(src_dir, fname)
        count, error = learn_file_safe(dka, fpath)
        total_files += 1
        
        if error:
            print(f"  [--] {fname}")
            errors.append(f"{fname}: {error}")
        elif count > 0:
            total_ok += 1
            total_pie += count
            print(f"  [+] {fname} (+{count})")
        else:
            total_ok += 1
            print(f"  [=] {fname} (0 new)")

# VÉGLEGES STATISZTIKA
print(f"\n{'='*60}")
print("VEGLEGES STATISZTIKA")
print(f"{'='*60}")

stats = dka.stats()

print(f"\nFajlok: {total_files} (+{total_ok} OK, {len(errors)} skip)")
print(f"Osszes PIE: {stats['total_pie']}")
print(f"  1. reteg (Primitiv):  {stats['primitives']}")
print(f"  2. reteg (Minta):     {stats['patterns']}")
print(f"  3. reteg (Sema):      {stats['schemas']}")

# Top 20 minta típus
type_counts = {}
for p in dka.graph.patterns.values():
    tname = p.type.name
    type_counts[tname] = type_counts.get(tname, 0) + 1

print(f"\nTop 15 minta tipus:")
for tname, count in sorted(type_counts.items(), key=lambda x: -x[1])[:15]:
    bar = "#" * min(count // 2, 30)
    print(f"  {tname:20s} {count:4d} {bar}")

# Strukturális mélység
depths = [dka.graph.calculate_depth(pid) for pid in list(dka.graph.patterns.keys())[:500]]
max_depth = max(depths) if depths else 0
avg_depth = sum(depths) / len(depths) if depths else 0
print(f"\nMax melyseg: {max_depth} szint")
print(f"Atlags melyseg: {avg_depth:.1f} szint")

# SRT: mennyire járható be a gráf
print(f"\nOsszefuggesek:")
print(f"  Primitive id-k: {len(dka.graph.primitives)}")
print(f"  Pattern id-k: {len(dka.graph.patterns)}")
print(f"  Fingerprint-ek: {stats['fingerprints']}")
print(f"  Forrasok: {stats['sources']}")

# Minta/primitív arány
ratio = stats['patterns'] / stats['primitives'] if stats['primitives'] > 0 else 0
print(f"  Tomorites: {ratio:.2f} (minel magasabb, annal jobb)")

# Skip-elt fájlok
if errors:
    print(f"\nSkip-elt fajlok ({len(errors)}):")
    for e in errors[:10]:
        print(f"  {e}")

# Mentés
save_path = "dka_big_model.json"
dka.save(save_path)
file_size = os.path.getsize(save_path) / 1024
print(f"\nGraf elmentve: {save_path} ({file_size:.1f} KB, {stats['total_pie']} PIE)")
print(f"\nKesz. A DKA most {stats['total_pie']} PIE-t tud.")
