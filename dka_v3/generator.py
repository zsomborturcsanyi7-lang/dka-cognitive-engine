"""
DKA V3 — Generator
==================
A tervből (Plan) kódot generál. Több nyelvet támogat:
Python, HTML, JavaScript, CSS.

A Generator nem használ előre gyártott sablonokat. Minden
kimenetet a fogalmakból vezet le:
  - "lista" → IS_A "gyűjtemény" → Python: [], JS: [], HTML: ul/ol
  - "szűrés" → REQUIRES "feltétel" → Python: if x condition, JS: .filter()
  - "űrlap" → PART_OF "weblap" → HTML: <form>

MOST: 80+ komplex template, CSS dialektus, inferált fogalom támogatás.
"""

from __future__ import annotations
import random as _random
from typing import Optional
from concept_graph import ConceptGraph, RelationType
from planner import Plan, PlanStep


class LanguageDialect:
    """Egy programozási nyelv "dialektusa" — hogyan képezzük le
    az absztrakt fogalmakat a nyelv szintaxisára."""

    def __init__(self, name: str):
        self.name = name
        self._mappings: dict[str, str] = {}
        self._imports: dict[str, str] = {}

    def map(self, concept: str, template: str, imports: str = ""):
        self._mappings[concept] = template
        if imports:
            self._imports[concept] = imports

    def get_template(self, concept: str) -> Optional[str]:
        return self._mappings.get(concept)

    def get_import(self, concept: str) -> str:
        return self._imports.get(concept, "")


# ======================================================================
# PYTHON DIALECT — Komplex template-ekkel
# ======================================================================

class PythonDialect(LanguageDialect):
    """Python nyelv — alap + haladó template-ek."""

    def __init__(self):
        super().__init__("python")
        # ===== ALAP =====
        self.map("gyűjtemény", "[]")
        self.map("szótár", "{}")
        self.map("szöveg", "\"\"")
        self.map("bejárás", "for {item} in {collection}:")
        self.map("szűrés", "[{item} for {item} in {collection} if {condition}]")
        self.map("rendezés", "sorted({collection})")
        self.map("transzformáció", "[{func}({item}) for {item} in {collection}]")
        self.map("összegzés", "sum({collection})")
        self.map("függvény", "def {name}({params}):\n    {body}")
        self.map("feltétel", "if {condition}:\n    {body}")
        self.map("visszatérés", "return {value}")
        self.map("kiírás", "print({value})")
        self.map("bekérés", "input({prompt})")

        # ===== HALADÓ ADATMŰVELETEK =====
        self.map("minimum", "min({collection})")
        self.map("maximum", "max({collection})")
        self.map("átlag", "sum({collection}) / len({collection})")
        self.map("fordítás", "list(reversed({collection}))")
        self.map("megszámlálás", "len([x for x in {collection} if {condition}])")
        self.map("első", "{collection}[:{n}]")
        self.map("utolsó", "{collection}[-{n}:]")
        self.map("egyedi", "set({collection})")
        self.map("csoportosítás", "dict(zip({keys}, {values}))")
        self.map("halmaz", "set()")
        self.map("sor", "collections.deque()", "import collections")
        self.map("verem", "[]")
        self.map("gráf", "defaultdict(list)", "from collections import defaultdict")

        # ===== OSZTÁLYOK =====
        self.map("osztály", "class {name}:\n    {body}")
        self.map("konstruktor", "def __init__(self, {params}):\n        pass")
        self.map("metódus", "def {name}(self, {params}):\n    {body}")
        self.map("tulajdonság", "self.{name} = {value}")
        self.map("statikus_metódus", "@staticmethod\ndef {name}({params}):")
        self.map("osztály_metódus", "@classmethod\ndef {name}(cls, {params}):")
        self.map("property_getter", "@property\ndef {name}(self):")
        self.map("property_setter", "@{name}.setter\ndef {name}(self, value):")
        self.map("str_method", "def __str__(self):\n    return {value}")
        self.map("repr_method", "def __repr__(self):\n    return {value}")
        self.map("len_method", "def __len__(self):\n    return {value}")
        self.map("eq_method", "def __eq__(self, other):\n    return {condition}")
        self.map("iter_method", "def __iter__(self):\n    return iter({collection})")
        self.map("adat_osztály", "@dataclass\nclass {name}:", "from dataclasses import dataclass")
        self.map("enum_osztály", "class {name}(Enum):", "from enum import Enum")

        # ===== HIBAKEZELÉS =====
        self.map("try_catch", "try:")
        self.map("kivétel", "except {error} as e:")
        self.map("else_block", "else:")
        self.map("finally_block", "finally:")
        self.map("hiba_dobás", "raise {error}(\"{message}\")")
        self.map("saját_kivétel", "class {name}(Exception):\n    pass")

        # ===== FÁJL MŰVELETEK =====
        self.map("fájl_olvas", "open({path}).read()")
        self.map("fájl_nyit", "with open({path}, '{mode}') as {var}:")
        self.map("fájl_írás", "open({path}, 'w').write({content})")
        self.map("fájl_másolás", "shutil.copy({src}, {dst})", "import shutil")
        self.map("fájl_mozgatás", "shutil.move({src}, {dst})", "import shutil")
        self.map("fájl_törlés", "os.remove({path})", "import os")
        self.map("mappa_létrehozás", "os.makedirs({path}, exist_ok=True)", "import os")
        self.map("mappa_lista", "os.listdir({path})", "import os")
        self.map("csv_olvasás", "csv.DictReader(open({path}))", "import csv")
        self.map("csv_írás", "csv.writer(open({path}, 'w', newline=''))", "import csv")
        self.map("json_olvasás", "json.load(open({path}))", "import json")
        self.map("json_írás", "json.dump({data}, open({path}, 'w'), indent=2)", "import json")

        # ===== LIST COMPREHENSION =====
        self.map("list_comprehension", "[{expression} for {item} in {collection}]")
        self.map("dict_comprehension", "{{{key}: {value} for {item} in {collection}}}")
        self.map("set_comprehension", "{{{expression} for {item} in {collection}}}")
        self.map("szűrő_comprehension", "[{item} for {item} in {collection} if {condition}]")

        # ===== DEKORÁTOROK =====
        self.map("dekorátor", "def {name}(func):\n    def wrapper({params}):\n        {body}\n    return wrapper")
        self.map("időzítő", "import time\n\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f\"{func.__name__} took {time.time()-start:.2f}s\")\n        return result\n    return wrapper")
        self.map("cache", "from functools import lru_cache\n\n@lru_cache(maxsize={size})\ndef {name}({params}):")

        # ===== GENERÁTOR =====
        self.map("generátor", "def {name}({params}):\n    for {item} in {collection}:\n        yield {item}")
        self.map("generátor_kifejezés", "({expression} for {item} in {collection})")
        self.map("yield_from", "yield from {collection}")

        # ===== KONTEKSTUS KEZELŐ =====
        self.map("kontextus_kezelő", "from contextlib import contextmanager\n\n@contextmanager\ndef {name}({params}):\n    try:\n        yield\n    finally:\n        {cleanup}")
        self.map("context_manager", "from contextlib import contextmanager\n\n@contextmanager\ndef {name}({params}):\n    try:\n        yield\n    finally:\n        {cleanup}")

        # ===== LAMBDA =====
        self.map("lambda", "lambda {params}: {expression}")
        self.map("map_kifejezés", "map(lambda {item}: {expression}, {collection})")
        self.map("filter_kifejezés", "filter(lambda {item}: {condition}, {collection})")
        self.map("reduce_kifejezés", "functools.reduce(lambda acc, {item}: {expression}, {collection}, {initial})", "import functools")

        # ===== ASZINKRON =====
        self.map("async_függvény", "async def {name}({params}):")
        self.map("await", "await {coroutine}")
        self.map("async_for", "async for {item} in {async_iter}:")
        self.map("async_with", "async with {context}:")
        self.map("async_kliens", "import aiohttp\n\nasync def {name}({params}):\n    async with aiohttp.ClientSession() as session:\n        {body}", "import aiohttp")

        # ===== VÉLETLEN =====
        self.map("véletlen", "random.randint({min}, {max})", "import random")
        self.map("random_elem", "random.choice({collection})", "import random")
        self.map("random_minta", "random.sample({collection}, {k})", "import random")

        # ===== IMPORT =====
        self.map("import", "import {module}")
        self.map("from_import", "from {module} import {names}")
        self.map("as_import", "import {module} as {alias}")

        # ===== ALGORITMUSOK (10+) =====
        self.map("buborékrendezés", """def bubble_sort(lista):
    n = len(lista)
    for i in range(n):
        for j in range(0, n - i - 1):
            if lista[j] > lista[j + 1]:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
    return lista""")
        self.map("gyorsrendezés", """def quick_sort(lista):
    if len(lista) <= 1:
        return lista
    pivot = lista[len(lista) // 2]
    left = [x for x in lista if x < pivot]
    middle = [x for x in lista if x == pivot]
    right = [x for x in lista if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)""")
        self.map("bináris_keresés", """def binary_search(lista, target):
    left, right = 0, len(lista) - 1
    while left <= right:
        mid = (left + right) // 2
        if lista[mid] == target:
            return mid
        elif lista[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1""")
        self.map("gráf_bejárás", """def bfs(graph, start):
    visited = set()
    queue = [start]
    while queue:
        node = queue.pop(0)
        if node not in visited:
            visited.add(node)
            queue.extend(graph.get(node, []))
    return visited""")
        self.map("legrövidebb_út", """def shortest_path(graph, start, end):
    queue = [(start, [start])]
    visited = {start}
    while queue:
        node, path = queue.pop(0)
        for neighbor in graph.get(node, []):
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None""")
        self.map("faktoriális", """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)""")
        self.map("fibonacci", """def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b""")
        self.map("prímteszt", """def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True""")
        self.map("palindrom", """def is_palindrome(s):
    s = s.lower().replace(' ', '')
    return s == s[::-1]""")
        self.map("karakterszámlálás", """def char_count(s):
    result = {}
    for c in s:
        result[c] = result.get(c, 0) + 1
    return result""")

        # ===== KÜLSŐ ADAT / API =====
        self.map("api_kliens", """import requests

def get_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None""", "import requests")

        self.map("api_post", """import requests

def send_data(url, data):
    response = requests.post(url, json=data)
    return response.status_code == 200""", "import requests")

        self.map("file_listazas", """import os

def list_files(path):
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]""")

        self.map("file_meret", """import os

def file_size(path):
    return os.path.getsize(path)""")

        # ===== JÁTÉK TEMPLATE-EK (Pygame) — változó paraméterekkel =====
        self.map("játék", """import pygame
import random
import sys

# === KONSTANSONS ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# === SZÍNEK ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COL = {player_color}
ENEMY_COL = {enemy_color}
BG_COL = {bg_color}
SCORE_COL = (0, 0, 0)

# === MODUL IMPORT ===
from player import Player
from enemy import Enemy

# === FŐ JÁTÉK ===
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("{game_title}")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)

    player = Player()
    enemies = []
    score = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.move(keys)

        # Ellenfelek spawnolása
        if random.random() < {spawn_rate}:
            enemies.append(Enemy())

        # Ellenfelek frissítése
        for enemy in enemies[:]:
            enemy.move()
            if enemy.y > SCREEN_HEIGHT:
                enemies.remove(enemy)
                score += 1
            elif enemy.collides_with(player):
                running = False

        # Rajzolás
        screen.fill(BG_COL)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)

        # Pontszám
        score_text = font.render(f"Score: {score}", True, SCORE_COL)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    # Játék vége
    screen.fill(BG_COL)
    game_over = big_font.render("{game_over_text}", True, ENEMY_COL)
    text_rect = game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
    screen.blit(game_over, text_rect)
    final_score = font.render(f"Végső pontszám: {score}", True, SCORE_COL)
    score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    screen.blit(final_score, score_rect)
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()""")

        self.map("karakter", """import pygame

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PLAYER_COL = {player_color}
ENEMY_COL = {enemy_color}

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 100
        self.width = {player_size}
        self.height = {player_size}
        self.speed = {player_speed}

    def move(self, keys):
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < SCREEN_HEIGHT - self.height:
            self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, PLAYER_COL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)""")

        self.map("ellenség", """import pygame
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PLAYER_COL = {player_color}
ENEMY_COL = {enemy_color}

class Enemy:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH - {enemy_size})
        self.y = -50
        self.width = {enemy_size}
        self.height = {enemy_size}
        self.speed = random.randint({enemy_speed_min}, {enemy_speed_max})

    def move(self):
        self.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, ENEMY_COL, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)

    def collides_with(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)""")

        self.map("lövedék", """class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 10
        self.height = 10
        self.speed = 10

    def move(self):
        self.y -= self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (self.x, self.y), 5)

    def collides_with(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)""")

        self.map("pontszám", """# Pontszám kijelzés
score_text = font.render(f"Score: {score}", True, BLACK)
screen.blit(score_text, (10, 10))""")

        self.map("ütközés", """# Ütközésvizsgálat
for enemy in enemies[:]:
    if enemy.collides_with(player):
        running = False""")

