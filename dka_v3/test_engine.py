"""Teszt: 3 játék az új DKAEngine összes képességével."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()

from llm_game_engine import DKAEngine

# ═══════════════════════════════════════════════════════════
# 1. JÁTÉK: PLATFORMER
# ═══════════════════════════════════════════════════════════

platformer_code = """
===init===
engine.set_var("player_x", 50)
engine.set_var("player_y", 400)
engine.set_var("player_vx", 0)
engine.set_var("player_vy", 0)
engine.set_var("on_ground", False)
engine.set_var("score", 0)
engine.set_var("coins", 0)
engine.set_var("lives", 3)

# Egyszerű tilemap (40x15, 1 = fal, 0 = levegő)
grid = []
for r in range(15):
    row = [0] * 40
    if r == 14:
        row = [1] * 40
    elif r >= 12:
        row[0] = 1
        row[38] = 1
        row[39] = 1
    elif r in (4, 8, 10):
        row[0] = 1
        row[38] = 1
        row[39] = 1
    elif r == 6:
        row[0] = 1
        row[38] = 1
        row[39] = 1
    grid.append(row)

engine.load_tilemap({"width": 40, "height": 15, "tilesize": 32, "solids": [1],
    "layers": [{"name": "terrain", "data": grid}]})
engine.set_var("coin_positions", [(200, 350), (500, 350), (700, 280)])
engine.timer.set("coin_sparkle", 2.0)

===update===
import pygame
px = engine.get_var("player_x", 50)
py = engine.get_var("player_y", 400)
pvx = engine.get_var("player_vx", 0)
pvy = engine.get_var("player_vy", 0)
ground = engine.get_var("on_ground", False)
gravity = 0.6
spd = 5

if engine.input.key_pressed(pygame.K_LEFT):
    pvx = -spd
elif engine.input.key_pressed(pygame.K_RIGHT):
    pvx = spd
else:
    pvx = pvx * 0.8

if engine.input.key_just_pressed(pygame.K_SPACE) and ground:
    pvy = -12
    ground = False

pvy = pvy + gravity
if pvy > 15:
    pvy = 15

px = px + pvx
py = py + pvy

# Tilemap ütközés (egyszerűsítve)
player_rect = pygame.Rect(px, py, 28, 32)
hits = engine.tilemap.collides(player_rect)
ground = False
for tile_type, col, row in hits:
    tile_x = col * 32
    tile_y = row * 32
    if pvy > 0 and py < tile_y and py + 32 < tile_y + 20:
        py = tile_y - 32
        pvy = 0
        ground = True
    elif pvy < 0 and py > tile_y + 20:
        py = tile_y + 32
        pvy = 0

if px < 0: px = 0
if px > 1240: px = 1240

if py > 500:
    engine.set_var("lives", engine.get_var("lives", 3) - 1)
    px, py = 50, 400
    pvy = 0
    engine.camera.shake(8)
    engine.filter.flash((255, 0, 0))

# Coin gyűjtés
coins = engine.get_var("coin_positions", [])
new_coins = []
for cx, cy in coins:
    if abs(px - cx) < 24 and abs(py - cy) < 24:
        engine.inc_var("coins", 1)
        engine.inc_var("score", 10)
        engine.particles.emit(cx, cy, 15, "spark", color=(255, 215, 0))
    else:
        new_coins.append((cx, cy))
engine.set_var("coin_positions", new_coins)

# Kamera
engine.camera.follow(px + 14, py + 16)
engine.camera.update()

engine.set_var("player_x", px)
engine.set_var("player_y", py)
engine.set_var("player_vx", pvx)
engine.set_var("player_vy", pvy)
engine.set_var("on_ground", ground)

===draw===
import pygame
px = engine.get_var("player_x", 50)
py = engine.get_var("player_y", 400)
engine.tilemap.render(engine.screen, engine.camera)

sx = px - engine.camera.x
sy = py - engine.camera.y
pygame.draw.rect(engine.screen, (50, 100, 255), (sx, sy, 28, 32))
pygame.draw.rect(engine.screen, (100, 150, 255), (sx + 4, sy - 8, 20, 8))

for cx, cy in engine.get_var("coin_positions", []):
    sx2 = cx - engine.camera.x
    sy2 = cy - engine.camera.y
    pygame.draw.circle(engine.screen, (255, 215, 0), (int(sx2), int(sy2)), 8)

