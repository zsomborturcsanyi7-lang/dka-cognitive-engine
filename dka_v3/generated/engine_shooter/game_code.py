"""
DKA V3 — 2D Shooter játék
==========================
LLM által generált játéklogika a DKA Engine-hez.
Futtatás: python main.py
"""

SHOOTER_CODE = """
===init===
# Játékos
engine.set_var("px", engine.width // 2)
engine.set_var("py", engine.height - 80)
engine.set_var("speed", 5)
engine.set_var("hp", 100)
engine.set_var("max_hp", 100)

# Lövedékek
engine.set_var("bullets", [])
engine.set_var("bullet_cd", 0)
engine.set_var("bullet_delay", 12)
engine.set_var("bullet_damage", 25)

# Ellenségek
engine.set_var("enemies", [])
engine.set_var("enemy_bullets", [])
engine.set_var("score", 0)
engine.set_var("combo", 0)
engine.set_var("max_combo", 0)
engine.set_var("kills", 0)
engine.set_var("wave", 1)
engine.set_var("wave_enemies", 0)
engine.set_var("wave_max", 6)
engine.set_var("difficulty", 1.0)

# Power-up
engine.set_var("powerups", [])
engine.set_var("shield", False)
engine.set_var("rapid_fire", False)
engine.set_var("rapid_timer", 0)

# Effektek
engine.set_var("stars", [])
import random
stars = []
for _ in range(80):
    stars.append([random.randint(0, engine.width), random.randint(0, engine.height), random.uniform(1, 3)])
engine.set_var("stars_data", stars)

# Időzítők
engine.timer.set("spawn", 2.0)
engine.timer.set("wave_display", 0)
engine.set_var("show_wave", 0)
engine.timer.set("powerup", 10.0)
engine.set_var("game_time", 0.0)

# Highscore betöltés
hs = engine.save.get_highscores(1)
engine.set_var("highscore", hs[0]["score"] if hs else 0)

===update===
import pygame, random, math

# Alapértékek
px = engine.get_var("px")
py = engine.get_var("py")
spd = engine.get_var("speed", 5)
hp = engine.get_var("hp", 100)
mhp = engine.get_var("max_hp", 100)
bullets = engine.get_var("bullets", [])
enemies = engine.get_var("enemies", [])
enemy_bullets = engine.get_var("enemy_bullets", [])
powerups = engine.get_var("powerups", [])
score = engine.get_var("score", 0)
combo = engine.get_var("combo", 0)
kills = engine.get_var("kills", 0)
wave = engine.get_var("wave", 1)
wave_max = engine.get_var("wave_max", 6)
difficulty = engine.get_var("difficulty", 1.0)
shield = engine.get_var("shield", False)
rapid_fire = engine.get_var("rapid_fire", False)
rapid_timer = engine.get_var("rapid_timer", 0)
stars = engine.get_var("stars_data", [])
game_time = engine.get_var("game_time", 0.0)
bullet_cd = engine.get_var("bullet_cd", 0)
wave_enemies = engine.get_var("wave_enemies", 0)

game_time = game_time + engine.dt
engine.set_var("game_time", game_time)

# --- JÁTÉKOS MOZGÁS ---
if engine.input.key_pressed(pygame.K_LEFT): px = px - spd
if engine.input.key_pressed(pygame.K_RIGHT): px = px + spd
if engine.input.key_pressed(pygame.K_UP): py = py - spd
if engine.input.key_pressed(pygame.K_DOWN): py = py + spd
px = max(30, min(engine.width - 30, px))
py = max(30, min(engine.height - 30, py))

# --- LÖVÉS ---
delay = 5 if rapid_fire else engine.get_var("bullet_delay", 12)
bullet_cd = bullet_cd - 1

if engine.input.key_pressed(pygame.K_SPACE) and bullet_cd <= 0:
    dmg = engine.get_var("bullet_damage", 25)
    bullets.append({"x": px, "y": py - 20, "vx": 0, "vy": -12, "dmg": dmg})
    bullets.append({"x": px - 12, "y": py - 10, "vx": 0, "vy": -12, "dmg": dmg})
    bullets.append({"x": px + 12, "y": py - 10, "vx": 0, "vy": -12, "dmg": dmg})
    bullet_cd = delay
    if not shield:
        engine.audio.play_sfx("shoot")

# --- LÖVEDÉK FRISSÍTÉS ---
for b in bullets[:]:
    b["x"] = b["x"] + b.get("vx", 0)
    b["y"] = b["y"] + b.get("vy", 0)
    if b["y"] < -20:
        bullets.remove(b)

# --- ELLENSÉG SPAWN ---
spawn_rate = max(0.4, 2.0 - game_time * 0.005)
engine.timer.set("spawn", spawn_rate / difficulty)

if engine.timer.ready("spawn") and wave_enemies < wave_max:
    ex = random.randint(40, engine.width - 40)
    hp_mult = 1.0 + (wave - 1) * 0.3
    spd_mult = 1.0 + (wave - 1) * 0.1

    # Típus választás
    roll = random.random()
    if roll < 0.5:
        etype, ehp, espd, ecolor, esize, escore = "basic", 30, 2, (255, 80, 80), 14, 10
    elif roll < 0.75:
        etype, ehp, espd, ecolor, esize, escore = "fast", 20, 4, (255, 200, 50), 10, 15
    elif roll < 0.9:
        etype, ehp, espd, ecolor, esize, escore = "tank", 80, 1.2, (150, 50, 150), 20, 25
    else:
        etype, ehp, espd, ecolor, esize, escore = "shooter", 40, 1.5, (50, 200, 50), 16, 20

    enemies.append({
        "x": ex, "y": -30,
        "type": etype, "hp": int(ehp * hp_mult), "max_hp": int(ehp * hp_mult),
        "speed": espd * spd_mult, "color": ecolor, "size": esize,
        "score": escore, "shoot_timer": random.uniform(1, 3)
    })
    wave_enemies = wave_enemies + 1

engine.set_var("wave_enemies", wave_enemies)

# --- ELLENSÉG FRISSÍTÉS ---
for e in enemies[:]:
    # Mozgás
    e["y"] = e["y"] + e.get("speed", 2)

    # Shooter lövése
    if e.get("type") == "shooter":
        e["shoot_timer"] = e.get("shoot_timer", 2) - engine.dt
        if e["shoot_timer"] <= 0:
            dx = px - e["x"]
            dy = py - e["y"]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                enemy_bullets.append({
                    "x": e["x"], "y": e["y"] + 15,
                    "vx": (dx / dist) * 3,
                    "vy": (dy / dist) * 3,
                    "dmg": 10
                })
            e["shoot_timer"] = random.uniform(1.5, 3.0)

    # Ha lement a képernyőről
    if e["y"] > engine.height + 40:
        enemies.remove(e)
        hp = hp - 15
        engine.camera.shake(5)
        if hp < 0: hp = 0
        continue

# --- ELLENSÉG LÖVEDÉK FRISSÍTÉS ---
for eb in enemy_bullets[:]:
    eb["x"] = eb["x"] + eb.get("vx", 0)
    eb["y"] = eb["y"] + eb.get("vy", 0)
    if eb["y"] < -20 or eb["y"] > engine.height + 20 or eb["x"] < -20 or eb["x"] > engine.width + 20:
        enemy_bullets.remove(eb)
        continue

    # Találat a játékoson
    dx = eb["x"] - px
    dy = eb["y"] - py
    if dx * dx + dy * dy < 900 and not shield:
        hp = hp - eb.get("dmg", 10)
        engine.particles.emit(px, py, 5, "spark", color=(255, 50, 50))
        engine.camera.shake(3)
        enemy_bullets.remove(eb)
        if hp < 0: hp = 0

# --- LÖVÉS vs ELLENSÉG TALÁLAT ---
for b in bullets[:]:
    for e in enemies[:]:
        dx = b["x"] - e["x"]
        dy = b["y"] - e["y"]
        sz = e.get("size", 14)
        if dx * dx + dy * dy < (sz + 4) * (sz + 4):
            e["hp"] = e["hp"] - b.get("dmg", 25)
            engine.particles.emit(e["x"], e["y"], 5, "spark", color=(255, 200, 50))
            if b in bullets: bullets.remove(b)
            if e["hp"] <= 0:
                # Ellenség meghalt
                escore = e.get("score", 10) * (1 + combo * 0.5)
                score = score + int(escore)
                combo = combo + 1
                kills = kills + 1
                if combo > engine.get_var("max_combo", 0):
                    engine.set_var("max_combo", combo)

                engine.particles.emit(e["x"], e["y"], 25, "explosion", color=e.get("color", (255, 80, 80)))
                engine.filter.flash((255, 255, 255))
                engine.camera.shake(e.get("size", 14) * 0.3)

                # Power-up drop (20% esély)
                if random.random() < 0.20:
                    ptype = random.choice(["health", "rapid", "shield"])
                    powerups.append({"x": e["x"], "y": e["y"], "type": ptype})

                if e in enemies: enemies.remove(e)
            break

# --- HULLÁM RENDSZER ---
if wave_enemies >= wave_max and len(enemies) == 0:
    wave = wave + 1
    wave_max = min(6 + wave, 20)
    wave_enemies = 0
    engine.set_var("show_wave", 90)  # 90 frame-ig látszik
    difficulty = 1.0 + (wave - 1) * 0.15

    # Szintlépés effekt
    engine.particles.emit(engine.width // 2, engine.height // 2, 40, "explosion", color=(100, 255, 255))
    engine.filter.flash((100, 200, 255))
    hp = min(mhp, hp + 30)

# --- POWER-UP ---
for p in powerups[:]:
    p["y"] = p["y"] + 1.5
    if p["y"] > engine.height + 10:
        powerups.remove(p)
        continue
    dx = p["x"] - px
    dy = p["y"] - py
    if dx * dx + dy * dy < 900:
        if p["type"] == "health":
            hp = min(mhp, hp + 30)
            engine.particles.emit(p["x"], p["y"], 15, "spark", color=(0, 255, 0))
        elif p["type"] == "rapid":
            rapid_fire = True
            rapid_timer = 5.0
            engine.particles.emit(p["x"], p["y"], 15, "spark", color=(255, 255, 0))
        elif p["type"] == "shield":
            shield = True
            engine.particles.emit(p["x"], p["y"], 20, "spark", color=(0, 150, 255))
        powerups.remove(p)
        engine.audio.play_sfx("powerup")

# Rapid fire timer
if rapid_fire:
    rapid_timer = rapid_timer - engine.dt
    if rapid_timer <= 0:
        rapid_fire = False
        rapid_timer = 0

# Shield vizuális visszajelzés
if shield:
    shield_hp = engine.get_var("shield_hp", 50)
    shield_hp = shield_hp - engine.dt * 2
    if shield_hp <= 0:
        shield = False
        engine.set_var("shield_hp", 50)
    else:
        engine.set_var("shield_hp", shield_hp)
        # Shield világít
        engine.particles.emit(px, py, 1, "spark", color=(0, 150, 255))

# --- CSILLAGOK ---
for s in stars:
    s[1] = s[1] + s[2]
    if s[1] > engine.height:
        s[1] = 0
        s[0] = random.randint(0, engine.width)
        s[2] = random.uniform(1, 3)
engine.set_var("stars_data", stars)

# --- VÁLTOZÓK MENTÉSE ---
engine.set_var("px", px)
engine.set_var("py", py)
engine.set_var("hp", hp)
engine.set_var("bullets", bullets)
engine.set_var("enemies", enemies)
engine.set_var("enemy_bullets", enemy_bullets)
engine.set_var("powerups", powerups)
engine.set_var("score", score)
engine.set_var("combo", combo)
engine.set_var("kills", kills)
engine.set_var("wave", wave)
engine.set_var("wave_max", wave_max)
engine.set_var("difficulty", difficulty)
engine.set_var("shield", shield)
engine.set_var("rapid_fire", rapid_fire)
engine.set_var("rapid_timer", rapid_timer)
engine.set_var("bullet_cd", bullet_cd)
engine.set_var("wave_enemies", wave_enemies)

# Részecskék + animáció
engine.particles.update(engine.dt)

# Wave display timer
wd = engine.get_var("show_wave", 0)
if wd > 0:
    engine.set_var("show_wave", wd - 1)

===draw===
import pygame, random, math

px = engine.get_var("px")
py = engine.get_var("py")
hp = engine.get_var("hp", 100)
mhp = engine.get_var("max_hp", 100)
bullets = engine.get_var("bullets", [])
enemies = engine.get_var("enemies", [])
enemy_bullets = engine.get_var("enemy_bullets", [])
powerups = engine.get_var("powerups", [])
score = engine.get_var("score", 0)
combo = engine.get_var("combo", 0)
wave = engine.get_var("wave", 1)
shield = engine.get_var("shield", False)
rapid_fire = engine.get_var("rapid_fire", False)
stars = engine.get_var("stars_data", [])
game_time = engine.get_var("game_time", 0.0)

# --- HÁTTÉR ---
# Mélyűr (sötétkék -> fekete)
for i in range(engine.height):
    intensity = max(0, 5 - i * 0.02)
    color_val = max(0, min(255, int(5 + i * 0.04)))
    engine.screen.set_at((0, i), (color_val, color_val, color_val + 10))

# Csillagok
for s in stars:
    brightness = min(255, int(100 + s[2] * 50))
    engine.screen.set_at((int(s[0]), int(s[1])), (brightness, brightness, min(255, brightness + 20)))

# --- JÁTÉKOS (csillaghajó) ---
# Hajó törzs
pygame.draw.polygon(engine.screen, (0, 180, 255), [
    (px, py - 28),
    (px - 22, py + 8),
    (px - 10, py + 12),
    (px, py + 4),
    (px + 10, py + 12),
    (px + 22, py + 8),
])
# Pilótafülke
pygame.draw.polygon(engine.screen, (100, 220, 255), [
    (px, py - 18),
    (px - 10, py + 2),
    (px, py + 6),
    (px + 10, py + 2),
])
# Láng (hátsó)
flame_len = 8 + int(math.sin(game_time * 20) * 4)
pygame.draw.polygon(engine.screen, (255, 200, 50), [
    (px - 8, py + 10),
    (px, py + 10 + flame_len),
    (px + 8, py + 10),
])
pygame.draw.polygon(engine.screen, (255, 100, 0), [
    (px - 4, py + 12),
    (px, py + 10 + flame_len - 3),
    (px + 4, py + 12),
])

# Shield (ha van)
if shield:
    alpha = 60 + int(math.sin(game_time * 8) * 30)
    shield_surf = pygame.Surface((56, 56), pygame.SRCALPHA)
    pygame.draw.circle(shield_surf, (0, 150, 255, alpha), (28, 28), 28, 3)
    engine.screen.blit(shield_surf, (px - 28, py - 28))

# --- LÖVEDÉKEK ---
for b in bullets:
    bx, by = b["x"], b["y"]
    for i in range(3):
        c = (255, 255 - i * 60, 100 - i * 30)
        pygame.draw.circle(engine.screen, c, (int(bx), int(by) + i * 3), 3 - i)

# --- ELLENSÉG LÖVEDÉKEK ---
for eb in enemy_bullets:
    pygame.draw.circle(engine.screen, (255, 100, 100), (int(eb["x"]), int(eb["y"])), 4)
    pygame.draw.circle(engine.screen, (255, 200, 200), (int(eb["x"]), int(eb["y"])), 2)

# --- ELLENSÉGEK ---
for e in enemies:
    etype = e.get("type", "basic")
    color = e.get("color", (255, 80, 80))
    sz = e.get("size", 14)
    ex, ey = int(e["x"]), int(e["y"])

    if etype == "basic":
        pygame.draw.circle(engine.screen, color, (ex, ey), sz)
        pygame.draw.circle(engine.screen, (255, 200, 200), (ex, ey), sz - 4)
        # Szemek
        pygame.draw.circle(engine.screen, (255, 255, 255), (ex - 5, ey - 3), 3)
        pygame.draw.circle(engine.screen, (255, 255, 255), (ex + 5, ey - 3), 3)
        pygame.draw.circle(engine.screen, (0, 0, 0), (ex - 5, ey - 3), 1)
        pygame.draw.circle(engine.screen, (0, 0, 0), (ex + 5, ey - 3), 1)
    elif etype == "fast":
        # Kis, hegyes
        pygame.draw.polygon(engine.screen, color, [
            (ex, ey + sz), (ex - sz, ey - sz // 2), (ex, ey - 2), (ex + sz, ey - sz // 2)
        ])
    elif etype == "tank":
        # Nagy, vastag
        pygame.draw.rect(engine.screen, color, (ex - sz, ey - sz, sz * 2, sz * 2), border_radius=4)
        pygame.draw.rect(engine.screen, (200, 150, 200), (ex - sz + 3, ey - sz + 3, sz * 2 - 6, sz * 2 - 6), 2)
        for i in range(4):
            pygame.draw.circle(engine.screen, (100, 100, 100), (ex - sz + 5 + i * 8, ey + sz - 5), 3)
    elif etype == "shooter":
        # Háromszög
        pygame.draw.polygon(engine.screen, color, [
            (ex, ey + sz), (ex - sz, ey - sz), (ex + sz, ey - sz)
        ])
        pygame.draw.circle(engine.screen, (200, 255, 200), (ex, ey - 2), 4)

    # HP bar
    if e.get("max_hp", 30) > 30:
        hp_pct = e["hp"] / max(e["max_hp"], 1)
        engine.ui.progress_bar(engine.screen, ex - 12, ey - sz - 10, 24, 4, hp_pct, (255, 50, 50))

# --- POWER-UP ---
for p in powerups:
    px_pu, py_pu = p["x"], p["y"]
    pulse = 1.0 + math.sin(game_time * 6 + px_pu) * 0.1
    size = int(8 * pulse)
    glow = 4 + int(math.sin(game_time * 4 + py_pu) * 2)

    if p["type"] == "health":
        color = (0, 255, 0)
        glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (0, 255, 0, 60), (size * 2, size * 2), size + glow)
        engine.screen.blit(glow_surf, (px_pu - size * 2, py_pu - size * 2))
        pygame.draw.circle(engine.screen, color, (int(px_pu), int(py_pu)), size)
        # + jel
        pygame.draw.line(engine.screen, (255, 255, 255), (px_pu, py_pu - 5), (px_pu, py_pu + 5), 2)
        pygame.draw.line(engine.screen, (255, 255, 255), (px_pu - 5, py_pu), (px_pu + 5, py_pu), 2)
    elif p["type"] == "rapid":
        color = (255, 255, 0)
        glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 255, 0, 60), (size * 2, size * 2), size + glow)
        engine.screen.blit(glow_surf, (px_pu - size * 2, py_pu - size * 2))
        pygame.draw.circle(engine.screen, color, (int(px_pu), int(py_pu)), size)
        pygame.draw.polygon(engine.screen, (255, 255, 255), [
            (px_pu - 3, py_pu - 5), (px_pu + 5, py_pu), (px_pu - 3, py_pu + 5)
        ])
    elif p["type"] == "shield":
        color = (0, 150, 255)
        glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (0, 150, 255, 60), (size * 2, size * 2), size + glow)
        engine.screen.blit(glow_surf, (px_pu - size * 2, py_pu - size * 2))
        pygame.draw.circle(engine.screen, color, (int(px_pu), int(py_pu)), size)
        pygame.draw.circle(engine.screen, (255, 255, 255), (int(px_pu), int(py_pu)), size - 2, 2)

# --- RÉSZECSKÉK ---
engine.particles.render(engine.screen)

# --- HUD ---
# HP bar
engine.ui.draw_label(engine.screen, "HP", (10, 10), (255, 100, 100), engine.ui.font_small)
hp_pct = hp / max(mhp, 1)
hp_color = (0, 255, 0) if hp_pct > 0.5 else ((255, 255, 0) if hp_pct > 0.25 else (255, 0, 0))
engine.ui.progress_bar(engine.screen, 40, 14, 150, 14, hp_pct, hp_color)
engine.ui.draw_label(engine.screen, str(int(hp)) + "/" + str(int(mhp)), (195, 12), (255, 255, 255), engine.ui.font_small)

# Score + combo
engine.ui.draw_label(engine.screen, "SCORE: " + str(score), (10, 34), (255, 215, 0), engine.ui.font_small)
if combo > 1:
    engine.ui.draw_label(engine.screen, "COMBO x" + str(combo), (10, 54), (255, 255, 100), engine.ui.font_small)

# Wave
engine.ui.draw_label(engine.screen, "WAVE " + str(wave), (engine.width - 100, 10), (100, 200, 255), engine.ui.font_small)

# Kills
engine.ui.draw_label(engine.screen, "KILLS: " + str(engine.get_var("kills", 0)), (engine.width - 110, 34), (200, 200, 200), engine.ui.font_small, engine.ui.font_small)

# Rapid fire indicator
if rapid_fire:
    rt = engine.get_var("rapid_timer", 0)
    engine.ui.draw_label(engine.screen, "RAPID FIRE " + str(int(rt)) + "s", (engine.width // 2 - 60, engine.height - 30), (255, 255, 0), engine.ui.font_small)

# Highscore
hs = engine.get_var("highscore", 0)
if hs > 0:
    engine.ui.draw_label(engine.screen, "BEST: " + str(hs), (engine.width - 140, 58), (150, 150, 150), engine.ui.font_small, engine.ui.font_small)

# Wave kiírás középre
wd = engine.get_var("show_wave", 0)
if wd > 0:
    alpha = min(255, wd * 3)
    wave_text = "WAVE " + str(wave)
    # Fényes hatás
    glow_surf = engine.ui.font_large.render(wave_text, True, (100, 200, 255))
    engine.screen.blit(glow_surf, (engine.width // 2 - glow_surf.get_width() // 2 + 2, engine.height // 2 - 38))
    engine.ui.draw_label(engine.screen, wave_text, (engine.width // 2, engine.height // 2 - 40),
                         (200, 255, 255), engine.ui.font_large, center=True)

# Irányítás infó
if game_time < 5:
    engine.ui.draw_label(engine.screen, "Nyilak: mozgas | SPACE: loves | ESC: pause",
                         (engine.width // 2, engine.height - 20),
                         (150, 150, 150), engine.ui.font_small, center=True)

===collision===
hp = engine.get_var("hp", 100)
if hp <= 0:
    # Highscore mentés
    score = engine.get_var("score", 0)
    hs = engine.get_var("highscore", 0)
    if score > hs:
        engine.save.save_highscore("JATEKOS", score)
        engine.set_var("highscore", score)
    return True
return False

===menu_draw===
import pygame, random, math

# Csillagos háttér
for i in range(engine.height):
    intensity = max(0, 3 - i * 0.01)
    engine.screen.set_at((0, i), (intensity, intensity, intensity + 5))

stars = engine.get_var("stars_data", [])
for s in stars:
    brightness = min(255, int(100 + s[2] * 50))
    engine.screen.set_at((int(s[0]), int(s[1])), (brightness, brightness, min(255, brightness + 20)))

# Cím (pulzáló)
t = engine.get_var("game_time", 0)
pulse = 1.0 + math.sin(t * 2) * 0.03

# Cím háttér glow
title = "  2D SHOOTER  "
glow_surf = engine.ui.font_large.render(title, True, (50, 100, 255))
glow_rect = glow_surf.get_rect(center=(engine.width // 2 + 3, int(engine.height // 3 * pulse) + 3))
engine.screen.blit(glow_surf, glow_rect)

engine.ui.draw_label(engine.screen, title, (engine.width // 2, int(engine.height // 3 * pulse)),
                     (100, 200, 255), engine.ui.font_large, center=True)

# DKA + LLM felirat
engine.ui.draw_label(engine.screen, "DKA V3 + LLM", (engine.width // 2, int(engine.height // 3 * pulse) + 55),
                     (150, 150, 200), engine.ui.font_small, center=True)

# Gombok
btn_y = engine.height // 2 + 10
play_btn = pygame.Rect(engine.width // 2 - 100, btn_y, 200, 45)
hovered = play_btn.collidepoint(pygame.mouse.get_pos())
play_color = (60, 180, 60) if not hovered else (80, 220, 80)
if engine.ui.button(engine.screen, "JATEK INDITASA", play_btn, color=play_color):
    engine.switch_state(engine.STATE_PLAYING)

hs_btn = pygame.Rect(engine.width // 2 - 120, btn_y + 55, 240, 35)
hs_color = (80, 80, 150)
hs_list = engine.save.get_highscores(5)
if hs_list:
    hs_btn_text = "HIGHSCORES: " + str(hs_list[0]["score"])
else:
    hs_btn_text = "HIGHSCORES"
engine.ui.button(engine.screen, hs_btn_text, hs_btn, color=hs_color)

# Irányítás
engine.ui.draw_label(engine.screen, "Nyilak: mozgas | SPACE: loves | ESC: szunet | F1: debug | F12: screenshot",
                     (engine.width // 2, engine.height - 40),
                     (120, 120, 140), engine.ui.font_small, center=True)

# Animált csillagok frissítése
for s in stars:
    s[1] = s[1] + s[2] * 0.5
    if s[1] > engine.height:
        s[1] = 0
        s[0] = random.randint(0, engine.width)
engine.set_var("stars_data", stars)

===menu_handle===
import pygame
# Enter vagy SPACE indítja a játékot
if engine.input.key_just_pressed(pygame.K_SPACE) or engine.input.key_just_pressed(pygame.K_RETURN):
    engine.switch_state(engine.STATE_PLAYING)
"""

if __name__ == "__main__":
    print("Ez a játék logika fájl. Futtatás: python run_shooter.py")