class HTMLDialect(LanguageDialect):
    """HTML nyelv — gazdag, modern template-ek 50+ komponenssel."""

    def __init__(self):
        super().__init__("html")

        # ===== TELJES WEBLAP MODERN CSS-SEL =====
        self.map("weblap", """<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 60px 20px; text-align: center; }
        header h1 { font-size: 2.8em; margin-bottom: 10px; }
        header p { font-size: 1.3em; opacity: 0.9; }
        nav { background: #2c3e50; padding: 15px 0; position: sticky; top: 0; z-index: 100; }
        nav ul { list-style: none; display: flex; gap: 25px; justify-content: center; max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        nav a { color: white; text-decoration: none; font-size: 1.05em; padding: 5px 10px; border-radius: 4px; transition: background 0.3s; }
        nav a:hover { background: #3498db; }
        main { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: 30px auto; max-width: 1200px; }
        footer { background: #2c3e50; color: white; padding: 30px 20px; text-align: center; margin-top: 40px; }
        footer p { margin: 5px 0; font-size: 0.9em; opacity: 0.8; }
        h1 { color: #2c3e50; margin-bottom: 20px; font-size: 2.2em; }
        h2 { color: #34495e; margin: 30px 0 15px; font-size: 1.6em; }
        h3 { color: #2c3e50; margin: 20px 0 10px; font-size: 1.3em; }
        p { margin-bottom: 15px; }
        .section { margin: 40px 0; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 25px; }
        .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
        @media (max-width: 768px) { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <header>
        <h1>{header_title}</h1>
        <p>{header_subtitle}</p>
    </header>
    <nav>
        <ul>
            <li><a href="#">Főoldal</a></li>
            <li><a href="#">Rólunk</a></li>
            <li><a href="#">Szolgáltatások</a></li>
            <li><a href="#">Galéria</a></li>
            <li><a href="#">Kapcsolat</a></li>
        </ul>
    </nav>
    <div class="container">
        <main>
            {children}
        </main>
    </div>
    <footer>
        <p>&copy; 2026 DKA V3 Generált Weboldal. Minden jog fenntartva.</p>
        <p>Készült a Determinisztikus Kognitív Architektúra V3 segítségével.</p>
    </footer>
</body>
</html>""")

        # ===== KÁRTYA =====
        self.map("kártya", """<div class="card" style="background:#f8f9fa;padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid #3498db;">
    <h3 style="margin-bottom:10px;">{title}</h3>
    <p>{text}</p>
</div>""")

        # ===== KÁRTYA CSOPORT (grid-ben) =====
        self.map("kártya_grid", """<div class="grid-3">
    {children}
</div>""")

        # ===== HERO SZEKCIÓ =====
        self.map("hero", """<section class="hero" style="background:linear-gradient(135deg,#2c3e50,#3498db);color:white;padding:80px 40px;border-radius:12px;text-align:center;margin:30px 0;">
    <h2 style="color:white;font-size:2.4em;margin-bottom:15px;">{hero_title}</h2>
    <p style="font-size:1.2em;opacity:0.9;max-width:800px;margin:0 auto 25px;">{hero_text}</p>
    <a href="#" style="display:inline-block;background:white;color:#2c3e50;padding:14px 35px;border-radius:30px;text-decoration:none;font-weight:bold;font-size:1.1em;">{button}</a>
</section>""")

        # ===== JELLEMZŐK RÁCS =====
        self.map("jellemzők", """<section class="features" style="margin:40px 0;">
    <h2 style="text-align:center;margin-bottom:30px;">{section_title}</h2>
    <div class="grid-3">
        {children}
    </div>
</section>""")

        self.map("jellemző", """<div class="feature" style="background:#f8f9fa;padding:25px;border-radius:8px;text-align:center;">
    <i class="{icon}" style="font-size:2.5em;color:#3498db;margin-bottom:15px;display:block;"></i>
    <h3>{feature_title}</h3>
    <p style="color:#666;font-size:0.95em;">{feature_text}</p>
</div>""")

        # ===== STATISZTIKA =====
        self.map("statisztika", """<section class="stats" style="background:linear-gradient(135deg,#2c3e50,#27ae60);color:white;padding:50px 30px;border-radius:12px;margin:30px 0;">
    <div class="grid-4">
        {children}
    </div>
</section>""")

        self.map("stat", """<div class="stat" style="text-align:center;">
    <div style="font-size:2.8em;font-weight:bold;">{stat_number}</div>
    <div style="font-size:1em;opacity:0.8;">{stat_label}</div>
</div>""")

        # ===== ÁRAZÁSI KÁRTYÁK =====
        self.map("árazás", """<section class="pricing" style="margin:40px 0;">
    <h2 style="text-align:center;margin-bottom:30px;">{section_title}</h2>
    <div class="grid-3">
        {children}
    </div>
</section>""")

        self.map("ár_kártya", """<div class="pricing-card" style="background:#f8f9fa;padding:30px;border-radius:12px;text-align:center;border:2px solid {border};">
    <h3 style="font-size:1.5em;">{plan_name}</h3>
    <div style="font-size:3em;font-weight:bold;color:#2c3e50;margin:20px 0;">{price}<span style="font-size:0.3em;color:#666;">/hó</span></div>
    <ul style="list-style:none;padding:0;margin:20px 0;text-align:left;">
        <li style="padding:8px 0;border-bottom:1px solid #ddd;">&#10003; {feature_1}</li>
        <li style="padding:8px 0;border-bottom:1px solid #ddd;">&#10003; {feature_2}</li>
        <li style="padding:8px 0;border-bottom:1px solid #ddd;">&#10003; {feature_3}</li>
    </ul>
    <a href="#" style="display:block;background:#3498db;color:white;padding:12px;border-radius:6px;text-decoration:none;font-weight:bold;">{button}</a>
</div>""")

        # ===== ACCORDION / FAQ =====
        self.map("faq", """<section class="faq" style="margin:40px 0;">
    <h2 style="text-align:center;margin-bottom:30px;">{section_title}</h2>
    {children}
</section>""")

        self.map("faq_elem", """<details style="margin:10px 0;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
    <summary style="padding:15px 20px;background:#f8f9fa;cursor:pointer;font-weight:bold;font-size:1.05em;">{question}</summary>
    <div style="padding:15px 20px;border-top:1px solid #ddd;color:#555;">{answer}</div>
</details>""")

        # ===== TABOK =====
        self.map("tabs", """<div class="tabs" style="margin:30px 0;">
    <div class="tab-buttons" style="display:flex;gap:5px;border-bottom:2px solid #3498db;margin-bottom:20px;">
        {tab_buttons}
    </div>
    <div class="tab-content" style="padding:20px;background:#f8f9fa;border-radius:0 8px 8px 8px;">
        {children}
    </div>
</div>""")

        self.map("tab_button", """<button class="tab-btn" onclick="showTab('{tab_id}','{tab_name}')" style="padding:12px 25px;border:none;background:{active};color:white;border-radius:6px 6px 0 0;cursor:pointer;font-size:1em;">{tab_name}</button>""")

        self.map("tab_panel", """<div id="tab_{tab_name}" class="tab-panel" style="display:{display};">
    <h3>{tab_title}</h3>
    <p>{tab_content}</p>
</div>""")

        # ===== MODÁLIS ABLAK =====
        self.map("modális", """<div id="{modal_id}" class="modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);justify-content:center;align-items:center;z-index:1000;">
    <div class="modal-content" style="background:white;padding:35px;border-radius:12px;max-width:600px;width:90%;position:relative;">
        <span onclick="document.getElementById('{modal_id}').style.display='none'" style="position:absolute;top:15px;right:20px;font-size:1.8em;cursor:pointer;color:#888;">&times;</span>
        <h2 style="margin-bottom:15px;">{modal_title}</h2>
        <div>{children}</div>
        <button onclick="document.getElementById('{modal_id}').style.display='none'" style="background:#3498db;color:white;padding:10px 25px;border:none;border-radius:6px;cursor:pointer;margin-top:15px;">Bezárás</button>
    </div>
</div>""")

        # ===== OLDALSÁV LAYOUT =====
        self.map("oldalsáv", """<div class="sidebar-layout" style="display:grid;grid-template-columns:300px 1fr;gap:30px;margin:30px 0;">
    <aside class="sidebar" style="background:#f8f9fa;padding:25px;border-radius:8px;height:fit-content;position:sticky;top:80px;">
        <h3 style="margin-bottom:15px;">{sidebar_title}</h3>
        {sidebar_children}
    </aside>
    <div class="main-content">
        {children}
    </div>
</div>""")

        # ===== CSAPAT RÁCS =====
        self.map("csapat", """<section class="team" style="margin:40px 0;">
    <h2 style="text-align:center;margin-bottom:30px;">{section_title}</h2>
    <div class="grid-3">
        {children}
    </div>
</section>""")

        self.map("csapattag", """<div class="team-member" style="background:#f8f9fa;padding:25px;border-radius:8px;text-align:center;">
    <img src="{avatar}" alt="{name}" style="width:120px;height:120px;border-radius:50%;object-fit:cover;margin-bottom:15px;">
    <h3>{name}</h3>
    <p style="color:#3498db;font-weight:bold;margin:5px 0;">{role}</p>
    <p style="color:#666;font-size:0.9em;">{bio}</p>
</div>""")

        # ===== IDŐVONAL =====
        self.map("idővonal", """<section class="timeline" style="margin:40px 0;">
    <h2 style="text-align:center;margin-bottom:30px;">{section_title}</h2>
    <div class="timeline-items" style="position:relative;padding-left:30px;border-left:3px solid #3498db;">
        {children}
    </div>
</section>""")

        self.map("idővonal_elem", """<div class="timeline-item" style="margin:30px 0;position:relative;">
    <div style="position:absolute;left:-38px;top:5px;width:14px;height:14px;background:#3498db;border-radius:50%;border:3px solid white;"></div>
    <div style="background:#f8f9fa;padding:20px;border-radius:8px;">
        <span style="color:#3498db;font-weight:bold;">{date}</span>
        <h4 style="margin:8px 0;">{event_title}</h4>
        <p style="color:#666;">{event_desc}</p>
    </div>
</div>""")

        # ===== VISSZAJELZÉS KÁRTYÁK =====
        self.map("visszajelzés", """<section class="testimonials" style="margin:40px 0;">
    <h2 style="text-align:center;margin-bottom:30px;">{section_title}</h2>
    <div class="grid-2">
        {children}
    </div>
</section>""")

        self.map("tesztimónium", """<div class="testimonial" style="background:#f8f9fa;padding:25px;border-radius:8px;border-left:4px solid #3498db;">
    <p style="font-style:italic;margin-bottom:15px;">&ldquo;{quote}&rdquo;</p>
    <div style="display:flex;align-items:center;gap:12px;">
        <img src="{avatar}" alt="{author}" style="width:50px;height:50px;border-radius:50%;object-fit:cover;">
        <div>
            <strong>{author}</strong>
            <span style="display:block;color:#666;font-size:0.85em;">{author_role}</span>
        </div>
    </div>
</div>""")

        # ===== KAPCSOLAT SZEKCIÓ =====
        self.map("kapcsolati_szekció", """<section class="contact" style="margin:40px 0;">
    <h2 style="text-align:center;margin-bottom:20px;">{section_title}</h2>
    <div style="max-width:600px;margin:0 auto;">
        {children}
    </div>
</section>""")

        # ===== HÍRLEVÉL =====
        self.map("hírlevél", """<section class="newsletter" style="background:linear-gradient(135deg,#3498db,#2c3e50);color:white;padding:50px 30px;border-radius:12px;text-align:center;margin:30px 0;">
    <h3 style="color:white;font-size:1.5em;margin-bottom:10px;">{newsletter_title}</h3>
    <p style="opacity:0.9;margin-bottom:20px;">{newsletter_text}</p>
    <form action="#" method="post" style="display:flex;max-width:500px;margin:0 auto;gap:10px;">
        <input type="email" placeholder="email@pelda.hu" required style="flex:1;padding:14px 20px;border:none;border-radius:6px;font-size:1em;">
        <button type="submit" style="background:#27ae60;color:white;padding:14px 30px;border:none;border-radius:6px;cursor:pointer;font-size:1em;font-weight:bold;">{button}</button>
    </form>
</section>""")

        # ===== KERESŐ SÁV =====
        self.map("kereső", """<div class="search-bar" style="margin:20px 0;">
    <form action="#" method="get" style="display:flex;max-width:500px;gap:10px;">
        <input type="search" placeholder="{placeholder}" required style="flex:1;padding:12px 18px;border:2px solid #ddd;border-radius:8px;font-size:1em;">
        <button type="submit" style="background:#3498db;color:white;padding:12px 25px;border:none;border-radius:8px;cursor:pointer;"><i class="fas fa-search"></i> Keresés</button>
    </form>
</div>""")

        # ===== LAPOZÓ =====
        self.map("lapozó", """<div class="pagination" style="display:flex;justify-content:center;gap:8px;margin:30px 0;">
    <a href="#" style="padding:10px 16px;background:#f8f9fa;border-radius:6px;text-decoration:none;color:#333;">&laquo;</a>
    <a href="#" style="padding:10px 16px;background:#3498db;color:white;border-radius:6px;text-decoration:none;">1</a>
    <a href="#" style="padding:10px 16px;background:#f8f9fa;border-radius:6px;text-decoration:none;color:#333;">2</a>
    <a href="#" style="padding:10px 16px;background:#f8f9fa;border-radius:6px;text-decoration:none;color:#333;">3</a>
    <a href="#" style="padding:10px 16px;background:#f8f9fa;border-radius:6px;text-decoration:none;color:#333;">&raquo;</a>
</div>""")

        # ===== HALADÁSSÁV =====
        self.map("haladássáv", """<div class="progress-section" style="margin:30px 0;">
    <h3>{section_title}</h3>
    {children}
</div>""")

        self.map("haladás", """<div style="margin:15px 0;">
    <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
        <span>{skill_name}</span>
        <span>{percent}%</span>
    </div>
    <div style="background:#e0e0e0;border-radius:10px;height:12px;overflow:hidden;">
        <div style="background:linear-gradient(90deg,#3498db,#27ae60);width:{percent}%;height:100%;border-radius:10px;transition:width 1s;"></div>
    </div>
</div>""")

        # ===== CÉL / STATISZTIKA KÁRTYA =====
        self.map("cél_kártya", """<div class="stat-card" style="background:white;padding:25px;border-radius:12px;text-align:center;box-shadow:0 2px 15px rgba(0,0,0,0.06);">
    <div style="font-size:2.2em;color:#3498db;margin-bottom:8px;">{stat_icon}</div>
    <div style="font-size:2em;font-weight:bold;">{stat_value}</div>
    <div style="color:#666;font-size:0.9em;">{stat_label}</div>
</div>""")

        # ===== ALAP HTML ELEMEK =====
        self.map("űrlap", """<form action="#" method="post" style="background:#f8f9fa;padding:30px;border-radius:8px;margin:20px 0;">
    <h2>Kapcsolatfelvétel</h2>
    <p style="margin-bottom:20px;">Kérjük, töltse ki az alábbi űrlapot:</p>
    {children}
    <button type="submit" style="background:#3498db;color:white;padding:14px 30px;border:none;border-radius:6px;font-size:1em;cursor:pointer;font-weight:bold;margin-top:10px;">Küldés</button>
</form>""")
        self.map("input_mező", """    <div class="form-group" style="margin-bottom:15px;">
        <label for="{name}" style="display:block;margin-bottom:5px;font-weight:bold;color:#555;">{label}</label>
        <input type="{type}" id="{name}" name="{name}" placeholder="Adja meg a(z) {label}-t" required style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;font-size:1em;">
    </div>""")
        self.map("gomb", """    <button onclick="{onclick}" style="background:#3498db;color:white;padding:12px 25px;border:none;border-radius:6px;cursor:pointer;font-size:1em;margin-top:10px;">{text}</button>""")

        self.map("cím", """<h1 style="color:#2c3e50;margin:20px 0;">{text}</h1>""")
        self.map("bekezdés", """<p style="margin-bottom:15px;line-height:1.8;">{text}</p>""")
        self.map("lista", """<ul style="margin:20px 0;padding-left:25px;">
    {items}
</ul>""")
        self.map("lista_elem", """    <li style="margin:8px 0;">{item}</li>""")

        self.map("kép", """<figure style="margin:25px 0;">
    <img src="{src}" alt="{alt}" style="width:100%;max-width:700px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.1);">
    <figcaption style="text-align:center;color:#666;margin-top:10px;font-style:italic;">{caption}</figcaption>
</figure>""")

        self.map("táblázat", """<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;margin:25px 0;box-shadow:0 2px 10px rgba(0,0,0,0.05);">
    <thead>
        <tr>
            <th style="padding:14px;text-align:left;background:#2c3e50;color:white;font-weight:bold;">Név</th>
            <th style="padding:14px;text-align:left;background:#2c3e50;color:white;font-weight:bold;">Leírás</th>
            <th style="padding:14px;text-align:left;background:#2c3e50;color:white;font-weight:bold;">Érték</th>
        </tr>
    </thead>
    <tbody>
        <tr style="border-bottom:1px solid #eee;"><td style="padding:12px;">Első elem</td><td style="padding:12px;">Példa adat</td><td style="padding:12px;">1</td></tr>
        <tr style="border-bottom:1px solid #eee;"><td style="padding:12px;">Második elem</td><td style="padding:12px;">Példa adat</td><td style="padding:12px;">2</td></tr>
        <tr><td style="padding:12px;">Harmadik elem</td><td style="padding:12px;">Példa adat</td><td style="padding:12px;">3</td></tr>
    </tbody>
</table>
</div>""")

        self.map("dinamikus_tábla", """<div style="overflow-x:auto;">
<table id="{table_id}" style="width:100%;border-collapse:collapse;margin:25px 0;box-shadow:0 2px 10px rgba(0,0,0,0.05);">
    <thead>
        <tr>
            {headers}
        </tr>
    </thead>
    <tbody id="{tbody_id}">
        {children}
    </tbody>
</table>
</div>""")

        self.map("táblázat_fejléc", """<th style="padding:14px;text-align:left;background:#2c3e50;color:white;font-weight:bold;">{header_text}</th>""")
        self.map("táblázat_sor", """<tr style="border-bottom:1px solid #eee;">
    {cells}
</tr>""")
        self.map("táblázat_cella", """<td style="padding:12px;">{cell_text}</td>""")

        self.map("link", """<a href="{href}" style="color:#3498db;text-decoration:none;font-weight:500;">{text}</a>""")
        self.map("menü", """<nav style="background:#2c3e50;padding:15px 0;border-radius:8px;margin:20px 0;">
    <ul style="list-style:none;display:flex;gap:20px;justify-content:center;padding:0 20px;">
        <li><a href="#" style="color:white;text-decoration:none;padding:8px 15px;">Főoldal</a></li>
        <li><a href="#" style="color:white;text-decoration:none;padding:8px 15px;">Rólunk</a></li>
        <li><a href="#" style="color:white;text-decoration:none;padding:8px 15px;">Szolgáltatások</a></li>
        <li><a href="#" style="color:white;text-decoration:none;padding:8px 15px;">Kapcsolat</a></li>
    </ul>
</nav>""")
        self.map("stílus", """<style>
    {children}
</style>""")
        self.map("fejléc", """<header style="background:linear-gradient(135deg,#2c3e50,#3498db);color:white;padding:30px;border-radius:12px;margin-bottom:25px;">
    <h2 style="color:white;margin:0;">{text}</h2>
    {children}
</header>""")
        self.map("lábléc", """<footer style="margin-top:40px;padding:25px;text-align:center;color:#666;border-top:1px solid #ddd;">
    <p>&copy; 2026 DKA V3</p>
    {children}
</footer>""")

        # ===== INPUT TÍPUSOK =====
        self.map("email_input", """    <div class="form-group" style="margin-bottom:15px;">
        <label for="{name}" style="display:block;margin-bottom:5px;font-weight:bold;color:#555;">{label}</label>
        <input type="email" id="{name}" name="{name}" placeholder="pelda@email.hu" required style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;font-size:1em;">
    </div>""")
        self.map("password_input", """    <div class="form-group" style="margin-bottom:15px;">
        <label for="{name}" style="display:block;margin-bottom:5px;font-weight:bold;color:#555;">{label}</label>
        <input type="password" id="{name}" name="{name}" placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022" required style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;font-size:1em;">
    </div>""")
        self.map("textarea", """    <div class="form-group" style="margin-bottom:15px;">
        <label for="{name}" style="display:block;margin-bottom:5px;font-weight:bold;color:#555;">{label}</label>
        <textarea id="{name}" name="{name}" rows="5" placeholder="Írja ide az üzenetét..." required style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;font-size:1em;resize:vertical;"></textarea>
    </div>""")
        self.map("number_input", """    <div class="form-group" style="margin-bottom:15px;">
        <label for="{name}" style="display:block;margin-bottom:5px;font-weight:bold;color:#555;">{label}</label>
        <input type="number" id="{name}" name="{name}" placeholder="{placeholder}" min="0" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;font-size:1em;">
    </div>""")
        self.map("select_input", """    <div class="form-group" style="margin-bottom:15px;">
        <label for="{name}" style="display:block;margin-bottom:5px;font-weight:bold;color:#555;">{label}</label>
        <select id="{name}" name="{name}" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;font-size:1em;">
            <option value="">Válasszon...</option>
            {options}
        </select>
    </div>""")
        self.map("checkbox_input", """    <div class="form-group" style="margin-bottom:15px;">
        <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
            <input type="checkbox" name="{name}" style="width:18px;height:18px;">
            <span>{label}</span>
        </label>
    </div>""")
        self.map("radio_input", """    <div class="form-group" style="margin-bottom:15px;">
        <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
            <input type="radio" name="{name}" value="{value}" style="width:18px;height:18px;">
            <span>{label}</span>
        </label>
    </div>""")


