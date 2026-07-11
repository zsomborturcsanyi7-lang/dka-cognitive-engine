"""
DKA V3 — 300 FELADATOS ÖNTANULÁSI TESZT
=========================================
A DKA 300 feladatot kap. Minden sikeres generálásból tanul.
Ha 3 egymást követő feladat hibás, megállunk.
"""

import sys, random, time
sys.path.insert(0, r'C:\Users\iga\Desktop\DTK model\dka_v3')

from concept_graph import ConceptGraph
from seed_concepts import seed_basic_concepts
from planner import Planner
from generator import Generator
from self_improver_v2 import SelfImproverV2

random.seed(42)

g = ConceptGraph()
seed_basic_concepts(g)
planner = Planner(g)
gen = Generator(g)
improver = SelfImproverV2(g, planner, gen)

# ===== 300 FELADAT GENERÁLÁSA =====
html_elements = [
    "cimmel", "bekezdessel", "urlappal", "input mezovel",
    "gombbal", "keppel", "tablazattal", "listaval",
    "fejleccel", "menüvel", "linkkel", "stilussal",
]
html_adjectives = ["szep", "gyonyoru", "modern", "teljes", "interaktiv", "reszletes", "gyors"]
html_verbs = ["csinalj", "keszits", "epits"]
html_nouns = ["weblapot", "weboldalt", "oldalt", "honlapot"]

python_actions = [
    "szurd ki a paros szamokat",
    "szurd ki a paratlan szamokat", 
    "rendezd a listat",
    "forditsd meg a listat",
    "szamold meg az elemeket",
    "vedd az elsö harom elemet",
    "keresd meg a legnagyobbat",
    "keresd meg a legkisebbet",
    "szurd ki a pozitiv szamokat",
    "vond ki az atlagot",
]

extra_tasks = [
    "csinalj egy weblapot cimmel",
    "keszits egy urlapot email mezovel",
    "epits egy oldalt fejleccel",
    "csinalj egy weblapot cimmel es gombbal",
    "keszits egy urlapot ket input mezovel",
    "rendezd a listat csokkenobe",
    "csinalj egy weblapot ket gombbal es cimmel",
    "keszits egy weblapot bekezdessel es urlappal",
]

# 300 feladat előállítása
tasks = []

# 100 HTML feladat
for _ in range(100):
    verb = random.choice(html_verbs)
    noun = random.choice(html_nouns)
    
    # Hány elemet adjunk hozzá?
    num_elements = random.randint(0, 4)
    if num_elements == 0:
        task = f"{verb} egy {random.choice(html_adjectives)} {noun}"
    else:
        elements = random.sample(html_elements, min(num_elements, len(html_elements)))
        elem_str = " es ".join(elements)
        task = f"{verb} egy {random.choice(html_adjectives)} {noun} {elem_str}"
    tasks.append((task, "html"))

# 100 Python feladat
for _ in range(100):
    action = random.choice(python_actions)
    tasks.append((action, "python"))

# 50 kevert feladat
for _ in range(50):
    if random.random() < 0.5:
        task = f"{random.choice(html_verbs)} egy {random.choice(html_adjectives)} {random.choice(html_nouns)}"
        tasks.append((task, "html"))
    else:
        task = random.choice(python_actions)
        tasks.append((task, "python"))

# 50 extra
for task in extra_tasks:
    tasks.append((task, "html" if "urlap" in task or "weblap" in task or "oldalt" in task or "weboldalt" in task else "python"))

# Keverés — de az első 20 feladat ismert legyen (hogy legyen mit tanulnia)
known_tasks = [
    ("csinalj egy weblapot", "html"),
    ("csinalj egy weblapot cimmel", "html"),
    ("csinalj egy weblapot urlappal", "html"),
    ("csinalj egy urlapot input mezovel", "html"),
    ("szurd ki a paros szamokat", "python"),
    ("rendezd a listat", "python"),
    ("csinalj egy weblapot gombbal", "html"),
    ("keszits egy weboldalt cimmel es bekezdessel", "html"),
    ("csinalj egy teljes weblapot urlappal", "html"),
    ("keszits egy urlapot ket input mezovel", "html"),
    ("csinalj egy weblapot cimmel es egy gombbal", "html"),
    ("keszits egy weboldalt", "html"),
    ("csinalj egy szep weblapot", "html"),
    ("keszits egy weblapot bekezdessel", "html"),
    ("csinalj egy urlapot gombbal", "html"),
    ("keszits egy weboldalt input mezovel", "html"),
    ("csinalj egy weblapot cimmel es urlappal", "html"),
    ("keszits egy urlapot", "html"),
    ("csinalj egy weblapot ket gombbal", "html"),
    ("rendezd a listat csokkenobe", "python"),
]
# Ismert feladatok az elején
first_batch = known_tasks + tasks[:50]
# A maradékot hozzáfűzzük
remaining = tasks[50:]
random.shuffle(remaining)
tasks = first_batch + remaining

