"""
DKA V2 — Programozási Benchmark
=================================
Feladatok 5 nehézségi szinten.
Cél: meghatározni, hogy a DKA milyen "modell szinten" van.
"""

import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))

from dka import DKA
from node_types import NodeType
from creative_composer import CreativeComposer


class BenchmarkResult:
    def __init__(self):
        self.tests = []
    
    def add(self, level, name, result, valid, time_s, notes=""):
        self.tests.append({
            "level": level, "name": name,
            "result": result, "valid": valid,
            "time": f"{time_s:.2f}s",
            "notes": notes
        })
    
    def report(self):
        print(f"\n{'='*70}")
        print(f"  DKA V2 — PROGRAMOZÁSI BENCHMARK")
        print(f"{'='*70}")
        
        for level in sorted(set(t["level"] for t in self.tests)):
            level_tests = [t for t in self.tests if t["level"] == level]
            passed = sum(1 for t in level_tests if t["valid"])
            
            print(f"\n  {level}. SZINT ({passed}/{len(level_tests)} pass)")
            print(f"  {'-'*60}")
            
            for t in level_tests:
                icon = "PASS" if t["valid"] else "FAIL"
                print(f"    [{icon}] {t['name']} ({t['time']})")
                if t["notes"]:
                    print(f"          {t['notes']}")
                if t["valid"]:
                    preview = t["result"][:100].replace('\n', ' | ')
                    print(f"          -> {preview}")
        
        self._estimate_level()
    
    def _estimate_level(self):
        print(f"\n{'='*70}")
        print(f"  BECSLÉS: Modell méret ekvivalencia")
        print(f"{'='*70}")
        
        # Pontozás
        points = 0
        for t in self.tests:
            if t["valid"]:
                points += t["level"]
        
        max_possible = sum(t["level"] for t in self.tests)
        pct = points / max_possible * 100 if max_possible > 0 else 0
        
        print(f"\n  Pontszám: {points}/{max_possible} ({pct:.0f}%)")
        print()
        
        # Ekvivalencia tábla
        levels = [
            (0, "1B param", "Alap kód kiegészítés, egyszerű függvények"),
            (20, "3B param", "Ismert algoritmusok, library hívások"),
            (40, "7B param", "Több lépéses függvények, hibakezelés"),
            (60, "13B param", "Komplex algoritmusok, OOP, API design"),
            (80, "70B param", "Kreatív megoldások, optimalizáció"),
            (90, "200B+ param", "Teljes programok, rendszertervezés"),
        ]
        
        for threshold, size, desc in levels:
            if points >= threshold:
                status = "ELÉRVE" if points >= threshold else ""
                bar = "#" * min(threshold // 5, 20) + "." * max(0, 20 - threshold // 5)
                print(f"  {bar} {size:10s} | {desc}")
        
        print(f"\n  Jelenlegi szint: {points} pont")
        print(f"  -> {self._map_to_model(points)}")
    
    def _map_to_model(self, points):
        if points >= 80: return "70B-200B+ (Claude 3.5 Sonnet, GPT-4)"
        if points >= 60: return "13B-70B (CodeLlama 34B, DeepSeek-Coder 33B)"
        if points >= 40: return "7B-13B (CodeLlama 13B, StarCoder 15B)"
        if points >= 20: return "3B-7B (CodeLlama 7B, Phi-3)"
        return "<3B (kis modellek, alap kód)"

# ═════════════════════════════════════════════════════════════════════
# BENCHMARK FELADATOK
# ═════════════════════════════════════════════════════════════════════

def run_benchmark():
    dka = DKA()
    composer = CreativeComposer(dka.graph, dka.generator, dka.semantics)
    results = BenchmarkResult()
    
    # ================================================================
    # 0. SZINT: Tanító adatok (minden teszt ebből dolgozik)
    # ================================================================
    
    training = {
        "bubble_sort": '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
''',
        "factorial": '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
''',
        "read_config": '''
def read_config(path):
    with open(path) as f:
        data = json.load(f)
    return data
''',
        "fetch_user": '''
def fetch_user(user_id):
    import requests
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
''',
        "count_items": '''
def count_items(items):
    count = 0
    for item in items:
        count += 1
    return count
''',
        "check_value": '''
def check_value(x, threshold):
    if x > threshold:
        return True
    return False
''',
    }
    
    for name, code in training.items():
        dka.learn(code, source=name)
    
    print(f"Tanulas kesz. {dka.stats()['total_pie']} PIE, "
          f"{dka.stats()['patterns']} minta, "
          f"{dka.stats()['schemas']} sema")
    
    # ================================================================
    # 1. SZINT: Pontos egyezés (ismert függvények név alapján)
    # ================================================================
    
    print(f"\n{'='*70}")
    print("  1. SZINT: Ismert függvények előhívása")
    print(f"{'='*70}")
    
    level1_tests = [
        ("sort numbers", "sort numbers"),
        ("calculate factorial", "factorial"),
        ("read config file", "read_config"),
        ("fetch user data", "fetch_user"),
        ("count items in list", "count_items"),
        ("check value against threshold", "check_value"),
    ]
    
    for prompt, expected in level1_tests:
        t0 = time.time()
        code = dka.generate(goal=prompt)
        dt = time.time() - t0
        
        valid = False
        notes = ""
        try:
            compile(code, '<test>', 'exec')
            valid = True
        except SyntaxError as e:
            notes = f"SyntaxError: {str(e)[:40]}"
        
        # Ellenőrizzük, hogy a várt függvényt kaptuk-e
        if expected.replace("_", " ") in code[:code.find("(")]:
            pass
        elif expected in code:
            pass
        else:
            if valid:
                notes += " (más függvény)"
        
        results.add(1, f"'{prompt}' -> {expected}", code, valid, dt, notes)
        icon = "OK" if valid else "X"
        print(f"  [{icon}] {prompt}: {dt:.2f}s")
    
    # ================================================================
    # 2. SZINT: Analógia (hasonló, de nem pontosan tanított)
    # ================================================================
    
    print(f"\n{'='*70}")
    print("  2. SZINT: Analógia alapú feladatok")
    print(f"{'='*70}")
    
    level2_tests = [
        ("sort strings", "sort strings alphabetically"),
        ("calculate fibonacci", "fibonacci number"),
        ("read json file", "read json from file"),
        ("api get request", "make api get call"),
    ]
    
    for prompt, desc in level2_tests:
        t0 = time.time()
        code = dka.generate(goal=prompt)
        dt = time.time() - t0
        
        valid = False
        try:
            compile(code, '<test>', 'exec')
            valid = True
        except SyntaxError:
            pass
        
        # Van-e benne function def?
        has_func = "def " in code
        notes = ""
        if not has_func:
            notes = "nincs fuggvenydef"
        
        results.add(2, f"'{prompt}'", code, valid and has_func, dt, notes)
        icon = "OK" if valid and has_func else "~" if has_func else "X"
        print(f"  [{icon}] {prompt}: {dt:.2f}s")
    
    # ================================================================
    # 3. SZINT: Kombináció (két ismert minta összeolvasztása)
    # ================================================================
    
    print(f"\n{'='*70}")
    print("  3. SZINT: Kreatív kombináció")
    print(f"{'='*70}")
    
    level3_tests = [
        # Template + content kombinációk
        ("loop and check", 
         lambda: composer._merge_into_template(
             dka.graph.find_by_type(NodeType.FOR_LOOP)[0],
             dka.graph.find_by_type(NodeType.IF_STATEMENT)[:1],
             "loop with check")),
        ("sort and return",
         lambda: composer._merge_into_template(
             dka.graph.find_by_type(NodeType.FUNCTION_DEF)[0],
             dka.graph.find_by_type(NodeType.RETURN_STMT)[:1],
             "function with return")),
    ]
    
    for name, fn in level3_tests:
        t0 = time.time()
        try:
            code = fn()
            dt = time.time() - t0
            valid = False
            try:
                compile(code, '<test>', 'exec')
                valid = True
            except SyntaxError as e:
                pass
            results.add(3, name, code or "", valid, dt)
            icon = "OK" if valid else "X"
            print(f"  [{icon}] {name}: {dt:.2f}s")
        except Exception as e:
            results.add(3, name, "", False, time.time()-t0, str(e)[:40])
            print(f"  [X] {name}: HIBA")
    
    # ================================================================
    # 4. SZINT: Több lépéses kreatív kompozíció
    # ================================================================
    
    print(f"\n{'='*70}")
    print("  4. SZINT: Kreatív kompozíció (creative_synthesize)")
    print(f"{'='*70}")
    
    level4_tests = [
        "loop and count",
        "check each item",
        "read and return",
    ]
    
    for prompt in level4_tests:
        t0 = time.time()
        code = composer.creative_synthesize(prompt)
        dt = time.time() - t0
        
        valid = False
        notes = ""
        if code:
            try:
                compile(code, '<test>', 'exec')
                valid = True
            except SyntaxError as e:
                notes = str(e)[:40]
        else:
            notes = "nincs valasz"
        
        results.add(4, f"'{prompt}'", code or "", valid, dt, notes)
        icon = "OK" if valid else "X"
        print(f"  [{icon}] {prompt}: {dt:.2f}s")
    
    # ================================================================
    # 5. SZINT: Teljesen új probléma (nincs közvetlen minta)
    # ================================================================
    
    print(f"\n{'='*70}")
    print("  5. SZINT: Teljesen új probléma")
    print(f"{'='*70}")
    
    level5_tests = [
        ("sum all numbers in list", "sum of list elements"),
        ("find maximum value", "find max in array"),
        ("filter even numbers", "keep only even numbers"),
        ("count occurrences", "count word frequency"),
    ]
    
    for prompt, desc in level5_tests:
        t0 = time.time()
        code = dka.generate(goal=prompt)
        dt = time.time() - t0
        
        valid = False
        notes = ""
        if code:
            try:
                compile(code, '<test>', 'exec')
                valid = True
            except SyntaxError as e:
                notes = str(e)[:40]
        else:
            notes = "ures"
        
        results.add(5, f"'{prompt}'", code or "", valid, dt, notes)
        icon = "OK" if valid else "X"
        print(f"  [{icon}] {prompt}: {dt:.2f}s")
    
    # ================================================================
    # Eredmény
    # ================================================================
    
    results.report()
    return results


if __name__ == "__main__":
    run_benchmark()