# ======================================================================
# CSS DIALECT
# ======================================================================

class CSSDialect(LanguageDialect):
    """CSS nyelv specifikus leképezések."""

    def __init__(self):
        super().__init__("css")
        self.map("grid", "display: grid;\ngrid-template-columns: repeat({cols}, 1fr);\ngap: {gap};")
        self.map("flex", "display: flex;\nflex-wrap: wrap;\ngap: {gap};")
        self.map("flex_center", "display: flex;\njustify-content: center;\nalign-items: center;")
        self.map("flex_between", "display: flex;\njustify-content: space-between;\nalign-items: center;")
        self.map("flex_column", "display: flex;\nflex-direction: column;\ngap: {gap};")
        self.map("shadow", "box-shadow: 0 {x}px {y}px {blur}px rgba(0,0,0,0.1);")
        self.map("gradient", "background: linear-gradient({deg}deg, {color1}, {color2});")
        self.map("rounded", "border-radius: {radius}px;")
        self.map("transition", "transition: all {duration}s ease;")
        self.map("animation", "@keyframes {name} {\n    from { {from_prop}: {from_val}; }\n    to { {to_prop}: {to_val}; }\n}")
        self.map("responsive", "@media (max-width: {breakpoint}px) {\n    {children}\n}")
        self.map("hover", "&:hover {\n    {children}\n}")
        self.map("card_style", "background: white;\npadding: 25px;\nborder-radius: 8px;\nbox-shadow: 0 2px 10px rgba(0,0,0,0.06);")
        self.map("container", "max-width: 1200px;\nmargin: 0 auto;\npadding: 0 20px;")
        self.map("dark_theme", "background: #1a1a2e;\ncolor: #eee;")
        self.map("glass_effect", "background: rgba(255,255,255,0.1);\nbackdrop-filter: blur(10px);\n-webkit-backdrop-filter: blur(10px);")


