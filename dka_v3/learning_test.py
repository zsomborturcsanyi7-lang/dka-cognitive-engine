"""
DKA V3 — Önálló tanulási teszt
================================
A DKA kap egy feladatsort, és minden egyes sikeres generálásból
tanul. Mi utána NEM adunk hozzá semmit — csak a saját tanulására
hagyatkozunk.

Mérés:
- Hány új szabályt fedez fel magától?
- Hány új feladatot tud megoldani a tanultak alapján?
- Mennyivel nő a tudása 10 feladat után?
"""

import sys
sys.path.insert(0, r'C:\Users\iga\Desktop\DTK model\dka_v3')

from concept_graph import ConceptGraph
from seed_concepts import seed_basic_concepts
from planner import Planner
from generator import Generator
from self_improver_v2 import SelfImproverV2

# ===== 1. KEZDETI ÁLLAPOT =====
g = ConceptGraph()
seed_basic_concepts(g)
planner = Planner(g)
gen = Generator(g)
improver = SelfImproverV2(g, planner, gen)

def state():
    s = g.stats()
    discoveries = len(improver.discoveries)
    patterns = len(planner.parser._task_patterns)
    return f"{s['concepts']} fog, {s['relations']} kapcs, {discoveries} felfedezes, {patterns} szo→akcio"

def test(goal, nyelv="html", check_plan=True):
    """Egy feladat: generálás + tanulás"""
    plan = planner.plan(goal)
    if not plan:
        return (False, "NINCS TERV", "")
    
    # SelfImprover futtatás (generál + tanul)
    code, log = improver.run(goal, nyelv)
    
    if code:
        # Tanulás a sikerből
        new_learnings = len([d for d in improver.discoveries if "[TANULÁS]" in d])
        return (True, f"{len(code)} char, {new_learnings} tanulas", code)
    else:
        return (False, "NEM SIKERULT", "")

print("=" * 70)
print("DKA V3 — ÖNÁLLÓ TANULÁS TESZT")
print("=" * 70)
print(f"Kezdeti állapot: {state()}")
print("-" * 70)

# Feladatsor — egyre nehezebb feladatok
tasks = [
    # 1-2: Alap HTML
    ("csinalj egy weblapot", "html"),
    ("csinalj egy weblapot cimmel es bekezdessel", "html"),
    
    # 3-4: HTML + form
    ("csinalj egy urlapot input mezovel", "html"),
    ("csinalj egy weblapot urlappal es egy gombbal", "html"),
    
    # 5: Python váltás
    ("szurd ki a paros szamokat", "python"),
    
    # 6-7: Bonyolultabb HTML
    ("csinalj egy teljes weblapot cimmel es bekezdessel es urlappal", "html"),
    ("keszits egy weblapot ket gombbal", "html"),
    
    # 8-9: Kombinációk
    ("csinalj egy szep weblapot cimmel", "html"),
    ("keszits egy weboldalt urlappal es input mezokkel", "html"),
]

results = []
uj_tanulas_count = 0

for i, (goal, nyelv) in enumerate(tasks, 1):
    siker, msg, code = test(goal, nyelv)
    uj = len([d for d in improver.discoveries if "[TANULÁS]" in d])
    uj_tanulas_count = uj
    results.append((i, siker, goal[:45], msg[:30]))
    status = "OK" if siker else "FAIL"
    print(f"  [{status}] {i}. \"{goal[:40]}...\"")
    print(f"         {msg}")

print("-" * 70)
print(f"Végső állapot: {state()}")
print("-" * 70)

# TESZT: ÚJ feladatok, amiket még NEM látott
print("\n=== TESZT: TELJESEN ÚJ FELADATOK (nem volt a tanító adatban) ===")
print()

new_tasks = [
    ("keszits egy weboldalt egy tablazattal", "html", "új: táblázat"),
    ("csinálj egy weblapot egy képpel", "html", "új: kép"),
    ("rendezd a listat csokkenö sorrendbe", "python", "új: rendezés"),
    ("keszits egy urlapot email es jelszo mezovel", "html", "új: specifikus mezők"),
    ("csinalj egy oldalt fejleccel es labfejleccel", "html", "új: fejléc/lábléc"),
]

for goal, nyelv, leiras in new_tasks:
    plan = planner.plan(goal)
    if plan:
        actions = [s.action for s in plan.steps]
        temp = f"Terv: {', '.join(actions)}"
    else:
        temp = "NINCS TERV"
    
    code, log = improver.run(goal, nyelv)
    siker = code is not None
    status = "OK" if siker else "FAIL"
    print(f"  [{status}] {leiras}")
    print(f"         \"{goal}\"")
    print(f"         {temp}")
    if siker:
        print(f"         {len(code)} char kód generálva")
    print()

print("=" * 70)
print("ÖSSZESÍTÉS")
print("=" * 70)
print(f"  Feladatok: {len(tasks)}")
print(f"  Sikeres: {sum(1 for r in results if r[1])}")
print(f"  Új tanulások: {uj_tanulas_count}")
print(f"  Graph: {g.stats()['concepts']} fogalom, {g.stats()['relations']} kapcsolat")
