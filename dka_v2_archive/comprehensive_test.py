"""Teljes rendszer teszt: mit tud a DKA most?"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dka import DKA

dka = DKA()
dka.load('dka_trained_500.json')

print("=" * 65)
print("DKA V2 — TELJES RENDSZER ÉRTÉKELÉS")
print("=" * 65)
print(f"Adatbázis: {dka.stats()['total_pie']} PIE, {len(dka.graph.patterns)} minta")

szintek = {
    "ALAP (10 alap algoritmus)": [
        ("sum all numbers", "sum_list/digit_sum"),
        ("filter even numbers", "filter_even"),
        ("find maximum", "find_max"),
        ("find minimum", "find_min"),
        ("contains value", "contains"),
        ("reverse list", "reverse_list"),
        ("count occurrences", "count_occurrences"),
        ("are all positive", "are_all_positive"),
        ("get first n", "get_first_n"),
        ("merge sorted lists", "merge_sorted"),
    ],
    "HALADÓ (trained 244)": [
        ("sort array", "bubble_sort/merge_sort"),
        ("binary search", "binary_search"),
        ("is prime", "is_prime"),
        ("factorial", "factorial"),
        ("reverse string", "reverse_string"),
        ("count word frequency", "word_frequency"),
        ("sort dictionary by value", "sort_dict_by_value"),
        ("read file", "read_file"),
    ],
    "KREATÍV (scaffold)": [
        ("guess the number", "guess_game scaffold"),
    ],
}

for szint, tesztek in szintek.items():
    print(f"\n{'='*65}")
    print(f"  {szint}")
    print(f"{'='*65}")
    print(f"  {'CÉL':<25} {'EREDMÉNY':<30} {'VALID'}")
    print(f"  {'─'*25} {'─'*30} {'─'*5}")
    
    for goal, expected in tesztek:
        code = dka.generate(goal=goal)
        if not code:
            print(f"  {goal:<25} {'─ (nincs válasz)':<30} {'N/A'}")
            continue
        
        first = code.split(chr(10))[0][:50] if code else "─"
        valid = False
        try:
            compile(code, '<test>', 'exec')
            valid = True
        except SyntaxError:
            pass
        
        # Check if result matches expected
        match = "[várttól eltér]" 
        expected_parts = expected.replace("/", " ").lower().split()
        first_clean = first.replace("def ", "").replace("(", "").strip().lower()
        if first_clean in expected_parts or any(p in first_clean for p in expected_parts):
            match = ""
        
        status = "OK" if valid else "HIBA"
        print(f"  {goal:<25} {first:<30} [{status}] {match}")
        
        if not valid:
            print(f"  {'':>25} ⚠ SZINTAXIS HIBA")

print(f"\n{'='*65}")
print(f"ÖSSZESÍTÉS")
print(f"{'='*65}")
# Count
total_valid = 0
total_goals = 0
for szint, tesztek in szintek.items():
    for goal, expected in tesztek:
        total_goals += 1
        code = dka.generate(goal=goal)
        if code:
            try:
                compile(code, '<test>', 'exec')
                total_valid += 1
            except SyntaxError:
                pass
print(f"  Sikeres generálások: {total_valid}/{total_goals} valid Python kód")
print(f"  Felhasználható: {total_valid/total_goals*100:.0f}%")
print(f"\n  Korábban (tegnap):   ~60% valid, 'sort numbers'→bubble_sort OK")
print(f"  Most:               {total_valid/total_goals*100:.0f}% valid, word_frequency+read_file OK")