# ======================================================================
# JAVASCRIPT DIALECT — Komplex template-ekkel
# ======================================================================

class JavaScriptDialect(LanguageDialect):
    """JavaScript nyelv — alap + haladó template-ek."""

    def __init__(self):
        super().__init__("javascript")
        # ===== ALAP =====
        self.map("gyűjtemény", "[]")
        self.map("szűrés", "{collection}.filter({item} => {condition})")
        self.map("rendezés", "{collection}.sort({compare})")
        self.map("transzformáció", "{collection}.map({item} => {func})")
        self.map("összegzés", "{collection}.reduce((acc, {item}) => acc + {item}, 0)")
        self.map("bejárás", "{collection}.forEach({item} => {body})")
        self.map("feltétel", "if ({condition}) {body}")
        self.map("függvény", "function {name}({params}) {body}")
        self.map("visszatérés", "return {value};")
        self.map("kiírás", "console.log({value})")
        self.map("gomb_kattintás", "document.querySelector('{selector}').onclick = () => {body}")

        # ===== DOM =====
        self.map("dom_kiválasztás", "document.querySelector('{selector}')")
        self.map("dom_összes", "document.querySelectorAll('{selector}')")
        self.map("dom_tartalom", "document.querySelector('{selector}').innerHTML = {content}")
        self.map("dom_szöveg", "document.querySelector('{selector}').textContent = '{text}'")
        self.map("dom_stílus", "document.querySelector('{selector}').style.{property} = '{value}'")
        self.map("dom_osztály", "document.querySelector('{selector}').classList.{method}('{class_name}')")
        self.map("dom_létrehoz", "document.createElement('{tag}')")
        self.map("dom_hozzáad", "document.querySelector('{parent}').appendChild({element})")
        self.map("dom_töröl", "document.querySelector('{selector}').remove()")
        self.map("dom_esemény", "document.querySelector('{selector}').addEventListener('{event}', (e) => {body})")

        # ===== FETCH / API =====
        self.map("fetch_get", "fetch('{url}')\n    .then(res => res.json())\n    .then(data => {body})\n    .catch(err => console.error(err))")
        self.map("fetch_post", "fetch('{url}', {\n    method: 'POST',\n    headers: { 'Content-Type': 'application/json' },\n    body: JSON.stringify({data})\n})\n    .then(res => res.json())\n    .then(data => {body})\n    .catch(err => console.error(err))")
        self.map("async_fetch", "async function {name}(url) {\n    try {\n        const res = await fetch(url);\n        const data = await res.json();\n        {body}\n    } catch (error) {\n        console.error('Fetch error:', error);\n    }\n}")

        # ===== ŰRLAP VALIDÁCIÓ =====
        self.map("űrlap_validáció", """document.querySelector('form').addEventListener('submit', function(e) {
    e.preventDefault();
    let valid = true;
    const fields = this.querySelectorAll('[required]');
    fields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = 'red';
            valid = false;
        } else {
            field.style.borderColor = '#ddd';
        }
    });
    if (valid) {
        alert('Sikeres küldés!');
        this.reset();
    }
});""")

        # ===== LOCAL STORAGE =====
        self.map("localStorage_mentés", "localStorage.setItem('{key}', JSON.stringify({value}))")
        self.map("localStorage_olvas", "JSON.parse(localStorage.getItem('{key}') || '[]')")
        self.map("localStorage_töröl", "localStorage.removeItem('{key}')")

        # ===== ANIMÁCIÓ =====
        self.map("animáció_indítás", "document.querySelector('{selector}').animate([\n    { '{from_prop}': '{from_val}' },\n    { '{to_prop}': '{to_val}' }\n], {\n    duration: {dur}ms,\n    iterations: {iter},\n    easing: 'ease'\n})")

        # ===== IDŐZÍTŐ =====
        self.map("setTimeout", "setTimeout(() => {body}, {ms})")
        self.map("setInterval", "setInterval(() => {body}, {ms})")
        self.map("requestAnimationFrame", "requestAnimationFrame(() => {body})")

        # ===== MATH =====
        self.map("random", "Math.random()")
        self.map("egész", "Math.round({value})")
        self.map("minimum", "Math.min({a}, {b})")
        self.map("maximum", "Math.max({a}, {b})")


