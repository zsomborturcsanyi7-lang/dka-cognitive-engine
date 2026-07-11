"""
DKA V2 — Batch training signal.settimeout használatával
"""

import sys, os, signal, json, time
sys.path.insert(0, os.path.dirname(__file__))

from node_types import NodeType, DataDomain
from grammar_parser import GrammarParser
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from inference_engine_v2 import InferenceEngineV2


class DKA_Batch:
    """Lightweight batch DKA — csak a tanulás, nincs automatikus pattern discovery."""
    def __init__(self):
        self.graph = HypergraphV2()
        self.parser = GrammarParser()
    
    def learn(self, code, source=""):
        old = self.graph.total_pies
        nodes = self.parser.parse(code, domain=DataDomain.GENERAL, source=source)
        self.graph.ingest_pattern_tree(nodes, domain=DataDomain.GENERAL, source=source)
        return self.graph.total_pies - old


dka = DKA_Batch()

src_dirs = {
    "drug_repurposing": "C:/Users/iga/Desktop/AI Drug Repurposing/src/",
    "dka_poc": "C:/Users/iga/Desktop/DTK model/dka_poc/",
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
        total_files += 1
        
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            if len(code) < 10:
                print(f"  [--] {fname} (too short)")
                continue
            
            t0 = time.time()
            count = dka.learn(code, source=fpath)
            dt = time.time() - t0
            
            if count > 0:
                total_ok += 1
                total_pie += count
                print(f"  [+] {fname} (+{count}, {dt:.2f}s)")
            else:
                total_ok += 1
                print(f"  [=] {fname} (0)")
                
        except SyntaxError:
            print(f"  [--] {fname} (syntax)")
            errors.append(f"{fname}: SyntaxError")
        except Exception as e:
            print(f"  [!]  {fname} ({str(e)[:60]})")
            errors.append(f"{fname}: {str(e)[:60]}")

# Pattern discovery egyszer a végén
print(f"\n=== Pattern discovery... ===")
patterns = dka.graph.discover_patterns(min_instances=2)
print(f"  Talalt mintak: {len(patterns)}")

# Séma építés
for p in patterns[:10]:
    schema_name = p['signature'].split('|')[0].lower().replace(":", "_")
    if len(p['pattern_ids']) >= 2:
        dka.graph.build_schema(f"auto_{schema_name}", p['pattern_ids'])

# STATISZTIKA
print(f"\n{'='*60}")
print("VEGLEGES STATISZTIKA")
print(f"{'='*60}")

stats = dka.graph.stats()
print(f"\nFajlok: {total_files} (+{total_ok} OK, {len(errors)} skip)")
print(f"Osszes PIE: {stats['total_pie']}")
print(f"  Primitiv: {stats['primitives']}")
print(f"  Minta:    {stats['patterns']}")
print(f"  Sema:     {stats['schemas']}")

# Top 15 minta típus
tc = {}
for p in dka.graph.patterns.values():
    tc[p.type.name] = tc.get(p.type.name, 0) + 1
print(f"\nTop 15:")
for t, c in sorted(tc.items(), key=lambda x: -x[1])[:15]:
    print(f"  {t:20s} {c:4d}")

# Mélység
depths = [dka.graph.calculate_depth(pid) for pid in list(dka.graph.patterns.keys())[:500]]
if depths:
    print(f"\nMax melyseg: {max(depths)} szint")
    print(f"Atlag: {sum(depths)/len(depths):.1f}")

ratio = stats['patterns'] / max(stats['primitives'], 1)
print(f"Tomorites: {ratio:.2f}")

# Mentés
save_path = "dka_big_model.json"
dka.graph.to_json_file(save_path)
fsize = os.path.getsize(save_path) / 1024
print(f"\nElmentve: {save_path} ({fsize:.1f} KB)")
print(f"Kesz! A DKA most {stats['total_pie']} PIE-t tud.")