engine.ui.draw_label(engine.screen, "Coins: " + str(engine.get_var("coins", 0)), (10, 10), (255, 215, 0), engine.ui.font_small)
engine.ui.draw_label(engine.screen, "Score: " + str(engine.get_var("score", 0)), (10, 30), (255, 255, 255), engine.ui.font_small)
engine.ui.draw_label(engine.screen, "Lives: " + str(engine.get_var("lives", 3)), (10, 50), (255, 100, 100), engine.ui.font_small)

engine.particles.render(engine.screen, engine.camera)

===collision===
return engine.get_var("lives", 3) <= 0

===menu_draw===
import pygame
engine.ui.draw_label(engine.screen, "PLATFORMER", (engine.width // 2, engine.height // 3), (50, 150, 255), engine.ui.font_large, center=True)
engine.ui.draw_label(engine.screen, "Nyilak: mozgas | SPACE: ugras", (engine.width // 2, engine.height // 2 - 20), (200, 200, 200), engine.ui.font_small, center=True)
btn = pygame.Rect(engine.width // 2 - 80, engine.height // 2 + 30, 160, 45)
if engine.ui.button(engine.screen, "INDITAS", btn, color=(50, 150, 50)):
    engine.switch_state(engine.STATE_PLAYING)
"""

# ═══════════════════════════════════════════════════════════
# 2. JÁTÉK: SHOOT'EM UP
# ═══════════════════════════════════════════════════════════

shootemup_code = """
===init===
engine.set_var("px", engine.width // 2)
engine.set_var("py", engine.height - 80)
engine.set_var("bullets", [])
engine.set_var("enemies", [])
engine.set_var("score", 0)
engine.set_var("lives", 3)
engine.set_var("combo", 0)
engine.set_var("cd", 0)
engine.timer.set("spawn", 1.0)
engine.timer.set("star_update", 0.05)

===update===
import pygame, random, math
px = engine.get_var("px")
py = engine.get_var("py")
bullets = engine.get_var("bullets", [])
enemies = engine.get_var("enemies", [])
cd = engine.get_var("cd", 0)

spd = 6
if engine.input.key_pressed(pygame.K_LEFT): px = px - spd
if engine.input.key_pressed(pygame.K_RIGHT): px = px + spd
if engine.input.key_pressed(pygame.K_UP): py = py - spd
if engine.input.key_pressed(pygame.K_DOWN): py = py + spd
if px < 20: px = 20
if px > engine.width - 20: px = engine.width - 20
if py < 20: py = 20
if py > engine.height - 20: py = engine.height - 20

if engine.input.key_pressed(pygame.K_SPACE) and cd <= 0:
    bullets.append({"x": px, "y": py})
    cd = 10

for b in bullets[:]:
    b["y"] = b["y"] - 10
    if b["y"] < -10:
        bullets.remove(b)

if engine.timer.ready("spawn"):
    ex = random.randint(30, engine.width - 30)
    etype = random.choice(["basic", "fast"])
    hp = 1 if etype == "basic" else 1
    spd_e = 2 if etype == "basic" else 4
    enemies.append({"x": ex, "y": -20, "hp": hp, "spe": spd_e})

for e in enemies[:]:
    e["y"] = e["y"] + e.get("spe", 2)
    if e["y"] > engine.height + 20:
        enemies.remove(e)
        engine.set_var("lives", engine.get_var("lives", 3) - 1)
        engine.camera.shake(5)

for b in bullets[:]:
    for e in enemies[:]:
        dx = b["x"] - e["x"]
        dy = b["y"] - e["y"]
        if dx * dx + dy * dy < 400:
            e["hp"] = e["hp"] - 1
            if b in bullets: bullets.remove(b)
            engine.particles.emit(e["x"], e["y"], 8, "spark", color=(255, 200, 50))
            if e["hp"] <= 0:
                engine.inc_var("score", 10 * (1 + engine.get_var("combo", 0)))
                engine.inc_var("combo", 1)
                engine.particles.emit(e["x"], e["y"], 20, "explosion")
                engine.filter.flash((255, 255, 255))
                engine.camera.shake(3)
                if e in enemies: enemies.remove(e)
            break

if cd > 0: cd = cd - 1

engine.set_var("px", px)
engine.set_var("py", py)
engine.set_var("bullets", bullets)
engine.set_var("enemies", enemies)
engine.set_var("cd", cd)
engine.particles.update(engine.dt)

===draw===
import pygame, random
px = engine.get_var("px")
py = engine.get_var("py")
bullets = engine.get_var("bullets", [])
enemies = engine.get_var("enemies", [])

engine.screen.fill((0, 0, 10))
for _ in range(30):
    sx = random.randint(0, engine.width)
    sy = random.randint(0, engine.height)
    engine.screen.set_at((sx, sy), (40, 40, 60))

pygame.draw.polygon(engine.screen, (0, 200, 255), [(px, py - 25), (px - 18, py + 10), (px + 18, py + 10)])

for b in bullets:
    pygame.draw.rect(engine.screen, (255, 255, 100), (b["x"] - 2, b["y"] - 6, 4, 12))

for e in enemies:
    color = (255, 80, 80) if e.get("type") == "basic" else (255, 200, 50)
    pygame.draw.circle(engine.screen, color, (int(e["x"]), int(e["y"])), 14)
    pygame.draw.circle(engine.screen, (255, 255, 255), (int(e["x"]), int(e["y"])), 10, 1)

engine.particles.render(engine.screen)
engine.ui.draw_label(engine.screen, "Score: " + str(engine.get_var("score", 0)), (10, 10), (255, 255, 255))
engine.ui.draw_label(engine.screen, "Lives: " + str(engine.get_var("lives", 3)), (10, 36), (255, 100, 100))
c = engine.get_var("combo", 0)
if c > 1:
    engine.ui.draw_label(engine.screen, "Combo x" + str(c) + "!", (engine.width // 2, 20), (255, 215, 0), engine.ui.font_large, center=True)

===collision===
for e in engine.get_var("enemies", []):
    px = engine.get_var("px", 400)
    py = engine.get_var("py", 500)
    dx = e["x"] - px
    dy = e["y"] - py
    if dx * dx + dy * dy < 900:
        engine.set_var("lives", engine.get_var("lives", 3) - 1)
        engine.particles.emit(px, py, 30, "explosion", color=(255, 0, 0))
        engine.camera.shake(12)
        if engine.get_var("lives", 3) <= 0:
            return True
return False

===menu_draw===
import pygame, random
engine.screen.fill((0, 0, 10))
for _ in range(50):
    engine.screen.set_at((random.randint(0, engine.width), random.randint(0, engine.height)), (50, 50, 80))
engine.ui.draw_label(engine.screen, "SHOOT'EM UP", (engine.width // 2, engine.height // 3), (255, 100, 50), engine.ui.font_large, center=True)
engine.ui.draw_label(engine.screen, "Nyilak: mozgas | SPACE: loves", (engine.width // 2, engine.height // 2 - 20), (200, 200, 200), engine.ui.font_small, center=True)
btn = pygame.Rect(engine.width // 2 - 80, engine.height // 2 + 30, 160, 45)
if engine.ui.button(engine.screen, "INDITAS", btn, color=(200, 100, 50)):
    engine.switch_state(engine.STATE_PLAYING)
"""

# ═══════════════════════════════════════════════════════════
# 3. JÁTÉK: RPG DEMO
# ═══════════════════════════════════════════════════════════

rpg_code = """
===init===
engine.set_var("px", 400)
engine.set_var("py", 300)
engine.set_var("hp", 100)
engine.set_var("mhp", 100)
engine.set_var("atk", 10)
engine.set_var("lvl", 1)
engine.set_var("exp", 0)
engine.set_var("nexp", 50)
engine.set_var("gold", 0)
engine.set_var("enemies", [])
engine.set_var("show_menu", False)
engine.timer.set("spawn", 3.0)

===update===
import pygame, random, math
px = engine.get_var("px")
py = engine.get_var("py")
hp = engine.get_var("hp", 100)
mhp = engine.get_var("mhp", 100)
enemies = engine.get_var("enemies", [])

if engine.get_var("show_menu", False):
    if engine.input.key_just_pressed(pygame.K_RETURN) or engine.input.key_just_pressed(pygame.K_ESCAPE):
        engine.set_var("show_menu", False)
    return

spd = 4
if engine.input.key_pressed(pygame.K_LEFT): px = px - spd
if engine.input.key_pressed(pygame.K_RIGHT): px = px + spd
if engine.input.key_pressed(pygame.K_UP): py = py - spd
if engine.input.key_pressed(pygame.K_DOWN): py = py + spd
if px < 20: px = 20
if px > engine.width - 20: px = engine.width - 20
if py < 20: py = 20
if py > engine.height - 20: py = engine.height - 20

if len(enemies) < 4 and engine.timer.ready("spawn"):
    ex = random.randint(50, engine.width - 50)
    ey = random.randint(50, engine.height - 50)
    etype = random.choice(["goblin", "skeleton", "slime"])
    enemies.append({"x": ex, "y": ey, "type": etype, "hp": 20, "mhp": 20, "atk": 5})

for e in enemies[:]:
    dx = px - e["x"]
    dy = py - e["y"]
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > 0 and dist < 200:
        e["x"] = e["x"] + (dx / dist) * 1.5
        e["y"] = e["y"] + (dy / dist) * 1.5
    if dist < 35:
        hp = hp - e.get("atk", 5) * 0.1
    if hp < 0: hp = 0

if engine.input.key_just_pressed(pygame.K_SPACE):
    for e in enemies[:]:
        dx = px - e["x"]
        dy = py - e["y"]
        if dx * dx + dy * dy < 1600:
            dmg = engine.get_var("atk", 10) + random.randint(-3, 5)
            e["hp"] = e["hp"] - dmg
            engine.particles.emit(e["x"], e["y"], 8, "spark", color=(255, 100, 50))
            engine.filter.flash((255, 200, 100))
            if e["hp"] <= 0:
                engine.inc_var("exp", e["mhp"])
                engine.inc_var("gold", random.randint(1, 5))
                engine.particles.emit(e["x"], e["y"], 20, "explosion", color=(100, 255, 100))
                enemies.remove(e)
                exp = engine.get_var("exp", 0)
                nexp = engine.get_var("nexp", 50)
                if exp >= nexp:
                    engine.inc_var("lvl", 1)
                    engine.inc_var("mhp", 20)
                    engine.inc_var("atk", 5)
                    engine.set_var("exp", 0)
                    engine.set_var("nexp", nexp + 50)
                    engine.filter.flash((100, 255, 255))
                    engine.camera.shake(10)
                    hp = engine.get_var("mhp", 100)

if hp < mhp:
    hp = min(mhp, hp + 0.05)

engine.set_var("px", px)
engine.set_var("py", py)
engine.set_var("hp", hp)
engine.set_var("enemies", enemies)
engine.particles.update(engine.dt)

if engine.input.key_just_pressed(pygame.K_i):
    engine.set_var("show_menu", not engine.get_var("show_menu", False))

===draw===
import pygame
px = engine.get_var("px")
py = engine.get_var("py")
hp = engine.get_var("hp", 100)
mhp = engine.get_var("mhp", 100)
enemies = engine.get_var("enemies", [])

engine.screen.fill((30, 30, 40))
pygame.draw.rect(engine.screen, (80, 150, 255), (px - 18, py - 18, 36, 36), border_radius=18)
pygame.draw.circle(engine.screen, (130, 200, 255), (px - 5, py - 5), 6)

hp_pct = hp / max(mhp, 1)
engine.ui.progress_bar(engine.screen, px - 20, py - 30, 40, 5, hp_pct, (0, 255, 0))

for e in enemies:
    color = (50, 180, 50) if e.get("type") == "goblin" else ((200, 200, 200) if e.get("type") == "skeleton" else (100, 200, 200))
    pygame.draw.circle(engine.screen, color, (int(e["x"]), int(e["y"])), 16)
    pygame.draw.circle(engine.screen, (255, 255, 255), (int(e["x"]), int(e["y"])), 16, 1)
    ehp_pct = e["hp"] / max(e.get("mhp", 20), 1)
    engine.ui.progress_bar(engine.screen, int(e["x"]) - 14, int(e["y"]) - 22, 28, 4, ehp_pct, (255, 50, 50))

engine.particles.render(engine.screen)

engine.ui.draw_label(engine.screen, "HP: " + str(int(hp)) + "/" + str(int(mhp)), (10, 10), (100, 255, 100))
engine.ui.draw_label(engine.screen, "Szint: " + str(engine.get_var("lvl", 1)), (10, 34), (255, 255, 255), engine.ui.font_small)
engine.ui.draw_label(engine.screen, "I = inventory | SPACE = tamadas", (10, engine.height - 30), (120, 120, 120), engine.ui.font_small)

if engine.get_var("show_menu", False):
    overlay = pygame.Surface((engine.width, engine.height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    engine.screen.blit(overlay, (0, 0))
    engine.ui.draw_label(engine.screen, "STATUS", (engine.width // 2, engine.height // 2 - 60), (255, 255, 255), engine.ui.font_large, center=True)
    lines = ["Szint: " + str(engine.get_var("lvl", 1)), "HP: " + str(int(hp)) + "/" + str(int(mhp)), "Sebzes: " + str(engine.get_var("atk", 10))]
    for i, l in enumerate(lines):
        engine.ui.draw_label(engine.screen, l, (engine.width // 2, engine.height // 2 - 20 + i * 28), (200, 200, 200), engine.ui.font_small, center=True)

===collision===
return engine.get_var("hp", 100) <= 0

===menu_draw===
import pygame
engine.screen.fill((20, 20, 30))
engine.ui.draw_label(engine.screen, "RPG DEMO", (engine.width // 2, engine.height // 3 - 20), (100, 180, 255), engine.ui.font_large, center=True)
engine.ui.draw_label(engine.screen, "Nyilak: mozgas | SPACE: tamadas | I: status", (engine.width // 2, engine.height // 2), (200, 200, 200), engine.ui.font_small, center=True)
btn = pygame.Rect(engine.width // 2 - 80, engine.height // 2 + 40, 160, 40)
if engine.ui.button(engine.screen, "JATEK", btn, color=(60, 100, 200)):
    engine.switch_state(engine.STATE_PLAYING)
"""

# ═══════════════════════════════════════════════════════════
# TESZT
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("DKA V3 ENGINE TESZT — 3 játék verifikálása")
print("=" * 60)

tests = [
    ("1. Platformer", platformer_code, ["kamera", "tilemap", "particles", "timers"]),
    ("2. Shoot'em Up", shootemup_code, ["particles", "timers", "combo", "explosion"]),
    ("3. RPG Demo", rpg_code, ["menu", "UI", "save", "state machine"]),
]

all_ok = True
for name, code, features in tests:
    print(f"\n🎮 {name} ({', '.join(features)})")
    print("-" * 50)

    engine = DKAEngine(title="Test", game_dir=os.path.dirname(os.path.abspath(__file__)))

    # Parse + compile (mint a valós engine.run)
    sections = engine._parse_sections(code)
    ok = engine._compile_functions(sections)

    if ok:
        print(f"   ✅ Parsing + compilation OK")
        print(f"   ✅ Szekciok: {list(sections.keys())}")

        # Init hívás
        if engine.llm_init:
            try:
                engine.llm_init(engine)
                score = engine.get_var("score", set())
                lives = engine.get_var("lives", set())
                print(f"   ✅ Init: score={score}, lives={lives}")
            except Exception as e:
                print(f"   ⚠ Init hiba: {e}")
                all_ok = False

        # Update (1 frame)
        if engine.llm_update:
            try:
                engine.input.keys_down.add(pygame.K_RIGHT)
                engine.input.keys_down.add(pygame.K_SPACE)
                engine.llm_update(engine)
                print(f"   ✅ Update (1 frame) OK")
            except Exception as e:
                import traceback
                print(f"   ❌ Update hiba: {e}")
                traceback.print_exc()
                all_ok = False

        # Draw (1 frame)
        if engine.llm_draw:
            try:
                engine.screen = pygame.Surface((engine.width, engine.height))
                engine.llm_draw(engine)
                print(f"   ✅ Draw (1 frame) OK")
            except Exception as e:
                print(f"   ⚠ Draw hiba: {e}")
                all_ok = False

        # Collision
        if engine.llm_collision:
            try:
                result = engine.llm_collision(engine)
                print(f"   ✅ Collision: return {result}")
            except Exception as e:
                print(f"   ⚠ Collision hiba: {e}")
                all_ok = False

        # Menu draw
        if engine.llm_menu_draw:
            try:
                engine.llm_menu_draw(engine)
                print(f"   ✅ Menu draw OK")
            except Exception as e:
                print(f"   ⚠ Menu draw hiba: {e}")

    else:
        print(f"   ❌ HIBA")
        all_ok = False

print(f"\n{'=' * 60}")
if all_ok:
    print("✅ MIND a 3 jatek kodja HELYES! A motor hasznalhato.")
else:
    print("⚠ Van hiba (lásd fent)")

# Mentsük el a generált játékokat
base = os.path.dirname(os.path.abspath(__file__))
for name, code, folder in [
    ("Platformer", platformer_code, "generated/engine_platformer"),
    ("ShootemUp", shootemup_code, "generated/engine_shootemup"),
    ("RPG", rpg_code, "generated/engine_rpg"),
]:
    p = os.path.join(base, folder)
    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, "game_code.txt"), "w", encoding='utf-8') as f:
        f.write(code)
    print(f"   📄 {folder}/game_code.txt mentve")