# ======================================================================
# GENERATOR
# ======================================================================

class Generator:
    """
    Terv → Kód.

    Megkap egy tervet (Plan) és egy célnyelvet.
    Végigmegy a terv lépésein, és minden lépéshez
    generálja a megfelelő kódot a nyelv dialektusából.
    """

    def __init__(self, graph: ConceptGraph):
        self.graph = graph
        self.dialects = {
            "python": PythonDialect(),
            "html": HTMLDialect(),
            "javascript": JavaScriptDialect(),
            "css": CSSDialect(),
        }
        # Téma-specifikus tartalom generátor
        self._topic_content: dict[str, dict] = {}

    def add_dynamic_template(self, concept: str, template: str, language: str = "html", imports: str = ""):
        """Dinamikus template hozzáadása — inferált fogalmakhoz."""
        dialect = self.dialects.get(language)
        if dialect and not dialect.get_template(concept):
            dialect.map(concept, template, imports)

    def _get_topic_context(self, goal: str) -> dict:
        """Kivonja a témát a cél szövegből, és témához illő tartalmat generál."""
        if goal in self._topic_content:
            return self._topic_content[goal]

        g = goal.lower()

        # Téma detektálás
        topic = "általános"
        if any(w in g for w in ["játék", "jatek", "game", "fps", "rpg"]):
            topic = "játék"
        elif any(w in g for w in ["portfólió", "portfolio", "bemutatkoz"]):
            topic = "portfólió"
        elif any(w in g for w in ["étterem", "etterem", "restaurant", "vendéglő"]):
            topic = "étterem"
        elif any(w in g for w in ["iskola", "tanulás", "oktatás", "training", "oktatas"]):
            topic = "oktatás"
        elif any(w in g for w in ["blog", "cikk", "hirek", "news"]):
            topic = "blog"
        elif any(w in g for w in ["sport", "edzés", "fitness", "sport"]):
            topic = "sport"
        elif any(w in g for w in ["tech", "technológia", "technologia"]):
            topic = "tech"

        # Téma-specifikus tartalom
        content = {
            "játék": {
                "header_title": "Epikus Kalandok Birodalma",
                "header_subtitle": "Merülj el egy lenyűgöző fantáziavilágban",
                "title": "Játék bemutató - Fedezd fel a kalandot!",
                "text": "Egy izgalmas akció-kalandjáték, ahol a hős egy sötét erő ellen harcol. Fedezz fel titkokat, győzz le ellenségeket és mentsd meg a világot!",
                "alt": "Képernyőkép a játékból",
                "caption": "Játékmenet - A főhős csatája",
                "src": "https://via.placeholder.com/800x500?text=Jatek+kepernyokep",
                "button": "Játék letöltése",
                "card_title": "Játékjellemzők",
                "features": ["Lenyűgöző grafika", "Izgalmas történet", "Többjátékos mód"],
                "hero_title": "Fedezd fel a Kalandot!",
                "hero_text": "Egy epikus akciójáték, ahol a választásaid számítanak. Több mint 50 óra játékidő, lenyűgöző környezetek.",
                "section_title": "Játékjellemzők",
                "avatar": "https://via.placeholder.com/120?text=Avatar",
            },
            "sport": {
                "header_title": "Sport Központ",
                "header_subtitle": "Mozgás, egészség, közösség",
                "title": "Üdvözöljük a Sport Központban!",
                "text": "Professzionális edzőtermek, személyi edzők és közösségi programok várnak. Csatlakozz te is!",
                "alt": "Sport terem",
                "caption": "Modern edzőterem",
                "src": "https://via.placeholder.com/800x500?text=Sport+kozpont",
                "button": "Csatlakozom!",
                "card_title": "Szolgáltatásaink",
                "features": ["Személyi edzés", "Csoportos órák", "Táplálkozási tanácsadás"],
                "hero_title": "Érj el többet!",
                "hero_text": "Személyre szabott edzésterv, tapasztalt edzők, barátságos közösség.",
                "section_title": "Miért válassz minket?",
                "avatar": "https://via.placeholder.com/120?text=Avatar",
            },
            "portfólió": {
                "header_title": "Üdvözöljük a Portfóliómban",
                "header_subtitle": "Kreatív megoldások, modern technológiák",
                "title": "Bemutatkozás - Ki vagyok és mit csinálok",
                "text": "Szenvedélyes fejlesztő vagyok, aki szeret új kihívásokkal szembenézni. Tapasztalatom van webfejlesztésben, dizájnban és projektmenedzsmentben.",
                "alt": "Projekt képernyőkép",
                "caption": "Kiemelt projekt",
                "src": "https://via.placeholder.com/800x500?text=Portfolio+projekt",
                "button": "Kapcsolatfelvétel",
                "card_title": "Szolgáltatásaim",
                "features": ["Webfejlesztés", "UI/UX Design", "Tanácsadás"],
                "hero_title": "Kreatív Megoldások",
                "hero_text": "Modern webalkalmazások, reszponzív design, felhasználóközpontú tervezés.",
                "section_title": "Kiemelt szolgáltatásaim",
                "avatar": "https://via.placeholder.com/120?text=Avatar",
            },
            "oktatás": {
                "header_title": "Tanulj Velünk!",
                "header_subtitle": "Online oktatás mindenkinek",
                "title": "Oktatási Portál",
                "text": "Interaktív kurzusok, szakértő oktatók, modern tananyag. Fejleszd tudásod még ma!",
                "alt": "Oktatás kép",
                "caption": "Online tanulás",
                "src": "https://via.placeholder.com/800x500?text=Oktatas",
                "button": "Kurzusok megtekintése",
                "card_title": "Kurzusaink",
                "features": ["Programozás", "Design", "Adatelemzés"],
                "hero_title": "Fejleszd a jövődet!",
                "hero_text": "Több mint 100 kurzus, gyakorlati tudás, okleveles képzés.",
                "section_title": "Népszerű kurzusok",
                "avatar": "https://via.placeholder.com/120?text=Avatar",
            },
            "blog": {
                "header_title": "Blog",
                "header_subtitle": "Friss hírek, érdekes cikkek",
                "title": "Üdvözöljük a Blogban!",
                "text": "Itt találod a legfrissebb híreket, cikkeket és gondolatébresztő írásokat.",
                "alt": "Blog kép",
                "caption": "Blog poszt",
                "src": "https://via.placeholder.com/800x500?text=Blog",
                "button": "Tovább olvasom",
                "card_title": "Legfrissebb",
                "features": ["Technológia", "Tudomány", "Kultúra"],
                "hero_title": "Fedezd fel!",
                "hero_text": "Hetente frissülő tartalmak, szakértő szerzőktől.",
                "section_title": "Legújabb posztok",
                "avatar": "https://via.placeholder.com/120?text=Author",
            },
            "tech": {
                "header_title": "TechPort",
                "header_subtitle": "A technológia világa",
                "title": "Technológiai hírek és elemzések",
                "text": "AI, felhőszolgáltatások, kiberbiztonság és még sok más. Tarts velünk!",
                "alt": "Tech kép",
                "caption": "Technológiai újdonságok",
                "src": "https://via.placeholder.com/800x500?text=Tech",
                "button": "Tudj meg többet",
                "card_title": "Témakörök",
                "features": ["Mesterséges intelligencia", "Felhő", "Biztonság"],
                "hero_title": "A technológia jövője",
                "hero_text": "Friss hírek, terméktesztek, szakértői vélemények.",
                "section_title": "Kiemelt témák",
                "avatar": "https://via.placeholder.com/120?text=Expert",
            },
            "általános": {
                "header_title": "DKA V3 Weboldal",
                "header_subtitle": "Ezt az oldalt a Determinisztikus Kognitív Architektúra V3 generálta",
                "title": "Üdvözöljük a DKA V3 által generált weboldalon!",
                "text": "Ez a weboldal a DKA V3 (Determinisztikus Kognitív Architektúra) által készült. A DKA egy új típusú mesterséges intelligencia, ami fogalmi szinten érti meg a feladatokat.",
                "alt": "DKA V3 által generált kép",
                "caption": "DKA V3 - Generált tartalom",
                "src": "https://via.placeholder.com/800x500?text=DKA+V3",
                "button": "Tovább",
                "card_title": "Jellemzők",
                "features": ["Gyors", "Megbízható", "Okos"],
                "hero_title": "DKA V3 - Új AI faj",
                "hero_text": "Determinisztikus Kognitív Architektúra. Fogalmi szintű megértés, nulla hallucináció.",
                "section_title": "Képességek",
                "avatar": "https://via.placeholder.com/120?text=DKA",
            },
        }

        result = content.get(topic, content["általános"])
        self._topic_content[goal] = result
        return result

    def generate(self, plan: Plan, language: str = "python") -> Optional[dict[str, str] | str]:
        """Terv → kód. Visszaadhat dict-et (file→kód) vagy stringet (1 fájl)."""
        dialect = self.dialects.get(language)
        if not dialect:
            return None

        goal_lower = plan.goal.lower()
        has_html_part = any(w in goal_lower for w in ["html", "weblap", "weboldal", "urlap"])
        has_python_part = any(w in goal_lower for w in ["python", "pythonban", "szurd", "szűrd", "rendez"])

        if has_html_part and has_python_part and language == "html":
            pass

        # Több fájlba gyűjtés
        files: dict[str, list[str]] = {}
        file_imports: dict[str, set[str]] = {}
        topic_ctx = self._get_topic_context(plan.goal)

        def add_to_file(fname: str, code: str, imp: str = ""):
            if fname not in files:
                files[fname] = []
                file_imports[fname] = set()
            if code:
                files[fname].append(code)
            if imp:
                file_imports[fname].add(imp)

        def process_step(step: PlanStep, imports_used: set, ctx: dict, default_file: str):
            """Rekurzívan feldolgoz egy lépést és a gyerekeit."""
            fname = step.file or default_file
            if not self._has_template(step, dialect):
                for c in step.children:
                    process_step(c, imports_used, ctx, fname)
                return
            step_imports = set()
            code = self._generate_step(step, dialect, step_imports, ctx)
            if code:
                add_to_file(fname, code)
                for imp in step_imports:
                    add_to_file("__imports__", "", imp)
            
            for c in step.children:
                child_imports = set()
                child_code = self._generate_step(c, dialect, child_imports, ctx)
                # Gyerekek MÁR benne vannak a szülő {body}/{children} placeholderében
                # Csak akkor adjuk külön fájlba, ha saját file-juk van
                if child_code and c.file and c.file != fname:
                    target_file = c.file
                    add_to_file(target_file, child_code)
                    for imp in child_imports:
                        add_to_file(target_file, "", imp)

        for step in plan.steps:
            step_imports = set()
            process_step(step, step_imports, topic_ctx, "main.py")

        if not files:
            return None

        # Összeállítás: minden fájlhoz import + kód
        result = {}
        default_file = "main.py"
        for fname in sorted(files.keys()):
            if fname == "__imports__":
                continue
            code_parts = files[fname]
            imps = file_imports.get(fname, set()) | file_imports.get("__imports__", set())
            if imps:
                imp_lines = sorted(imps)
            else:
                imp_lines = []
            
            full_code = ""
            if imp_lines:
                full_code = "\n".join(imp_lines) + "\n\n"
            full_code += "\n".join(code_parts)
            
            # HTML esetén weblapba csomagolás
            if language == "html" and fname == default_file:
                already_full_page = any(s.action == "weblap" for s in plan.steps)
                if not already_full_page:
                    template = dialect.get_template("weblap") or "{content}"
                    full_code = template.replace("{title}", plan.goal).replace("{content}", full_code)
            
            result[fname] = full_code

        if len(result) == 1 and default_file in result:
            return result[default_file]
        return result

    def _has_template(self, step: PlanStep, dialect: LanguageDialect) -> bool:
        """Van-e template a lépéshez a célnyelv dialektusában?"""
        if dialect.get_template(step.action):
            return True
        for child in step.children:
            if self._has_template(child, dialect):
                return True
        return False

    def _generate_step(self, step: PlanStep, dialect: LanguageDialect,
                        imports_used: set, topic_ctx: dict = None) -> Optional[str]:
        """Egy tervlépés kódra fordítása."""
        if topic_ctx is None:
            topic_ctx = {}

        # Speciális eset: feltétel → csak a kifejezést generáljuk (nem if-et)
        if step.action == "feltétel":
            condition_map = {
                "páros": "x % 2 == 0", "páratlan": "x % 2 != 0",
                "even": "x % 2 == 0", "odd": "x % 2 != 0",
                "pozitív": "x > 0", "positive": "x > 0",
                "negatív": "x < 0", "negative": "x < 0",
                "nagyobb": "x > {val}", "kisebb": "x < {val}",
                "egyenlő": "x == {val}", "equal": "x == {val}",
                "tartalmaz": "'{sub}' in x", "contains": "'{sub}' in x",
                "hosszabb": "len(x) > {val}", "longer": "len(x) > {val}",
            }
            for keyword, code in condition_map.items():
                if keyword in (step.description or "").lower():
                    return code
            return step.description or "True"

        # Próbáljuk a gyerek lépéseket először
        child_codes = []
        for child in step.children:
            child_code = self._generate_step(child, dialect, imports_used, topic_ctx)
            if child_code:
                child_codes.append(child_code)

        template = dialect.get_template(step.action)
        if not template:
            # Ha nincs közvetlen template, próbáljuk a fogalom
            # kapcsolataiból következtetni
            concept = self.graph.get(step.action)
            if not concept:
                return None

            # Nézzük a HAS_OPERATION kapcsolatokat
            for rel in concept.relations:
                if rel.type == RelationType.HAS_OPERATION:
                    template = dialect.get_template(rel.target_name)
                    if template:
                        break

            if not template:
                return None

        # Template kitöltése
        result = template

        # Téma-kontextus alapértelmezett értékei
        if not topic_ctx:
            topic_ctx = {"header_title": "DKA V3", "header_subtitle": "Generált oldal",
                        "title": "Üdvözöljük", "text": "Tartalom", "alt": "Kép",
                        "caption": "Felirat", "src": "#", "button": "Tovább",
                        "card_title": "Jellemzők", "features": [],
                        "hero_title": "Hero cím", "hero_text": "Hero szöveg",
                        "section_title": "Szekció cím"}

        # Dinamikus placeholder kitöltés
        placeholders = {
            "{children}": "\n".join(child_codes) if child_codes else "",
            "{collection}": step.target if step.target and step.target not in ("", "érték", "gyűjtemény") else "data",
            "{item}": "x",
            "{func}": "str",
            "{action}": "#",
            "{method}": "post",
            "{compare}": "(a, b) => a - b",
            "{items}": "\n".join(child_codes) if child_codes else "    <li>Első elem</li>\n    <li>Második elem</li>\n    <li>Harmadik elem</li>",
            "{body}": "\n".join(child_codes) if child_codes else "    pass",
            # Python/JS placeholderek (alapértelmezett értékekkel)
            "{params}": "",
            "{value}": "None",
            "{prompt}": "",
            "{error}": "Exception",
            "{message}": "error",
            "{path}": "file.txt",
            "{content}": "data",
            "{module}": "os",
            "{names}": "func1, func2",
            "{alias}": "mod",
            "{n}": "5",
            "{min}": "0",
            "{max}": "100",
            "{expression}": "x",
            "{game_title}": "Játék",
            "{key}": "k",
            "{size}": "128",
            "{cleanup}": "pass",
            "{coroutine}": "async_func()",
            "{async_iter}": "async_iter",
            "{context}": "ctx",
            "{initial}": "0",
            "{k}": "3",
            "{keys}": "['a', 'b']",
            "{values}": "[1, 2]",
            "{var}": "f",
            "{selector}": "body",
            "{url}": "https://api.example.com/data",
            "{data}": "{key: 'value'}",
            "{property}": "color",
            "{from_prop}": "opacity",
            "{from_val}": "1",
            "{to_prop}": "opacity",
            "{to_val}": "0",
            "{dur}": "500",
            "{iter}": "1",
            "{ms}": "1000",
            "{event}": "click",
            "{parent}": "body",
            "{element}": "newElement",
            "{tab_id}": "tab1",
            "{tab_name}": "tab1",
            "{active}": "#3498db",
            "{display}": "block",
            "{modal_id}": "myModal",
            "{modal_title}": "Modal cím",
            "{sidebar_title}": "Navigáció",
            "{sidebar_children}": "",
            "{section_title}": "Szekció",
            "{avatar}": "https://via.placeholder.com/120",
            "{name}": "field",
            "{role}": "Tag",
            "{bio}": "Leírás",
            "{date}": "2026",
            "{event_title}": "Esemény",
            "{event_desc}": "Leírás",
            "{quote}": "Idealéző szöveg",
            "{author}": "Szerző",
            "{author_role}": "Beosztás",
            "{placeholder}": "Keresés...",
            "{newsletter_title}": "Iratkozz fel!",
            "{newsletter_text}": "Értesülj a legfrissebb hírekről!",
            "{skill_name}": "Képesség",
            "{percent}": "75",
            "{stat_icon}": "fa-star",
            "{stat_value}": "100",
            "{stat_label}": "Példa",
            "{stat_number}": "99",
            "{border}": "#3498db",
            "{plan_name}": "Csomag",
            "{price}": "9.990",
            "{feature_1}": "Alap funkció",
            "{feature_2}": "Pro funkció",
            "{feature_3}": "Premium funkció",
            "{table_id}": "myTable",
            "{tbody_id}": "myTbody",
            "{headers}": "<th>Név</th><th>Érték</th>",
            "{header_text}": "Fejléc",
            "{cell_text}": "Cella",
            "{question}": "Mi a kérdés?",
            "{answer}": "Ez a válasz.",
            "{tab_content}": "Tab tartalom",
            "{tab_title}": "Tab cím",
            "{tab_buttons}": "",
            "{options}": "<option>1</option><option>2</option>",
            "{table_header}": "",
            "{table_body}": "",
            "{table_data}": "",
            "{id}": "id1",
            "{class_name}": "active",
            "{tag}": "div",
            "{html_content}": "",
            "{slot_machine}": "slot",
            "{tab_id}": "tab1",
        }

        # Feltételes placeholderek
        if "{condition}" in result:
            if child_codes:
                placeholders["{condition}"] = child_codes[0]
            elif step.children:
                placeholders["{condition}"] = "True"
            else:
                placeholders["{condition}"] = "True"

        # Label / név
        label_val = "Mező"
        name_val = "field"
        if step.target and step.target not in ("érték", "gyűjtemény", ""):
            label_val = step.target.capitalize()
            name_val = step.target
        placeholders["{label}"] = label_val
        placeholders["{name}"] = name_val
        placeholders["{type}"] = "text"

        # Téma-kontextus placeholderek
        for key, default in [("text", "Üdvözöljük!"), ("title", "DKA V3"),
                              ("src", "https://via.placeholder.com/600x400"),
                              ("alt", "Kép"), ("caption", "Felirat"),
                              ("href", "#"), ("header_title", "Weboldal"),
                              ("header_subtitle", ""), ("onclick", "alert('Kattintás!')"),
                              ("button", "Tovább"), ("card_title", "Jellemzők"),
                              ("hero_title", "Hero"), ("hero_text", "Hero szöveg"),
                              ("section_title", "Szekció")]:
            val = topic_ctx.get(key, default)
            if isinstance(val, str) and len(val) > 100:
                val = val[:100]
            placeholders["{" + key + "}"] = val

        # === JÁTÉK VÁLTOZÓK: minden generálás más ===
        # Első játék step-nél számoljuk ki, utána újrahasználjuk
        if not hasattr(self, '_game_params') or self._game_params is None:
            import time
            game_seed = int(time.time() * 1000) % (2**16)
            rng = _random.Random(game_seed)
            schemes = [
                ("(0, 102, 204)", "(255, 50, 50)", "(240, 248, 255)"),
                ("(50, 205, 50)", "(255, 165, 0)", "(30, 30, 40)"),
                ("(147, 0, 211)", "(255, 215, 0)", "(245, 245, 220)"),
                ("(255, 20, 147)", "(0, 255, 255)", "(25, 25, 35)"),
                ("(0, 255, 127)", "(255, 0, 255)", "(240, 240, 240)"),
            ]
            scheme = rng.choice(schemes)
            self._game_params = {
                "{player_color}": scheme[0],
                "{enemy_color}": scheme[1],
                "{bg_color}": scheme[2],
                "{player_speed}": str(rng.randint(3, 8)),
                "{player_size}": str(rng.randint(30, 60)),
                "{enemy_size}": str(rng.randint(25, 50)),
                "{enemy_speed_min}": str(rng.randint(1, 3)),
                "{enemy_speed_max}": str(rng.randint(3, 7)),
                "{spawn_rate}": f"{rng.uniform(0.01, 0.04):.3f}",
                "{game_title}": f"DKA V3 Játék",
                "{game_over_text}": rng.choice(["GAME OVER", "Vége", "Játék vége"]),
            }
        for k, v in self._game_params.items():
            if k in result:
                placeholders[k] = v

        # Függvény body: a step description-ja tartalmazza a valós kifejezést
        if step.action == "visszatérés" and step.description:
            placeholders["{value}"] = step.description
        if step.action == "kiírás" and step.description:
            placeholders["{value}"] = step.description

        # Alkalmazzuk a placeholdereket (több menetben a nested esetekre)
        for _ in range(3):
            before = result
            for ph, val in list(placeholders.items()):
                if ph in result:
                    result = result.replace(ph, str(val))
            if result == before:
                break

        # Ha a step-nek nincs template-je, de van HAS_OPERATION kapcsolata,
        # és az action a "gyűjtemény" (célpont, nem akció), akkor
        # hagyjuk ki — a tényleges akció majd kezeli
        if step.action in ("gyűjtemény", "érték", "szám", "szöveg", "szótár", "logikai"):
            if child_codes:
                return "\n".join(child_codes)
            return None

        # Importok
        imp = dialect.get_import(step.action)
        if imp:
            imports_used.add(imp)

        return result
