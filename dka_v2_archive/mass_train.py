"""
DKA V2 — Tömeges mintagenerálás
=================================
400-500 Python függvény generálása sablonokból.
Cél: a DKA szemantikus indexének és mintakönyvtárának feltöltése.
"""

import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))

random.seed(42)

# ─── ALGORITMUS SABLONOK ───────────────────────────────────────────

# Minden sablon: (name_template, code_template)
# A {} helyére változónevek kerülnek

ALGORITHMS = []

# 1. RENDEZÉSEK (5)
SORTING = [
    ("bubble_sort_{}", '''
def {}(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''),
    ("selection_sort_{}", '''
def {}(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
'''),
    ("insertion_sort_{}", '''
def {}(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr
'''),
    ("merge_sort_{}", '''
def {}(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = {}(arr[:mid])
    right = {}(arr[mid:])
    return merge(left, right)
'''),
    ("quick_sort_{}", '''
def {}(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    less = [x for x in arr[1:] if x <= pivot]
    greater = [x for x in arr[1:] if x > pivot]
    return {}(less) + [pivot] + {}(greater)
'''),
]

# 2. KERESÉSEK (5)
SEARCHING = [
    ("linear_search_{}", '''
def {}(items, target):
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1
'''),
    ("binary_search_{}", '''
def {}(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
'''),
    ("find_all_{}", '''
def {}(items, target):
    result = []
    for i, item in enumerate(items):
        if item == target:
            result.append(i)
    return result
'''),
    ("first_occurrence_{}", '''
def {}(items, target):
    for item in items:
        if item == target:
            return item
    return None
'''),
    ("last_occurrence_{}", '''
def {}(items, target):
    result = None
    for item in items:
        if item == target:
            result = item
    return result
'''),
]

# 3. SZÁMELMÉLET (5)
MATH = [
    ("is_prime_{}", '''
def {}(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
'''),
    ("factorial_{}", '''
def {}(n):
    if n <= 1:
        return 1
    return n * {}(n - 1)
'''),
    ("fibonacci_{}", '''
def {}(n):
    if n <= 1:
        return n
    return {}(n - 1) + {}(n - 2)
'''),
    ("gcd_{}", '''
def {}(a, b):
    while b:
        a, b = b, a % b
    return a
'''),
    ("lcm_{}", '''
def {}(a, b):
    return a * b // {}(a, b)
'''),
]

# 4. SZÖVEGKEZELÉS (5)
STRING = [
    ("reverse_string_{}", '''
def {}(s):
    return s[::-1]
'''),
    ("is_palindrome_{}", '''
def {}(s):
    return s == s[::-1]
'''),
    ("count_vowels_{}", '''
def {}(s):
    vowels = 'aeiouAEIOU'
    count = 0
    for ch in s:
        if ch in vowels:
            count += 1
    return count
'''),
    ("to_uppercase_{}", '''
def {}(s):
    result = ''
    for ch in s:
        if 'a' <= ch <= 'z':
            result += chr(ord(ch) - 32)
        else:
            result += ch
    return result
'''),
    ("word_count_{}", '''
def {}(text):
    count = 0
    in_word = False
    for ch in text:
        if ch != ' ' and not in_word:
            count += 1
            in_word = True
        elif ch == ' ':
            in_word = False
    return count
'''),
]

# 5. LISTA MŰVELETEK (10)
LIST_OPS = [
    ("sum_list_{}", '''def {}(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total\n'''),
    ("average_{}", '''def {}(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)\n'''),
    ("max_value_{}", '''def {}(numbers):\n    if not numbers:\n        return None\n    max_val = numbers[0]\n    for num in numbers:\n        if num > max_val:\n            max_val = num\n    return max_val\n'''),
    ("min_value_{}", '''def {}(numbers):\n    if not numbers:\n        return None\n    min_val = numbers[0]\n    for num in numbers:\n        if num < min_val:\n            min_val = num\n    return min_val\n'''),
    ("filter_even_{}", '''def {}(numbers):\n    result = []\n    for num in numbers:\n        if num % 2 == 0:\n            result.append(num)\n    return result\n'''),
    ("filter_odd_{}", '''def {}(numbers):\n    result = []\n    for num in numbers:\n        if num % 2 != 0:\n            result.append(num)\n    return result\n'''),
    ("contains_{}", '''def {}(items, target):\n    for item in items:\n        if item == target:\n            return True\n    return False\n'''),
    ("count_occurrences_{}", '''def {}(items, target):\n    count = 0\n    for item in items:\n        if item == target:\n            count += 1\n    return count\n'''),
    ("remove_duplicates_{}", '''def {}(items):\n    seen = []\n    for item in items:\n        if item not in seen:\n            seen.append(item)\n    return seen\n'''),
    ("reverse_list_{}", '''def {}(items):\n    return items[::-1]\n'''),
]

# 6. ADAT STRUKTÚRÁK (10)
DATA_STRUCT = [
    ("stack_push_{}", '''def {}(stack, item):\n    stack.append(item)\n    return stack\n'''),
    ("stack_pop_{}", '''def {}(stack):\n    if not stack:\n        return None\n    return stack.pop()\n'''),
    ("queue_enqueue_{}", '''def {}(queue, item):\n    queue.append(item)\n    return queue\n'''),
    ("queue_dequeue_{}", '''def {}(queue):\n    if not queue:\n        return None\n    return queue.pop(0)\n'''),
    ("linked_list_node_{}", '''
class {}:
    def __init__(self, data):
        self.data = data
        self.next = None
'''),
    ("linked_list_append_{}", '''
def {}(head, data):
    if not head:
        return {}(data)
    current = head
    while current.next:
        current = current.next
    current.next = {}(data)
    return head
'''),
    ("linked_list_find_{}", '''
def {}(head, target):
    current = head
    while current:
        if current.data == target:
            return current
        current = current.next
    return None
'''),
    ("tree_node_{}", '''
class {}:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
'''),
    ("tree_insert_{}", '''
def {}(root, value):
    if not root:
        return {}(value)
    if value < root.value:
        root.left = {}(root.left, value)
    else:
        root.right = {}(root.right, value)
    return root
'''),
    ("tree_inorder_{}", '''
def {}(root, result=None):
    if result is None:
        result = []
    if root:
        {}(root.left, result)
        result.append(root.value)
        {}(root.right, result)
    return result
'''),
]

# 7. FÁJL MŰVELETEK (5)
FILE_OPS = [
    ("read_file_{}", '''
def {}(path):
    with open(path, 'r') as f:
        return f.read()
'''),
    ("write_file_{}", '''
def {}(path, content):
    with open(path, 'w') as f:
        f.write(content)
    return True
'''),
    ("read_lines_{}", '''
def {}(path):
    with open(path, 'r') as f:
        return [line.rstrip('\\n') for line in f]
'''),
    ("copy_file_{}", '''
def {}(src, dst):
    with open(src, 'r') as f:
        data = f.read()
    with open(dst, 'w') as f:
        f.write(data)
    return True
'''),
    ("file_size_{}", '''
def {}(path):
    with open(path, 'r') as f:
        content = f.read()
    return len(content)
'''),
]

# 8. API/JSON (5)
API = [
    ("fetch_json_{}", '''
def {}(url):
    import json
    import urllib.request
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())
'''),
    ("post_json_{}", '''
def {}(url, data):
    import json
    import urllib.request
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, 
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())
'''),
    ("parse_json_{}", '''
def {}(text):
    import json
    return json.loads(text)
'''),
    ("to_json_{}", '''
def {}(data):
    import json
    return json.dumps(data, indent=2)
'''),
    ("http_status_{}", '''
def {}(url):
    import urllib.request
    try:
        with urllib.request.urlopen(url) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code
'''),
]

# 9. JÁTÉKOK (5)
GAMES = [
    ("guess_number_{}", '''
def {}():
    import random
    target = random.randint(1, 100)
    attempts = 0
    while True:
        guess = int(input("Tipp: "))
        attempts += 1
        if guess == target:
            return attempts
        elif guess < target:
            print("Nagyobb")
        else:
            print("Kisebb")
'''),
    ("rock_paper_{}", '''
def {}(choice):
    import random
    options = ['rock', 'paper', 'scissors']
    computer = random.choice(options)
    if choice == computer:
        return 'draw'
    if (choice == 'rock' and computer == 'scissors') or \\
       (choice == 'paper' and computer == 'rock') or \\
       (choice == 'scissors' and computer == 'paper'):
        return 'win'
    return 'lose'
'''),
    ("dice_roll_{}", '''
def {}():
    import random
    return random.randint(1, 6)
'''),
    ("shuffle_list_{}", '''
def {}(items):
    import random
    result = items[:]
    for i in range(len(result) - 1, 0, -1):
        j = random.randint(0, i)
        result[i], result[j] = result[j], result[i]
    return result
'''),
    ("random_choice_{}", '''
def {}(items):
    import random
    if not items:
        return None
    return random.choice(items)
'''),
]

# 10. HIBAKEZELÉS (5)
ERROR = [
    ("safe_divide_{}", '''
def {}(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return None
'''),
    ("safe_int_{}", '''
def {}(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None
'''),
    ("retry_{}", '''
def {}(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception:
            if attempt == max_attempts - 1:
                raise
    return None
'''),
    ("validate_email_{}", '''
def {}(email):
    if '@' not in email:
        return False
    local, domain = email.split('@')
    if not local or not domain:
        return False
    if '.' not in domain:
        return False
    return True
'''),
    ("ensure_directory_{}", '''
def {}(path):
    import os
    os.makedirs(path, exist_ok=True)
    return path
'''),
]

# Összes kategória
ALL_CATEGORIES = [
    ("sorting", SORTING),
    ("searching", SEARCHING),
    ("math", MATH),
    ("string", STRING),
    ("list_ops", LIST_OPS),
    ("data_struct", DATA_STRUCT),
    ("file_ops", FILE_OPS),
    ("api", API),
    ("games", GAMES),
    ("error", ERROR),
]


def generate_code(n_variations=5):
    """
    400-500 program generálása.
    Minden sablonhoz n_variations változat különböző névvel.
    """
    all_code = []
    seen = set()
    
    for category_name, templates in ALL_CATEGORIES:
        for name_template, code_template in templates:
            for i in range(n_variations):
                # Különböző nevek generálása
                suffixes = ["", "_v2", "_alt", "_fast", "_simple"]
                suffix = suffixes[i % len(suffixes)]
                
                func_name = name_template.format(f"variety_{i}")
                if suffix:
                    func_name = name_template.format(f"variety_{i}{suffix}")
                
                # Ha a sablon önhivatkozó (rekurzív), cseréljük a nevet
                code = code_template.replace("{}", func_name)
                
                # Duplikáció szűrés
                code_hash = code.strip()[:100]
                if code_hash in seen:
                    continue
                seen.add(code_hash)
                
                all_code.append((func_name, code))
    
    return all_code


def train_dka(dka, all_code):
    """DKA betanítása a generált kódokkal."""
    trained = 0
    errors = 0
    
    for name, code in all_code:
        try:
            count = dka.learn(code, source=name)
            if count > 0:
                trained += 1
        except Exception:
            errors += 1
    
    stats = dka.stats()
    sem_stats = dka.semantics.stats()
    
    return {
        "trained": trained,
        "errors": errors,
        "total_pie": stats["total_pie"],
        "patterns": stats["patterns"],
        "schemas": stats["schemas"],
        "concepts": sem_stats["total_concepts"],
    }


if __name__ == "__main__":
    from dka import DKA
    
    print("Kódok generálása...")
    all_code = generate_code(n_variations=5)
    print(f"  Generálva: {len(all_code)} függvény")
    
    print("\nDKA betanítása...")
    dka = DKA()
    result = train_dka(dka, all_code)
    
    print(f"\n=== EREDMÉNY ===")
    print(f"  Betanult: {result['trained']} függvény")
    print(f"  Hiba: {result['errors']}")
    print(f"  PIE: {result['total_pie']}")
    print(f"  Minta: {result['patterns']}")
    print(f"  Séma: {result['schemas']}")
    print(f"  Fogalom: {result['concepts']}")
    
    # Mentés
    dka.save("dka_trained_500.json")
    print(f"\n  Elmentve: dka_trained_500.json")
    
    # Tesztek
    print("\n=== TESZTEK ===")
    tests = [
        "sort array", "find item", "is prime", "reverse text",
        "count words", "sum numbers", "filter even", "read file",
        "guess number", "safe divide", "validate email",
    ]
    for goal in tests:
        code = dka.generate(goal=goal)
        if code:
            first = code.split('\\n')[0][:60]
            valid = False
            try:
                compile(code, '<test>', 'exec')
                valid = True
            except:
                pass
            print(f"  [{'OK' if valid else 'X'}] {goal:20s} → {first}")
        else:
            print(f"  [--] {goal:20s} → (nincs)")