# ===== TESZT FUTTATÁS =====
print("=" * 70)
print("DKA V3 — 300 FELADATOS ÖNTANULÁS")
print("=" * 70)
print(f"Kezdet: {g.stats()['concepts']} fog, {g.stats()['relations']} kapcs, 34 szo→akcio")
print(f"Feladatok: {len(tasks)}")
print("-" * 70)

success = 0
fail = 0
consecutive_fail = 0
start_time = time.time()

# Eredménykövetés
success_history = []
fail_history = []
state_snapshots = []
concept_snapshots = []
pattern_snapshots = []

for i, (goal, lang) in enumerate(tasks, 1):
    plan = planner.plan(goal)
    
    if plan:
        code, log = improver.run(goal, lang)
        if code:
            success += 1
            consecutive_fail = 0
            success_history.append((i, goal, lang))
        else:
            fail += 1
            consecutive_fail += 1
            fail_history.append((i, goal, lang, log[-3:] if log else ""))
    else:
        fail += 1
        consecutive_fail += 1
        fail_history.append((i, goal, lang, ["NINCS TERV"]))
    
    # Állapot rögzítése minden 20. feladatnál
    if i % 20 == 0:
        state_snapshots.append((i, g.stats()['concepts'], g.stats()['relations']))
        pattern_snapshots.append((i, len(planner.parser._task_patterns)))
    
    # Progress report minden 30. feladatnál
    if i % 30 == 0 or i == len(tasks):
        elapsed = time.time() - start_time
        rate = i / elapsed
        print(f"  [{i}/300] Sikeres: {success}, Hiba: {fail}, "
              f"Kapcs: {g.stats()['relations']}, "
              f"Szo→akcio: {len(planner.parser._task_patterns)} "
              f"({rate:.0f} feladat/perc)")
    
    # Leállítás 3 egymást követő hiba után
    if consecutive_fail >= 3:
        print(f"\n  !!! 3 egymást követő hiba. Leállítás a {i}. feladatnál.")
        print(f"  Utolsó 3 hiba:")
        for f in fail_history[-3:]:
            print(f"    \"{f[1][:50]}\"")
        break

# ===== ÖSSZESÍTÉS =====
total = success + fail
elapsed = time.time() - start_time

print()
print("=" * 70)
print("VÉGEREDMÉNY")
print("=" * 70)
print(f"  Feldolgozva: {total}/300 feladat")
print(f"  Sikeres:     {success} ({success/total*100:.0f}%)")
print(f"  Hibás:       {fail} ({fail/total*100:.0f}%)")
print(f"  Idő:         {elapsed:.0f} másodperc")
print(f"  Sebesség:    {total/elapsed:.0f} feladat/perc")
print()
print(f"  TUDÁS NÖVEKEDÉS:")
print(f"    Kapcsolatok:   {state_snapshots[0][2] if state_snapshots else 21} → {g.stats()['relations']}")
print(f"    Szó→akció:     {pattern_snapshots[0][1] if pattern_snapshots else 34} → {len(planner.parser._task_patterns)}")
print(f"    Felfedezések:  {len(improver.discoveries)}")
print(f"    Javítások:     {improver.improvement_count}")
print()
print(f"  ÁLLAPOT SNAPSHOTOK (minden 20. feladat):")
for i, c, r in state_snapshots:
    print(f"    {i}. feladat: {c} fogalom, {r} kapcsolat")
print()
print(f"  HIBA ELEMZÉS:")
if fail_history:
    # Top hibák
    fail_types = {}
    for f in fail_history:
        reason = str(f[3])[:40]
        fail_types[reason] = fail_types.get(reason, 0) + 1
    print(f"    Leggyakoribb hibák:")
    for reason, count in sorted(fail_types.items(), key=lambda x: -x[1])[:5]:
        print(f"      {reason}: {count}x")
else:
    print("    (nincs hiba)")
